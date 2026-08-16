"""M13 reports; it does not fail the run.

The target string has read `=0 (reported)` since the metric shipped and the
rubric describes it the same way, while the verdict was computed — so a document
with one flagged contradiction exited non-zero for two releases. The rule text
was right and the code was wrong: a quantity legitimately changes across a time
series or a target/actual pair, and a gate here would have an author edit
correct prose to silence it.
"""
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


def test_the_two_checkers_express_gating_differently():
    """In check_design a metric gates only if its target carries `(gates)`; in
    check_prose ANY failing row exits non-zero, and `(gates)` on M12 is emphasis
    rather than mechanism. A count taken from one convention and applied to the
    other is wrong, and one was.
    """
    prose = CHECK_PROSE.read_text(encoding="utf-8")
    design = (ROOT / "scripts" / "check" / "check_design.py").read_text(encoding="utf-8")
    assert prose.count("(gates)") == 1, "only M12 carries the emphasis in prose"
    assert design.count('"=0 (gates)"') >= 5, "design marks each gate in its target"
