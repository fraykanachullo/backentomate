import time
from ultralytics import YOLO
from app.core.config import settings
from app.services.inference.class_names import CLASS_NAMES

# Intentar pybreaker, fallback a dummy si no está instalado
try:
    import pybreaker
    breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)
except:
    class DummyBreaker:
        def call(self, func, *a, **kw): return func(*a, **kw)
    breaker = DummyBreaker()

class InferenceEngine:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self):
        if self._model is None:
            print(f"[YOLO] Cargando modelo {settings.model_path}")
            self._model = YOLO(settings.model_path)
            print(f"[YOLO] Clases: {self._model.names}")
            model_names = {int(key): value for key, value in self._model.names.items()}
            if model_names != CLASS_NAMES:
                raise RuntimeError(
                    f"Las clases de {settings.model_path} no coinciden con CLASS_NAMES: "
                    f"modelo={model_names}, configuradas={CLASS_NAMES}"
                )

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    @property
    def names(self):
        return self.model.names

    def predict(self, image, conf=None, iou=None, imgsz=None):
        conf = conf if conf is not None else settings.confidence_threshold
        iou = iou if iou is not None else settings.iou_threshold
        imgsz = imgsz if imgsz is not None else settings.image_size
        def _call():
            return self.model(image, conf=conf, iou=iou, imgsz=imgsz, agnostic_nms=True, verbose=False)
        # Si breaker es dummy, call directo; si es pybreaker, usa breaker.call
        try:
            if hasattr(breaker, 'call') and 'pybreaker' in str(type(breaker)):
                return breaker.call(_call)
            else:
                return _call()
        except Exception as e:
            # Si breaker abierto, re-lanzar como 503
            if "Circuit breaker" in str(e) or "open" in str(e).lower():
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail={"code":"INFERENCE_SERVICE_UNAVAILABLE","message":"Modelo no disponible, intente luego","retry_after":60})
            raise

# Singleton global
engine = InferenceEngine()
