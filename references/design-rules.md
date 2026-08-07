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

- **Canvas — light by default, dark on request** (v1.3): the default canvas for
  every deliverable is near-white (#FAFAF8) with the ink ladder. The dark canvas
  (near-black #060806 with a breath of green, cold-white ladder) is applied only
  when the user explicitly asks for dark. Both palettes share one structure —
  build with semantic tokens (`--bg`, `--nw`, ladder, accents) and switch the
  whole palette with a single `body.dark` override block; never fork the file.
  Literal colors in component CSS or inline SVG are a defect: they silently
  ignore the palette switch.
- **Single accent = natural green** (#48633E on light; lift to #7C9F63 on the
  dark canvas — the deep green fails contrast on near-black): emphasis, pass, built.
  **China red (#C8102E) is for warnings/red-lines/vetoes only** — never
  decoration. This is stricter than SpaceX/Tesla: they let color appear only where
  it carries meaning; LUMI pins each meaning to exactly one color.
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
(small light-gray text); 5. fixed type scale (figure title 14 / axis 10–11 /
source 11); 6. **the legend sits at the top right of the figure, above the plot**;
7. **caption anatomy is two-part** — "Figure N · Name" centered and bold on its
own line, then the detailed description left-aligned at the figure's width.

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
- **Page-geometry axis — the primary one.** Every deliverable serves two output
  formats, so both are matrix points, not options:
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
- **Fill axis (D7).** For every page, measure content height over available
  height between the title and the footer rule, and require **≥82%** at the
  design viewport. This cannot be a static check: the figure that failed to grow
  had perfectly legal CSS. Report the worst pages by ratio rather than a pass or
  fail alone, because the number tells you which layout to reconsider.
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
