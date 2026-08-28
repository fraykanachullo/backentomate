import io
from PIL import Image
import numpy as np
import cv2
from fastapi import HTTPException

MAX_SIZE_MB = 5
MIN_DIM = 320
TARGET_SIZE = 640

# Magic bytes para JPEG/PNG
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"

def validate_magic_bytes(data: bytes):
    if data.startswith(MAGIC_JPEG) or data.startswith(MAGIC_PNG):
        return True
    # También aceptar si PIL puede abrirlo (HEIC etc. pero preferimos JPEG/PNG)
    try:
        Image.open(io.BytesIO(data)).verify()
        return True
    except:
        return False

def validate_image(data: bytes, max_mb: int = MAX_SIZE_MB):
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE", "message": f"Supera {max_mb} MB", "max_size_mb": max_mb})
    if not validate_magic_bytes(data):
        raise HTTPException(status_code=400, detail={"code": "INVALID_IMAGE", "message": "No es JPEG/PNG valido"})
    try:
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if w < MIN_DIM or h < MIN_DIM:
            raise HTTPException(status_code=400, detail={"code": "INVALID_IMAGE", "message": f"Imagen muy pequena {w}x{h}, minimo {MIN_DIM}x{MIN_DIM}"})
        return img
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_IMAGE", "message": f"Imagen invalida: {e}"})

def letterbox(img: np.ndarray, new_shape=(640, 640), color=(114, 114, 114)):
    """Redimensiona con relleno preservando aspecto (Ultralytics letterbox)."""
    shape = img.shape[:2]  # h, w
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, r, (dw, dh)

def preprocess_image(pil_image: Image.Image, target_size: int = TARGET_SIZE):
    """Convierte PIL a array listo para YOLO (solo para validar, YOLO acepta PIL directo)."""
    img = np.array(pil_image.convert("RGB"))
    # OpenCV usa BGR, pero YOLO maneja RGB; aquí solo hacemos letterbox para validación
    letterboxed, ratio, pad = letterbox(img, (target_size, target_size))
    # Normalización a float32 se hace dentro de Ultralytics; aquí solo retornamos metadata
    return letterboxed, ratio, pad
