"""Metadatos del modelo activo (metadata.json junto a best.pt).

Al cambiar de modelo se reemplazan best.pt y metadata.json; el backend reporta la
version en cada diagnostico y valida que las clases coincidan con el modelo.
"""
import json
from pathlib import Path

from app.core.config import settings
from app.services.inference.class_names import CLASS_NAMES

_path = Path(settings.model_path).parent / "metadata.json"

if _path.exists():
    MODEL_INFO = json.loads(_path.read_text(encoding="utf-8"))
else:
    MODEL_INFO = {
        "name": "tomate-majes",
        "version": "desconocida",
        "architecture": "YOLO",
        "classes": [CLASS_NAMES[i] for i in sorted(CLASS_NAMES)],
    }

# Columna diagnostics.model_version es String(20): "YOLOv8n-v1.0.0"
MODEL_LABEL = f"{MODEL_INFO.get('architecture', 'YOLO')}-v{MODEL_INFO.get('version', '?')}"[:20]

if MODEL_INFO["classes"] != [CLASS_NAMES[i] for i in sorted(CLASS_NAMES)]:
    raise RuntimeError(
        f"metadata.json tiene clases {MODEL_INFO['classes']} distintas a CLASS_NAMES {CLASS_NAMES}"
    )
