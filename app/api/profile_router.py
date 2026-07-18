from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_db
from app.models.user_model import User
from app.core.security import decode_access_token
from app.schemas.auth_schemas import UserOut
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api", tags=["Profile"])
security = HTTPBearer()


# ── Dependencia: usuario actual ──────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ── Dependencia: solo admins ─────────────────────────────────────────

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado — se requiere rol de administrador"
        )
    return current_user


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
    role: str
    badge: str = "Explorer"
    stats: ProfileStats
    model_config = {"from_attributes": True}

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None

class AddFavoriteRequest(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


# ── GET /api/auth/profile ────────────────────────────────────────────

@router.get("/auth/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return ProfileResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        auth_provider=current_user.auth_provider,
        role=current_user.role,
        badge="Admin" if current_user.role == "admin" else "Explorer",
        stats=ProfileStats(routes=0, favorites=0, avg_km=0.0),
    )


# ── PUT /api/auth/profile ────────────────────────────────────────────

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
    return {"routes": [], "total": 0}


# ── GET /api/favorites ───────────────────────────────────────────────

@router.get("/favorites")
def get_favorites(current_user: User = Depends(get_current_user)):
    return {"favorites": [], "total": 0}


# ── POST /api/favorites ──────────────────────────────────────────────

@router.post("/favorites", status_code=status.HTTP_201_CREATED)
def add_favorite(body: AddFavoriteRequest, current_user: User = Depends(get_current_user)):
    return {"message": "Favorito agregado", "name": body.name}


# ── DELETE /api/favorites/{id} ───────────────────────────────────────

@router.delete("/favorites/{favorite_id}")
def delete_favorite(favorite_id: str, current_user: User = Depends(get_current_user)):
    return {"message": "Favorito eliminado"}


# ── GET /api/admin/users — solo admins ──────────────────────────────

@router.get("/admin/users")
def list_users(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "auth_provider": u.auth_provider,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


# ── PUT /api/admin/users/{id}/role — cambiar rol ─────────────────────

@router.put("/admin/users/{user_id}/role")
def change_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Rol inválido. Usar 'user' o 'admin'")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.role = role
    db.commit()
    return {"message": f"Rol actualizado a '{role}'", "user_id": user_id}