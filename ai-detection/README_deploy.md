# Hướng dẫn triển khai (Ubuntu) — Docker + nginx + Let's Encrypt

Mô tả nhanh: dùng Docker để chạy FastAPI app và Nginx làm reverse proxy/serve frontend. SSL lấy bằng Let's Encrypt (certbot).

1) Chuẩn bị server
 - Ubuntu 20.04/22.04
 - Cấp quyền SSH, mở port 22,80,443

2) Cài Docker & docker-compose
```bash
sudo apt update; sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
```

3) Clone repo và đặt model
```bash
git clone <repo-url> ai-detection
cd ai-detection
# đặt file model yolov8s.pt vào ./app/models/ hoặc mount vào volume
```

4) Build và chạy
```bash
docker-compose up -d --build
```

5) Cấu hình Nginx & SSL
- Tạo file `deploy/nginx.conf` (một ví dụ đã có trong repo mẫu). Nếu dùng certbot trên host, đặt chứng chỉ vào `./certs` và mount vào container nginx.
- Hoặc dùng một proxy như Traefik cho tự động triển khai SSL.

6) Các biến môi trường quan trọng
- MODEL_PATH: đường dẫn model (mặc định `models/yolov8s.pt`)
- CORS_ORIGINS: danh sách origin cho phép

Lưu ý:
- Nếu cần GPU, dùng image Docker base tương thích với CUDA và cài torch tương thích. Dùng `nvidia-docker` runtime.
- Không nên commit model vào Git; lưu ở storage ngoài hoặc mount volume.
