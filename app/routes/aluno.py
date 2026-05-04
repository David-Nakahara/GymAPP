from fastapi import APIRouter, Depends, HTTPException, Header
from app.core.security import decodificar_token, verificar_senha, hash_senha
from app.database import users_collection
from app.services import aluno_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/aluno", tags=["Aluno"])


async def get_current_aluno(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    if payload.get("role") != "aluno":
        raise HTTPException(status_code=401, detail="Acesso não autorizado")
    return payload


@router.get("/me")
async def get_me(aluno=Depends(get_current_aluno)):
    aluno_data = await aluno_service.get_aluno_by_token(aluno["sub"])
    if not aluno_data:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return aluno_data


@router.get("/me/treino")
async def get_treino(aluno=Depends(get_current_aluno)):
    treino = await aluno_service.get_treino_aluno(aluno["sub"])
    if not treino:
        return {"message": "Nenhum treino atribuído", "exercicios": []}
    return treino


@router.get("/me/historico")
async def get_historico(aluno=Depends(get_current_aluno)):
    historico = await aluno_service.get_historico(aluno["sub"])
    return {"historico": historico}


class ConcluirTreinoInput(BaseModel):
    treino_id: str
    treino_nome: str


@router.post("/me/treino/concluir")
async def concluir_treino(data: ConcluirTreinoInput, aluno=Depends(get_current_aluno)):
    sucesso = await aluno_service.concluir_treino(
        aluno["sub"], data.treino_id, data.treino_nome
    )
    if not sucesso:
        raise HTTPException(status_code=500, detail="Erro ao concluir treino")
    return {"ok": True, "message": "Treino concluído com sucesso!"}


class TrocarSenhaInput(BaseModel):
    senha_atual: str = Field(..., min_length=4)
    nova_senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


@router.post("/me/trocar-senha")
async def trocar_senha(data: TrocarSenhaInput, aluno=Depends(get_current_aluno)):
    
    if data.nova_senha != data.confirmar_senha:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")

    
    user = await users_collection.find_one({"_id": __import__('bson').ObjectId(aluno["sub"])})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.get("role") != "aluno":
        raise HTTPException(status_code=403, detail="Não permitido")

    # Verifica senha atual
    if not verificar_senha(data.senha_atual, user["senha"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    # Salva nova senha
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"senha": hash_senha(data.nova_senha)}}
    )

    return {"ok": True, "message": "Senha alterada com sucesso!"}