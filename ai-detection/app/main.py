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

# Serve frontend static files so the same container image can serve the SPA
# (useful for single-image deployments like Render). Mount static files under
# `/static` so API routes (like /predict/) are not shadowed by StaticFiles which
# only supports GET/HEAD and would return 405 for POST requests. We also add
# explicit routes to serve `index.html` for the SPA root and fallback.
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    from fastapi.responses import FileResponse

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(frontend_path / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # If the requested file exists in the frontend folder, serve it. Otherwise
        # return index.html so the SPA client-side router can handle the path.
        requested = frontend_path / full_path
        if requested.exists() and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_path / "index.html")

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
async def predict_options():
    return PlainTextResponse("ok", status_code=200)


@app.get("/predict/")
async def predict_get():
    # Helpful message for GET requests (not used for actual prediction)
    return {"detail": "Use POST /predict/ with multipart/form-data field 'file' to upload an image."}


@app.post("/predict/", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    # Tạo một thư mục tạm thời duy nhất cho mỗi request
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        # Tạo tên file duy nhất để tránh xung đột
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        input_image_path = temp_dir / unique_filename

        try:
            # Lưu file upload
            with open(input_image_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Predict
            if model is None:
                # Model not available yet (startup failure or still loading)
                raise HTTPException(status_code=503, detail="Model not loaded yet")

            results = model.predict(str(input_image_path), save=True, project=temp_dir, name="results", exist_ok=True)
            result = results[0]

            # Lấy tốc độ xử lý
            speed = getattr(result, "speed", {})
            try:
                speed_text = f"{speed.get('preprocess',0):.1f}ms preprocess, {speed.get('inference',0):.1f}ms inference, {speed.get('postprocess',0):.1f}ms postprocess"
            except Exception:
                speed_text = ""

            # Xử lý kết quả
            summary, description = process_prediction_results(result, speed_text)

            # Lấy ảnh kết quả và mã hóa
            result_image_path = Path(result.save_dir) / unique_filename
            encoded_image = encode_image_to_base64(result_image_path)

            return PredictionResponse(
                filename=file.filename,
                description=description,
                details=summary,
                speed=speed,
                image_base64=encoded_image,
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi khi xử lý ảnh: {e}")
