# Dự án: Nhận dạng đối tượng với YOLOv8 + FastAPI

Ứng dụng này cung cấp API để nhận dạng đối tượng trên ảnh sử dụng mô hình YOLOv8. Frontend là một SPA đơn giản (HTML/JS) và backend là một dịch vụ FastAPI nằm trong `app/`.

Tài liệu này mô tả hai cách chạy ứng dụng - bằng Docker (khuyến nghị cho deployment) và bằng môi trường ảo Python (virtualenv) cho phát triển.

## Cấu trúc chính

- `app/` - mã nguồn FastAPI (entrypoint: `app/main.py`).
- `models/` - chứa mô hình `yolov8s.pt` (cần có để chạy inference thực tế).
- `frontend/` - tệp tĩnh SPA.
- `deploy/` - cấu hình nginx / reverse proxy, docker-compose, v.v.
- `requirements.txt`, `constraints.txt` - dependencies Python (lưu ý: `constraints.txt` có ràng buộc `numpy<2`).

---

## Cách 1 — Triển khai bằng Docker (Production / Render / Cloud)

Ưu điểm: môi trường nhất quán, dễ deploy và scale. Khuyến nghị cho môi trường staging/production.

1) Build image (PowerShell):

```powershell
# chạy từ thư mục chứa Dockerfile (ai-detection)
docker build -t your-registry/ai-detection:latest .
```

2) Chạy container cục bộ để kiểm tra:

```powershell
# thiết lập PORT cho container (uvicorn trong image đọc biến PORT)
$env:PORT = '8000'
docker run --rm -e PORT=8000 -p 8000:8000 your-registry/ai-detection:latest
```

3) Dùng docker-compose (nếu repo có `docker-compose.yml`):

```powershell
docker compose up --build
```

4) Push image lên registry (Docker Hub / GHCR):

```powershell
docker tag your-registry/ai-detection:latest yourhub/ai-detection:1.0.0
docker push yourhub/ai-detection:1.0.0
```

Ghi chú quan trọng:
- Nhiều PaaS (ví dụ Render) cung cấp biến môi trường `PORT` — ứng dụng phải bind tới `$PORT`. `start.sh` trong repo đã đọc biến này. Đảm bảo platform của bạn set biến đó.
- Torch là gói lớn; khi build image, quá trình tải wheel có thể mất thời gian hoặc thất bại nếu mạng không ổn định. Nếu gặp lỗi build/cancel ở bước cài torch, cân nhắc:
  - Pre-download wheel và thêm vào context build, hoặc
  - Dùng một image base đã chứa torch wheel, hoặc
  - Thực hiện build trên CI có kết nối ổn định.
- Nếu thấy lỗi NumPy ABI (ví dụ: "A module compiled using NumPy 1.x cannot be run in NumPy 2.x"), hãy chắc chắn `constraints.txt` chứa `numpy<2` và rebuild image.

---

## Cách 2 — Chạy local bằng virtualenv (phát triển / debug)

Ưu điểm: nhẹ cho development, dễ sửa code, dễ debug bằng IDE. Nhược điểm: có thể phải cài các package nặng (torch) nếu bạn cần chạy inference thật.

1) Tạo và kích hoạt virtualenv (PowerShell):

```powershell
cd path\to\ai-detection
python -m venv .venv
# Kích hoạt (PowerShell)
.\.venv\Scripts\Activate.ps1
# Nếu PowerShell chặn script: mở PowerShell với quyền Admin và chạy:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

2) Cài dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt
```

3) Thiết lập PORT và chạy server (ví dụ PORT=8000):

```powershell
$env:PORT = '8000'
uvicorn app.main:app --host 0.0.0.0 --port $env:PORT --reload
```

4) Mở trình duyệt tới `http://localhost:8000/` để kiểm tra.

Ghi chú cho local dev:
- Nếu không muốn cài torch (nặng), bạn có thể mock inference hoặc chỉ chạy unit tests; hoặc dùng Docker cho bước inference thật.
- Hãy đảm bảo file mô hình `models/yolov8s.pt` có trong `models/` nếu bạn muốn chạy inference thực tế.

