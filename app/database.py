from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGO_URI
import certifi

client = AsyncIOMotorClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    tls=True,
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=5000,
)

db = client["gymapp"]

users_collection = db["users"]
alunos_collection = db["alunos"]
treinos_collection = db["treinos"]
planos_collection = db["planos"]
configuracoes_collection = db["configuracoes"]  