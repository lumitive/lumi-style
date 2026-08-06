# lumi-style

**LUMI's design language and writing style, packaged as a continuously-iterating,
cross-platform skill.** Works with Claude Code, Codex, Kimi, and DeepSeek.

LUMI 的设计语言与输出文字风格,打包为可持续迭代的跨平台 skill。
规则不是凭空写的——每一条都来自真实交付物的多轮打磨与读者回评复盘。

## 安装与使用

| 平台 | 方式 |
|---|---|
| **Claude Code** | `git clone https://github.com/lumitive/lumi-style ~/.claude/skills/lumi-style`,然后 `/lumi-style <任务>` |
| **Codex** | 读 `AGENTS.md`(见 `adapters/codex.md`) |
| **Kimi** | 把 `prompts/lumi-style-core.md` 作系统提示(见 `adapters/kimi.md`) |
| **DeepSeek** | 同 Kimi(见 `adapters/deepseek.md`) |

## 里面有什么

```
SKILL.md / AGENTS.md / prompts/   三个装载入口,同一套规则(单源在 references/)
references/writing-rules.md       文字风格:不编中文红线 · 禁词 · 标点 · 数字纪律 · LUMI 声口
references/storyline-templates.md 叙事模板:销售(价值与未来)· 咨询 · 内部分析 + 共同纪律
references/design-rules.md        设计语言:版式纪律 · 图表五铁律 · 图标语义化 · 色彩用法
references/eval-rubric.md         评分卡 M1–M8 / H1–H6 + 回评协议(迭代引擎)
tokens/                           设计 token(CSS + JSON):色板 · 字体 · 字号阶梯
adapters/                         四平台装载说明
```

## 设计语言一句话

**太空灰基底 · 自然绿唯一强调 · 中国红只给警示;一屏一事、数字即文案、标题即结论。**
排版骨架研究并借鉴了 SpaceX 与 Tesla 的公开网页设计(大留白、参数直述、单色纪律),
色板与语义是 LUMI 自己的——一色一义,比它们更严格。

## 持续迭代协议

1. 每份输出交付时附 H1–H6 自评(**未经读者检验不给 5 分**);
2. 读者回评;分歧 ≥2 分的维度**强制复盘**;
3. 复盘产出规则修订 → `CHANGELOG.md` + 版本号;
4. 同一教训跨两份文档出现 → 升为正式规则。

规则不接受无案例的凭空增删——每条修订都必须能指回一次真实回评。

## License

MIT
