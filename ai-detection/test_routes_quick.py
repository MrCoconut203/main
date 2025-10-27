"""Quick test to verify routing works correctly (POST /predict/ should not 405)"""
from fastapi.testclient import TestClient
import sys
import os

# Add parent to path so we can import app
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app

client = TestClient(app)

def test_health():
    """Health check should return 200"""
    resp = client.get("/health")
    print(f"GET /health -> {resp.status_code}")
    assert resp.status_code == 200

def test_predict_options():
    """OPTIONS /predict/ should return 200 (CORS preflight)"""
    resp = client.options("/predict/")
    print(f"OPTIONS /predict/ -> {resp.status_code}")
    assert resp.status_code == 200

def test_predict_get():
    """GET /predict/ should return helpful message"""
    resp = client.get("/predict/")
    print(f"GET /predict/ -> {resp.status_code}")
    assert resp.status_code == 200

def test_predict_post_no_file():
    """POST /predict/ without file should return 422 (validation error), NOT 405"""
    resp = client.post("/predict/")
    print(f"POST /predict/ (no file) -> {resp.status_code}")
    # Should be 422 (Unprocessable Entity) because 'file' is required
    # If we get 405, routing is broken
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code} - routing may be broken!"

def test_predict_post_with_mock_file():
    """POST /predict/ with mock file should reach handler (may 503 if model not loaded, or 400 if decode fails)"""
    files = {"file": ("test.jpg", b"\xff\xd8\xff\xd9", "image/jpeg")}  # minimal JPEG
    resp = client.post("/predict/", files=files)
    print(f"POST /predict/ (with file) -> {resp.status_code}")
    # Acceptable: 200 (success), 503 (model not ready), 400 (bad image), 500 (other error)
    # NOT acceptable: 405 (method not allowed)
    assert resp.status_code != 405, f"Got 405 - POST handler not registered correctly!"
    print(f"  -> Response: {resp.json() if resp.status_code != 500 else resp.text[:200]}")

if __name__ == "__main__":
    print("=== Testing route registration ===")
    test_health()
    test_predict_options()
    test_predict_get()
    test_predict_post_no_file()
    test_predict_post_with_mock_file()
    print("\n✅ All routing tests passed! POST /predict/ is correctly registered.")
