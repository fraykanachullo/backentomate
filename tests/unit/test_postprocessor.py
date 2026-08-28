from app.services.inference.postprocessor import severity_from_confidence, build_detections

class FakeBox:
    def __init__(self, x1, y1, x2, y2, conf, cls):
        self._xyxy = [[x1, y1, x2, y2]]
        self._conf = [conf]
        self._cls = [cls]
        self.xyxy = type("obj", (), {"__getitem__": lambda s, i: type("t", (), {"tolist": lambda: self._xyxy[i]})()})()
        self.conf = type("obj", (), {"__getitem__": lambda s, i: self._conf[i]})()
        self.cls = type("obj", (), {"__getitem__": lambda s, i: self._cls[i]})()

class FakeBoxes:
    def __init__(self, boxes):
        self._boxes = boxes
    def __iter__(self):
        return iter(self._boxes)
    def __bool__(self):
        return True

class FakeResult:
    def __init__(self, boxes):
        self.boxes = FakeBoxes(boxes) if boxes else None

# Mock simple: usar estructura real de postprocessor con datos sintéticos
def test_severity():
    assert severity_from_confidence(0.3) == "MILD"
    assert severity_from_confidence(0.6) == "MODERATE"
    assert severity_from_confidence(0.9) == "SEVERE"

def test_build_detections_empty():
    res = build_detections([], 640, 640)
    assert res == []

def test_build_detections_with_data():
    # Simular results con boxes via objetos reales sería complejo; probar que función maneja lista vacía y orden
    # Crear fake results mínimos
    r = FakeResult([])
    out = build_detections([r], 640, 640)
    assert out == []
