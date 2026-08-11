# The expressive register — design

Date: 2026-08-11 · Written against 0.1.405 · **Status: designed, not yet
implemented.**

The owner reviewed the skill from the perspective of its three deliverable
families — consulting, training, user documentation — and found the visual
range too narrow for the second and third: one icon skin, no illustration
capability at all, and a water language that never shows its Japanese ancestry.
The directive: more icons and illustrations that carry LUMI's brand traits;
illustration in an exaggerated cartoon style with Japanese design influence;
water and ripples drawn the Japanese way (seigaiha, `青海波`), consistent with
the `上善若水` thesis in `references/brand.md`. An owner directive is a documented
case under maintenance convention 2.

---

## 1 · What exists today

- **Icons.** `assets/icons/lucide/` — vendored Lucide static (the release
  NOTICE records), 2007 icons, 24×24, `stroke="currentColor"`, re-stroked to the 1.25px hairline at
  emit time by `scripts/embed_icons.py`, which also owns the 18 reserved
  semantic bindings (`CORE`) and the CI integrity gate (`--check`: ≥300 files,
  LICENSE present, bindings resolve, every file `currentColor` + 24×24 + no
  hardcoded hex). One skin, deliberately neutral.
- **Illustration.** None. The word appears in the rules only in the
  number-discipline sense, plus one negative: the cover mark is "sized as a
  field the typography sits against, **not as a spot illustration**"
  (`references/storyline-templates.md`).
- **Water.** Three structural devices in `references/brand.md`: the field
  (discrete, every mark is a datum), the ground (continuous, uncountable,
  ≤1.40:1 rendered contrast, no repeated identical marks, no blend mode,
  `<defs>`/`<use>`, `slice`), the waterline (exactly one per page). The only
  shipped ripple drawing is the 16-polyline table in
  `scripts/build_fixtures.py:ground_defs()`.
- **The red line this touches.** "No watermark, no ornament, no flourish"
  (`brand.md` §4). The ground is the one carved-out decoration, legal
  *because* it is uncountable.

## 2 · The two decisions that shape everything

**Koboyo is not vendored.** The requested icon source (koboyo.com/icons,
98,511 hand-drawn icons) is free for use but its license prohibits
redistributing the collection — or any substantial part — and prohibits
bundling icons anywhere users can pick, extract or download them. A public
repository of SVG files is exactly that. Koboyo remains a private style
reference; nothing from it ships here. The owner chose to draw a house set
instead, and chose the same for illustration: fully hand-drawn, no CC0
vendoring, full brand control, small first batch.

**A pure seigaiha is a field pretending to be water.** The traditional pattern
is repeated identical arcs — precisely what the ground rule bans, and bans for
a reason this design keeps: a countable decoration can be mistaken for
evidence. So the Japanese water language ships in two layers with different
honesty contracts, rather than as one pattern that quietly weakens the ground
rule.

## 3 · The design

### 3a · One rule set, two registers

A deliverable declares `<body data-register="expressive">`; absent means
**restrained**, which is today's rules unchanged. Sales, consulting and
internal analysis are restrained, mandatorily. Training and user documentation
may declare expressive. User documentation rides the training register — no
new genre; `check_prose.py --genre` is untouched.

The honesty logic, to be written into `brand.md`: the expressive layer exists
where the reader's task is learning, not adjudication. Evidence — figures,
fields, grounds — obeys the same rules in both registers. The register never
relaxes a contrast floor, a lime rule, or a red line; it adds vocabulary, not
exceptions.

### 3b · The hand-drawn icon set — `assets/icons/lumi/`

First batch target ~24 (a target, not a floor): the 18 `CORE` meanings plus
about six training/doc meanings (tip, step, practice, caution, question,
celebrate). Same structural invariants as the Lucide set — 24×24,
`currentColor`, no hex — so `embed_icons.py --check` extends by iterating a
second directory, not by growing new rules. The hand-drawn character lives in
the path geometry (wobble, varied weight within the stroke budget), never in
breaking the invariants.

`embed_icons.py` gains `--register expressive`: `CORE` bindings resolve
lumi-first, Lucide fallback. One semantic vocabulary, two skins — the meaning
of `shield` does not fork. First-party work, so no NOTICE entry; provenance is
a note in the directory.

### 3c · Illustration — `assets/illustrations/` + `scripts/embed_illustrations.py`

First batch target ~12 hand-authored SVG scenes for training and documentation
needs: onboarding, empty-search, success, error, teamwork, data-flow,
decision, practice, setup, feedback, security, progress.

Style contract (new section in `design-rules.md`):

