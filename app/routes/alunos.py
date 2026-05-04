from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import alunos_collection, treinos_collection, users_collection
from app.core.security import decodificar_token, hash_senha
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
import random
import string

router = APIRouter(prefix="/admin/alunos", tags=["Alunos"])


# ================= AUTH =================
async def get_current_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload


# ================= MODELS =================
class AlunoCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    telefone: str = Field(..., min_length=8, max_length=20)
    treino_id: Optional[str] = None
    plano_meses: int = Field(default=1, ge=1, le=12)
    matricula_data: Optional[str] = None


class AlunoTreinoUpdate(BaseModel):
    treino_id: Optional[str] = None


# ================= UTILS =================
def calcular_vencimento(matricula_data: datetime, plano_meses: int) -> datetime:
    return matricula_data + relativedelta(months=plano_meses)


def calcular_status(proximo_vencimento: datetime) -> str:
    return "atrasado" if proximo_vencimento < datetime.today() else "em_dia"


def gerar_senha_aleatoria(tamanho=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(tamanho))


# ================= ROTAS =================

# 🔹 LISTAR ALUNOS (mantido leve)
@router.get("")
async def listar_alunos(admin=Depends(get_current_admin)):
    alunos = []
    async for aluno in alunos_collection.find().sort("_id", -1):
        alunos.append({
            "id": str(aluno["_id"]),
            "nome": aluno.get("nome", ""),
            "telefone": aluno.get("telefone", ""),
            "treino_nome": aluno.get("treino_nome", "—"),
            "treino_id": aluno.get("treino_id", None),
            "status": aluno.get("status", "ativo"),
            "pagamento_status": aluno.get("pagamento_status", "em_dia"),
            "plano_meses": aluno.get("plano_meses", 1),
            "matricula_data": aluno.get("matricula_data", None),
            "proximo_vencimento": aluno.get("proximo_vencimento", None),
        })
    return alunos


# 🔥 NOVO — OBTER ALUNO COMPLETO (COM EMAIL)
@router.get("/{aluno_id}")
async def obter_aluno(aluno_id: str, admin=Depends(get_current_admin)):
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})

    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    user = await users_collection.find_one({"aluno_id": aluno_id})

    return {
        "id": str(aluno["_id"]),
        "nome": aluno.get("nome"),
        "telefone": aluno.get("telefone"),
        "email": user.get("email") if user else None,
        "plano_meses": aluno.get("plano_meses"),
        "matricula_data": aluno.get("matricula_data"),
        "proximo_vencimento": aluno.get("proximo_vencimento"),
        "pagamento_status": aluno.get("pagamento_status"),
        "status": aluno.get("status"),
        "treino_id": aluno.get("treino_id"),
        "treino_nome": aluno.get("treino_nome"),
    }


# 🔥 RESET DE SENHA (PROFISSIONAL)
@router.post("/{aluno_id}/reset-senha")
async def reset_senha(aluno_id: str, admin=Depends(get_current_admin)):
    user = await users_collection.find_one({"aluno_id": aluno_id})

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    nova_senha = gerar_senha_aleatoria()

    await users_collection.update_one(
        {"aluno_id": aluno_id},
        {"$set": {"senha": hash_senha(nova_senha)}}
    )

    return {
        "ok": True,
        "nova_senha": nova_senha
    }


# 🔹 CRIAR ALUNO
@router.post("")
async def criar_aluno(data: AlunoCreate, admin=Depends(get_current_admin)):
    treino_nome = "—"
    if data.treino_id:
        treino = await treinos_collection.find_one({"_id": ObjectId(data.treino_id)})
        if treino:
            treino_nome = treino.get("nome", "—")

    matricula_data = (
        datetime.strptime(data.matricula_data, "%Y-%m-%d")
        if data.matricula_data
        else datetime.today()
    )

    proximo_vencimento = calcular_vencimento(matricula_data, data.plano_meses)
    pagamento_status = calcular_status(proximo_vencimento)

    aluno = {
        "nome": data.nome,
        "telefone": data.telefone,
        "treino_id": data.treino_id,
        "treino_nome": treino_nome,
        "status": "ativo",
        "plano_meses": data.plano_meses,
        "matricula_data": matricula_data.strftime("%Y-%m-%d"),
        "proximo_vencimento": proximo_vencimento.strftime("%Y-%m-%d"),
        "pagamento_status": pagamento_status,
        "historico": [],
    }

    result = await alunos_collection.insert_one(aluno)
    aluno_id = str(result.inserted_id)

    id_final = aluno_id[-6:]
    email_aluno = f"aluno.{id_final}@gymmanager.com"
    senha_aluno = f"gym{id_final}"

    await users_collection.insert_one({
        "email": email_aluno,
        "senha": hash_senha(senha_aluno),
        "role": "aluno",
        "aluno_id": aluno_id,
        "nome": data.nome,
    })

    return {
        "id": aluno_id,
        "nome": data.nome,
        "telefone": data.telefone,
        "treino_id": data.treino_id,
        "treino_nome": treino_nome,
        "status": "ativo",
        "plano_meses": data.plano_meses,
        "matricula_data": matricula_data.strftime("%Y-%m-%d"),
        "proximo_vencimento": proximo_vencimento.strftime("%Y-%m-%d"),
        "pagamento_status": pagamento_status,
        "credenciais": {
            "email": email_aluno,
            "senha": senha_aluno,
        },
    }


# 🔹 ATUALIZAR TREINO
@router.patch("/{aluno_id}/treino")
async def atualizar_treino(
    aluno_id: str,
    data: AlunoTreinoUpdate,
    admin=Depends(get_current_admin)
):
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    treino_nome = "—"
    if data.treino_id:
        treino = await treinos_collection.find_one({"_id": ObjectId(data.treino_id)})
        if not treino:
            raise HTTPException(status_code=404, detail="Treino não encontrado")
        treino_nome = treino.get("nome", "—")

    await alunos_collection.update_one(
        {"_id": ObjectId(aluno_id)},
        {"$set": {
            "treino_id": data.treino_id,
            "treino_nome": treino_nome,
        }}
    )

    return {
        "ok": True,
        "treino_id": data.treino_id,
        "treino_nome": treino_nome,
    }


# 🔹 DELETAR
@router.delete("/{aluno_id}")
async def deletar_aluno(aluno_id: str, admin=Depends(get_current_admin)):
    await users_collection.delete_one({"aluno_id": aluno_id})
    await alunos_collection.delete_one({"_id": ObjectId(aluno_id)})
    return {"ok": True}