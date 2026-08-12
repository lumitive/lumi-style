# Reading the first third-party debug log — design record

Date: 2026-08-13 · Status: settled, implementing at 0.1.451 · Owner ask: analyse
the Cursor validation log and report; one PR for the findings.

## The input

The owner built a deliverable on Cursor under debug mode on skill 0.1.449 and
kept the artifacts. The log is the first execution record this package has from
an agent it did not drive: platform `cursor`, 10 commands, 5 error entries,
design/prose/layout snapshots attached 3/3/2 times, H1–H6 self-scored with
reasons. Repeated snapshots of one checker mean it failed and was re-run, which
is exactly the signal debug mode was built to give.

Alongside it, one defect the owner found by eye: the cover and closing globes
did not turn.

## What the log said

Three genuine defects, all caught by tools: four icon references resolving to
nothing (D19), 36 em dashes in sales copy (M9), and seven grade rows spilling
past the footer on one page (content spill, browser-only). Two of the three
would have shipped — a `<use>` pointing at nothing renders as empty space, and
declared CSS cannot see rendered geometry.

Then four things the tools got wrong or stayed silent about, which are what
this release is.

## Decisions

**D1 — A `[data-globe]` with no runtime is a D19 failure, not a new metric.**
D19 already says every reference in this document resolves inside this
document. `data-globe` is the runtime's selector and nothing else reads it, so
it is a reference in exactly that sense, and a document carrying the mark
without the script is the icon defect one layer out. It belongs with D12/D14/D15
— decidable facts about whether the artifact is finished — and not with the
design diagnostics, because motion is not what is measured: the runtime is in
the file or it is not.

*The direction is the design.* A mark obliges a runtime; a drawing does not
oblige a mark. The mirrored assertion would fail `fixtures/deck-pass.en.html`,
which carries the brand globe and deliberately carries no script, and a gate
whose first act is to fail this package's own passing fixture is the mistake
D19's first cut and the withdrawn `_grid_arity` both made. A cover or closing
globe with no `data-globe` is reported instead. One of the four unit tests
exists only to hold that direction in place.

The marker word is `createGlobe`, which is what `embed_globe.py`'s own `check()`
looks for in the block it just built. Reading the same word from both ends
avoids FM-04 in miniature: a second spelling here would be a private vocabulary
this repository never shipped.

**D2 — M6 gets the rules' semantic test; length becomes a backstop.**
The false positive was "Answer confirmation questions in blocks 1–3 and
cross-region" — 61 characters, a truthful enumeration label, counted as an
unsourced data range. The exemption had been "40 characters or fewer".
`writing-rules.md` §4 rule 6 has never mentioned a length; it asks whether the
pair carries quantitative context.

Three tests in order: a figure-shaped number anywhere in the block counts; a
counting noun in front of the pair reads as a label; length survives underneath
both. The first branch stays first because `deck-degenerate.en.html`'s plant is
a 61-character block containing `78%` — it is the only fixture that fails M6,
and `check_fixtures.py` requires every graded verdict to have one.

The counting-noun list is closed on purpose. An open test — any word before a
dash pair — would exempt every range in the language, which is the metric
switched off.

Declined: reporting M6 instead of gating it. The predicate is decidable and the
window is defined in the rules; the defect was a bad proxy, not an undecidable
question.

**D3 — Debug mode reads the checkers' JSON instead of tailing it.**
A nonzero exit writes its own error record from the last twenty lines. That is
right for a crash and wrong for a checker: every check script prints its
thresholds last, so the tail of a `--json` failure is the schema footer. Three
of the log's five errors were that footer.

`debug_log.py` parses the output when it is JSON and records the verdicts that
are not `ok`, covering both shapes the checkers emit (a list of per-file
documents from check_prose/check_design; one dict with top-level `verdicts` and
`unmeasured` from inspect_layout). It falls back to the tail for anything else,
which is the case that must keep working — a crash, or a tool that is not ours.
`n/a` is not a failure; and because check_design drops an unmeasurable file from
its JSON while still exiting 1, "nonzero with nothing failing" is a real answer
and is written as a sentence rather than a blank.

The extractor lives in `debug_log.py` rather than `scripts/lib/`. The three
checkers each roll their own `grade()` and there is no shared verdict helper to
extend; adding one for a single consumer would be the wrong direction.

**D4 — Do not narrow the geometry matrix. A rule, not a gate.**
The run was verified at 16:9 alone, and its spill fix left one pixel of
clearance under a gate that fires above one pixel. `inspect_layout.py` already
runs the points a document's `data-geometry` implies — four for landscape, two
for portrait — so the failure was an explicit `--geometry 16x9` switching the
matrix off, not a missing default. Its help text had also been advertising a
three-geometry default since the default became five at 0.1.390.

The rule goes in `design-rules.md` §7 with a palette axis beside it (`--dark` is
a second run, not a matrix point) and re-flows to the three entry points. Owner
decision, taken during planning: state the requirement, do not add it to
`check_evidence.py`'s obligations.

**D5 — Two failure modes, both invisible without the snapshots.**
FM-12, the fix that spends a neighbour's headroom: satisfying M9 drove M11 from
40.0 to 56.0 against a ceiling of 60.0, with three checkers green and none of
them saying so. FM-13, a threshold standing in for the rule's own test, which is
D2 above.

Both are recorded rather than mechanised. FM-12's mechanical form would be a
checker that diffs its own previous run, which needs state this package
deliberately does not keep; the debug log already holds the snapshots, and the
prevention is to read them.

## Out of scope

The build script that produced the empty `<script></script>` lives outside this
repository and is not edited here. What this release owes is the check that
would have caught its output, plus the sentence in `SKILL.md` saying the runtime
is built by the assembler and never harvested from another file — the shape the
`_sources/deck|prd|train` assembler family also has.

The ten-minute target in `SKILL.md` is untouched: the owner is deciding it, and
0.1.450's measurement (27 minutes for a 30-page A4 training handbook) is the
input to that decision, not to this one.
