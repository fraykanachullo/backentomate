import io, json
from PIL import Image
import pytest

def make_img(size=(640,640), color=(50,100,50)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@pytest.mark.asyncio
async def test_detect_no_auth(client):
    img = make_img()
    r = await client.post("/api/v1/diagnostic/detect", files={"file": ("img.jpg", img, "image/jpeg")})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_detect_with_auth(client, user_token, plot_id):
    img = make_img()
    meta = {"plot_id": plot_id, "latitude": -16.3, "longitude": -72.2, "quality_warning": False}
    r = await client.post("/api/v1/diagnostic/detect", files={"file": ("img.jpg", img, "image/jpeg")}, data={"metadata": json.dumps(meta)}, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert "diagnostic_id" in j
    assert "detections" in j and "summary" in j and "model_info" in j
    did = j["diagnostic_id"]
    # get by id
    r2 = await client.get(f"/api/v1/diagnostic/{did}", headers={"Authorization": f"Bearer {user_token}"})
    assert r2.status_code == 200
    # list
    r3 = await client.get("/api/v1/diagnostic", headers={"Authorization": f"Bearer {user_token}"})
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)

@pytest.mark.asyncio
async def test_detect_invalid_image(client, user_token):
    r = await client.post("/api/v1/diagnostic/detect", files={"file": ("bad.txt", b"not an image", "image/jpeg")}, data={"metadata": json.dumps({})}, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_detect_invalid_plot(client, user_token):
    img = make_img()
    meta = {"plot_id": "00000000-0000-0000-0000-000000000000"}
    r = await client.post("/api/v1/diagnostic/detect", files={"file": ("img.jpg", img, "image/jpeg")}, data={"metadata": json.dumps(meta)}, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_legacy_detect_still_works(client):
    img = make_img()
    r = await client.post("/detect", files={"file": ("img.jpg", img, "image/jpeg")})
    assert r.status_code == 200
    assert "data" in r.json()

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    r = await client.get("/api/v1/health/detailed")
    assert r.status_code == 200
    assert "checks" in r.json()
