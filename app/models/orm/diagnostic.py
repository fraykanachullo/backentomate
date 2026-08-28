from datetime import datetime
from sqlalchemy import String, Boolean, Text, Float, SmallInteger, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.orm.base import Base, generate_uuid

class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    plot_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("plots.id", ondelete="SET NULL"), nullable=True, index=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_storage_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_disease: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_detections: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    dominant_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dominant_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(10), nullable=False, default="synced")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    details: Mapped[list["DiagnosticDetail"]] = relationship("DiagnosticDetail", back_populates="diagnostic", cascade="all, delete-orphan")


class DiagnosticDetail(Base):
    __tablename__ = "diagnostic_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    diagnostic_id: Mapped[str] = mapped_column(String(36), ForeignKey("diagnostics.id", ondelete="CASCADE"), nullable=False, index=True)
    disease_label: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    disease_scientific: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity_level: Mapped[str] = mapped_column(String(10), nullable=False)  # MILD | MODERATE | SEVERE
    bounding_box_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    diagnostic: Mapped["Diagnostic"] = relationship("Diagnostic", back_populates="details")
