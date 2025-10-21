# Pin to a stable Debian codename to avoid mirror/release-info issues
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system deps in a single step and ensure CA certs are present so apt HTTPS works
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    apt-transport-https \
    build-essential \
    libgl1 \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    libjpeg-dev \
    libsndfile1 \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy app, frontend and requirements (assume build context = ./ai-detection)
# If you run `docker compose build` from the ai-detection folder, these relative paths work.
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY requirements.txt ./requirements.txt
COPY constraints.txt ./constraints.txt
# copy models from the ai-detection folder (if present)
COPY models/ ./models/

RUN pip install --upgrade pip
# Install build tools to help installing some wheels
RUN pip install --upgrade pip setuptools wheel

# Install CPU-only PyTorch wheel explicitly to avoid building from source inside the image.
# If you have CUDA-enabled environment replace this with the appropriate wheel URL.
RUN pip install --no-cache-dir "torch==2.2.0+cpu" -f https://download.pytorch.org/whl/torch_stable.html

# Now install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

EXPOSE 8000

# Use the PORT provided by the hosting provider (Render sets $PORT). Fallback to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
