#!/usr/bin/env python3
"""
拍摄冰箱照片后，用 Qwen3-VL 识别食材，可选与菜谱对比。

用法:
  # 仅识别冰箱食材
  python3 check_fridge.py --image ~/cam-snapshots/fridge.jpg

  # 识别 + 与菜谱对比
  python3 check_fridge.py --image ~/cam-snapshots/fridge.jpg --recipe ~/recipes/红烧肉/recipe.json
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

# Try to load API key from .env if not in environment
def load_api_key():
    key = os.environ.get("DASHSCOPE_API_KEY", "")
    if key:
        return key
    for env_path in [
        Path.home() / "Desktop/homepaw/omni-realtime-code/.env",
        Path.home() / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DASHSCOPE_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return ""


def encode_image(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def identify_fridge(image_path: str, api_key: str) -> list:
    """Use Qwen3-VL to identify food items in the fridge photo."""
    try:
        from openai import OpenAI
    except ImportError:
        print("[ERROR] pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    img_b64 = encode_image(image_path)
    suffix = Path(image_path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(suffix, "image/jpeg")

    resp = client.chat.completions.create(
        model="qwen3-vl-plus",
        messages=[
            {"role": "system", "content": "你是食材识别专家。只输出合法 JSON 数组，不要输出其他文字。"},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                {"type": "text", "text": """请仔细观察这张冰箱/食材照片，识别所有可见的食材。

输出 JSON 数组：
[
  {"name": "食材名", "quantity": "大致数量(如 约3个、一袋、半盒)", "confidence": 0.0到1.0}
]

要求：
1. 识别所有可见食材，包括蔬菜、水果、肉类、蛋类、调味品、饮料等
2. 数量用自然语言描述
3. confidence 表示识别置信度
4. 只输出 JSON 数组"""},
            ]},
        ],
        temperature=0.2,
    )

    raw = resp.choices[0].message.content.strip()
    # Debug: print raw response
    print(f"[DEBUG] VL raw response: {raw[:300]}", file=sys.stderr)
    
    # Strip markdown code blocks
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    
    # Strip thinking tags (Qwen3 sometimes adds these)
    raw = re.sub(r'<think>[\s\S]*?</think>', '', raw)
    
    # Extract JSON array
    m = re.search(r'\[[\s\S]*\]', raw)
    if m:
        raw = m.group()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"[WARN] JSON 解析失败: {raw[:300]}", file=sys.stderr)
        return []


def compare_with_recipe(fridge_items: list, recipe: dict) -> dict:
    """Compare fridge contents with recipe requirements."""
    needed = recipe.get("ingredients", [])
    fridge_map = {}
    for item in fridge_items:
        fridge_map[item["name"].lower()] = item

    # Common seasonings/condiments assumed to be available at home
    common = {"盐", "糖", "白糖", "冰糖", "食用油", "油", "酱油", "生抽", "老抽",
              "醋", "料酒", "黄酒", "胡椒粉", "味精", "鸡精", "淀粉", "水淀粉",
              "花椒", "辣椒", "干辣椒", "蚝油", "香油", "芝麻油", "豆瓣酱",
              "葱", "姜", "蒜", "大葱", "小葱", "香葱", "姜片", "蒜片",
              "八角", "桂皮", "香叶", "草果", "丁香", "小茴香", "大料",
              "五香粉", "十三香", "白胡椒", "黑胡椒", "孜然",
              "番茄酱", "豆豉", "腐乳", "甜面酱", "芝麻酱",
              "水", "热水", "开水", "清水", "温水"}

    comparison = []
    missing = []

    for ing in needed:
        name = ing["name"]
        qty = ing.get("quantity", "适量")
        is_seasoning = name in common or ing.get("category") in ("调味料", "调味", "香料")

        # Fuzzy match
        found = None
        for fn, fi in fridge_map.items():
            if name.lower() in fn or fn in name.lower():
                found = fi
                break

        if found:
            comparison.append({
                "name": name, "needed": qty,
                "have": found["detected_quantity"] if "detected_quantity" in found else found.get("quantity", "有"),
                "status": "ok",
            })
        elif is_seasoning:
            comparison.append({
                "name": name, "needed": qty,
                "have": "默认已有(调味料)", "status": "ok",
            })
        else:
            comparison.append({
                "name": name, "needed": qty,
                "have": "未检测到", "status": "missing",
            })
            missing.append({"name": name, "quantity": qty})

    return {
        "dish": recipe.get("dish", ""),
        "fridge_items": fridge_items,
        "comparison": comparison,
        "missing_items": missing,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="冰箱照片路径")
    parser.add_argument("--recipe", help="菜谱 JSON 路径（可选，用于对比）")
    args = parser.parse_args()

    img = Path(args.image).expanduser()
    if not img.exists():
        print(f"[ERROR] 图片不存在: {img}", file=sys.stderr)
        sys.exit(1)

    api_key = load_api_key()
    if not api_key:
        print("[ERROR] DASHSCOPE_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 识别冰箱食材...", file=sys.stderr)
    items = identify_fridge(str(img), api_key)
    print(f"🥬 识别到 {len(items)} 种食材", file=sys.stderr)

    if args.recipe:
        rp = Path(args.recipe).expanduser()
        if not rp.exists():
            print(f"[ERROR] 菜谱不存在: {rp}", file=sys.stderr)
            sys.exit(1)
        recipe = json.loads(rp.read_text("utf-8"))
        print(f"📊 与「{recipe.get('dish','')}」菜谱对比...", file=sys.stderr)
        result = compare_with_recipe(items, recipe)
        n = len(result["missing_items"])
        if n:
            print(f"⚠️  缺少 {n} 种食材", file=sys.stderr)
        else:
            print("🎉 食材齐全！", file=sys.stderr)
    else:
        result = {"fridge_items": items}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
