# 2026-08-24 · What round 4 measured, and what it actually found

## Why this record exists

Round 4 compared this package driven by two agents on one source document. It was
read as "one platform is faster and produces better figures than the other". That
reading does not survive contact with the artifacts, and the real finding is about
this package rather than about either agent.

## What the comparison actually compared

The two build scripts, diffed:

- the second agent's differs from round 3's by **one line** (`VERSION` 0.1.589 →
  0.1.591). Its 25-second build had nothing to build.
- the first agent's differs from round 3's by **1446 lines** — a genuine rebuild.

Token counts were comparable (151,895 vs 154,060 output once the counter's ×2 was
corrected) and the "faster" side made MORE API calls (96 vs 66). What differed was
wall-clock and the fact that one side reprinted while the other built.

**Decision:** round 5 runs two passes, one variable each — both agents replay one
frozen recipe (path B), and both build from a new source (path A). Neither pass is
meaningful without the other, and the source for the path-A pass may not be the one
both recipes already encode.

## What the quality gap actually was

Measured, per page, on the rendered documents:

| | round 3 lineage | the rebuild |
|---|---|---|
| distinct layouts / top share | 5 / 28.6% | **3 / 64.3%** |
| visual share median | 43% | **35%** |

Seven of ten content pages sat at exactly 35% because seven of them were `split`.
`inspect_layout.py` already carried the sentence that explains it — *"A `split` page
cannot reach this number, so choosing the layout is part of meeting it"* — and
`storyline-templates.md` already carried the rule — *"A figure-led page is `stack` or
`split-wide` with the drawing in the wide cell"*.

**`new_deck.py` emitted `body split` on every content page it produced.** The author
did not choose the layout the owner faulted; the scaffold did, and it had been doing
so for every deck this package has ever scaffolded. Its own output measured 71.4% top
share — worse than the 70.0% deck a review rejected — while the deck GAP-024
records as accepted (the landscape roadshow deck at 33.3%) uses `split` zero
times.

**Decision:** fix the generator, not the author. The scaffold alternates `split-wide`
and `stack`. Measured on its own output: 4 of 11 content pages under target instead
of 10, worst page 46% instead of 37%, top share 42.9% instead of 71.4%. (37% is the
scaffold's worst page; the 35% quoted for the field deck is a different document.)

A first version also gave any unit too thin for the figure box `stack` whatever its
turn. A review caught it: two of the four shape-yielding analysis moves resolve to
sub-55% units, so an outline repeating one move put EVERY content page in `stack` —
100% top share, worse than the 71.4% being removed, on the plan-driven path that is
the package's main route. The override is gone; the rotation is unconditional.

## The threshold that was drafted and withdrawn

The owner directed that thresholds be settled by automated evals rather than by her
blind scoring. GAP-024 wants a bar on layout top share and has been open since
0.1.543 for want of a second document.

Five documents now carry a recorded verdict, and ordered they looked decisive: 28.6 /
30.0 / 33.3 not faulted, 64.3 / 70.0 faulted, an empty band between. A `provisional`
bar of 50 was written into `evals/thresholds.json` — and then measured against A1,
A1, the corpus's own accepted anchor: **78.6%**, worse than both faulted
documents — and note A1 is a *different* accepted document from the roadshow
deck above, which uses `split` zero times. Two accepted documents disagreeing
this hard about one layout is itself the finding.

**Decision: the bar was removed.** Scoping it to decks was considered and declined —
A1 is landscape too, and inventing a distinction to rescue a number is what convention
6 exists to stop. The metric is measured and printed without a bar, the
counter-example sits beside it in `reported_not_thresholded`, and GAP-024 records that
it may be mis-framed: the property separating these documents is probably not variety.

This is the automated route working rather than failing. A bar that a person had
blessed would have shipped; a bar checked against the corpus disconfirmed itself in
one command.

## Also fixed, because each was found by the same reading

- the Hermes token counter reported exactly twice the truth (two readers of one table
  sharing an accumulator);
- a trace inferred its entry path from the presence of an outline, and fingerprinted
  that outline as "the recipe" — so two replays were recorded as original builds and
  the script that produced every page was fingerprinted by nothing;
- `version_in` could not read a recipe's own `VERSION` line, only a rendered colophon;
- the evidence gate's obligation map listed the layout instrument and the tokens but
  not the generator between them, so a release that changed every page's layout owed
  no browser check.

## Not done here

The remaining round-4 tool findings — element-level overflow reporting, the rotated
axis-name false positive in `figure_clipped`, `--assess` being cleared between rounds,
`brief.py` exceeding a harness output cap — are real and are queued, not fixed. They
cost round trips; they did not cause the quality regression.
