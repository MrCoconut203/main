# YOLOv8 物体検出 API

YOLOv8モデルを使用した物体検出のFastAPI WebサービスとDockerコンテナです。

## 📁 プロジェクト構造

```
ai-detection/
├── app/
│   └── main.py          # FastAPI アプリケーション
├── frontend/
│   └── index.html       # Web UI (日本語)
├── models/
│   └── yolov8s.pt       # YOLOv8モデルファイル
├── temp/                # 一時ファイル
├── utils/               # ユーティリティ
├── requirements.txt     # Python依存関係
├── Dockerfile          # Dockerビルド設定
└── docker-compose.yml  # Docker Composeファイル
```

## 🚀 デプロイ方法

### 方法1: Docker で実行（推奨）

#### 前提条件
- Docker Desktop (Windows/Mac)
- Git

#### 手順

**1. リポジトリをクローン**
```powershell
git clone https://github.com/MrCoconut203/main.git
cd main
```

**2. モデルファイルを配置**
```powershell
# models/yolov8s.pt が存在することを確認
# ない場合は ultralytics からダウンロード
```

**3. Dockerイメージをビルド**
```powershell
# リポジトリルートから実行
docker build -f ai-detection/Dockerfile -t yolov8-api:latest .
```

**4. コンテナを起動**
```powershell
# ポート 8000 で起動
docker run -d `
  -p 8000:8000 `
  -e MODEL_PATH="models/yolov8s.pt" `
  -e CORS_ORIGINS="*" `
  --name yolov8-container `
  yolov8-api:latest
```

**5. 動作確認**
```powershell
# ヘルスチェック
curl http://localhost:8000/health

# ブラウザで http://localhost:8000 を開く
```

#### Docker Compose で実行（代替）

```powershell
cd ai-detection
docker-compose up -d
```

### 方法2: 仮想環境で実行

#### 前提条件
- Python 3.11+
- pip

#### 手順

**1. 仮想環境を作成**
```powershell
cd ai-detection
python -m venv .venv
.\.venv\Scripts\Activate
```

**2. 依存関係をインストール**
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**3. モデルを配置**
```powershell
# models/yolov8s.pt が存在することを確認
```

**4. サーバーを起動**
```powershell
# デフォルトポート 8000
$env:MODEL_PATH="models/yolov8s.pt"
$env:CORS_ORIGINS="*"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**5. アクセス**
- Web UI: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

## 📡 API エンドポイント

### `GET /health`
ヘルスチェックエンドポイント

**レスポンス例:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### `POST /predict/`
画像内の物体を検出

**リクエスト:**
- Content-Type: `multipart/form-data`
- Body: `file` (画像ファイル: JPG, PNG など)

**レスポンス例:**
```json
{
  "description": "person: 2件, car: 1件",
  "image_base64": "iVBORw0KGgoAAAANS...",
  "detections": [
    {
      "class": "person",
      "confidence": 0.92,
      "bbox": [120, 45, 280, 350]
    }
  ]
}
```

## 🌐 クラウドデプロイ

### Render.com でデプロイ

**1. GitHubにプッシュ**
```powershell
git add .
git commit -m "Initial commit"
git push origin main
```

**2. Render設定**
- Root Directory: `.` (ルート)
- Dockerfile Path: `ai-detection/Dockerfile`
- Environment Variables:
  - `PORT`: 自動設定 (Renderが提供)
  - `MODEL_PATH`: `models/yolov8s.pt`
  - `CORS_ORIGINS`: `*`

**3. デプロイ**
Renderが自動的にビルド＆デプロイします。

## ⚙️ 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `MODEL_PATH` | `models/yolov8s.pt` | YOLOv8モデルのパス |
| `CORS_ORIGINS` | `*` | 許可するオリジン |
| `PORT` | `8000` | サーバーポート |

## 🐛 トラブルシューティング

### 問題: `405 Method Not Allowed`
**原因:** GETリクエストを/predict/に送信している

**解決策:**
- POSTメソッドを使用
- curlの場合: `curl -X POST -F "file=@image.jpg" http://localhost:8000/predict/`

### 問題: `500 Internal Server Error`
**原因1:** モデルファイルが見つからない

**解決策:**
```powershell
# モデルの存在を確認
ls models/yolov8s.pt

# ない場合はダウンロード
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
Move-Item yolov8s.pt models/
```

**原因2:** メモリ不足

**解決策:**
- 小さいモデルを使用: `yolov8n.pt` (nano版)
- Docker Desktopのメモリを増やす (Settings > Resources)

### 問題: `502 Bad Gateway` (Render)
**原因:** ポート設定が間違っている

**解決策:**
- Dockerfile CMD を確認: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- 環境変数 `PORT` をRenderが自動設定していることを確認

### 問題: `504 Gateway Timeout`
**原因:** 処理時間が長すぎる

**解決策:**
- 小さい画像を使用
- yolov8n.pt (nano) モデルに変更
- Renderプランをアップグレード

### 問題: NumPy ABI エラー
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility.
```

**解決策:**
```powershell
pip uninstall numpy -y
pip install numpy==1.26.4
pip install --force-reinstall --no-cache-dir ultralytics
```

## 📦 依存関係

主要なPythonパッケージ:
- `fastapi` - Web API フレームワーク
- `uvicorn` - ASGI サーバー
- `ultralytics` - YOLOv8 実装
- `torch` - PyTorch (ディープラーニング)
- `opencv-python` - 画像処理
- `pillow` - 画像操作
- `python-multipart` - ファイルアップロード

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

Pull Requestは歓迎します！大きな変更の場合は、まず Issue を開いて変更内容を説明してください。

## 📧 連絡先

問題や質問がある場合は、GitHub Issues にお知らせください。

---

**注意:** 本番環境では、CORS設定を適切に調整し、モデルファイルのセキュリティを確保してください。
