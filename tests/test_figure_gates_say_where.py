"""A figure finding names the move, not just the overlap.

`figure_axis_overlap` printed the page, the name and the size of the overlap —
everything except the one thing the author has to decide, which is where to put
the name instead. The 2026-08-25 validation round measured the cost: three
build rounds spent moving one label by trial, and the author's report said so
in as many words ("the report names pages and not coordinates").

The gate itself is right and is not touched here. What changes is that the
finding carries the shortest move that clears the plot, in the direction the
axis convention already fixes: an x name goes below its line, a y name to the
left of its.

Renders, so it needs Chromium and is skipped without it — the same posture as
`tests/test_clipped_measures_where_it_renders.py`, whose scaffold this copies.
"""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "scripts" / "check" / "inspect_layout.py"

_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>.page{{width:1280px;height:720px}}.fig svg{{width:640px;height:300px}}
.axname-y{{writing-mode:vertical-rl;rotate:180deg;transform-box:fill-box;
transform-origin:center}}</style>
</head><body data-geometry="landscape" data-genre="internal">
<section class="page" id="p4"><div class="body stack"><div class="fill">
<div class="fig"><svg viewBox="0 0 640 300" role="img" aria-label="t">
  <rect x="60" y="20" width="500" height="200" fill="#8a8"/>
  <rect x="60" y="230" width="300" height="12" fill="#8a8"/>
  {mark}
</svg><div class="cap"><span class="n">Figure 1</span> A title</div></div>
</div></div></section></body></html>"""

# Lies across the plate: the gate fires, and the author needs to know it must
# go below y=242 rather than that it overlaps by some number of pixels.
NAME_ON_THE_PLOT = ('<text x="200" y="120" class="axname-x" '
                    'style="font-size:11px">share of scheduled reads</text>')
# Clear of it, below the deepest mark.
NAME_BELOW_THE_PLOT = ('<text x="200" y="270" class="axname-x" '
                       'style="font-size:11px">share of scheduled reads</text>')


def _report(tmp_path, mark, name):
    pytest.importorskip(
        "playwright",
        reason="inspect_layout.py renders; see SKILL.md's browser step")
    deck = tmp_path / f"{name}.en.html"
    deck.write_text(_PAGE.format(mark=mark), encoding="utf-8")
    out = subprocess.run([sys.executable, str(LAYOUT), str(deck),
                          "--deliverable", "--iterate", "--no-sheet"],
                         capture_output=True, text=True, cwd=ROOT)
    # A crash is not a pass: the probe must have run for the report to mean
    # anything (the lesson tests/test_clipped_measures_where_it_renders.py
    # records).
    assert "@ 16x9" in out.stdout, out.stdout + out.stderr
    return out.stdout


def test_an_overlapping_axis_name_is_told_where_to_go(tmp_path):
    report = _report(tmp_path, NAME_ON_THE_PLOT, "over")
    assert "figure_axis_overlap" in report and "FAIL" in report
    line = next(ln for ln in report.splitlines() if "axis name" in ln.lower())
    assert "down" in line, (
        f"the finding does not say which way the name must move: {line!r}")


def test_a_name_clear_of_the_plot_is_not_reported(tmp_path):
    """The counter-red: the message change must not make the gate fire more."""
    report = _report(tmp_path, NAME_BELOW_THE_PLOT, "clear")
    line = next((ln for ln in report.splitlines()
                 if "axis name" in ln.lower() and "FAIL" in ln), None)
    assert line is None, f"a name outside the plot was reported: {line!r}"
