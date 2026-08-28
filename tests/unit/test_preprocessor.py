import io
from PIL import Image
import pytest
from fastapi import HTTPException
from app.services.inference.preprocessor import validate_image, letterbox

def make_jpeg(size=(640,640), color=(10,20,30)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_validate_image_ok():
    data = make_jpeg((640,640))
    img = validate_image(data)
    assert img.size == (640,640)

def test_validate_image_too_small():
    data = make_jpeg((100,100))
    with pytest.raises(HTTPException) as e:
        validate_image(data)
    assert e.value.status_code == 400

def test_validate_image_too_large():
    data = make_jpeg((640,640))
    # fake large by padding (real content less, but we test size check via small max)
    with pytest.raises(HTTPException) as e:
        validate_image(data, max_mb=0)  # 0 MB -> always too large
    assert e.value.status_code == 413

def test_validate_image_invalid():
    with pytest.raises(HTTPException) as e:
        validate_image(b"not an image")
    assert e.value.status_code == 400

def test_letterbox():
    import numpy as np
    arr = np.zeros((400, 600, 3), dtype=np.uint8)
    out, ratio, pad = letterbox(arr, (640, 640))
    assert out.shape[0] == 640 and out.shape[1] == 640
    assert 0.9 < ratio < 1.1
