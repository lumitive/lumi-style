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

- status: open
- opened: 0.1.422
- surface: conformance/CONFORMANCE.md, scripts/check_design.py, SKILL.md
- symptom: both agents ever scored (Claude Code, Cursor) fail the T1-deck
  task — collision and layout-gate findings on the produced deck. The
  scoreboard records it; nothing tracks it toward closure.
- check: python3 scripts/run_conformance.py score --run <run-dir>

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
