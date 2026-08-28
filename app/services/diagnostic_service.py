import io
import time
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from PIL import Image

from app.services.inference.preprocessor import validate_image
from app.services.inference.yolo_engine import engine
from app.services.inference.postprocessor import build_detections
from app.models.orm.diagnostic import Diagnostic, DiagnosticDetail
from app.models.orm.plot import Plot
from app.storage.supabase_storage import upload_image
from sqlalchemy import select

async def process_diagnostic(
    db: AsyncSession,
    user_id: str,
    image_bytes: bytes,
    metadata: dict,
    filename: str = "image.jpg",
):
    start = time.time()

    # 1. Validar imagen
    pil = validate_image(image_bytes)
    width, height = pil.size

    # 2. Validar plot_id si viene
    plot_id = metadata.get("plot_id")
    if plot_id:
        result = await db.execute(select(Plot).where(Plot.id == plot_id))
        plot = result.scalars().first()
        if not plot:
            raise HTTPException(status_code=400, detail={"code": "INVALID_PLOT", "message": "plot_id no existe"})
        # Opcional: verificar owner? Por ahora permite cualquier plot existente
    else:
        plot = None

    # 3. Inferencia
    # YOLO acepta PIL o numpy; usamos PIL
    try:
        results = engine.predict(pil)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail={"code": "INFERENCE_SERVICE_UNAVAILABLE", "message": str(e), "retry_after": 60})

    # 4. Postprocesar
    from app.core.config import settings
    detections = build_detections(results, width, height, conf_thres=settings.confidence_threshold)

    # 5. Generar IDs y subir imagen
    diagnostic_id = str(uuid.uuid4())
    captured_at_str = metadata.get("timestamp_utc") or metadata.get("timestamp") or datetime.now(timezone.utc).isoformat()
    try:
        captured_at = datetime.fromisoformat(captured_at_str.replace("Z", "+00:00"))
    except:
        captured_at = datetime.now(timezone.utc)

    image_url, storage_path = upload_image(user_id, diagnostic_id, image_bytes, filename)

    # 6. Summary
    has_disease = any(d["disease_label"] != "sana" for d in detections)
    dominant = detections[0] if detections else None

    diagnostic = Diagnostic(
        id=diagnostic_id,
        user_id=user_id,
        plot_id=plot_id,
        image_url=image_url,
        image_storage_path=storage_path,
        latitude=metadata.get("latitude"),
        longitude=metadata.get("longitude"),
        altitude_m=metadata.get("altitude"),
        gps_accuracy_m=metadata.get("gps_accuracy_meters"),
        quality_warning=bool(metadata.get("quality_warning", False)),
        has_disease=has_disease,
        total_detections=len(detections),
        dominant_class=dominant["disease_label"] if dominant else None,
        dominant_confidence=dominant["confidence_score"] if dominant else None,
        processing_time_ms=int((time.time() - start) * 1000),
        model_version="YOLOv8n-tomato-v1",
        device_model=metadata.get("device_model"),
        app_version=metadata.get("app_version"),
        sync_status="synced",
        captured_at=captured_at,
    )
    db.add(diagnostic)
    await db.flush()

    for d in detections:
        detail = DiagnosticDetail(
            diagnostic_id=diagnostic_id,
            disease_label=d["disease_label"],
            disease_scientific=d["disease_name_scientific"],
            confidence_score=d["confidence_score"],
            severity_level=d["severity_level"],
            bounding_box_json=d["bounding_box"],
        )
        db.add(detail)

    # Audit log
    from app.models.orm.audit_log import AuditLog
    db.add(AuditLog(user_id=user_id, action="DIAGNOSTIC_CREATED", target_type="DIAGNOSTIC", target_id=diagnostic_id, details={"detections": len(detections)}))
    await db.commit()

    # 7. Response
    processing_ms = int((time.time() - start) * 1000)
    return {
        "diagnostic_id": diagnostic_id,
        "status": "completed",
        "created_at": diagnostic.created_at.isoformat() if diagnostic.created_at else datetime.now(timezone.utc).isoformat(),
        "processing_time_ms": processing_ms,
        "image_url": image_url,
        "image_dimensions": {"width_px": width, "height_px": height},
        "metadata": {
            "plot_id": plot_id,
            "plot_name": plot.name if plot else None,
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "altitude": metadata.get("altitude"),
            "quality_warning": bool(metadata.get("quality_warning", False)),
            "timestamp_capture_utc": captured_at.isoformat(),
        },
        "model_info": {
            "model_name": "YOLOv8n-tomato-v1",
            "model_version": "1.0.0",
            "inference_backend": "ultralytics",
            "confidence_threshold": 0.40,
            "iou_threshold": 0.45,
        },
        "summary": {
            "total_detections": len(detections),
            "has_disease": has_disease,
            "dominant_class": dominant["disease_label"] if dominant else None,
            "dominant_confidence": dominant["confidence_score"] if dominant else None,
        },
        "detections": [
            {**d, "detection_id": f"det-{i+1:03d}"} for i, d in enumerate(detections)
        ],
    }
