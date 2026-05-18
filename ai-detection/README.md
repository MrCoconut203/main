# AI Object Detection Service (FastAPI + YOLOv8)

This project provides an image object-detection API powered by YOLOv8, with a simple web frontend.

## What was cleaned up

- Consolidated documentation to a single English Markdown file (`README.md`).
- Removed outdated/duplicate docs and backup files.
- Standardized image processing for multiple formats and variable image sizes.
- Added upload validation and image-size optimization to improve runtime performance and memory efficiency.

## Features

- **Object detection API** (`POST /predict/`) using YOLOv8.
- **Multi-format image support**: `jpg/jpeg`, `png`, `webp`, `bmp`, `tiff`.
- **Input validation**:
  - Rejects empty files.
  - Rejects unsupported file formats.
  - Rejects files larger than configured limit.
- **Performance optimization**:
  - Resizes very large images while preserving aspect ratio before inference.
  - Limits concurrent requests to reduce memory pressure.

## Configuration (Environment Variables)

- `MODEL_PATH` (default: `models/yolov8s.pt`)
- `CORS_ORIGINS` (default: `*`)
- `ENABLE_CAPTIONING` (default: `false`)
- `MAX_CONCURRENT_REQUESTS` (default: `3`)
- `MAX_UPLOAD_BYTES` (default: `10485760` = 10MB)
- `MAX_IMAGE_SIDE` (default: `1920`)

## Run locally

```bash
cd ai-detection
pip install -r requirements.txt -c constraints.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- Frontend: `http://localhost:8000/`
- Health: `http://localhost:8000/health`

## API

### `POST /predict/`

Upload a file as multipart form-data with field name `file`.

Possible responses:

- `200`: prediction result
- `400`: invalid/unsupported image
- `413`: file too large
- `503`: model not loaded yet

## Tests

```bash
cd ai-detection
pytest -q
```
