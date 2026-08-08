#!/usr/bin/env python3
"""Run the check scripts against the tracked fixtures and assert the verdicts.

This is the regression test the checkers have never had. It invokes them as
subprocesses rather than importing them, so what gets tested is the contract a
user actually meets: argv parsing, the --json shape, and above all the exit code.

The broken fixture is the point. `deck-pass` proves a clean document is not
flagged; only `deck-broken` can prove the check still *fires*, and it asserts
which finding fired rather than merely that the run failed. A check that fails
for the wrong reason is not a check that passed.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
SCRIPTS = {"prose": "check_prose.py", "design": "check_design.py"}


def run(script: str, args: list[str], path: pathlib.Path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), str(path), "--json", *args],
        capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, None


def verdicts_of(report) -> dict:
    if isinstance(report, list) and report:
        report = report[0]
    return (report or {}).get("verdicts", {}) or {}


def main() -> int:
    spec = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
    errors = []
    # A suite with nothing to run is not a suite that passed. This printed
    # "ok 0 fixtures, 0 check runs" and exited 0 on an empty spec, which is the
    # inspect_layout defect of 0.1.350 one level up.
    if len(spec.get("fixtures", {})) < 2:
        errors.append(f"expected.json declares {len(spec.get('fixtures', {}))} "
                      f"fixtures; the suite needs at least the passing one and the "
                      f"broken one, or it cannot tell a working check from an "
                      f"unconditional ok")

    for fixture, checks in spec["fixtures"].items():
        path = FIXTURES / fixture
        if not path.exists():
            errors.append(f"{fixture}: missing; run scripts/build_fixtures.py")
            continue
        for kind, expect in checks.items():
            code, report = run(SCRIPTS[kind], expect.get("argv", []), path)
            label = f"{fixture} [{kind}]"
            if code != expect["exit"]:
                errors.append(f"{label}: exit {code}, expected {expect['exit']}")
            if report is None:
                errors.append(f"{label}: emitted no parseable --json report")
                continue
            # Unwrap once. `verdicts_of` unwrapped a copy, so `report` stayed a
            # list and the detail lookup below crashed on it.
            if isinstance(report, list) and report:
                report = report[0]
            actual = verdicts_of(report)
            for metric, want in expect.get("verdicts", {}).items():
                got = actual.get(metric)
                if got != want:
                    errors.append(f"{label}: {metric} is {got!r}, expected {want!r}")
            # A document too thin to grade is not a document that passed.
            for forbidden in expect.get("forbid_verdicts", []):
                for metric, got in actual.items():
                    if got == forbidden:
                        errors.append(
                            f"{label}: {metric} came back {forbidden!r} — the fixture "
                            f"has decayed below the floor that metric needs to grade")
            for metric, needles in expect.get("contains", {}).items():
                # Scoped to the metric's own detail. This searched the whole
                # serialized report, so the metric key was decorative: keying it
                # to a name no checker emits still passed, in the one assertion
                # whose stated job is "a check that fails for the wrong reason is
                # not a check that passed".
                # check_prose reports detail under the metric's PREFIX —
                # M4_banned_hits is detailed in M4_detail — so the key is
                # derived, not assumed.
                key = f"{metric.split('_')[0]}_detail"
                detail = report.get(key)
                if detail is None:
                    errors.append(
                        f"{label}: contains names {metric!r}, but the report has no "
                        f"{key!r}; the assertion would search nothing")
                    continue
                blob = json.dumps(detail)
                for needle in needles:
                    if needle not in blob:
                        errors.append(
                            f"{label}: {metric} fired but its detail never mentions "
                            f"{needle!r}; a check that fails for the wrong reason is "
                            f"not a check that passed")

    for err in errors:
        print(f"FAIL  {err}")
    if not errors:
        n = sum(len(v) for v in (c for c in spec["fixtures"].values()))
        print(f"ok    {len(spec['fixtures'])} fixtures, {n} check runs, all verdicts as expected")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
