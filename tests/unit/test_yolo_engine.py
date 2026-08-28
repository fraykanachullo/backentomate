import io
from PIL import Image
from app.services.inference.yolo_engine import engine

def make_image():
    img = Image.new("RGB", (640,640), (0,255,0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return Image.open(buf)

def test_engine_singleton():
    a = engine
    from app.services.inference.yolo_engine import InferenceEngine
    b = InferenceEngine()
    assert a is b

def test_engine_load_and_predict():
    img = make_image()
    results = engine.predict(img)
    assert results is not None
    # Debe tener al menos 1 result
    assert len(results) == 1
    assert hasattr(results[0], "boxes")

def test_engine_names():
    names = engine.names
    assert isinstance(names, dict)
    assert 0 in names
