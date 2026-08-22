# LUMI Design Rules

> **Subordinate to the four hard rules in `SKILL.md`, and to
> [`brand.md`](brand.md), which loads before it.** `brand.md` says what to reach
> for; this file says what has gone wrong before. Reach first, then read this.
>
> This file is craft knowledge and defect history: what has gone wrong and what
> fixed it.
> None of it outranks *design per page*, *verify on rendered geometry*, *redraw
> rather than grow chrome*, and *done when a human reads the page as intentional*.
> Read it as a designer reads a body of precedent, not as a checklist to satisfy.
>
> Skeleton researched from the public web design of SpaceX and Tesla (one claim
> per screen / numbers-as-copy / monochrome discipline); the palette and its
> semantics are LUMI's own. Tokens live in `tokens/`; this file covers usage and
> judgment. (Repository language: English only — red line.)

## Contents

- [1 · Color: one color, one meaning; hierarchy via transparency](#1--color-one-color-one-meaning-hierarchy-via-transparency)
  - [1.1 · Region hue: the one place colour encodes identity](#11--region-hue-the-one-place-colour-encodes-identity)
  - [1.2 · The mark and the map](#12--the-mark-and-the-map)
- [2 · Typography: two voices, never mixed](#2--typography-two-voices-never-mixed)
- [3 · Layout: one claim per screen](#3--layout-one-claim-per-screen)
- [4 · Five chart iron rules + form selection](#4--five-chart-iron-rules--form-selection)
- [5 · The commercial footer](#5--the-commercial-footer)
- [6 · Icons: semantic, never decorative](#6--icons-semantic-never-decorative)
- [7 · Numbers are the copy](#7--numbers-are-the-copy)
- [8 · The verification matrix](#8--the-verification-matrix)

## 1 · Color: one color, one meaning; hierarchy via transparency

*Serves: **P-1**.* · id `DR-1`

**The colour values below are the shipped ones, and a deliverable copies them.**
`tokens/lumi-theme.css` is the authority and `scripts/ops/new_deck.py` puts it
in the document for you. A document may set its own SIZES — design per page —
but a colour token that disagrees with the shipped value is a different design
language under the same variable names, and `check_design.py`'s D20 fails it.

**One declared exception: a trademark mark keeps its owner's colours.** A
platform logo on **any page that names third-party products** — a get-started
page, an ecosystem page, a BP's protocol or partner page (scope widened at
0.1.521) — is someone else's identity: recolouring
it into this palette would falsify the mark, and redrawing it in tokens would
fabricate one. Declare it — `data-mark` on the `<svg>` — and D4's literal
scan excises the element; an undeclared logo's hexes still fail, so the
exemption is auditable on the element rather than inferred from its looks.
Marks come from `assets/logos/` with their provenance in its SOURCES.md; a
platform whose official vector is not shipped gets its name set in type,
never a redrawn imitation.
*Provenance: the rule set said where the tokens are and never that the values
were fixed. Found while diagnosing runs that invented palettes — which turned
out to be a harness fault rather than a reading of this rule, so the correction
stands on the asymmetry itself: the display face beside it has always said
"embed rather than improvise".*

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
  | `--acc` | #48633E (6.71) | #7C9F63 (5.61) | built · running · pass · emphasis — as TEXT |
  | `--acc-live` | #3E7A2E (5.21) | #7FC45A (7.97) | the same meaning in FIGURES: strokes, marks, small fills |
  | `--seal` | #C8102E (5.88) | #C8102E for fills; text lifts to `--seal-t` #E97C6E (6.07) | warning · red line · veto · blocked |
  | `--amber` | #9C5D06 (5.27) | #E0A73E (7.83) | partial · in progress · awaiting an input |
  | `--brass` | #7A6C52 (5.13) | #C3B393 (8.17) | reference · archival · out of scope but real |

  (The amber and dark-seal cells drifted from the tokens for six releases —
  0.1.343 moved the values and this table kept the old ones. Where a number
  here disagrees with `tokens/`, the tokens win; the 0.1.442 retrospective
  re-synced the row and added the live green's.)

  *Provenance: the palette was accent-plus-warning only, so "partial" and "not
  built" both rendered as dashed grey and a deck could not say the one thing it
  most needed to say about itself. Amber and brass exist to carry state, not to
  decorate — adding a fifth colour needs a meaning that none of these four covers,
  and a contrast measurement on both canvases.*

  *One recorded extension (0.1.375, at the owner's ask): the footer's handling
  marker — the `shield` icon ahead of the confidentiality line, shipped in
  `tokens/lumi-layouts.css` — renders in `--seal-t`, the seal that stays
  text-safe on both canvases. The handling terms are a
  standing warning to the reader (do not forward), so this is the warning
  meaning applied on every page, not a fifth meaning; the seal still never
  decorates, and on the lime opener the marker inverts with the rest of the
  footer.*
- **Hierarchy comes from a transparency ladder, not new grays** — and since 0.1.338
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

  *Provenance:* until 0.1.337 one alpha list served both canvases and the lower
  steps ran 2.91 / 1.81 / 1.32 / 1.16 on light and 4.08 / 1.99 / 1.36 / 1.16 on
  dark. A shipped deck put its eyebrows, captions, source lines, page numbers and
  table headers on those steps, and the reader's first note was that both canvases
  were exhausting to read. **Pick a text color by contrast, never by how quiet you
  want it to look**; if a thing should be quieter than `--tx4`, make it smaller or
  cut it, do not fade it below legibility.
- **Text on a filled surface is checked separately.** `--on-acc` is
  palette-dependent: cold white on the light accent measures 5.93, and on the
  lifted dark accent 2.65, so the dark palette flips it to canvas ink (6.69).
  Until 0.1.338 one value claimed to serve both and white labels inside accent bars
  shipped unreadable on dark.
- Chart data colors are an independent CVD-validated triple (blue/red/teal) and
  never change with the brand palette — data distinguishability outranks branding.

**A colour is verified against the surface it is printed on, not against the
canvas.** A status chip sits on its own wash and never touches `--bg`; an accent
field is a third surface with its own foreground. 0.1.343's amber measured 4.68
against a canvas it never touches and **4.24 against the wash it actually sits
on**, and the dark seal did the same — both had been "verified" since 0.1.338.
`check_design.py` now discovers painted surfaces by reading the CSS, composites
translucent washes onto the canvas first, and grades a rule that declares its own
background against that background.

**Colour at page scale is a claim; colour as hairlines is decoration.** The part
openers are full accent fields with the claim reversed out, and they are the only
pages in the deck that are. Restraint everywhere is not a voice — a deck in one
register reads as careful rather than as anything. Text on a field takes the
solid `--on-accent`: fading it to 72% for hierarchy drops it to 3.97:1, which is
the 0.1.338 contrast defect returning through a colour choice. Hierarchy on a field
comes from size and letterspacing.

### 1.1 · Region hue: the one place colour encodes identity

*Serves: **P-1**.* · id `DR-2`

**In the globe's region form, hue encodes which region a shape is, and nothing
else.** This is an owner directive and it is the single exception to *one colour
one meaning*. It is safe only because these hues are declared to carry no data
meaning — the standing `light_ramp` already has. Semantic colour is untouched:
`--acc`, `--seal`, `--amber`, `--brass` and the chart triple still mean what
they mean, and a region hue never appears outside a region shape.

The hues are generated, never picked: `scripts/build/build_region_palette.py` spaces
them evenly around the OKLCH circle and assigns them so adjacent regions sit as
far apart as the graph allows. Two regions count as adjacent when they share a
border **or come within 1500 km**, because an ocean strait is not a visual
separation — Europe and North America have no land border and face each other
across 300 km at Greenland.

Four numbers, and each states which way it points:

| | |
|---|---|
| Adjacent regions, CIEDE2000 | **≥ 20 — a floor** |
| Label text on a region fill | **≥ 4.5 : 1 — a floor** |
| Region boundary stroke against the canvas | **≥ 3 : 1 — a floor** |
| Chroma, as a fraction of the per-hue sRGB gamut maximum | **0.65 — the lowest value that clears the first floor** |

The generator asserts the three FLOORS on both canvases and fails naming the
pair it could not separate. The chroma fraction is a generation input, not a
floor: it is the knob the floors are cleared with, and nothing asserts it. A quieter palette is reached by having fewer regions, never
by lowering the floor.

**`tokens/region-palette.css` ships the bindings, not only the values** (since
0.1.391). One include gives a document the `--rg-*` variables, the `.rg-<id>`
fill and stroke rules, the state classes, `.is-hover` and `:focus-visible`, and
the `.gl-*` figure chrome. A document paints a region map by including that file
and nothing else. It took until 0.1.390's contact sheets to see why this
matters: the variables shipped for three releases with no rule joining them to
the classes the generator emits, so the reference fixture's own region figure
rendered four solid black rectangles while every metric passed — no check in
this package reads rendered colour, and a palette nobody can apply is not a
palette.

**Every coloured region carries a label or a legend entry.** Unconditionally,
whatever the hue count. At the theoretical maximum separation of 90 degrees,
deuteranopia collapses two adjacent regions to ΔE00 9.6 and protanopia to 8.5,
and a real map runs at 60 or less. Hue separates neighbours at a glance; text
carries identity. `check_design.py` D18 checks for the text and never counts hues.

### 1.2 · The mark and the map

*Serves: **P-1**.* · id `DR-3`

Two geographies ship, and they disagree about where a coastline is.

* `assets/vectors/globe-orthographic.svg` and `world-flat.svg` are a **mark** —
  a two-degree stylisation with no islands under about 500 km, for a cover.
* `assets/vectors/world-110m.json` is a **map** — Natural Earth 110m, 177
  countries, the geometry the globe component draws.

**A document may use either and must never place both in one view.** Re-deriving
the coarse set from 110m would change the shipped cover mark byte for byte, so it
has not been done; until it is, this rule is what keeps the disagreement out of
the reader's eye.


#### The figure grammar for the globe and the region map

*Moved here at 0.1.482 from comments inside `tokens/region-palette.css`. A token
file is read by the build, not by a person forming a judgement, so design prose
there is invisible to every reader of `references/` and to the `principle trace`
guard. The values stay in the token file; the reasoning is here.*

**The plate and the light.** The plate, with the shadow that lifts the globe off
the page. A flat filled disc reads as a circle printed on the paper; a shadow
under it reads as a sphere in front of it, and it costs one declaration against
a lighting model. Scoped to the plate so the marks and the land are not smeared
by it. Night is a lighting condition laid over the geography, so it is a wash
rather than a fill and it takes no pointer events — a reader aiming at a mark in
the dark must still hit the mark.

**A line you can name is not scaffolding.** The equator and the tropics are
NAMED lines, not graticule: a reader can point at them, so they are gold, drawn
well above the grid, and the tropics are dashed to say they are a pair. At 3 and
2 they read as heavier graticule; the weight is what separates a line you can
name from a line that is scaffolding.

**The land, in three weights.** Every land line used to be one weight, so a
coastline and a provincial border looked alike and the eye had nothing to group
by. A reader asked to compare where one bloc sits against another needs the
continents to read as shapes first, and that is what a hierarchy of line is for.
The FILLS carry no stroke at all now; all linework is here.

- **A coast** is a continent's edge, and it is the heaviest line on the figure
  after the data. This is also what puts Oceania back: an island coast is a
  coast whether or not the island is in a bloc, and 0.1.405's outline-only rule
  had left Papua New Guinea, Fiji, the Solomons and Vanuatu as 1.2px hairlines.
- **Where one trade bloc meets another.** Heavier than a border inside a bloc
  and lighter than a coast, which is the order of the question a reader is
  asking.
- **A border between two countries in the SAME bloc.** Present, because the
  countries are real; faint, because the figure is not about them.

**A bloc on the globe is quieter than the same bloc on a map.** The flat map is
a choropleth and the fill IS the subject; the globe is a field of marks and the
fill is where they sit. At full strength the eight hues buried the marks —
Australia read hotter than the datum on top of it — so the globe takes the same
hue at reduced strength and keeps one palette across both figures rather than
minting a second set of colours that would have to be kept in step.

**A bloc's FULL membership, outlined when a reader selects it.** No fill: the countries
underneath keep their own bloc's colour, which is the point — the outline says
'these too' without claiming they stopped belonging where they were.

**Labels, and what a label on a sphere cannot rely on.** The globe's own layers.
A city is a NAME on the sphere and a bloc label is an identifier over a fill, so
both are set in the utility face at a weight that survives being drawn over land
— and both carry a halo, because a label on a globe has no white box to sit in
the way a map label does. paint-order puts the stroke behind the glyph so the
halo never eats the letterform.

Region labels, set in the ink the contrast floor is computed against:
`selftest()` asserts every fill carries INK_LIGHT / INK_DARK at 4.5:1 or better,
and `--nw` is those two values. A label in any other colour is outside the
floor's guarantee.

The two tspans a label can carry. Both have existed as CLASSES since labels
shipped and neither had a rule, so a value and a membership count set
identically to the bloc name beside them — the same class-with-no-rendering
defect the 0.1.396 audit found on the globe's hover state, one file away. The
people count recedes: the reader is identifying a bloc, and the magnitude is
context for the identification rather than the point of it. Same relationship
`.rg-label-v` has to `.rg-label`.

**Size is set by the emitter, not by CSS.** No font-size here: the emitter sets
it as an attribute scaled to the frame's R, because a fixed pixel size inside a
2R-unit viewBox renders at whatever the layout divides it to — 13px became ~7 at
a typical figure width. CSS would override the attribute, so CSS stays silent
about size.

**A signal is one code in transit**: the dot is where, the text is what. The halo
is the same one city names carry — a label on a sphere has no white box to sit
in.

**Interaction has to be visible or it does not exist.** Hover and keyboard
focus. The runtime has toggled is-hover since the globe shipped and no
stylesheet anywhere defined it, so hovering worked and showed nothing; and the
first delivered demo set outline:none on a tabindex='0' element with no
:focus-visible to replace it. Both affordances ship here so no document
re-decides them. Not inside any media query, per the media-only-rules guard.

The globe's points need their own hover rule. 0.1.393 shipped the region one and
the globe kept toggling is-hover on marks and nodes against no CSS at all — the
same defect, moved rather than closed. A mark grows; a node takes the accent so
it reads as selected.

The drag affordance. The arcball has worked since the globe shipped and nothing
ever said so: no cursor, no chrome, no hint. A figure that can be turned should
look like it.

## 2 · Typography: two voices, never mixed

*Serves: **P-1**.* · id `DR-4`

- **Primary face — D-DIN takes over** (v1.2): D-DIN is the single Latin face
  for titles, body, and data alike, with CJK fallback (PingFang SC / Noto Sans
  SC). Display titles are ALL-CAPS at **weight 700** with tight leading
  (0.92) — `--w-display` and `--lh-display` in `tokens/` are the authority.
  (This sentence said weight 400 while the tokens shipped 700 for over a
  hundred releases — the drift the tokens-win rule exists for.) Rounded faces (Quicksand/Nunito) are retired
  from decks. **The face ships with this skill** — `assets/fonts/D-DIN.woff2`
  and `D-DIN-Bold.woff2` (SIL OFL, `COPYING.txt` alongside). Embed it as a data
  URI, never link it: `python3 scripts/build/embed_font.py` prints the ready
  `@font-face` block, and `--check` verifies the vendored files are intact.
  A linked font falls back the moment a deliverable is opened offline, emailed,
  or printed elsewhere; a declared-but-unvendored one renders nothing at all,
  which is what shipped in 1.2.
- **The embed rule is scoped to the Latin faces, and Chinese uses the default
  stack** (owner decision, 2026-08-10). No CJK face is vendored and none will
  be: a Chinese face of comparable quality is one to two orders of magnitude
  larger than the Latin pair, and embedding one in every deliverable is a cost
  the owner has declined. Chinese deliverables therefore render through the
  fallback the default stack already names — PingFang SC, Hiragino Sans GB,
  Noto Sans SC — which means **CJK glyph rendering depends on the reader's
  machine**. State it rather than hide it: on macOS and iOS that is PingFang,
  on most Linux and Android it is Noto Sans SC, and on a machine with none of
  the three the system serif takes over. This is the honest answer the
  maintenance rules require — the alternative was a rule ("embed the face,
  never link it") that could not be kept for half the documents this package
  exists to produce.
- **Small type is a contrast problem before it is a size problem.** A reader
  reported both canvases exhausting to read when 9.5px labels sat on ladder steps
  measuring 1.81:1; raising the contrast fixed most of it. **There is no universal
  size floor** — 0.1.338 set one at 11px without being asked, and a floor applied to
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

*Serves: **GOAL**.* · id `DR-5`

- **The eyebrow names the part and the page's subject, and it opens with the
  subject's icon.** On every content page the guide line reads `<icon> PART
  <letter> · <what this page is about>` — the icon is §5's subject icon in the
  flex slot `tokens/` ships, the part letter matches the opener the page sits
  under, and the label is that page's own phrase, not a repeated section name.
  Uniformity here is deliberate and exempt from the parallel-structure caution:
  the eyebrow is apparatus, like the page number — a reader orients by its
  sameness. Titles stay governed by the title contract and M11; the eyebrow is
  not a title and the checkers do not count it as one. (Owner directive
  2026-08-09, from the reference deck, where the pattern held on all 26 content
  pages.)
- Each screen/page carries exactly one claim: a conclusion-style headline (an
  accent word in green is available, not required — mechanical emphasis on every
  headline is inflation), **one to three sentences of support whose lengths
  visibly differ — on every content page without exception, figure pages
  included** (D8), one centerpiece, a thin footer rule with source + page number
  — nothing else. *Provenance: this rule has stood since 0.1.336 and 10 of 25 pages
  shipped without a support line — all six figure pages plus four table pages —
  because a figure felt like it spoke for itself. It does not: the reader arrives
  at a diagram with nothing telling them what they are about to look at.* (The rule read "one sentence of support" until 0.1.336, which
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
  that page — **there is no size floor and no requirement that it be type.** Which way round the
  number and its gloss go is fixed, and §7 fixes it: the number first. The
  apparatus already ships — `.lead` with `.lead .v` and its `.g` gloss for a page
  that turns on one number, `.stats`/`.stat` for three or four read across a row
  — and until 0.1.521 no shipped deliverable used `.lead` even once, which is how
  a page's biggest number ends up inside a twenty-word title instead.
  `.lead` and the `--fs-lead / --fs-lead-xl / --fs-say` tier are in
  `tokens/`; `inspect_layout.py` reports the ratio of the largest element to
  body copy and names the pages that have neither. *Provenance: a reader called
  a 28-page deck flat and mediocre, and the measurement agreed exactly — 24 of
  28 pages had nothing on them larger than 15px body copy, and only the cover
  and two stat-band pages carried any display tier at all. A page with no entry
  point gets read top-left like a document instead of looked at. The fix is per
  page: half of those pages got a number, the rest got a redrawn figure.*
- **A part opener earns its page.** The part label, one claim at display scale
  saying where the reader is, and one run line saying what the next pages argue —
  the `.openpart` / `.openclaim` / `.openrun` set on the lime field — and then
  no chart, no map, no navigation rail, and no icon carrying a second message.
  **One oversized subject mark is permitted**: a single silhouette carrying no text
  of its own, reversed out of the field, which restates the part's claim in another
  modality rather than adding a second thing to the page (0.1.521, owner directive).
  It is the part's subject or it is not there. A navigation rail cannot do this at a glance,
  and the quiet page is what makes the dense ones read as dense on purpose.
- **A page has a layout, chosen for its content.** Sixteen ship in
  `tokens/lumi-layouts.css` as `.body.<name>`; pick with the table below. This is
  the same discipline as §4's chart form-selection: the point is not that many
  layouts exist, it is that the content decides which one.

  | The content is | Layout |
  |---|---|
  | one number, and it is the story | `hero-band` |
  | a cover or a closing page | `cover-grid` |
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
  | a part divider or section opener | `full-bleed` (the lime field) or `rail` |
  | a table of 6 or more columns | `stack`, no exceptions |

  **Every layout has one row that absorbs the page's leftover height, and the
  content that belongs in it is the centerpiece.** In `stack`, `band-hero`,
  `split` and its variants that row is the last one, which is why a lede-then-
  figure page composes on either geometry. In `hero-band` it is the **middle**
  row — that is the layout's whole point, "one number, and it is the story" —
  and in `thirds-v` the slack divides evenly across three. Pick by asking which
  block should grow: put a thin evidence strip in a flexible row and the sheet's
  entire leftover height opens up between it and whatever sits beneath.
  *Provenance: a figure-led page on the A4 sheet was built on `hero-band` with
  the stat band in the flexible row. Nothing was broken and every rule was
  followed; the drawing simply sat in a rigid row with a hand's width of nothing
  above it, and a reader read the gap as a spacing bug.*

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
  drawing. `scripts/check/inspect_layout.py` reports both, per page, and gates nothing.

  **A figure is drawn for the geometry it will sit in.** The cell decides: a
  full-width cell is about **2.5:1 on the 16:9 stage and about 0.85:1 on the A4
  sheet**, and a two-column cell is about 1.3:1 and 1.0:1. A 1.5:1 drawing in a
  0.85:1 cell fills a little over half its height however it is scaled, and no
  CSS fixes that. *Measured on the first handbook actually designed for the
  sheet: its figures were drawn at 1.4:1 to 2.2:1, and its content pages ran a
  24 to 39 percent empty band against 5 to 27 percent on a landscape deck built
  the same week. Portrait figures stack what landscape figures place side by
  side; that is the redraw, not a scale factor.*

  *Provenance, the 16:9 side (owner investigation, 0.1.442 review item 8 —
  the owner suspected the proportions without evidence, and the measurement
  agreed): across two shipped landscape decks, one 30-page deck carried a
  2.7:1 figure in a 1.28:1 cell (ratio 2.1) and a 3.8:1 figure in a 1.59:1
  cell (ratio 2.4) — each rendering at under half its cell — and a 15-page
  deck ran three of five figures past 1.2× their cell. The same sweep found
  the display tier nearly unused: across 45 landscape pages, zero uses of
  `--fs-lead-xl` and the 54px SVG numeral, and the largest number on most
  pages was a 43px band value. The targets above bind at authoring time;
  the probe stays reported-not-gated (eval-rubric: a number satisfiable
  without improving the page ends the looking), so drawing to the cell is
  the author's discipline, checked by the eye on the contact sheet.*

  *Provenance: 0.1.339 turned "the pages look empty" into an 82% fill floor and then
  satisfied it — stretching table rows, and measuring the bounding box of all ink
  so that a small chart with a long caption scored as full. Four diagrams at 4.6
  to 5.4:1 passed while rendering at 40% of their cell. The floor is withdrawn.
  A number that can be satisfied without improving the page is worse than no
  number, because it ends the looking.*

- **A drawing outargues a paragraph, and its share of the page is watched**
  (owner directive 2026-08-09). Every content page carries at least one visual
  block — a drawn figure, a stat band, a display lead, or one of the comparison
  patterns — and the **target** share of the content area given to visual blocks
  follows the genre (owner directive, 0.1.380): **about half for sales,
  marketing and consulting**, where the page argues visually, and **about a
  third for training**, where a learner needs the words beside the drawing. The
  document declares its genre (`<body data-genre="training">`) and the checks
  grade against that number. **A storyline may raise its genre's target, and one
  does**: a `pitch-deck` page is looked at while a founder talks, so it carries
  about **80%** (0.1.521, owner directive; Template 11 states the register, and
  `inspect_layout.py`'s two tables are the authority). Where both speak the
  storyline wins, being the more specific claim about the document. Raising the
  number is a floor on the drawing and therefore a **ceiling on the prose**, and
  a 50/50 `split` page measures about 43% once the lede and the takeaway are
  counted — so choosing the layout is part of meeting it.

- **A page on the sheet carries more than a page on the slide** (owner directive,
  2026-08-09). A slide is narrated and an A4 page is read alone, so a portrait
  content page carries a **second content block beside its centerpiece** — what
  to notice in the figure, the steps, the caution, the worked example — and **at
  least one marked key point**. Marked means the *standard* tier, the aside with
  the plain left rule; it does **not** raise the tier-one budget three bullets up,
  which stays at one per page and a third of the document. A page whose every
  emphasis is tier one has no emphasis. That is a **floor on the page's blocks**, and
  deliberately not on the support line: §3's one to three sentences under the
  title is unchanged, because the fix for a thin page is another block, never a
  longer paragraph in the reserve. The sheet is a fixed box and type is never
  nudged to make room, so the escape when both will not fit is the only one there
  has ever been — **the page becomes two pages**. *Provenance: the first handbook
  designed for the sheet gave nine of twenty-one content pages a second block and
  left the other twelve running a 24 to 33 percent empty band under the figure.
  Its reader asked why the printed page said less than the projected one. Every
  layout rule had been applied; none of them was about how much a page says.*
  `inspect_layout.py` reports portrait content pages carrying a centerpiece and
  nothing else.

- **An apparatus page is exempt, and it says so** (owner decision, 0.1.381).
  Some pages are reference the reader returns to rather than a claim the deck
  advances: the glossary, the scoring or feedback page, the boundaries page of
  what will not be claimed, the how-to-use-this-deck page, a contents index.
  Asking those to carry a figure produces decoration, which is the thing every
  rule in this file exists to prevent. They carry `data-role="apparatus"` on the
  section and drop out of the share target and out of D16's prose-only list.

  **Declared, never inferred.** A page is apparatus because the author says so
  in the markup, not because a checker guessed from its contents — an inferred
  exemption is the escape hatch that empties the metric, and a declared one is
  auditable. The test is the claim: **a content page advances a claim and needs
  its visual block; an apparatus page carries no claim, only reference.** A page
  that simply failed to earn a figure is not apparatus, and calling it that is
  the move this paragraph exists to make visible.

  **A ceiling, not a target: about one content page in five.** Past that the
  deck has stopped arguing and become a handbook. `check_design.py` reports the
  count and the share, `inspect_layout.py` names the pages that claimed it, and
  neither gates — a reviewer reads the list and decides whether each page earned
  the word. `check_design.py` D16 reports the pages that carry none, and
  `inspect_layout.py` reports each page's rendered share against the target;
  both are review triggers, never floors, because the withdrawn 82% fill floor
  is the standing record of what a floor here does. The reconciliation with §4
  stands in both directions: a comparison may take a table or a labelled figure
  (§4), a table is still for values and never for what a chart says better, and
  a table page still wants its visual weight from a figure or a band beside it. Vary the figure form page
  to page as §4's form selection directs — from the content, never for variety's
  own sake.

- Generous whitespace is part of the design; content distributes across the full
  page height (never crowds the top half);
- The full-bleed block skeleton (single title + single CTA) is usable. The
  centerpiece is a chart, a diagram, a composed shape or — since 0.1.493 — a
  **sourced photograph treated to §9's rules**. The old clause read "without a
  professional photo library, never set text directly on imagery", which was a
  condition and was read as a ban; §9 is the condition being met;
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
- **On portrait, the split family is ONE composition, and variety comes from
  the vertical and composite families.** `tokens/` deliberately collapses
  `split`, `split-wide`, `split-narrow` and `sidebar-notes` to a single grid on
  the sheet, so choosing among them changes nothing a reader sees — D9 counts
  them as one there. Distinct portrait composition lives in `stack`,
  `hero-band`, `band-hero`, `columns-2`, `quad`, `thirds-v`, `rail` and
  `diagonal-flow`, chosen from the content: a strip of measured numbers over a
  dominant block is `band-hero`; a dominant figure anchored by a thin strip is
  `hero-band`; four parallel items are `quad`; an ordered sequence that steps
  is `diagonal-flow`. Two cautions, both watched on rendered pages rather than
  guessed: **content volume is part of "choose from the content"** — a thin
  list under a 1fr hero row opens a dead band, and the fix is a second content
  block from the page's own facts, never a stretched one; and **portrait
  `columns-2` centers each cell independently**, so it suits near-equal columns
  and misaligns unequal ones. (Two real rebuilds, 64 pages: every conversion
  was verified on its rendered PNG, and three that read well in markup were
  reverted after looking.)

## 4 · Five chart iron rules + form selection

*Serves: **P-4** + **P-1** + **P-2**.* · id `DR-6` — one family, three parents: the form-selection rules serve P-4, the single accent colour P-1, the source line P-2. (A split into three sections was promised for "P0.5's rule ids" and never made; DR-15 then established the multi-parent form, and this follows it rather than carrying a promise a shipped release could no longer keep.)

1. Figure titles state conclusions, not labels; 2. one accent color — the
figure green `--acc-live`, which is what the `f-acc`/`s-acc` paint classes
resolve to — everything else grayscale, red only for warnings; 3. no gridlines, no
chart borders, no legend for single series; 4. every figure carries a source line
(small light-gray text) **in consulting and internal material — see rule 9, which
scopes this: a sales or marketing figure carries none, because the document states
its provenance once**; 5. a type scale that suits the figure, not a fixed one.

**A figure that puts numbers on a scale draws the scale's baseline and names its
unit.** Rule 3 above bans gridlines and chart borders, and this is not a
retraction of it: a gridline is background a reader is asked to ignore, while a
baseline is the datum the marks are measured from and the unit is what makes the
numbers mean anything. A bar chart with no line at its foot is a row of
rectangles, and "42" beside one of them is a number with no dimension. Draw one
line, on the axis the values run along, in the non-text ladder; put the unit in
the axis label or in the value itself.

**A figure that puts numbers on a scale NAMES its axes**, with the shipped
classes, and `figure_axis_named` gates it. Without the name a reader is handed a
quantity and no dimension — and the two placement gates below have nothing to
grade, so a document could walk past both by declining to say which text is an
axis name. *Owner ruling 2026-08-22, taken knowing the cost: every document
built before the classes shipped fails this until it is rebuilt, the accepted
reference among them (10 of its 10 scaled figures). See GAP-027.*

**An axis NAME sits outside the plot, and the vertical one reads upward.** The
horizontal axis's name goes below its line, level. The vertical axis's name goes
to the LEFT of its line, set upright reading bottom to top — `tokens/` ships
`.axname-x` and `.axname-y` for exactly this, and the y rule pairs
`writing-mode: vertical-rl` with `rotate: 180deg` because the bare property
reads downward. **Neither may overlap the plot area**, which is the region the
marks occupy: a name lying across the data is indistinguishable from a label
belonging to it, and a reader has to work out which.

The names are a ROLE, and the role has to be declared. A checker measuring
geometry cannot tell an axis name from a data label printed on its own mark —
both are text inside a drawing, and only one of them is a defect. `figure_axis`
gates a figure that declares the classes; a figure that scales numbers and names
no axis is reported, because "the author did not say" is a different finding
from "the author said and got it wrong".

`inspect_layout.py` reports `figure_axes` and does not gate on it. Measured
2026-08-22 on the documents on record: the accepted reference draws no baseline
on two of its nine scaled figures and an accepted intro deck on one of its four,
while three other documents carry no figure that scales numbers at all. **The
accepted document fails this, which is why it reports** — a rule the reference
breaks is either a rule the reference should have followed or a bar nobody has
earned the right to set, and one document cannot tell those apart (CLAUDE.md
convention 6; 0.1.339's withdrawn fill floor is the standing lesson).

6. **The legend goes where the figure's own layout wants it.** Top right above the
plot is one good answer, not the rule — a vertical bar chart may want it under the
title, a small-multiple grid may want it once at the bottom, and a figure with two
marks may not want a legend at all if the marks are labelled in place. What is
fixed: the legend is quieter than the plot (it is a key, not a finding), it sits
close enough that the eye pairs it with the marks without hunting, and it never
takes a line of its own at the top of a page where it reads as a heading.
*Provenance: "top right, above the plot" was applied to every figure regardless of
shape, at a size that competed with the figure title.*

7. **Figure number and name go below the figure. This does not change.** **The
name holds one line at the document's geometry** — a wrapped caption stops
reading as a label and starts reading as prose under the drawing. That is a
**ceiling on the name, not a target**, and it is set by the CELL the figure
sits in rather than by the page: about 100 characters for a full-width figure
on the 16:9 stage, about 60 in a two-column split or on the A4 sheet. A name
that overruns gets shortened, never set smaller. `inspect_layout.py` counts wrapped captions. A reader
looks at the picture and then asks what it is; putting the name above answers a
question they have not formed yet, and putting it beside breaks the pairing when
the column stacks. *Provenance: two split-layout pages moved the caption into the
side column, which detached the number from the figure it numbers.*

8. **Below the figure: the number and its conclusion name. Nothing else — the
source line goes INSIDE the drawing** (rule 17). The two halves of this bullet
contradicted each other for several releases: this one said the caption carries
the source, rule 17 said the source is the SVG's last text node and "stays clear
of the caption block". Rule 17 wins, by owner ruling 2026-08-22, and the reason
is measurable. Run together in one inline flow the two read as one sentence —
three conformance decks shipped `…off the green lineIllustrative programme-board
values`, with no separator at all — and worse, the line break lands inside the
source, so the NAME never appears to wrap and the one-line ceiling above cannot
be measured. Nine of ten captions on one deck rendered two lines while the
checker reported every name holding one. Moving the source into the drawing
leaves the name alone under the figure, where the ceiling is a real measurement
and the source travels with the picture it describes.

Everything below still applies to what remains:** Explanation belongs in the page's own column, where it is set at
reading size next to the argument it serves. Under the figure it sits at caption
size, a page away from that argument, and it grows: the two longest ran 72 and
124 words. Worse, it repeats — on both of those pages the "caption" turned out to
be the opposite column restated, two of four sentences word for word on one and
the entire ordered list on the other. A reader sees the duplication before they
can say what is wrong with it, which is why one asked what those blocks were doing
there. `inspect_layout.py` reports caption word count and any sentence that
already appears elsewhere on the page.

**The caption block centres on its figure** — the number, the name and the
source line together, in both geometries. *Provenance: this rule said the
opposite for eleven releases ("the caption aligns with the drawing's left edge,
so the eye returns to where the figure began"), nothing measured it, and the
shipped CSS had never implemented it. The caption aligned with the CELL's left
edge, which is the drawing's edge only while the figure's box is unclamped; the
moment a height ceiling bites, the drawing is pillarboxed to the middle of its
box and the caption stays behind at the margin. A reader saw the gap and asked
for centring, which is also the alignment that survives the clamp.* One boundary
comes with it, because CSS centres the figure's **box**: a drawing whose ink sits
off-centre inside its own viewBox cannot be aligned by any rule here and gets
redrawn. `inspect_layout.py` reports the offset between the rendered caption's
centre and the figure's ink.

9. **Sales and marketing material states its provenance once for the document,
not on every page.** The cover and the closing carry it; the pages carry the
handling terms instead. A source under every figure and again in every footer is
apparatus a customs manager does not need, and it was crowding out the line a
commercial document does need. **This is genre-scoped**: consulting deliverables
and internal analysis keep per-page sourcing, because there the reader is
auditing the claim rather than being sold to. Red line 1 is unchanged — no
invented facts, and every number still traces — the obligation moved to where it
is read once rather than skipped thirty times. *Reader-requested.*

  **This governs the FIGURE too, from 0.1.521.** Rule 9 removed the per-page and
  per-footer line and left rule 4 demanding one under every drawing with no genre
  qualifier, so the section contradicted itself for releases: a sales deck was
  told both to state provenance once and to repeat it fourteen times. In sales and
  marketing material the figure carries no source line, rule 8's caption drops to
  the number and the name, rule 10's tie-break has nothing to break, and rule 17's
  in-SVG line does not apply. *Owner review, 0.1.521: "in a BP this does not need
  to be shown."*

  **One trap comes with it, and it is invisible.** M2's window is the PAGE, not
  the figure, and its marker vocabulary includes bare `per` and `as of`; SVG text
  is stripped before it measures, so a line drawn inside a figure never counted
  toward it anyway. A deck that removes every source line looks fine while it has
  fewer than four percent-or-currency figures in HTML prose, and collapses the day
  it has more. **So the page keeps a source marker somewhere in its own text** —
  the eyebrow, a stat gloss, the takeaway — even when no figure carries a line.

  **The accepted provenance words are the checker's `D6_PROVENANCE`** —
  source · derives/derived from · based on · provenance · traces (back) to ·
  drawn from · comes from — the same discipline as the M2/M6 marker list:
  the list is the contract, and a colophon that gestures with a word off the
  list ("cited to") reads as missing on every page at once, which is how a
  fifteen-page deck failed D6 fifteen times in its first build.

10. **A page states its source once (any genre).** §4 rule 4 asks every figure for a source
line and the footer contract asks every page for one; on a single-figure page
they are the same sentence twice. The figure's line wins — it is where a reader
is standing when they ask where the number came from, and it was the more
specific of the two on all thirteen pages that carried both. The footer keeps a
source line only when it says something the figure's cannot, and then says only
that. *Provenance: eleven pages cited overlapping sections in both places and two
were identical word for word; a reader asked why the information appears twice.*

11. **One table per page.** Two grids side by side is two documents on one page:
a grid claims its cells are comparable along the axis its header names, and two
grids with different columns and different row counts share no axis, so their
rows can never line up and a reader sees the misalignment before they can say
what is wrong. If you have two tables, either they are one table, or one of them
is not a table, or they are two pages. *Provenance: a page held a three-step
table beside a three-tier table; a reader called the misalignment a bug and the
design uncreative, and was right on both. It became one drawing — the deck's own
thirty pages as a strip, each coloured by tier — and one numbered sequence.*

12. **A table is for values. Prose poured into a grid is a layout error wearing a
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

13. **A table's row height comes from its content, never from the space left
over.** A table does not grow into its cell the way a figure does, and a cell
holding one is expected to have slack; the slack splits above and below the grid
and is a page asking to be given something else to say — a second block, a
callout, a figure — never taller rows. *Provenance: a centerpiece table was
handed its cell's height and spread it across its own rows, capped only below
four rows by a threshold no retrospective had argued. A reader called the
stretched rows a bug, and the record already agreed: stretching table rows is
this package's own example of satisfying a measurement without improving a page,
and is why 0.1.340 withdrew the 82% fill floor. It survived four releases as a
mechanism after being named as a defect.*

14. **A mark that encodes a quantity declares it, and the drawing obeys it.**
Put the number on the mark — `data-datum="80"` on the bar, the segment, the dot —
and the length follows it in proportion. This is the only way a check can tell a
bar chart from a picture of one: 48 pixels means nothing to a script until the
markup says what it is 48 pixels *of*. `inspect_layout.py --deliverable` fails a
mark drawn out of proportion to its own declared value, which makes it one of the
few figure findings that is decidable rather than aesthetic.
*Provenance: a shipped deck floored every bar at 48px so short bars would not
vanish. It drew 1 and 4 as the same bar — a 7.4× overstatement — and on the page
whose caption read "Europe stays hollow at four" it drew that 4 at twice its
length. Nothing could see it: the figure passed every design metric, and its own
build script had written the true values into the markup one attribute away from
the width it then ignored. The fix for a short bar is a shorter axis or a
different form, never a floor under the ink.*
**A bar on a full-width track states a share.** If the track is not the whole of
something, it is a second, wrong scale sitting under the first — the same deck
laid every bar on a full-width rule, so its largest value read as 100% of a total
it was 55% of.


15. **A figure's viewBox width is chosen to match the CELL it renders in, so one
user unit is about one pixel.** That is what makes `font-size: 17` inside a
drawing mean 17px on the page, and it is the constant that lets a figure in a
full-width cell and one in a 62% cell belong to the same document: line weights,
label sizes and stroke dashes all land at the same rendered scale. Roughly 660 in
a `split-wide` right cell, 1100 in `stack`, 1280 full-bleed; §4.1's per-cell
aspect ratios then decide each height.
*Provenance: this rule said "a document's figures share one viewBox width" for
exactly one release. Its own evidence was miscounted — the deck it cited runs
640, 660 and 680, rendering between 0.70 and 1.53 px per unit — and applied to a
deck with varied layouts it does the opposite of what it promises: the same 660
units render at 1.0 px/unit in a 652px cell and 1.66 in a 1096px one, so one
declared size becomes two rendered sizes. The number was never the constant; the
ratio is.*

15a. **A repeating block's row NAME carries title weight.** The graded ladder,
the vow block, the launch sequence: each is a list of named things with a note
under each name, and the name is a heading. `.gr .gn` declared no weight at all
until 0.1.551 and computed to 400 — the same weight as its own note and as the
body around it, separated by one pixel of size and a step of colour. An owner
review read a four-row ladder and could not tell the names from the notes.
`tokens/` ships the weight and `inspect_layout`'s `role_weight` gates the
rendering, because a weight arrives through the cascade and only the browser
knows which rule won.

15b. **The in-figure type ladder, since "a scale that suits the figure" was the
only guidance and produced fourteen flat drawings.** A figure's **row and section
names set at title weight** — `svg .row-lbl`, 17px bold ink — because a chart's
row names are read before its bars (EX-2 item 5). Its **values** take `.mid`
(30px) or `.huge` (54px) where the number is the argument. Its **fine print** —
axis ends, basis lines, scope flags — stays at `.lbl` / `.sm`. A drawing whose
largest text is 13px is a diagram with captions; an exhibit has a heading you
read from across the room.

16. **A figure that compares two states names them inside the drawing**, as a
label pair on the top line: the left in `--tx1`, the right in `--acc`. "the
bill, item by item" against "after the standard"; "what you put in" against
"what you get out". The pair does the work a legend would and costs no
apparatus, and putting the accent on the right-hand label is what tells a
reader which side is the finding.

17. **The figure's source or caveat line is the last text node inside the SVG,
at the foot of its viewBox** — 11 to 11.5px in `--tx2` or `--tx3` — not an HTML
sibling beside it. It travels with the drawing when the drawing is resized,
scaled or exported, which a sibling does not, and it stays clear of the caption
block §4 rule 8 keeps to the number, the name and nothing else.

18. **A number label inside a filled mark is reversed out of the mark**, in
`--on-acc` or `--on-lime` at 20-22px, with its descriptor stacked immediately
beneath at 11.5-12px in the same ink. This is §7's number-first order at figure
scale, and it is the one place this package already applied it consistently
before the rule was written down.

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
commitments → milestone timeline; **a comparison may be a table or a figure, and the
condition is the same either way: the reader must be able to read the values
off it.** A table was the rule here through 0.1.494 for a good reason — it is
precise and it cannot distort — and the reason survives rather than the rule.
A figure qualifies when it carries the values a table would have carried:
labelled on the marks, not implied by their size. A comparison drawn as
unlabelled geometry is decoration wearing a table's job, and it is worse than
the table it replaced. Columns = options, rows = dimensions is still the right
default when the values are the point and there are more than a handful.
Illustrative values must be labeled.

### 4.0 · From question to framework to shape

*Serves: **GOAL**.* · id `DR-16`

Form selection (§4) starts one step earlier than a chart: **what analytical
question is this page answering?** `assets/frameworks.json` is the
dictionary — each entry names the question, the analytical move behind it
(analysis-rules.md AR-1), the slots to fill, the misuse that turns it into
decoration, and the library shapes that draw it. The chain is **question →
framework → shape**; §4.1's relation rule then holds the chosen shape to
the data exactly as before. Choosing the framework because it looks
professional is the failure the misuse lines name: a SWOT of restated facts
and a 2x2 hugging its diagonal are decoration wearing an analysis's
clothes.

### 4.1 · Choosing a figure from the shape library

*Serves: **P-4**.* · id `DR-11`

**Choose by the relation the content has, never by how a shape looks.** The
library is tagged with a `relation` — composition, order, process, hierarchy,
degree, metaphor — and the rule is that the relation in the data and the
relation the shape encodes must be the same one. A funnel whose values do not
decrease, a 2×2 whose axes are not independent, a waterfall that does not add
up: each is a drawing that asserts something the data does not.

**A shape enters the library only if its relation serves these chart rules.**
Extraction is not ingestion. A family that draws a relation this design language
has no use for stays in the raw material and does not become a second figure
vocabulary competing with §4 — three vocabularies is the state this package has
spent releases getting out of.

**Metaphor families carry a decoration risk and are marked with it.** An
iceberg, a gear train, a honeycomb: each can carry an argument, and each is
mostly used because it fills a page. Reaching for one is a moment to check
P-4 — a figure that carries no argument violates that clause rather than
satisfying it.

**Look at the unit before you use it, and the unit is the SVG.** `relation`
narrows the field; it does not tell you what the geometry actually draws, and
this library has been curated wrongly twice by reading a name as a
classification. `embed_shapes.py --list` names what a document references and
`assets/shapes/<id>.svg` opens in any browser — that is the whole check, and it
is one the package can honour, because it ships the file. The manifest used to
carry a `preview` path for every unit and the package shipped none of them, so
the discipline pointed at 206 files nobody had.

**Shapes reach a deliverable through `scripts/build/embed_shapes.py`**, which
emits only the symbols the document referenced. Two things follow without new
machinery: D19 already fails a reference that resolves to no symbol, so the
pipeline's correctness is checked by a gate that has been running for releases;
and only the recoloured library is a source, so original-palette geometry has no
path into a deliverable at all.


### 4.2 · Composing a shape: layer it, recolour it, transform it, label it

*Serves: **P-4**.* · id `DR-14`

A shape from the library is a **starting geometry, not a finished figure**. 192
of the 206 units carry no text at all, so the words and the numbers are the
document's job — and that is the capability, not a gap. A shape dropped in
unlabelled is decoration, and decoration on an argument page is a finding.

**The page's numbers go into the geometry, not beside it.** In the external
genres a figure earns its place by carrying the numbers the page states —
lengths, fills, step heights, counts drawn to the values — so that the reader
takes the quantity from the drawing and the insight from the composition. A
library shape composed with words alone is still an icon wearing labels: the
first blind-reviewed product deck shipped a staircase carrying six step names
on a page claiming 206 units and 16 layouts, and the reviewer's verdict was
`没有把数字和矢量图结合` = `没有洞察` — no number in the geometry, no insight
in the figure. `check_design.py` D29 reports every figure page whose SVG text
carries none of the page's own stated values. (Reader review D16, C8.)

**Label it against measured coordinates, never assumed ones.** Render the unit
once with a coordinate grid over it, read where its segments actually fall, and
place the text there. The alternative is placing labels by eye on a geometry you
have not seen, which is how the figure ends up saying something the drawing does
not.

**Two traps that do not announce themselves**, both found the first time this
was done for real:

- A `<use>` of a symbol whose viewBox has a **non-zero origin** — which is most
  of this library, the units having been extracted at their source coordinates —
  renders **shifted**, and with a large enough offset renders entirely outside
  the visible box. It does not error. Give the `<use>` explicit `x`, `y`,
  `width` and `height` matching the symbol's viewBox.
- A `fill="…"` **presentation attribute** on a `<text>` loses to any CSS rule
  that styles figure text, so a label written that way silently takes the
  stylesheet's colour rather than the one you chose. Use `style="fill:…"`.

**Layering, recolouring and transforming are all in scope.** Two units may be
composed on one canvas; a unit may be tinted to a different token to separate a
series; a unit may be scaled, mirrored or rotated where the relation survives
the transform. What may not change is the relation: a funnel that is mirrored is
still a funnel and still has to decrease, and a transform that makes a shape
mean something it did not is the same defect as choosing the wrong shape.

**Recolour within the ladder.** The library ships bound to `--acc-2` through
`--acc-5` with `--on-acc` for text on top and `--lime` reserved for the event
green. Retinting a unit means moving it along that ladder, never introducing a
colour — §1 is unchanged by any of this, and D20 gates it.
- **A label on a library shape is sized in the shape's own units, not the
  token ladder's pixels.** A unit's viewBox can run thousands of units across
  (flow-5 is ~32 units per rendered pixel), so a token 11px text class renders
  invisibly small inside it. Scale the font size by the viewBox-to-cell ratio,
  the same arithmetic the `x`/`y`/`width`/`height` rule already forces.
  (Found composing the first library shape into a rebuilt operations guide.)


## 5 · The commercial footer

*Serves: **P-5**.* · id `DR-7`

**Every page carries its handling terms and where the document is from.** Left of
the footer rule: the confidentiality line, then the organisation's site. Right:
`N / total`. Pages travel alone — a slide is screenshotted out of a deck and
forwarded without the cover — so terms that live only on page one do not travel
with the page.

**The terms open with the handling marker**: the `shield` reserved icon, in
`--seal-t` (the seal's text-safe form, which lifts on the dark canvas), inside
the `.foot .conf` flex slot `tokens/lumi-layouts.css` ships, ahead of the
terms (owner directive 2026-08-09). The seal may mark it because the handling
line is a standing warning to the reader — §1's ledger records the extension —
and on the lime opener the marker inverts with the rest of the footer. The
marker is the standard rendering, not part of the gate: D12 gates on the terms
being present, and a page whose terms arrive without the icon has a style
defect, not a compliance one.

**This is one of the checks in `check_design.py` that fail the run.** Which
ones is not written here: a row whose target carries `(gates)` gates, that
string is the authority, and the `gating claims` guard holds this file to it.
The sentence used to say "one of the five" and then list seven, which is
convention 13's case in one line — a count in prose rots, a sentence naming its
authority cannot.
Everything else there reports, because a page is done when a human reads it as
intentional and a threshold satisfiable without improving the page ends the
looking. This is different in kind: not a judgement about whether a page is well
made, but a commercial requirement on the artifact, like a contract term. A
design metric that gates is a mistake; a commercial one that does not is a
different mistake.

**A repository path is not a reader-facing source line.** A source line names
something the reader can act on — a system, an extract and its date — not a file
on the machine that built the deck. `.foot .src` was removed from `tokens/` in
0.1.366 after the first deliverable to meet it printed a build path on every
client page; a second put one back, in Chinese, and every gate passed it.
**D15 gates on it now**, in every genre: consulting and internal analysis keep
per-page sourcing, and no genre wants a path.

**The other is D14: no slot the author left for themselves may reach the
reader.** `[TO FILL]`, `[TBD]`, `{{name}}`, an empty bracket pair. Also different
in kind — it asks whether the document is *finished*, which is decidable. A real
deliverable shipped four of these on its closing page, immediately beside its own
callout saying they must not ship, and nothing in this package noticed: a
placeholder is not a banned phrase, not a colour, and occupies exactly as much
room as the text that should have replaced it.

## 6 · Icons: semantic, never decorative

*Serves: **P-4**.* · id `DR-8`

**Two icon sets ship with this skill, and they do different jobs.**

`assets/icons/lucide/` is the **semantic inline set** — 2007 icons on a 24×24
grid, `stroke=currentColor` re-stroked to 1.25px, so they follow the text ladder
and switch with the palette for free. Every eyebrow, figure node and row-head
icon comes from here.

`assets/icons/koboyo/` is **36 filled silhouettes, for part-opener subject marks
only** (§3). Fill-based, not stroked, because a stroked icon scaled to display
size renders as the accident this section records two bullets below, while a
filled silhouette renders as a deliberate graphic. It was vendored for that one
purpose and named in no rule file until 0.1.547 — three conformance decks left
every opener bare, and the set they needed had been sitting in the package the
whole time. Two commands do the work:

```bash
python3 scripts/build/embed_icons.py --search tariff   # find one
python3 scripts/build/embed_icons.py radar route code  # sprite of just these
```

**Embed only what the document uses.** A full-library sprite is 0.9 MB of dead
weight in every deliverable, which is how a library becomes a liability.

**Breadth and consistency are two different problems and both need solving.**
Breadth comes from the library: a page about a tariff line, a page about a court
ruling and a page about a comment deadline should not share one icon, and they
will if the set is small. Consistency comes from the **reserved bindings** in
`scripts/build/embed_icons.py` (`--list`), which pin one icon per recurring LUMI
meaning so the same concept looks the same in every deliverable. Outside those
bindings the choice is free, but **within one document an icon still means
exactly one thing** — an icon reused for a second meaning is worse than no icon,
because the reader learns a vocabulary that then lies to them.

**Where they go**: the section eyebrow on a content page carries the icon that
names that page's subject, ahead of the `PART <letter> · <subject>` label the
§3 eyebrow contract sets. **So does every labelled node inside a figure and
every table row-head group** — a named box in a diagram is a sub-heading, and it
carries the same weight of meaning as the eyebrow above it. Minimum **14px
effective size** at the design viewport, which for an SVG node means checking the
rendered size, not the authored one. Never add icons to "look rich". Never draw
one ad hoc either: with 2007 available, "nothing fits" almost always means the
page's subject is not what you thought it was.

*Provenance, two rounds.* This section required "symbol library embedded per
document" from 1.2 to 1.7 while the package shipped nothing, so the 0.1.337 deck
contained zero icons — the same defect 0.1.337 fixed for the display face, one
directory over. **A rule may not mandate an asset the package does not ship.**
0.1.338 then shipped eight hand-drawn icons and the reader said the expressiveness
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
- **The 14px minimum governs a SEMANTIC INLINE icon, not a display-scale mark.**
  An opener's subject mark (§3) is a composition element sized in viewport units;
  it is not on a text line and it names nothing a reader must read. What it must
  be is **fill-based, never stroke-based**: a hairline outline scaled to display
  size is the accident the next bullet records, while a filled silhouette at the
  same size is a deliberate graphic. Check which one a library ships before
  scaling anything from it — Lucide is stroked, and a stroked icon does not
  survive this treatment.
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
  legal move and the evidence went first. Then 0.1.337's author read "budget two
  lines" as a target and capped every title at 48ch, so all 24 content titles
  broke near the middle and the reader asked why they were not filling the line.)
- **Figure vocabulary ⊆ body vocabulary**: when body terminology is renamed,
  sweep every figure label in the same pass — a chart that still speaks the old
  names contradicts the text beside it.
- Cards in a row need internal alignment constraints: equalize title heights
  (min-height) and stack stat numbers above their labels, or differing title
  wraps misalign every row below.

## 7 · Numbers are the copy

*Serves: **P-2**.* · id `DR-9`

- Exact values, never rounded for effect (671 stays 671, not "670+");
- Label + value spec strips (HEIGHT 70 m style), values in the data voice;
- Negative/qualifying information is stated inline in parentheses
  ("(illustrative)", "(proposal value)", "(uncalibrated)") — neither buried in
  footnotes nor dramatized;
- **Copy the form, not the framing**: never pick the most flattering measurement
  condition for a headline number — numbers may serve as copy only when the
  framing survives scrutiny.
- **A number reads before the words it belongs to.** Three places, one order: in
  a **stat block** the figure comes first at display size and the sentence sits
  under it in support ink (`.stat` / `.sv` / `.sn`, and `.band` renders the same
  way round); **where a title carries a number** it leads rather than being
  spelled into the middle of the sentence; **inside a figure** the value is set on
  or above its mark with the descriptor beneath. This is an **order, not a size
  floor and not a quota** — which tier a number takes, and whether a page carries
  a display number at all, stays §3's focal-element decision, and **a title with
  no number in it is a normal title.** *Second provenance, one release later: the
  release that introduced this rule then produced a deck whose fourteen content
  titles every one opened on a small operational count, and M11 title uniformity
  reached 52.9% against its 60% ceiling. A placement rule had been read as a
  template, which is convention 4's failure mode inside a rule written to prevent
  it.* *Provenance: `.band` rendered
  label-above-value for eleven releases while
  `references/exemplars/mckinsey-design-notes.md` EX-2 item 2 stated the
  opposite, and nothing compared the two. The deck that reached the owner's
  standard wrote the rule twenty times as an inline style because the package
  shipped no role for it; the deck that did not carry the rule put its single
  most important number — zero signed customers — in a band below a title that
  spelled the page's other quantities out in words.*

## 8 · The verification matrix

*Serves: **P-2**.* · id `DR-10`

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
    export.
  - **A4 portrait, 794×1123** — printing and binding.

  **A deliverable is designed for ONE of them, and it says which** (owner
  directive, 0.1.380). `<body data-geometry="landscape">` or `"portrait"`, and
  the tokens hang the stage off that declaration rather than off the reader's
  window. The genre picks the default — sales, marketing and consulting are
  projected, so 16:9; training is printed, annotated and bound, so A4 portrait —
  **and when the request does not settle the genre or the format, ask before
  generating.** That is the one question worth a round trip, because the answer
  changes every page.

  **Both editions of one file is not a thing this package produces.** A second
  geometry is a second *composition*: different layouts, figures drawn for the
  new proportions, its own title lengths. Serving both from one file gives the
  unnamed one an automatic collapse nobody designed. *Provenance: a 31-page
  landscape deck exported at A4 produced dead half-pages, figures starved to
  188px in a 682px column, and a footer wrapped to two lines on every page —
  none of it visible at the geometry it was designed for. `export_pdf.py` now
  refuses a geometry the document does not declare, and `inspect_layout.py`
  grades the declared one.*

  **Portrait is a composition, not a reflow.** A two-column split at 794px wide
  gives two 370px gutters, so a page that is a split in landscape usually wants a
  different structure in portrait. Collapsing every horizontal layout at a width
  breakpoint is not a portrait design; it is the landscape design giving up.
- **Export axis** (owner directive 2026-08-09). `scripts/ops/export_pdf.py` renders
  a deliverable at the stage geometry: **PDF** as one vector page per `.page`
  (no resolution to pick), and **page rasters** at `--scale` device pixels per
  CSS pixel — **default 3, which is 4K from the landscape stage (3840×2160);
  floor 2 (2K), and the script refuses a smaller scale**. The scale is an
  export multiplier only and never changes the CSS stage, because every
  `clamp()` in `tokens/` is written against the stage; the HTML edition needs
  no scale at all — the zoom stage adapts to the reader's window and pixel
  density natively.

- **Output axis: a deliverable lands in the reader's workspace, not wherever the
  input happened to sit** (owner directive, 2026-08-09). **The default is
  `Documents/LUMI-Style/` under the user's home directory** — the same one place
  on macOS, Windows and Linux — and a directory the user names still wins. **The
  agent asks before creating it**; a package that silently makes folders in
  someone's home is one nobody installs twice. *Provenance: the default was the
  input file's own directory, which is right for one person on one document and
  wrong for every other case — several agents working at once, several people on
  one machine, and the case that found it: an input living inside the package,
  which put finished client documents in the skill's own install tree.*

  Two things this rule does **not** say, because both have been "fixed" by
  someone reading only the first sentence. **An export lands beside the document
  it was made from** — `export_pdf.py` writes the PDF next to its HTML and
  `inspect_layout.py` writes its contact sheet into a `_layout/` beside it, so a
  deliverable's files stay together; that is a different question from where a
  *new* document goes. And because the default is now one shared folder rather
  than one folder per project, **a deliverable's filename carries its own
  identity** — the document's name and the version that produced it. Two files
  that share a stem there do not sit politely side by side: `export_pdf.py`
  refuses the second export rather than overwrite the first.

  `scripts/ops/output_dir.py` resolves the path for an agent that can run it —
  Windows redirects and localizes the Documents folder, so `~/Documents` is a
  guess there rather than an answer. It is a convenience, never the authority:
  the rule above is a literal path a `prompt`-tier model can write down unaided,
  and the script must agree with it.
- **Viewport axis**: also check a short laptop window (e.g. 1000×550). The
  landscape page is a fixed 1280×720 stage scaled by `zoom`, so the check
  exists to prove the stage SCALES — do **not** add window-keyed
  (`max-width`/`max-height`) media queries that restyle the inside of the
  stage: a window-triggered reflow of a stage that never got narrower is how
  both scored conformance decks shipped colliding pages (GAP-001; the tokens
  themselves carried such a block until 0.1.380). **The footer rule and page
  number must be visible on every page at every matrix point.**
- Verified at one matrix point is not verified. Screenshot page by page; a
  defect found by the reader is a matrix point you skipped.
- **Do not narrow the matrix on the command line.** `inspect_layout.py` already
  reads `data-geometry` and runs the points that declaration implies — four for
  a landscape deck, two for portrait. Passing a single `--geometry` overrides
  that and turns the matrix off, which is how a 0.1.449 deliverable was verified
  at 16:9 alone: its content-spill fix left one pixel of clearance under a gate
  that fires above one, and one pixel is what a different geometry moves.
  Narrow it only to reproduce a known defect, and run the full set again after
  the fix.
- **Palette axis.** `--dark` is a switch, not a matrix point: one run renders
  one palette, so a deliverable that ships a dark variant is checked by running
  the tool a second time. Nothing infers this — a `*.dark.*` filename is the
  only thing that turns it on by itself.
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
  reconsider; do not set a threshold on it. 0.1.340 withdrew the 82% floor because
  it was satisfiable by stretching table rows while four diagrams rendered at 40%
  of their cell, and it measured the bounding box of all ink, so a small chart
  with a long caption scored as full.
- **Consistency axis.** Read the deck as a system, not as pages: for every
  repeated role collect the computed family, weight, size, transform, tracking
  and colour, and count the distinct renderings. More than one is a finding, and
  every sanctioned exception is declared in the probe rather than tolerated.
  Normalise tracking to em before comparing — it is authored in em and computes
  to px, so two sizes can never agree otherwise, which cost one round of chasing
  a difference that was not there. Add: one datum per geometry for where content
  begins, one colour per chart component across pages, and a shared baseline
  inside a stat band.

  **Never ignore the axis a defect sits on.** A title is checked as three
  registers — content, cover, closing — each compared on size. Collapsing them
  into one role that ignored size, to excuse a cover legitimately larger than a
  content page, made a title at 34px and one at 57.6px produce the same key, so
  the first defect the consistency audit was built to catch could not be seen by
  it. Split the role; do not blind the comparison.

  **Run it at every geometry, and measure the type rather than its box.** This
  audit hard-coded a 1280×720 viewport for a release, so a callout set to three
  different sizes by the portrait block went unreported while landscape read
  clean. And a stat-band value written the shipped way — `41<span class="u">%
  </span>` — sits in a box 25px deeper than one without a unit while the digits
  stay on the same baseline, so comparing element boxes flagged bands whose
  numbers were exactly aligned.

- **Coverage axis: a check that did not run is not a check that passed.** Every
  probe below reports `NOT MEASURED` with a reason when its subject is absent,
  and `inspect_layout.py` exits non-zero if anything could not be measured. That
  is not a gate on the design — the judgements still gate nothing — it is the
  difference between silence and approval. *Provenance: a document with no
  `section.page` at all drew eleven affirmative lines and exit 0, including "one
  horizon on each of 0 pages"; a document whose class names differed from the
  probe's lost eight of ten role checks and got shorter, greener output for it.
  The role vocabulary those checks key on now ships in `tokens/lumi-layouts.css`,
  so the contract is inspectable rather than folkloric.* `check_repo.py`'s
  **probe vocabulary** guard holds the two together: a class a probe asserts as
  a role must have a base rendering in `tokens/`, and a class it merely counts
  must be waived in writing. That is what surfaced the four block patterns — the
  tier-1 callout, the card, the swap, the vow — which the package audited for
  four releases and shipped only inside a portrait media query.
- **Collision axis.** Nothing may land on anything. Text against text **and text
  against every drawn element** — field, figure, band, spec, geography. 0.1.347
  shipped this comparing text to text only, and a reader immediately found two
  defects it could not see: a field sitting 22px on a paragraph, and the cover
  globe crossing the document attributes on both the cover and the closing.
  Eleven pairs, every one of them text against a drawing. *A probe that knows one
  kind of collision finds one kind of collision.* Containment is not collision: a
  caption inside its own figure is fine. Two text blocks may not land on each
  other. Every other
  probe measures a block against the *page* — its top, its bottom, its column,
  the footer rule — and none of them can see two blocks overlapping in the middle
  of one. A reader found it twice before any check did, when 0.1.346's heavier
  register outgrew grid rows that had been sized for the old one. Measure leaf
  text against leaf text; a container legitimately encloses its children. **When
  the type scale moves, the tracks that hold it have to move with it** —
  `min-content` on the row, or the block overflows onto its neighbour instead of
  lengthening its own row.
- **Reserve axis, and the thing every other probe on this list is blind to.**
  `.body .lede` reserves its height, and the reserve is a **ceiling**: a title
  needing three lines does not get a taller block, it gets shorter text. A real
  deliverable broke that rule — a closing page authored as a body page, four
  title lines in a two-line reserve — and then answered the overflow with
  `-webkit-line-clamp: 2; overflow: hidden`. Three of four title lines and the
  tail of a support sentence stopped rendering. **Hiding an overflow deletes
  content, and deleted content is invisible to geometry:** clamped text produces
  no spill, no collision and no page overflow, so every probe above passed the
  page. Measure both halves — what the children need against what the block
  reserves, and whether anything inside a lede is clipping. A clamp in a title
  block is never legitimate.
- **Do not turn that into a per-element `scrollHeight` vs `clientHeight` check.**
  It was the obvious generalisation and it is wrong: `h2.t` measures a 35px box
  holding 42px of ink at the design geometry, because `--fs-title` resolves to
  34.56px against a `line-height` of 1.02. That is the tight leading this system
  uses on purpose, so such a check fires on every correctly-set title in the
  deck. The frame axis below compares content against the *page* box, which is
  fixed and has no leading; an element box is a different question.
- **Nothing may be styled only inside a media query.** The general form of the
  rule below, and the one a machine can hold: a class the stylesheet touches in
  one geometry and nowhere else is a rendering the package half-ships, so the
  document gets `tokens/`'s value on the sheet and whatever it invented at 1280.
  The only honest exception is a rule whose *purpose* is to differ per geometry —
  the landscape/portrait figure pair, where a figure is drawn twice and each
  geometry hides one. `check_repo.py`'s **media-only rules** guard requires
  everything else to have a base rendering or a written waiver. *It found a
  density modifier that meant nothing at 1280, a graded-criterion block with no
  base rendering and no documentation, and a sixteenth page layout.*
- **The layouts the stylesheet defines and the layouts the checker grades are one
  list.** D9 reads a page whose `.body` class is not a shipped layout as using
  none, so a layout present in `tokens/` and absent from `check_design.py` reads
  as an author's typo. `.body.cover-grid` was in exactly that state for eleven
  releases — portrait-only, missing from the token file's own "fifteen page
  layouts" header, missing from the §3 table, missing from the checker — and was
  removed rather than completed, because shipping a sixteenth layout nobody asked
  for is the speculative rule-making CLAUDE.md rule 2 forbids. When the owner's
  cover standard did ask for it, 0.1.375 reinstated it completed: base rendering,
  portrait variant, header count, §3 row and checker entry moved together.
- **A geometry may tighten spacing. It may not change type.** brand.md's rule —
  a page that no longer fits gets its content trimmed, never its type nudged —
  binds across the two page geometries as well as across pages. Breaking it is
  undetectable at the design viewport by construction: run the consistency audit
  at A4 and the split appears at once, run it at 1280 and the deck is clean.
  *Provenance: `lumi-layouts.css` wrote that sentence in its portrait block and
  then broke it in the next twenty lines for eighteen releases — seven rules
  setting a font-size for `.key`, `.no`, `.yes`, `.ledname`, `.card dd`, a notes
  list and a notes table. None of those classes had a base rendering anywhere,
  so the portrait value was the only value the package shipped and every one of
  them rendered two ways. The same trap caught `.gd` in 0.1.350 and `.duo`, whose
  base grid existed only in the geometry that collapses it.*
- **A scoped role audit hides its own subject.** `.band .k` and `.band .v`
  reported "one rendering" on a deliverable whose `.k` and `.v` rendered five
  different ways each — every one of them outside a band, where `tokens/` says
  nothing and the author necessarily invented the rendering. The scoping is not
  the error (a band value and a lead value are two roles on purpose); reporting
  only the scoped uses is. Count what sits outside the shipped scope too.
- **Ground axis.** Measure the ground on the *rendered* page with every
  foreground element hidden, and require it under 1.40:1 against the canvas plus
  free of repeated identical marks. Reasoning about it from the declared alpha
  does not work: the tiers were tuned analytically, measured at 1.428 and 1.549,
  and had to come back down. The probe caught its own author.
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
  flex-start }` since 0.1.339 and it had **never once applied**, because the fill
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
  at 1817px: 0.1.341 shipped `max-width` on `.body` and nothing on `.foot`, so all
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

## 9 · Imagery: a photograph is evidence or it is not on the page

*Serves: **P-4** + **P-1**.* · id `DR-15`

Opened at 0.1.493 on the owner's direction. Until then this package shipped no
photo library, and the absence had hardened into a ban applied to every kind of
image — the failure convention 5 exists to prevent, recorded there in those
words. What follows is the condition the old clause was waiting for.

**An image earns its place by carrying an argument the page cannot make
otherwise.** A photograph of the thing being discussed, a screenshot of the
artifact under review, a map or a document image the reader is asked to look at.
A photograph chosen to make a page feel professional is decoration, and this
document's own history says decoration is where these decks go wrong. The
question is the same one §6 asks of icons: *what does the reader now know that
they did not?*

**Four rules, and every one of them is checkable.**

1. **Embedded, never linked.** A deliverable is one self-contained file. A
   `src` pointing at a host is a page that breaks the first time it is read on a
   plane, and it also tells that host who is reading. Rasters ship as `data:`
   URIs. **D24 gates this.**
2. **Sourced and licensed, on the page.** Every image names its origin and the
   terms it is used under, in the colophon at minimum and in the figure's source
   line where the image is the evidence. Public domain and CC0 are the default;
   anything else needs the licence named. **D25 gates this.**
3. **Treated into the palette.** A full-colour photograph beside this palette
   reads as a foreign object. Tint it into the accent ladder — duotone against
   `--acc-5` and `--acc-2` is the house treatment — or place it as a mono plate.
   §1 does not bend for imagery: the page still carries one colour with one
   meaning.
4. **Text does not sit on an untreated image.** Set text on a treated plate with
   a measured contrast floor, or beside the image, never on raw photography.
   This is the surviving half of the old clause and it survives on its merits.

**Where imagery belongs**: the cover, a part opener, a full-bleed evidence page,
or inside a `.fig` as the figure itself. **Where it does not**: behind body copy,
behind a table, or as a repeating texture. The ground is the brand's texture and
there is one of it.

**The stock-photograph tells**, banned by name because they are how a deck
announces it was assembled rather than written: the handshake, the glass tower
at dusk, the diverse team around a laptop, the lone figure at a whiteboard, the
abstract network of glowing dots. If the image would fit any deck about any
subject, it is not evidence.

**Weight is a reader's problem.** An embedded raster is base64 and grows the
file by a third over its bytes. Downscale to the size it is actually rendered
at, and prefer a vector when the content is a diagram — a diagram embedded as a
photograph of a diagram is a defect, not a shortcut.

