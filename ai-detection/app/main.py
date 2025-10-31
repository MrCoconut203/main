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
import logging
import sys


# --- Cấu hình ---
import logging
import sys
import asyncio
from asyncio import Semaphore


# --- Cấu hình Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# --- Cấu hình ---
MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov8s.pt")
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")
# Disable BLIP-2 by default for AWS to save cost (set to "true" to enable)
ENABLE_CAPTIONING = os.getenv("ENABLE_CAPTIONING", "true").lower() == "true"
# Maximum concurrent requests to prevent OOM
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))


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
# Semaphore for rate limiting
request_semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)


@app.on_event("startup")
async def load_model_on_startup():
    global model, captioner, caption_processor
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load YOLO
    try:
        from ultralytics import YOLO
        logger.info("Loading YOLO model from %s...", MODEL_PATH)
        model = YOLO(MODEL_PATH)
        logger.info("✓ YOLO model loaded successfully")
    except Exception as e:
        logger.error("Failed to load YOLO model: %s", e, exc_info=True)
        # Don't raise - let server start even if YOLO fails
    
    # Load BLIP-2 for image captioning (optional, can be disabled via env var)
    if ENABLE_CAPTIONING:
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            logger.info("Loading BLIP captioning model (this may take 1-2 minutes on first run)...")
            caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            captioner = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            logger.info("✓ BLIP captioning model loaded successfully")
        except Exception as e:
            logger.warning("Failed to load BLIP captioning model: %s. Captioning will be disabled.", e, exc_info=True)
            captioner = None
            caption_processor = None
    else:
        logger.info("Image captioning disabled via ENABLE_CAPTIONING=false")
    
    logger.info("Startup complete. PORT=%s", os.getenv("PORT", "8000"))

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


