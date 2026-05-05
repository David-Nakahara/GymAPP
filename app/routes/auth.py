from fastapi import APIRouter, HTTPException, Request
from app.schemas.auth import LoginInput, TokenOutput
from app.database import users_collection
from app.core.security import verificar_senha, criar_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenOutput)
async def login(request: Request, data: LoginInput):
    print(f"[DEBUG] Login attempt: {data.email}")
    user = await users_collection.find_one({"email": data.email})

    if not user or not verificar_senha(data.senha, user["senha"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    token = criar_token({"sub": str(user["_id"]), "role": user["role"]})

    return {"access_token": token, "token_type": "bearer", "role": user["role"]}