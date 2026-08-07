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
| **Claude Code** | `git clone https://github.com/lumitive/lumi-style` somewhere you keep checkouts, then `ln -s <path> ~/.claude/skills/lumi-style` and `/lumi-style <task>`. **Symlink rather than copy**: an installed copy silently stranded at 1.4.0 while the repo reached 1.7.0, and a deck was built against three versions of superseded rules. |
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
references/eval-rubric.md         eval rubric M1–M11 / D1–D6 / H1–H6 + the review protocol
tokens/                           design tokens (CSS + JSON): two ladders · palette · type · scale
assets/fonts                      D-DIN, vendored (SIL OFL) — embed, never link
assets/icons                      the eight semantic icons, hairline, currentColor
assets/vectors                    orthographic globe · flat trade map, generated from lat/lon
scripts/                          check_repo · check_prose (M) · check_design (D) ·
                                  embed_font · embed_icons · build_geography
adapters/                         per-platform loading notes
```

Rules and assets ship together on purpose. Twice now a rule required something the
package did not contain — an embedded display face, then a semantic icon set — and
both times deliverables simply went without. `CLAUDE.md` §5 states the resulting
maintenance rule.

## The design language in one line

**Pure-white canvas (Apple space grey on request) · natural green as the single
accent · China red for warnings only, amber for partial, brass for reference;
one claim per screen and one focal element on it, numbers are the copy, titles
are conclusions, and a table is for values.**
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
