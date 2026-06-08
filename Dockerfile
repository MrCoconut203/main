# 1. Base image
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV YOLO_CONFIG_DIR=/app/.ultralytics

WORKDIR /app

# 2. System dependencies (Thay đổi rất ít)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates apt-transport-https build-essential libgl1 ffmpeg \
    libsm6 libxext6 libxrender1 libglib2.0-0 libjpeg-dev libsndfile1 libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Cài đặt Python Dependencies (Tách riêng để cache)
# Chỉ copy những file cần thiết cho việc cài đặt thư viện
COPY requirements.txt constraints.txt ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    "torch==2.2.0+cpu" \
    "torchvision==0.17.0+cpu" \
    -f https://download.pytorch.org/whl/torch_stable.html && \
    mkdir -p /app/.ultralytics && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

# 4. Copy toàn bộ code (Thay đổi thường xuyên nhất - để ở dưới cùng)
COPY . .

# 5. Cấu hình runtime
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
# Chỉ cần tạo và cấp quyền rộng rãi là xong
RUN mkdir -p /var/cache/nginx/client_temp && \
    chmod -R 777 /var/cache/nginx/client_temp
