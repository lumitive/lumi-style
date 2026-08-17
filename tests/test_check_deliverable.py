"""The one-command pre-delivery driver, and the block it must not split.

The ten-round autopsy attributed at least three rounds to partial reading:
the author assembled the gate stack by hand, filtered each tool's output, and
met failures in installments that had all been present in the first report.
The driver's contract is therefore exactly one thing: EVERY failure family in
ONE final block, and an exit code that cannot disagree with it.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "ops" / "check_deliverable.py"

TRIFAIL = """<html><head><title>t</title><style>.x{color:#123456}</style></head>
<body data-geometry="landscape" data-genre="sales">
<section class="page"><div class="body split"><div class="lede">
<h2 class="t">A title</h2></div>
<p>In order to leverage synergies, this is a testament to [TO FILL] robust delivery.</p>
</section></body></html>"""


def _run(doc_text, tmp_path, *args):
    doc = tmp_path / "doc.html"
    doc.write_text(doc_text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(DRIVER), str(doc), "--skip-layout", *args],
        capture_output=True, text=True, cwd=ROOT)


def test_every_failure_family_lands_in_the_one_block(tmp_path):
    """The planted red: prose, design, privacy and layout must all be present
    in a single run's output — no installments."""
    p = _run(TRIFAIL, tmp_path)
    tail = p.stdout[p.stdout.find("the verdict"):]
    assert "prose:" in tail
    assert "design:" in tail, "an unmeasurable design run must be NAMED, not absent"
    assert "privacy:" in tail
    assert "layout:" in tail
    assert p.returncode != 0


def test_the_exit_code_cannot_disagree_with_the_block(tmp_path):
    p = _run(TRIFAIL, tmp_path)
    assert f"exit {p.returncode}" in p.stdout.rsplit("\n", 3)[-2]


def test_a_skipped_layout_is_loud_and_nonzero(tmp_path):
    """A browserless environment is a degraded check, never a quiet pass."""
    p = _run(TRIFAIL, tmp_path)
    assert "layout: the instrument did not speak (skipped)" in p.stdout


def test_genre_is_read_from_the_document_itself(tmp_path):
    p = _run(TRIFAIL, tmp_path)
    assert "genre=sales" in p.stdout.splitlines()[0]


def test_json_mode_emits_one_parseable_object(tmp_path):
    import json
    p = _run(TRIFAIL, tmp_path, "--json")
    doc = json.loads(p.stdout)
    assert set(doc) >= {"gating", "graded", "silent", "exits", "exit"}
    assert doc["exit"] == p.returncode


# checker_report: the shared reader the four scripts now import.

sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import checker_report  # noqa: E402


def test_parse_report_reads_both_shapes():
    reports, spoke = checker_report.parse_report('[{"file": "a", "verdicts": {"M1": "ok"}}]')
    assert spoke and reports[0]["file"] == "a"
    reports, spoke = checker_report.parse_report('{"verdicts": {"collision": "FAIL"}, "unmeasured": 2}')
    assert spoke and reports[0]["unmeasured"] == 2


def test_parse_report_distinguishes_silence_from_an_empty_report():
    """The distinction ledger 2 depends on: a crash is not an empty report."""
    assert checker_report.parse_report("Traceback (most recent call last)") == (None, False)
    reports, spoke = checker_report.parse_report("[]")
    assert spoke is True and reports == []


def test_findings_treats_na_as_not_a_failure():
    rows = checker_report.findings([{"file": "x.html",
                                     "verdicts": {"a": "ok", "b": "n/a", "c": "FAIL"}}])
    assert rows == ["x.html: c FAIL"]
