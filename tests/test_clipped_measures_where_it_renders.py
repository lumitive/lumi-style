"""`figure_clipped` measures a drawing where it RENDERS, and says which element.

Two defects at one code point, both found in the field at 0.1.591.

`getBBox()` answers in the element's own user space, BEFORE its `transform`.
This package's own axis-name convention rotates text
(`translate(x, y) rotate(-90)`), and such a label's untransformed box sits at
negative y — so six correct drawings in one deck were reported as clipped and
the author shortened real axis names to silence a probe that was wrong.

The same push recorded `{over, pct}` and nothing else: eight pages, one number
each, and no way to find the element without writing a private probe.
"""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "scripts" / "check" / "inspect_layout.py"

_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>.page{{width:1280px;height:720px}}.fig svg{{width:640px;height:300px}}</style>
</head><body data-geometry="landscape" data-genre="internal">
<section class="page" id="p4"><div class="body stack"><div class="fill">
<div class="fig"><svg viewBox="0 0 640 300" role="img" aria-label="t">
  <rect x="60" y="20" width="540" height="230" fill="#ddd"/>
  {mark}
</svg><div class="cap"><span class="n">Figure 1</span> A title</div></div>
</div></div></section></body></html>"""

# Renders upward from y=240 along x=14 — wholly inside the box. Its
# untransformed bbox is the thing that sits outside.
ROTATED_AXIS_NAME = ('<text transform="translate(14,240) rotate(-90)" '
                     'class="axname-y" style="font-size:11px">'
                     'How much context drives the UI</text>')
# Genuinely runs off the right edge.
RUNAWAY_LABEL = ('<text x="500" y="150" class="lbl" style="font-size:18px">'
                 'this label really does run off the right edge</text>')

def _render(tmp_path, mark, name):
    pytest.importorskip(
        "playwright",
        reason="inspect_layout.py renders; see SKILL.md's browser step")
    deck = tmp_path / f"{name}.en.html"
    deck.write_text(_PAGE.format(mark=mark), encoding="utf-8")
    r = subprocess.run([sys.executable, str(LAYOUT), str(deck)],
                       capture_output=True, text=True, cwd=ROOT)
    # A CRASH IS NOT A PASS. Asserting only `"FIGURE CLIPPED" not in out` reads
    # green when the renderer died and `out` is empty. NOT `returncode == 0`:
    # these one-page fixtures carry almost no roles, so the run legitimately
    # exits 1 on "could not be measured" — what must hold is that the report
    # RAN, which its per-geometry header proves.
    assert "@ 16x9" in r.stdout, (
        f"inspect_layout produced no report (exit {r.returncode})\n"
        f"{r.stderr[-800:]}")
    return r.stdout


def test_a_rotated_axis_name_inside_its_box_is_not_clipped(tmp_path):
    out = _render(tmp_path, ROTATED_AXIS_NAME, "rotated")
    assert "FIGURE CLIPPED" not in out, (
        "a drawing wholly inside its viewBox was reported as clipped — the "
        "measurement is being taken before the element's transform:\n" + out)
    assert "every drawing stays inside its own viewBox" in out


def test_a_drawing_that_really_escapes_is_still_caught(tmp_path):
    """The other half of the same change: it must still go red."""
    out = _render(tmp_path, RUNAWAY_LABEL, "runaway")
    assert "FIGURE CLIPPED" in out, "a real clip stopped firing:\n" + out


def test_the_report_names_the_element_that_went_outside(tmp_path):
    out = _render(tmp_path, RUNAWAY_LABEL, "named")
    assert "<text.lbl" in out, (
        "the report gives a number and no identity, which is what made an "
        "author write a private probe to find the element:\n" + out)
    assert "run off the right" in out, "the element's own text is not quoted"


AXNAME_Y = ('<text class="axname-y" x="118" y="180">feeder class</text>')


def test_the_packages_own_y_axis_name_rule_names_its_transform_box():
    """`svg .axname-y` is `writing-mode: vertical-rl; rotate: 180deg`, and the
    CSS `rotate` property turns an SVG element about the USER-SPACE ORIGIN
    unless a transform-box says otherwise. Every y-axis name the package
    shipped was therefore spun about (0, 0) and clipped away unseen — measured
    at 103 units left and 199 above on the passing fixture, and confirmed by a
    screenshot showing a bare axis where the name should be.

    Held here rather than only in the stylesheet because the rule and the probe
    were wrong in the same direction, and each made the other look right.
    """
    # NO importorskip: this reads the stylesheet and renders nothing, so it is
    # the one assertion here that can run everywhere. Behind a browser skip it
    # was inert in CI, and deleting `transform-box` from the tokens went green.
    css = (ROOT / "tokens" / "lumi-layouts.css").read_text(encoding="utf-8")
    rule = css[css.index("svg .axname-y"):]
    rule = rule[:rule.index("}")]
    assert "transform-box" in rule and "transform-origin" in rule, (
        "the y-axis name rule names no transform box, so `rotate` turns it "
        f"about the drawing's corner: {rule}")


def test_the_passing_fixture_keeps_its_axis_names_inside():
    """The fixture the evidence gate renders every release carried nine of
    these and passed every gate every release."""
    pytest.importorskip("playwright", reason="renders")
    r = subprocess.run(
        [sys.executable, str(LAYOUT), "--deliverable",
         str(ROOT / "fixtures" / "deck-pass.en.html")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, f"exited {r.returncode}\n{r.stderr[-800:]}"
    assert "FIGURE CLIPPED" not in r.stdout, r.stdout[-1200:]


def test_the_verdict_line_names_the_element_on_every_clipped_page(tmp_path):
    """The verdict line is the one an author acts on, and it named only pages.

    0.1.594 taught the PAGE REPORT to say which element went outside and left
    the verdict saying "3 pages". Measured in a validation round: a build spent
    three of its eighteen rounds hand-measuring bounding boxes to find elements
    the renderer already knew, and its own report named this as the cost.

    One per page, not one overall — that build had three clipped pages.
    """
    pytest.importorskip("playwright", reason="renders")
    deck = tmp_path / "multi.en.html"
    pages = "".join(
        f'<section class="page" id="{pid}"><div class="body stack"><div class="fill">'
        f'<div class="fig"><svg viewBox="0 0 640 300" role="img" aria-label="t">'
        f'<rect class="f-acc" x="20" y="20" width="600" height="60"/>'
        f'<text x="{x}" y="150" class="{cls}" style="font-size:18px">{txt}</text>'
        f'</svg><div class="cap"><span class="n">Figure {i}</span> A title</div></div>'
        f'</div></div></section>'
        for i, (pid, x, cls, txt) in enumerate(
            [("p11", 560, "axname-y", "utilisation by tier"),
             ("p12", 480, "fval", "a much longer runaway value label")], 1))
    deck.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><style>'
        '.page{width:1280px;height:720px}.fig svg{width:640px;height:300px}'
        '</style></head><body data-geometry="landscape" data-genre="internal">'
        + pages + "</body></html>", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(LAYOUT), "--deliverable", str(deck)],
        capture_output=True, text=True, cwd=ROOT).stdout
    line = next((x for x in out.splitlines() if "FAIL" in x and "figure_clipped" in x), "")
    assert line, "figure_clipped did not fail on a deck with two clipped pages\n" + out[-900:]
    for pid, cls in (("p11", "text.axname-y"), ("p12", "text.fval")):
        assert pid in line and cls in line, (
            f"the verdict line does not name {pid}'s element:\n{line}")


def test_a_spilling_page_names_the_block_that_runs_deepest(tmp_path):
    """`deepestWho` has been measured on every page since the probe was written
    and never reached the verdict. A build shrank a table from 12px to 9px over
    several rounds hunting the block that spilled, and its report asked for
    exactly this line."""
    pytest.importorskip("playwright", reason="renders")
    deck = tmp_path / "spill.en.html"
    deck.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><style>'
        '.page{width:1280px;height:720px;position:relative}'
        '.foot{position:absolute;bottom:24px;left:64px;right:64px}'
        '</style></head><body data-geometry="landscape" data-genre="internal">'
        '<section class="page" id="p4"><div class="body stack"><div class="fill">'
        '<div class="notes">' + "<p>a long row of table text</p>" * 60 + "</div>"
        '</div></div><div class="foot"><span class="conf">Internal</span>'
        "<span>4</span></div></section></body></html>", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(LAYOUT), "--deliverable", str(deck)],
        capture_output=True, text=True, cwd=ROOT).stdout
    line = next((x for x in out.splitlines()
                 if "FAIL" in x and "content_spill" in x), "")
    assert line, "content_spill did not fail on a spilling page\n" + out[-900:]
    assert "deepest:" in line and "p4 ." in line, (
        "the verdict does not name the block that runs deepest:\n" + line)
