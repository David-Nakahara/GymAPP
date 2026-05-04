from fastapi import APIRouter, Depends, HTTPException
from app.database import treinos_collection
from app.core.security import decodificar_token
from fastapi import Header
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/admin/treinos", tags=["Treinos"])

async def get_current_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload

# 🔥 Schema de mídia
class ExercicioMedia(BaseModel):
    type: Optional[str] = "gif"        # gif | video | image
    url: Optional[str] = None          # URL do GIF/vídeo
    thumbnail: Optional[str] = None    # URL da thumbnail

# 🔥 Schema completo do exercício
class Exercicio(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    muscle_group: Optional[str] = None        # biceps, triceps, pernas...
    equipment: Optional[str] = None           # barra, haltere, máquina...
    series: int = Field(..., ge=1, le=20)
    reps: str = Field(..., max_length=20)
    rest_seconds: Optional[int] = Field(default=60, ge=0, le=600)
    media: Optional[ExercicioMedia] = None
    instructions: Optional[List[str]] = []

class TreinoCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    exercicios: List[Exercicio] = Field(..., min_length=1)

@router.get("")
async def listar_treinos(admin=Depends(get_current_admin)):
    treinos = []
    async for treino in treinos_collection.find().sort("_id", -1):
        treinos.append({
            "id": str(treino["_id"]),
            "nome": treino.get("nome", ""),
            "exercicios": treino.get("exercicios", []),
        })
    return treinos

@router.get("/{treino_id}")
async def buscar_treino(treino_id: str, admin=Depends(get_current_admin)):
    treino = await treinos_collection.find_one({"_id": ObjectId(treino_id)})
    if not treino:
        raise HTTPException(status_code=404, detail="Treino não encontrado")
    return {
        "id": str(treino["_id"]),
        "nome": treino.get("nome", ""),
        "exercicios": treino.get("exercicios", []),
    }

@router.post("")
async def criar_treino(data: TreinoCreate, admin=Depends(get_current_admin)):
    treino = {
        "nome": data.nome,
        "exercicios": [e.model_dump() for e in data.exercicios],
    }
    result = await treinos_collection.insert_one(treino)
    return {
        "id": str(result.inserted_id),
        "nome": data.nome,
        "exercicios": treino["exercicios"],
    }

# 🔥 Rota para editar treino existente
@router.put("/{treino_id}")
async def editar_treino(treino_id: str, data: TreinoCreate, admin=Depends(get_current_admin)):
    treino = await treinos_collection.find_one({"_id": ObjectId(treino_id)})
    if not treino:
        raise HTTPException(status_code=404, detail="Treino não encontrado")

    exercicios_atualizados = [e.model_dump() for e in data.exercicios]

    await treinos_collection.update_one(
        {"_id": ObjectId(treino_id)},
        {"$set": {
            "nome": data.nome,
            "exercicios": exercicios_atualizados,
        }}
    )
    return {
        "id": treino_id,
        "nome": data.nome,
        "exercicios": exercicios_atualizados,
    }

@router.delete("/{treino_id}")
async def deletar_treino(treino_id: str, admin=Depends(get_current_admin)):
    await treinos_collection.delete_one({"_id": ObjectId(treino_id)})
    return {"ok": True}