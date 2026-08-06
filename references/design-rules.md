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
  from decks. Vendor the font (SIL OFL) and embed it — a declared face that
  never ships falls back silently and the identity never renders.
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

- Each screen/page carries exactly one claim: a giant short headline (3–6
  words, one accent word in green), one sentence of support, one centerpiece,
  a thin footer rule with source + page number — nothing else. Prefer
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
  citation reading).

## 4 · Five chart iron rules + form selection

1. Figure titles state conclusions, not labels; 2. one accent color (natural
green), everything else grayscale, red only for warnings; 3. no gridlines, no
chart borders, no legend for single series; 4. every figure carries a source line
(small light-gray text); 5. fixed type scale (figure title 14 / axis 10–11 /
source 11).

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
- **Page titles budget two lines at the design viewport** — shorten the title,
  never shrink the type. A third title line eats the content area and pushes the
  footer below the fold.
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
