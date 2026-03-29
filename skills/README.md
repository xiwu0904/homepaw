# 🍳 HomePaw 智能烹饪工作流

基于 OpenClaw 的全自动烹饪助手技能包。用户只需说一句"今晚想做红烧肉"，系统自动完成：搜索菜谱 → 生成图文指南 → 拍冰箱识别食材 → 天猫超市加购缺少食材 → 发送菜谱给用户。

## 演示流程

```
用户: "今晚想做红烧排骨，帮我准备"
  │
  ├─ 1. 搜索小红书菜谱（浏览器自动操作）
  ├─ 2. 截图 + AI 提取食材和步骤
  ├─ 3. 生成图文并茂的 HTML 烹饪指南
  ├─ 4. 摄像头拍冰箱 → Qwen3-VL 识别食材 → 对比菜谱
  ├─ 5. 缺少的主要食材自动在天猫超市加入购物车
  └─ 6. 发送 HTML 菜谱 + 通知用户自行结算
```

## 技能列表

| 技能 | 说明 |
|------|------|
| `cook-workflow` | 编排技能，串联全流程 |
| `recipe-search` | 小红书搜索菜谱 + 生成 HTML |
| `cooking-guide` | HTML 烹饪指南生成器（纯 Python，零依赖） |
| `fridge-check` | 摄像头拍冰箱 + Qwen3-VL 食材识别 + 菜谱对比 |
| `purchase-planner` | 天猫超市自动搜索食材并加入购物车 |

## 辅助脚本

| 脚本 | 说明 |
|------|------|
| `scripts/analyze-image.py` | 通用图片分析（调用 Qwen3-VL-Plus API） |
| `scripts/snap-fridge.sh` | 摄像头拍照（处理设备锁定、自动曝光） |
| `scripts/start-xhs-browser.sh` | 启动已登录的 Chrome 浏览器（CDP 模式） |

## ⚠️ 关键前置条件

### 1. 浏览器 Profile（最重要）

本项目使用 OpenClaw 的 browser 工具控制 Chrome 浏览器。**必须使用已登录小红书和天猫/淘宝的 Chrome Profile**，否则无法搜索菜谱和加购物车。

配置方法：

1. 用 Chrome 浏览器手动登录小红书（xiaohongshu.com）和淘宝/天猫（taobao.com / tmall.com）
2. 复制 Chrome 用户数据到 OpenClaw 浏览器目录：
   ```bash
   mkdir -p ~/.openclaw/browser/xhs/user-data
   cp -r ~/.config/google-chrome/Default ~/.openclaw/browser/xhs/user-data/Default
   cp ~/.config/google-chrome/"Local State" ~/.openclaw/browser/xhs/user-data/
   ```
3. 启动带远程调试的 Chrome：
   ```bash
   /opt/google/chrome/chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=$HOME/.openclaw/browser/xhs/user-data \
     --no-sandbox --no-first-run --disable-gpu &
   ```
   或使用脚本：`bash ~/.openclaw/workspace/scripts/start-xhs-browser.sh`

4. 在 `~/.openclaw/openclaw.json` 中配置 browser：
   ```json
   {
     "browser": {
       "enabled": true,
       "executablePath": "/opt/google/chrome/chrome",
       "noSandbox": true,
       "defaultProfile": "openclaw",
       "profiles": {
         "openclaw": { "cdpPort": 18800 },
         "xhs": { "cdpUrl": "http://127.0.0.1:9222" }
       }
     }
   }
   ```

5. 确认 `tools.profile` 设为 `"full"`（包含 browser 工具）：
   ```json
   { "tools": { "profile": "full" } }
   ```

### 2. DashScope API Key

用于 Qwen3-VL 图片识别和菜谱内容分析。在 `.env` 文件中设置：
```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 摄像头

冰箱食材识别需要摄像头（`/dev/video0`）。需要安装 `fswebcam`：
```bash
sudo apt install fswebcam
```

### 4. OpenClaw 配置

- 模型：glm-5 或其他支持的模型
- 工具权限：`tools.profile: "full"`（必须包含 browser）
- DingTalk 插件（可选）：用于通过钉钉接收消息和菜谱文件

## 安装步骤

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 复制技能到 OpenClaw workspace
cp -r skills/* ~/.openclaw/workspace/skills/
cp scripts/* ~/.openclaw/workspace/scripts/
chmod +x ~/.openclaw/workspace/scripts/*.sh

# 3. 创建菜谱存储目录
mkdir -p ~/recipes

# 4. 配置浏览器 Profile（见上方说明）

# 5. 重启 OpenClaw Gateway
openclaw gateway restart
```

## 文件结构

```
skills/
├── cook-workflow/SKILL.md        # 全流程编排
├── recipe-search/SKILL.md        # 小红书菜谱搜索
├── cooking-guide/
│   ├── SKILL.md
│   └── scripts/generate_guide.py # HTML 生成器
├── fridge-check/
│   ├── SKILL.md
│   └── scripts/check_fridge.py   # 冰箱食材识别
└── purchase-planner/SKILL.md     # 天猫超市采购

scripts/
├── analyze-image.py              # Qwen3-VL 图片分析
├── snap-fridge.sh                # 摄像头拍照
└── start-xhs-browser.sh          # 启动 Chrome CDP

~/recipes/{菜名}/                  # 生成的菜谱
├── recipe.json                   # 菜谱数据
├── {菜名}.html                   # 图文 HTML 指南
├── cover.jpg                     # 封面图
└── step1.jpg, step2.jpg ...      # 步骤图
```

## 已知限制

- glm-5 模型无法直接分析图片，图片分析通过 `analyze-image.py` 脚本调用 Qwen3-VL-Plus 实现
- 天猫超市有反爬机制，搜索可能触发验证码，需要用户手动通过
- 天猫超市"加入购物车"是图标按钮（非文字），agent 通过 CSS selector 或 AI 截图分析定位
- 小红书登录状态可能过期，需要定期在 Chrome 中重新登录
- 采购只加购物车，不会自动结算付款（安全考虑）
