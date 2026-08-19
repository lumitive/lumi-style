"""0.1.522 — the two consistency checks, each with a failing case.

Both were fired at a real shipped deck before they were believed (convention
15): `check_outline.py --against` named six planned titles that never reached
the document, and `check_facts.py` named the market and platform names a
rebuild had dropped. These tests hold the shapes those runs proved.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check"))
import check_facts  # noqa: E402
import check_outline  # noqa: E402

OUTLINE = """genre: sales
storyline: pitch-deck

## Part A
- 4 approaches expose an interface; not one declares a boundary
  analysis: position | finding: the gap is declaration | implication: patching a protocol onto a legacy stack does not close it
- 0 signed customers, and three named things in the way
  analysis: decompose | finding: the gap is three artifacts | implication: an investor can price it because we can name it
"""

def _page(pid, title, take):
    return (f'<section class="page" id="{pid}"><div class="body stack">'
            f'<div class="lede"><h2 class="t">{title}</h2></div>'
            f'<div class="fill"><p class="take">{take}</p></div></div></section>')


def test_outline_mirror_passes_when_the_plan_reached_the_document():
    html = ("<html><body>"
            + _page("p4", "4 approaches expose an interface; not one declares a boundary",
                    "patching a protocol onto a legacy stack does not close it")
            + _page("p5", "0 signed customers, and three named things in the way",
                    "an investor can price it because we can name it")
            + "</body></html>")
    out = check_outline.drift(OUTLINE, html)
    mirror = next(f for f in out if f["check"] == "outline mirror")
    assert mirror["verdict"] == "ok"


def test_outline_mirror_fails_when_a_planned_title_was_replaced():
    """The shipped defect: a declared finding overwritten by a slogan."""
    html = ("<html><body>"
            + _page("p4", "4 approaches expose an interface; not one declares a boundary",
                    "patching a protocol onto a legacy stack does not close it")
            + _page("p5", "What Stripe is to payments, this layer is to agentic commerce",
                    "we are building the layer every one of them needs")
            + "</body></html>")
    out = check_outline.drift(OUTLINE, html)
    mirror = next(f for f in out if f["check"] == "outline mirror")
    assert mirror["verdict"] == "FAIL"
    assert any("0 signed customers" in x for x in mirror["detail"])


def test_outline_stale_when_nothing_matched():
    html = "<html><body>" + _page("p4", "An unrelated page", "and an unrelated take") + "</body></html>"
    out = check_outline.drift(OUTLINE, html)
    assert any(f["check"] == "outline stale" and f["verdict"] == "FAIL" for f in out)


CONTRACT = """# Contract

## Register
Write in American English. Do not use DASHED rules.

## FACTS — the whole permitted set
Live in Malaysia, Indonesia and Thailand. Measured cost 0.85 cents per turn.
The partner is Volcano Engine.
"""

def test_facts_reports_a_name_the_rebuild_dropped():
    html = "<html><body><section class='page' id='p4'><p>Live in Malaysia. 0.85 cents a turn.</p></section></body></html>"
    r = check_facts.compare(CONTRACT, html)
    assert "Indonesia" in r["absent_names"]
    assert "Thailand" in r["absent_names"]
    assert "Volcano Engine" in r["absent_names"]


def test_facts_gates_a_quantity_the_contract_never_authorised():
    html = "<html><body><section class='page' id='p4'><p>It costs $1.10 per change.</p></section></body></html>"
    r = check_facts.compare(CONTRACT, html)
    assert "1.1" in r["unsourced_quantities"]


def test_facts_ignores_instructions_dates_and_page_furniture():
    html = ("<html><body><section class='page' id='p4'><p>Malaysia, Indonesia, Thailand,"
            " 0.85 cents, Volcano Engine. Source: internal record, 2026-08.</p>"
            "<div class='foot'><span>04 / 20</span></div></section></body></html>")
    r = check_facts.compare(CONTRACT, html)
    assert r["unsourced_quantities"] == []
    assert "American English" not in r["absent_names"]
