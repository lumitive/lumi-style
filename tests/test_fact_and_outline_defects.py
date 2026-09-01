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


# --- 7. a magnitude suffix must not eat the next word ------------------------

def test_a_currency_figure_is_not_multiplied_by_the_following_word():
    """`$10.95 Meal` read as ten million, `$9.00 back` as nine billion.

    The k/m/b suffix carried no word boundary, so it consumed the first letter
    of whatever came next. It corrupts BOTH sides of the comparison, and which
    way depends on the word order of the sentence around the figure — so a
    contract and a document stating the same price disagree if one of them
    happens to be followed by "Meal".
    """
    assert cf.facts("$10.95 Meal", names=False)[0] == {"10.95"}
    assert cf.facts("$9.00 back to single", names=False)[0] == {"9"}
    assert cf.facts("$1.2 billion", names=False)[0] == {"1200000000"}


def test_a_clock_time_is_not_a_quantity():
    """`22:00` yielded a bare `0` from its minutes."""
    assert cf.facts("she sleeps at 22:00", names=False)[0] == set()


def test_a_dose_is_a_quantity_on_both_sides():
    """`75mg` was invisible to the pattern, so a contract stating a dose and a
    document stating the same dose could never be compared."""
    assert cf.facts("about 75mg at bedtime", names=False)[0] == {"75"}
    assert cf.facts("4g of protein", names=False)[0] == {"4"}


# --- 8. a Chinese agenda line is not an orphan for want of a space -----------

def test_d27_normaliser_ignores_spaces_between_cjk():
    """`<span>` stripping inserts a separator that English needs and Chinese does not.

    D27 compares an agenda line with the deck's own titles. Stripping the inline
    highlight span leaves a space where the tag was: in English that lands on a
    word boundary and matches, in Chinese it invents one, so an identical line
    read as an orphan and the zh build failed a gate it should pass.
    """
    import pathlib as _p
    import sys as _s
    _s.path.append(str(_p.Path(__file__).resolve().parents[1] / "scripts" / "check"))
    import check_design as cd
    assert cd._norm_line("每个 Agent 都会撞上的 那堵墙") == cd._norm_line("每个 Agent 都会撞上的那堵墙")
    # English still needs its spaces: these are two different lines.
    assert cd._norm_line("the wall every agent hits") != cd._norm_line("thewalleveryagenthits")


# --- 9. a source filename is provenance, not a claim -------------------------

def test_a_source_filename_is_not_a_quantity():
    """`Lumi-Agent-介绍 260819.html` reported 260819 as an invented figure.

    A converted deck names the file it was converted from, and that name often
    carries a date. It is furniture of exactly the class already stripped here
    -- an ISO date, a clock time, a page fraction, a phone number -- and left
    in, it fails a document whose every figure is sourced. The digits stay
    readable to a person; they are simply not a quantity anyone asserted.
    """
    assert cf.facts("Source: Lumi-Agent-介绍 260819.html", names=False)[0] == set()
    assert cf.facts("built from deck-2024-Q3.pdf", names=False)[0] == set()
    # A figure BESIDE a filename is still a figure.
    assert cf.facts("chart.html shows $4,200", names=False)[0] == {"4200"}


# --- 10. the outline mirror could not read a Chinese title -------------------

def test_the_outline_mirror_reads_chinese():
    """`_WORD` was `[a-z0-9]+`, so a pure-CJK title had NO words at all.

    Both branches of `_matches` then fell through — containment needs two
    non-empty strings and the overlap test needs a non-empty plan — and every
    Chinese title without a digit or a Latin word in it read as never having
    reached the document. Measured on the shipped zh deck: exactly the three
    titles carrying no Latin and no digit failed a gate, and all three were on
    the page, character for character.
    """
    assert co._matches("缺的不是能力：是一份声明", "缺的不是能力：是一份声明")
    # An inline highlight span leaves a space behind when the tag is stripped:
    # English needs it, Chinese does not. Same defect as D27's normaliser.
    assert co._matches("缺的不是能力：是一份声明", "缺的不是能力：是一份 声明")
    # A title tightened during composition still matches, as in English.
    assert co._matches("四类大玩家：每一类都绕开了同一件事", "四类大玩家都绕开了同一件事")
    # A different claim is still a different claim — the gate can go red.
    assert not co._matches("缺的不是能力：是一份声明", "四类大玩家：每一类都绕开了同一件事")


