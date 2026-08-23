#!/usr/bin/env python3
"""Run a deliverable checker and read its report — one implementation.

Four scripts grew private copies of the same two facts: how to invoke a checker
kind (`--genre` for prose, `--deliverable` plus a sheet choice for layout) and how to
parse what comes back (prose and design print a LIST of per-file dicts; layout
prints ONE dict with `verdicts` at the top and `unmeasured` beside it).
`run_conformance.score_checks` had both; `check_fixtures.verdicts_of` and
`debug_log.failing_verdicts` each had the parsing half; `trace.py`'s
`_checker_json` had the running half. Four copies of a contract is how the
0.1.463 sheet described H1-H6 for two releases after C1-C8 replaced them — the
defect class this repository has fixed twenty-six times, in the tooling that
exists to catch it.

The distinction this module must never lose (it is the whole reason trace.py's
copy exists): **a checker that could not speak is not a checker with nothing to
say.** `spoke=False` means the output was not a report — a crash, a timeout,
prose printed over the JSON. An honest empty report is `([], True)`. Consumers
that conflate them record a broken instrument as a clean run.
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
import subprocess  # noqa: E402
import sys  # noqa: E402

from deliverable_registry import checker_path  # noqa: E402


def checker_argv(kind: str, path, genre: str | None = None,
                 iterate: bool = False, sheet: bool = False,
                 against=None) -> list[str]:
    """The canonical invocation for one checker kind, in one place.

    The knowledge here used to live in `run_conformance.score_checks` alone,
    which is why every OTHER caller ran prose without `--genre` and graded
    every deliverable as sales material whatever it declared itself to be.

    `iterate` is the author's loop rather than the delivery check: every gate
    still runs, at the declared stage only. It is meaningless to the checkers
    that do not render, so it is silently theirs to ignore rather than an error
    — a caller looping over `kinds()` passes one flag, not a special case.
    """
    argv = [sys.executable, str(checker_path(kind)), str(path), "--json"]
    if kind == "prose" and genre:
        argv += ["--genre", genre]
    if kind == "layout":
        # `--deliverable` is the point: without it inspect_layout gates on
        # nothing. `--no-sheet` by default because nobody is watching a harness
        # run — but `sheet` exists because a person IS watching the last round,
        # and the contact sheet is the last gate this package has. Suppressing
        # it unconditionally meant the one-command path could not produce the
        # one artifact SKILL.md calls the final check, so every author ran
        # inspect_layout a second time to get it. Measured on one 2026-08 build:
        # 64 separate runs at 22 seconds each, against 6 of the one command.
        argv.append("--deliverable")
        if not sheet:
            argv.append("--no-sheet")
        if iterate:
            argv.append("--iterate")
        if against:
            # The previous round's reading. Only the renderer can compare
            # rendered geometry, so only the layout kind carries it.
            argv += ["--against", str(against)]
    return argv


def parse_report(stdout: str | bytes):
    """-> (reports, spoke). Both checker JSON shapes, one reader.

    `reports` is always a list of dicts (layout's single dict is wrapped), or
    None when `spoke` is False. An empty list is a checker that ran and graded
    nothing — real, and distinct from a crash.
    """
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", "replace")
    try:
        doc = json.loads(stdout)
    except ValueError:
        return None, False
    if isinstance(doc, list):
        return [r for r in doc if isinstance(r, dict)], True
    if isinstance(doc, dict):
        return [doc], True
    return None, False


def run_checker(kind: str, path, genre: str | None = None, timeout: int = 600,
                iterate: bool = False):
    """-> {kind, exit, spoke, reports}. Executes and parses; decides nothing.

    A timeout or unparseable output is `spoke=False` with the raw exit — the
    caller records that state rather than skipping it.
    """
    argv = checker_argv(kind, path, genre, iterate=iterate)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"kind": kind, "exit": None, "spoke": False, "reports": None}
    reports, spoke = parse_report(proc.stdout)
    return {"kind": kind, "exit": proc.returncode, "spoke": spoke,
            "reports": reports}


def first_verdicts(reports) -> dict:
    """-> the first report's verdict map, for single-file runs."""
    if not reports:
        return {}
    return (reports[0] or {}).get("verdicts", {}) or {}


def findings(reports) -> list[str]:
    """-> every non-ok fact in a parsed report, named the checker's own way.

    `n/a` is not a failure — the metric does not apply. `unmeasurable` and
    `unmeasured` are failures of a different kind: the check did not run, and
    a check that did not run is not a check that passed.
    """
    out: list[str] = []
    for report in reports or []:
        name = pathlib.PurePath(str(report.get("file", ""))).name
        prefix = f"{name}: " if name else ""
        if report.get("unmeasurable"):
            out.append(f"{prefix}unmeasurable — {report['unmeasurable']}")
        for metric, verdict in (report.get("verdicts") or {}).items():
            if verdict not in ("ok", "n/a"):
                out.append(f"{prefix}{metric} {verdict}")
        if report.get("unmeasured"):
            out.append(f"{prefix}{report['unmeasured']} check(s) could not be measured")
    return out
