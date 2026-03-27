#!/usr/bin/env python3
"""
自动下单脚本 - 通过淘宝闪购/盒马下单。
如果自动下单失败，生成购物链接供用户手动下单。

用法: python3 place_order.py --plan /tmp/openclaw_purchase_plan_西红柿炒鸡蛋.json
"""

import argparse
import json
import sys
import urllib.parse
from pathlib import Path


def generate_taobao_search_url(keyword: str) -> str:
    """生成淘宝搜索链接"""
    encoded = urllib.parse.quote(keyword)
    return f"https://s.taobao.com/search?q={encoded}"


def generate_taobao_flash_deeplink(items: list[dict]) -> str:
    """
    生成淘鲜达/淘宝买菜的深度链接。
    注意：实际的淘宝闪购 API 需要商家入驻和 OAuth 授权，
    这里生成搜索链接作为 fallback。
    """
    keywords = " ".join(item["search_keyword"] for item in items)
    encoded = urllib.parse.quote(keywords)
    return f"https://market.m.taobao.com/app/supermarket/h5-search/index.html?q={encoded}"


def try_auto_order(plan: dict) -> dict:
    """
    尝试自动下单。

    实际实现需要：
    1. Playwright 浏览器自动化 + 预登录的 cookie
    2. 或者接入淘宝开放平台 API（需要商家资质）
    3. 或者接入盒马/美团买菜的开放 API

    当前实现：生成购物链接，让用户手动完成最后一步。
    """
    items = plan.get("items", [])

    # TODO: 实现真正的自动下单
    # 以下是 fallback 方案：生成购物链接
    order_result = {
        "status": "manual_required",
        "message": "自动下单功能开发中，已为您生成购物链接",
        "links": [],
        "items": [],
    }

    for item in items:
        link = generate_taobao_search_url(item["search_keyword"])
        order_result["links"].append({
            "name": item["name"],
            "quantity": item["quantity"],
            "url": link,
        })
        order_result["items"].append(item)

    # 生成一键购物链接（淘鲜达）
    order_result["one_click_url"] = generate_taobao_flash_deeplink(items)

    return order_result


def format_order_message(result: dict) -> str:
    """格式化下单结果为用户消息"""
    if result["status"] == "success":
        return f"✅ 下单成功！订单号: {result.get('order_id', 'N/A')}\n预计送达时间: {result.get('eta', '30分钟')}"

    lines = ["📱 已为您准备好购物链接：", ""]

    # 一键链接
    if result.get("one_click_url"):
        lines.append(f"🔗 一键购买: {result['one_click_url']}")
        lines.append("")

    # 单品链接
    lines.append("或分别搜索：")
    for link in result.get("links", []):
        lines.append(f"  • {link['name']} x{link['quantity']}: {link['url']}")

    lines.append("\n💡 点击链接后选择「淘鲜达」或「小时达」可快速配送")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="自动下单或生成购物链接")
    parser.add_argument("--plan", required=True, help="采购计划 JSON 路径")
    parser.add_argument("--output", help="输出文件路径")
    args = parser.parse_args()

    if not Path(args.plan).exists():
        print(f"[ERROR] 文件不存在: {args.plan}", file=sys.stderr)
        sys.exit(1)

    with open(args.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)

    if plan.get("status") == "no_purchase_needed":
        print("无需采购", file=sys.stderr)
        print(json.dumps({"status": "no_purchase_needed"}))
        return

    print("🛒 正在尝试下单...", file=sys.stderr)
    result = try_auto_order(plan)

    # 保存结果
    dish = plan.get("dish", "unknown")
    output_path = args.output or f"/tmp/openclaw_order_{dish}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    message = format_order_message(result)
    print(message, file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
