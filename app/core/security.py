import hashlib
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.core.config import settings


# ── Encriptación SHA256 ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hashea la contraseña con SHA256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña coincida con el hash guardado."""
    return hash_password(plain_password) == hashed_password


# ── JWT Tokens ───────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Crea un JWT con expiración configurada en .env."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    """Decodifica y valida un JWT. Retorna None si es inválido o expiró."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None