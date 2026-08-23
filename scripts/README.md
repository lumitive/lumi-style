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
  markup          the ONE HTML reader (pages, bodies, agenda vocabulary)
  gating          which metrics gate, read from evals/gates.json
  gate_registry   that register's reader: family, since, severity
  shipped         which side of the repository split a file is on
  state_dir       where an operator's stores live ($LUMI_STATE / ~/.lumi)
  trace_store     the ONE trace-store resolver, writer and readers alike

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
  export_pdf · output_dir · new_deck · review_scores · debug_log
  ci_wait.sh · emergency_merge.sh   the CI-outage runbook pair; the trusted
                  emergency EXECUTION closure = check/check_repo.py +
                  color_math/css_tokens/lock/deliverable_registry from lib/ +
                  ops/review_scores.py (the subprocess) — the closure test
                  parses the .sh and holds it to check_repo's real imports
```

Import edges (who depends on whom): all of render/ and two of build/
(build_geography, build_worldmap — three counting build_brand via
globe_svg) sit on `lib/geo_*`; check_repo and check_design sit on both `lib/color_math` and
`lib/css_tokens` (inspect_layout on color_math alone); `check/check_globe` additionally imports both renderers
and `build/embed_globe`; `ops/run_conformance` and `check/check_fixtures`
INVOKE the deliverable checkers only through `lib/deliverable_registry`
(run_conformance and ops/export_pdf additionally import `check_prose` for
its GENRES constant). `ops/new_deck` imports `build/embed_font`,
`build/embed_globe` and `build/embed_icons` — the scaffold embeds what it
tells an author to embed — and `build/build_fixtures` imports `ops/new_deck`
back, for the one function that prepares the brand mark, so that the fixture
and the scaffold cannot disagree about how it is embedded. **That pair is a
cycle waiting to happen**: `new_deck` reads `fixtures/deck-pass.en.html`, the
artifact `build_fixtures` generates, so its `FIXTURE` read stays inside
`preamble()` and must never move to module scope — at module scope the
fixture generator could not import while the fixture was absent or stale.
Nothing else imports `ops/` (tests do). `lib/` modules DO import each other —
`geo_frame → geo_projection`, `checker_report → deliverable_registry`,
`gating → gate_registry`, `trace_schema → deliverable_registry`, and
`corpus`/`trace_store` → `state_dir` — each of them a shared definition with one
owner, which is what `lib/` is for. What no module in it may do is import from
`ops/`, `check/` or `build/`.

History note: this tree was flat (36 files, counting the registry that
arrived with the hardening) until 0.1.438–0.1.440. The
migration story, including the four silent-failure shapes it surfaced and
the guards that now prevent them, is in the CHANGELOG entries for those
releases and `specs/2026-08-13-audit-restructure-design.md`.
