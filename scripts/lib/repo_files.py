#!/usr/bin/env python3
"""Asking git what this repository holds, in one place.

WHY THIS EXISTS. Sixteen invocations, three identical `git(*args)` helpers
copied into three files, and thirteen spellings of `git ls-files` whose FAILURE
handling disagreed. Most said the right thing — *a scan that did not run is not
a scan that passed* — and two did not: `_json_manifests`, which feeds the
English-only red line, returned an empty list when git could not be asked, so
the guard scanned nothing and printed exactly what it prints on a clean tree
(FM-24). A guard that cannot look must say so.

`-z` ALWAYS. Callers split on newlines — a filename bug waiting for a filename
with a newline in it — and one shared reader makes the safe spelling the only
spelling. How many there were is not written here: the first version of this
sentence said five, a review counted nine, and three of them survived the
release that claimed to have moved them all, because the untracked listing had
no reader to move to. It has one now.

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


def repo_root(root: pathlib.Path | None = None) -> pathlib.Path:
    """-> the repository root, or the one the caller named.

    ONE HOME, because five modules grew an identical private `_root` in the
    same release — in the five modules written to end exactly that, and the
    register could not see it because no fact declared the name. One of the
    five had already diverged, anchoring on its own data file rather than on
    `SKILL.md`, so a synthetic tree carrying one and not the other resolved a
    different root there than in its four siblings.

    Not a bootstrap fact: the `ROOT` constants at the top of every script are
    computed before any sibling can be imported and stay where they are. This
    runs after the bootstrap, and is a function five modules call.
    """
    if root is not None:
        return root
    return next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / "SKILL.md").exists())


_root = repo_root


def run_git(*args: str, root: pathlib.Path | None = None,
            capture: bool = True) -> tuple[int, str]:
    """-> (exit code, stdout stripped). The one spelling of the invocation.

    `capture=False` lets the command write to the terminal — `git add`, `git
    commit` — and returns an empty string, so a caller that needs the output
    and a caller that needs the operator to SEE the output share one function
    instead of one of them keeping a private `subprocess.run`.
    """
    p = subprocess.run(["git", *args], cwd=_root(root),
                       capture_output=capture, text=True)
    return p.returncode, (p.stdout.strip() if capture else "")


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


def untracked_files(*pathspec: str, root: pathlib.Path | None = None,
                    what: str = "scan") -> tuple[list[str], str | None]:
    """-> (files present, not tracked and not ignored; a problem).

    The listing `check_evidence` needs — a brand-new script is exactly the kind
    of change that owes evidence, and `git diff` cannot see a file that was
    never tracked. It had nowhere to go when the other two moved, so it kept
    the newline split and read a FAILED listing as a clean tree, inside the
    evidence gate.
    """
    args = ["ls-files", "--others", "--exclude-standard", "-z"]
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
