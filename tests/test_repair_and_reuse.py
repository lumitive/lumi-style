"""0.1.589's three readings, each proven able to fire and to stay quiet.

They come from one measured failure: a build DIAGNOSED a page's dead band and
collapsed figure correctly, fixed it twice, and shipped it still broken — with
every gate green before and after. The package could find a layout defect and
had no way to confirm a repair, and the three numbers that describe such a
defect were computed, printed, and read by nothing.
"""
import json
import pathlib
import subprocess
import sys

import check_design
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
INSPECT = ROOT / "scripts/check/inspect_layout.py"


# --- D32, per page rather than per document --------------------------------

def _deck(sections):
    return "<html><body>" + "".join(sections) + "</body></html>"


def test_one_shape_no_longer_clears_every_declared_move():
    """The measured hole: `1 library shape(s) on 10 analysis page(s)`, green.
    Both prose sites describing D32 said *a page* that declares a move draws
    the library's shape for it, so the code was the half that was wrong."""
    raw = _deck([
        '<section class="page" id="p1" data-analysis="compare">'
        '<use href="#shape-p156-x"/></section>',
        '<section class="page" id="p2" data-analysis="compare">no shape</section>',
    ])
    out = check_design.d32_shape_use(raw)
    assert out["bare"] == ["p2"], out
    assert out["held"] == 2


def test_a_page_is_held_only_when_the_library_can_draw_its_move(monkeypatch):
    """The exemption, which must survive the registry being complete.

    This test used to use `correlate` as its undrawable example, because
    `correlate` HAD no framework (GAP-032, closed at 0.1.663 by registering
    `scatter`). Reusing a real gap as a fixture meant the test died the moment
    the gap closed — and a reader could not tell whether it was asserting the
    exemption or the gap. It now makes its own undrawable move, so it asserts
    the rule rather than the state of the registry."""
    monkeypatch.setattr(check_design, "_drawable_moves", lambda: {"compare"})
    raw = _deck(['<section class="page" id="p1" data-analysis="correlate">'
                 'no shape</section>'])
    out = check_design.d32_shape_use(raw)
    assert out["bare"] == []
    assert out["undrawable"] == ["correlate"]


def test_which_moves_are_drawable_is_a_fact_about_the_library():
    """A first cut of this asserted all five moves drawable, because 0.1.663
    had bound a shape to `correlate` to satisfy a guard. A review opened that
    SVG — an empty axis frame with one bubble — and the binding was withdrawn
    (GAP-032, AG-10). `correlate`'s framework is `drawn: "native"`, so the move
    is NOT drawable and a correlate page stays exempt from D32, which is the
    honest state: this library ships no scatter.

    What this test pins is that the exemption is derived from the registry
    rather than hardcoded, so it moves the day someone draws one."""
    drawable = check_design._drawable_moves()
    assert {"compare", "decompose", "position", "bridge"} <= drawable
    assert "correlate" not in drawable, (
        "correlate became drawable — if a scatter unit was added to the "
        "library, close GAP-032 and update this test; if a shape was bound to "
        "satisfy a checker, read AG-10 first")


def test_a_document_declaring_no_move_is_not_measured():
    raw = _deck(['<section class="page" id="p1">plain</section>'])
    assert check_design.d32_shape_use(raw)["held"] == 0


# --- D41, two roles saying one thing ---------------------------------------

def test_a_takeaway_that_repeats_the_support_line_is_reported():
    """Measured on two documents, which is this package's bar for promoting a
    lesson to a rule."""
    raw = _deck(['<section class="page" id="p9">'
                 '<p class="sup">Order cannot change. Capability negotiation '
                 'lands first, then the catalogue has somewhere to go.</p>'
                 '<p class="take">Capability negotiation lands first, then the '
                 'catalogue has somewhere to go.</p></section>'])
    hits = check_design.d41_role_echo(raw)
    assert hits and hits[0][0] == "p9"
    assert hits[0][1:3] == ("take", "sup")


