#!/usr/bin/env python3
"""The verdict on a PR's check rollup: every job, never any job.

    python3 scripts/lib/ci_rollup.py "IN_PROGRESS/,COMPLETED/SUCCESS"   -> pending

WHY THIS EXISTS. `scripts/ops/ci_wait.sh` judged the rollup with a bash
substring match, `*COMPLETED/SUCCESS*`, so one finished job made the whole PR
"Passed" while the required job was still running. PR #204 (2026-09-02): the
rollup read `IN_PROGRESS/,COMPLETED/SUCCESS,COMPLETED/SUCCESS`, the script
printed Passed, and `gh pr merge` refused. The judgement is a function now,
with the four answers named, and the shell script only routes to them.

The input is what `gh pr view --json statusCheckRollup` prints through the
script's jq: one `STATUS/CONCLUSION` per check, comma-separated. An Actions
job reads `COMPLETED/SUCCESS`; a commit-status context has only a state and
reads it twice, `SUCCESS/SUCCESS`.

The third answer (convention 11): an empty rollup — no checks registered yet
— is `pending`, never `pass`. Absence of evidence is not a green.
"""
from __future__ import annotations

import argparse
import sys

PASSING = {"SUCCESS", "SKIPPED", "NEUTRAL"}
FAILING = {"FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
CANCELLED = {"CANCELLED", "STALE"}


def verdict(rollup: str) -> str:
    """`pass` | `fail` | `cancelled` | `pending`, over EVERY check in the rollup.

    Any failed check is `fail` even while others still run — a red job is a
    defect regardless of the queue. Any cancelled check, with none failed, is
    `cancelled` (re-run once; it is an infrastructure symptom). `pass` needs
    every check finished with a passing conclusion and at least one check at
    all. Everything else is `pending`.
    """
    checks = []
    for raw in rollup.split(","):
        raw = raw.strip()
        if not raw:
            continue
        status, _, conclusion = raw.partition("/")
        status, conclusion = status.strip().upper(), conclusion.strip().upper()
        done = status == "COMPLETED" or (status == conclusion and status != "")
        checks.append((done, conclusion))
    if not checks:
        return "pending"
    concluded = {c for done, c in checks if done}
    if concluded & FAILING:
        return "fail"
    if concluded & CANCELLED:
        return "cancelled"
    if all(done and c in PASSING for done, c in checks):
        return "pass"
    return "pending"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("rollup", nargs="?", default="",
                    help="comma-separated STATUS/CONCLUSION per check, as ci_wait.sh builds it")
    a = ap.parse_args(argv)
    print(verdict(a.rollup))
    return 0


if __name__ == "__main__":
    sys.exit(main())
