"""The measure slot: the scaffold hands it over, and D14 refuses an unfilled one.

There is deliberately NO new metric here, and the reason is measured. A
unit-and-period predicate was built for this rule and then tested against real
material: it false-failed **5 of 7** genuine McKinsey and Bain measure lines —
including Bain Figure 2's "Global buyout assets under management", which carries
neither a unit token nor a period token — and it went GREEN on the scaffold's own
example placeholder. A measure line is a noun phrase naming a quantity, which is
not decidable from tokens (AG-1 / FM-23 refused that class twice).

So the rule is carried the way this package carries what a generator can hand
over: `new_deck.py` emits the slot, and `d14_placeholders`, which already gates,
catches an unfilled one. The scaffold half reaches all twelve platforms; the gate
half is machinery that already exists.
"""
import pathlib
import re

import check_design
import new_deck


def test_a_quantitative_move_gets_the_measure_slot():
    for move in ("compare", "decompose", "bridge", "correlate"):
        assert new_deck.sup_for(move) == new_deck.SUP_MEASURE, move


def test_a_framework_page_keeps_the_prose_slot():
    """`position` is a framework move — a 2x2 has no unit and no period, and
    EX-2 records the market 2x2 as a page the owner accepted outright. Handing
    it a measure slot would push an author to invent one."""
    assert new_deck.sup_for("position") == new_deck.SUP_PROSE
    assert new_deck.sup_for("") == new_deck.SUP_PROSE


def _page(sup):
    return (f'<html><body><section class="page" id="p1">'
            f'<p class="sup">{sup}</p></section></body></html>')


def test_the_unfilled_slot_is_caught_by_the_gate_that_already_exists():
    """The deliberate red. D14 gates, so an author who ships the slot unfilled
    fails the deliverable — no new metric, no new vocabulary, and no false
    positives on real measure lines."""
    found = check_design.d14_placeholders(_page(new_deck.SUP_MEASURE))
    assert found and found[0]["page"] == "p1", (
        "an unfilled measure slot must not reach the reader")


def test_a_filled_measure_line_passes():
    """The other half of the red — including the real Bain and McKinsey measure
    lines that a token predicate false-failed."""
    for line in ("Global buyout assets under management",
                 "Household debt liabilities, GDP multiple",
                 "Revenue by segment, $ million, 2022-25"):
        assert check_design.d14_placeholders(_page(line)) == [], line


def test_the_slot_fits_the_gate_that_has_to_catch_it():
    """D14's window is 60 characters inside the brackets. The first slot was 63
    and slipped through silently — a placeholder the gate cannot see is worse
    than none, because the scaffold then teaches the author that shipping it is
    fine."""
    inner = new_deck.SUP_MEASURE.strip("[]")
    assert len(inner) <= 60, f"the slot is {len(inner)} chars; D14 stops at 60"
    assert check_design.PLACEHOLDER.search(new_deck.SUP_MEASURE)
    assert check_design.PLACEHOLDER_MARKERS.search(inner)


def test_the_rule_reaches_the_prompt_tier_too():
    """Ten of twelve platforms run the checks; two get one pasted context. The
    scaffold cannot reach those, so the page recipe carries the same rule —
    otherwise the product goal ("any AI agent") is served by ten of twelve."""
    root = pathlib.Path(__file__).resolve().parents[1]
    core = (root / "prompts" / "lumi-style-core.md").read_text(encoding="utf-8")
    assert re.search(r"support line names what is\s+counted", core), (
        "the prompt tier must carry the measure-line rule")
    assert "position` page" in core, (
        "the prompt tier must carry the position-page exemption, or an author "
        "invents a unit for a 2x2")
    assert "issue tree decomposes" in core, (
        "the prompt tier must also say what to do on a quantitative-move page "
        "with no measure — otherwise an author invents one to clear the slot")