- exaggerated cartoon proportions; flat shapes; no gradients, no raster;
- Japanese flat composition — asymmetry, generous negative space, thick/thin
  line contrast;
- every illustration contains the waterline as part of its composition, and
  where water appears it is drawn as seigaiha-derived arc texture — this is
  how the brand lives *inside* the drawing rather than being stamped on it;
- paint only via `var()` tokens, so illustrations re-skin with the palette;
  lime is surface-only inside an illustration too, at most one lime surface;
  people are painted from the ramp — no hex, no skin tones.

Technical contract, enforced by `embed_illustrations.py --check`: one fixed
viewBox aspect, fill/stroke drawn from an allowed token-role list, no hex, no
`<image>`, namespaced ids, and a manifest (`manifest.json`: name, meaning,
tags) 1:1 with the files. CLI mirrors `embed_icons.py`; embed only what the
document uses. Semantics mirror icons: within one document an illustration
means exactly one thing. Expressive register only. Budget is a **ceiling**
(one illustration per page), stated as such per convention 4.

### 3d · Japanese water, two layers — `scripts/build_seigaiha.py`

- **Layer 1, both registers: the ground upgrade.** Seigaiha-*inspired*
  concentric-arc clusters, every radius/spacing/phase/width drawn from fixed
  jitter tables — deterministic, byte-stable, and uncountable, so it obeys the
  existing ground contract wholesale (≤1.40:1, no blend mode, `<defs>`/`<use>`,
  `slice`, crowds below the waterline). Emitted as a `<defs>` block;
  `build_fixtures.py` adopts it as the fixture ground.
- **Layer 2, expressive only: the pattern band.** True repeating seigaiha as a
  new *bounded* device: covers, part openers, footer bands. **Never behind
  data marks, figures or tables** — a countable decoration must never sit
  where it could read as evidence, which is the ground rule's own logic
  carried over rather than waived. Height and loudness ceilings ship as
  tokens.

`--check` follows the `build_worldmap.py` pattern: regenerating must reproduce
the tracked output byte-for-byte.

### 3e · Rules, tokens, checks, entry points

- `brand.md`: registers section; the band as a fourth device; illustration
  honesty; the §4 red line scoped to the restrained register and to evidence
  pages in both.
- `design-rules.md`: §5 extended (lumi skin, register resolution); a new
  illustration section; verification-matrix rows.
- `storyline-templates.md`: the training scenario gains the expressive
  language; the cover contract notes the band allowance.
- `tokens/lumi-theme.css` + `tokens/design-tokens.json` edited together
  (parity guard): band tokens, illustration role list, and — found during
  this design's exploration — the JSON `assets` note still says "the eight
  semantic icons" three releases after the set became 2007 Lucide files; it
  gets fixed here.
- `tokens/lumi-layouts.css`: base renderings for every class a checker will
  assert (`.illo`, `.band`), honouring the checker-vocabulary guard.
- `check_design.py`: the one *gating* addition is decidable — expressive-only
  vocabulary used without the register declaration. Counts of illustrations
  and bands are reported diagnostics, like D10.
- `inspect_layout.py`: a band overlapping a figure or table is a decidable
  finding; illustrations join the ink accounting.
- Fixtures: a third, expressive fixture from `build_fixtures.py`;
  `check_fixtures.py` asserts its verdicts.
- CI: `embed_illustrations.py --check`, `build_seigaiha.py --check`, new
  scripts in the `py_compile` list.
- Entry points re-flowed by hand (`SKILL.md`, `AGENTS.md`,
  `prompts/lumi-style-core.md`, `README.md`); generated artifacts via
  `build_entrypoints.py`; one CHANGELOG entry and one version bump for the
  change.

## 4 · How it will be verified

- Mechanical: `check_repo.py` and every `--check` above exit 0 at every
  commit.
- Rendered, per convention 8: one expressive training page and one restrained
  consulting page built with the new ground, through `inspect_layout.py` and
  `export_pdf.py`, and looked at — every illustration page, at the design
  viewport, over `file://`.
- Drift re-read: after the rule prose lands, all three entry points and
  `README.md` re-read in full.

## 5 · What this does not do

- It does not vendor Koboyo, Open Peeps, unDraw, or any external art.
- It does not add a genre or touch `check_prose.py`.
- It does not relax any restrained-register rule: consulting output changes
  only in that its ground may now carry the seigaiha-derived drawing.
- It does not let the band or any illustration near evidence: figures,
  fields and tables look the same in both registers.
- It does not state 24 or 12 anywhere in the rules: rules reference the
  shipped set, whatever its size, per convention 5.
