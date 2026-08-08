import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base


class SidewalkNode(Base):
    """Punto de conexión de una acera. No es un POI: es invisible para la
    app de usuarios finales, solo lo gestiona el panel admin y lo usa el
    motor de rutas (app/services/routing_service.py) para armar el grafo
    caminable del campus."""

    __tablename__ = "sidewalk_nodes"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SidewalkEdge(Base):
    """Conexión caminable entre dos SidewalkNode (bidireccional). La
    existencia de esta arista es lo que le dice al motor de rutas
    'se puede caminar en línea recta entre estos dos puntos'."""

    __tablename__ = "sidewalk_edges"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    node_a_id: Mapped[str] = mapped_column(String, ForeignKey("sidewalk_nodes.id"), nullable=False)
    node_b_id: Mapped[str] = mapped_column(String, ForeignKey("sidewalk_nodes.id"), nullable=False)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
