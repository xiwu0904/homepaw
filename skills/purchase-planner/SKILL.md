---
name: purchase-planner
description: "根据缺少的食材生成采购计划，发送审批请求，审批通过后自动通过淘宝闪购下单。当冰箱检查发现缺少食材时使用。"
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["DASHSCOPE_API_KEY"]
    primaryEnv: "DASHSCOPE_API_KEY"
---

# 采购计划与自动下单 (Purchase Planner)

根据冰箱检查结果中缺少的食材，生成采购计划，发送给用户审批，审批通过后自动下单。

## 触发条件

- 冰箱检查完成后发现缺少食材
- 用户说"帮我买食材"或"下单"
- 烹饪工作流的第三步

## 前置依赖

- 需要先运行 `fridge-check` 技能获取缺少食材清单

## 指令

### 步骤 1：生成采购计划

运行 `python3 scripts/plan_purchase.py --missing "/tmp/openclaw_fridge_check_{dish}.json"`

脚本会：
1. 读取缺少的食材清单
2. 估算价格
3. 生成采购计划

### 步骤 2：发送审批请求

将采购计划通过 DingTalk 发送给用户，格式如下：

```
🛒 食材采购计划 - {菜名}

缺少食材：
1. 番茄 x1  ~¥3
2. 鸡蛋 x4  ~¥8

预计总价：¥11
配送方式：淘宝闪购（约30分钟送达）

请回复"确认下单"或"取消"
```

### 步骤 3：等待用户审批

- 用户回复"确认"/"下单"/"好的" → 执行下单
- 用户回复"取消"/"不用了" → 取消采购
- 用户修改数量 → 更新计划后重新确认

### 步骤 4：自动下单

运行 `python3 scripts/place_order.py --plan "/tmp/openclaw_purchase_plan_{dish}.json"`

注意：自动下单功能需要预先配置淘宝/盒马的登录凭证。如果未配置或下单失败，
生成一个预填好的购物链接发送给用户，让用户手动完成最后一步支付。

## 输出格式

采购计划 JSON：
```json
{
  "dish": "西红柿炒鸡蛋",
  "items": [
    {"name": "番茄", "quantity": "1个", "est_price": 3.0, "search_keyword": "新鲜番茄"},
    {"name": "鸡蛋", "quantity": "4个", "est_price": 8.0, "search_keyword": "鲜鸡蛋"}
  ],
  "total_est_price": 11.0,
  "platform": "taobao_flash",
  "status": "pending_approval"
}
```

## 错误处理

- 自动下单失败 → 生成购物链接，发送给用户手动下单
- 价格异常（单品超过50元）→ 提醒用户确认
- 平台不可用 → 切换到备选平台（盒马/美团买菜）

## 示例用法

Agent: "根据冰箱检查，需要采购：
🛒 番茄 1个 ~¥3
🛒 鸡蛋 4个 ~¥8
预计总价 ¥11，淘宝闪购约30分钟送达。确认下单吗？"

用户: "确认下单"
Agent: [运行 place_order.py]
Agent: "已下单成功！订单号 TB20260326xxx，预计30分钟内送达。我先帮你准备烹饪指南。"
