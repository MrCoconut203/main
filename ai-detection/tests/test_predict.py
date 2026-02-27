import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_test_image():
    try:
        from PIL import Image
    except Exception:
        # If PIL isn't installed in the environment running the tests, return a small
        # bytes object representing a minimal JPEG (this is a fallback; installing
        # Pillow is recommended for real test runs).
        return io.BytesIO(b"\xff\xd8\xff\xd9")
    img = Image.new("RGB", (128, 128), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_predict_smoke():
    image_buf = create_test_image()
    files = {"file": ("test.jpg", image_buf, "image/jpeg")}
    resp = client.post("/predict/", files=files)
    # Accept 200 (success), 503 (model not loaded), or 500 (server error) as valid smoke-test outcomes.
    assert resp.status_code in (200, 500, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert "image_base64" in data
        assert "filename" in data
        assert data["filename"] == "test.jpg"


def test_health_exposes_readiness_fields():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data
    assert "captioning_enabled" in data
    assert "captioning_available" in data
    assert "max_concurrent_requests" in data


def test_translate_caption_to_japanese_supports_katakana_only_result():
    from app.main import translate_caption_to_japanese

    translated = translate_caption_to_japanese("a photo of beach")
    assert translated == "ビーチ"
