from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.database.database import get_db
from app.models.user_model import User
from app.models.place_history_model import PlaceHistory
from app.api.profile_router import get_current_user

router = APIRouter(prefix="/api/history", tags=["History"])


# ── Schemas ──────────────────────────────────────────────────────────

class AddPlaceRequest(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    type: Optional[str] = None

class PlaceHistoryOut(BaseModel):
    id: str
    name: str
    address: Optional[str]
    place_type: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    visited_at: datetime
    time_ago: str

    model_config = {"from_attributes": True}


def _time_ago(dt: datetime) -> str:
    """Convierte datetime a texto relativo: 'Hace 2h', 'Ayer', etc."""
    now = datetime.now(timezone.utc)
    diff = now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt
    seconds = diff.total_seconds()

    if seconds < 3600:
        mins = int(seconds / 60)
        return f"Hace {mins}min" if mins > 1 else "Ahora"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"Hace {hours}h"
    elif seconds < 172800:
        return "Ayer"
    else:
        days = int(seconds / 86400)
        return f"Hace {days}d"


# ── POST /api/history/places ─────────────────────────────────────────
# Flutter llama a este endpoint cuando el usuario selecciona un destino

@router.post("/places", status_code=status.HTTP_201_CREATED)
def add_place_to_history(
    body: AddPlaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Evitar duplicados recientes (mismo lugar en las últimas 2 horas)
    from datetime import timedelta
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    existing = db.query(PlaceHistory).filter(
        PlaceHistory.user_id == current_user.id,
        PlaceHistory.name == body.name,
        PlaceHistory.visited_at >= two_hours_ago,
    ).first()

    if existing:
        # Actualizar timestamp en lugar de duplicar
        existing.visited_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Actualizado en recientes"}

    place = PlaceHistory(
        user_id=current_user.id,
        name=body.name,
        address=body.address,
        place_type=body.type,
        latitude=body.latitude,
        longitude=body.longitude,
    )
    db.add(place)
    db.commit()
    return {"message": "Agregado a recientes"}


# ── GET /api/history/places ──────────────────────────────────────────
# Devuelve los últimos 10 lugares visitados

@router.get("/places")
def get_places_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    places = (
        db.query(PlaceHistory)
        .filter(PlaceHistory.user_id == current_user.id)
        .order_by(PlaceHistory.visited_at.desc())
        .limit(10)
        .all()
    )

    return {
        "places": [
            {
                "id": p.id,
                "name": p.name,
                "address": p.address,
                "place_type": p.place_type,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "visited_at": p.visited_at.isoformat(),
                "time_ago": _time_ago(p.visited_at),
            }
            for p in places
        ],
        "total": len(places),
    }


# ── DELETE /api/history/places ───────────────────────────────────────

@router.delete("/places")
def clear_places_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(PlaceHistory).filter(PlaceHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Historial eliminado"}
