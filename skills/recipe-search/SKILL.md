---
name: recipe-search
description: "在小红书上搜索菜谱并生成图文并茂的 HTML 烹饪指南。当用户想做菜、需要菜谱、提到任何菜名时使用。"
---

# 菜谱搜索 + HTML 烹饪指南

搜索小红书菜谱，获取图片，生成带图的 HTML。

**用 browser 工具，不要用 web_search。**

## ⚠️ 浏览器规则

1. **每次 browser 调用都必须带 `profile: "xhs"`**
2. **只用 `open` 打开第一个页面，之后用 `navigate` 复用同一个 tab**
3. **遇到 "tab not found"：先 `browser tabs profile=xhs`**
4. **screenshot 文件在 `~/.openclaw/media/browser/` 下**
5. **限制总 browser 调用不超过 12 次**

## ⚠️ 图片分析规则

**不要用 `image` 工具分析图片（当前模型不支持）。**
**要分析截图内容，用这个脚本调用 Qwen3-VL：**
```bash
python3 ~/.openclaw/workspace/scripts/analyze-image.py \
  --image "{图片路径}" \
  --prompt "请提取这张菜谱截图中的所有内容：食材清单（名称和用量）、制作步骤、注意事项。用JSON格式输出。"
```

## Step 1：搜索

```
browser open profile=xhs url="https://www.xiaohongshu.com/search_result?keyword={菜名}+菜谱+做法&source=web_search_result_notes"
```

等 3 秒，snapshot 看结果，选 1 个高赞帖子。

## Step 2：进入帖子 + 截图

用 navigate 进入帖子，然后：

1. `browser screenshot profile=xhs` 截取页面
2. 复制截图到菜谱文件夹：
```bash
mkdir -p ~/recipes/{菜名}
ls -t ~/.openclaw/media/browser/*.png | head -1 | xargs -I {} cp {} ~/recipes/{菜名}/cover.jpg
```

3. 如果帖子有多张图（轮播），点击下一张再 screenshot：
```bash
ls -t ~/.openclaw/media/browser/*.png | head -1 | xargs -I {} cp {} ~/recipes/{菜名}/step1.jpg
```

4. **用 Qwen3-VL 分析截图提取菜谱内容（不要用 image 工具）：**
```bash
python3 ~/.openclaw/workspace/scripts/analyze-image.py \
  --image ~/recipes/{菜名}/cover.jpg \
  --prompt "请提取这张菜谱截图中的所有内容，包括食材清单和制作步骤。用JSON格式输出：{\"ingredients\":[{\"name\":\"食材\",\"quantity\":\"用量\"}],\"steps\":[{\"step\":1,\"description\":\"步骤\"}],\"tips\":[\"技巧\"]}"
```

5. 用 evaluate 也提取一下 HTML 中的文字（作为补充）：
```
browser evaluate profile=xhs --fn "document.querySelector('#detail-desc, .note-text, .content')?.innerText"
```

## Step 3：写 recipe.json + 生成 HTML

综合 Qwen3-VL 分析结果和 evaluate 提取的文字，写 `~/recipes/{菜名}/recipe.json`。

然后生成 HTML：
```bash
python3 ~/.openclaw/workspace/skills/cooking-guide/scripts/generate_guide.py --recipe ~/recipes/{菜名}/recipe.json
```

## Step 4：发送

```
/home/robin/recipes/{菜名}/{菜名}.html
```
