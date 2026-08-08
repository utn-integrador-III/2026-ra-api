import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base


class NavigationRoute(Base):
    __tablename__ = "navigation_routes"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    duration_s: Mapped[float] = mapped_column(Float, nullable=False)

    points: Mapped[list] = mapped_column(JSON, nullable=False)  # [{lat, lng}, ...]
    steps: Mapped[list] = mapped_column(JSON, nullable=False)  # [{instruction, turn, lat, lng, distance_to_next_m}, ...]

    # 'calculated' | 'active' | 'finished' | 'cancelled'
    status: Mapped[str] = mapped_column(String(20), default="calculated", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