def test_the_scaffold_actually_emits_the_slot_end_to_end(tmp_path):
    """THE INTEGRATION, which the unit tests above do not reach and the
    fixtures cannot: `fixtures/deck-pass.en.html` declares no analytical move
    (only the BROKEN fixture does, deliberately — `build_fixtures.py:755`
    refuses a graded metric no fixture can fail), so nothing in the tracked
    corpus exercises this path. Without this test the change ships verified by
    hand only."""
    import subprocess
    import sys
    root = pathlib.Path(__file__).resolve().parents[1]
    outline = tmp_path / "outline.md"
    outline.write_text(
        "# Part 1\n"
        "- A market that grew while its leaders shrank\n"
        "analysis: compare | finding: A market that grew while its leaders "
        "shrank | implication: Re-price before the next cycle.\n"
        "- The frame that holds the choice\n"
        "analysis: position | finding: The frame that holds the choice | "
        "implication: Pick the quadrant you can defend.\n",
        encoding="utf-8")
    deck = tmp_path / "deck.html"
    subprocess.run(
        [sys.executable, str(root / "scripts/ops/new_deck.py"),
         "--outline", str(outline), "--out", str(deck), "--no-trace"],
        capture_output=True, text=True, cwd=root, check=True)
    raw = deck.read_text(encoding="utf-8")

    seeds = {}
    for m in re.finditer(r'data-analysis="([^"]+)"', raw):
        window = raw[m.start():m.start() + 2500]
        sup = re.search(r'class="sup">(.*?)</p>', window, re.S)
        seeds[m.group(1)] = re.sub(r"<[^>]+>", "", sup.group(1)) if sup else ""
    assert "compare" in seeds and "position" in seeds, seeds
    assert new_deck.SUP_MEASURE in seeds["compare"], (
        "a quantitative page must arrive with the measure slot")
    assert new_deck.SUP_MEASURE not in seeds["position"], (
        "a framework page must not be asked to invent a unit")

    # and the gate sees it in the real generated markup, not just in a string
    found = check_design.d14_placeholders(raw)
    assert any(f["text"].startswith("[TO FILL: the measure") for f in found), (
        "the slot must reach D14 through the real scaffold output")


def test_an_unfilled_slot_in_a_non_english_deliverable_is_caught_too():
    """THE ESCAPE THAT FALSIFIED THE CLAIM. `PLACEHOLDER_MARKERS` was
    English-only, so a deck carrying four unfilled Chinese slots printed
    `ok D14_placeholders 0` — byte-identical to a finished document. This
    release makes D14 the SOLE enforcement of the measure slot and the prompt
    tier teaches agents to author directly in the reader's language, so a
    marker list in one language is a gate that reads one language and reports
    clean on the rest. D12 eleven hundred lines away learned the same lesson on
    the first real Chinese deliverable."""
    for slot in ("[待填:度量、单位与期间]", "[待补:来源]", "[占位]", "[未定]"):
        assert check_design.d14_placeholders(_page(slot)), slot


def test_real_bracketed_content_is_not_swept_up_with_it():
    """The other direction: widening a marker list is how a gate starts failing
    correct prose. A year, a citation mark and a filled measure line must pass."""
    for ok in ("[2024]", "[i]", "分部收入,亿元,2024 年", "[…]"):
        assert check_design.d14_placeholders(_page(ok)) == [], ok


def test_a_move_outside_the_five_is_announced(tmp_path):
    """`check_outline` validates the vocabulary and this scaffold does not run
    it, so a typo shipped an invalid `data-analysis` and a quantitative page
    silently never got asked for its measure. It now says so on stderr."""
    import subprocess
    import sys
    root = pathlib.Path(__file__).resolve().parents[1]
    outline = tmp_path / "o.md"
    outline.write_text("# P1\n- A title\nanalysis: comparison | finding: A "
                       "title | implication: x.\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/ops/new_deck.py"),
         "--outline", str(outline), "--out", str(tmp_path / "d.html"),
         "--no-trace"], capture_output=True, text=True, cwd=root, check=True)
    assert "is not one of" in proc.stderr and "comparison" in proc.stderr
