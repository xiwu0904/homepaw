---
name: recipe-search
description: "在小红书上搜索菜谱并生成图文并茂的 HTML 烹饪指南。当用户想做菜、需要菜谱、提到任何菜名时使用。"
---

# 菜谱搜索 + HTML 烹饪指南

搜索小红书菜谱，下载图片，生成 HTML 烹饪指南。

**必须用 browser 工具（profile: xhs），不要用 web_search。**
**必须完成全部 5 步。最终产物是 HTML 文件，不是纯文字。**

## 文件结构

每道菜一个子文件夹，所有文件放在一起：
```
~/recipes/{菜名}/
  ├── recipe.json      # 菜谱数据
  ├── {菜名}.html      # 最终 HTML 指南
  ├── cover.jpg        # 封面图
  ├── step1.jpg        # 步骤图
  ├── step2.jpg
  └── ...
```

## 前置检查

browser 连接失败时先运行：`bash ~/.openclaw/workspace/scripts/start-xhs-browser.sh`

## Step 1：搜索小红书

browser（profile: xhs）打开：
`https://www.xiaohongshu.com/search_result?keyword={菜名}+菜谱+做法&source=web_search_result_notes`

snapshot → 点击 2-3 个高赞帖子。

## Step 2：提取文字 + 下载图片

先创建文件夹：
```bash
mkdir -p ~/recipes/{菜名}
```

每个帖子里：
1. snapshot 提取正文
2. 用 browser screenshot 截取帖子页面保存为图片：
   ```bash
   # screenshot 会返回图片路径，用 exec 复制到菜谱文件夹
   cp /path/to/screenshot.png ~/recipes/{菜名}/step1.jpg
   ```
3. 或者用 browser evaluate 提取图片 URL 后用 curl 下载：
   ```bash
   curl -sL -o ~/recipes/{菜名}/step1.jpg "{图片URL}"
   ```

**至少保存 1 张封面图 + 每个步骤 1 张图。如果 URL 提取失败，用 screenshot 截图替代。**

## Step 3：写菜谱 JSON

用 write 写入 `~/recipes/{菜名}/recipe.json`。

**image 字段必须指向实际存在的本地文件路径（绝对路径）：**

```json
{
  "dish": "菜名",
  "summary": "简介",
  "ingredients": [{"name": "食材", "quantity": "用量", "category": "分类", "essential": true}],
  "steps": [{"step": 1, "description": "步骤", "tips": "技巧", "image": "/home/robin/recipes/{菜名}/step1.jpg"}],
  "tips": ["技巧"],
  "images": ["/home/robin/recipes/{菜名}/cover.jpg"],
  "source": "小红书"
}
```

## Step 4：生成 HTML（必须执行）

```bash
python3 ~/.openclaw/workspace/skills/cooking-guide/scripts/generate_guide.py --recipe ~/recipes/{菜名}/recipe.json
```

输出: `~/recipes/{菜名}/{菜名}.html`

## Step 5：发送 HTML 给用户

输出文件路径：
```
/home/robin/recipes/{菜名}/{菜名}.html
```

**完成标志：用户收到 HTML 文件。**
