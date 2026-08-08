from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database.database import get_db
from app.models.sidewalk_model import SidewalkNode, SidewalkEdge
from app.models.user_model import User
from app.api.profile_router import get_admin_user
from app.utils.geo import haversine_m

router = APIRouter(prefix="/api/sidewalks", tags=["Sidewalks"])


# ── Schemas ──────────────────────────────────────────────────────────

class NodeCreate(BaseModel):
    latitude: float
    longitude: float

class NodeOut(BaseModel):
    id: str
    latitude: float
    longitude: float

    model_config = {"from_attributes": True}

class EdgeCreate(BaseModel):
    node_a_id: str
    node_b_id: str

class EdgeOut(BaseModel):
    id: str
    node_a_id: str
    node_b_id: str
    distance_m: float
    node_a: NodeOut
    node_b: NodeOut


# ── Nodos ────────────────────────────────────────────────────────────
# Puntos de "acera": invisibles para la app, solo el panel admin y el
# motor de rutas los usan. Todo el router requiere rol admin.

@router.get("/nodes", response_model=List[NodeOut])
def list_nodes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return db.query(SidewalkNode).filter(SidewalkNode.is_active == True).all()


@router.post("/nodes", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
def create_node(
    body: NodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    node = SidewalkNode(latitude=body.latitude, longitude=body.longitude)
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    node = db.query(SidewalkNode).filter(SidewalkNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    # Al borrar un nodo, sus aristas dejan de tener sentido
    db.query(SidewalkEdge).filter(
        (SidewalkEdge.node_a_id == node_id) | (SidewalkEdge.node_b_id == node_id)
    ).delete(synchronize_session=False)

    db.delete(node)
    db.commit()


# ── Aristas ──────────────────────────────────────────────────────────
# Una arista = "se puede caminar en línea recta entre estos dos nodos".

@router.get("/edges", response_model=List[EdgeOut])
def list_edges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    edges = db.query(SidewalkEdge).filter(SidewalkEdge.is_active == True).all()
    nodes = {n.id: n for n in db.query(SidewalkNode).all()}

    result = []
    for e in edges:
        node_a = nodes.get(e.node_a_id)
        node_b = nodes.get(e.node_b_id)
        if not node_a or not node_b:
            continue
        result.append(EdgeOut(
            id=e.id, node_a_id=e.node_a_id, node_b_id=e.node_b_id,
            distance_m=e.distance_m,
            node_a=NodeOut.model_validate(node_a),
            node_b=NodeOut.model_validate(node_b),
        ))
    return result


@router.post("/edges", response_model=EdgeOut, status_code=status.HTTP_201_CREATED)
def create_edge(
    body: EdgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    if body.node_a_id == body.node_b_id:
        raise HTTPException(status_code=400, detail="Un nodo no puede conectarse consigo mismo")

    node_a = db.query(SidewalkNode).filter(SidewalkNode.id == body.node_a_id).first()
    node_b = db.query(SidewalkNode).filter(SidewalkNode.id == body.node_b_id).first()
    if not node_a or not node_b:
        raise HTTPException(status_code=404, detail="Alguno de los nodos no existe")

    existing = db.query(SidewalkEdge).filter(
        SidewalkEdge.is_active == True,
        (
            ((SidewalkEdge.node_a_id == body.node_a_id) & (SidewalkEdge.node_b_id == body.node_b_id)) |
            ((SidewalkEdge.node_a_id == body.node_b_id) & (SidewalkEdge.node_b_id == body.node_a_id))
        ),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una conexión entre estos dos nodos")

    distance = haversine_m(node_a.latitude, node_a.longitude, node_b.latitude, node_b.longitude)

    edge = SidewalkEdge(node_a_id=body.node_a_id, node_b_id=body.node_b_id, distance_m=distance)
    db.add(edge)
    db.commit()
    db.refresh(edge)

    return EdgeOut(
        id=edge.id, node_a_id=edge.node_a_id, node_b_id=edge.node_b_id,
        distance_m=edge.distance_m,
        node_a=NodeOut.model_validate(node_a),
        node_b=NodeOut.model_validate(node_b),
    )


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(
    edge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    edge = db.query(SidewalkEdge).filter(SidewalkEdge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    db.delete(edge)
    db.commit()
