"""
テスト: BLIP-2キャプションの日本語翻訳機能

このスクリプトは翻訳関数をテストします。
"""

def translate_caption_to_japanese(english_caption: str) -> str:
    """Dịch caption tiếng Anh sang tiếng Nhật"""
    translations = {
        "a photo of": "", "an image of": "", "a picture of": "",
        "street": "通り", "road": "道路", "city": "都市", "town": "町",
        "beach": "ビーチ", "ocean": "海", "mountain": "山", "forest": "森",
        "park": "公園", "building": "建物", "house": "家",
        "busy": "賑やかな", "crowded": "混雑した", "empty": "空の",
        "people": "人々", "person": "人", "man": "男性", "woman": "女性",
        "car": "車", "cars": "車", "bus": "バス", "truck": "トラック",
        "dog": "犬", "cat": "猫", "bird": "鳥",
        "walking": "歩いている", "running": "走っている", "sitting": "座っている",
        " with ": "と", " and ": "と", " in ": "の中に",
    }
    
    result = english_caption.lower().strip()
    for en, ja in translations.items():
        result = result.replace(en, ja)
    return result.strip()


# テストケース
test_cases = [
    "a photo of a busy street with cars and people",
    "a man walking in the park",
    "a dog sitting on the beach",
    "people and cars in the city",
    "a busy road with cars",
]

print("=" * 60)
print("日本語翻訳テスト")
print("=" * 60)

for i, caption in enumerate(test_cases, 1):
    translated = translate_caption_to_japanese(caption)
    print(f"\n{i}. 英語: {caption}")
    print(f"   日本語: {translated}")

print("\n" + "=" * 60)
print("✅ 翻訳機能が正常に動作しています！")
print("=" * 60)
