# 🚀 Chạy server ngay - Quick Start

## ⚡ Cách nhanh nhất (KHÔNG BLIP-2 - chỉ YOLO)

```powershell
cd d:\project\ai-detection
$env:PYTHONPATH="d:\project\ai-detection"
$env:ENABLE_CAPTIONING="false"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Sau đó mở browser**: http://localhost:8000

---

## 🧠 Với BLIP-2 (Mô tả AI chi tiết tiếng Nhật)

### ⚠️ Yêu cầu:
- RAM: ~4GB trống
- Thời gian: Lần đầu tải model ~1GB (1-2 phút)
- Sau lần đầu: Model được cache, nhanh hơn

### Bước 1: Chạy server
```powershell
cd d:\project\ai-detection
$env:PYTHONPATH="d:\project\ai-detection"
$env:ENABLE_CAPTIONING="true"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Bước 2: Chờ model load
- Thấy: "Loading BLIP captioning model..."
- Chờ: "✓ BLIP captioning model loaded successfully"
- Mất: ~30 giây đến 2 phút (tuỳ mạng)

### Bước 3: Test
- Mở: http://localhost:8000
- Upload ảnh
- Xem kết quả với AI description!

---

## 🎯 So sánh Output

### Không BLIP-2 (fast, ít RAM):
```
YOLO検出: car: 2個、person: 3個

📊 メトリクス:
🎯 検出物体数: 5
⏱️ 処理時間: 0.45s
```

### Có BLIP-2 (slow, nhiều RAM, mô tả chi tiết):
```
📝 AI説明:
この画像は「賑やかな通りと車と人々」という場面を示しています。
画像内に合計5個の物体が検出されました。
具体的には、車が2個、人が3個が含まれています。

YOLO検出: car: 2個、person: 3個

📊 メトリクス:
🎯 検出物体数: 5
⏱️ 処理時間: 1.23s  ← Chậm hơn do BLIP-2
```

---

## 🔧 Troubleshooting

### Lỗi: ModuleNotFoundError: No module named 'app'
```powershell
# Phải set PYTHONPATH!
$env:PYTHONPATH="d:\project\ai-detection"
```

### Lỗi: Server shutdown ngay sau startup
- Thường do BLIP-2 model quá lớn/hết RAM
- **Giải pháp**: Tắt BLIP-2
```powershell
$env:ENABLE_CAPTIONING="false"
```

### Lỗi: Import transformers could not be resolved
```powershell
pip install transformers pillow sentencepiece accelerate
```

### BLIP-2 load chậm lần đầu
- Bình thường! Model 990MB cần thời gian
- Lần sau sẽ nhanh hơn (đã cache)
- Kiên nhẫn chờ "✓ BLIP captioning model loaded"

---

## 🎊 Đã test thành công?

**Không BLIP-2** (nhanh, ít RAM):
```powershell
cd d:\project\ai-detection
$env:PYTHONPATH="d:\project\ai-detection"
$env:ENABLE_CAPTIONING="false"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Mở http://localhost:8000 và test ngay!
