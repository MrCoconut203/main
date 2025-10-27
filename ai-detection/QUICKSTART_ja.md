# クイックスタートガイド - YOLOv8 + BLIP-2 検出システム

## 🚀 最速セットアップ（5分）

### 前提条件
- Python 3.11+
- 8GB+ RAM推奨（BLIP-2使用時）

### ステップ1: リポジトリをクローン
```powershell
git clone https://github.com/MrCoconut203/main.git
cd main/ai-detection
```

### ステップ2: 仮想環境を作成
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

### ステップ3: 依存関係をインストール
```powershell
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### ステップ4: モデルを配置
```powershell
# YOLOv8モデルが自動ダウンロードされます（初回実行時）
```

### ステップ5: サーバーを起動
```powershell
cd ai-detection
uvicorn app.main:app --reload
```

### ステップ6: ブラウザで開く
```
http://localhost:8000
```

## 🎯 使い方

1. **画像を選択**: 「ファイルを選択」ボタンをクリック
2. **検出開始**: 🚀「検出開始」ボタンをクリック
3. **結果を確認**: 
   - AI生成の詳細説明（日本語）
   - 検出物体の数と種類
   - 処理時間とメトリクス
   - バウンディングボックス付き画像

## ⚙️ 設定オプション

### メモリが少ない場合（<4GB）
```powershell
# BLIP-2画像説明を無効化（YOLO検出のみ）
$env:ENABLE_CAPTIONING="false"
uvicorn app.main:app --reload
```

### ポートを変更
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### より高速なモデル（精度↓、速度↑）
`main.py` で `yolov8s.pt` を `yolov8n.pt` に変更

### より高精度なモデル（精度↑、速度↓）
`main.py` で `yolov8s.pt` を `yolov8m.pt` に変更

## 🐳 Dockerで実行（推奨）

```powershell
# ビルド（リポジトリルートから）
docker build -f ai-detection/Dockerfile -t yolov8-blip:latest .

# 実行（BLIP-2有効）
docker run -d -p 8000:8000 -e ENABLE_CAPTIONING=true yolov8-blip:latest

# 実行（BLIP-2無効、軽量）
docker run -d -p 8000:8000 -e ENABLE_CAPTIONING=false yolov8-blip:latest
```

## 📊 期待される結果

### 入力: 人と車が写った街の写真

**出力:**
```
この画像はa busy street with people walking and cars drivingを示しています。
画像内に合計7個の物体が検出されました。
具体的には、人が4個、車が2個、信号が1個が含まれています。
```

**メトリクス:**
- 🎯 検出物体数: 7
- ⏱️ 処理時間: 1.23s
- ⚡ 前処理速度: 2.5ms
- 🚀 推論速度: 45.3ms
- ✨ 後処理速度: 1.8ms

## 🆘 よくある問題

### 1. "Model not loaded yet" エラー
→ サーバー起動後30秒待ってから再試行

### 2. メモリ不足エラー
→ `ENABLE_CAPTIONING=false` を設定

### 3. 画像がアップロードできない
→ ファイル形式を確認（JPG、PNG対応）

### 4. 処理が遅い
→ より小さいモデル（yolov8n.pt）を使用

## 📚 さらに詳しく

- 完全な日本語ドキュメント: `README_ja.md`
- API詳細: http://localhost:8000/docs
- トラブルシューティング: `README_ja.md` のトラブルシューティングセクション

---

質問がある場合は、GitHub Issuesでお知らせください！
