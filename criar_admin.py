import asyncio
from app.database import users_collection
from app.core.security import hash_senha

async def criar_admin():
    admin = {
        "email": "admin@gymapp.com",
        "senha": hash_senha("admin123"),
        "role": "admin",
        "nome": "Administrador"
    }

    existente = await users_collection.find_one({"email": admin["email"]})
    if existente:
        print("Admin já existe!")
        return

    await users_collection.insert_one(admin)
    print("Admin criado com sucesso!")
    print("Email: admin@gymapp.com")
    print("Senha: admin123")

asyncio.run(criar_admin())