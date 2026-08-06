---
name: lumi-style
description: |
  LUMI's design language and output writing style. Use when producing business documents, slides, client materials, marketing copy, HTML reports, or charts for LUMI — in any language — or when reviewing existing drafts against LUMI standards. Triggers: "LUMI style", "lumi-style", "按 LUMI 风格". Not for: pure coding tasks or content unrelated to LUMI deliverables.
license: MIT
metadata:
  version: "1.1.0"
---

# LUMI Style · Design Language & Writing Style

LUMI is an AI-native consulting firm serving a global audience. This skill gives
every output the same voice and the same visual discipline, and iterates through
a score-and-review loop (rule revisions go through CHANGELOG).

**Repository language: English only (red line).** Chinese strings appear in the
rules only as rule data for Chinese-language output.

## Workflow

1. **Pick the scenario**: sales/marketing · consulting/client document · internal
   analysis — three different narrative skeletons. Read
   [`references/storyline-templates.md`](references/storyline-templates.md) and
   choose before writing.
2. **Write and review** under
   [`references/writing-rules.md`](references/writing-rules.md) (terminology red
   lines / banned phrases / punctuation / number discipline / the LUMI voice /
   de-AI-flavor pass). **Run the punctuation pass after drafting.**
3. **Visuals and charts**: for HTML/slides/chart output follow
   [`references/design-rules.md`](references/design-rules.md); tokens come from
   [`tokens/lumi-theme.css`](tokens/lumi-theme.css) and
   [`tokens/design-tokens.json`](tokens/design-tokens.json).
4. **Before delivery**: run the critic gate (structure before polish) and the
   H1–H6 self-score per
   [`references/eval-rubric.md`](references/eval-rubric.md);
   **never self-score 5 before a reader has scored it**.
5. **Review loop**: decks embed the scoring table as the final page; on receiving
   reviews, any dimension diverging ≥2 forces a retrospective that produces a rule
   revision (CHANGELOG + version bump) — this is the skill's iteration engine.

## Six non-negotiable red lines (every scenario)

1. No invented facts; every number carries its source; illustrative values are
   labeled;
2. No coined Chinese: new concepts with no established Chinese term take the
   English term directly;
3. The sales storyline is **value and future**; honesty boundaries converge to a
   single trust page;
4. Titles are conclusions; all titles concatenated must read as a complete
   argument;
5. Charts: one accent color, conclusion-style titles, a source line on every
   figure;
6. AI never signs; money/safety conclusions never come from a language model.

## Cross-platform

Four entry points load one rule set (single source in `references/`):
Claude Code uses this file; Codex reads `AGENTS.md`; Kimi / DeepSeek use
`prompts/lumi-style-core.md` (self-contained single file). Per-platform loading
notes live in `adapters/`.

## Boundaries

- This skill contains style rules and templates only — no client names, project
  figures, or engagement facts;
- Style rewrites must not change facts or framing;
- Rule revisions come only from review retrospectives — no additions or deletions
  without a documented case.
