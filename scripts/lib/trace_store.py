"""Where a trace lives — one answer, for the writer and for every reader.

`scripts/ops/trace.py` honours `LUMI_TRACES`; `scripts/ops/ledger.py` resolved
`ROOT/evals/traces` on its own and did not. Setting the variable therefore sent
the writer somewhere the reader never looked, and the ledger reported an empty
store rather than an error — the shape a guard cannot catch, because both sides
are individually correct.

Not importable as `trace`: the canonical bootstrap APPENDS to `sys.path` so the
standard library always wins, and the standard library has a `trace` module.
A reader that tried the obvious import would get stdlib's and fail in a way
that has nothing to do with traces.
"""
from __future__ import annotations

import json
import os
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import state_dir  # noqa: E402

# The fallback is not decoration: a synthetic tree built by a guard test has no
# SKILL.md, and a bare `next()` raises StopIteration from an IMPORT — a
# traceback with nothing about traces in it. Same shape corpus.py and
# state_dir.py carry, for the same reason.
ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "SKILL.md").exists()),
            pathlib.Path(__file__).resolve().parents[2])


def traces_dir(root: pathlib.Path | None = None) -> pathlib.Path:
    """-> the trace store. `LUMI_TRACES` redirects it (tests, dry runs).

    The default is this checkout's tracked directory when it has one, because
    a trace that is not kept is not a record — and the operator state directory
    when it does not, because an installed skill has no `evals/`. `root` is the
    caller's, so a synthetic tree can be pointed at.
    """
    override = os.environ.get("LUMI_TRACES")
    if override:
        return pathlib.Path(override)
    return state_dir.store("traces", in_repo=("evals", "traces"), root=root or ROOT)


# The day the suite stopped writing into the tracked store. Nothing pytest
# wrote can be dated after it, so the population `suite_artifact` describes is
# CLOSED and finite — which is what makes a shape heuristic tolerable at all.
SUITE_LEAK_STOPPED = "2026-08-26"


def suite_artifact(t) -> bool:
    """A trace the test suite wrote, not a build anybody made.

    Until the suite got its own store, `tests/test_fewer_round_trips.py` drove
    `build.py` with no environment, so every run of pytest opened a trace of a
    throwaway two-page scaffold in the TRACKED store. `preflight.py` runs the
    suite and `release.py` stages with `git add -A`, so they were committed.

    **WHAT THIS CANNOT DISTINGUISH, said plainly because the first version of
    this docstring claimed the opposite.** It said four conditions together
    protect a real build. They do not: `trace.py cmd_open` sets `pages=0`,
    `closed_at=None` and `recipe_hash=None` on EVERY trace it opens, and
    `entry_path == "B"` is what most real builds use — so three of the four are
    just the initial state of any trace, and a real path-B build abandoned
    before `annotate --recipe` ran matches exactly. What actually separates the
    two populations is the date, and it only works because the leak has a stop:
    after `SUITE_LEAK_STOPPED` the suite writes elsewhere, so nothing written
    from that day on can be one of these however it is shaped.

    Measured when this was written: 182 of 199 build records matched, across
    sixteen distinct `skill_version`s (not sixteen releases — the span is
    0.1.532 and then most of 0.1.586-0.1.605).

    SET ASIDE, not deleted — by this function. `--with-suite-artifacts` puts
    them back everywhere, including in `--json` and `--board`.

    The 182 measured above WERE deleted, at 0.1.632, by the owner's decision:
    they were pytest's own build traces, records of nothing that happened, and
    keeping them meant keeping a denominator every reader had to be warned
    about. This classifier stays because the next test run writes more. What
    changed is that setting one aside is no longer the end of its life, and
    this paragraph said the opposite for one release.
    """
    if not isinstance(t, dict):
        return False
    return (t.get("source") == "build"
            and t.get("entry_path") == "B"
            and not (t.get("pages") or 0)
            and not t.get("recipe_hash")
            and not t.get("closed_at")
            and (t.get("opened_at") or "") < SUITE_LEAK_STOPPED)


def load(include_suite_artifacts: bool = False):
    if not traces_dir().exists():
        return []
    out = []
    for path in sorted(traces_dir().glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    if include_suite_artifacts:
        return out
    return [t for t in out if not suite_artifact(t)]


def set_aside_count() -> int:
    """-> how many records the filter is holding back, for the disclosure."""
    return sum(1 for t in load(True) if suite_artifact(t))
