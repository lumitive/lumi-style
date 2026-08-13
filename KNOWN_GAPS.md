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
