# Known gaps

The queryable ledger of known defects and unclosed verification gaps in this
package. One entry per gap, machine-checked by `check_repo.py`'s ledger guard:
ids unique, statuses legal (`open | fixed | declined`), `fixed` entries name
the closing release (whose CHANGELOG entry must cite the id), `declined`
entries carry a reason. Deferred work goes to `backlog/ideas-prd.md`
(IDEA-ids); recurring failure *shapes* go to `FAILURE_MODES.md` (FM-ids);
this file holds concrete, current gaps.

Tracked bugs live here, not in code comments — a `TODO` in a script citing a
GAP id fails CI. (The lumi project's KNOWN_GAPS rule, adopted 0.1.422.)

## GAP-001 · T1-deck fails on both scored conformance agents

- status: fixed
- opened: 0.1.422
- closed: 0.1.434
- surface: conformance/CONFORMANCE.md, references/storyline-templates.md,
  scripts/check/check_prose.py, tokens/lumi-layouts.css (historical)
- symptom: both agents ever scored (Claude Code, Cursor) fail the T1-deck
  task. DIAGNOSED at 0.1.433 by reproducing every verdict: the dominant
  failure (collision, both agents) was the skill's own window-keyed media
  block in tokens/lumi-layouts.css — both decks copied it verbatim — removed
  at 0.1.380, AFTER the decks were built; the instruments that see it
  (0.1.368/0.1.385/0.1.390) also postdate the builds. Two live skill defects
  found and fixed at 0.1.433: the [TO FILL] template-vs-D14 contradiction
  and M6 counting enumeration labels as ranges. The five remaining findings
  are agent-capability (unfit title reserves, inline role overrides, an
  overfull closing page shipped against the agent's own screenshot, a
  1-unit descender clip, one unsourced page).
- check: EXECUTED 2026-08-13 — T1 re-run on both agents against the 0.1.433
  rules: Cursor hand-driven by the operator (pass), Claude Code driven clean
  with the skill (pass; T2/T3 also pass). Scored with run_conformance.py,
  recorded via report --record (history rows pin skill 0.1.433); the
  scoreboard renders the current-skill runs and names the superseded ones.

## GAP-006 · Rules whose only home is outside references/, and a subset claim that is false

- status: fixed
- opened: 0.1.456
- closed: 0.1.480
- surface: references/operating-rules.md, SKILL.md, AGENTS.md,
  prompts/lumi-style-core.md, CLAUDE.md
- symptom: whole rule families were stated nowhere in `references/` — the
  debug-mode contract, the parallel-build protocol and its merge gate, the
  questions-come-once rule, the colophon-placement rule, the
  scaffold-never-fixture rule, the world-figure generation rule, the
  capability-tier rule, and the globe/map figure grammar living as comments in
  `region-palette.css`. And `CLAUDE.md` called `prompts/lumi-style-core.md` "a
  strict subset of `references/`" while that file carried rules of its own.
- check: **two of the families were homed by this refactor's other work before
  this entry was reached** — the capability-tier rule is now P-2's closing
  sentence in `PRINCIPLES.md`, and colophon placement is in
  `storyline-templates.md`. The remaining five share a category the original
  entry did not name: **they are all rules about how the agent works, not about
  what a deliverable is**, which is why none of them fitted the five existing
  reference files. `references/operating-rules.md` is their home, under P-2
  because each answers the same question — what makes the result trustworthy
  rather than merely finished.
- the false claim is corrected rather than made true: the core prompt is now
  described as **a derived restatement that may carry prompt-tier-only rules**,
  and those are named. Making it a strict subset would have meant deleting rules
  that exist because a prompt-tier agent has no tools, which is a worse answer
  than an accurate sentence.
- what is NOT closed by this: the globe/map figure grammar is still comments in
  `tokens/region-palette.css`. It is design prose in a token file, which is the
  same defect one file along, and it is recorded as **GAP-010** rather than
  quietly folded into a closure.

## GAP-010 · The globe and map figure grammar lives as comments in a token file

- status: open
- opened: 0.1.480
- surface: tokens/region-palette.css, references/design-rules.md
- symptom: how a globe or region map is composed — what the graticule is for,
  when a region carries a label, how the marks relate to the coastline — is
  written as comment prose inside `region-palette.css`. A token file is read by
  the build, not by a person forming a judgement, and design prose there is
  invisible to every reader of `references/` and to the `principle trace` guard.
- check: move the grammar into `design-rules.md` §1.2 (the mark and the map),
  leaving the token file with the values and a pointer. It is a prose move like
  GAP-007's, content-frozen, and the same multiset proof applies.

## GAP-009 · The shape library's relation classification is a third unclassified

- status: fixed
- opened: 0.1.473
- closed: 0.1.478
- surface: assets/shapes/tags.json
- symptom: the library shipped complete — all 206 units — but 70 carried
  `relation_from: unclassified`, so a third of it could not be reached by
  selection-by-relation. Usable, but not findable by the thing that finds
  shapes.
- check: all 70 are classified, and by the one method that has not been wrong
  here — **the rendered previews were opened and each shape classified from what
  it draws**. Contact sheets of twelve at a time; `relation_from: looked-at`.
  Two earlier attempts classified from the extraction's tags and from the page
  names, and both were wrong: the tags are sparse (they dropped the `flow-2`…
  `flow-6` and `cycle-2`…`cycle-8` families), and the names lie — `box` is a 2×2
  grid with a four-arrow cycle, `surround` is a large directional arrow, and
  `p012-footnotesource` is a 3×3×3 cube.
- what looking found that no name would have: the fourth and fifth sheets are
  almost entirely **chart primitives** — sorted bars, stacked areas over time,
  grouped columns, pie, histogram, scatter, Harvey balls — which is Zelazny's
  comparison set in drawable form. And `p157-illustrative` / `p158-disguised-
  client-example` are a set of **"illustrative / preliminary draft / for
  discussion only" stamps**, which is exactly what C4-③ asks a document to carry
  where an estimate appears.
- two categories were added rather than forcing everything into a relation:
  **`element`** is a basic form asserting no relation by itself (a plain block, a
  single circle) and **`apparatus`** serves the document rather than the argument
  (legend swatches, the disclosure stamps). Neither is a reject.

## GAP-008 · P-1 is stated wider than anything checks it

- status: fixed
- opened: 0.1.460
- closed: 0.1.481
- surface: references/design-rules.md §1-§2, scripts/check/check_design.py
- symptom: P-1 says the brand pack is the single source of visual and verbal
  identity. What was held was the palette. **Typography had no check at all**
  (verified: `check_design.py` contained no occurrence of `font-family`), and
  **layout was collected but not judged** — D9 gathered every page whose layout
  class the tokens do not define into an `unknown` list, and then its verdict
  was hard-coded to `True`. An agent inventing a seventeenth layout was caught
  by nothing.
- check: **D22 layout vocabulary (gates)** — a page claiming a layout `tokens/`
  does not define fails, on the same reasoning as D19: it is decidable, not a
  judgement about design. **D23 font count (reported)** — distinct font stacks
  against what the tokens declare, and **the ceiling is derived rather than
  written**: design-rules says two voices and the tokens declare two, so a
  literal `2` here would be quietly wrong the day a third is added. A test
  proves the ceiling moves with the tokens.
- the failing subject was already in the tree: `deck-degenerate` has fourteen
  pages carrying no layout class at all, and D9 had been collecting them for
  releases while reporting the run clean. **The evidence of the hole was sitting
  inside the fixture the whole time**, which is what a verdict hard-coded to
  pass does — it is the shape this repository calls a check that has only ever
  been seen passing.
- what remains under P-1 and is honestly not covered: whether a page's
  composition is *good*. That is a judgement, it belongs to C7 and to the eye,
  and no metric here claims it.

## GAP-007 · The reference files read as accretion, not as documents

- status: fixed
- opened: 0.1.456
- closed: 0.1.480
- surface: references/design-rules.md, references/storyline-templates.md,
  references/eval-rubric.md
- symptom: the owner read the rule set end to end and said a person cannot form
  a correct judgement from it, and the skeletons agreed: design-rules ran
  1, 1c, 1d, 2, 3, 4, 4b, 5, **7, 6** with its chart rules numbered 1-5, 6, 7,
  7b, 7c, 7d, 7e, 8, 8b; storyline-templates wedged its shared apparatus between
  Template 1 and Template 2; eval-rubric described three gating surfaces in
  three places with three vocabularies.
- check: **each of the four symptoms measured against the files, not recalled.**
  design-rules' top-level sections now read 1 2 3 4 5 6 7 8 and its chart rules
  6..14 after the inline 1-5 (0.1.457, content-frozen — the multiset of
  non-heading lines was identical before and after, and the same proof was run
  for storyline-templates at 0.1.458, whose four templates are now adjacent with
  the three universal sections following them). eval-rubric carries one gating
  notation in its target columns and **one** paragraph explaining what gates;
  the two other appearances of `(gates)` are quoting `check_design.grade()`'s
  own target string where that format is being discussed, which is a citation
  rather than a second vocabulary.
- what the reorder produced that the entry did not anticipate: the citation
  re-flow found **twenty-one live citations pointing at moved sections while all
  twenty-nine guards stayed green**, because `check_links` only sees markdown
  link syntax. The `section citations` guard was built for it and is the
  durable half of this closure — the next reorder cannot repeat this.

## GAP-004 · The Evals thresholds are gameable and calibrated on two documents

- status: open
- opened: 0.1.455
- surface: evals/thresholds.json, scripts/ops/eval_corpus.py
- symptom: a red-team pass cleared all four bars on the rejected corpus
  document with two mechanical rewrites that add no content — every `<li>`
  re-tagged as `.vows` markup, and one decorative rect-only SVG per prose page.
  The two metrics that saw it (`rect_only_share` 0.667, `shape_kinds_min` 1)
  had been demoted to reported for not separating a two-document corpus.
  Separately: the sales column is calibrated from a REJECTED document only —
  there is no accepted sales document — so those cells say where a bar could
  sit, not where it should. The bars therefore report and do not gate.
- check: the agreement study. Score the deliverables already on the operator's
  machine against the owner's recorded H1-H6 review scores and publish the
  correlation per threshold. A bar that does not track her judgement across ten
  documents is not measuring what she measures, however cleanly it separates
  two. `references/eval-rubric.md`'s own promotion rule asks for the same
  thing: two releases of real documents read against a metric before it gates.

## GAP-005 · Three of the owner's four deliverable categories have no accepted reference

- status: open
- opened: 0.1.455
- surface: evals/thresholds.json, references/storyline-templates.md
- symptom: only `training` has a document on record as meeting the product
  requirement. `sales` has a rejected one; `consulting` has none outside
  synthetic conformance decks; **product introduction has no genre at all** —
  the phrase appears nowhere in SKILL.md, references/ or scripts/, and the
  nearest fit (`marketing`) has no skeleton and cannot be scaffolded. Nine of
  twenty threshold cells therefore read `provisional`, and `internal`'s figure
  floor is `declined` outright because the only real internal document argues
  in prose and clears every gate.
- check: an accepted document per category, or a recorded decision that a
  category maps onto an existing genre. Until then the provisional cells are
  reasoned, not measured, and the file says so per cell.

## GAP-003 · The conformance history's producer path has no automated test

- status: fixed
- opened: 0.1.431
- closed: 0.1.433
- surface: scripts/ops/run_conformance.py (report --record)
- symptom: conformance_fresh() is tested against hand-written rows, but
  nothing tests that `report --record` produces rows of that shape — the
  agent/task key split, the digest pinning, the idempotency claim. A
  one-sided producer/consumer contract is FM-07's shape. Mitigations that
  keep this a 5-not-an-8: `validate` schema-checks the history in CI, and a
  malformed or under-grouped row reads as stale (fail-closed).
- check: python3 -m pytest tests/test_record_producer.py — drives the real
  main() against a synthetic ROOT (stubbed registry, task, run dir); closing
  it found one defect: a corrupt scores.json crashed the report merge loop
  with a traceback before the --record block's own does-not-parse guard could
  fire, so that guard was unreachable (fixed with the test)

## GAP-002 · Five checks CI cannot run are verified by prose

- status: fixed
- opened: 0.1.422
- closed: 0.1.425
- surface: scripts/check/inspect_layout.py, scripts/check/check_prose.py,
  scripts/check/check_design.py, scripts/check/check_globe.py, scripts/ops/run_conformance.py
- symptom: the layout gates, full-deliverable prose/design modes, the globe's
  JS half and conformance runs need a browser or an operator; their results
  were recorded as sentences in release notes — claims, not evidence. 0.1.415
  reported "all gates green" on eight of seventeen.
- check: python3 scripts/check/check_evidence.py --check (red in CI since 0.1.425:
  an operator check is a recorded execution with a digest, or the release
  does not ship)
