
---

## 📄 **README.md para el BACKEND**

```powershell
notepad D:\tomate_backend\README.md



# 🍅 Tomate Detection App - Backend

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-8.3.0-red.svg)

Backend para la detección de enfermedades y plagas en cultivos de tomate, utilizando FastAPI y YOLOv8.

---

## 🚀 **Descripción**

Este backend proporciona una API REST para la inferencia de enfermedades en imágenes de tomate. Utiliza un modelo YOLOv8 entrenado con un dataset de 4,602 imágenes recolectadas en campo (Majes, Arequipa).

### 🎯 **Características Principales**

- ✅ **Inferencia con YOLOv8** (GPU/CPU)
- ✅ **API REST** con FastAPI
- ✅ **CORS habilitado** para conexión con Flutter
- ✅ **Soporte para múltiples formatos** (JPG, PNG, HEIC)
- ✅ **Respuesta en JSON** con bounding boxes
- ✅ **Optimizado para zonas áridas** (Majes, Arequipa)

---

## 🏗️ **Arquitectura del Proyecto**
app/
├── main.py # Punto de entrada de la API
├── models/
│ └── best.pt # Modelo YOLOv8 entrenado
└── services/
└── inference.py # Servicio de inferencia

models/ # Modelos de Deep Learning
├── best.pt # Modelo principal (6.0 MB)
├── best.onnx # Modelo en formato ONNX
├── best_int8.tflite # Modelo para móvil (3.1 MB)
└── configs/
├── dataset.yaml # Configuración del dataset
└── class_mapping.json # Mapeo de clases


---

## 🔧 **Requisitos Previos**

| Software | Versión |
|----------|---------|
| **Python** | 3.11 o superior |
| **pip** | Última versión |
| **Git** | (Opcional) |

---

## 📦 **Instalación y Configuración**

### **1. Clonar el repositorio**

```bash
git clone https://github.com/fraykanachullo/BackendAPPTOMATE.git
cd BackendAPPTOMATE



Crear entorno virtual
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate


*** Instalar dependencias ****
pip install -r requirements.txt



 Verificar el modelo
Asegúrate que el archivo app/models/best.pt exista. Si no, descárgalo o coloca tu modelo entrenado.

5. Ejecutar el servidor
bash
python app/main.py
Verás:

text
✅ Modelo cargado desde: app/models/best.pt
✅ Clases del modelo: {0: 'mildiu', 1: 'mosca_blanca', 2: 'oidio', 3: 'polilla', 4: 'sana'}
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
📡 Endpoints de la API
GET /health
Verifica el estado del servidor.

Respuesta:

json
{"status": "healthy"}
GET /classes
Obtiene las clases que el modelo puede detectar.

Respuesta:

json
{
  "status": "success",
  "data": {
    "classes": ["mildiu", "mosca_blanca", "oidio", "polilla", "sana"],
    "total": 5
  }
}
POST /detect
Envía una imagen para diagnóstico.

Request:

Método: POST

Content-Type: multipart/form-data

Body: file (imagen en JPG, PNG o HEIC)

Respuesta (200 OK):

json
{
  "status": "success",
  "message": "Diagnóstico completado",
  "data": {
    "detections": [
      {
        "disease": "mildiu",
        "confidence": 67.45,
        "bbox": [0.0271, 0.7435, 0.145, 0.8572]
      }
    ],
    "total": 1,
    "processed_at": "2026-06-30T17:52:45.056358"
  }
}
🚀 Comandos Útiles
Comando	Descripción
python app\main.py	Ejecutar el servidor
CTRL + C	Detener el servidor
pip install -r requirements.txt	Instalar dependencias
venv\Scripts\activate	Activar entorno virtual
📁 Estructura de Carpetas
text
app/
├── main.py                        # ✅ Punto de entrada
├── models/
│   └── best.pt                    # ✅ Modelo YOLOv8
└── services/
    └── inference.py               # Servicio de inferencia

models/                            # Modelos de Deep Learning
├── best.pt                        # Modelo principal (6.0 MB)
├── best.onnx                      # Modelo en formato ONNX
├── best_int8.tflite               # Modelo para móvil (3.1 MB)
└── configs/
    ├── dataset.yaml               # Configuración del dataset
    └── class_mapping.json         # Mapeo de clases
📊 Clases Detectables
Clase	Nombre Científico	Tipo
mildiu	Phytophthora infestans	Enfermedad
mosca_blanca	Bemisia tabaci	Plaga
oidio	Leveillula taurica	Enfermedad
polilla	Tuta absoluta	Plaga
sana	-	Saludable
🛠️ Tecnologías Utilizadas
Tecnología	Versión	Uso
Python	3.11	Lenguaje principal
FastAPI	0.115.6	Framework web
Uvicorn	0.34.0	Servidor ASGI
YOLOv8	8.3.0	Modelo de detección
PyTorch	2.5.1	Deep Learning
OpenCV	4.10.0	Procesamiento de imágenes
Pillow	11.0.0	Manipulación de imágenes