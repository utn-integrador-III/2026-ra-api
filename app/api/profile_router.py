from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database.database import get_db
from app.models.user_model import User
from app.core.security import decode_access_token
from app.schemas.auth_schemas import UserOut
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["Profile"])
security = HTTPBearer()


# ── Dependencia para obtener usuario actual ──────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ── Schemas ──────────────────────────────────────────────────────────

class ProfileStats(BaseModel):
    routes: int = 0
    favorites: int = 0
    avg_km: float = 0.0

class ProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    auth_provider: str
    badge: str = "Explorer"
    stats: ProfileStats

    model_config = {"from_attributes": True}

class RecentItem(BaseModel):
    id: str
    name: str
    address: str
    time_ago: str

class FavoriteItem(BaseModel):
    id: str
    name: str
    address: str


# ── GET /api/auth/profile ────────────────────────────────────────────

# ANTES
@router.get("/auth/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return ProfileResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        auth_provider=current_user.auth_provider,
        badge="Explorer",
        stats=ProfileStats(routes=0, favorites=0, avg_km=0.0),
    )

# ── PUT /api/auth/profile ────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None

@router.put("/auth/profile", response_model=UserOut)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name:
        current_user.name = body.name
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


# ── GET /api/history/routes ──────────────────────────────────────────

@router.get("/history/routes")
def get_routes_history(current_user: User = Depends(get_current_user)):
    # TODO: conectar con tabla de rutas cuando esté implementada
    return {
        "routes": [],
        "total": 0
    }


# ── GET /api/favorites ───────────────────────────────────────────────

@router.get("/favorites")
def get_favorites(current_user: User = Depends(get_current_user)):
    # TODO: conectar con tabla de favoritos cuando esté implementada
    return {
        "favorites": [],
        "total": 0
    }


# ── POST /api/favorites ──────────────────────────────────────────────

class AddFavoriteRequest(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float

@router.post("/favorites", status_code=status.HTTP_201_CREATED)
def add_favorite(
    body: AddFavoriteRequest,
    current_user: User = Depends(get_current_user),
):
    # TODO: guardar en BD cuando esté la tabla
    return {"message": "Favorito agregado", "name": body.name}


# ── DELETE /api/favorites/{id} ───────────────────────────────────────

@router.delete("/favorites/{favorite_id}")
def delete_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
):
    # TODO: eliminar de BD
    return {"message": "Favorito eliminado"}
