FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy app, frontend and requirements (build context = repo root)
# when Render uses repo root as build context the ai-detection folder is at ./ai-detection
COPY ai-detection/app/ ./app/
COPY ai-detection/frontend/ ./frontend/
COPY ai-detection/requirements.txt ./requirements.txt
# copy models from repo root (if present)
COPY models/ ./models/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000

# Use the PORT provided by the hosting provider (Render sets $PORT). Fallback to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
