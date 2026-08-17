#!/usr/bin/env python3
"""How much finished work has not left this machine.

This exists because of a measured failure, not a hypothesis. Forty releases —
0.1.457 through 0.1.496 — accumulated on a branch that was never pushed, had no
pull request, and had never been seen by CI, while `origin/main` sat at 0.1.456.
Every local check was green the whole time. Nothing in the repository could say
otherwise, because nothing asked.

The number is REPORTED and never gates. A gate here would stop a release the
author has good reason not to push yet, and the problem was never that somebody
decided to wait — it was that nobody was told how long they had been waiting.

One definition, two callers (`release.py` and `preflight.py`). A second copy of
this arithmetic is the shadow-math this repository forbids.
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import re
import subprocess
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import pathlib  # noqa: E402
import sys  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
# A release commit is one whose subject opens with its version. That is
# `check_commit_convention`'s rule, and reusing it means this counter cannot
# drift from what the repository calls a release.
RELEASE_SUBJECT = re.compile(r"^\d+\.\d+\.\d+ — ")


def _git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def _released_versions(ref):
    """-> {version} shipped in `ref`'s history, read from commit SUBJECTS."""
    rc, log = _git("log", "--format=%s", ref)
    if rc != 0:
        return None
    return {s.split(" — ", 1)[0] for s in log.splitlines()
            if RELEASE_SUBJECT.match(s)}


def unshipped():
    """-> (count, note) — release VERSIONS present here and not on origin/main.

    Compared by version, never by commit identity. This repository lands a
    multi-release branch with `gh pr merge --rebase`, because merge commits are
    disabled and squashing is forbidden — and a rebase gives every commit a new
    hash. A counter that asked `origin/main..HEAD` would therefore report the
    whole branch as unshipped forever, immediately after shipping it. Subjects
    survive a rebase, which is the same property `check_evidence.py` relies on
    to re-resolve a dangling diff base.

    `count` is None when the question cannot be asked: no `.git`, no
    `origin/main` (a fork's fresh clone, an offline checkout). None is not
    zero, and the note says which it is.
    """
    if not (ROOT / ".git").exists():
        return None, "no .git — nothing to compare"
    rc, _ = _git("rev-parse", "--verify", "--quiet", "origin/main")
    if rc != 0:
        return None, "no origin/main to compare against (fetch first)"
    here = _released_versions("HEAD")
    shipped = _released_versions("origin/main")
    if here is None or shipped is None:
        return None, "git could not read the commit log"
    subjects = sorted(here - shipped)
    rc, branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    rc_up, _ = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    where = ("this branch has no upstream — it exists only here"
             if rc_up != 0 else f"{branch} tracks a remote")
    return len(subjects), where


def report(stream=sys.stdout):
    """Print the count. Returns it, so a caller can decide to say more."""
    count, note = unshipped()
    if count is None:
        print(f"note  unshipped releases: not counted — {note}", file=stream)
        return None
    if count == 0:
        print("ok    unshipped releases: 0 — everything committed here is on "
              "origin/main", file=stream)
        return 0
    plural = "" if count == 1 else "s"
    print(f"note  unshipped releases: {count} release commit{plural} ahead of "
          f"origin/main; {note}.\n"
          f"      Forty once accumulated this way and CI had seen none of "
          f"them. This is a count, not a gate.", file=stream)
    return count


if __name__ == "__main__":
    report()
