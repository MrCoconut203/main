# YOLOv8 物体検出 API + AI画像説明

YOLOv8モデルとBLIP-2画像キャプションを使用した高度な物体検出WebサービスとDockerコンテナです。

## ✨ 主な機能

- 🎯 **YOLOv8物体検出**: リアルタイムで画像内の物体を検出
- 🧠 **AI画像説明（日本語）**: BLIP-2モデルによる詳細なシーン説明を自動的に日本語に翻訳
- 📊 **詳細なメトリクス**: 処理時間、推論速度、物体数を日本語で表示
- 🌐 **完全日本語対応**: すべての結果とUIが日本語（BLIP-2の説明も日本語翻訳）
- 🎨 **美しいUI**: アニメ風グラデーション背景、ローディングアニメーション
- 🔄 **デフォルトで有効**: BLIP-2画像説明はデフォルトで有効（無効化可能）

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
  "filename": "sample.jpg",
  "description": "この画像は「賑やかな通りと人々と車」という場面を示しています。画像内に合計5個の物体が検出されました。具体的には、車が2個、人が3個が含まれています。",
  "yolo_summary": "YOLO検出: car: 2個、person: 3個",
  "object_count": 5,
  "object_details": {
    "car": 2,
    "person": 3
  },
  "processing_time": 1.234,
  "inference_speed": {
    "preprocess": 2.5,
    "inference": 45.3,
    "postprocess": 1.8
  },
  "image_base64": "iVBORw0KGgoAAAANS..."
}
```

### レスポンスフィールドの説明

- `description`: BLIP-2（日本語翻訳）とYOLOを組み合わせた詳細な日本語説明
  - BLIP-2のキャプションは自動的に日本語に翻訳されます
  - 例: "busy street with people" → "賑やかな通りと人々"
- `yolo_summary`: YOLO検出結果の要約（日本語）
- `object_count`: 検出された物体の総数
- `object_details`: 各物体タイプの個数
- `processing_time`: 総処理時間（秒）
- `inference_speed`: 推論速度の詳細（ミリ秒）
  - `preprocess`: 前処理時間
  - `inference`: 推論時間
  - `postprocess`: 後処理時間
- `image_base64`: バウンディングボックス付き結果画像（Base64エンコード）

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
| `ENABLE_CAPTIONING` | `true` | BLIP-2画像説明を有効化（デフォルト有効） |

**注意**: 
- BLIP-2はデフォルトで有効です（日本語翻訳付き）
- `ENABLE_CAPTIONING=false` に設定すると、BLIP-2をロードせずYOLO検出のみを使用します（メモリ節約、約2GB削減）

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

### 問題: BLIP-2メモリ不足
**原因:** BLIPモデルが大きすぎる

**解決策1:** 画像説明を無効化
```powershell
$env:ENABLE_CAPTIONING="false"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**解決策2:** Docker Desktopのメモリを増やす
- Settings > Resources > Memory を 4GB+ に設定

**解決策3:** より小さいBLIPモデルを使用
`main.py` 内で `Salesforce/blip-image-captioning-base` を `Salesforce/blip-image-captioning-large` に変更（より高精度だがメモリを多く使用）。

### 問題: transformersパッケージが見つからない
```
ModuleNotFoundError: No module named 'transformers'
```

**解決策:**
```powershell
pip install transformers pillow sentencepiece accelerate
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
- `transformers` - BLIP-2画像キャプション
- `sentencepiece` - トークナイザー
- `accelerate` - モデル最適化

## 🎨 UI機能

- **アニメ風グラデーション背景**: 紫〜青のグラデーション
- **ローディングスピナー**: 回転アニメーション
- **詳細メトリクス表示**:
  - 🎯 検出物体数
  - ⏱️ 総処理時間
  - ⚡ 前処理速度
  - 🚀 推論速度
  - ✨ 後処理速度
- **完全日本語対応**: すべてのテキストが日本語

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

Pull Requestは歓迎します！大きな変更の場合は、まず Issue を開いて変更内容を説明してください。

## 📧 連絡先

問題や質問がある場合は、GitHub Issues にお知らせください。

---

**注意:** 本番環境では、CORS設定を適切に調整し、モデルファイルのセキュリティを確保してください。
