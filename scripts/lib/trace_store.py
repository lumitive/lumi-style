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

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())


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
