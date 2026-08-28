from datetime import datetime
from sqlalchemy import String, Boolean, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.orm.base import Base, generate_uuid

class Plot(Base):
    __tablename__ = "plots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    crop_type: Mapped[str] = mapped_column(String(50), nullable=False, default="tomate")
    owner_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
