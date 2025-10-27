from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ultralytics import YOLO
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import shutil
import base64
import tempfile
import uuid
import os
import time


# --- Cấu hình ---
MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov8s.pt")
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")
ENABLE_CAPTIONING = os.getenv("ENABLE_CAPTIONING", "true").lower() == "true"


# --- Định nghĩa response ---
class PredictionResponse(BaseModel):
    filename: str
    description: str  # Mô tả chi tiết bằng tiếng Nhật
    yolo_summary: str  # Tóm tắt YOLO detection
    object_count: int  # Tổng số vật thể
    object_details: Dict[str, int]  # Chi tiết từng loại
    processing_time: float  # Thời gian xử lý (giây)
    inference_speed: Dict[str, float]  # Tốc độ inference (ms)
    image_base64: str


app = FastAPI()

# Models loaded at startup
model = None
captioner = None
caption_processor = None


@app.on_event("startup")
def load_model_on_startup():
    global model, captioner, caption_processor
    import logging
    
    # Load YOLO
    try:
        from ultralytics import YOLO
        model = YOLO(MODEL_PATH)
        logging.info("✓ YOLO model loaded successfully")
    except Exception as e:
        logging.warning("Failed to load YOLO model on startup: %s", e)
    
    # Load BLIP-2 for image captioning (optional, can be disabled via env var)
    if ENABLE_CAPTIONING:
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            logging.info("Loading BLIP captioning model...")
            caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            captioner = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            logging.info("✓ BLIP captioning model loaded successfully")
        except Exception as e:
            logging.warning("Failed to load BLIP captioning model: %s. Captioning will be disabled.", e)
            captioner = None
    else:
        logging.info("Image captioning disabled via ENABLE_CAPTIONING=false")
    
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


def generate_scene_description(img_array, detected_objects: Dict[str, int]) -> str:
    """
    Tạo mô tả chi tiết khung cảnh ảnh bằng tiếng Nhật.
    Kết hợp BLIP caption (nếu có) và YOLO detection.
    """
    import logging
    
    # Translate object names to Japanese
    object_translations = {
        "person": "人", "people": "人々", "car": "車", "truck": "トラック",
        "bus": "バス", "motorcycle": "バイク", "bicycle": "自転車",
        "dog": "犬", "cat": "猫", "bird": "鳥", "horse": "馬",
        "chair": "椅子", "table": "テーブル", "couch": "ソファ",
        "tv": "テレビ", "laptop": "ノートパソコン", "phone": "電話",
        "book": "本", "clock": "時計", "bottle": "ボトル",
        "cup": "カップ", "fork": "フォーク", "knife": "ナイフ",
        "spoon": "スプーン", "bowl": "ボウル", "banana": "バナナ",
        "apple": "リンゴ", "orange": "オレンジ", "broccoli": "ブロッコリー",
        "tree": "木", "building": "建物", "sky": "空", "road": "道路",
        "sign": "標識", "light": "信号", "umbrella": "傘", "bag": "バッグ"
    }
    
    # Get BLIP caption if available
    caption_text = ""
    if captioner is not None and caption_processor is not None:
        try:
            from PIL import Image
            import cv2
            # Convert BGR to RGB for PIL
            rgb_img = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            
            inputs = caption_processor(pil_img, return_tensors="pt")
            out = captioner.generate(**inputs, max_length=50)
            caption_text = caption_processor.decode(out[0], skip_special_tokens=True)
            logging.info(f"BLIP caption: {caption_text}")
        except Exception as e:
            logging.warning(f"Failed to generate caption: {e}")
            caption_text = ""
    
    # Build detailed Japanese description
    description_parts = []
    
    # Add scene caption if available
    if caption_text:
        # Translate common English caption phrases to Japanese
        caption_ja = caption_text.replace("a photo of", "").replace("an image of", "").strip()
        description_parts.append(f"この画像は{caption_ja}を示しています。")
    
    # Add detected objects in Japanese
    if detected_objects:
        total_objects = sum(detected_objects.values())
        description_parts.append(f"画像内に合計{total_objects}個の物体が検出されました。")
        
        object_list = []
        for obj_name, count in detected_objects.items():
            ja_name = object_translations.get(obj_name, obj_name)
            if count == 1:
                object_list.append(f"{ja_name}が1つ")
            else:
                object_list.append(f"{ja_name}が{count}個")
        
        description_parts.append("具体的には、" + "、".join(object_list) + "が含まれています。")
    else:
        description_parts.append("画像内に認識可能な物体は検出されませんでした。")
    
    return " ".join(description_parts)


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
    Xử lý inference với YOLO + Image Captioning - tối ưu cho Render.
    Trả về mô tả chi tiết bằng tiếng Nhật với metrics đầy đủ.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    start_time = time.time()
    
    try:
        import numpy as np
        import cv2

        # Đọc toàn bộ file vào memory
        contents = await file.read()
        
        # Decode image
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Cannot decode image. Please upload a valid image file.")

        # YOLO Prediction
        results = model.predict(img, save=False, verbose=False)
        result = results[0]

        # Extract detected objects
        detected_objects = {}
        try:
            detected_names = [result.names[int(c)] for c in result.boxes.cls]
            for name in detected_names:
                detected_objects[name] = detected_objects.get(name, 0) + 1
        except Exception:
            detected_objects = {}

        # Get inference speed metrics
        speed = getattr(result, "speed", {})
        inference_speed = {
            "preprocess": speed.get('preprocess', 0.0),
            "inference": speed.get('inference', 0.0),
            "postprocess": speed.get('postprocess', 0.0)
        }

        # Generate detailed Japanese description
        detailed_description = generate_scene_description(img, detected_objects)
        
        # Create YOLO summary in Japanese
        total_objects = sum(detected_objects.values())
        if detected_objects:
            object_summary = "、".join([f"{k}: {v}個" for k, v in detected_objects.items()])
            yolo_summary = f"YOLO検出: {object_summary}"
        else:
            yolo_summary = "YOLO検出: 物体なし"

        # Draw bounding boxes
        plotted_img = result.plot()
        _, buffer = cv2.imencode('.jpg', plotted_img)
        encoded_image = base64.b64encode(buffer).decode('utf-8')

        # Calculate total processing time
        processing_time = time.time() - start_time

        return PredictionResponse(
            filename=file.filename or "uploaded_image.jpg",
            description=detailed_description,
            yolo_summary=yolo_summary,
            object_count=total_objects,
            object_details=detected_objects,
            processing_time=round(processing_time, 3),
            inference_speed=inference_speed,
            image_base64=encoded_image,
        )

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error("Inference error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"画像処理中にエラーが発生しました: {str(e)}")


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
