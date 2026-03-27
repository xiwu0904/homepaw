---
name: fridge-check
description: "拍摄冰箱照片，用 AI 识别食材，与菜谱对比找出缺少的食材。当用户说检查冰箱、看看冰箱有什么、缺什么食材时使用。"
---

# 冰箱食材检查

拍摄冰箱照片 → Qwen VL 识别食材 → 与菜谱对比 → 列出缺少的食材。

## Step 1：拍摄冰箱照片

用摄像头拍照（复用 snap 技能的方法）：

```bash
pkill -f "ffmpeg.*video0" 2>/dev/null; sleep 2
SNAP=~/cam-snapshots/fridge-$(date +%Y%m%d-%H%M%S).jpg
fswebcam -r 1280x720 --no-banner -S 20 "$SNAP" 2>/dev/null
python3 ~/.openclaw/workspace/skills/camera/cam_stream.py > /tmp/cam_stream.log 2>&1 &
echo "$SNAP"
```

拍完后先把照片路径发给用户看（DingTalk 会显示图片）。

## Step 2：AI 识别 + 对比菜谱

运行识别脚本：

```bash
python3 ~/.openclaw/workspace/skills/fridge-check/scripts/check_fridge.py \
  --image "$SNAP" \
  --recipe ~/recipes/{菜名}/recipe.json
```

如果没有指定菜谱，只做识别不做对比：
```bash
python3 ~/.openclaw/workspace/skills/fridge-check/scripts/check_fridge.py --image "$SNAP"
```

## Step 3：展示结果

脚本输出 JSON，向用户展示：
- ✅ 已有的食材
- ❌ 缺少的食材（含需要的数量）
- 询问是否需要采购

## 环境变量

脚本需要 `DASHSCOPE_API_KEY`，从 `.env` 或环境变量读取。
