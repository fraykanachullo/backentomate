import io
import os
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
from ultralytics import YOLO
import uvicorn

# =====================================================
# CONFIGURACIÓN DEL MODELO
# =====================================================

# Ruta del modelo entrenado
MODEL_PATH = os.getenv("MODEL_PATH", "app/models/best.pt")

# Cargar modelo YOLOv8
model = YOLO(MODEL_PATH)

# Verificar que el modelo cargó correctamente
print(f" Modelo cargado desde: {MODEL_PATH}")
print(f" Clases del modelo: {model.names}")

# =====================================================
# APLICACIÓN FASTAPI
# =====================================================

app = FastAPI(
    title="Tomate Disease Detection API",
    description="API para detección de enfermedades y plagas del tomate - UPEU",
    version="2.0.0"
)

# Configurar CORS para permitir conexiones desde Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ENDPOINTS
# =====================================================

@app.get("/")
async def root():
    return {
        "message": "API de Detección de Enfermedades del Tomate",
        "status": "online",
        "version": "2.0.0",
        "model_classes": model.names
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/classes")
async def get_classes():
    """Retorna la lista de clases que el modelo puede detectar"""
    return {
        "status": "success",
        "data": {
            "classes": list(model.names.values()),
            "total": len(model.names)
        }
    }

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Endpoint para detectar enfermedades en imágenes de tomate
    
    Recibe: Imagen (JPG, PNG, HEIC)
    Retorna: Lista de detecciones con enfermedad, confianza y bounding boxes
    """
    try:
        # 1. Leer la imagen
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_np = np.array(image)
        
        # 2. Obtener dimensiones de la imagen
        height, width = image_np.shape[:2]
        print(f"📐 Dimensiones de la imagen: {width}x{height}")
        
        # 3. Realizar inferencia con YOLO
        results = model(image_np)
        
        # 4. Procesar resultados
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    # Obtener coordenadas
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    
                    # Normalizar coordenadas a [0, 1]
                    x1_norm = round(x1 / width, 4)
                    y1_norm = round(y1 / height, 4)
                    x2_norm = round(x2 / width, 4)
                    y2_norm = round(y2 / height, 4)
                    
                    # Filtrar por confianza mínima (0.25 para pruebas, 0.5 en producción)
                    if confidence > 0.25:
                        detections.append({
                            "disease": class_name,
                            "confidence": round(confidence * 100, 2),
                            "bbox": [x1_norm, y1_norm, x2_norm, y2_norm]
                        })
        
        # 5. Log de resultados
        print(f"🔍 Detecciones encontradas: {len(detections)}")
        if detections:
            print(f"📦 Detecciones: {detections}")
        
        # 6. Preparar respuesta
        response = {
            "status": "success",
            "message": "Diagnóstico completado",
            "data": {
                "detections": detections,
                "total": len(detections),
                "processed_at": datetime.now().isoformat()
            }
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al procesar la imagen: {str(e)}"
        )

# =====================================================
# EJECUCIÓN DEL SERVIDOR
# =====================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )