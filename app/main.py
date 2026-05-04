from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, admin, alunos, treinos, financeiro, planos, aluno, configuracoes, ranking  # 🔥

app = FastAPI(title="GymApp API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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