import io
import os
from datetime import datetime, timezone
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
from ultralytics import YOLO
import uvicorn

from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.core.middleware import RequestIDMiddleware
from app.api.v1.router import api_router
from app.database.session import init_db

# =====================================================
# CARGA DEL MODELO
# =====================================================
MODEL_PATH = settings.model_path
model = YOLO(MODEL_PATH)
print(f"Modelo cargado desde: {MODEL_PATH}")
print(f"Clases del modelo: {model.names}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas si no existen
    await init_db()
    print("DB inicializada")
    yield

# =====================================================
# APP FASTAPI
# =====================================================
app = FastAPI(
    title=settings.app_name,
    description="API para deteccion de enfermedades y plagas del tomate - UPEU",
    version=settings.app_version,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static para uploads locales (fallback cuando Supabase no configurado)
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Router versionado /api/v1
app.include_router(api_router)

# =====================================================
# ENDPOINTS LEGACY (compatibilidad con app actual)
# Se mantienen para no romper la app Flutter existente.
# En Fase A.6 el endpoint canonico sera POST /api/v1/diagnostic/detect
# =====================================================

@app.get("/", tags=["legacy"])
async def root():
    return {
        "message": "API de Deteccion de Enfermedades del Tomate",
        "status": "online",
        "version": settings.app_version,
        "model_classes": model.names,
    }


@app.get("/health", tags=["legacy"])
async def health_legacy():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/classes", tags=["legacy"])
async def get_classes():
    return {
        "status": "success",
        "data": {
            "classes": list(model.names.values()),
            "total": len(model.names),
        },
    }


@app.post("/detect", tags=["legacy"])
async def detect(file: UploadFile = File(...)):
    """
    Endpoint legacy para compatibilidad.
    Recibe: Imagen (JPG, PNG)
    Retorna: Lista de detecciones con enfermedad, confianza y bbox normalizados.
    """
    try:
        contents = await file.read()
        if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"Archivo supera {settings.max_upload_size_mb} MB")

        image = Image.open(io.BytesIO(contents))
        # Validar formato por magic bytes basico: verificar que PIL pudo abrir
        image_np = np.array(image)
        if image_np.size == 0:
            raise HTTPException(status_code=400, detail="Imagen invalida o vacia")

        height, width = image_np.shape[:2]
        if width < 320 or height < 320:
            raise HTTPException(status_code=400, detail="Imagen muy pequena, minimo 320x320")

        print(f"Dimensiones: {width}x{height}")

        results = model(image_np)

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]

                    x1_norm = round(x1 / width, 4)
                    y1_norm = round(y1 / height, 4)
                    x2_norm = round(x2 / width, 4)
                    y2_norm = round(y2 / height, 4)

                    if confidence > settings.confidence_threshold:
                        detections.append({
                            "disease": class_name,
                            "confidence": round(confidence * 100, 2),
                            "bbox": [x1_norm, y1_norm, x2_norm, y2_norm],
                        })

        print(f"Detecciones: {len(detections)}")

        response = {
            "status": "success",
            "message": "Diagnostico completado",
            "data": {
                "detections": detections,
                "total": len(detections),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level,
    )
