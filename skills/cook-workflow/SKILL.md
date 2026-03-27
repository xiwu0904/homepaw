---
name: cook-workflow
description: "完整的智能烹饪工作流编排。当用户说想做某道菜时，自动串联菜谱搜索→冰箱检查→采购下单→烹饪指南生成的全流程。"
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["DASHSCOPE_API_KEY"]
    primaryEnv: "DASHSCOPE_API_KEY"
---

# 智能烹饪工作流 (Cook Workflow Orchestrator)

这是一个编排技能，当用户表达"我要回家做菜"的意图时，自动串联所有烹饪相关技能，完成从菜谱搜索到烹饪指南生成的全流程。

## 触发条件

- 用户说"我快到家了，想做XXX"
- 用户说"今晚做XXX"
- 任何包含"做菜"+"菜名"的意图

## 完整工作流

```
用户消息 → 提取菜名
         ↓
  ┌──────────────────┐
  │ 1. recipe-search │  搜索小红书 + AI 生成菜谱
  │    菜谱搜索       │  输出: /tmp/openclaw_recipe_{dish}.json
  └────────┬─────────┘
           ↓ 向用户展示菜谱，确认后继续
  ┌──────────────────┐
  │ 2. 摄像头快照     │  使用 OpenClaw 内置摄像头技能
  │    (内置技能)     │  拍摄冰箱照片
  └────────┬─────────┘
           ↓
  ┌──────────────────┐
  │ 3. fridge-check  │  AI 识别冰箱食材 + 对比菜谱
  │    冰箱检查       │  输出: /tmp/openclaw_fridge_check_{dish}.json
  └────────┬─────────┘
           ↓
       缺少食材？──── 否 ──→ 跳到步骤 5
           │ 是
           ↓
  ┌──────────────────┐
  │ 4. purchase-     │  生成采购计划 → 用户审批 → 下单
  │    planner       │  通过 DingTalk 发送审批请求
  └────────┬─────────┘
           ↓ 等待用户确认
  ┌──────────────────┐
  │ 5. cooking-guide │  生成 PPT 烹饪指南
  │    烹饪指南       │  输出: /tmp/openclaw_guide_{dish}.pptx
  └────────┬─────────┘
           ↓
     发送指南给用户（DingTalk）
     完成 ✅
```

## 执行指令

当检测到用户的做菜意图时，按以下顺序执行：

### Step 1: 提取菜名并搜索菜谱
从用户消息中提取菜名，然后调用 recipe-search 技能：
```
python3 .qoder/skills/recipe-search/scripts/search_recipe.py --dish "{菜名}"
```
展示菜谱摘要给用户，等待确认。

### Step 2: 拍摄冰箱照片
使用 OpenClaw 内置的摄像头快照技能拍摄冰箱照片。
提示用户："正在查看冰箱..."

### Step 3: 检查冰箱食材
```
python3 .qoder/skills/fridge-check/scripts/check_fridge.py \
  --image "{冰箱照片路径}" \
  --recipe "/tmp/openclaw_recipe_{dish}.json"
```
展示对比结果给用户。

### Step 4: 采购（如需要）
如果有缺少的食材：
```
python3 .qoder/skills/purchase-planner/scripts/plan_purchase.py \
  --missing "/tmp/openclaw_fridge_check_{dish}.json"
```
通过 DingTalk 发送采购计划，等待用户审批。
审批通过后：
```
python3 .qoder/skills/purchase-planner/scripts/place_order.py \
  --plan "/tmp/openclaw_purchase_plan_{dish}.json"
```

### Step 5: 生成烹饪指南
```
python3 .qoder/skills/cooking-guide/scripts/generate_guide.py \
  --recipe "/tmp/openclaw_recipe_{dish}.json"
```
将 PPT 文件通过 DingTalk 发送给用户。

## 状态管理

每个步骤完成后，向用户报告进度：
- "🔍 正在搜索菜谱..."
- "📷 正在查看冰箱..."
- "📊 正在对比食材..."
- "🛒 生成采购计划中..."
- "📖 正在生成烹饪指南..."
- "✅ 全部完成！祝您做菜愉快！"

## 中断处理

- 用户随时可以说"取消"终止流程
- 如果某个步骤失败，报告错误并询问是否跳过或重试
- 采购步骤可以跳过（用户可能自己去买）

## 示例对话

用户: "我快到家了，今晚想做西红柿炒鸡蛋"
Agent: "好的！让我帮你准备。🔍 正在搜索西红柿炒鸡蛋的菜谱..."
Agent: "找到菜谱了！需要：番茄3个、鸡蛋4个、葱1根、盐糖油适量。确认用这个菜谱吗？"
用户: "可以"
Agent: "📷 正在查看冰箱..."
Agent: "冰箱里有：番茄2个、葱。缺少：番茄1个、鸡蛋4个。要帮你下单吗？"
用户: "好的，下单吧"
Agent: "🛒 已生成采购计划：番茄1个+鸡蛋4个，约¥11。确认下单？"
用户: "确认"
Agent: "✅ 已下单，约30分钟送达。📖 正在生成烹饪指南..."
Agent: "烹饪指南已发送到您的钉钉！共8页，包含详细步骤。祝您做菜愉快！🍳"
