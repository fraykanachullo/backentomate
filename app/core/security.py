"""
Funciones JWT y hashing. Implementacion completa en Fase A.4.
Por ahora: placeholders con interfaz definida para no romper imports.
"""
from datetime import datetime, timedelta, timezone
from jose import jwt
import secrets
import hashlib
import bcrypt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_access_expire_hours)
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token() -> str:
    raw = secrets.token_urlsafe(32)
    return raw


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.JWTError as e:
        raise ValueError(f"Token invalido: {e}")
