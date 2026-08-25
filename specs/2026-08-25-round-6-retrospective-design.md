# Round-6 retrospective — what two agents hit, and what the code says

Date: 2026-08-25 · Status: in progress · Releases: 0.1.598 onward

## The case

The sixth validation round drove two agents on two platforms from the same
source document: one at 0.1.596 (five build rounds), one at 0.1.597 (six). Both
delivered green. Both wrote a report naming the tools that got in the way, and
**six of those findings are the same finding, arrived at independently**. That
is this repository's own promotion threshold (CLAUDE.md convention 2, and the
two-document rule) reached without anybody arranging it.

The expensive class is not the friction. It is that **three hard gates misfired
and both authors edited their deliverables to satisfy them**: one added axis
names to 2x2 diagrams that carry no scale, the other merged a figure's labels
into a single `<text>` node so its `textContent` ran past a fourteen-character
ceiling, and one rerouted two connectors as elbows. FM-13 already names the
class — *a false positive that edits prose is worse than a miss, because
nothing downstream records that it happened* — and these are three shipped
instances of it, found in one week.

## What was verified before anything was written

Every claim in both reports was checked against the code at HEAD. Two of them
are wrong and are **not** implemented:

- *"The verdict detail lives only in terminal scrollback."* False. A failing
  command's last twenty lines are stored, and the three checker reports are
  attached whole. The real defect is that the next round deletes them.
- *"`check_facts` charges the author for CSS comments and shape path data."*
  False. `<style>`, `<script>` and comments are stripped before the scan, and
  attributes never survive tag-stripping at all. The real sources are a version
  stamp with a `v` in front of it and a caption ordinal past nine.

A third, *"D31 is permanently red because apparatus pages are not declared"*,
has the wrong mechanism (that attribute belongs to two other metrics) and the
wrong frequency (eleven of thirty-two). Its noise complaint stands on its own
evidence: it is the top row of the ledger's failing table.

## One finding was refuted by measurement, and is not implemented

The design carried a fourth fix: `figure_axis_overlap` computes its plot region
as the union of every drawn element, so a figure composed from one library
`<use>` was said to have no in-viewBox position an axis name could occupy.

**Measured, that is not true of the artifact it was claimed from.** The 2x2 in
question occupies 79.5% x 78.4% of its own drawing, its viewBox is 640x385, and
both of its axis names sit inside the viewBox and clear of the shape — one
below it, one to its left. There was room the whole time. The gate fired on a
name lying **across the quadrants**, which is what the rule asks it to fire on,
and moving the name out of the plot is the correct response rather than a
workaround.

So the region is left alone. What the round actually paid for was **not knowing
which way to move**: the finding named the page, the text and the size of the
overlap, and the author spent three rounds guessing. That is what changed.

The stop condition written into the plan — *if no single threshold separates
the two sides with headroom, stop and re-scope rather than tune the number* —
is what produced this outcome. Tuning it until both fixtures agreed would have
been FM-13 committed by the person fixing FM-13.

## The releases, in order

One release per idea, one commit each, rebase-merged. The numbers are not
written here: a spec that names a version it has not shipped is a forward
promise, and this repository has a guard for those.

1. **The three figure gates.** A name with a digit in it is not a value; the ink
   check confirms on geometry rather than on bounding boxes; the axis finding
   names the move rather than the overlap.
2. **`check_facts`.** A `v`-prefixed version stamp is provenance, not a
   quantity; a caption ordinal is furniture on both sides of ten.
3. **D26/D31.** The corpus is what a reader meets, and a scope note declares
   rather than covers.
4. **The debug log.** The record belongs to the artifact; the round is a field
   on it.
5. **The trace.** One document, one trace.
6. **The recipe.** The driver already knows it; it records it.
7. **The outline's omissions.** A declaration made once reaches the page.

Ordering is not free: 3 lands before 7 (otherwise an emitted scope note
satisfies coverage through its own prose), and 4 before 5 and 6 (the log is the
record the later rounds are read out of).

## What is deliberately not done

- **No bar moves**, D31's included. Release 5 changes what a trace counts, so the
  denominator behind "eleven of thirty-two" changes meaning at that commit. Any
  bar proposal waits for a re-measurement over traces recorded after it, run
  through `bar_replay.py`.
- **The scaffold keeps seeding the checklist's section names into the agenda's
  run lines.** That a fresh scaffold measures itself compliant is perverse, but
  the seeding is a documented decision and the honest fix is that D31 stops
  being satisfiable by anything a reader would not call coverage.
- **A digit-led name — `5G`, `4K`, a bare `2024` — still counts as a value.** It
  is the same shape as `3.5x` and `4.2m`, so no pattern separates them; recorded
  in KNOWN_GAPS with the measurement that would settle it rather than guessed at.
