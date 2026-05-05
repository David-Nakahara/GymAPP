import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))


_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
CORS_ORIGINS = [origin.strip() for origin in _cors_raw.split(",")]