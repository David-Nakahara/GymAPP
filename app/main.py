from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routes import (
    auth,
    admin,
    alunos,
    treinos,
    financeiro,
    planos,
    aluno,
    configuracoes,
    ranking,
)  # 🔥
from app.core.config import CORS_ORIGINS

app = FastAPI(title="GymApp API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas tentativas. Tente novamente em 1 minuto."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(alunos.router)
app.include_router(treinos.router)
app.include_router(financeiro.router)
app.include_router(planos.router)
app.include_router(aluno.router)
app.include_router(configuracoes.router)
app.include_router(ranking.router)


@app.get("/")
async def root():
    return {"status": "GymApp API rodando"}
