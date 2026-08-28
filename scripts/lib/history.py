#!/usr/bin/env python3
"""`conformance/history.json`, read in one place, with one discipline.

WHY THIS EXISTS. Every reader of this file answered a damaged one
differently. One checked absence, parse failure and shape and named which had
happened; one raised whatever `json` raised; one caught `JSONDecodeError` but
not `OSError` and never asked whether the result was a list; one — the
`validate` command, in the same file as two of the others — checked the shape
and not the OS; and the `record` path, the one that WRITES, caught nothing at
all, so a history damaged by a merge would have taken the run's own results down
with it after the run had been paid for.

`json.JSONDecodeError` subclasses `ValueError`, so a single `except ValueError`
around a parse turned "this file is a merge conflict" into "nothing is wrong".
A tracked file that two branches both append to is the likeliest thing in this
repository to arrive unparseable, and it is the only evidence store there is.

THE RETURN TYPE IS THE DISCIPLINE. `(rows, problem)` keeps three answers apart:
absent is `([], None)` — a first run has no rows to break — while unreadable and
not-a-list each come back with the sentence that says which. What a caller DOES
about a problem stays the caller's: the guard fails, the board refuses to score,
the recorder stops before it writes.
"""
from __future__ import annotations

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

import json  # noqa: E402
import pathlib  # noqa: E402

import repo_files  # noqa: E402 — one repository root

RELATIVE = "conformance/history.json"


_root = repo_files.repo_root


def path(root: pathlib.Path | None = None) -> pathlib.Path:
    return _root(root) / RELATIVE


def read_rows(root: pathlib.Path | None = None) -> tuple[list, str | None]:
    """-> (rows, problem). `problem` is None when the rows can be trusted."""
    hist = path(root)
    if not hist.exists():
        return [], None                    # a first run has no rows to break
    try:
        rows = json.loads(hist.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [], f"{hist} could not be read ({exc})"
    if not isinstance(rows, list):
        return [], (f"{hist} holds a {type(rows).__name__}, not a list of rows "
                    f"— `null`, a number and an object all parse as JSON")
    return rows, None
