# LUMI Design Rules

> **Subordinate to the four hard rules in `SKILL.md`.** This file is craft
> knowledge and defect history: what has gone wrong before and what fixed it.
> None of it outranks *design per page*, *verify on rendered geometry*, *redraw
> rather than grow chrome*, and *done when a human reads the page as intentional*.
> Read it as a designer reads a body of precedent, not as a checklist to satisfy.
>
> Skeleton researched from the public web design of SpaceX and Tesla (one claim
> per screen / numbers-as-copy / monochrome discipline); the palette and its
> semantics are LUMI's own. Tokens live in `tokens/`; this file covers usage and
> judgment. (Repository language: English only — red line.)

## 1 · Color: one color, one meaning; hierarchy via transparency

- **Canvas — light by default, dark on request.** The light canvas is **pure
  white (#FFFFFF)** with cards a hair off it (#FAFAFA). **Not the warm cream**
  (#F4F1EA and its neighbours) that has become the field default: it reads as a
  template, and it drags every accent toward a sepia cast. The dark canvas is
  **Apple space grey (#1D1D1F)**, cards #2C2C2E — a grey that has been looked at
  by a lot of people on a lot of screens. Both palettes share one structure: build
  with semantic tokens and switch with a single `body.dark` override block, never
  a forked file. Literal colors in component CSS or inline SVG are a defect,
  because they silently ignore the switch.
- **One color, one meaning — four of them, each clearing 4.5:1 as text on its own
  canvas.** This is stricter than SpaceX/Tesla: they let color appear only where it
  carries meaning; LUMI pins each meaning to exactly one color.

  | Token | Light | Dark | Means |
  |---|---|---|---|
  | `--acc` | #48633E (6.71) | #7C9F63 (5.61) | built · running · pass · emphasis |
  | `--seal` | #C8102E (5.88) | #E0685A (5.05) | warning · red line · veto · blocked |
  | `--amber` | #A86407 (4.68) | #E0A73E (7.83) | partial · in progress · awaiting an input |
  | `--brass` | #7A6C52 (5.13) | #C3B393 (8.17) | reference · archival · out of scope but real |

  *Provenance: the palette was accent-plus-warning only, so "partial" and "not
  built" both rendered as dashed grey and a deck could not say the one thing it
  most needed to say about itself. Amber and brass exist to carry state, not to
  decorate — adding a fifth colour needs a meaning that none of these four covers,
  and a contrast measurement on both canvases.*
- **Hierarchy comes from a transparency ladder, not new grays** — and since 1.8.0
  it is **two ladders**, because one of them was unreadable. The token names carry
  the rule:
  - `--tx1..--tx4` is the **text ladder**. Every step clears **4.5:1** against
    both `--bg` and `--card-bg` of its own palette. Text may use nothing else.
  - `--ln1..--ln3` is the **non-text ladder**: rules, borders, hairlines, tint
    fills, chart furniture. It may never carry text.
  - Marks a reader must distinguish (a data dot, a status ring) are text for this
    purpose, not furniture. Use the text ladder.

  **The two palettes do not share one alpha list.** Light derives from ink
  #2B2E33 at α .92/.80/.72/.66 (text) and .20/.12/.07 (non-text); dark from cold
  white **#F0F0FA** at α .88/.76/.66/.58 and .18/.11/.07. **Dark-canvas text is
  cold white, never pure white.** Measured ratios live in `tokens/design-tokens.json`
  under `contrast.measured`; `check_repo.py` recomputes them and refuses a ladder
  that drops below the floor.

  *Provenance:* until 1.7.0 one alpha list served both canvases and the lower
  steps ran 2.91 / 1.81 / 1.32 / 1.16 on light and 4.08 / 1.99 / 1.36 / 1.16 on
  dark. A shipped deck put its eyebrows, captions, source lines, page numbers and
  table headers on those steps, and the reader's first note was that both canvases
  were exhausting to read. **Pick a text color by contrast, never by how quiet you
  want it to look**; if a thing should be quieter than `--tx4`, make it smaller or
  cut it, do not fade it below legibility.
- **Text on a filled surface is checked separately.** `--on-acc` is
  palette-dependent: cold white on the light accent measures 5.93, and on the
  lifted dark accent 2.65, so the dark palette flips it to canvas ink (6.69).
  Until 1.8.0 one value claimed to serve both and white labels inside accent bars
  shipped unreadable on dark.
- Chart data colors are an independent CVD-validated triple (blue/red/teal) and
  never change with the brand palette — data distinguishability outranks branding.

**A colour is verified against the surface it is printed on, not against the
canvas.** A status chip sits on its own wash and never touches `--bg`; an accent
field is a third surface with its own foreground. 2.2.0's amber measured 4.68
against a canvas it never touches and **4.24 against the wash it actually sits
on**, and the dark seal did the same — both had been "verified" since 1.8.0.
`check_design.py` now discovers painted surfaces by reading the CSS, composites
translucent washes onto the canvas first, and grades a rule that declares its own
background against that background.

**Colour at page scale is a claim; colour as hairlines is decoration.** The part
openers are full accent fields with the claim reversed out, and they are the only
pages in the deck that are. Restraint everywhere is not a voice — a deck in one
register reads as careful rather than as anything. Text on a field takes the
solid `--on-accent`: fading it to 72% for hierarchy drops it to 3.97:1, which is
the 1.8.0 contrast defect returning through a colour choice. Hierarchy on a field
comes from size and letterspacing.

## 2 · Typography: two voices, never mixed

- **Primary face — D-DIN takes over** (v1.2): D-DIN is the single Latin face
  for titles, body, and data alike, with CJK fallback (PingFang SC / Noto Sans
  SC). Display titles are ALL-CAPS at **weight 400** with tight leading
  (0.95–1.0) — size and case carry the authority, not boldness; bold is
  reserved for the accent word. Rounded faces (Quicksand/Nunito) are retired
  from decks. **The face ships with this skill** — `assets/fonts/D-DIN.woff2`
  and `D-DIN-Bold.woff2` (SIL OFL, `COPYING.txt` alongside). Embed it as a data
  URI, never link it: `python3 scripts/embed_font.py` prints the ready
  `@font-face` block, and `--check` verifies the vendored files are intact.
  A linked font falls back the moment a deliverable is opened offline, emailed,
  or printed elsewhere; a declared-but-unvendored one renders nothing at all,
  which is what shipped in 1.2.
- **Small type is a contrast problem before it is a size problem.** A reader
  reported both canvases exhausting to read when 9.5px labels sat on ladder steps
  measuring 1.81:1; raising the contrast fixed most of it. **There is no universal
  size floor** — 1.8.0 set one at 11px without being asked, and a floor applied to
  every label in every figure is the kind of blanket rule that stops a designer
  looking at the page. Set type for the page: a dense reference table and a
  three-node diagram do not want the same scale. The chart scale of figure title
  13 / axis 11.5 / source 10.5 is a **starting point**, not a minimum. What is not
  negotiable is §1's contrast floor, because that came from a reader.
- **Data voice** (codes/rates/percentages/dates/counters/specs): D-DIN or
  monospace, tabular-nums always on; **counters and countdowns give each digit a
  fixed-width box** so changes never reflow.
- Judgment rule: **a value someone will read out and verify goes in the data
  voice**; anything spoken to a human goes in the narrative voice.
- D-DIN is SIL OFL 1.1 (Datto, 2017): free for commercial use and embedding;
  Latin-only, so CJK must fall back to a Chinese face; derivatives may not use the
  reserved name "D-DIN".
- **CJK has no uppercase**: Latin eyebrows use small caps-style ALL-CAPS +
  0.14em tracking; the CJK equivalent for display titles is size contrast +
  0.02em tracking — never "shout" CJK by scaling alone.

## 3 · Layout: one claim per screen

- Each screen/page carries exactly one claim: a conclusion-style headline (an
  accent word in green is available, not required — mechanical emphasis on every
  headline is inflation), **one to three sentences of support whose lengths
  visibly differ — on every content page without exception, figure pages
  included** (D8), one centerpiece, a thin footer rule with source + page number
  — nothing else. *Provenance: this rule has stood since 1.6.0 and 10 of 25 pages
  shipped without a support line — all six figure pages plus four table pages —
  because a figure felt like it spoke for itself. It does not: the reader arrives
  at a diagram with nothing telling them what they are about to look at.* (The rule read "one sentence of support" until 1.6.0, which
  drove sentence-length variance across a deck to near zero; see M8.) **The headline has no word
  ceiling**: its length is set by the title contract in
  `storyline-templates.md` — topic + assertive subtitle carrying a verifiable
  fact — and the only hard limit is two lines at the design viewport. (Lesson:
  v1.2 replaced that contract with "a giant short headline (3–6 words)", which
  compressed deck titles to 4–8 CJK characters, deleted every evidence figure
  from the title line, and left bare antitheses that read as AI filler.) Prefer
  hairline-separated rows over card boxes: on a dark canvas, borders are
  furniture; hierarchy comes from the ink ladder;
- **Every page has one focal element, and it is not the title.** The thing the
  eye lands on before it starts reading: a display number with its gloss, a
  claim set at display size, or a figure composed to dominate its cell. Which of
  the three, and whether a page wants a number at all, is a design decision for
  that page — **there is no size floor and no requirement that it be type.**
  `.lead` and the `--fs-lead / --fs-lead-xl / --fs-say` tier are in
  `tokens/`; `inspect_layout.py` reports the ratio of the largest element to
  body copy and names the pages that have neither. *Provenance: a reader called
  a 28-page deck flat and mediocre, and the measurement agreed exactly — 24 of
  28 pages had nothing on them larger than 15px body copy, and only the cover
  and two stat-band pages carried any display tier at all. A page with no entry
  point gets read top-left like a document instead of looked at. The fix is per
  page: half of those pages got a number, the rest got a redrawn figure.*
- **A part opener earns its page.** One line at display scale saying where the
  reader is and what the next run of pages argues, and nothing else. A navigation
  rail cannot do this at a glance, and the quiet page is what makes the dense
  ones read as dense on purpose.
- **A page has a layout, chosen for its content.** Fifteen ship in
  `tokens/lumi-layouts.css` as `.body.<name>`; pick with the table below. This is
  the same discipline as §4's chart form-selection: the point is not that many
  layouts exist, it is that the content decides which one.

  | The content is | Layout |
  |---|---|
  | one number, and it is the story | `hero-band` |
  | a short frame, then a dominant block | `band-hero` |
  | 2 / 3 / 4 parallel items of equal weight | `columns-2` / `columns-3` / `columns-4` |
  | four parallel items, or a matrix with named axes | `quad` |
  | a centerpiece wider than 3:1 | `stack` |
  | a map, globe or wide timeline | `full-bleed` |
  | a tall or square centerpiece **and** long prose | `split` or `split-wide` |
  | long prose with small supporting evidence | `split-narrow` |
  | a claim whose qualifications are as load-bearing as itself | `sidebar-notes` |
  | a three-stage sequence read downward | `thirds-v` |
  | a progression where direction carries meaning | `diagonal-flow` |
  | a part divider or section opener | `rail` |
  | a table of 6 or more columns | `stack`, no exceptions |

  **This table is a reference, not a lookup.** It says what has worked, not what
  to apply. Which layout a page uses is a judgement about that page's content, its
  emphasis, and where it sits in the story — and a page that wants something not
  in the table should get it. *Provenance, from both directions: a shipped deck
  used one layout on 25 consecutive pages and read flat; the release that fixed
  that assigned layouts from this table like a lookup and scored 1 on structural
  expression. A vocabulary is not a design.*

- **Layout answers the empty half; the measure does not.** Body prose stays at a
  comfortable measure (88ch cap, `--measure`). An 1180px column at 14.5px would
  hold ~115 characters against a comfortable 45–75, so widening prose to fill the
  page makes it harder to read, not easier. When a text page looks half empty the
  fix is a second column carrying real content — a stat rail, the figure, the
  caveats — never a longer line.

- **When a page looks empty, the centerpiece is too small or the wrong shape.
  Redraw it.** Do not grow chrome to fill the gap, and do not measure your way out
  of it. The diagnostic that helps is **centerpiece scale** — how much of the
  content area the figure or table actually occupies — together with the
  **figure-to-cell aspect ratio**: a 5:1 diagram in a 1.8:1 cell renders at 40% of
  the available height no matter how it is scaled, and the only fix is a different
  drawing. `scripts/inspect_layout.py` reports both, per page, and gates nothing.

  *Provenance: 1.9.0 turned "the pages look empty" into an 82% fill floor and then
  satisfied it — stretching table rows, and measuring the bounding box of all ink
  so that a small chart with a long caption scored as full. Four diagrams at 4.6
  to 5.4:1 passed while rendering at 40% of their cell. The floor is withdrawn.
  A number that can be satisfied without improving the page is worse than no
  number, because it ends the looking.*

- Generous whitespace is part of the design; content distributes across the full
  page height (never crowds the top half);
- The full-bleed block skeleton (single title + single CTA) is usable, but the
  centerpiece is a chart/diagram/directional gradient — without a professional
  photo library, never set text directly on imagery;
- Navigation preserves traceability (documents are not landing pages): long
  documents keep a table of contents; decks use a narrative rail; **the footer
  carries the source line and the page number as `N / total`.** A bare page
  number tells a reader where they are and not how far they have to go, which is
  the one thing a page number is for.
- scroll-snap is for decks only — never long documents (it breaks table and
  citation reading);
- **Callouts form a three-tier hierarchy, and tier one has a budget** (reader-
  reported twice, from both directions): key conclusions get a tinted box with a
  full 1px border plus a strong left edge; standard guidance keeps the plain left
  rule; weak notes are muted text with no frame. **At most one tier-one callout
  per page, and tier one on no more than a third of a deck's pages.** If two
  things on a page both read as the conclusion, the page has two claims and
  should be two pages. (The first review said one uniform rule for every
  highlight flattens the page; the tiers fixed that and the next deck put 18
  tier-one callouts on 14 of 27 pages, so the reader's note became "not every
  paragraph needs a bold vertical rule". A hierarchy with no budget degrades into
  the flat page it replaced.)
- **Deliverables state results, not process**: edit history, deletion notices,
  strikethrough leftovers, and "this section moved on <date>" asides belong in
  the working ledger, never in a formal deliverable — keep the design rationale,
  drop the revision story.

## 4 · Five chart iron rules + form selection

1. Figure titles state conclusions, not labels; 2. one accent color (natural
green), everything else grayscale, red only for warnings; 3. no gridlines, no
chart borders, no legend for single series; 4. every figure carries a source line
(small light-gray text); 5. a type scale that suits the figure, not a fixed one.

6. **The legend goes where the figure's own layout wants it.** Top right above the
plot is one good answer, not the rule — a vertical bar chart may want it under the
title, a small-multiple grid may want it once at the bottom, and a figure with two
marks may not want a legend at all if the marks are labelled in place. What is
fixed: the legend is quieter than the plot (it is a key, not a finding), it sits
close enough that the eye pairs it with the marks without hunting, and it never
takes a line of its own at the top of a page where it reads as a heading.
*Provenance: "top right, above the plot" was applied to every figure regardless of
shape, at a size that competed with the figure title.*

7. **Figure number and name go below the figure. This does not change.** A reader
looks at the picture and then asks what it is; putting the name above answers a
question they have not formed yet, and putting it beside breaks the pairing when
the column stacks. *Provenance: two split-layout pages moved the caption into the
side column, which detached the number from the figure it numbers.*

7b. **Below the figure: the number, its conclusion name, and the source line.
Nothing else.** Explanation belongs in the page's own column, where it is set at
reading size next to the argument it serves. Under the figure it sits at caption
size, a page away from that argument, and it grows: the two longest ran 72 and
124 words. Worse, it repeats — on both of those pages the "caption" turned out to
be the opposite column restated, two of four sentences word for word on one and
the entire ordered list on the other. A reader sees the duplication before they
can say what is wrong with it, which is why one asked what those blocks were doing
there. The caption aligns with the drawing's left edge rather than centring, so
the eye returns to where the figure began. `inspect_layout.py` reports caption
word count and any sentence that already appears elsewhere on the page.

7c. **Sales and marketing material states its provenance once for the document,
not on every page.** The cover and the closing carry it; the pages carry the
handling terms instead. A source under every figure and again in every footer is
apparatus a customs manager does not need, and it was crowding out the line a
commercial document does need. **This is genre-scoped**: consulting deliverables
and internal analysis keep per-page sourcing, because there the reader is
auditing the claim rather than being sold to. Red line 1 is unchanged — no
invented facts, and every number still traces — the obligation moved to where it
is read once rather than skipped thirty times. *Reader-requested.*

7d. **A page states its source once (any genre).** §4 rule 4 asks every figure for a source
line and the footer contract asks every page for one; on a single-figure page
they are the same sentence twice. The figure's line wins — it is where a reader
is standing when they ask where the number came from, and it was the more
specific of the two on all thirteen pages that carried both. The footer keeps a
source line only when it says something the figure's cannot, and then says only
that. *Provenance: eleven pages cited overlapping sections in both places and two
were identical word for word; a reader asked why the information appears twice.*

7e. **One table per page.** Two grids side by side is two documents on one page:
a grid claims its cells are comparable along the axis its header names, and two
grids with different columns and different row counts share no axis, so their
rows can never line up and a reader sees the misalignment before they can say
what is wrong. If you have two tables, either they are one table, or one of them
is not a table, or they are two pages. *Provenance: a page held a three-step
table beside a three-tier table; a reader called the misalignment a bug and the
design uncreative, and was right on both. It became one drawing — the deck's own
thirty pages as a strip, each coloured by tier — and one numbered sequence.*

8. **A table is for values. Prose poured into a grid is a layout error wearing a
table's clothes.** A grid claims its cells are comparable along the axis its
header names; when the cells hold sentences, the claim is false and the page reads
as a form. Ask what the content actually is and draw that: a sequence is a flow, a
duration is a timeline, a pair of alternatives is a swap, a ranking is a ladder, a
two-by-two is a two-by-two, a set with one distinguished member is an annotated
set. *Provenance: a reader said a 28-page deck used far too many tables for
non-numeric information. Measured, 16 pages carried a table and 14 of them had a
digit density at or below 2% — including a literal 2×2 truth table laid out as
four rows, and three pages whose "table" was a tempting sentence beside a safer
one. `inspect_layout.py` reports the census.* Genuinely tabular things stay
tables: a scoring form is a form.

Flow-diagram shape vocabulary (shapes carry semantics, never decoration):
**parallelogram** = data input/output · **rectangle** = process ·
**diamond** = decision · **stadium/ellipse** = start or terminal ·
dashed outline = not built · one accent-colored arrow marker throughout.
A flow chart drawn entirely in rectangles hides where decisions happen
(reader-requested UML/use-case richness).

**Figure parity across a document.** The shape vocabulary and the level of
construction have to hold across every figure in one deliverable. If one figure
earns decision diamonds, dashed not-built states and directional arrows, the
others are built to that level or they are not figures. (Reader-reported: "page 4's
flow diagram is very good, the others are too simple, the design rules look
inconsistent." Measured, figure 1 carried three shape kinds, six dashed states and
nine arrows while four of the remaining six were rectangles and text with no
arrows at all. One good figure beside five weak ones does not read as one good
figure; it reads as a document that stopped trying.)

**A grid of rectangles containing sentences is a table.** Draw the table. An SVG
that has no arrows, no decisions and no encoding is prose in a box, and it costs
a reader more than the table would.

Form selection: one number is the story → stat callout (big figure + small label,
data voice); composition/trend → segmented bars / tick bands; a bridge between
two numbers → waterfall; concept relations → icon-led flow diagram; time
commitments → milestone timeline; **comparisons always use tables** (columns =
options, rows = dimensions). Illustrative values must be labeled.

## 4b · The commercial footer

**Every page carries its handling terms and where the document is from.** Left of
the footer rule: the confidentiality line, then the organisation's site. Right:
`N / total`. Pages travel alone — a slide is screenshotted out of a deck and
forwarded without the cover — so terms that live only on page one do not travel
with the page.

**This is the one design check that fails the run** (`check_design.py` D12).
Everything else there reports, because a page is done when a human reads it as
intentional and a threshold satisfiable without improving the page ends the
looking. This is different in kind: not a judgement about whether a page is well
made, but a commercial requirement on the artifact, like a contract term. A
design metric that gates is a mistake; a commercial one that does not is a
different mistake.

## 5 · Icons: semantic, never decorative

**The icon library ships with this skill** — `assets/icons/lucide/`, 2007 icons
on a 24×24 grid, `stroke=currentColor` re-stroked to 1.25px, so they follow the
text ladder and switch with the palette for free. Two commands do the work:

```bash
python3 scripts/embed_icons.py --search tariff   # find one
python3 scripts/embed_icons.py radar route code  # sprite of just these
```

**Embed only what the document uses.** A full-library sprite is 0.9 MB of dead
weight in every deliverable, which is how a library becomes a liability.

**Breadth and consistency are two different problems and both need solving.**
Breadth comes from the library: a page about a tariff line, a page about a court
ruling and a page about a comment deadline should not share one icon, and they
will if the set is small. Consistency comes from the **reserved bindings** in
`scripts/embed_icons.py` (`--list`), which pin one icon per recurring LUMI
meaning so the same concept looks the same in every deliverable. Outside those
bindings the choice is free, but **within one document an icon still means
exactly one thing** — an icon reused for a second meaning is worse than no icon,
because the reader learns a vocabulary that then lies to them.

**Where they go**: the section eyebrow on a content page carries the icon that
names that page's subject. **So does every labelled node inside a figure and
every table row-head group** — a named box in a diagram is a sub-heading, and it
carries the same weight of meaning as the eyebrow above it. Minimum **14px
effective size** at the design viewport, which for an SVG node means checking the
rendered size, not the authored one. Never add icons to "look rich". Never draw
one ad hoc either: with 2007 available, "nothing fits" almost always means the
page's subject is not what you thought it was.

*Provenance, two rounds.* This section required "symbol library embedded per
document" from 1.2 to 1.7 while the package shipped nothing, so the 1.7.0 deck
contained zero icons — the same defect 1.7.0 fixed for the display face, one
directory over. **A rule may not mandate an asset the package does not ship.**
1.8.0 then shipped eight hand-drawn icons and the reader said the expressiveness
was still short and the icons did not match the content: eight meanings across
twenty-five pages meant `gauge` did five jobs. **A vocabulary too small to say the
thing is its own defect**, and a house set of eight was the wrong shape of answer.

Field-tested layout guards (each from a real defect):

- A right-anchored label on a full-width bar must be anchored **inside the fill**,
  or its tail lands on the canvas and white text goes invisible — anchor position
  must track fill width.
- **An icon on a text line lives in a flex container** —
  `display:flex;align-items:center;gap` — never a bare inline SVG nudged with
  `vertical-align`: the manual nudge breaks the moment font size, line height,
  or icon size changes (field defect: caption icons floating above their text).
  Size an inline icon at roughly 1.4× the text size it accompanies (11px caption
  → ~16px icon; 20px+ next to 11px text reads as clutter).
- **Icon size is fixed and never inherits container scaling.** Blanket rules like
  `.fig svg{width:100%}` must exclude icons (`.fig svg.ic{width:20px}`) — a
  stretched 24px icon becoming a 110px graphic is an accident, not a design
  choice, even when it accidentally looks bold. If a reviewer has to ask "is this
  the reference style?", it isn't.
- **One title line is the goal; two is the ceiling.** This is a bound, not a
  target: a title that fits on one line at the design viewport should be on one
  line. **Never narrow the title container below the content width to manufacture
  a break** — a title folded in half mid-phrase reads worse than the long line it
  was avoiding, and the reader sees the seam. Display titles are set as a size
  *range*, not a single size, and a long title takes the lower end before any word
  is cut. Order of remedy: (1) drop to the bottom of the title range; (2) tighten
  wording without losing the subject or the fact; (3) split the claim across the
  title and the support line. **Never cut below the information floor.** A third
  title line eats the content area and pushes the footer below the fold. (Two
  lessons here. The original guard read "shorten the title, never shrink the
  type"; once v1.2 made display titles giant, that left cutting words as the only
  legal move and the evidence went first. Then 1.7.0's author read "budget two
  lines" as a target and capped every title at 48ch, so all 24 content titles
  broke near the middle and the reader asked why they were not filling the line.)
- **Figure vocabulary ⊆ body vocabulary**: when body terminology is renamed,
  sweep every figure label in the same pass — a chart that still speaks the old
  names contradicts the text beside it.
- Cards in a row need internal alignment constraints: equalize title heights
  (min-height) and stack stat numbers above their labels, or differing title
  wraps misalign every row below.

## 7 · The verification matrix

A layout is verified only across the **matrix**, not at a point:

- **Language axis**: translated text runs 30–50% longer or shorter — after any
  localization pass, re-inspect every fixed-width container (SVG text in
  fixed-coordinate boxes, stat-band labels, flex rows near their wrap point).
- **Page-height conformance comes first: one page is exactly one page.** Every
  section renders at exactly the geometry's height in both formats — not less and
  never more. A section taller than the page prints across two sheets, scrolls past
  the fold when projected, and is **invisible to every other measurement**, because
  fill, aspect and centerpiece scale are all measured *within* the page. Check it
  before anything else; `inspect_layout.py` reports it per geometry.
  *Provenance: two pages ran 94px and 116px past A4 while every other number on
  them looked healthy. The reader spotted it by eye — they were simply longer than
  their neighbours. The causes were a callout pasted into both cells of a split and
  an orphan one-paragraph cell left behind by a re-lay, neither of which any
  content metric can see.*
- **Page-geometry axis.** Every deliverable serves two output formats, so both are
  matrix points, not options:
  - **16:9 landscape, 1280×720**, checked at 1920×1080 — projection, PDF and PPT
    export. This is the primary geometry.
  - **A4 portrait, 794×1123** — printing and binding.

  **Portrait is a composition, not a reflow.** A two-column split at 794px wide
  gives two 370px gutters, so a page that is a split in landscape usually wants a
  different structure in portrait. Collapsing every horizontal layout at a width
  breakpoint is not a portrait design; it is the landscape design giving up.
- **Viewport axis**: also check a short laptop window (e.g. 1000×550). Slides use
  `min-height:100svh`, so an overflowing page pushes its footer below the fold
  silently. **The footer rule and page number must be visible on every page at
  every matrix point** — provide height-based media queries that step down type
  and spacing.
- Verified at one matrix point is not verified. Screenshot page by page; a
  defect found by the reader is a matrix point you skipped.
- **Geometry axis (SVG).** `check_design.py` reads declared CSS and cannot see
  rendered geometry, so figures need browser checks. Three, in this order,
  because each caught a defect the previous one missed:
  1. **Every drawn element inside its viewBox.** Not just text — a band extended
     to y=212 inside a viewBox 208 tall is clipped and collides with the caption
     below it. Editing a shape without editing the viewBox is the single easiest
     figure defect to ship.
  2. **Every label inside its own shape, at the corners.** Test the text's four
     bbox corners with `isPointInFill`, not the midline: against a sloped edge the
     midline fits while the corners cross, which is exactly how a sentence in a
     diamond passed inspection and read as struck through.
  3. **Re-run both after any type-size change.** Raising the type floor moved
     seven labels out of their boxes at once. §7's language axis already said to
     re-inspect fixed-coordinate SVG boxes after a text change; a size change is
     a text change.
- **Fill axis, reported and never a floor.** `inspect_layout.py` reports each
  page's centerpiece scale against its own cell. Read it to find which layout to
  reconsider; do not set a threshold on it. 2.0.0 withdrew the 82% floor because
  it was satisfiable by stretching table rows while four diagrams rendered at 40%
  of their cell, and it measured the bounding box of all ink, so a small chart
  with a long caption scored as full.
- **Units axis.** Once the page is a scaled stage, a device pixel is no longer
  the unit of the design. Divide every measured distance by the page's scale
  before comparing it to a threshold, or the same layout reports 3px of skew at
  one window size and 4px at another and the check silently tightens as the
  window grows.
- **An adjacent-sibling selector inside a grid is almost always wrong.** `.lead +
  *` means the next sibling in DOM order, which in a grid is **the next column**,
  not the block below. Written unscoped it put a 4px top margin on the first cell
  of every page whose lead spanned the row: six pages with one column sitting 4px
  low, and a reader who saw it as a bug before any probe did.
- **Column axis.** Side-by-side cells start on one line and carry comparable
  weight, or the page reads as two unrelated documents. Measure the outcome, never
  the declaration: `lumi-layouts.css` had said `.body.split > div { justify-content:
  flex-start }` since 1.9.0 and it had **never once applied**, because the fill
  rule above it reaches specificity (0,6,1) — every `:not()` contributes its
  argument — against that selector's (0,2,1). Twelve of fifteen multi-column pages
  centred their columns independently and drifted by up to 132px, which is what a
  reader meant by "the left and right are not level". A rule that loses silently
  is indistinguishable from no rule. The same chain has since won two more
  arguments it should not have, against `.lead.row` and against `.sidebar-notes >
  .notes`; when a declaration and the render disagree, suspect specificity first.
- **Focal axis.** The largest element on the page against body copy, and whether
  a drawing dominates its cell. Report it, never floor it — a page whose figure
  is the entry point should not be made to grow a number.
- **Off-geometry axis.** Render one size the document was **not** designed for —
  a window wider than the design page is the cheap one. Constraints set on a
  single child of the page frame are invisible at 1280×720 and open a dead band
  at 1817px: 2.0.1 shipped `max-width` on `.body` and nothing on `.foot`, so all
  28 pages ran the footer to the window edge past a left-anchored composition,
  and the contact sheet could not see it because it renders only the two design
  geometries. Check that the page frame's parts stay the same width and centre.
- **Ink axis, and it keeps catching the same class of thing.** Ask the drawing,
  never the box: `scrollHeight` on an `overflow:visible` box **does not count
  children that spill out of it**, so a spill probe built on it reported exactly
  zero while two pages ran 26px and 8px past their footer rule. That is the third
  probe in three releases to measure a container instead of its contents. Measure
  the deepest ink against the footer rule.
- **Frame axis.** A page is a fixed box or it is not a page. Landscape is a
  1280x720 stage and A4 is a 794x1123 sheet, each scaled to fit the window with
  `zoom` and letterboxed; the leftover window is a gutter that never holds page
  content. Assert the aspect **at window shapes that are not the design
  geometry** — 1280x960, 1440x900, 1600x1200 — because that is the only place
  the answer can be wrong. *Provenance: `.page` was `min-height:100svh` with no
  aspect lock, so a page was whatever shape the reader's window was: 16:9 at
  1280x720 and 4:3 at 1280x960. The surplus height was the dead band above the
  footer that a reader circled on four pages.* Locking the height moves the
  failure rather than removing it — a fixed box does not grow when its content
  does, it spills — so **measure content against the box** (`scrollHeight`
  against `clientHeight`) as well as the box against the viewport.
- **A probe that establishes the condition it verifies proves nothing.** This
  outranks every other line in this section. The page-height check set the
  viewport to 1280x720 and then measured `section.height - window.innerHeight`
  on a page that was `min-height:100svh`: zero by construction, for every page,
  forever. "All 30 pages are exactly 720px" meant "the page filled the window I
  made 720px tall". Before trusting a probe, write down what a failure would
  look like; if you cannot construct one, the probe is a thermometer in a glass
  of its own water.
- **A probe that has never failed is not a probe.** Before trusting a new check,
  reintroduce the defect it was written for and confirm it fires. Two of the
  three geometry probes above passed clean on a document that was visibly broken,
  and D8 and D9 were both confirmed by running them against the deck that
  prompted them: 10 missing support lines, 0 layouts.

## 6 · Numbers are the copy

- Exact values, never rounded for effect (671 stays 671, not "670+");
- Label + value spec strips (HEIGHT 70 m style), values in the data voice;
- Negative/qualifying information is stated inline in parentheses
  ("(illustrative)", "(proposal value)", "(uncalibrated)") — neither buried in
  footnotes nor dramatized;
- **Copy the form, not the framing**: never pick the most flattering measurement
  condition for a headline number — numbers may serve as copy only when the
  framing survives scrutiny.
