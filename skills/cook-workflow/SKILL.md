---
name: cook-workflow
description: "完整的智能烹饪工作流。当用户说想做某道菜、下班做饭、今晚吃什么时，自动串联菜谱搜索→HTML生成→冰箱检查→采购→发送菜谱的全流程。"
---

# 智能烹饪工作流

用户说想做菜 → 自动完成全流程。**全程自动，不要每步问用户。**

## ⚠️ 全局浏览器规则

**所有 browser 调用必须带 `profile: "xhs"`。这个 profile 已登录小红书和天猫。**
**只用 `open` 打开第一个页面，之后全部用 `navigate` 复用同一个 tab。**
**不要因为"操作慢"、"ref 刷新"就放弃。必须完成每个步骤。**

## Step 1：检查已有菜谱

```bash
ls ~/recipes/{菜名}/recipe.json 2>/dev/null && echo "EXISTS" || echo "NOT_FOUND"
```
存在 → 跳到 Step 3。

## Step 2：搜索菜谱 + 生成 HTML

按 `recipe-search` 技能。控制在 5 分钟内，1 个帖子够了。
完成标志：`~/recipes/{菜名}/{菜名}.html` 存在。

## Step 3：拍冰箱 + 对比食材

```bash
bash ~/.openclaw/workspace/scripts/snap-fridge.sh
```

拍照失败则用最近的旧照片：`ls -t ~/cam-snapshots/fridge-*.jpg | head -1`

对比：
```bash
python3 ~/.openclaw/workspace/skills/fridge-check/scripts/check_fridge.py \
  --image "{照片路径}" --recipe ~/recipes/{菜名}/recipe.json
```

全部齐全 → 跳到 Step 5。

## Step 4：天猫超市加购

按 `purchase-planner` 技能。**用 navigate 跳转到天猫（不要 open 新 tab），复用已有的浏览器 tab。**

**⛔ 只加购物车，不结算。**
**必须尝试每个缺少的食材，不要中途放弃。**

## Step 5：发送菜谱

```
/home/robin/recipes/{菜名}/{菜名}.html
```
