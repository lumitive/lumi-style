# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

lumi-style packages LUMI's design language and writing style as a cross-platform
LLM skill. It ships Markdown rules and design tokens — there is nothing to build
or install. "Development" here means editing rules, keeping the entry points in
sync, and recording changes in the changelog.

## Checks

```bash
python3 scripts/check_repo.py            # repo invariants; exit 1 on any failure
python3 scripts/check_prose.py <file>    # AI-flavor metrics on a deliverable
python3 scripts/embed_font.py            # @font-face block with the face inlined
bash    scripts/ci_wait.sh <PR>          # bounded wait, short-circuits on outage
```

Standard library only, no dependencies. `.github/workflows/ci.yml` runs
`check_repo.py` plus syntax checks on every push to `main` and every pull
request. Its five guards are the mechanical half of the invariants below: version
stamps, the English-only red line, markdown link targets, palette parity between
the two `tokens/` files, and ban-list parity.

`check_prose.py` measures the AI-flavor metrics (M4, M8–M11) on a **deliverable**,
not on this repo, so CI cannot run it — there are no deliverables here. It is
English-only and takes `--genre internal` to exempt internal analysis documents
from the em-dash rule.

Its banned-phrase list is a second copy of `references/writing-rules.md` §2, so
the **ban-list parity** guard holds the two together: every phrase §2 bans must
appear in the script either as a matching pattern or in `NOT_MECHANIZED` with a
reason, and the script may not ban anything §2 does not list. Adding a phrase to
the rules without deciding what the machine does about it fails CI, which is the
point — the alternative is a rule that looks enforced and is not.

Everything the checks cannot decide — above all whether a rule change was
re-flowed into the entry points — stays with the reviewer.

## When CI is slow or down

`main` requires the `checks` status and enforces it for admins, so a GitHub
Actions incident blocks merging for everyone. Do not wait it out by polling.

1. **Ask the status page before waiting**, not after. One call to
   `githubstatus.com/api/v2/components.json` answers whether waiting is worth
   anything. Polling a capacity-constrained service also adds to the load causing
   the outage.
2. **Bound every wait.** `scripts/ci_wait.sh <PR>` does both of the above: it
   short-circuits when Actions is degraded, and otherwise checks three times over
   about four minutes and then stops. Open-ended polling turns a service problem
   into a person problem — during the 2026-08-06 outage it consumed most of a
   working session and merged nothing.
3. **Separate correctness from the gate.** `check_repo.py` answers "is this
   change good", locally and in seconds. CI only unlocks the merge button. During
   an outage, report the local verdict and hand over the decision rather than
   blocking on a queue nobody can drain.
4. **A cancelled run is a symptom, not a verdict.** Re-run it once. If it is
   cancelled again during a declared incident, stop re-running.
5. Merging anyway is `scripts/emergency_merge.sh <PR>`, which verifies the merge
   result locally before it unlocks anything and restores protection on every
   exit path. It is the last resort, not the second.

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
   The repo carries **one version**: `metadata.version` in SKILL.md frontmatter,
   the newest CHANGELOG heading, and the version stamp in each `tokens/` file all
   read the same number and bump together, even when a revision leaves the tokens
   untouched. Those four places are the only ones a version string lives, and the
   `version stamps` check fails on any mismatch. The historical notes inside
   `tokens/lumi-theme.css` ("v1.3.0: light-first…") name the version that
   introduced a change and are not stamps — leave them alone. Commit messages
   follow `X.Y.Z — comma-separated summary of the rule changes`.
4. This repo holds style rules and templates only — never add client names,
   project figures, or engagement facts. This binds `CHANGELOG.md` hardest, since
   every entry summarizes a real engagement's review: record the lesson and the
   score that forced it, never the client or the document (follow the anonymized
   phrasing of the existing entries).
