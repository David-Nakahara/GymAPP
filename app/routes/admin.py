from fastapi import APIRouter, Depends, Header, HTTPException
from app.database import users_collection, alunos_collection, treinos_collection
from app.core.security import decodificar_token

router = APIRouter(prefix="/admin", tags=["Admin"])

async def get_current_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload

@router.get("/dashboard")
async def dashboard(admin=Depends(get_current_admin)):
    total_alunos = await alunos_collection.count_documents({"status": "ativo"})
    inadimplentes = await alunos_collection.count_documents({"pagamento_status": "atrasado"})
    total_treinos = await treinos_collection.count_documents({})

    alunos_recentes = []
    async for aluno in alunos_collection.find().sort("_id", -1).limit(5):
        alunos_recentes.append({
            "id": str(aluno["_id"]),
            "nome": aluno.get("nome", ""),
            "treino": aluno.get("treino_nome", "—"),
            "status": aluno.get("status", "ativo"),
            "pagamento_status": aluno.get("pagamento_status", "em_dia"),
        })

    return {
        "alunos_ativos": total_alunos,
        "inadimplentes": inadimplentes,
        "total_treinos": total_treinos,
        "checkins": 0,
        "alunos_recentes": alunos_recentes,
    }