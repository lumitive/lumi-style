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

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())


def traces_dir(root: pathlib.Path | None = None) -> pathlib.Path:
    """-> the trace store. `LUMI_TRACES` redirects it (tests, dry runs).

    The default is the tracked directory, because a trace that is not kept is
    not a record. `root` is the caller's, so a synthetic tree can be pointed at.
    """
    override = os.environ.get("LUMI_TRACES")
    return pathlib.Path(override) if override else (root or ROOT) / "evals" / "traces"
