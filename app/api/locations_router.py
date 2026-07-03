from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import math

from app.database.database import get_db
from app.models.location_model import Location
from app.models.user_model import User
from app.api.profile_router import get_current_user

router = APIRouter(prefix="/api/locations", tags=["Locations"])


# ── Schemas ──────────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location_type: str = "classroom"
    latitude: float
    longitude: float
    building: Optional[str] = None
    floor: Optional[str] = None

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    is_active: Optional[bool] = None

class LocationOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    location_type: str
    latitude: float
    longitude: float
    building: Optional[str]
    floor: Optional[str]
    is_active: bool
    distance_m: Optional[float] = None
    distance_text: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Helper: calcular distancia ────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371000  # metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _distance_text(meters: float) -> str:
    if meters < 1000:
        return f"{int(meters)} m"
    return f"{meters/1000:.1f} km"


# ── GET /api/locations ───────────────────────────────────────────────
# Lista todas las ubicaciones (usuarios y admins)

@router.get("/", response_model=List[LocationOut])
def list_locations(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Location).filter(Location.is_active == True)

    if location_type:
        query = query.filter(Location.location_type == location_type)

    if search:
        query = query.filter(
            Location.name.ilike(f"%{search}%") |
            Location.description.ilike(f"%{search}%") |
            Location.building.ilike(f"%{search}%")
        )

    locations = query.all()

    result = []
    for loc in locations:
        out = LocationOut.model_validate(loc)
        if lat and lng:
            dist = _haversine(lat, lng, loc.latitude, loc.longitude)
            out.distance_m = round(dist)
            out.distance_text = _distance_text(dist)
        result.append(out)

    # Ordenar por distancia si se proporcionó ubicación
    if lat and lng:
        result.sort(key=lambda x: x.distance_m or 999999)

    return result


# ── GET /api/locations/nearby ─────────────────────────────────────────
# Ubicaciones cercanas a coordenadas dadas

@router.get("/nearby", response_model=List[LocationOut])
def get_nearby_locations(
    lat: float,
    lng: float,
    radius_m: float = 500,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    locations = db.query(Location).filter(Location.is_active == True).all()

    result = []
    for loc in locations:
        dist = _haversine(lat, lng, loc.latitude, loc.longitude)
        if dist <= radius_m:
            out = LocationOut.model_validate(loc)
            out.distance_m = round(dist)
            out.distance_text = _distance_text(dist)
            result.append(out)

    result.sort(key=lambda x: x.distance_m or 0)
    return result


# ── GET /api/locations/{id} ──────────────────────────────────────────

@router.get("/{location_id}", response_model=LocationOut)
def get_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    return LocationOut.model_validate(loc)


# ── POST /api/locations ──────────────────────────────────────────────
# Solo admins crean ubicaciones

@router.post("/", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    body: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: verificar rol admin cuando se implemente
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Solo admins pueden crear ubicaciones")

    loc = Location(
        name=body.name,
        description=body.description,
        location_type=body.location_type,
        latitude=body.latitude,
        longitude=body.longitude,
        building=body.building,
        floor=body.floor,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return LocationOut.model_validate(loc)


# ── PUT /api/locations/{id} ──────────────────────────────────────────

@router.put("/{location_id}", response_model=LocationOut)
def update_location(
    location_id: str,
    body: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(loc, field, value)

    db.commit()
    db.refresh(loc)
    return LocationOut.model_validate(loc)


# ── DELETE /api/locations/{id} ───────────────────────────────────────

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")

    # Soft delete
    loc.is_active = False
    db.commit()
