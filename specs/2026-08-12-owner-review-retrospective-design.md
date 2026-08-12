# Owner-review retrospective: seven defects, three roots — design record

Date: 2026-08-12 · Status: settled, implementing across 0.1.443+ (this file is
history once landed, per specs/README — never cite it as authority)

## The case

The owner read a 34-page A4-portrait deliverable built at 0.1.442 and reported
seven defects, one performance complaint (an hour for 34 pages, ceiling ten
minutes) and two product asks (a debug mode; evidence on 16:9 figure/number
proportion). Under CLAUDE.md rule 2 this review is the documented case for
every revision below. Forensics on the delivered file, the rule tree and the
build pipeline preceded any fix; the owner corrected two initial mis-readings
in review: the brand-globe requirement was explicit and prior (her words:
`放 assets/brand`),
and the cover-attrs styling was previously verified in a shipped 16:9
deliverable — both defects are REGRESSIONS, not new gaps.

## Root causes (three, for seven defects)

1. **The document was hand-copied from the test fixture, not scaffolded** —
   style block byte-identical to `fixtures/deck-pass.en.html`, `REPLACE ME`
   title, fixture footer site, no fonts, no scripts.
2. **Owner-verified renderings lived only in single documents' DOC_CSS** and
   were lost by the next build (recorded as FM-11; the footer-flex history is
   the precedent).
3. **The repo's own rules contradicted each other on the figure green**, and
   the token-mirror guard walked one way only, so the contradiction had no
   mechanical surface.

## Decisions (owner-ratified where marked)

- **D1 — Scaffold is the start.** `new_deck.py` is the stated origin of every
  deliverable; fixtures are checker inputs. D14 gains the scaffold's own
  unbracketed slots (`REPLACE ME`, literal `lumi-style VERSION`), head
  included. The fixture's reserved site domain stays uncaught by decision
  (IDEA-9). The scaffold embeds the display face itself.
- **D2 — Owner (ratified): the FIELD globe is the default cover/closing
  mark**, vendored into `assets/brand/lumivate/` and locked, embedded live
  (`data-globe` + inlined runtime, reduced-motion respected). It is identity,
  not a document claim — the truth test governs replacement marks only. The
  cover pair joins the lock it had always been missing from.
- **D3 — Owner (ratified): lime-on-dark.** The lime is the one event green and
  never touches the light canvas bare: openers keep the lime field, the
  cover/closing subject word becomes lime on its own `--on-lime` chip, number
  panels keep near-black-on-lime. D13's carve-out is exactly the same-rule
  `color:--lime` + `background:--on-lime` pairing.
- **D4 — One accent meaning, two measured inks.** `--acc` carries it as text;
  `--acc-live` carries it in figures (`f-acc`/`s-acc`, geo layer, legend
  swatch). brand.md and the theme comment now state the same rule.
  `design-tokens.json` gains the missing keys and `check_palette_parity`
  walks both directions.
- **D5 — The verified-then-lost renderings are promoted** (`.attrs .k` bold /
  `.v` one-line-ellipsis, `.band .v .u`/`.v.acc`/`.first`, the print
  page-break block) and the portrait block gains the `--fs-cover` override
  its own comment claimed. `--genre training` appends Template 4's reference
  page.
- **D6 — Owner (ratified): the wordmark is the literal string "LUMI Style"**,
  stated in prose, not just markup.
- **D7 — The footer's runs share one baseline**, held by a new gated
  `footer_baseline` probe (ratio of the line box, threshold at half the
  shipped defect) with a planted failing fixture.
- **D8 — Performance (next release).** Measured: scripts ≈4 min portrait /
  ≈8 min landscape for 34 pages; the hour is the instructed serial loop. The
  fixes are the `Counter` hotspot in `inspect_layout.py` (~90s/geometry), one
  shared browser across its four Playwright contexts, and promoting the
  `_sources` parts-and-placeholders convention into `SKILL.md` as the
  multi-agent build protocol. AG-3's local/warn-only stance on timing stands.
- **D9 — Debug mode (own spec + release).** Reuses the perf-baseline step
  schema, the evidence no-human-verdict principle, the checkers' `--json`,
  and the review-scores self-score rules; English-only; written beside the
  output via `output_dir.py`; platforms reached through the registry only.
- **D10 — 16:9 proportion: evidence before rules.** Measure existing 16:9
  deliverables with the aspect/centerpiece/share probes and a key-number
  census; legislate only on the two-document threshold, with every number
  direction-marked per CLAUDE.md rule 4.

## Acceptance

The reviewed deliverable is rebuilt from scratch on the fixed rules (proper
scaffold, field globe live, one green system, promoted renderings, aligned
footer, "LUMI Style"), passes the full check suite including
`--deliverable`, and each of the seven reported defects is re-verified at the
pixel level. End-to-end build time is measured against the ten-minute
ceiling with the multi-agent protocol, and the debug mode's first real log is
written during that rebuild.
