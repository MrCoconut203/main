from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ultralytics import YOLO
from pathlib import Path
from typing import Dict, Any, Tuple
import shutil
import base64
import tempfile
import uuid
import os


# --- Cấu hình ---
MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov8s.pt")
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")


# --- Định nghĩa response ---
class PredictionResponse(BaseModel):
    filename: str
    description: str
    details: Dict[str, int]
    speed: Dict[str, float]
    image_base64: str


app = FastAPI()

# Model is loaded lazily at startup to avoid importing heavy ML deps at module import time.
# This makes tests and lightweight tools importable without requiring torch/ultralytics.
model = None


@app.on_event("startup")
def load_model_on_startup():
    global model
    try:
        from ultralytics import YOLO
        model = YOLO(MODEL_PATH)
    except Exception as e:
        # Log a warning; server can still start but /predict/ will return 503 until model is loaded.
        import logging
        logging.warning("Failed to load YOLO model on startup: %s", e)
    # Log the PORT environment variable to help debugging on Render
    import os, logging
    logging.info("Startup: effective PORT=%s", os.getenv("PORT", "(not set)"))

# CORS
if ALLOWED_ORIGINS == "*":
    allow_origins = ["*"]
else:
    # phân tách danh sách origin nếu cần
    allow_origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple request logging middleware to help debug Method/Path/Origin on Render
@app.middleware("http")
async def log_requests(request, call_next):
    import logging
    client = request.client.host if request.client else "-"
    logging.info("Incoming request %s %s from %s", request.method, request.url.path, client)
    logging.debug("Request headers: %s", dict(request.headers))
    response = await call_next(request)
    logging.info("Response %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


def process_prediction_results(result: Any, speed_text: str) -> Tuple[Dict[str, int], str]:
    """Xử lý kết quả từ model YOLO để lấy summary và description."""
    # result.boxes.cls có thể là tensor; chuyển thành list
    detected_names = []
    try:
        detected_names = [result.names[int(c)] for c in result.boxes.cls]
    except Exception:
        # fallback: không tìm thấy boxes
        detected_names = []

    summary: Dict[str, int] = {}
    for name in detected_names:
        summary[name] = summary.get(name, 0) + 1

    if summary:
        object_text = ", ".join([f"{v} {k}" for k, v in summary.items()])
        description = f"Ảnh có {object_text}. Tốc độ: {speed_text}"
    else:
        description = f"Không phát hiện đối tượng nào trong ảnh. Tốc độ: {speed_text}"

    return summary, description


def encode_image_to_base64(image_path: Path) -> str:
    """Đọc file ảnh và mã hóa sang chuỗi base64."""
    if not image_path.exists():
        raise FileNotFoundError("Không tìm thấy ảnh kết quả.")
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


@app.get("/health")
async def health():
    return {"status": "ok"}


# OPTIONS handler to satisfy CORS preflight or probes that may hit /predict/
from fastapi.responses import PlainTextResponse


@app.options("/predict/")
async def predict_options_slash():
    return PlainTextResponse("ok", status_code=200)


@app.options("/predict")
async def predict_options_no_slash():
    return PlainTextResponse("ok", status_code=200)


@app.get("/predict/")
async def predict_get_slash():
    # Helpful message for GET requests (not used for actual prediction)
    return {"detail": "Use POST /predict/ with multipart/form-data field 'file' to upload an image."}


@app.get("/predict")
async def predict_get_no_slash():
    return {"detail": "Use POST /predict/ with multipart/form-data field 'file' to upload an image."}


@app.post("/predict/", response_model=PredictionResponse)
async def predict_slash(file: UploadFile = File(...)):
    """
    Xử lý inference với YOLO - tối ưu cho Render (tránh disk I/O, timeout).
    Ưu tiên xử lý in-memory; fallback sang disk nếu cần.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        import numpy as np
        import cv2
        import io

        # Đọc toàn bộ file vào memory
        contents = await file.read()
        
        # Thử decode trực tiếp bằng OpenCV (in-memory, nhanh hơn disk I/O)
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Cannot decode image. Please upload a valid image file.")

        # Predict trực tiếp từ numpy array (không save, nhanh hơn)
        results = model.predict(img, save=False, verbose=False)
        result = results[0]

        # Lấy tốc độ xử lý
        speed = getattr(result, "speed", {})
        try:
            speed_text = f"{speed.get('preprocess',0):.1f}ms preprocess, {speed.get('inference',0):.1f}ms inference, {speed.get('postprocess',0):.1f}ms postprocess"
        except Exception:
            speed_text = ""

        # Xử lý kết quả
        summary, description = process_prediction_results(result, speed_text)

        # Vẽ bounding boxes trực tiếp trên ảnh (in-memory)
        plotted_img = result.plot()  # trả về numpy array với boxes đã vẽ
        
        # Encode sang JPEG in-memory
        _, buffer = cv2.imencode('.jpg', plotted_img)
        encoded_image = base64.b64encode(buffer).decode('utf-8')

        return PredictionResponse(
            filename=file.filename or "uploaded_image.jpg",
            description=description,
            details=summary,
            speed=speed,
            image_base64=encoded_image,
        )

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error("Inference error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi khi xử lý ảnh: {str(e)}")


@app.post("/predict", response_model=PredictionResponse)
async def predict_no_slash(file: UploadFile = File(...)):
    """Redirect to main handler with trailing slash for consistency"""
    return await predict_slash(file)


# ============================================================================
# SPA Frontend serving (registered AFTER all API routes)
# ============================================================================
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    from fastapi.responses import FileResponse
    
    # Mount static files under /static for explicit asset paths
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        """Serve index.html at root"""
        return FileResponse(frontend_path / "index.html")
    
    @app.get("/index.html", include_in_schema=False)
    async def index_html():
        """Explicit route for index.html"""
        return FileResponse(frontend_path / "index.html")
