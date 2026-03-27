#!/usr/bin/env python3
"""
搜索小红书菜谱并用 Qwen 综合生成标准化菜谱。
回退策略：如果小红书搜索失败，直接用 Qwen 生成菜谱。

用法: python3 search_recipe.py --dish "西红柿炒鸡蛋"
"""

import argparse
import json
import os
import sys
import re
import time
import random
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("需要安装 openai: pip install openai", file=sys.stderr)
    sys.exit(1)


def search_xiaohongshu(dish: str, max_results: int = 5) -> list[dict]:
    """
    搜索小红书获取菜谱内容。
    使用 requests + 简单解析，避免重量级浏览器依赖。
    """
    try:
        import requests
    except ImportError:
        print("[WARN] requests 未安装，跳过小红书搜索", file=sys.stderr)
        return []

    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.xiaohongshu.com/",
        }

        search_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
        params = {
            "keyword": f"{dish} 菜谱 做法",
            "page": 1,
            "page_size": max_results,
            "sort": "general",
            "note_type": 0,
        }

        resp = requests.get(search_url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", {}).get("items", [])
            for item in items[:max_results]:
                note = item.get("note_card", {})
                results.append({
                    "title": note.get("display_title", ""),
                    "desc": note.get("desc", ""),
                    "likes": note.get("interact_info", {}).get("liked_count", "0"),
                    "image_url": note.get("cover", {}).get("url_default", ""),
                })
        else:
            print(f"[WARN] 小红书搜索返回 {resp.status_code}", file=sys.stderr)

    except Exception as e:
        print(f"[WARN] 小红书搜索失败: {e}", file=sys.stderr)

    return results


def synthesize_recipe_with_qwen(dish: str, xhs_results: list[dict]) -> dict:
    """
    使用 Qwen API 综合小红书搜索结果（或直接生成）标准化菜谱。
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("[ERROR] DASHSCOPE_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 构建 prompt
    if xhs_results:
        refs = "\n\n".join(
            f"【参考菜谱 {i+1}】\n标题: {r['title']}\n内容: {r['desc']}"
            for i, r in enumerate(xhs_results)
        )
        context = f"以下是从小红书搜索到的关于「{dish}」的菜谱参考：\n\n{refs}"
    else:
        context = f"请根据你的知识，为「{dish}」生成一份详细的家常菜谱。"

    prompt = f"""{context}

请综合以上信息，生成一份标准化的菜谱 JSON，格式如下：
{{
  "dish": "菜名",
  "summary": "一句话简介（30字以内）",
  "prep_time": "准备时间",
  "cook_time": "烹饪时间",
  "difficulty": "简单/中等/困难",
  "servings": "几人份",
  "ingredients": [
    {{"name": "食材名", "quantity": "用量", "category": "分类(蔬菜/肉类/蛋类/调味料/主食/其他)", "essential": true}}
  ],
  "steps": [
    {{"step": 1, "description": "步骤描述", "tips": "小贴士(可选)", "duration": "耗时(可选)"}}
  ],
  "tips": ["额外烹饪技巧"]
}}

要求：
1. 食材清单必须完整，包括油、盐等调味料
2. essential 字段标记是否为核心食材（调味料为 false）
3. 步骤要详细到新手也能跟着做
4. 只输出 JSON，不要其他文字"""

    response = client.chat.completions.create(
        model="qwen-max",
        messages=[
            {"role": "system", "content": "你是一位专业的中餐厨师和菜谱编辑。只输出合法的 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()

    # 提取 JSON（处理可能的 markdown 包裹）
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        content = json_match.group()

    try:
        recipe = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Qwen 返回的 JSON 解析失败: {e}", file=sys.stderr)
        print(f"[DEBUG] 原始内容: {content[:500]}", file=sys.stderr)
        sys.exit(1)

    # 附加小红书来源信息
    recipe["source_urls"] = []
    recipe["images"] = []
    for r in xhs_results:
        if r.get("image_url"):
            recipe["images"].append(r["image_url"])

    return recipe


def main():
    parser = argparse.ArgumentParser(description="搜索并生成标准化菜谱")
    parser.add_argument("--dish", required=True, help="菜名")
    parser.add_argument("--skip-xhs", action="store_true", help="跳过小红书搜索，直接用 AI 生成")
    parser.add_argument("--output", help="输出文件路径（默认 /tmp/openclaw_recipe_{dish}.json）")
    args = parser.parse_args()

    dish = args.dish.strip()
    print(f"🔍 正在搜索「{dish}」的菜谱...", file=sys.stderr)

    # Step 1: 搜索小红书
    xhs_results = []
    if not args.skip_xhs:
        xhs_results = search_xiaohongshu(dish)
        if xhs_results:
            print(f"📝 找到 {len(xhs_results)} 个小红书菜谱参考", file=sys.stderr)
        else:
            print("⚠️  小红书搜索无结果，将使用 AI 直接生成菜谱", file=sys.stderr)

    # Step 2: AI 综合生成
    print("🤖 正在用 AI 综合生成标准化菜谱...", file=sys.stderr)
    recipe = synthesize_recipe_with_qwen(dish, xhs_results)

    # Step 3: 保存结果
    output_path = args.output or f"/tmp/openclaw_recipe_{dish}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(recipe, f, ensure_ascii=False, indent=2)
    print(f"✅ 菜谱已保存到: {output_path}", file=sys.stderr)

    # 输出到 stdout 供 OpenClaw 读取
    print(json.dumps(recipe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
