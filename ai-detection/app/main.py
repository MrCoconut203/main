from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Tạo model lúc khởi động (đường dẫn có thể cấu hình qua biến môi trường)
model = YOLO(MODEL_PATH)

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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi khi xử lý ảnh: {e}")
