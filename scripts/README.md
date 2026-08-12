# scripts/ — the map

Five drawers plus one front door. Every script runs as
`python3 scripts/<drawer>/<name>.py` from the repo root; bare-name sibling
imports resolve through the canonical bootstrap block each importing script
carries (the `bootstrap` guard in check_repo enforces it, and the
`script paths` guard fails any prose or config that cites a path which no
longer exists — including paths BUILT from pieces).

```
preflight.py    the front door: runs exactly what CI runs, read from ci.yml.
                Deliberately at the top level — it is the command a person
                types most, and it depends on nothing here.

lib/            imported, never gates by itself
  geo_projection  the orthographic maths (the golden grid holds its JS port)
  geo_frame       topology decode, great circles, ring classification
  color_math      the ONE sRGB/WCAG implementation (strict-typed from birth)
  css_tokens      the ONE CSS custom-property reader (ditto)
  lock            the brand-lock verifier (LOCKED.json's teeth)
  deliverable_registry  the ONE kind->checker map (both consumers below)

render/         geometry becomes SVG
  globe_svg       a static globe frame; re-exports geo_frame for its callers
  regionmap_svg   the flat region map
  sea_route       lanes routed over water by construction (Dijkstra on a mask)

build/          generators — each --check byte-compares its outputs in CI
  build_brand · build_entrypoints · build_fixtures · build_geography ·
  build_region_palette · build_trade_registry · build_worldmap ·
  embed_font · embed_globe · embed_icons · embed_regionmap

check/          the gates
  check_repo      the guard hub (CHECKS tuple is the authority on what runs)
  check_evidence  the evidence gate: operator checks become recorded executions
  check_fixtures  the checkers checked against tracked fixtures
  check_globe     globe maths + the JS port under bare node
  check_js        node --check over every JS surface, embedded probes included
  check_prose · check_design · inspect_layout   deliverable checkers (M / D /
                  rendered-layout; inspect_layout needs local Playwright)

ops/            operator tools
  run_conformance  the cross-agent task suite (validate runs in CI)
  export_pdf · output_dir · new_deck · review_scores
  ci_wait.sh · emergency_merge.sh   the CI-outage runbook pair; the trusted
                  emergency closure = check/check_repo.py + everything in lib/
```

Import edges (who depends on whom): everything in render/ and half of
build/ sits on `lib/geo_*`; the checkers sit on `lib/color_math` and
`lib/css_tokens`; `check/check_globe` additionally imports both renderers
and `build/embed_globe`; `ops/run_conformance` and `check/check_fixtures`
reach the deliverable checkers only through `lib/deliverable_registry`.
Nothing imports `ops/` and nothing in `lib/` imports anything local except
`geo_frame → geo_projection`.

History note: this tree was flat (35 files) until 0.1.438–0.1.440. The
migration story, including the four silent-failure shapes it surfaced and
the guards that now prevent them, is in the CHANGELOG entries for those
releases and `specs/2026-08-13-audit-restructure-design.md`.
