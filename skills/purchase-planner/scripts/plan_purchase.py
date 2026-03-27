#!/usr/bin/env python3
"""
根据缺少食材清单生成采购计划。

用法: python3 plan_purchase.py --missing /tmp/openclaw_fridge_check_西红柿炒鸡蛋.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("需要安装 openai: pip install openai", file=sys.stderr)
    sys.exit(1)


# 常见食材参考价格（元）
PRICE_REFERENCE = {
    "番茄": 2.5, "西红柿": 2.5, "鸡蛋": 1.5, "鸡蛋(个)": 1.5,
    "葱": 1.0, "姜": 2.0, "蒜": 2.0, "洋葱": 3.0,
    "土豆": 2.0, "胡萝卜": 2.0, "白菜": 3.0, "青椒": 3.0,
    "猪肉": 15.0, "牛肉": 35.0, "鸡肉": 12.0, "鱼": 20.0,
    "豆腐": 3.0, "米饭": 5.0, "面条": 4.0, "米": 5.0,
}


def estimate_price(name: str, quantity: str) -> float:
    """估算食材价格"""
    # 从参考价格表查找
    base_price = None
    for key, price in PRICE_REFERENCE.items():
        if key in name or name in key:
            base_price = price
            break

    if base_price is None:
        base_price = 5.0  # 默认价格

    # 尝试从数量中提取数字
    import re
    nums = re.findall(r'(\d+)', quantity)
    multiplier = int(nums[0]) if nums else 1

    return round(base_price * multiplier, 1)


def generate_purchase_plan(fridge_check_path: str) -> dict:
    """生成采购计划"""
    with open(fridge_check_path, "r", encoding="utf-8") as f:
        check_result = json.load(f)

    dish = check_result.get("dish", "")
    missing = check_result.get("missing_items", [])

    if not missing:
        return {
            "dish": dish,
            "items": [],
            "total_est_price": 0,
            "platform": "none",
            "status": "no_purchase_needed",
            "message": "食材齐全，无需采购",
        }

    items = []
    total = 0.0

    for item in missing:
        name = item["name"]
        quantity = item["quantity"]
        est_price = estimate_price(name, quantity)
        total += est_price

        items.append({
            "name": name,
            "quantity": quantity,
            "est_price": est_price,
            "search_keyword": f"新鲜{name}" if name not in ("鸡蛋",) else name,
            "reason": item.get("reason", ""),
        })

    plan = {
        "dish": dish,
        "items": items,
        "total_est_price": round(total, 1),
        "platform": "taobao_flash",
        "platform_alternatives": ["hema", "meituan"],
        "status": "pending_approval",
        "estimated_delivery": "约30分钟",
    }

    return plan


def format_plan_message(plan: dict) -> str:
    """格式化采购计划为用户可读消息"""
    if plan["status"] == "no_purchase_needed":
        return f"🎉 做「{plan['dish']}」的食材齐全，无需采购！"

    lines = [f"🛒 食材采购计划 - {plan['dish']}", ""]
    lines.append("缺少食材：")
    for i, item in enumerate(plan["items"], 1):
        lines.append(f"  {i}. {item['name']} x{item['quantity']}  ~¥{item['est_price']}")

    lines.append(f"\n💰 预计总价：¥{plan['total_est_price']}")
    lines.append(f"🚚 配送方式：淘宝闪购（{plan['estimated_delivery']}）")
    lines.append("\n请回复「确认下单」或「取消」")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成食材采购计划")
    parser.add_argument("--missing", required=True, help="冰箱检查结果 JSON 路径")
    parser.add_argument("--output", help="输出文件路径")
    args = parser.parse_args()

    if not Path(args.missing).exists():
        print(f"[ERROR] 文件不存在: {args.missing}", file=sys.stderr)
        sys.exit(1)

    print("📋 正在生成采购计划...", file=sys.stderr)
    plan = generate_purchase_plan(args.missing)

    # 保存计划
    dish = plan.get("dish", "unknown")
    output_path = args.output or f"/tmp/openclaw_purchase_plan_{dish}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"✅ 采购计划已保存到: {output_path}", file=sys.stderr)

    # 输出可读消息
    message = format_plan_message(plan)
    print(f"\n{message}", file=sys.stderr)

    # JSON 输出供 OpenClaw 读取
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
