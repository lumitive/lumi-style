#!/usr/bin/env python3
"""Run exactly what CI runs, locally, before pushing.

    python3 scripts/preflight.py          # every CI step, stop-on-first-failure off
    python3 scripts/preflight.py -x       # stop at the first failure

WHY THIS EXISTS. `check_repo.py` answers "is this change good" and is the thing
a person reaches for. It is one of FIFTEEN commands CI runs. So a release could
be — and was — reported locally as "all gates green" on the strength of eight of
them, pushed, and failed in CI on a generator check that had never been run.

The failure that produced this file: a shared value was added to a palette
generator, the generator was re-run, and its bare write refreshed one of the two
files it owns while its bare check verified both. `check_repo` does not invoke
that generator at all, so nothing local could have seen it.

THE COMMANDS ARE READ OUT OF `.github/workflows/ci.yml`, never listed here.
A copy of the list would drift from CI the moment a step was added, and this
file exists precisely because a hand-maintained idea of "everything" was wrong.
If it cannot parse the workflow it says so and exits non-zero, rather than
running a subset and printing a reassuring line — that failure mode is the one
this repository keeps rediscovering.

Standard library only, because there is no yaml module in it and this needs no
dependency to read fifteen `run:` lines.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/ci.yml"


def ci_commands(text):
    """-> [command] in workflow order, block scalars folded into one string.

    A hand-rolled reader for the one construct this workflow uses: `- run:` with
    either an inline command or a `|` block. It is deliberately strict — an
    unrecognised shape raises instead of being skipped, because a step silently
    dropped from a completeness check is worse than no check.
    """
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)- run:\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        indent, rest = m.group(1), m.group(2).strip()
        i += 1
        if rest and rest not in ("|", ">", "|-", ">-"):
            out.append(rest)
            continue
        if not rest:
            raise ValueError(f"`- run:` with no command and no block scalar at "
                             f"line {i}")
        block = []
        while i < len(lines):
            if not lines[i].strip():
                block.append("")
                i += 1
                continue
            if len(lines[i]) - len(lines[i].lstrip()) <= len(indent):
                break
            block.append(lines[i])
            i += 1
        if not block:
            raise ValueError(f"empty `- run: {rest}` block at line {i}")
        out.append("\n".join(block))
    if not out:
        raise ValueError("no `- run:` steps found; the workflow shape changed")
    return out


def label(cmd):
    one = " ".join(cmd.split())
    return one if len(one) <= 68 else one[:65] + "..."


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-x", "--exitfirst", action="store_true",
                    help="stop at the first failing step")
    args = ap.parse_args(argv)

    if not WORKFLOW.exists():
        print(f"FAIL  {WORKFLOW} not found — cannot know what CI runs")
        return 1
    try:
        cmds = ci_commands(WORKFLOW.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"FAIL  cannot read {WORKFLOW.name}: {exc}")
        print("      Refusing to run a subset. Fix the parser or the workflow.")
        return 1

    print(f"{len(cmds)} steps, read from {WORKFLOW.relative_to(ROOT)}\n")
    failed = []
    for n, cmd in enumerate(cmds, 1):
        start = time.monotonic()
        # shell=True, and it is the point rather than an oversight: these
        # strings ARE shell commands — CI hands them to a shell, one of them is
        # a multi-line py_compile with backslash continuations, and splitting
        # them into argv lists would run something other than what CI runs,
        # which is the one thing this file must not do. The input is a tracked
        # workflow file in this repository, executed by its own maintainer;
        # anyone who can edit it can already edit the scripts it invokes.
        p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True,
                           text=True)
        secs = time.monotonic() - start
        mark = "ok  " if p.returncode == 0 else "FAIL"
        print(f"{mark}  {n:2d}/{len(cmds)}  {label(cmd):<70} {secs:5.1f}s")
        if p.returncode != 0:
            failed.append((cmd, p))
            for line in (p.stdout + p.stderr).strip().splitlines()[-12:]:
                print(f"          {line}")
            if args.exitfirst:
                break

    print()
    if failed:
        print(f"{len(failed)} of {len(cmds)} steps failed. CI will fail the same way.")
        return 1
    print(f"all {len(cmds)} steps pass. This is what CI runs, so CI passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
