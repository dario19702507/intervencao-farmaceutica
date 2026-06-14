import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
APP_ENV = os.getenv("APP_ENV", "development").lower()

if not SECRET_KEY:
    if APP_ENV in {"production", "homologation", "staging"}:
        raise RuntimeError("SECRET_KEY deve ser configurada em produção/homologação")
    SECRET_KEY = "dev-secret-key-change-before-deploy"

if APP_ENV in {"production", "homologation", "staging"} and SECRET_KEY in {
    "troque-esta-chave-em-producao",
    "dev-secret-key-change-before-deploy",
}:
    raise RuntimeError("SECRET_KEY insegura: defina uma chave forte no ambiente de produção/homologação")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
