# LUMI Design Rules

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
- **Hierarchy comes from a transparency ladder, not new grays**: on light canvas
  every level (body/secondary/notes/rules) derives from ink #2B2E33 at α
  90/70/50/30/15/08; on dark canvas from cold white **#F0F0FA** at α 70/55/45/25/10.
  **Dark-canvas text is cold white, never pure white.**
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
  visibly differ**, one centerpiece, a thin footer rule with source + page number
  — nothing else. (The rule read "one sentence of support" until 1.6.0, which
  drove sentence-length variance across a deck to near zero; see M8.) **The headline has no word
  ceiling**: its length is set by the title contract in
  `storyline-templates.md` — topic + assertive subtitle carrying a verifiable
  fact — and the only hard limit is two lines at the design viewport. (Lesson:
  v1.2 replaced that contract with "a giant short headline (3–6 words)", which
  compressed deck titles to 4–8 CJK characters, deleted every evidence figure
  from the title line, and left bare antitheses that read as AI filler.) Prefer
  hairline-separated rows over card boxes: on a dark canvas, borders are
  furniture; hierarchy comes from the ink ladder;
- Generous whitespace is part of the design; content distributes across the full
  page height (never crowds the top half);
- The full-bleed block skeleton (single title + single CTA) is usable, but the
  centerpiece is a chart/diagram/directional gradient — without a professional
  photo library, never set text directly on imagery;
- Navigation preserves traceability (documents are not landing pages): long
  documents keep a table of contents; decks use a narrative rail;
- scroll-snap is for decks only — never long documents (it breaks table and
  citation reading);
- **Long-document callouts form a three-tier hierarchy** (reader-reported: one
  uniform left-rule for every highlight flattens the page): key conclusions get
  a tinted box with a full 1px border plus a strong left edge; standard guidance
  keeps the plain left rule; weak notes are muted text with no frame;
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

Form selection: one number is the story → stat callout (big figure + small label,
data voice); composition/trend → segmented bars / tick bands; a bridge between
two numbers → waterfall; concept relations → icon-led flow diagram; time
commitments → milestone timeline; **comparisons always use tables** (columns =
options, rows = dimensions). Illustrative values must be labeled.

## 5 · Icons: semantic, never decorative

Line style, stroke=currentColor, symbol library embedded per document; each icon
holds one fixed meaning (ledger=master data · radar=watch · funnel=adjudication ·
bell=alert · shield=compliance · pen=signature · gauge=measurement ·
slashed circle=forbidden); never add icons to "look rich".

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
- **Page titles budget two lines at the design viewport.** Display titles are set
  as a size *range*, not a single size, and a long title takes the lower end
  before any word is cut. Order of remedy: (1) drop to the bottom of the title
  range; (2) tighten wording without losing the subject or the fact; (3) split the
  claim across the title and the support line. **Never cut below the information
  floor.** A third title line eats the content area and pushes the footer below
  the fold. (The original guard read "shorten the title, never shrink the type";
  once v1.2 made display titles giant, that phrasing left cutting words as the
  only legal move and the evidence went first.)
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
- **Viewport axis**: verify at minimum three sizes — the design viewport
  (e.g. 1450×900), the print page (e.g. 1280×720), and a short laptop window
  (e.g. 1000×550). Slides use `min-height:100svh`, so an overflowing page pushes
  its footer below the fold silently. **The footer rule and page number must be
  visible on every page at every matrix point** — provide height-based media
  queries that step down type and spacing.
- Verified at one matrix point is not verified. Screenshot page by page; a
  defect found by the reader is a matrix point you skipped.

## 6 · Numbers are the copy

- Exact values, never rounded for effect (671 stays 671, not "670+");
- Label + value spec strips (HEIGHT 70 m style), values in the data voice;
- Negative/qualifying information is stated inline in parentheses
  ("(illustrative)", "(proposal value)", "(uncalibrated)") — neither buried in
  footnotes nor dramatized;
- **Copy the form, not the framing**: never pick the most flattering measurement
  condition for a headline number — numbers may serve as copy only when the
  framing survives scrutiny.
