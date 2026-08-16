# lumi-style

[![checks](https://github.com/lumitive/lumi-style/actions/workflows/ci.yml/badge.svg)](https://github.com/lumitive/lumi-style/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**LUMI's design language and writing style, packaged as a continuously-iterating,
cross-platform skill.** Built on the [Agent Skills](https://agentskills.io)
standard, so it loads on any agent that implements it.

Every rule traces to a real delivery iteration or a reader review — nothing here
was written from thin air.

> **Repository language: English only (red line).** LUMI serves a global
> audience. Chinese strings appear in rule files only as *rule data* for
> Chinese-language output (banned phrases, punctuation examples), never as
> document prose.

## Install & use

Clone once, then symlink into whichever agents you use. **Symlink rather than
copy**: an installed copy silently stranded at 0.1.334 while the repo reached
0.1.337, and a deck was built against three versions of superseded rules.

```bash
git clone https://github.com/lumitive/lumi-style ~/src/lumi-style
ln -s ~/src/lumi-style ~/.agents/skills/lumi-style
```

**That one path covers five agents.** `~/.agents/skills/` is the convergent
cross-agent location — Gemini CLI, GitHub Copilot, OpenCode, OpenClaw and Pi all
read it, and Gemini CLI gives it precedence over its own directory.

| Platform | Install path | Notes |
|---|---|---|
| **Claude Code** | `~/.claude/skills/lumi-style` | [`adapters/claude-code.md`](adapters/claude-code.md) |
| **Gemini CLI** | `~/.agents/skills/` or `~/.gemini/skills/` | [`adapters/gemini-cli.md`](adapters/gemini-cli.md) |
| **OpenAI Codex** | `~/.codex/skills/lumi-style` | also reads `AGENTS.md` — [`adapters/codex.md`](adapters/codex.md) |
| **Cursor** | `~/.cursor/skills/lumi-style` | [`adapters/cursor.md`](adapters/cursor.md) |
| **Google Antigravity** | `~/.gemini/antigravity/skills/` | workspace path is `.agent/skills/`, singular — [`adapters/antigravity.md`](adapters/antigravity.md) |
| **GitHub Copilot** | `~/.agents/skills/` or `.github/skills/` | separate mechanism from `copilot-instructions.md` — [`adapters/github-copilot.md`](adapters/github-copilot.md) |
| **OpenCode** | `~/.config/opencode/skills/` | [`adapters/opencode.md`](adapters/opencode.md) |
| **Pi** | `~/.agents/skills/` or `~/.pi/agent/skills/` | [`adapters/pi.md`](adapters/pi.md) |
| **OpenClaw** | `~/.agents/skills/lumi-style` | [`adapters/openclaw.md`](adapters/openclaw.md) |
| **Hermes** | `~/.agents/skills/` — **unconfirmed** | [`adapters/hermes.md`](adapters/hermes.md) |
| **Kimi / DeepSeek** | paste `prompts/lumi-style-core.md` | no skill mechanism — [`adapters/kimi.md`](adapters/kimi.md) |

Any other agent implementing the standard — Kiro, Trae, Roo Code, Goose, Amp,
Factory, Mistral Vibe, VS Code — loads it from `~/.agents/skills/` with no work
here. They are not listed because
[`adapters/platforms.json`](adapters/platforms.json) records only what has been
checked, and an unlisted platform is not one this repository claims.

**What is and is not verified.** Every push verifies, offline and mechanically,
that the package is well-formed: the install paths above come from each vendor's
documentation and are checked for internal consistency, every per-platform
artifact is generated from one registry and cannot silently drift, and the check
scripts still produce the expected verdicts on a tracked passing fixture and a
deliberately broken one. Hermes carries a written waiver naming exactly what is
unconfirmed.

**What that is not.** It is not a claim that any model produces good output. The
checks measure mechanical conformance; a page is done when a human reads it as
intentional. `python3 scripts/ops/run_conformance.py` runs a fixed task suite through
whichever agent CLIs are installed and records the result in
[`conformance/CONFORMANCE.md`](conformance/CONFORMANCE.md) — including the agents
it could not run, which are listed rather than omitted. Each row there is one run
of one CLI version on one machine on one date, not a property of the agent.

## What's inside

```
SKILL.md / AGENTS.md / prompts/   the three hand-written entry points — one rule set
                                  (single source: references/); GEMINI.md, the Copilot
                                  and Cursor rule files are GENERATED from the registry
references/writing-rules.md       writing style: terminology red lines · banned phrases ·
                                  punctuation · number discipline · the LUMI voice
references/storyline-templates.md narrative skeletons: sales (value & future) · consulting ·
                                  internal analysis · training + shared discipline
references/design-rules.md        design language: color semantics · dual-voice typography ·
                                  five chart iron rules · semantic icons · layout
references/eval-rubric.md         the M / D / H eval rubric + the review protocol
references/eval-inventory.md      GENERATED: every quantitative constraint, extracted from the checkers
tokens/                           design tokens (CSS + JSON): two ladders · palette · type · scale
assets/brand                      LUMIVATE's locked marks — the field globe is the
                                  default cover/closing mark, embedded live
assets/fonts                      D-DIN, vendored (SIL OFL) — embed, never link
assets/icons                      vendored Lucide library (ISC) + the reserved bindings, currentColor
assets/vectors                    orthographic globe · flat trade map, generated from lat/lon
assets/vectors/world-110m.json    Natural Earth 110m as a shared-arc topology (public domain)
assets/vectors/regions.json       trade-region registry, node point layer, bilingual names
assets/geo                        the shared geometry core: projection, topology decode, hit test
assets/globe                      the globe component: SVG and canvas back ends over the core
fixtures/                         synthetic deliverables the checkers are tested on — a
                                  well-formed one, one with a named defect per page, one
                                  that exists only to fail, and a Chinese prose pair
conformance/                      fixed task suite · the tracked cross-agent scoreboard ·
                                  history.json, the dated memory the freshness gate reads
scripts/                          five drawers + preflight at the top (see scripts/README.md):
                                  check/ (the gates) · build/ (generators + embedders) ·
                                  lib/ (shared implementations) · render/ (geometry→SVG) ·
                                  ops/ (operator tools) — among them check_prose (M) · check_design (D) ·
                                  inspect_layout (renders and looks) · export_pdf (PDF/4K) ·
                                  output_dir (where a deliverable belongs) ·
                                  check_fixtures · check_js · check_evidence (the evidence
                                  gate) · color_math + css_tokens (the shared
                                  implementations) · build_entrypoints · build_fixtures ·
                                  run_conformance · embed_font · embed_icons · build_geography
tests/                            pytest suite: shared-module characterization, guards
                                  proven able to fail, a --help floor on every argparse CLI
releases/evidence/                one JSON per release since 0.1.424: the operator checks
                                  the diff obliged, each an EXECUTED command with its digest
KNOWN_GAPS.md · FAILURE_MODES.md  the defect ledger and the escape-class registry
adapters/platforms.json           the platform registry: install paths · capability
                                  tiers · entry files, guarded by check_repo
adapters/*.md                     per-platform loading notes
backlog/                          the ideas backlog: problems with their evidence,
                                  ranked, with stable IDEA-ids — proposals, never rules
```

Rules and assets ship together on purpose. Four times now a rule has required
something the package did not contain — an embedded display face, a semantic icon
set, the reserve that holds the content datum, and the class names its own
consistency probe checks for — and every time deliverables simply went without.
`CLAUDE.md` §5 states the resulting maintenance rule.

## The brand in one line

**`上善若水，水利万物而不争`** — the supreme good is like water, nourishing all
things without contending. One apparatus for every industry; a company that
declines where others claim, and can show you the code where it declines. LUMI is
light: you cannot see a current, you can see light on it. The visual key is
`波光鳞鳞`, shimmer on water — **many small marks at varying intensity, arranged by
a flow you cannot otherwise see** — which is why the signature device is a field
of one mark per datum, why a field with nothing behind it is forbidden, and why
the water behind every page may be decorative only because it cannot be counted.
See [`references/brand.md`](references/brand.md), which loads before everything
else.

## The design language in one line

**Pure-white canvas (Apple space grey on request) · one green meaning in two
measured inks (forest as text, live green in figures) plus the lime as the
event surface · China red for warnings only, amber for partial, brass for reference;
a fixed 16:9 page and a fixed A4 sheet (the genre picks which leads — training
leads with A4), handling terms behind a seal shield on every page, a cover and
closing sharing the rotating LUMIVATE field globe, a lime opener at every part boundary, one claim
per screen and one focal element on it, visual blocks carrying about half of
every content page, numbers are the copy, titles are conclusions, and a table is
for values.**
The layout skeleton was researched from the public web design of SpaceX and Tesla
(whitespace, spec-first copy, monochrome discipline); the palette and its
semantics are LUMI's own — one color, one meaning, enforced more strictly than
either reference.

## Continuous-iteration protocol

1. Every output ships with a C1–C8 self-score (**never a 5 before a reader has
   scored it**);
2. Readers score; any dimension diverging ≥2 points **forces a retrospective**;
3. Retrospectives produce rule revisions → `CHANGELOG.md` + version bump;
4. The same lesson across two documents → promoted to a formal rule.

No rule is added or removed without a documented case behind it.

## License

MIT for everything this repository authors. The package **redistributes
third-party assets under their own licenses** — D-DIN (SIL OFL 1.1), the
Lucide icon set (ISC), Natural Earth geometry (public domain) — inventoried
in [`NOTICE`](NOTICE), with full license texts beside the vendored files.
