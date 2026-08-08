from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from dataclasses import asdict

from app.database.database import get_db
from app.models.navigation_route_model import NavigationRoute
from app.models.user_model import User
from app.api.profile_router import get_current_user
from app.services.routing_service import compute_route, NoWalkableRouteError
from app.utils.geo import distance_text

router = APIRouter(prefix="/api/navigation", tags=["Navigation"])


# ── Schemas ──────────────────────────────────────────────────────────

class RouteCreateRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    destination_name: Optional[str] = None

class RecalculateRequest(BaseModel):
    route_id: str
    current_lat: float
    current_lng: float

class RouteIdRequest(BaseModel):
    route_id: str

class PointOut(BaseModel):
    lat: float
    lng: float

class StepOut(BaseModel):
    instruction: str
    turn: str
    lat: float
    lng: float
    distance_to_next_m: float

class RouteOut(BaseModel):
    id: str
    destination_name: Optional[str]
    distance_m: float
    distance_text: str
    duration_s: float
    status: str
    points: List[PointOut]
    steps: List[StepOut]
    created_at: datetime


def _to_route_out(route: NavigationRoute) -> RouteOut:
    return RouteOut(
        id=route.id,
        destination_name=route.destination_name,
        distance_m=route.distance_m,
        distance_text=distance_text(route.distance_m),
        duration_s=route.duration_s,
        status=route.status,
        points=[PointOut(**p) for p in route.points],
        steps=[StepOut(**s) for s in route.steps],
        created_at=route.created_at,
    )


def _get_owned_route(db: Session, route_id: str, user: User) -> NavigationRoute:
    route = db.query(NavigationRoute).filter(NavigationRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    if route.user_id != user.id:
        raise HTTPException(status_code=403, detail="Esta ruta no te pertenece")
    return route


# ── POST /api/navigation/route ───────────────────────────────────────
# FR-10 (ruta más corta) + FR-11 (distancia estimada)

@router.post("/route", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(
    body: RouteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = compute_route(
            db, body.origin_lat, body.origin_lng, body.destination_lat, body.destination_lng
        )
    except NoWalkableRouteError as e:
        raise HTTPException(status_code=422, detail=str(e))

    route = NavigationRoute(
        user_id=current_user.id,
        origin_lat=body.origin_lat,
        origin_lng=body.origin_lng,
        destination_lat=body.destination_lat,
        destination_lng=body.destination_lng,
        destination_name=body.destination_name,
        distance_m=result.distance_m,
        duration_s=result.duration_s,
        points=result.points,
        steps=[asdict(s) for s in result.steps],
        status="calculated",
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return _to_route_out(route)


# ── POST /api/navigation/recalculate ─────────────────────────────────

@router.post("/recalculate", response_model=RouteOut)
def recalculate_route(
    body: RecalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    route = _get_owned_route(db, body.route_id, current_user)

    try:
        result = compute_route(
            db, body.current_lat, body.current_lng, route.destination_lat, route.destination_lng
        )
    except NoWalkableRouteError as e:
        raise HTTPException(status_code=422, detail=str(e))

    route.origin_lat = body.current_lat
    route.origin_lng = body.current_lng
    route.distance_m = result.distance_m
    route.duration_s = result.duration_s
    route.points = result.points
    route.steps = [asdict(s) for s in result.steps]

    db.commit()
    db.refresh(route)
    return _to_route_out(route)


# ── POST /api/navigation/start ───────────────────────────────────────

@router.post("/start", response_model=RouteOut)
def start_route(
    body: RouteIdRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    route = _get_owned_route(db, body.route_id, current_user)
    route.status = "active"
    route.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(route)
    return _to_route_out(route)


# ── POST /api/navigation/finish ──────────────────────────────────────

@router.post("/finish", response_model=RouteOut)
def finish_route(
    body: RouteIdRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    route = _get_owned_route(db, body.route_id, current_user)
    route.status = "finished"
    route.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(route)
    return _to_route_out(route)


# ── GET /api/navigation/history ──────────────────────────────────────

@router.get("/history", response_model=List[RouteOut])
def get_route_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    routes = (
        db.query(NavigationRoute)
        .filter(NavigationRoute.user_id == current_user.id)
        .order_by(NavigationRoute.created_at.desc())
        .limit(20)
        .all()
    )
    return [_to_route_out(r) for r in routes]


# ── GET /api/navigation/{id} ─────────────────────────────────────────

@router.get("/{route_id}", response_model=RouteOut)
def get_route(
    route_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    route = _get_owned_route(db, route_id, current_user)
    return _to_route_out(route)


# ── DELETE /api/navigation/{id} ──────────────────────────────────────

@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    route_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    route = _get_owned_route(db, route_id, current_user)
    db.delete(route)
    db.commit()
