# LUMI Design Rules

> Skeleton researched from the public web design of SpaceX and Tesla (one claim
> per screen / numbers-as-copy / monochrome discipline); the palette and its
> semantics are LUMI's own. Tokens live in `tokens/`; this file covers usage and
> judgment. (Repository language: English only — red line.)

## 1 · Color: one color, one meaning; hierarchy via transparency

- **Canvas**: space-gray light canvas for long documents; night-green dark canvas
  for cover / end-state / future pages — dark pages create the narrative's
  "three-act rhythm" and never exceed three per deck.
- **Single accent = natural green** (#48633E): emphasis, pass, built.
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

- **Narrative voice** (titles/body): rounded Latin (Quicksand/Nunito) with CJK
  fallback (PingFang SC / Noto Sans SC). Weight rule: heavy titles, light body,
  large contrast.
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

- Each screen/page carries exactly one claim: one conclusion-style title + one
  visual centerpiece + at most one supporting group;
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

Field-tested layout guard: a right-anchored label on a full-width bar must be
anchored **inside the fill**, or its tail lands on the canvas and white text goes
invisible — anchor position must track fill width.

## 6 · Numbers are the copy

- Exact values, never rounded for effect (671 stays 671, not "670+");
- Label + value spec strips (HEIGHT 70 m style), values in the data voice;
- Negative/qualifying information is stated inline in parentheses
  ("(illustrative)", "(proposal value)", "(uncalibrated)") — neither buried in
  footnotes nor dramatized;
- **Copy the form, not the framing**: never pick the most flattering measurement
  condition for a headline number — numbers may serve as copy only when the
  framing survives scrutiny.
