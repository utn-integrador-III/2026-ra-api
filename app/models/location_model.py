import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tipo: 'classroom', 'lab', 'office', 'cafeteria', 'bathroom', 'parking', 'other'
    location_type: Mapped[str] = mapped_column(String(50), default="classroom")

    # Coordenadas GPS
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Edificio y piso (opcional)
    building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
