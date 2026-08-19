"""The six defects a five-agent review found in the 0.1.522 gates.

Every test here was written to FAIL against the code as reviewed, and each one
reproduces a defect that was demonstrated rather than reasoned about. They are
kept after the fix because convention 11 is explicit that a gate's first proof
is that it can go red: these are the reds.

The shared root, worth stating once: each defect got through because the test
written alongside the code assumed the same shape the code assumed. Convention
15 asks for a real instance instead, so several of these read the repo's own
fixtures and the shipped contract rather than a hand-built string.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts" / "check"))

import check_facts as cf  # noqa: E402
import check_outline as co  # noqa: E402

CONTRACT = """# Brief

Write in American English.

## FACTS

Revenue reaches $1.2 billion by 2030 in Berlin.
"""


# --- 1. furniture must not read as an invented number ------------------------

def test_a_bare_year_is_not_an_unsourced_quantity():
    """A roadmap year is a date, not a claim about a quantity.

    Gating on it makes an author delete a correct year, which is the failure
    this repo treats as most serious: a wrong gate that edits right prose.
    """
    r = cf.compare(CONTRACT, "<html><p>We reach breakeven in 2027, after a "
                             "2026 pilot.</p></html>")
    assert r["unsourced_quantities"] == []


def test_a_phone_number_is_not_an_unsourced_quantity():
    r = cf.compare(CONTRACT, "<html><p>Call +65 6123 4567 to reach us.</p></html>")
    assert r["unsourced_quantities"] == []


def test_a_currency_figure_the_contract_lacks_still_gates():
    """The fix must not buy silence: the check's whole job still works."""
    r = cf.compare(CONTRACT, "<html><p>We booked $88.5M last year.</p></html>")
    assert r["unsourced_quantities"], "the gate stopped catching invented money"


# --- 2. a document nothing was read from is not a clean document -------------

def test_a_document_it_could_not_read_is_unmeasurable():
    """Every figure invented, all of it inside an excluded drawing.

    `check_design.py` reports UNMEASURABLE when a document declares no token
    block; this gate had no equivalent and printed the same `ok` as a clean
    document. "I found no invented numbers" and "I found no numbers" are
    different sentences.
    """
    blind = ('<html><body><svg class="ground"><text>91 markets</text>'
             '<text>$88.5M revenue</text><text>412 customers</text></svg>'
             + "<p>x</p>" * 400 + "</body></html>")
    r = cf.compare(CONTRACT, blind)
    assert r.get("unmeasurable"), "a document it read nothing from passed"


# --- 3. the contract shapes and name kinds it is blind to --------------------

def test_a_bulleted_fact_list_yields_its_names():
    """A list is the natural shape for a FACTS section, and it yielded none.

    The admission rule required a name to appear preceded by a lowercase word
    or a comma; under `- ` every name is at the start of its line.
    """
    _q, names = cf.facts(cf.permitted(
        "## FACTS\n- Berlin is the first market.\n- Osaka follows.\n"))
    assert {"Berlin", "Osaka"} <= names


def test_an_acronym_is_a_name():
    """The measured defect this check exists for was four PLATFORM names
    dropped in a rebuild, and platform names are acronym-shaped."""
    _q, names = cf.facts(cf.permitted(
        "## FACTS\n- MCP and A2A are the protocols.\n- IBM signed first.\n"))
    assert {"MCP", "A2A", "IBM"} <= names


def test_a_hyphenated_class_is_not_a_decorative_drawing():
    """`\\b(?:gl|ground)\\b` treats `-` as a boundary, so `ground-truth` and
    `gl-panel` had all their text deleted before measurement. Third outing for
    this bug class in this repo."""
    assert "391732" in cf._visible('<svg class="ground-truth"><text>391732</text></svg>')


# --- 4. a parse failure is not a verdict about the author --------------------

def test_a_page_whose_id_precedes_its_class_is_still_a_page():
    html = '<section id="p4" class="page"><h2 class="t">Alpha beats beta</h2></section>'
    assert [p["title"] for p in co.deck_pages(html)] == ["Alpha beats beta"]


def test_a_document_no_page_parsed_from_is_not_called_stale():
    """The report accused a correct outline of describing a different
    document when the parser had read nothing at all."""
    outline = ("genre: sales\nstoryline: pitch-deck\n\n## Part A · Alpha\n\n"
               "- Alpha beats beta on cost\n- Gamma holds the line\n")
    findings = co.drift(outline, "<html><body><p>no sections here</p></body></html>")
    findings = findings[0] if isinstance(findings, tuple) else findings
    verdicts = {f["check"]: f["verdict"] for f in findings}
    assert verdicts.get("outline mirror") == "not_measured", verdicts


# --- 5. a coverage claim states the number it actually checked ---------------

def test_the_implication_rung_counts_only_what_it_checked():
    """It reported `all 3 planned implications reached a takeaway` in the same
    report where the mirror said one of the three reached no page at all."""
    outline = (
        "genre: sales\nstoryline: pitch-deck\n\n## Part A · Alpha\n\n"
        "- Alpha beats beta on cost\n"
        "  analysis: compare | finding: alpha beats beta | implication: buyers save\n"
        "- Gamma holds the line\n"
        "  analysis: position | finding: gamma holds | implication: the moat is gamma\n"
        "- Epsilon closes in 2027\n"
        "  analysis: bridge | finding: epsilon closes | implication: the plan lands\n")
    html = ('<section class="page" id="p1"><h2 class="t">Alpha beats beta on cost</h2>'
            '<p class="take">buyers save</p></section>'
            '<section class="page" id="p2"><h2 class="t">Gamma holds the line</h2>'
            '<p class="take">the moat is gamma</p></section>')
    findings = co.drift(outline, html)
    findings = findings[0] if isinstance(findings, tuple) else findings
    rung = next(f for f in findings if f["check"] == "implication rung")
    assert " 3" not in str(rung["detail"]), (
        f"claims a denominator of 3 when only 2 titles reached a page: {rung['detail']}")
