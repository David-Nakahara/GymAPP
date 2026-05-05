from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha[:72])

def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha[:72], hash)

def criar_token(data: dict) -> str:
    payload = data.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expira})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None