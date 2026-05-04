from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import alunos_collection
from app.core.security import decodificar_token
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter(prefix="/admin/financeiro", tags=["Financeiro"])

async def get_current_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload

def calcular_status(proximo_vencimento_str: str) -> str:
    if not proximo_vencimento_str:
        return "em_dia"
    proximo = datetime.strptime(proximo_vencimento_str, "%Y-%m-%d")
    return "atrasado" if proximo < datetime.today() else "em_dia"

def valor_plano(plano_meses: int) -> float:
    tabela = {1: 100.0, 3: 270.0, 6: 480.0, 12: 840.0}
    return tabela.get(plano_meses, plano_meses * 100.0)

@router.get("")
async def listar_financeiro(admin=Depends(get_current_admin)):
    alunos = []
    async for aluno in alunos_collection.find().sort("_id", -1):
        proximo_vencimento = aluno.get("proximo_vencimento", None)
        status_atual = calcular_status(proximo_vencimento)
        if status_atual != aluno.get("pagamento_status"):
            await alunos_collection.update_one(
                {"_id": aluno["_id"]},
                {"$set": {"pagamento_status": status_atual}}
            )
        alunos.append({
            "id": str(aluno["_id"]),
            "nome": aluno.get("nome", ""),
            "status": aluno.get("status", "ativo"),
            "pagamento_status": status_atual,
            "plano_meses": aluno.get("plano_meses", 1),
            "matricula_data": aluno.get("matricula_data", None),
            "proximo_vencimento": proximo_vencimento,
            "historico_pagamentos": aluno.get("historico_pagamentos", []),
        })
    return alunos

@router.get("/relatorio")
async def relatorio_financeiro(admin=Depends(get_current_admin)):
    total_receita = 0.0
    receita_por_mes = {}
    em_dia = 0
    atrasados = 0
    por_plano = {"1": 0, "3": 0, "6": 0, "12": 0}

    async for aluno in alunos_collection.find():
        plano = aluno.get("plano_meses", 1)
        status = calcular_status(aluno.get("proximo_vencimento", ""))

        if status == "em_dia":
            em_dia += 1
        else:
            atrasados += 1

        chave = str(plano) if str(plano) in por_plano else "1"
        por_plano[chave] += 1

        
        for pag in aluno.get("historico_pagamentos", []):
            total_receita += pag.get("valor", 0)
            mes = pag.get("data", "")[:7]  # "2026-04"
            if mes:
                receita_por_mes[mes] = receita_por_mes.get(mes, 0) + pag.get("valor", 0)

    receita_mensal = [
        {"mes": k, "valor": round(v, 2)}
        for k, v in sorted(receita_por_mes.items())
    ]

    return {
        "total_receita": round(total_receita, 2),
        "em_dia": em_dia,
        "atrasados": atrasados,
        "receita_mensal": receita_mensal,
        "por_plano": [
            {"plano": "Mensal",     "quantidade": por_plano["1"]},
            {"plano": "Trimestral", "quantidade": por_plano["3"]},
            {"plano": "Semestral",  "quantidade": por_plano["6"]},
            {"plano": "Anual",      "quantidade": por_plano["12"]},
        ],
    }


@router.get("/{aluno_id}/historico")
async def historico_aluno(aluno_id: str, admin=Depends(get_current_admin)):
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return {
        "nome": aluno.get("nome"),
        "historico_pagamentos": aluno.get("historico_pagamentos", []),
    }

class PagamentoUpdate(BaseModel):
    acao: str

@router.patch("/{aluno_id}")
async def atualizar_pagamento(aluno_id: str, data: PagamentoUpdate, admin=Depends(get_current_admin)):
    if data.acao not in ["quitar", "atrasar"]:
        raise HTTPException(status_code=400, detail="Ação inválida")
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    if data.acao == "quitar":
        plano_meses = aluno.get("plano_meses", 1)
        novo_vencimento = datetime.today() + relativedelta(months=plano_meses)
        valor = valor_plano(plano_meses)

        
        registro = {
            "data": datetime.today().strftime("%Y-%m-%d"),
            "valor": valor,
            "plano_meses": plano_meses,
            "descricao": f"Mensalidade {plano_meses} mês(es)",
            "vencimento_anterior": aluno.get("proximo_vencimento", ""),
            "novo_vencimento": novo_vencimento.strftime("%Y-%m-%d"),
        }

        await alunos_collection.update_one(
            {"_id": ObjectId(aluno_id)},
            {
                "$set": {
                    "pagamento_status": "em_dia",
                    "proximo_vencimento": novo_vencimento.strftime("%Y-%m-%d"),
                    "matricula_data": datetime.today().strftime("%Y-%m-%d"),
                },
                "$push": {"historico_pagamentos": registro},
            }
        )
    else:
        await alunos_collection.update_one(
            {"_id": ObjectId(aluno_id)},
            {"$set": {"pagamento_status": "atrasado"}}
        )
    return {"ok": True}

class PlanoUpdate(BaseModel):
    plano_meses: int = Field(..., ge=1, le=12)
    matricula_data: str

@router.patch("/{aluno_id}/plano")
async def atualizar_plano(aluno_id: str, data: PlanoUpdate, admin=Depends(get_current_admin)):
    try:
        matricula_data = datetime.strptime(data.matricula_data, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida")
    novo_vencimento = matricula_data + relativedelta(months=data.plano_meses)
    status = "atrasado" if novo_vencimento < datetime.today() else "em_dia"
    await alunos_collection.update_one(
        {"_id": ObjectId(aluno_id)},
        {"$set": {
            "plano_meses": data.plano_meses,
            "matricula_data": data.matricula_data,
            "proximo_vencimento": novo_vencimento.strftime("%Y-%m-%d"),
            "pagamento_status": status,
        }}
    )
    return {"ok": True}