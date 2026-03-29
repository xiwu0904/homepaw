---
name: purchase-planner
description: "根据缺少的食材清单，在天猫超市自动搜索、选购、加入购物车。当用户需要采购食材、买菜时使用。"
---

# 食材采购 (Purchase Planner)

在天猫超市搜索缺少的**主要食材**，加入购物车。

## ⛔ 硬性规则

1. **只加购物车。绝对不点"结算"、"下单"、"购买"、"付款"。**
2. **只在天猫超市采购。不要建议去菜市场、线下超市、其他平台。这是 demo，只用天猫超市。**
3. **不要自动放弃采购。不管遇到什么困难（页面慢、ref 刷新、搜索结果看不到），都要坚持尝试。**
4. **只采购主要食材（肉、菜、蛋等），调味料/配料（盐、糖、酱油、葱姜蒜、香料等）假设家里都有，不需要买。**

## ⚠️ 浏览器规则

- **每次 browser 调用都必须带 `profile: "xhs"`**
- **天猫搜索会打开新 tab！搜索后必须 `browser tabs` → `browser focus` 切到新 tab**
- **搜索结果在 snapshot 中可能看不到（JS渲染）。用 screenshot + analyze-image.py 看页面**

## 流程

### 1. 打开天猫超市

```
browser navigate profile=xhs url="https://chaoshi.tmall.com"
```

等 3 秒，snapshot，关闭弹窗。

### 2. 对每个主要食材执行搜索+加购

#### 2a. 搜索

1. snapshot 找 searchbox ref
2. click searchbox
3. type ref "{食材名}" --submit
4. 等 3 秒
5. **`browser tabs profile=xhs`** — 找到新打开的搜索结果 tab
6. **`browser focus profile=xhs {新tabId}`** — 切过去

#### 2b. 看搜索结果

snapshot 可能看不到商品。两个方法：

方法 A（优先）：用 evaluate 提取
```
browser evaluate profile=xhs --fn "JSON.stringify([...document.querySelectorAll('a[href*=\"detail.tmall\"], a[href*=\"item.taobao\"]')].slice(0,3).map(a=>({text:a.innerText?.slice(0,50),href:a.href})))"
```

方法 B：screenshot + AI 分析
```
browser screenshot profile=xhs
```
然后：
```bash
python3 ~/.openclaw/workspace/scripts/analyze-image.py \
  --image "$(ls -t ~/.openclaw/media/browser/*.jpg 2>/dev/null | head -1)" \
  --prompt "这是天猫超市搜索结果页面。请列出前3个商品的名称和价格。"
```

#### 2c. 进入商品页

用 evaluate 拿到的商品链接 navigate 进入：
```
browser navigate profile=xhs url="{商品链接}"
```

或者如果 snapshot 能看到商品 ref，直接 click。

#### 2d. 加入购物车

**天猫超市的"加入购物车"不是文字按钮，是"立即购买"旁边的一个购物车图标（🛒）。**

1. snapshot 查看商品页
2. **不要点"立即购买"！** 找"立即购买"按钮旁边的购物车图标按钮
3. 如果 snapshot 中看不到购物车图标，用 evaluate 找到它：
```
browser evaluate profile=xhs --fn "const btn = document.querySelector('[class*=\"cart\"], [class*=\"Cart\"], [data-spm*=\"cart\"], .tm-btn-cart, button[aria-label*=\"购物车\"], a[href*=\"cart\"]'); if(btn) { btn.click(); 'clicked cart button' } else { JSON.stringify([...document.querySelectorAll('button, [role=button]')].map(b=>({text:b.innerText?.slice(0,20), class:b.className?.slice(0,30)})).filter(b=>b.text||b.class)) }"
```
4. 如果 evaluate 也找不到，用 screenshot 截图，然后用 analyze-image.py 分析：
```bash
python3 ~/.openclaw/workspace/scripts/analyze-image.py \
  --image "$(ls -t ~/.openclaw/media/browser/*.jpg 2>/dev/null | head -1)" \
  --prompt "这是天猫超市商品页面。请找到'加入购物车'按钮的位置。它通常是'立即购买'按钮旁边的一个购物车图标。描述它的位置。"
```
5. screenshot 确认加购成功

#### 2e. 回天猫继续下一个

```
browser navigate profile=xhs url="https://chaoshi.tmall.com"
```

### 3. 截图购物车

```
browser navigate profile=xhs url="https://cart.taobao.com/cart.htm"
browser screenshot profile=xhs
```

### 4. 通知用户

列出已加购的食材，提醒用户自行结算。