def test_a_lead_that_restates_the_title_is_reported():
    """Following the rule produced the defect: SKILL.md encourages `.lead` and
    says nothing about what it must carry that the title does not."""
    raw = _deck(['<section class="page" id="p4">'
                 '<h2 class="t">Zero official renderers support v1.0</h2>'
                 '<p class="lead">Zero official renderers support v1.0 and six '
                 'stopped at v0.9.</p></section>'])
    hits = check_design.d41_role_echo(raw)
    assert hits and hits[0][1:3] == ("lead", "title")


def test_a_short_shared_phrase_is_not_a_repetition():
    raw = _deck(['<section class="page" id="p4">'
                 '<p class="sup">The gateway is the seam.</p>'
                 '<p class="take">Build the gateway next quarter, with an '
                 'owner and a date attached to it.</p></section>'])
    assert check_design.d41_role_echo(raw) == []


# --- --against, the reading that confirms a repair --------------------------

def _against(before, now):
    import inspect_layout
    return inspect_layout.against_report(before, now)


def _doc(pages, verdicts=None):
    return {"results": [{"file": "d.html", "geometry": "16x9", "pages": pages}],
            "verdicts": verdicts or {}}


def test_a_repair_that_did_not_land_says_so():
    """The whole point. A build fixed one page twice and the numbers never
    moved; nothing in the package noticed."""
    page = [{"id": "p4", "centerScale": 37.0, "emptyBandPct": 10.2}]
    out, regressed = _against(_doc(page), _doc(page))
    assert not regressed
    assert any("the repair did not land" in d for _v, _s, d in out), out


def test_a_number_that_moved_is_named_with_both_readings():
    out, _ = _against(_doc([{"id": "p4", "centerScale": 37.0}]),
                      _doc([{"id": "p4", "centerScale": 81.4}]))
    assert any("37.0 → 81.4" in d for _v, _s, d in out), out


def test_a_gating_verdict_that_went_red_is_not_a_matter_of_taste():
    out, regressed = _against(
        _doc([{"id": "p4"}], {"collision": "ok"}),
        _doc([{"id": "p4"}], {"collision": "FAIL"}))
    assert regressed
    assert any(v == "FAIL" and "REGRESSED" in d for v, _s, d in out), out


def test_a_previous_run_of_another_document_is_refused():
    out, regressed = _against(_doc([{"id": "zzz"}]), _doc([{"id": "p4"}]))
    assert regressed
    assert any("different document" in d for _v, _s, d in out), out


def test_an_unreadable_previous_run_is_not_a_verdict_on_this_one():
    """check_outline --against's distinction, copied deliberately: a parse
    failure is not a finding about the document."""
    out, regressed = _against({"results": []}, _doc([{"id": "p4"}]))
    assert not regressed
    assert out[0][0] == "not_measured"


def test_the_comparison_is_not_inside_the_verdict_map(tmp_path):
    """`run_conformance` turns every key in the top-level `verdicts` block into
    a required-ok gate on every task, so a comparison finding must not live
    there."""
    src = ROOT / "fixtures/deck-pass.en.html"
    before = tmp_path / "before.json"
    r1 = subprocess.run([sys.executable, str(INSPECT), "--deliverable",
                         "--no-sheet", "--iterate", "--json", str(src)],
                        capture_output=True, text=True)
    if r1.returncode != 0 and "playwright" in (r1.stdout + r1.stderr).lower():
        pytest.skip("no browser")
    before.write_text(r1.stdout, encoding="utf-8")
    r2 = subprocess.run([sys.executable, str(INSPECT), "--deliverable",
                         "--no-sheet", "--iterate", "--json",
                         "--against", str(before), str(src)],
                        capture_output=True, text=True)
    doc = json.loads(r2.stdout)
    assert "against" in doc
    assert not any(k.startswith("against") for k in doc["verdicts"])
