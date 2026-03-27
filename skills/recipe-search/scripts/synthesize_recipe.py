#!/usr/bin/env python3
"""
用 Qwen 综合从小红书浏览器提取的菜谱内容，生成标准化 JSON。
浏览器搜索由 OpenClaw 的 browser 工具完成，本脚本只做 AI 综合。

用法:
  # 有小红书内容时：
  python3 synthesize_recipe.py --dish "西红柿炒鸡蛋" --content "帖子1内容\n帖子2内容"

  # 降级模式（浏览器不可用）：
  python3 synthesize_recipe.py --dish "西红柿炒鸡蛋" --skip-xhs
"""

import argparse
import json
import os
import re
import sys

try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] 需要安装 openai: pip install openai", file=sys.stderr)
    sys.exit(1)


def synthesize(dish: str, xhs_content: str = "") -> dict:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("[ERROR] DASHSCOPE_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    if xhs_content.strip():
        context = f"以下是从小红书搜索到的「{dish}」菜谱内容（多个帖子）：\n\n{xhs_content}"
    else:
        context = f"请根据你的知识，为「{dish}」生成一份详细的家常菜谱。"

    prompt = f"""{context}

请综合以上内容，生成标准化菜谱 JSON：
{{
  "dish": "菜名",
  "summary": "一句话简介（20字内）",
  "prep_time": "准备时间",
  "cook_time": "烹饪时间",
  "difficulty": "简单/中等/困难",
  "servings": "几人份",
  "ingredients": [
    {{"name": "食材名", "quantity": "用量", "category": "蔬菜/肉类/蛋类/调味料/主食/其他", "essential": true}}
  ],
  "steps": [
    {{"step": 1, "description": "步骤描述", "tips": "小贴士（可选）"}}
  ],
  "tips": ["额外烹饪技巧"],
  "source": "小红书菜谱综合"
}}

要求：essential=false 用于调味料/辅料；只输出 JSON，不要其他文字。"""

    resp = client.chat.completions.create(
        model="qwen-max",
        messages=[
            {"role": "system", "content": "你是专业中餐厨师。只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    raw = resp.choices[0].message.content.strip()
    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        raw = m.group()

    try:
        recipe = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析失败: {e}\n原始: {raw[:300]}", file=sys.stderr)
        sys.exit(1)

    return recipe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dish", required=True)
    parser.add_argument("--content", default="", help="从浏览器提取的小红书帖子内容")
    parser.add_argument("--skip-xhs", action="store_true", help="跳过小红书内容，直接用 AI 生成")
    parser.add_argument("--output", help="输出路径，默认 /tmp/openclaw_recipe_{dish}.json")
    args = parser.parse_args()

    dish = args.dish.strip()
    content = "" if args.skip_xhs else args.content

    if content:
        print(f"🤖 综合 {len(content.splitlines())} 行小红书内容...", file=sys.stderr)
    else:
        print(f"🤖 用 AI 知识直接生成「{dish}」菜谱...", file=sys.stderr)

    recipe = synthesize(dish, content)

    out = args.output or f"/tmp/openclaw_recipe_{dish}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(recipe, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {out}", file=sys.stderr)

    print(json.dumps(recipe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
