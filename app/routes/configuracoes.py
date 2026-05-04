from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import configuracoes_collection
from app.core.security import decodificar_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/configuracoes", tags=["Configurações"])

async def get_current_admin(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return payload

class ConfigAcademia(BaseModel):
    nome_academia: Optional[str] = ""
    chave_pix: Optional[str] = ""
    tipo_pix: Optional[str] = "cpf"   # cpf | cnpj | email | telefone | aleatoria
    whatsapp: Optional[str] = ""
    mensagem_pagamento: Optional[str] = "Olá! Vi que minha mensalidade está próxima do vencimento. Gostaria de mais informações sobre o pagamento."

@router.get("")
async def buscar_configuracoes(admin=Depends(get_current_admin)):
    config = await configuracoes_collection.find_one({"tipo": "academia"})
    if not config:
        return ConfigAcademia().model_dump()
    config.pop("_id", None)
    config.pop("tipo", None)
    return config

@router.put("")
async def salvar_configuracoes(data: ConfigAcademia, admin=Depends(get_current_admin)):
    await configuracoes_collection.update_one(
        {"tipo": "academia"},
        {"$set": {**data.model_dump(), "tipo": "academia"}},
        upsert=True
    )
    return {"ok": True}

# Rota pública — aluno pode buscar sem ser admin
@router.get("/publica")
async def configuracoes_publicas(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = decodificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Não autorizado")
    config = await configuracoes_collection.find_one({"tipo": "academia"})
    if not config:
        return {"chave_pix": "", "tipo_pix": "cpf", "whatsapp": "", "nome_academia": "", "mensagem_pagamento": ""}
    return {
        "chave_pix": config.get("chave_pix", ""),
        "tipo_pix": config.get("tipo_pix", "cpf"),
        "whatsapp": config.get("whatsapp", ""),
        "nome_academia": config.get("nome_academia", ""),
        "mensagem_pagamento": config.get("mensagem_pagamento", ""),
    }