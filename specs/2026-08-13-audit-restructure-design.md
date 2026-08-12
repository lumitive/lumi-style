# The audit: cleanup, scripts/ physical reorganization, public-repo normalization — design

Date: 2026-08-13 · Written against 0.1.435 · Status: approved by the owner
(owner directive, 2026-08-13 — a documented case under maintenance
convention 2). The owner chose PHYSICAL subdirectories for scripts/ after
being shown the coupling cost. Companion plan:
`2026-08-13-audit-restructure-plan.md`.

## 1 · The case

Three owner findings: stale files accreting (an empty file named `1` at the
repo root, tracked since 0.1.387), 35 flat scripts hard for a human
architect to review, and a public repo whose naming and README predate its
own growth.

The audit that scoped this confirmed and extended the findings — and turned
up one live defect: **`emergency_merge.sh` is broken today.** Its
`PYTHONSAFEPATH=1` invocation of the trusted `check_repo.py` copy fails on
`import color_math` (a sibling import introduced at 0.1.420, after the
script's threat model was written), so the emergency path would misdiagnose
any PR as "real defect in the PR". The fix must copy the whole trusted
import closure and must APPEND to sys.path, never insert(0) — an insert
would put a PR-controlled directory ahead of the standard library,
resurrecting the `scripts/json.py` hijack the script's own comments
document.

## 2 · Decisions

**D1 — Physical subdirectories (owner decision).** `lib/ render/ build/
check/ ops/` plus `preflight.py` kept at the top level as the front door
(and so the pyproject S602 waiver path never moves). sea_route → render/
(domain cohesion with the geo/SVG space); lock → lib/ (check_repo's
non-stdlib closure becomes exactly the lib/ drawer, one directory for the
emergency copy).

**D2 — No Python packages; bare-name imports plus a canonical bootstrap
block.** Every script importing a sibling carries one uniform block that
walks up to the scripts/ root and appends it and its drawers to sys.path.
Rationale: CLIs run as `python3 scripts/check/x.py` need a bootstrap either
way; packages would silently disarm the mypy strict ratchet (bare module
names in the override) and contradict pyproject's stated position that
scripts/ is deliberately not a package. Append, never insert(0): stdlib and
the caller's environment always win; the emergency path's protection is the
trusted copies OVERWRITING the PR's files at the same paths, not path
ordering.

**D3 — Loudness before movement.** Nothing moves until every silent-failure
point is made loud: a new guard fails any `scripts/<path>` string in live
prose/config that does not resolve to a file (~180 mentions come under
machine control); the two non-recursive guard globs become recursive; the
evidence gate refuses TOUCH_MAP prefixes and OBLIGATIONS commands that point
at nothing (the ENTRY_STAMP precedent: a position pointing at nothing checks
nothing); a presence guard requires the bootstrap block wherever a sibling
import exists.

**D4 — Frozen history stays frozen.** CHANGELOG.md and specs/ keep old
paths forever; the path guard excludes them. Generated artifacts are never
hand-edited — their source literals in the builders change, `--check` gates
the regeneration.

**D5 — One lock ceremony.** lib/render/build move in a single release so
LOCKED.json is hand-rekeyed and `lock.py --update` runs exactly once, with
the three locked JS assets' comment citations updated in the same breath.

## 3 · Declined

- Packages/`__init__.py` (D2 rationale; recorded so it is not re-proposed).
- Rewriting CHANGELOG/specs path mentions (frozen history).
- A generated architecture map (the owner chose physical structure instead;
  a hand-written `scripts/README.md` ships with the final move release).
- Cleaning `conformance/results/` (evidence digests pin those artifacts) and
  touching the PR #85 worktree (owner's open decision).
