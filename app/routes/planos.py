from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import planos_collection, treinos_collection, alunos_collection
from app.core.security import decodificar_token
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(prefix="/admin/planos", tags=["Planos"])

DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]


async def get_current_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload


class DiaTreino(BaseModel):
    dia: str
    treino_id: Optional[str] = None  # None = descanso


class PlanoCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    dias: List[DiaTreino]


@router.get("")
async def listar_planos(admin=Depends(get_current_admin)):
    planos = []
    async for plano in planos_collection.find().sort("_id", -1):
        dias_com_treino = []
        for dia in plano.get("dias", []):
            treino_nome = "Descanso"
            if dia.get("treino_id"):
                treino = await treinos_collection.find_one(
                    {"_id": ObjectId(dia["treino_id"])}
                )
                if treino:
                    treino_nome = treino.get("nome", "—")
            dias_com_treino.append(
                {
                    "dia": dia["dia"],
                    "treino_id": dia.get("treino_id"),
                    "treino_nome": treino_nome,
                }
            )
        planos.append(
            {
                "id": str(plano["_id"]),
                "nome": plano.get("nome", ""),
                "dias": dias_com_treino,
            }
        )
    return planos


@router.post("")
async def criar_plano(data: PlanoCreate, admin=Depends(get_current_admin)):
    for dia in data.dias:
        if dia.dia not in DIAS_SEMANA:
            raise HTTPException(status_code=400, detail=f"Dia inválido: {dia.dia}")

    plano = {
        "nome": data.nome,
        "dias": [{"dia": d.dia, "treino_id": d.treino_id} for d in data.dias],
    }
    result = await planos_collection.insert_one(plano)
    return {"id": str(result.inserted_id), "nome": data.nome, "dias": plano["dias"]}


@router.delete("/{plano_id}")
async def deletar_plano(plano_id: str, admin=Depends(get_current_admin)):
    await planos_collection.delete_one({"_id": ObjectId(plano_id)})
    return {"ok": True}


@router.post("/{plano_id}/aluno/{aluno_id}")
async def vincular_plano(
    plano_id: str, aluno_id: str, admin=Depends(get_current_admin)
):
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    planos_atuais = aluno.get("planos_ids", [])
    if plano_id in planos_atuais:
        raise HTTPException(status_code=400, detail="Plano já vinculado")

    planos_atuais.append(plano_id)

    # 🔥 Busca o nome do plano e atualiza treino_nome do aluno
    plano = await planos_collection.find_one({"_id": ObjectId(plano_id)})
    novo_nome = plano.get("nome", "") if plano else ""

    await alunos_collection.update_one(
        {"_id": ObjectId(aluno_id)},
        {"$set": {"planos_ids": planos_atuais, "treino_nome": novo_nome}},
    )
    return {"ok": True}


@router.delete("/{plano_id}/aluno/{aluno_id}")
async def desvincular_plano(
    plano_id: str, aluno_id: str, admin=Depends(get_current_admin)
):
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    planos_atuais = aluno.get("planos_ids", [])
    planos_atuais = [p for p in planos_atuais if p != plano_id]

    novo_nome = ""
    if planos_atuais:
        ultimo_plano = await planos_collection.find_one(
            {"_id": ObjectId(planos_atuais[-1])}
        )
        if ultimo_plano:
            novo_nome = ultimo_plano.get("nome", "")

    await alunos_collection.update_one(
        {"_id": ObjectId(aluno_id)},
        {"$set": {"planos_ids": planos_atuais, "treino_nome": novo_nome}},
    )
    return {"ok": True}


@router.get("/aluno/{aluno_id}")
async def planos_do_aluno(aluno_id: str, admin=Depends(get_current_admin)):
    aluno = await alunos_collection.find_one({"_id": ObjectId(aluno_id)})
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    planos = []
    for plano_id in aluno.get("planos_ids", []):
        plano = await planos_collection.find_one({"_id": ObjectId(plano_id)})
        if plano:
            planos.append(
                {
                    "id": str(plano["_id"]),
                    "nome": plano.get("nome", ""),
                    "dias": plano.get("dias", []),
                }
            )
    return planos
