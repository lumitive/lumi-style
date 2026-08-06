# lumi-style

**LUMI's design language and writing style, packaged as a continuously-iterating,
cross-platform skill.** Works with Claude Code, Codex, Kimi, and DeepSeek.

Every rule traces to a real delivery iteration or a reader review — nothing here
was written from thin air.

> **Repository language: English only (red line).** LUMI serves a global
> audience. Chinese strings appear in rule files only as *rule data* for
> Chinese-language output (banned phrases, punctuation examples), never as
> document prose.

## Install & use

| Platform | How |
|---|---|
| **Claude Code** | `git clone https://github.com/lumitive/lumi-style ~/.claude/skills/lumi-style`, then `/lumi-style <task>` |
| **Codex** | reads `AGENTS.md` (see `adapters/codex.md`) |
| **Kimi** | paste `prompts/lumi-style-core.md` as the system prompt (see `adapters/kimi.md`) |
| **DeepSeek** | same as Kimi (see `adapters/deepseek.md`) |

## What's inside

```
SKILL.md / AGENTS.md / prompts/   three entry points, one rule set (single source: references/)
references/writing-rules.md       writing style: terminology red lines · banned phrases ·
                                  punctuation · number discipline · the LUMI voice
references/storyline-templates.md narrative skeletons: sales (value & future) · consulting ·
                                  internal analysis + shared discipline
references/design-rules.md        design language: color semantics · dual-voice typography ·
                                  five chart iron rules · semantic icons · layout
references/eval-rubric.md         eval rubric M1–M8 / H1–H6 + the review protocol (iteration engine)
tokens/                           design tokens (CSS + JSON): palette · type · scale
adapters/                         per-platform loading notes
```

## The design language in one line

**Space-gray canvas · natural green as the single accent · China red for warnings
only; one claim per screen, numbers are the copy, titles are conclusions.**
The layout skeleton was researched from the public web design of SpaceX and Tesla
(whitespace, spec-first copy, monochrome discipline); the palette and its
semantics are LUMI's own — one color, one meaning, enforced more strictly than
either reference.

## Continuous-iteration protocol

1. Every output ships with an H1–H6 self-score (**never a 5 before a reader has
   scored it**);
2. Readers score; any dimension diverging ≥2 points **forces a retrospective**;
3. Retrospectives produce rule revisions → `CHANGELOG.md` + version bump;
4. The same lesson across two documents → promoted to a formal rule.

No rule is added or removed without a documented case behind it.

## License

MIT

[broken](references/does-not-exist.md)
