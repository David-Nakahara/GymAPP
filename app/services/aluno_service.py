from app.database import alunos_collection, treinos_collection, users_collection, planos_collection
from bson import ObjectId
from datetime import datetime
from typing import Optional

# Mapeamento: weekday() do Python → chave usada na collection planos
DIAS_SEMANA = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
    5: "sabado",
    6: "domingo",
}


async def _get_aluno_doc(user_id: str) -> Optional[dict]:
    """
    Recebe o user._id do token JWT, cruza com users_collection
    para obter o aluno_id, e retorna o documento completo de alunos.
    """
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("aluno_id"):
        return None

    aluno = await alunos_collection.find_one({"_id": ObjectId(user["aluno_id"])})
    return aluno


async def get_aluno_by_token(user_id: str) -> Optional[dict]:
    try:
        aluno = await _get_aluno_doc(user_id)
        if not aluno:
            return None

        return {
            "id": str(aluno["_id"]),
            "nome": aluno.get("nome", ""),
            "telefone": aluno.get("telefone", ""),
            "status": aluno.get("status", "ativo"),
            "pagamento_status": aluno.get("pagamento_status", "em_dia"),
            "plano_meses": aluno.get("plano_meses", 1),
            "matricula_data": aluno.get("matricula_data"),
            "proximo_vencimento": aluno.get("proximo_vencimento"),
            "treino_id": aluno.get("treino_id"),
            "treino_nome": aluno.get("treino_nome", "—"),
        }
    except Exception:
        return None


async def get_treino_aluno(user_id: str) -> Optional[dict]:
    """
    Prioridade:
    1. Se o aluno tem planos vinculados (planos_ids), pega o primeiro plano,
       identifica o dia da semana atual e retorna o treino desse dia.
    2. Fallback: usa o treino_id fixo salvo no documento do aluno (legado).
    3. Se nenhum dos dois existir, retorna None.
    """
    try:
        aluno = await _get_aluno_doc(user_id)
        if not aluno:
            return None

        planos_ids = aluno.get("planos_ids", [])

        # ── 1. Lógica de plano semanal ────────────────────────────────────
        if planos_ids:
            dia_hoje = DIAS_SEMANA[datetime.today().weekday()]

            # Percorre os planos do aluno até achar um treino para hoje
            for plano_id in planos_ids:
                try:
                    plano = await planos_collection.find_one({"_id": ObjectId(plano_id)})
                except Exception:
                    continue

                if not plano:
                    continue

                dia_entry = next(
                    (d for d in plano.get("dias", []) if d.get("dia") == dia_hoje),
                    None
                )

                if not dia_entry or not dia_entry.get("treino_id"):
                    # Dia de descanso neste plano
                    return {
                        "id": None,
                        "nome": "Descanso",
                        "exercicios": [],
                        "plano_nome": plano.get("nome", ""),
                        "dia": dia_hoje,
                    }

                treino = await treinos_collection.find_one(
                    {"_id": ObjectId(dia_entry["treino_id"])}
                )
                if treino:
                    return {
                        "id": str(treino["_id"]),
                        "nome": treino.get("nome", ""),
                        "exercicios": treino.get("exercicios", []),
                        "plano_nome": plano.get("nome", ""),
                        "dia": dia_hoje,
                    }

        # ── 2. Fallback: treino_id fixo ───────────────────────────────────
        treino_id = aluno.get("treino_id")
        if not treino_id:
            return None

        treino = await treinos_collection.find_one({"_id": ObjectId(treino_id)})
        if not treino:
            return None

        return {
            "id": str(treino["_id"]),
            "nome": treino.get("nome", ""),
            "exercicios": treino.get("exercicios", []),
        }

    except Exception:
        return None


async def get_historico(user_id: str) -> list:
    try:
        aluno = await _get_aluno_doc(user_id)
        if not aluno:
            return []

        historico = aluno.get("historico", [])
        return sorted(historico, key=lambda x: x.get("data", ""), reverse=True)
    except Exception:
        return []


async def concluir_treino(user_id: str, treino_id: str, treino_nome: str) -> bool:
    try:
        aluno = await _get_aluno_doc(user_id)
        if not aluno:
            return False

        historico = aluno.get("historico", [])
        hoje = datetime.now().strftime("%Y-%m-%d")

        # Evita duplicata no mesmo dia para o mesmo treino
        ja_concluiu_hoje = any(
            h.get("data") == hoje and h.get("treino_id") == treino_id
            for h in historico
        )

        registro = {
            "data": hoje,
            "treino_id": treino_id,
            "treino_nome": treino_nome,
            "concluido": True,
        }

        # 🔥 XP: 50 base + 10 bônus se já treinou ontem (streak bonus)
        from datetime import date, timedelta
        ontem = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        treinou_ontem = any(h.get("data") == ontem for h in historico)
        xp_ganho = 0 if ja_concluiu_hoje else (60 if treinou_ontem else 50)

        update = {"$push": {"historico": registro}}
        if xp_ganho > 0:
            update["$inc"] = {"xp": xp_ganho}

        await alunos_collection.update_one({"_id": aluno["_id"]}, update)
        return True
    except Exception:
        return False