# Analysis rules — how a fact becomes a finding

> Part of lumi-style. Load order: after `storyline-templates.md`, before any
> page is written. `references/` wins on conflict.

**Why this file exists.** Two blind reviews and an owner verdict established
that this package could produce documents with no detectable defects that
still contained no insight — data displayed, never analysed; pages that
describe, never argue. The rules below are the generation side the package
never had: they do not gate content (that line holds — see
`storyline-templates.md`), they produce it. A page that skips them will still
render; it will also still read as a product sheet, and the benchmark review
(eval-rubric.md) is where that gets caught.

**The one-sentence discipline: a page earns its place by a finding, and a
finding is a fact that has been put through an analytical move.** A fact
("the accent appears 84 times as a fill") becomes a finding only when a move
is applied to it ("84 fills against 0 text uses — the accent is a surface,
never a voice, which is why one colour can mean one thing"). The move is
what consultants are trained in, and it is what this file names.

## 1 · The five analytical moves

*Serves: **GOAL**.* · id `AR-1`

Every content section of an external document declares which move produced
its finding. There are five, and the declaration is one word. A section that
declares none is not blocked — it is reported by the outline gate, and the
benchmark review will ask the question a machine cannot: where is the
insight?

1. **Compare** — set the fact against a benchmark, a time series, or a peer
   group. The finding names the gap and its direction. Input shape: one
   value plus at least one reference value. Frameworks: benchmark table,
   radar, Harvey scorecard. The tell that it is missing: a number standing
   alone with no reader able to say whether it is good.
2. **Decompose** — break the whole into parts that are mutually exclusive
   and collectively exhaustive, then find the part that carries the story.
   Input shape: a total and its parts. Frameworks: issue tree, waterfall,
   Mekko, value chain. The tell: a total discussed as a total while one
   segment drives all of the movement.
3. **Position** — place items on two independent axes the reader cares
   about, then read the quadrants. Input shape: a set of items scoreable on
   two dimensions. Frameworks: 2x2, SWOT (strengths/weaknesses internal,
   opportunities/threats external), 9-box. The tell: a list of items with
   properties that never becomes a map.
4. **Correlate** — show that two quantities move together (or fail to), and
   say what drives what, or say plainly that direction is unknown. Input
   shape: paired observations. Frameworks: scatter, driver tree. The tell:
   two trends narrated side by side with the relation left to the reader.
5. **Bridge** — explain the distance between two states of one quantity by
   naming the contributions. Input shape: a before, an after, and the
   attributable pieces. Frameworks: waterfall, three horizons. The tell: a
   change reported without its composition.

## 2 · The insight ladder

*Serves: **GOAL**.* · id `AR-2`

A finding is not yet an insight. The industry-standard ladder has three
rungs, and this package binds each rung to a page element, so the ladder is
visible in the markup rather than a hope:

| rung | question | where it lives |
|---|---|---|
| **finding** | what is true? (the move's output) | the page title |
| **implication** | so what, for THIS reader? | the `.take` line |
| **action** | who should do what about it? | the ask page, or the section's closing page |

A title that states a fact without a move behind it is a label (M1's
territory). A `.take` that restates the title instead of answering "so what
for you" is the rung this ladder exists to catch — the implication names the
reader's stake, not the page's content.

## 3 · The analysis beat

*Serves: **GOAL**.* · id `AR-3`

Between the agreed storyline and the first written page there is an
**analysis beat**. Its product is one line per content section, recorded in
the outline:

    analysis: <move> | finding: <the sentence that will be the title> |
    implication: <the sentence that will be the take>

Two rules about it, both process:

- **The beat is where the ghost deck happens.** Before any markup, each
  section's line names the figure that will carry the finding (the framework
  from `assets/frameworks.json`, or a chart form from design-rules §4).
  Storyboard first, compose second — the industry calls this the ghost deck,
  and it is the cheapest point in the whole pipeline to discover that a page
  has nothing to say.
- **`check_outline.py` reports declaration coverage and never judges
  content.** "6 of 8 content sections declare an analysis" is a fact; whether
  the declared move is the right one stays with the person running the
  benchmark review. Content is never gated (the form/content line holds);
  the DECLARATION is checkable, which is the pattern this repo already uses
  for omissions (`data-omitted`) and scope (D26).

## 4 · Choosing the framework

*Serves: **GOAL**.* · id `AR-4`

`assets/frameworks.json` is the dictionary: each entry names the analytical
question it answers, the slots to fill, the misuse warning, and the shape
ids in the library that draw it. The selection chain is **question →
framework → shape** — design-rules §4.1's relation rule then holds the
chosen shape to the data as before. Choosing a framework because it looks
professional is the same defect as choosing a shape because it looks good:
the 2x2 whose axes are not independent and the SWOT filled with restated
facts are decoration wearing an analysis's clothes, and the misuse line in
each dictionary entry names exactly that failure.
