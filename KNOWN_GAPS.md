# Known gaps

The queryable ledger of known defects and unclosed verification gaps in this
package. One entry per gap, machine-checked by `check_repo.py`'s ledger guard:
ids unique, statuses legal (`open | fixed | declined`), `fixed` entries name
the closing release (whose CHANGELOG entry must cite the id), `declined`
entries carry a reason. Deferred work goes to `Pipeline/ideas-prd.md`
(IDEA-ids); recurring failure *shapes* go to `FAILURE_MODES.md` (FM-ids);
this file holds concrete, current gaps.

Tracked bugs live here, not in code comments — a `TODO` in a script citing a
GAP id fails CI. (The lumi project's KNOWN_GAPS rule, adopted 0.1.422.)

## GAP-001 · T1-deck fails on both scored conformance agents

- status: fixed
- opened: 0.1.422
- closed: 0.1.434
- surface: conformance/CONFORMANCE.md, references/storyline-templates.md,
  scripts/check_prose.py, tokens/lumi-layouts.css (historical)
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

## GAP-003 · The conformance history's producer path has no automated test

- status: fixed
- opened: 0.1.431
- closed: 0.1.433
- surface: scripts/run_conformance.py (report --record)
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
- surface: scripts/inspect_layout.py, scripts/check_prose.py,
  scripts/check_design.py, scripts/check_globe.py, scripts/run_conformance.py
- symptom: the layout gates, full-deliverable prose/design modes, the globe's
  JS half and conformance runs need a browser or an operator; their results
  were recorded as sentences in release notes — claims, not evidence. 0.1.415
  reported "all gates green" on eight of seventeen.
- check: python3 scripts/check_evidence.py --check (red in CI since 0.1.425:
  an operator check is a recorded execution with a digest, or the release
  does not ship)
