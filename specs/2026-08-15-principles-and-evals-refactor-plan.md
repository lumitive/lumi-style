# Principles, taxonomy and evals — implementation plan

Design record: `2026-08-15-principles-and-evals-refactor-design.md`.
Date: 2026-08-15 · Status: executing.

One release per commit, subject `X.Y.Z — summary`, and a branch carrying several
releases is **merged, not squashed** (two guards assume one commit per release).
Every new gate ships with a deliberate-red run recorded in its CHANGELOG entry.

## P0 · Structural reorder (GAP-007)

The hazard is that a reorder is indistinguishable from an edit in a diff, so
each commit here is **content-frozen** and proves it mechanically: the multiset
of non-heading lines before and after must be identical. `scripts/check/`
gets nothing new; the proof runs in the commit's own verification and is quoted
in the CHANGELOG entry.

- **P0.1** `design-rules.md` section order. Today it runs 1, 1c, 1d, 2, 3, 4,
  4b, 5, **7, 6** — section 6 physically follows section 7. Reorder to
  monotonic, fold the lettered sections into their parents' sequence, and
  renumber the chart rules (today 1-5, 6, 7, 7b, 7c, 7d, 7e, 8, 8b) to 1..N.
- **P0.2** Re-flow every `§` citation the reorder breaks — `SKILL.md`,
  `AGENTS.md`, `prompts/lumi-style-core.md`, `README.md`, the checkers, and the
  ledgers. `check_repo.py`'s markdown-link and citation guards are the net;
  a dangling citation must go red before this commit is written.
- **P0.3** `storyline-templates.md`: the shared apparatus currently sits between
  Template 1 and Template 2. Move it ahead of the templates.
- ~~**P0.4** `eval-rubric.md`: collapse the three gating descriptions.~~
  **Moved into P3.1 while executing P0.** Two reasons, both found by doing the
  work rather than by planning it: collapsing three prose descriptions is
  **rewording, not a move**, and P0's whole safety property is that its commits
  are content-frozen and prove it — mixing the two is on this repository's own
  do-not-do list. And P3.1 rewrites that file anyway when H1–H6 becomes C1–C7,
  so doing it here would edit the same prose twice and invite a conflict
  between the two edits.
- **P0.5** Stable rule IDs. Each rule family gets an ID that does not move when
  sections do — this is what makes the next reorder cheap and what D1's parent
  declarations attach to.

## P1 · Constitution and fences

- **P1.1** `references/PRINCIPLES.md` — six clauses with obligation strengths,
  the conflict exit, and the scope sentence ("this constrains how rules are made,
  not the generation of individual documents").
- **P1.2** The conflict exit into `SKILL.md`'s pre-delivery step and
  `storyline-templates.md`'s critic gate. A procedure that exists only in
  `PRINCIPLES.md` is not executed at the moment it applies.
- **P1.3** `principle trace` guard: every rule family declares a P-id or `GOAL`;
  the P-id must exist. **Deliberate red**: delete one declaration, watch it fail.
  Its documented limit: it cannot verify the parent was chosen correctly.
- **P1.4** Red-line copies deleted down to one hand-written home each, with the
  parity guard holding the rest.
- **P1.5** `KNOWN_GAPS.md` entry for P-1's coverage shortfall (layout and font
  rules are only partly guarded; an agent inventing a seventeenth layout is
  caught by nothing).

## E1 · Early proof point

Rebuild one real deliverable under the post-P1 rules and score it against
C1–C7 as they stand. **If it is worse than the 0.1.449 level, stop and
re-examine rather than continue building.** Recorded through the evidence gate,
not as a sentence in the release notes.

## P2 · Product definition, taxonomy, trace

- **P2.1** Product definition into `specs/` (English).
- **P2.2** The `genre` / `storyline` split across the registry, the checkers,
  `new_deck.py`, the rubric and the entry points.
- **P2.3** Trace schema and collector — verdict fields machine-written, trace
  opened when the storyline is agreed, `principle_yields` and `refused_to_emit`
  included, free text rejected by the schema guard.
- **P2.4** `check_privacy.py`, three layers, `not_attempted` distinct from pass.
- **P2.5** `brands/registry.json`.

## P3 · Evals rebuild

- **P3.1** C1–C7 into `eval-rubric.md`; the blind scoring sheet follows the
  evidence items.
- **P3.2** `scores.json` schema migration, `corpus_id` required.
- **P3.3** Agreement study made permanent.
- **P3.4** Cross-page number consistency (C4-②) — the most direct hold on
  figure-text hallucination, and today there is no check at all.
- **P3.5** Judge finding layer: quotations required, reported, never gates.
- **P3.6** `check_outline.py` — the outline-stage evidence items and C5's
  `data-omitted` declaration.

## T-track (parallel, does not block the structure track)

- **T1** Usage fields and per-phase attribution. Starts alongside P1 so a
  baseline covers the whole run. **This is the falsification instrument for the
  four-beat cost argument**; without it that argument cannot be tested.
- **T2** Shape library: curation, tagging, `embed_shapes.py`, selection rules.
- **T3** Data contract — a figure declares its data; label, data block and body
  text are cross-checked.

## Converge

- **P4** Model matrix: Opus 5 / Sonnet 5 × three effort levels, quality and cost
  columns produced together.
- **P5** Candidate queue live, owner ratifies, ledger health metrics counting.

## Order of work and what blocks what

P0 runs first because a reorder after other edits is a merge hazard rather than
a pure move. P1 depends on P0.5's stable IDs for its parent declarations. E1
depends on P1 only. T1 is deliberately started early and depends on nothing.
P3 depends on P2.3 for traces to score against. P4 depends on P3.2's
`corpus_id`, without which the agreement study has no joinable rows.
