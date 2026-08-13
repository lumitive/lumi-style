#!/usr/bin/env python3
"""Run the check scripts against the tracked fixtures and assert the verdicts.

This is the regression test the checkers have never had. It invokes them as
subprocesses rather than importing them, so what gets tested is the contract a
user actually meets: argv parsing, the --json shape, and above all the exit code.

The broken fixture is the point. `deck-pass` proves a clean document is not
flagged; only `deck-broken` can prove the check still *fires*, and it asserts
which finding fired rather than merely that the run failed. A check that fails
for the wrong reason is not a check that passed.

And asserting a verdict is not the same as EXERCISING it. Until 0.1.390 this
suite asserted every metric on both fixtures and thirteen of eighteen design
verdicts read `ok` on both, so a checker rewritten to `return "ok"` would have
passed the regression test whose stated purpose is to catch that. Coverage is
computed now — see coverage_report — and a graded verdict with no failing case
fails this run.

Takes a couple of minutes locally, because it now drives a headless Chromium
over three fixtures at four geometries each. It still cannot run in CI, and it
says so with a count rather than passing quietly.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---

from deliverable_registry import checker_path  # noqa: E402

FIXTURES = ROOT / "fixtures"
# The kind->checker map lives in deliverable_registry (one copy; its
# docstring carries the FM-07 story).

# inspect_layout needs a headless Chromium, which CI does not have. That is a
# stated posture in CLAUDE.md, not an oversight, so the runner asserts it where
# a browser exists and SKIPS LOUDLY where one does not — never silently, because
# a suite that reports "all verdicts as expected" while the browser gates went unrun is
# the same defect 0.1.350 removed from inspect_layout itself.
LAYOUT_ARGV = ["--deliverable", "--no-sheet"]


def browser_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


def run(kind: str, args: list[str], path: pathlib.Path):
    proc = subprocess.run(
        [sys.executable, str(checker_path(kind)), str(path), "--json", *args],
        capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, None


def verdicts_of(report) -> dict:
    if isinstance(report, list) and report:
        report = report[0]
    return (report or {}).get("verdicts", {}) or {}


def coverage_report(collected, skipped_kinds) -> list[str]:
    """Say which verdicts have a case that fails, and refuse the ones that do not.

    This is the assertion the suite was missing. Until 0.1.390 every metric was
    asserted on both fixtures, and thirteen of eighteen design verdicts plus four
    of seven prose verdicts read `ok` on both — so a checker rewritten to
    `return "ok"` would have passed the regression suite whose stated purpose is
    to catch exactly that. Asserting a verdict is not the same as exercising it.

    A metric whose TARGET is literally "reported" cannot fail by construction and
    is counted separately rather than excused silently. That distinction is why
    the checkers now emit `targets` beside `verdicts`: without it this function
    would have to carry its own list of which metrics are graded, and a list like
    that goes stale the release after it is written.

    `n/a` counts as exercised. A reported metric that goes n/a where a document
    has no figures to measure still proves the checker is looking.

    Takes the reports main() already collected rather than re-running anything.
    Re-running doubled a suite that now drives a browser over three fixtures at
    four geometries each, and the run stopped finishing inside two minutes.
    """
    graded: dict[str, bool] = {}
    reported: dict[str, bool] = {}
    exercised = set()
    for (fixture, kind), report in collected.items():
        base = kind.split("@")[0]
        # inspect_layout has no per-metric targets because every one of its
        # findings gates: what it emits is the decidable subset, and the
        # judgements that are merely reported never reach `verdicts` at all.
        targets = report.get("targets")
        if targets is None and base != "layout":
            return [f"{fixture} [{kind}]: the report carries no 'targets', so "
                    f"coverage cannot be computed; a checker that stops "
                    f"declaring its targets disables this assertion"]
        targets = targets or {}
        for metric, verdict in (report.get("verdicts") or {}).items():
            # Substring, not equality: M1's target reads ">=70% (reported)"
            # because the number is worth printing even though it never gates,
            # and an equality test filed it as graded and then demanded a
            # failing case it cannot have.
            bucket = reported if "reported" in targets.get(metric, "") else graded
            bucket[metric] = True
            if verdict != "ok":
                exercised.add(metric)

    missing = sorted(m for m in graded if m not in exercised)
    n_rep_ex = sum(1 for m in reported if m in exercised)
    print(f"note  coverage: {len(graded) - len(missing)}/{len(graded)} graded "
          f"verdicts have a fixture that fails them; {len(reported)} are "
          f"reported and cannot fail ({n_rep_ex} exercised via n/a)")
    if skipped_kinds:
        # Loud, and it names the count. The acceptance for this move is that the
        # number of gates it could not assert is ZERO where a browser is present.
        print(f"note  SKIPPED {len(skipped_kinds)} rendered run(s) — no Chromium "
              f"importable, so inspect_layout's gates were NOT asserted here. "
              f"This run did not test them. pip install playwright && "
              f"playwright install chromium")
    if missing:
        return [f"{m} is graded and no fixture fails it — the suite cannot tell it "
                f"from a metric rewritten to return ok" for m in missing]
    return []


def main() -> int:
    spec = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
    errors = []
    # Every report, keyed by (fixture, kind), so coverage_report reads what was
    # already run instead of running it again.
    collected, skipped_kinds = {}, set()
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
            errors.append(f"{fixture}: missing; run scripts/build/build_fixtures.py")
            continue
        for kind, expect in checks.items():
            # "prose@training" runs check_prose a second time under another
            # genre; the suffix only names the run. Without this, M9's
            # training binding had no asserted run anywhere and a revert of
            # the genre pair passed CI.
            if kind.split("@")[0] == "layout" and not browser_available():
                skipped_kinds.add(kind)
                continue        # reported loudly by coverage_report below
            code, report = run(kind.split("@")[0], expect.get("argv", []), path)
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
            collected[(fixture, kind)] = report
            actual = verdicts_of(report)
            for metric, want in expect.get("verdicts", {}).items():
                got = actual.get(metric)
                if got != want:
                    errors.append(f"{label}: {metric} is {got!r}, expected {want!r}")
            # EVERY VERDICT A CHECKER EMITS MUST BE NAMED HERE. The loop above
            # walks the DECLARED keys, so a verdict nobody declared was never
            # compared — and two had been living that way: `starved_column`
            # since 0.1.412 and `footer_baseline` from the release that added
            # it, both green in every run and asserted by nothing. That is
            # FM-01 one level up: not a check that cannot fail, but a check
            # whose result nobody reads. Declaring a verdict is cheap; the
            # drift is silent, so the guard is mechanical.
            undeclared = sorted(set(actual) - set(expect.get("verdicts", {})))
            if undeclared:
                errors.append(
                    f"{label}: {', '.join(undeclared)} — emitted by the checker "
                    f"and named by no expected verdict, so nothing compares it. "
                    f"Add it to fixtures/expected.json with the value this "
                    f"fixture should produce.")
            # A document too thin to grade is not a document that passed.
            # `allow_na` names the metrics whose n/a is CORRECT rather than
            # decay — the Chinese pair on an English deck is n/a because the
            # document is not Chinese, and reading that as a decayed fixture
            # would push someone to delete the guard instead of scoping it.
            allowed = set(expect.get("allow_na", []))
            for forbidden in expect.get("forbid_verdicts", []):
                for metric, got in actual.items():
                    if metric in allowed:
                        continue
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

    # The export floor, executed rather than trusted: --scale below 2 must be
    # refused, and the refusal happens before any browser work (the check sits
    # ahead of the playwright import), so this runs in CI with no Chromium.
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ops" / "export_pdf.py"),
         str(FIXTURES / "deck-pass.en.html"), "--png", "--scale", "1"],
        capture_output=True, text=True)
    if proc.returncode != 2 or "floor" not in proc.stderr:
        errors.append(
            f"export_pdf.py did not refuse --scale 1 by naming the floor "
            f"(exit {proc.returncode}); the 2K floor is prose again")

    errors += coverage_report(collected, skipped_kinds)

    for err in errors:
        print(f"FAIL  {err}")
    if not errors:
        n = sum(len(v) for v in (c for c in spec["fixtures"].values()))
        print(f"ok    {len(spec['fixtures'])} fixtures, {n} check runs plus the "
              f"export floor, all verdicts as expected")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
