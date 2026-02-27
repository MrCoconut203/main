"""
YOLOv8 + BLIP-2 検出APIテストスクリプト

使い方:
    python test_api.py <画像パス>

例:
    python test_api.py sample.jpg
"""

import sys
import requests
import json
from pathlib import Path


def run_detection_api(image_path: str, api_url: str = "http://localhost:8000/predict/"):
    """
    画像を送信してAI検出結果を取得
    
    Args:
        image_path: テストする画像のパス
        api_url: APIエンドポイントURL
    """
    # 画像ファイルの確認
    img_file = Path(image_path)
    if not img_file.exists():
        print(f"❌ エラー: 画像ファイルが見つかりません: {image_path}")
        return
    
    print(f"📸 画像を送信中: {img_file.name}")
    print(f"🌐 API URL: {api_url}")
    print("-" * 60)
    
    # APIリクエスト
    try:
        with open(img_file, 'rb') as f:
            files = {'file': (img_file.name, f, 'image/jpeg')}
            response = requests.post(api_url, files=files, timeout=90)
        
        if response.status_code != 200:
            print(f"❌ エラー: HTTP {response.status_code}")
            print(response.text)
            return
        
        # レスポンス解析
        result = response.json()
        
        # 結果を日本語で表示
        print("✅ 検出成功！\n")
        
        print("📝 AI生成説明:")
        print(f"   {result.get('description', '説明なし')}\n")
        
        print("🎯 YOLO検出結果:")
        print(f"   {result.get('yolo_summary', 'なし')}\n")
        
        print("📊 検出統計:")
        print(f"   🔢 総物体数: {result.get('object_count', 0)}個")
        
        if result.get('object_details'):
            print("   📋 詳細:")
            for obj_name, count in result['object_details'].items():
                print(f"      - {obj_name}: {count}個")
        
        print(f"\n⏱️  処理時間:")
        print(f"   ⏰ 総時間: {result.get('processing_time', 0):.3f}秒")
        
        if result.get('inference_speed'):
            speed = result['inference_speed']
            print(f"   ⚡ 前処理: {speed.get('preprocess', 0):.1f}ms")
            print(f"   🚀 推論: {speed.get('inference', 0):.1f}ms")
            print(f"   ✨ 後処理: {speed.get('postprocess', 0):.1f}ms")
        
        # 結果画像を保存（オプション）
        if result.get('image_base64'):
            import base64
            output_path = img_file.parent / f"{img_file.stem}_detected{img_file.suffix}"
            
            img_data = base64.b64decode(result['image_base64'])
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            print(f"\n💾 結果画像を保存: {output_path}")
        
        print("\n" + "=" * 60)
        print("完全なJSONレスポンス:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except requests.exceptions.Timeout:
        print("❌ タイムアウトエラー: リクエストが90秒を超えました")
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: サーバーが起動していることを確認してください")
        print("   サーバー起動: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ エラー: {e}")


def main():
    if len(sys.argv) < 2:
        print("使い方: python test_api.py <画像パス>")
        print("例: python test_api.py sample.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # カスタムURLの場合
    api_url = "http://localhost:8000/predict/"
    if len(sys.argv) >= 3:
        api_url = sys.argv[2]
    
    run_detection_api(image_path, api_url)


if __name__ == "__main__":
    main()