# Health check endpoint for AWS ECS/Fargate
@app.get("/health")
async def health_check():
    """AWS health check endpoint - returns 200 if service is healthy"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "captioning_enabled": ENABLE_CAPTIONING,
        "captioning_available": captioner is not None
    }


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


def translate_caption_to_japanese(english_caption: str) -> str:
    """
    Dịch caption tiếng Anh sang tiếng Nhật bằng từ điển và pattern matching.
    """
    # Common English -> Japanese translations
    translations = {
        # Scenes
        "a photo of": "", "an image of": "", "a picture of": "",
        "street": "通り", "road": "道路", "city": "都市", "town": "町",
        "beach": "ビーチ", "ocean": "海", "mountain": "山", "forest": "森",
        "park": "公園", "building": "建物", "house": "家",
        "room": "部屋", "office": "オフィス", "kitchen": "キッチン",
        
        # Actions
        "walking": "歩いている", "running": "走っている", "sitting": "座っている",
        "standing": "立っている", "playing": "遊んでいる", "eating": "食べている",
        "driving": "運転している", "riding": "乗っている",
        
        # Descriptions
        "busy": "賑やかな", "crowded": "混雑した", "empty": "空の",
        "sunny": "晴れた", "cloudy": "曇りの", "rainy": "雨の",
        "beautiful": "美しい", "old": "古い", "new": "新しい",
        "large": "大きな", "small": "小さな",
        
        # Conjunctions
        " with ": "と", " and ": "と", " on ": "の上に",
        " in ": "の中に", " at ": "で", " near ": "の近くに",
        
        # Objects (common ones)
        "people": "人々", "person": "人", "man": "男性", "woman": "女性",
        "child": "子供", "children": "子供たち",
        "car": "車", "cars": "車", "bus": "バス", "truck": "トラック",
        "bicycle": "自転車", "motorcycle": "バイク",
        "dog": "犬", "cat": "猫", "bird": "鳥",
        "tree": "木", "trees": "木々", "grass": "草",
        "sky": "空", "cloud": "雲", "clouds": "雲",
        "water": "水", "river": "川", "lake": "湖",
    }
    
    # Clean and translate
    result = english_caption.lower().strip()
    
    # Replace patterns
    for en, ja in translations.items():
        result = result.replace(en, ja)
    
    # Capitalize first letter if it's a sentence
    if result and not any(char in result for char in "あいうえおかきくけこ"):
        # If no Japanese characters yet, keep original
        return english_caption.strip()
    
    return result.strip()


def generate_scene_description(img_array, detected_objects: Dict[str, int]) -> str:
    """
    Tạo mô tả chi tiết khung cảnh ảnh bằng tiếng Nhật.
    Kết hợp BLIP caption (dịch sang tiếng Nhật) và YOLO detection.
    """
    import logging
    
    # Translate object names to Japanese
    object_translations = {
        "person": "人", "people": "人々", "car": "車", "truck": "トラック",
        "bus": "バス", "motorcycle": "バイク", "bicycle": "自転車",
        "dog": "犬", "cat": "猫", "bird": "鳥", "horse": "馬", "sheep": "羊",
        "cow": "牛", "elephant": "象", "bear": "熊", "zebra": "シマウマ",
        "giraffe": "キリン",
        "backpack": "バックパック", "umbrella": "傘", "handbag": "ハンドバッグ",
        "tie": "ネクタイ", "suitcase": "スーツケース",
        "frisbee": "フリスビー", "skis": "スキー", "snowboard": "スノーボード",
        "sports ball": "ボール", "kite": "凧", "baseball bat": "野球バット",
        "skateboard": "スケートボード", "surfboard": "サーフボード",
        "tennis racket": "テニスラケット",
        "bottle": "ボトル", "wine glass": "ワイングラス", "cup": "カップ",
        "fork": "フォーク", "knife": "ナイフ", "spoon": "スプーン",
        "bowl": "ボウル",
        "banana": "バナナ", "apple": "リンゴ", "sandwich": "サンドイッチ",
        "orange": "オレンジ", "broccoli": "ブロッコリー", "carrot": "ニンジン",
        "hot dog": "ホットドッグ", "pizza": "ピザ", "donut": "ドーナツ",
        "cake": "ケーキ",
        "chair": "椅子", "couch": "ソファ", "potted plant": "鉢植え",
        "bed": "ベッド", "dining table": "ダイニングテーブル", "toilet": "トイレ",
        "tv": "テレビ", "laptop": "ノートパソコン", "mouse": "マウス",
        "remote": "リモコン", "keyboard": "キーボード", "cell phone": "携帯電話",
        "microwave": "電子レンジ", "oven": "オーブン", "toaster": "トースター",
        "sink": "シンク", "refrigerator": "冷蔵庫",
        "book": "本", "clock": "時計", "vase": "花瓶", "scissors": "はさみ",
        "teddy bear": "テディベア", "hair drier": "ドライヤー",
        "toothbrush": "歯ブラシ",
        "traffic light": "信号", "fire hydrant": "消火栓", "stop sign": "停止標識",
        "parking meter": "駐車メーター", "bench": "ベンチ",
    }
    
    # Get BLIP caption if available
    caption_text = ""
    caption_ja = ""
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
            
            # Translate to Japanese
            caption_ja = translate_caption_to_japanese(caption_text)
            
            logging.info(f"BLIP caption (EN): {caption_text}")
            logging.info(f"BLIP caption (JA): {caption_ja}")
        except Exception as e:
            logging.warning(f"Failed to generate caption: {e}")
            caption_text = ""
            caption_ja = ""
    
    # Build detailed Japanese description
    description_parts = []
    
    # Add scene caption if available
    if caption_ja:
        description_parts.append(f"この画像は「{caption_ja}」という場面を示しています。")
    elif caption_text:
        # Fallback to English if translation failed
        description_parts.append(f"この画像は「{caption_text}」という場面を示しています。")
    
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
        
        if object_list:
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
    Rate-limited to prevent OOM with concurrent requests.
    """
    # Acquire semaphore to limit concurrent requests
    async with request_semaphore:
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
            logger.error("Inference error: %s", e, exc_info=True)
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
