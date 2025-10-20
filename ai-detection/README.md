# Dự án Nhận dạng Đối tượng với YOLOv8 và FastAPI

Dự án này là một ứng dụng web cho phép người dùng tải lên hình ảnh và thực hiện nhận dạng đối tượng bằng mô hình YOLOv8. Giao diện người dùng đơn giản được xây dựng bằng HTML/JavaScript và backend được xử lý bởi một API mạnh mẽ sử dụng FastAPI.

## Chức năng chính

- Tải ảnh lên từ giao diện web.
- Xử lý ảnh bằng mô hình YOLOv8s để phát hiện các đối tượng.
- Hiển thị ảnh kết quả với các đối tượng đã được đánh dấu.

## Công nghệ sử dụng

### Backend
- **Python 3.11**
- **FastAPI:** Web framework hiệu suất cao để xây dựng API.
- **Uvicorn:** Máy chủ web ASGI để chạy ứng dụng FastAPI.
- **Ultralytics (YOLOv8):** Thư viện mã nguồn mở cho các mô hình AI tiên tiến, ở đây được sử dụng cho mô hình nhận dạng đối tượng YOLOv8.
- **Python-multipart:** Dùng để xử lý việc tải file lên.

### Frontend
- **HTML5**
- **CSS3**
- **JavaScript (Fetch API):** Dùng để tương tác với backend API một cách bất đồng bộ.

### Model
- **yolov8s.pt:** Một mô hình thuộc họ YOLOv8, được huấn luyện sẵn để nhận dạng nhiều loại đối tượng phổ biến.

## Cài đặt

1.  **Clone repository (Sao chép dự án):**
    ```bash
    git clone <URL_CUA_BAN>
    cd ai-detection
    ```

2.  **Tạo và kích hoạt môi trường ảo:**
    ```bash
    # Dành cho Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Dành cho macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Tải mô hình YOLOv8:**
    Đảm bảo file `yolov8s.pt` nằm trong thư mục `app.py/models/` hoặc một đường dẫn phù hợp mà code của bạn đang trỏ tới.
    Sau khi tái cấu trúc, đường dẫn đúng sẽ là `app/models/yolov8s.pt`.

## Sử dụng

1.  **Chạy máy chủ backend:**
    Mở terminal và chạy lệnh sau từ thư mục gốc của dự án (`ai-detection`):
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    *Lưu ý: Lệnh trên giả định file chính của bạn là `main.py` và biến FastAPI tên là `app` nằm trong thư mục `app` mới.*

2.  **Mở giao diện người dùng:**
    Mở trình duyệt và truy cập vào file `frontend/index.html`. Bạn có thể mở trực tiếp file này.

3.  **Thực hiện nhận dạng:**
    - Nhấn vào nút "Choose File" (Chọn tệp) để tải lên một hình ảnh.
    - Nhấn nút "Start" (Bắt đầu).
    - Chờ trong giây lát để hệ thống xử lý và xem kết quả hiển thị ngay trên trang.

## Cấu trúc thư mục (đề xuất)

Dưới đây là cấu trúc thư mục được đề xuất để dự án dễ quản lý hơn. Cấu trúc hiện tại của bạn có một thư mục tên là `app.py/` có thể gây nhầm lẫn.

```
ai-detection/
├── app/
│   ├── __init__.py
│   ├── main.py             # Logic chính của FastAPI
│   └── models/
│       └── yolov8s.pt      # Đặt model ở đây
├── frontend/
│   └── index.html
├── venv/
├── .gitignore
├── README.md
└── requirements.txt
```

## Thư mục `utils/` và `temp/` — giải thích

- `utils/`:
    - Dùng để chứa các hàm tiện ích (helper) tái sử dụng như xử lý ảnh (resize, validate), lưu file an toàn, logging helpers, v.v.
    - Gợi ý: đặt các module helper trong `app/utils/` (với `__init__.py`) hoặc `utils/` ở gốc repo. Nếu đặt trong `app/`, bạn có thể import như `from app.utils.image_utils import save_uploaded_file`.
    - Ví dụ file `app/utils/image_utils.py` (một số hàm cơ bản):

```py
def is_allowed_file(filename: str) -> bool:
        return filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))

def save_uploaded_file(upload_file, dest_path: str):
        with open(dest_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)

```

- `temp/`:
    - Thư mục `temp/` ở gốc repo thường dùng để lưu kết quả tạm thời hoặc output khi debug. Tuy nhiên trong mã `app/main.py` hiện tại, ứng dụng sử dụng `tempfile.TemporaryDirectory()` để tạo thư mục tạm thời cho mỗi request.
    - Do đó, xóa thư mục `temp/` trong repo an toàn và không làm hỏng chương trình, trừ khi bạn hoặc một script bên ngoài đang trực tiếp tham chiếu tới `./temp/` (ví dụ: bạn lưu kết quả persistent để debug). Nếu không cần, có thể xóa hoặc giữ nhưng thêm `.gitignore` để không commit file tạm.

### Hành động khuyến nghị

- Nếu bạn không dùng các file tạm lâu dài: xóa `temp/` khỏi repo.
- Nếu bạn muốn giữ cấu trúc rỗng để người khác biết vị trí đặt file: tạo `app/utils/__init__.py` và `app/utils/image_utils.py` hoặc thêm file placeholder `utils/.gitkeep` và `temp/.gitkeep`.
- Luôn thêm `temp/` vào `.gitignore` (đã có trong repo mẫu).

