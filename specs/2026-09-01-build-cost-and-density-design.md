# Design · The build's cost, and the density the reader asked for

*Written 2026-09-01, after the owner's review of the first deck built through
the figure data contract. Implemented across the releases that cite it. A record of what
was decided and why, not a source of rules: rule prose stays in `references/`,
values in `tokens/`, rationale in `CHANGELOG.md`.*

## The two verdicts

The owner validated `specs/2026-09-01-figure-data-contract-design.md` by asking
for a ten-page English market deck and returning two judgements:

1. **Ten pages took too long, and that is unfriendly to a user.**
2. **The delivered quality is ordinary** — with page-by-page detail: the
   development path figure too simple and carrying no time axis, with the time
   points the page states appearing nowhere on the drawing; a figure page with
   no brand colour and no content; a complex drawing that expressed none of the
   prose beside it; a two-by-two that was an empty box.

She also named a reference implementation to study for content logic, style and
layout, and asked for the gap between it and this package to be closed while
keeping LUMI's own visual language.

## What each verdict traced to

Neither traced to effort. Both traced to an interface.

**Quality.** The only way to put words into one of the 206 vendored shape units
was `shape_figure(shape, label_a, label_b)` — two labels, at the drawing's
bottom corners. A `position` unit therefore arrived as an empty box, a staircase
carried no dates, and an arrow chain named none of its stages. Every page she
faulted is that signature. Three blind spots kept it invisible: no timeline
component and no timeline renderer existed; D29 (numbers from the page appear in
the figure) printed its clean line on five of seven pages because their titles
spelled the numbers as English words; and D32 counted a page as drawn if it
declared a data contract, regardless of what the drawing said.

**Speed.** `new_deck.py` accepted structure and nothing else, so the author's
only interface to the words was regex surgery on the markup it had just
emitted. Measured on that build: a 519-line assembly script, 19 substitutions,
and 12 wrong guesses about markup shape, each costing an edit, a rebuild, a
render and a look. Separately measured on the same document:
`inspect_layout --deliverable` 21.2s against `--iterate --no-sheet` 3.3s, run
twelve times; raster export 3.7s for all thirteen pages against 1.1s for two.

## What was taken from the reference, and what was not

The reference is ten files and about 1200 lines: a CSS component library, a
109-line measure gate, and a three-command loop. It has no figure spec, no
generator, no two-by-two, no page contracts and no analytical moves — this
package leads on content logic, and copying that layer would be a downgrade.

**Taken:** the dense figure page (figure dominant, one lead line above,
conclusion boxes below); a semantic recolour mechanism where one class on a
container repaints everything inside it; a bitmap PowerPoint export.

**Not taken:** its 9.3px figure-text floor. Its own spec justifies that by
scoping the audience to a meeting-room screen and a PDF read at arm's length.
LUMI's delivery includes a projected screen, so the floor here is 12px and the
trade is stated rather than inherited (DR-22).

**Adapted rather than copied:** the recolour mechanism's names. The reference
uses lane indices; this package's palette rule is one colour one meaning, so
the classes are the four meanings the palette already carries — built/pass, red
line, partial, reference. An index-named set would let an author colour the
third lane green because it is third, and a reader would read that green as a
verdict.

## The decisions

1. **The content interface replaces the two labels** (`figure_slots.compose`),
   and refuses an empty composition rather than drawing one.
2. **Timelines and two-by-twos get renderers** rather than library shapes, in
   three tiers and to the reference figure the owner named.
3. **A seventeenth layout, `dense`**, rather than `stack` with a bigger figure:
   on a `stack` page the prose and the drawing compete for one vertical budget
   and the drawing loses.
4. **D43 gates the drawing's content** as a self-contradiction — the document's
   own spec says five items and the drawing names three — never as a judgement,
   so no reviewer is needed and `correlate` is exempt by construction.
5. **`new_deck.py --content` renders the document**, and every refusal in
   `deck_content.py` is an input shape: a field nothing renders, content for
   pages that do not exist, and a figure file that is not there all stop the
   build rather than producing a page that looks finished.
6. **PowerPoint is a bitmap export.** Reflowing into shapes would make it a
   second surface to debug, where every defect found is a defect in a document
   the checkers already passed.

## What this design does not answer

**Whether an agent outside this session reaches for any of it.** The
multi-agent conformance board is stale and its refresh needs the owner's own
keys and installs, so every release in this round ships with that obligation
waived and named. The evidence here is this repository's own renders, which say
the CSS and the renderers are right and say nothing about adoption.
