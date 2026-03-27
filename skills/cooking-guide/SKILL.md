---
name: cooking-guide
description: "根据菜谱生成 PPT 风格的烹饪指南，包含步骤图解和烹饪技巧。当菜谱确定、食材准备就绪后使用。"
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["DASHSCOPE_API_KEY"]
    primaryEnv: "DASHSCOPE_API_KEY"
---

# 烹饪指南生成 (Cooking Guide Generator)

根据菜谱生成精美的 PPT 风格烹饪指南，包含封面、食材总览、分步骤指导和烹饪技巧。

## 触发条件

- 食材采购完成或确认食材齐全后
- 用户说"生成烹饪指南"或"帮我做个做菜教程"
- 烹饪工作流的最后一步

## 前置依赖

- 需要 `recipe-search` 技能生成的菜谱 JSON

## 指令

运行 `python3 scripts/generate_guide.py --recipe "/tmp/openclaw_recipe_{dish}.json"`

脚本会：
1. 读取菜谱 JSON
2. 使用 Qwen 为每个步骤生成详细的烹饪指导文案
3. 使用 python-pptx 生成 PPT 文件
4. PPT 包含：封面页、食材清单页、每步骤一页、技巧总结页

生成完成后：
1. 告知用户 PPT 文件路径
2. 通过 DingTalk 发送文件给用户
3. 如果用户在家，可以在中控屏上展示

## PPT 结构

```
Slide 1: 封面
  - 菜名（大字）
  - 难度 | 时间 | 份量
  - 日期

Slide 2: 食材清单
  - 分类展示（主料 / 辅料 / 调味料）
  - 每种食材的用量

Slide 3~N: 烹饪步骤
  - 步骤编号和标题
  - 详细操作说明
  - 关键提示（火候、时间等）
  - 预留图片区域

Slide N+1: 烹饪技巧
  - 注意事项
  - 常见问题
  - 摆盘建议
```

## 输出

- PPT 文件: `/tmp/openclaw_guide_{dish}.pptx`
- 同时输出 JSON 摘要供其他技能使用

## 示例用法

Agent: [运行 generate_guide.py]
Agent: "烹饪指南已生成！📖
文件: /tmp/openclaw_guide_西红柿炒鸡蛋.pptx
共 8 页，包含详细的分步骤指导。
已发送到您的钉钉，也可以在中控屏上查看。祝您做菜愉快！🍳"
