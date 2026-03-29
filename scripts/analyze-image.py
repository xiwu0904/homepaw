#!/usr/bin/env python3
"""
通用图片分析脚本，调用 Qwen3-VL-Plus API。
用于分析小红书截图、菜谱图片等。

用法:
  python3 analyze-image.py --image /path/to/image.jpg --prompt "请提取图片中的菜谱内容"
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path


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


def analyze(image_path: str, prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    img_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    suffix = Path(image_path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp"}.get(suffix, "image/jpeg")

    resp = client.chat.completions.create(
        model="qwen3-vl-plus",
        messages=[
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                {"type": "text", "text": prompt},
            ]},
        ],
        temperature=0.3,
    )

    raw = resp.choices[0].message.content.strip()
    # Strip thinking tags
    raw = re.sub(r'<think>[\s\S]*?</think>', '', raw).strip()
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    img = Path(args.image).expanduser()
    if not img.exists():
        print(f"ERROR: {img} not found", file=sys.stderr)
        sys.exit(1)

    api_key = load_api_key()
    if not api_key:
        print("ERROR: DASHSCOPE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    result = analyze(str(img), args.prompt, api_key)
    print(result)


if __name__ == "__main__":
    main()
