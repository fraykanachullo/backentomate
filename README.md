# Tomate Detection API

API FastAPI para detectar enfermedades y plagas del tomate con un modelo YOLOv8n entrenado en Roboflow.

## Modelo verificado

El archivo `app/models/best.pt` se carga como detector YOLO y actualmente contiene estas clases, en este orden exacto:

| ID | Clase |
|---:|---|
| 0 | `mildiu` |
| 1 | `mosca_blanca` |
| 2 | `oidio` |
| 3 | `polilla` |
| 4 | `sana` |

El backend comprueba esta correspondencia al iniciar. Si se cambia `best.pt`, también se debe revisar el orden de clases exportado por Roboflow.

## Configuración de inferencia

Los valores por defecto son:

```env
MODEL_PATH=app/models/best.pt
IMAGE_SIZE=640
CONFIDENCE_THRESHOLD=0.40
IOU_THRESHOLD=0.45
MAX_UPLOAD_SIZE_MB=5
```

`IMAGE_SIZE=640` coincide con el entrenamiento habitual de YOLOv8n. `CONFIDENCE_THRESHOLD=0.40` es un punto inicial; se debe ajustar con imágenes de validación del campo. Para menos falsos positivos, subirlo a `0.50-0.60`; para detectar casos débiles, probar `0.25-0.35`. `IOU_THRESHOLD=0.45` controla la supresión de cajas duplicadas y no reemplaza una validación de precisión/recall.

## Ejecución local

```powershell
venv311\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Servidor: `http://localhost:8000`

## Subir una imagen desde el frontend

Endpoint canónico:

```text
POST /api/v1/diagnostic/detect
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

Campos multipart:

- `file`: obligatorio; JPEG o PNG recomendado, mínimo `320x320`, máximo `5 MB`.
- `metadata`: opcional; texto JSON con `plot_id`, ubicación y datos del dispositivo.

Ejemplo:

```javascript
const form = new FormData();
form.append("file", imageFile);
form.append("metadata", JSON.stringify({
  plot_id: plotId,
  latitude: -16.3,
  longitude: -72.2,
  altitude: 1450,
  gps_accuracy_meters: 8,
  timestamp_utc: new Date().toISOString(),
  device_model: "Android",
  app_version: "1.0.0",
  quality_warning: false
}));

const response = await fetch(`${API_URL}/api/v1/diagnostic/detect`, {
  method: "POST",
  headers: { Authorization: `Bearer ${accessToken}` },
  body: form
});
const diagnostic = await response.json();
```

No se debe establecer manualmente `Content-Type` al usar `FormData`; el navegador agrega el boundary correcto.

## Respuesta para pintar cajas

Cada detección incluye `confidence_score` entre `0` y `1` y una caja normalizada entre `0` y `1` respecto a la imagen original:

```json
{
  "disease_label": "oidio",
  "disease_name_spanish": "Oidío / Cenicilla",
  "confidence_score": 0.87,
  "severity_level": "SEVERE",
  "bounding_box": {
    "x_min": 0.12,
    "y_min": 0.18,
    "x_max": 0.66,
    "y_max": 0.82,
    "coordinate_space": "normalized_0_to_1",
    "reference": "original_image_dimensions"
  }
}
```

Para dibujar sobre un widget de ancho `W` y alto `H`:

```text
left = x_min * W
top = y_min * H
width = (x_max - x_min) * W
height = (y_max - y_min) * H
```

La imagen debe conservar la misma relación de aspecto visible; si el frontend usa `cover`, debe compensar el recorte antes de pintar las cajas.

## Endpoints útiles

- `GET /api/v1/health`: estado básico.
- `GET /classes`: clases detectables, endpoint legacy.
- `POST /detect`: endpoint legacy; usar `/api/v1/diagnostic/detect` para nuevas integraciones.

## Pruebas

```powershell
venv311\Scripts\python.exe -m pytest -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  para correrback

```
