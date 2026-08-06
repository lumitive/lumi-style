# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

lumi-style packages LUMI's design language and writing style as a cross-platform
LLM skill. It ships Markdown rules and design tokens — there is nothing to build
or install. "Development" here means editing rules, keeping the entry points in
sync, and recording changes in the changelog.

## Checks

```bash
python3 scripts/check_repo.py     # all four guards; exit 1 on any failure
```

Standard library only, no dependencies. `.github/workflows/ci.yml` runs the same
command on every push to `main` and every pull request. The four guards are the
mechanical half of the invariants below: version stamps, the English-only red
line, markdown link targets, and palette parity between the two `tokens/` files.
Everything the checks cannot decide — above all whether a rule change was
re-flowed into the entry points — stays with the reviewer.

## Architecture: one rule set, three entry points

`references/` is the single source of truth for rule prose:

- `references/writing-rules.md` — output-language default, terminology red lines, banned phrases, punctuation, number discipline, the LUMI voice
- `references/storyline-templates.md` — narrative skeletons per scenario (sales / consulting / internal analysis), cover & closing templates, the pre-delivery critic gate
- `references/design-rules.md` — color semantics, typography, chart rules, semantic icons, layout guards, verification matrix
- `references/eval-rubric.md` — M1–M8 / H1–H6 scoring rubric and the review protocol (the iteration engine)

`tokens/lumi-theme.css` and `tokens/design-tokens.json` are the authority for
palette and type values. Their palette values mirror each other exactly and must
be edited together, but the JSON is a superset: `palette_default`, `chart`,
`chart_scale_px`, and `layout` have no CSS counterpart. Where a numeric value in
`design-rules.md` disagrees with the tokens, the tokens win — the prose copies
drift.

Three entry points load these rules, and each restates part of them:

- `SKILL.md` — Claude Code entry; reads `references/` and `tokens/` on demand
- `AGENTS.md` — Codex entry; summarizes the load order and the six red lines inline
- `prompts/lumi-style-core.md` — **self-contained** single file for Kimi/DeepSeek (a strict subset of `references/`), so any substantive rule change must be re-flowed into it by hand

`adapters/` holds per-platform loading notes plus the precedence rule that
`references/` wins on conflict.

**Drift is this repo's main hazard, and the checks catch only its mechanical
half — semantic drift between prose copies is invisible to them.** After changing
`references/`, re-read all three entry points *and* `README.md`, which
independently restates the file map, the design language, and the iteration
protocol. Two known-stale spots to fix when you touch their subject matter:
`prompts/lumi-style-core.md:74-77` still carries pre-1.2.0 canvas hexes and the
retired rounded Latin voice, and `AGENTS.md:4-5` still calls the primary output
Simplified Chinese, which the 1.3.0 American-English default superseded.

## Maintenance conventions

("Red lines" in this repo names the six non-negotiable *content* rules for
deliverables — `SKILL.md:50-62`. These are the separate rules for changing the
repo itself.)

1. **Repository language is English only.** Chinese strings appear in rule files
   only as rule *data* for Chinese-language output (banned phrases, punctuation
   examples) — never as document prose.
2. **Rule changes come only from review retrospectives.** No rule is added or
   removed without a documented case (a reader review with a dimension diverging
   ≥2 points, or a reported defect). Do not invent or "improve" rules
   speculatively. A retrospective may legitimately end in an *anchor* revision or
   a recorded no-change instead of a rule revision — `references/eval-rubric.md`
   is itself editable under the protocol. A lesson is promoted to a formal rule
   once it has appeared across two documents.
3. **A rule revision requires a `CHANGELOG.md` entry and a version bump.**
   `metadata.version` in SKILL.md frontmatter and the CHANGELOG always move
   together. The version header inside each `tokens/` file records the last
   version that changed *that file* — both currently read 1.3.0 while the skill
   is at 1.4.0, which is correct, not drift. Bump a token header only when you
   edit that file, and bump both when you do, since their palettes mirror. Those
   four files are the only places a version string lives. Commit messages follow
   `X.Y.Z — comma-separated summary of the rule changes`.
4. This repo holds style rules and templates only — never add client names,
   project figures, or engagement facts. This binds `CHANGELOG.md` hardest, since
   every entry summarizes a real engagement's review: record the lesson and the
   score that forced it, never the client or the document (follow the anonymized
   phrasing of the existing entries).