---

## Endpoints & Health

- `GET /health` — health check.
- `POST /predict/` — endpoint inference (file upload form-data). Kiểm tra phần front-end tương ứng.

---

## Troubleshooting nhanh

**Lỗi 405 (Method Not Allowed)**
- Nguyên nhân: Client gọi endpoint không đúng phương thức hoặc trailing slash không khớp.
- Giải pháp: Repo đã hỗ trợ cả `/predict/` và `/predict` (với/không dấu `/`). Đảm bảo client POST đúng endpoint.

**Lỗi 500 (Internal Server Error) - NumPy ABI mismatch**
- Nguyên nhân: Thư viện compiled (torch, ultralytics) build với NumPy 1.x nhưng runtime có NumPy 2.x.
- Giải pháp: Rebuild image với `constraints.txt` chứa `numpy<2`, hoặc chạy `pip install 'numpy<2'` trong container.

**Lỗi 502/504 (Bad Gateway / Gateway Timeout)**
- Nguyên nhân: 
  - Backend crash do OOM (quá nhiều workers, model quá lớn).
  - Inference mất quá lâu (>30s Render default timeout).
  - Proxy timeout (nếu dùng nginx).
- Giải pháp:
  - Giảm workers xuống 1 (đã áp dụng trong `start.sh`).
  - Tăng uvicorn timeout: `--timeout-keep-alive 120` (đã áp dụng).
  - Tăng nginx proxy timeout (đã set 90s connect, 180s read trong `deploy/default.conf`).
  - Xử lý in-memory thay vì disk I/O (đã refactor trong `app/main.py`).

**Lỗi 503 (Service Unavailable)**
- Nguyên nhân: Model chưa load xong khi request đến (cold start).
- Giải pháp: Đợi vài giây và retry. Frontend đã có timeout 90s; nếu cần, cấu hình health check trên Render để đảm bảo service ready trước khi nhận traffic.

**Timeout khi upload ảnh lớn**
- Frontend có timeout 90s (có thể điều chỉnh trong `index.html`, biến `setTimeout(..., 90000)`).
- Backend xử lý in-memory nên nhanh hơn disk; nếu ảnh quá lớn (>10MB), cân nhắc resize client-side trước khi upload.

---

## Lệnh test nhanh

```powershell
# cài dependencies và chạy test (nếu tests có sẵn)
pip install -r requirements.txt -c constraints.txt
pip install pytest
pytest -q
```

## Khuyến nghị dọn dẹp

- Xóa `temp/` nếu không dùng (hoặc thêm `.gitkeep` nếu muốn giữ folder). Thêm `temp/` vào `.gitignore`.

---

Nếu bạn muốn, tôi có thể:
- Thêm phần hướng dẫn CI (ví dụ GitHub Actions) để build và push image tự động.
- Viết bước cụ thể để pre-download wheel torch vào context build để tránh lỗi no-cache builds.
# Dự án Nhận dạng Đối tượng với YOLOv8 và FastAPI

Dự án này là một ứng dụng web cho phép người dùng tải lên hình ảnh và thực hiện nhận dạng đối tượng bằng mô hình YOLOv8. Giao diện người dùng đơn giản được xây dựng bằng HTML/JavaScript và backend được xử lý bởi một API mạnh mẽ sử dụng FastAPI.

-
*** End Patch
### Hành động khuyến nghị

- Nếu bạn không dùng các file tạm lâu dài: xóa `temp/` khỏi repo.
- Nếu bạn muốn giữ cấu trúc rỗng để người khác biết vị trí đặt file: tạo `app/utils/__init__.py` và `app/utils/image_utils.py` hoặc thêm file placeholder `utils/.gitkeep` và `temp/.gitkeep`.
- Luôn thêm `temp/` vào `.gitignore` (đã có trong repo mẫu).

