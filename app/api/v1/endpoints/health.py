from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone

from app.database.session import get_db
from app.services.inference.yolo_engine import engine
from app.services.inference.model_info import MODEL_INFO

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "up",
            "model": "loaded" if engine._model is not None else "not_loaded",
            "database": "pending",
            "storage": "local_fallback",
        },
    }

@router.get("/health/detailed")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    checks = {}
    # DB
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "up", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "down", "error": str(e)}
    # Model
    try:
        names = engine.names
        checks["model"] = {"status": "loaded", "classes": list(names.values()) if isinstance(names, dict) else list(names), "info": MODEL_INFO}
    except Exception as e:
        checks["model"] = {"status": "down", "error": str(e)}
    # Storage
    from app.core.config import settings
    checks["storage"] = {"status": "configured" if "supabase" not in settings.supabase_url else "local_fallback", "bucket": settings.supabase_bucket}
    overall = "healthy" if all(v.get("status") in ("up", "loaded", "configured", "local_fallback") for v in checks.values()) else "degraded"
    return {"status": overall, "timestamp": datetime.now(timezone.utc).isoformat(), "checks": checks}
