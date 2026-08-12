#!/usr/bin/env python3
"""Run exactly what CI runs, locally, before pushing.

    python3 scripts/preflight.py          # every CI step, stop-on-first-failure off
    python3 scripts/preflight.py -x       # stop at the first failure

WHY THIS EXISTS. `check_repo.py` answers "is this change good" and is the thing
a person reaches for. It is ONE of the commands CI runs — how many is whatever
the workflow says today, never a number written here. So a release could be —
and was — reported locally as "all gates green" on the strength of eight of
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
dependency to read a workflow's `run:` lines.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/ci.yml"
PERF_BASELINE = ROOT / "releases" / "perf-baseline.json"


def load_baseline():
    """-> {command_sha256: seconds}, empty when no baseline is recorded."""
    if not PERF_BASELINE.exists():
        return {}
    try:
        doc = json.loads(PERF_BASELINE.read_text(encoding="utf-8"))
        return {s["command_sha256"]: float(s["seconds"])
                for s in doc.get("steps", [])}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        print("note  releases/perf-baseline.json does not parse; timing "
              "comparison skipped (re-record with --timing-update)")
        return {}


def slow_bound(baseline_secs):
    """WARN above max(2x baseline, baseline + 5s): the absolute floor keeps
    sub-second steps from crying wolf. Warn-only and local-only by design —
    a baseline is one machine's number, and a cross-machine fail-gate fails
    for reasons unrelated to the code (FAILURE_MODES.md AG-3)."""
    return max(2 * baseline_secs, baseline_secs + 5.0)


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
    ap.add_argument("--timing-update", action="store_true",
                    help="record this run's per-step wall time as the local "
                         "performance baseline (releases/perf-baseline.json)")
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
    baseline = load_baseline()
    timings = []
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
        digest = hashlib.sha256(cmd.encode()).hexdigest()
        timings.append({"label": label(cmd), "command_sha256": digest,
                        "seconds": round(secs, 2)})
        mark = "ok  " if p.returncode == 0 else "FAIL"
        print(f"{mark}  {n:2d}/{len(cmds)}  {label(cmd):<70} {secs:5.1f}s")
        if digest in baseline and secs > slow_bound(baseline[digest]):
            print(f"          WARN slow: {secs:.1f}s vs {baseline[digest]:.1f}s "
                  f"baseline (bound {slow_bound(baseline[digest]):.1f}s) — "
                  f"informational, never a failure")
        if p.returncode != 0:
            failed.append((cmd, p))
            for line in (p.stdout + p.stderr).strip().splitlines()[-12:]:
                print(f"          {line}")
            if args.exitfirst:
                break

    print()
    if args.timing_update and failed:
        print("note  timing baseline NOT recorded: a failed step's short "
              "wall time must not become the bar")
    if args.timing_update and not failed:
        PERF_BASELINE.parent.mkdir(parents=True, exist_ok=True)
        PERF_BASELINE.write_text(json.dumps({
            "machine": sys.platform,
            "recorded": datetime.date.today().isoformat(),
            "steps": timings,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"recorded {len(timings)}-step timing baseline -> "
              f"{PERF_BASELINE.relative_to(ROOT)}")
    if failed:
        print(f"{len(failed)} of {len(cmds)} steps failed. CI will fail the same way.")
        return 1
    print(f"all {len(cmds)} steps pass. This is what CI runs, so CI passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
