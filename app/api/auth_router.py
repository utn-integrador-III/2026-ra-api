from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import httpx

from app.database.database import get_db
from app.models.user_model import User
from app.schemas.auth_schemas import (
    RegisterRequest, LoginRequest, GoogleAuthRequest, AuthResponse, UserOut
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── POST /api/auth/register ──────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Verificar que el correo no esté en uso
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este correo ya está registrado"
        )

    # Validaciones básicas
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres"
        )

    # Crear usuario con contraseña hasheada en SHA256
    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


# ── POST /api/auth/login ─────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # Usuario no existe o se registró con Google (no tiene contraseña)
    if not user or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada"
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


# ── POST /api/auth/google ────────────────────────────────────────────
# Flutter manda el id_token que recibió de Google
# El backend lo verifica con Google y crea/encuentra al usuario

@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    # Verificar el Firebase ID Token
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={body.id_token}"
            )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Token de Firebase inválido")
        
        info = response.json()
        
        # Verificar que el token es para tu proyecto
        if info.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token no corresponde a esta app")

    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    google_id = info["sub"]
    email = info["email"]
    name = info.get("name", email.split("@")[0])

    # Buscar o crear usuario (igual que antes)
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            user.auth_provider = "google"
            db.commit()
            db.refresh(user)
    if not user:
        user = User(
            name=name,
            email=email,
            google_id=google_id,
            password_hash=None,
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


# ── GET /api/auth/profile ────────────────────────────────────────────

@router.get("/profile", response_model=UserOut)
def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
):
    from app.core.security import decode_access_token
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserOut.model_validate(user)
