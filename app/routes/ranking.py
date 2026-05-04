from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import alunos_collection, users_collection
from app.core.security import decodificar_token
from bson import ObjectId
from datetime import datetime, date, timedelta
from typing import Optional

router = APIRouter(prefix="/api/v1/ranking", tags=["Ranking"])


# ── Auth genérica (aluno ou admin) ──────────────────────────
async def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload


async def get_current_aluno(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "aluno":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload


# ── Helpers ──────────────────────────────────────────────────
async def _get_aluno_doc_by_user_id(user_id: str) -> Optional[dict]:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("aluno_id"):
        return None
    return await alunos_collection.find_one({"_id": ObjectId(user["aluno_id"])})


def calcular_nivel(xp: int) -> dict:
    niveis = [
        (0, 1, "Iniciante", "⚪"),
        (100, 2, "Dedicado", "🟢"),
        (300, 3, "Consistente", "🔵"),
        (600, 4, "Focado", "🟣"),
        (1000, 5, "Avançado", "🟠"),
        (1500, 6, "Elite", "🔴"),
        (2200, 7, "Campeão", "⭐"),
        (3000, 8, "Lenda", "👑"),
    ]
    nivel_atual = niveis[0]
    idx_atual = 0
    for i, n in enumerate(niveis):
        if xp >= n[0]:
            nivel_atual = n
            idx_atual = i

    proximo = niveis[idx_atual + 1] if idx_atual + 1 < len(niveis) else None
    xp_base = nivel_atual[0]
    xp_proximo = proximo[0] if proximo else xp_base + 1000
    progresso = (
        min(100, int((xp - xp_base) / (xp_proximo - xp_base) * 100))
        if xp_proximo > xp_base
        else 100
    )

    return {
        "numero": nivel_atual[1],
        "nome": nivel_atual[2],
        "emoji": nivel_atual[3],
        "xp_atual": xp,
        "xp_proximo_nivel": xp_proximo,
        "progresso_percent": progresso,
    }


def calcular_streak(historico: list) -> int:
    """Conta dias consecutivos de treino até hoje (ou ontem se ainda não treinou hoje)."""
    if not historico:
        return 0
    datas = sorted(
        set(date.fromisoformat(h["data"]) for h in historico if h.get("data")),
        reverse=True,
    )
    if not datas:
        return 0
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    # Se o treino mais recente é anterior a ontem, streak = 0
    if datas[0] < ontem:
        return 0

    # Começa a contagem a partir de hoje (se treinou) ou ontem (se não treinou hoje ainda)
    esperado = hoje if datas[0] == hoje else ontem
    streak = 0
    for d in datas:
        if d == esperado:
            streak += 1
            esperado = d - timedelta(days=1)
        elif d < esperado:
            break
    return streak


def calcular_medalhas(stats: dict) -> list:
    medalhas = []
    total = stats.get("total_treinos", 0)
    streak = stats.get("streak", 0)
    xp = stats.get("xp", 0)

    # Treinos concluídos
    if total >= 1:
        medalhas.append(
            {
                "id": "primeiro_treino",
                "nome": "Primeiro Treino",
                "emoji": "🏋️",
                "descricao": "Completou o primeiro treino",
            }
        )
    if total >= 7:
        medalhas.append(
            {
                "id": "semana_completa",
                "nome": "Semana Completa",
                "emoji": "📅",
                "descricao": "7 treinos concluídos",
            }
        )
    if total >= 30:
        medalhas.append(
            {
                "id": "trinta_treinos",
                "nome": "30 Treinos",
                "emoji": "🔥",
                "descricao": "30 treinos concluídos",
            }
        )
    if total >= 100:
        medalhas.append(
            {
                "id": "centenario",
                "nome": "Centenário",
                "emoji": "💯",
                "descricao": "100 treinos concluídos",
            }
        )

    # Streak
    if streak >= 3:
        medalhas.append(
            {
                "id": "streak_3",
                "nome": "3 Dias Seguidos",
                "emoji": "⚡",
                "descricao": "3 dias consecutivos",
            }
        )
    if streak >= 7:
        medalhas.append(
            {
                "id": "streak_7",
                "nome": "Semana Perfeita",
                "emoji": "🌟",
                "descricao": "7 dias consecutivos",
            }
        )
    if streak >= 30:
        medalhas.append(
            {
                "id": "streak_30",
                "nome": "Mês Imparável",
                "emoji": "🏆",
                "descricao": "30 dias consecutivos",
            }
        )

    # XP
    if xp >= 500:
        medalhas.append(
            {
                "id": "xp_500",
                "nome": "500 XP",
                "emoji": "💎",
                "descricao": "Acumulou 500 XP",
            }
        )
    if xp >= 1000:
        medalhas.append(
            {
                "id": "xp_1000",
                "nome": "Mil XP",
                "emoji": "👑",
                "descricao": "Acumulou 1000 XP",
            }
        )

    return medalhas


# ── Rotas ────────────────────────────────────────────────────


@router.get("/me")
async def meu_ranking(aluno=Depends(get_current_aluno)):
    """Retorna stats pessoais, nível, medalhas e comparativo com mês passado."""
    aluno_doc = await _get_aluno_doc_by_user_id(aluno["sub"])
    if not aluno_doc:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    historico = aluno_doc.get("historico", [])
    xp = aluno_doc.get("xp", 0)
    hoje = date.today()
    mes_atual = hoje.strftime("%Y-%m")
    mes_passado_dt = date(hoje.year, hoje.month - 1 if hoje.month > 1 else 12, 1)
    mes_passado = mes_passado_dt.strftime("%Y-%m")

    treinos_mes_atual = [
        h for h in historico if h.get("data", "").startswith(mes_atual)
    ]
    treinos_mes_passado = [
        h for h in historico if h.get("data", "").startswith(mes_passado)
    ]
    streak = calcular_streak(historico)

    stats = {
        "total_treinos": len(historico),
        "streak": streak,
        "xp": xp,
        "treinos_mes_atual": len(treinos_mes_atual),
        "treinos_mes_passado": len(treinos_mes_passado),
    }

    return {
        "aluno_id": str(aluno_doc["_id"]),
        "nome": aluno_doc.get("nome", ""),
        "participa_ranking": aluno_doc.get("participa_ranking", False),
        "stats": stats,
        "nivel": calcular_nivel(xp),
        "medalhas": calcular_medalhas(stats),
        "streak": streak,
    }


@router.get("/global")
async def ranking_global(aluno=Depends(get_current_aluno)):
    """Retorna top alunos que optaram pelo ranking, ordenados por XP."""
    ranking = []
    async for a in (
        alunos_collection.find({"participa_ranking": True}).sort("xp", -1).limit(50)
    ):
        xp = a.get("xp", 0)
        historico = a.get("historico", [])
        streak = calcular_streak(historico)
        stats = {"total_treinos": len(historico), "streak": streak, "xp": xp}
        nivel = calcular_nivel(xp)
        ranking.append(
            {
                "id": str(a["_id"]),
                "nome": a.get("nome", ""),
                "xp": xp,
                "total_treinos": len(historico),
                "streak": streak,
                "nivel": nivel,
                "medalhas_count": len(calcular_medalhas(stats)),
            }
        )
    return ranking


@router.post("/me/participar")
async def toggle_participar(aluno=Depends(get_current_aluno)):
    """Aluno entra ou sai do ranking global."""
    aluno_doc = await _get_aluno_doc_by_user_id(aluno["sub"])
    if not aluno_doc:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    atual = aluno_doc.get("participa_ranking", False)
    await alunos_collection.update_one(
        {"_id": aluno_doc["_id"]}, {"$set": {"participa_ranking": not atual}}
    )
    return {"participa_ranking": not atual}
