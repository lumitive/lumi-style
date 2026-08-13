# Evals from an accepted document — design record

Date: 2026-08-14 · Status: settled, implementing at 0.1.455 · Owner ask: stop the
multi-agent comparison and define what "good" is first, from
`~/Documents/LUMI-Style/adopting-lumi-style.0.1.449.en.html`.

## Why the previous order was wrong

A multi-agent comparison was built before any definition of the bar. When both
agents failed the conformance task there was no reference point to judge whether
the failure meant anything, and the day was spent debugging instruments in the
dark — producing two published attributions that were both wrong.

The deeper fault: `T1-deck` had never been validated as a proxy for "a document
the owner would accept", and it was being used as one.

## What the measurement showed

The accepted document passes **all sixteen gates and `=0` checks with a zero
count**. It proves the checkers run; it does not prove they discriminate. The
rejected document passed all nineteen design verdicts.

What separates them is entirely in quantities that had no threshold:

| | accepted | rejected |
|---|---|---|
| prose-only share of content pages | 0.000 | 0.455 |
| figures per content page | 0.957 | 0.227 |
| list items per content page | 0.739 | 4.409 |
| median visual share | 81% | 16.5% |

## Decisions

**D1 — Thresholds carry their evidence, in the data.**
`calibrated` / `inherited` / `provisional` / `declined`, per genre per metric.
The owner asked for all four genres defined at once and only one genre has an
accepted document, so without this field "define all four" becomes "invent
three". Four of twenty cells are calibrated; nine are provisional. The count is
the honest summary of how much of this table is evidence.

The precedent is not abstract: 0.1.339 invented an 82% page-fill floor, it was
satisfied by stretching table rows, and its reader scored three dimensions at 1.

**D2 — Only `training` and `sales` may read `calibrated`.**
Those are the two genres with a document on record — one accepted, one rejected.
An extension to `marketing`, `consulting` or `internal` is `provisional`, and the
first draft of this table over-claimed exactly that. Corrected before shipping.

**D3 — The corpus sweep is part of setting the table, not a later check.**
Sweeping the thirteen existing deliverables corrected the table twice:
`min_content_pages = 8` (a ratio over four pages is one page's opinion; three
component demos read 0.0 figures per page because a globe lives in `.markcell`
while D5 counts `.fig`), and `internal` lost its figure floor entirely (a real
design document sits at 0.273 and passes every checker — a floor there fails a
document for being what internal analysis is).

**D4 — A metric that stopped separating is recorded as such, not dropped.**
`rect_only_share` and `shape_kinds_min` separated the two documents yesterday and
do not today, because the rejected document's build script was repaired in
between. They move to `reported_not_thresholded` **with that history**, because a
metric that never fails is not a metric everyone passes — the same distinction
`check_fixtures.py` draws for the fixture suite.

**D5 — `eval_corpus.py` never runs in CI.** It evaluates documents, not this
repository. Same reason `inspect_layout`'s design judgements do not gate.

## Foundation faults fixed in the same release

1. **D20 declared a gate and did not gate.** The exit decision was a
   hand-written tuple that fell one behind; a document failing D20 alone exited
   0 while five files said it gated. The decision reads the rows now, as does
   the summary sentence that was a fourth copy of the same list.
2. **The rubric had two words for three tiers** (gate / graded / reported). Six
   rows called `reported` are graded against a hard predicate and print `FAIL`.
   The graded tier is where an Evals threshold belongs.
3. **Five genre vocabularies.** `check_prose --genre consulting` was refused
   while every other script accepted it, which makes a genre-keyed Evals suite
   impossible. One name set in `deliverable_registry`, behaviour stays per
   script, held by a new guard.
4. **`environment_check`.** The environment is proven reachable before any
   verdict is attributed. This is the mechanism whose absence produced two wrong
   attributions the day before.

## Declined

**A bar for `internal` figures.** See D3 — no accepted internal document exists
and the real candidates argue in prose. Recorded rather than left blank so it is
a decision, not an oversight.

**Gating `eval_corpus` in CI.** It measures documents that live outside this
repository, and CI has no browser for the rendered half.

## Not done here

The 4×4 model matrix (Opus / Sonnet / Haiku / Fable × four genres), the human
H1–H6 sampling loop, and the agreement check between mechanical scores and the
owner's scores. All three need this table to exist first; the agreement check is
what will show whether the table measures the right thing at all.
