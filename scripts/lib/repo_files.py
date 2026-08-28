#!/usr/bin/env python3
"""Asking git what this repository holds, in one place.

WHY THIS EXISTS. Sixteen invocations, three identical `git(*args)` helpers
copied into three files, and thirteen spellings of `git ls-files` whose FAILURE
handling disagreed. Most said the right thing — *a scan that did not run is not
a scan that passed* — and two did not: `_json_manifests`, which feeds the
English-only red line, returned an empty list when git could not be asked, so
the guard scanned nothing and printed exactly what it prints on a clean tree
(FM-24). A guard that cannot look must say so.

`-z` ALWAYS. Five of the callers split on newlines, which is a filename bug
waiting for a filename with a newline in it; one shared reader makes the safe
spelling the only spelling.

The return shape is `(names, problem)` for the same reason `history.read_rows`
uses it: absence and inability are different answers, and what to DO about the
second belongs to the caller — a guard fails, a sweeper says nothing was swept.
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

import pathlib  # noqa: E402
import subprocess  # noqa: E402


def _root(root: pathlib.Path | None = None) -> pathlib.Path:
    if root is not None:
        return root
    return next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / "SKILL.md").exists())


def run_git(*args: str, root: pathlib.Path | None = None) -> tuple[int, str]:
    """-> (exit code, stdout stripped). The one spelling of the invocation."""
    p = subprocess.run(["git", *args], cwd=_root(root),
                       capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def _ls(args: list[str], root: pathlib.Path | None,
        what: str) -> tuple[list[str], str | None]:
    p = subprocess.run(["git", *args], cwd=_root(root),
                       capture_output=True, text=True)
    if p.returncode != 0:
        return [], (f"git {' '.join(args[:2])} failed "
                    f"({p.stderr.strip()[:80]}) — the {what} did not run, and "
                    f"a scan that did not run is not a scan that passed")
    return [f for f in p.stdout.split("\0") if f], None


def tracked_files(*pathspec: str, root: pathlib.Path | None = None,
                  what: str = "scan") -> tuple[list[str], str | None]:
    """-> (every file git tracks, or those matching `pathspec`; a problem)."""
    args = ["ls-files", "-z"]
    if pathspec:
        args += ["--", *pathspec]
    return _ls(args, root, what)


def ignored_files(*pathspec: str, root: pathlib.Path | None = None,
                  what: str = "scan") -> tuple[list[str], str | None]:
    """-> (files present and IGNORED, so not tracked and not accidental).

    A repository that has git and cannot be asked is not a repository with
    nothing to report, which is why this shares the shape above.
    """
    args = ["ls-files", "-o", "-i", "-z", "--exclude-standard"]
    if pathspec:
        args += ["--", *pathspec]
    return _ls(args, root, what)
