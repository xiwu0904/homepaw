#!/usr/bin/env python3
"""
根据菜谱 JSON 生成图文并茂的 HTML 烹饪指南。
图片支持：本地路径(嵌入base64)、URL(直接引用)、缺失(跳过)。

用法: python3 generate_guide.py --recipe ~/recipes/红烧肉/recipe.json
"""

import argparse
import base64
import json
import sys
from datetime import date
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{dish} - 烹饪指南</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #1a1a2e; color: #e0e0e0; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
.cover {{ text-align: center; padding: 60px 20px; border-bottom: 2px solid #ff6b35; margin-bottom: 40px; }}
.cover h1 {{ font-size: 48px; margin-bottom: 12px; }}
.cover .subtitle {{ color: #ff6b35; font-size: 20px; margin-bottom: 16px; }}
.cover .meta {{ color: #aaa; font-size: 14px; }}
.section {{ margin-bottom: 40px; }}
.section-title {{ font-size: 24px; color: #ff6b35; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 1px solid #333; }}
.ingredients {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.ing-item {{ display: flex; justify-content: space-between; padding: 8px 12px; background: #16213e; border-radius: 6px; }}
.ing-name {{ color: #e0e0e0; }}
.ing-qty {{ color: #4fc3f7; }}
.ing-essential::before {{ content: "●"; color: #ff6b35; margin-right: 6px; }}
.ing-optional::before {{ content: "○"; color: #666; margin-right: 6px; }}
.step {{ background: #16213e; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
.step-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
.step-num {{ background: #ff6b35; color: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; }}
.step-title {{ font-size: 18px; font-weight: 600; }}
.step-desc {{ font-size: 16px; line-height: 1.8; margin-bottom: 12px; }}
.step-tip {{ background: rgba(0,230,118,0.1); border-left: 3px solid #00e676; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 14px; color: #aaa; margin-bottom: 12px; }}
.step-tip::before {{ content: "💡 "; }}
.step-img {{ width: 100%; max-height: 400px; object-fit: cover; border-radius: 8px; margin-top: 12px; }}
.tips {{ list-style: none; }}
.tips li {{ padding: 10px 14px; margin-bottom: 8px; background: #16213e; border-radius: 6px; font-size: 15px; }}
.tips li::before {{ content: "🎯 "; }}
.footer {{ text-align: center; padding: 30px; color: #666; font-size: 13px; border-top: 1px solid #333; margin-top: 40px; }}
.cover-img {{ width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; margin-bottom: 20px; }}
@media (max-width: 600px) {{
  .ingredients {{ grid-template-columns: 1fr; }}
  .cover h1 {{ font-size: 32px; }}
}}
</style>
</head>
<body>
<div class="container">
{content}
</div>
</body>
</html>"""


def resolve_image(path_or_url: str) -> str:
    """Local file -> base64 data URI; URL -> use directly; missing -> empty."""
    if not path_or_url:
        return ""
    # Expand ~ in paths
    expanded = str(Path(path_or_url).expanduser()) if not path_or_url.startswith("http") else path_or_url
    p = Path(expanded)
    if p.exists() and p.is_file():
        suffix = p.suffix.lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "gif": "image/gif", "webp": "image/webp"}.get(suffix, "image/jpeg")
        try:
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f"data:{mime};base64,{b64}"
        except Exception:
            return ""
    if path_or_url.startswith("http"):
        return path_or_url
    return ""


def img_tag(src: str, alt: str, css_class: str) -> str:
    resolved = resolve_image(src)
    if not resolved:
        return ""
    return f'<img class="{css_class}" src="{resolved}" alt="{alt}">'


def generate_html(recipe: dict) -> str:
    dish = recipe.get("dish", "美味佳肴")
    summary = recipe.get("summary", "")
    difficulty = recipe.get("difficulty", "中等")
    prep_time = recipe.get("prep_time", "")
    cook_time = recipe.get("cook_time", "")
    servings = recipe.get("servings", "")

    parts = []

    # Cover
    cover_img = ""
    for img in recipe.get("images", []):
        cover_img = img_tag(img, dish, "cover-img")
        if cover_img:
            break

    meta_parts = [f for f in [
        f"难度: {difficulty}" if difficulty else "",
        f"准备: {prep_time}" if prep_time else "",
        f"烹饪: {cook_time}" if cook_time else "",
        servings,
    ] if f]

    parts.append(f"""<div class="cover">
{cover_img}
<h1>{dish}</h1>
<div class="subtitle">🍳 {summary}</div>
<div class="meta">{' | '.join(meta_parts)}<br>{date.today().isoformat()} · HomePaw 智能烹饪</div>
</div>""")

    # Ingredients
    ingredients = recipe.get("ingredients", [])
    if ingredients:
        items_html = ""
        for ing in ingredients:
            cls = "ing-essential" if ing.get("essential", True) else "ing-optional"
            items_html += f'<div class="ing-item"><span class="ing-name {cls}">{ing.get("name","")}</span><span class="ing-qty">{ing.get("quantity","适量")}</span></div>\n'
        parts.append(f'<div class="section"><div class="section-title">📋 食材清单</div><div class="ingredients">{items_html}</div></div>')

    # Steps
    steps = recipe.get("steps", [])
    if steps:
        steps_html = ""
        for i, step in enumerate(steps):
            num = step.get("step", i + 1)
            desc = step.get("description", "")
            tip = step.get("tips", "")
            tip_html = f'<div class="step-tip">{tip}</div>' if tip else ""
            step_img = img_tag(step.get("image", ""), f"步骤{num}", "step-img")
            steps_html += f'<div class="step"><div class="step-header"><div class="step-num">{num}</div><div class="step-title">步骤 {num}</div></div><div class="step-desc">{desc}</div>{tip_html}{step_img}</div>\n'
        parts.append(f'<div class="section"><div class="section-title">👨\u200d🍳 烹饪步骤</div>{steps_html}</div>')

    # Tips
    tips = recipe.get("tips", [])
    if tips:
        tips_html = "\n".join(f"<li>{t}</li>" for t in tips)
        parts.append(f'<div class="section"><div class="section-title">🎯 烹饪技巧</div><ul class="tips">{tips_html}</ul></div>')

    parts.append(f'<div class="footer">祝您做菜愉快！🍽️<br>来源: {recipe.get("source","")}</div>')
    return HTML_TEMPLATE.format(dish=dish, content="\n".join(parts))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    rp = Path(args.recipe).expanduser()
    if not rp.exists():
        print(f"[ERROR] 不存在: {rp}", file=sys.stderr)
        sys.exit(1)

    recipe = json.loads(rp.read_text("utf-8"))
    dish = recipe.get("dish", "unknown")
    out = Path(args.output).expanduser() if args.output else rp.parent / f"{dish}.html"

    html = generate_html(recipe)
    out.write_text(html, "utf-8")
    print(f"✅ {out} ({len(html)} bytes)", file=sys.stderr)
    print(json.dumps({"dish": dish, "output_path": str(out), "status": "success"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
