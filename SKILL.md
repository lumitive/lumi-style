---
name: lumi-style
description: |
  LUMI 的设计语言与输出文字风格。产出中文商业文档、slides、客户材料、市场文案、HTML 报告或图表时使用;也用于按 LUMI 标准审校既有文稿。触发词:「按 LUMI 风格」「lumi-style」「LUMI 文档」。不用于:纯代码任务、英文长文写作、与 LUMI 输出物无关的内容。
license: MIT
metadata:
  version: "1.0.0"
---

# LUMI Style · 设计语言与文字风格

LUMI 是 AI-Native 咨询公司。本 skill 让任何产出都带着同一副声口与同一套视觉纪律,
并通过评分回评机制持续迭代(规则修订走 CHANGELOG)。

## 使用流程

1. **判断场景**:销售/市场材料 · 咨询/客户文档 · 内部分析——三种场景的叙事骨架不同,
   读 [`references/storyline-templates.md`](references/storyline-templates.md) 选对模板再动笔。
2. **写作与审校**:遵守 [`references/writing-rules.md`](references/writing-rules.md)
   (用词红线/禁词/标点/数字纪律/LUMI 声口/去 AI 味六动作)。**写完先跑标点归一。**
3. **视觉与图表**:产出 HTML/slides/图表时,遵守
   [`references/design-rules.md`](references/design-rules.md),token 取
   [`tokens/lumi-theme.css`](tokens/lumi-theme.css) 与
   [`tokens/design-tokens.json`](tokens/design-tokens.json)。
4. **交付前**:按 [`references/eval-rubric.md`](references/eval-rubric.md) 走 critic 门
   (先修结构再美化)与 H1–H6 自评;**未经读者检验不给 5 分**。
5. **回评闭环**:slides 末页内嵌评分表;收到回评后,分歧 ≥2 的维度强制复盘,
   产出规则修订(CHANGELOG + 版本号)——这是本 skill 的迭代引擎。

## 六条不可谈判红线(任何场景)

1. 不发明事实;每个数字带出处;示意值必标「示意」;
2. 不编中文:新概念无标准中文直接用英文,禁自造比喻词;
3. 销售叙事主线是**价值与未来**,诚实边界收敛为一页信任基础;
4. 标题即结论;全篇标题连读必须构成完整论证;
5. 图表单一强调色、图题写结论、必带 source 行;
6. AI 不签字;涉钱涉安全的结论不由语言模型给出。

## 跨平台

本仓库四个入口装载同一套规则(内容单源在 `references/`):
Claude Code 用本文件;Codex 读 `AGENTS.md`;Kimi / DeepSeek 用
`prompts/lumi-style-core.md`(自含单文件)。各平台装载说明见 `adapters/`。

## 边界

- 本 skill 只含风格规则与模板,不含任何客户名称、项目数字或商业事实;
- 风格改写不得改变事实与口径;
- 规则修订只通过回评复盘产生,不接受无案例的凭空增删。
