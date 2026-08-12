"""cell_spread — IDEA-8's render half, both directions.

The one distinction that matters: a verdict conflict that ALIGNS with
different build versions reads "skill changed between builds" and the latest
build governs; any conflict builds cannot explain stays UNSTABLE.
"""
import run_conformance


def _r(verdict, built=None, failed=()):
    return {"verdict": verdict, "built_version": built, "failed": list(failed)}


def test_single_pass():
    assert run_conformance.cell_spread([_r("pass")]) == ("pass", "pass")


def test_single_fail_carries_detail():
    cell, worst = run_conformance.cell_spread(
        [_r("fail", failed=["collision=FAIL"])])
    assert worst == "fail" and "collision=FAIL" in cell


def test_unanimous_runs_named():
    cell, worst = run_conformance.cell_spread([_r("pass"), _r("pass")])
    assert worst == "pass" and "2 runs, all pass" in cell


def test_conflict_same_build_is_unstable():
    cell, worst = run_conformance.cell_spread(
        [_r("fail", "0.1.400"), _r("pass", "0.1.400")])
    assert worst == "fail" and "UNSTABLE" in cell


def test_conflict_unknown_build_is_unstable():
    cell, worst = run_conformance.cell_spread(
        [_r("fail"), _r("pass", "0.1.433")])
    assert worst == "fail" and "UNSTABLE" in cell


def test_conflict_aligned_with_builds_reads_skill_changed():
    """The GAP-001 misread, decided the other way: old-build fails plus a
    new-build pass is the skill changing, and the latest build governs."""
    cell, worst = run_conformance.cell_spread(
        [_r("fail", "0.1.364", ["collision=FAIL"]),
         _r("fail", "0.1.364", ["collision=FAIL"]),
         _r("pass", "0.1.433")])
    assert worst == "pass"
    assert "skill changed between builds" in cell
    assert "fail@0.1.364" in cell and "pass@0.1.433" in cell
    assert "UNSTABLE" not in cell


def test_regression_across_builds_also_named_and_governs():
    """The alignment rule is symmetric: a NEW build failing where the old
    passed is a regression, named the same way, and the latest still
    governs — toward fail this time."""
    cell, worst = run_conformance.cell_spread(
        [_r("pass", "0.1.400"),
         _r("fail", "0.1.433", ["collision=FAIL"])])
    assert worst == "fail"
    assert "skill changed between builds" in cell
    assert "collision=FAIL" in cell


def test_version_ordering_is_numeric_not_lexical():
    cell, worst = run_conformance.cell_spread(
        [_r("fail", "0.1.99"), _r("pass", "0.1.100")])
    assert worst == "pass"  # 100 > 99 numerically; lexically it would lose
