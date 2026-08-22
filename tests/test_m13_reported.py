"""M13 reports; it does not fail the run.

The target string has read `=0 (reported)` since the metric shipped and the
rubric describes it the same way, while the verdict was computed — so a document
with one flagged contradiction exited non-zero for two releases. The rule text
was right and the code was wrong: a quantity legitimately changes across a time
series or a target/actual pair, and a gate here would have an author edit
correct prose to silence it.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECK_PROSE = ROOT / "scripts" / "check" / "check_prose.py"

CONTRADICTS = (
    '<!doctype html><html lang="en"><body>'
    "<p>The install backlog stood at 4.2 million units when the review began, "
    "and the team agreed clearing it was the largest lever available.</p>"
    "<p>Later analysis of the same install backlog put it at 4.5 million units, "
    "which is the figure quoted in the board pack this quarter.</p>"
    "</body></html>"
)


def test_the_verdict_is_hard_coded_reported():
    """Read out of the source, because the target string alone was not enough:
    it said `(reported)` while the verdict beside it was computed."""
    src = CHECK_PROSE.read_text(encoding="utf-8")
    m = re.search(r'\("M13_quantity_conflicts",(.*?)\),\n', src, re.S)
    assert m, "M13's verdict row is gone — the metric or its shape changed"
    parts = [p.strip() for p in m.group(1).split(",")]
    assert parts[2] == "True", f"M13's verdict is computed, not reported: {parts[2]}"


def test_a_contradiction_is_reported_and_the_run_still_passes(tmp_path):
    doc = tmp_path / "contradicts.en.html"
    doc.write_text(CONTRADICTS, encoding="utf-8")
    proc = subprocess.run([sys.executable, str(CHECK_PROSE), str(doc)],
                          capture_output=True, text=True)
    assert "M13_quantity_conflicts" in proc.stdout
    assert re.search(r"ok\s+M13_quantity_conflicts\s+1", proc.stdout), proc.stdout
    assert proc.returncode == 0, "a reported metric must not fail the run"


def _prose_targets(path):
    """-> {metric: target string}, from the checker's own report.

    Read out of a run rather than out of the source: the row table is what
    decides, and a regex over the file would be a second reading of it.
    """
    proc = subprocess.run([sys.executable, str(CHECK_PROSE), str(path), "--json"],
                          capture_output=True, text=True)
    return json.loads(proc.stdout)[0]["targets"]


def test_the_two_checkers_now_express_gating_the_same_way():
    """They did not, and eight prose metrics lived in the gap.

    `check_design` exits non-zero only on rows whose target says `(gates)`.
    `check_prose` exited non-zero on ANY failing row while marking one, so M2,
    M4, M4zh, M5, M6, M8, M9, M10 and M11 failed a build through the exit code
    and were classified as graded by `gating.py` — which every other consumer
    reads. `check_deliverable` printed them as `note` beside an exit that said
    otherwise. GAP-029, closed at 0.1.559 by the owner's decision.
    """
    prose = CHECK_PROSE.read_text(encoding="utf-8")
    design = (ROOT / "scripts" / "check" / "check_design.py").read_text(encoding="utf-8")
    assert "return 1 if gated else 0" in prose, (
        "check_prose exits on its FAIL count again, not on its gates")
    assert design.count('"=0 (gates)"') >= 5, "design marks each gate in its target"


def test_a_prose_row_gates_if_and_only_if_its_target_is_zero():
    """The rule, held to the row table rather than to a list of names.

    A target of zero is a line the document either crosses or does not. A target
    that is a share is a DIRECTION, and this repository has shipped three
    regressions from an author optimizing toward one — 0.1.336 drove sentence
    variance to zero doing exactly that. `(reported)` opts a zero-targeted row
    out, which is how M13 and M14 stay toothless on purpose.
    """
    targets = _prose_targets(ROOT / "fixtures" / "deck-pass.en.html")
    for metric, target in targets.items():
        zero = target.startswith("=0")
        reported = "(reported)" in target
        gates = "(gates)" in target
        if zero and not reported:
            assert gates, f"{metric} targets zero and does not gate: {target!r}"
        else:
            assert not gates, (
                f"{metric} gates on a target that is not a line: {target!r}")


# Six lists, three items each: M10's triad rate goes to 100% and nothing else
# moves. Built by running it rather than reasoned about — the first two
# candidates for this test failed NO metric at all, which would have made the
# assertion below pass without ever exercising the path it exists for
# (convention 15: a check that has never fired on a real artifact is not a
# check).
ONLY_DIRECTIONS = (
    '<!doctype html><html lang="en"><body>'
    "<p>The programme moved forward through the quarter and the team recorded "
    "what it found in each region as the work proceeded.</p>"
    + "".join(f"<ul><li>alpha {i}</li><li>beta {i}</li><li>gamma {i}</li></ul>"
              for i in range(6))
    + "</body></html>")


def test_a_graded_failure_alone_does_not_fail_the_run(tmp_path):
    """The whole point, end to end: a document that misses only directions is
    reported and exits zero. Before 0.1.559 this exited 1."""
    doc = tmp_path / "directions.en.html"
    doc.write_text(ONLY_DIRECTIONS, encoding="utf-8")
    proc = subprocess.run([sys.executable, str(CHECK_PROSE), str(doc)],
                          capture_output=True, text=True)
    verdicts = json.loads(subprocess.run(
        [sys.executable, str(CHECK_PROSE), str(doc), "--json"],
        capture_output=True, text=True).stdout)[0]["verdicts"]
    failing = {m for m, v in verdicts.items() if v == "FAIL"}
    gates = {m for m, t in _prose_targets(doc).items() if "(gates)" in t}
    assert failing, "the document must fail something, or this proves nothing"
    assert not (failing & gates), (
        f"this document was meant to fail only directions: {sorted(failing)}")
    assert proc.returncode == 0, proc.stdout[-400:]
    assert "none of them gating" in proc.stdout, proc.stdout[-400:]
