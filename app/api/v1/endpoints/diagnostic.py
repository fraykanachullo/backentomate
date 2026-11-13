import json
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.services.diagnostic_service import process_diagnostic
from sqlalchemy import select, desc
from app.models.orm.diagnostic import Diagnostic, DiagnosticDetail

router = APIRouter()

@router.post("/detect")
async def detect(
    request: Request,
    file: UploadFile = File(..., description="Imagen JPEG/PNG"),
    metadata: Optional[str] = Form(None, description="JSON string con plot_id, lat/lng, etc."),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
):
    # Parse metadata
    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except:
            raise HTTPException(status_code=400, detail={"code": "INVALID_METADATA", "message": "metadata no es JSON valido"})

    # Validar content-type
    if file.content_type not in ("image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif", None):
        # Permitir pero validar magic bytes luego
        pass

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail={"code": "INVALID_IMAGE", "message": "Archivo vacio"})

    result = await process_diagnostic(
        db=db,
        user_id=payload["user_id"],
        image_bytes=image_bytes,
        metadata=meta,
        filename=file.filename or "image.jpg",
    )
    return result

@router.get("/{diagnostic_id}")
async def get_diagnostic(diagnostic_id: str, db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user)):
    result = await db.execute(select(Diagnostic).where(Diagnostic.id == diagnostic_id))
    diag = result.scalars().first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnostico no encontrado")
    # RBAC: solo propietario o ADMIN
    if diag.user_id != payload["user_id"] and payload.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Permiso denegado")
    result = await db.execute(select(DiagnosticDetail).where(DiagnosticDetail.diagnostic_id == diagnostic_id))
    details = result.scalars().all()
    return {
        "diagnostic_id": diag.id,
        "user_id": diag.user_id,
        "plot_id": diag.plot_id,
        "image_url": diag.image_url,
        "has_disease": diag.has_disease,
        "total_detections": diag.total_detections,
        "dominant_class": diag.dominant_class,
        "created_at": diag.created_at.isoformat() if diag.created_at else None,
        "captured_at": diag.captured_at.isoformat() if diag.captured_at else None,
        "detections": [
            {
                "disease_label": d.disease_label,
                "confidence_score": d.confidence_score,
                "severity_level": d.severity_level,
                "bounding_box": d.bounding_box_json,
            } for d in details
        ],
    }

@router.get("")
async def list_diagnostics(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    mine: bool = False,
):
    # FIELD_TECH solo ve suyos, ADMIN ve todos (mine=true: solo los propios, p.ej.
    # para descargar el historial al celular)
    q = select(Diagnostic).order_by(desc(Diagnostic.created_at)).limit(min(limit, 200)).offset(offset)
    if payload.get("role") != "ADMIN" or mine:
        q = q.where(Diagnostic.user_id == payload["user_id"])
    result = await db.execute(q)
    diags = result.scalars().all()
    details = {}
    if diags:
        rows = await db.execute(select(DiagnosticDetail).where(DiagnosticDetail.diagnostic_id.in_([d.id for d in diags])))
        for det in rows.scalars().all():
            details.setdefault(det.diagnostic_id, []).append({
                "disease_label": det.disease_label,
                "confidence_score": det.confidence_score,
                "bounding_box": det.bounding_box_json,
            })
    return [
        {
            "diagnostic_id": d.id,
            "has_disease": d.has_disease,
            "total_detections": d.total_detections,
            "dominant_class": d.dominant_class,
            "dominant_confidence": d.dominant_confidence,
            "image_url": d.image_url,
            "model_version": d.model_version,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "captured_at": d.captured_at.isoformat() if d.captured_at else None,
            "detections": details.get(d.id, []),
        } for d in diags
    ]
