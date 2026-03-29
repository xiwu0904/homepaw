---
name: fridge-check
description: "拍摄冰箱照片，用 AI 识别食材，与菜谱对比找出缺少的食材。当用户说检查冰箱、看看冰箱有什么、缺什么食材时使用。"
---

# 冰箱食材检查

拍冰箱 → 运行脚本调用 Qwen3-VL 识别 → 对比菜谱 → 列出缺少食材。

**不要自己分析图片。不要用 image 工具。必须运行 check_fridge.py 脚本，它会调用 Qwen3-VL API 来识别食材。**

## Step 1：拍摄冰箱照片

```bash
bash ~/.openclaw/workspace/scripts/snap-fridge.sh
```

脚本输出照片绝对路径。拍完后把路径发给用户看。

拍照失败则用最近的旧照片：
```bash
ls -t ~/cam-snapshots/fridge-*.jpg | head -1
```

## Step 2：运行识别脚本（不要跳过）

**必须运行这个脚本，它内部调用 Qwen3-VL-Plus 模型来识别食材：**

```bash
python3 ~/.openclaw/workspace/skills/fridge-check/scripts/check_fridge.py \
  --image "{照片路径}" \
  --recipe ~/recipes/{菜名}/recipe.json
```

脚本输出 JSON，包含 fridge_items（识别到的食材）和 missing_items（缺少的食材）。

**如果识别到 0 种食材，可能是照片没拍到冰箱内部。告诉用户重新拍照或手动告知家里有什么食材。**

## Step 3：展示结果

向用户展示：✅ 已有 / ❌ 缺少（含数量）。