# --- 7. the document's own apparatus is not a claim (0.1.599) ----------------
# Three more of the same family as the year and the phone number above: a
# number the DOCUMENT is made of, graded as a number the document asserts. All
# three were found by reading the code during the round-6 retrospective rather
# than by a build failing, so the reds come first here too.

def test_a_v_prefixed_version_stamp_is_not_a_quantity():
    """`VERSION`'s leading `\\b` is defeated by the `v`.

    A colophon reading "built with lumi-style v0.1.599" invents the quantity
    599 and the gate that guards red line 1 fires on the package's own stamp.
    The bare form is stripped, so which way it goes depends on how the author
    typed it.
    """
    r = cf.compare(CONTRACT, "<html><p>Built with lumi-style v0.1.599 · "
                             "source: the engagement record.</p></html>")
    assert r["unsourced_quantities"] == []


def test_a_caption_ordinal_is_furniture_on_both_sides_of_ten():
    """`Figure 3` and `Figure 10` are the same kind of thing.

    `FURNITURE` already declares a caption ordinal furniture, and the quantity
    branch never consults it — so single-digit captions were invisible only
    because the quantity pattern needs two digits, and the tenth figure of a
    document became a claim about a quantity.
    """
    lo = cf.compare(CONTRACT, "<html><p>Figure 3 A title stating a conclusion"
                              "</p></html>")
    hi = cf.compare(CONTRACT, "<html><p>Figure 10 A title stating a conclusion"
                              "</p></html>")
    assert lo["unsourced_quantities"] == []
    assert hi["unsourced_quantities"] == lo["unsourced_quantities"]


def test_a_zero_padded_ordinal_ending_a_sentence_is_still_an_ordinal():
    """The ordinal strip's lookahead is defeated by a full stop.

    `(?<![\\d.])0\\d(?![\\d.])` refuses `00.` because the period is in the
    lookahead's class, so the scaffold's own card sample — "Page 00." — reads
    as the quantity zero.
    """
    r = cf.compare(CONTRACT, "<html><p>The one line to carry away. Page 00."
                             "</p></html>")
    assert r["unsourced_quantities"] == []


def test_a_real_figure_beside_the_apparatus_still_gates():
    """The counter-red, and the only thing between this and a hole in a gate.

    Run before and after: widening what counts as furniture must not blind the
    check to a quantity the contract never authorised.
    """
    r = cf.compare(CONTRACT, "<html><p>Built with lumi-style v0.1.599 · "
                             "Figure 10 · 41% of respondents agreed.</p></html>")
    assert "41" in r["unsourced_quantities"], (
        f"the gate stopped seeing a real figure: {r['unsourced_quantities']}")


# --- a placement is not a quantity (0.1.676) --------------------------------

def test_a_two_by_two_placement_is_not_held_to_the_fact_contract():
    """AG-10: a two-by-two's axes are ordinal, and `quadrant_svg` refuses any
    placement outside 0 to 1 because the number claims no precision. A fact
    contract cannot list 0.42 — it is not a fact about the world. Held to
    this, a correct integration matrix reported eight unsourced quantities and
    the only ways to clear them were to invent facts or delete the figure."""
    import check_facts
    spec = {"move": "position",
            "axes": {"x": {"name": "prerequisite", "unit": "host",
                           "low": "none", "high": "renderer"},
                     "y": {"name": "dynamism", "unit": "run time",
                           "low": "static", "high": "generative"}},
            "items": [{"label": "A", "x": 0.42, "y": 0.86, "note": "n"}]}
    assert check_facts._spec_values(spec) == []


def test_a_scatter_point_IS_held_to_it():
    """The exclusion is the move's, not the field name's: a `correlate`
    point's x and y are the measured data, and dropping them would blind red
    line 1 on the one figure that is nothing but numbers."""
    import check_facts
    spec = {"move": "correlate",
            "x": {"name": "hours", "unit": "h"}, "y": {"name": "seats", "unit": "%"},
            "points": [{"x": 12, "y": 34}]}
    assert sorted(check_facts._spec_values(spec)) == [12, 34]


def test_an_axis_mapping_is_never_collected_as_a_value():
    """`axes.x` is the x AXIS. It was appended whole and stringified, so the
    report named a dict among the document's unsourced numbers."""
    import check_facts
    spec = {"move": "correlate",
            "x": {"name": "hours", "unit": "h"}, "y": {"name": "seats", "unit": "%"},
            "points": []}
    assert check_facts._spec_values(spec) == []
