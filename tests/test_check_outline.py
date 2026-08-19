"""check_outline — the machine half of the storyline review beat.

That beat is the only defence completeness has, since C5 reports and never
gates. These tests are mostly about what the script refuses to decide.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_outline as co  # noqa: E402

GOOD = """genre: consulting
storyline: market-analysis

## Where the market is going
- Demand grew 12% while capacity grew 3%
- Three segments carry that growth, and one is closing
"""


def _verdicts(text):
    *_rest, findings = co.review(text)
    return {f["check"]: f["verdict"] for f in findings}


def test_a_title_with_a_verb_is_not_a_label():
    assert not co.is_label("Demand grew while capacity did not")


def test_a_title_with_a_figure_is_not_a_label():
    assert not co.is_label("Three segments, one closing by 2027")


def test_a_question_is_not_a_label():
    """A question sets up an answer; it is doing the same work as an assertion."""
    assert not co.is_label("Can the rural gap close without new hardware?")


def test_a_bare_noun_phrase_is_a_label():
    assert co.is_label("Market overview")


def test_label_titles_are_reported_never_gated():
    """A topic label is still named — it just does not stop the build.

    The heuristic is a closed verb list and English's is not: at 0.1.522 it
    failed five titles that were plainly sentences because `stand`, `buys`,
    `consume`, `price` and `leaving` were absent from it. Whether a title
    asserts something is a judgement about prose, and this repo does not gate
    on those; the gate in this file is the outline mirror, which asks only
    whether two artifacts still agree.
    """
    text = GOOD.replace("- Demand grew 12% while capacity grew 3%",
                        "- Market overview")
    assert _verdicts(text)["topic-label titles"] == "note"


def test_a_sentence_title_is_not_called_a_label():
    """The material, not the model of it — convention 15.

    Every verb here was missing from the list that shipped before 0.1.522.
    """
    for title in ("Three things stand between us and the first contract",
                  "The raise buys delivery without the founders in the room",
                  "Four kinds of competitor, each leaving the same thing behind",
                  "Three owners, and only one may price an order"):
        assert not co.is_label(title), title


def test_a_group_of_one_fails():
    text = GOOD + "\n## Conclusion\n- Everything is fine and will stay fine\n"
    assert _verdicts(text)["group size"] == "FAIL"


def test_completeness_is_a_note_never_a_failure():
    """Structural compliance does not predict quality, so it cannot gate."""
    assert _verdicts(GOOD)["type completeness"] == "note"


def test_a_declared_omission_without_a_reason_fails():
    """The declaration is what separates a decision from a gap."""
    text = GOOD + "\nomitted: risks\n"
    assert _verdicts(text)["declared omission"] == "FAIL"


def test_a_declared_omission_with_a_reason_is_accepted():
    text = GOOD + "\nomitted: risks — the client commissioned these separately\n"
    _m, _g, omissions, _t, findings = co.review(text)
    assert omissions[0]["reason"]
    assert not any(f["check"] == "declared omission" for f in findings)


def test_an_undeclared_genre_fails():
    """Without it the checklist and the thresholds are guesses."""
    assert _verdicts(GOOD.replace("genre: consulting\n", ""))["genre"] == "FAIL"


def test_a_storyline_outside_the_vocabulary_fails():
    assert _verdicts(GOOD.replace("market-analysis", "invented"))["storyline"] == "FAIL"


def test_it_does_not_judge_the_read_through():
    """Whether the titles cohere is the point of the beat; a checker claiming
    to decide it would replace the beat rather than serve it."""
    checks = set(_verdicts(GOOD))
    assert not any("read" in c or "cohere" in c or "argument" in c for c in checks)


# A storyline with no typical-section checklist used to disable the whole
# block — including the GATING declared-omission check. `proposal` was admitted
# to STORYLINES at 0.1.491 and never given a checklist, so the newest storyline
# shipped with the gate already disarmed, and the output looked like a pass.

BARE_OMISSION = """genre: internal
storyline: {storyline}

## Group

- Demand grew 12% while capacity grew 3%
- Three segments carry that growth

omitted: risks
"""


def _verdict_map(text):
    *_, findings = co.review(text)
    return {f["check"]: f["verdict"] for f in findings}


def test_bare_omission_gates_on_a_storyline_that_has_a_checklist():
    v = _verdict_map(BARE_OMISSION.format(storyline="market-analysis"))
    assert v["declared omission"] == "FAIL"


def test_bare_omission_gates_on_a_storyline_that_has_none():
    """The same file, one word changed, used to exit 0."""
    v = _verdict_map(BARE_OMISSION.format(storyline="proposal"))
    assert v["declared omission"] == "FAIL"


def test_a_storyline_without_a_checklist_says_so_rather_than_staying_silent():
    v = _verdict_map(BARE_OMISSION.format(storyline="proposal"))
    assert v["type completeness"] == "not_measured"


def test_every_storyline_either_has_a_checklist_or_is_reported_unmeasured():
    import deliverable_registry as reg
    for s in reg.STORYLINES:
        v = _verdict_map(BARE_OMISSION.format(storyline=s))
        assert v["type completeness"] in ("note", "not_measured"), s
        assert v["declared omission"] == "FAIL", s


# The analysis declarations (analysis-rules.md AR-3), red and green.

def test_analysis_declaration_outside_the_five_moves_fails():
    text = ("genre: sales\nstoryline: product-intro\n\n## G\n"
            "- A title that asserts 3 things\n"
            "analysis: vibes | finding: f | implication: i\n")
    *_, findings = co.review(text)
    assert any(f["check"] == "analysis vocabulary" and f["verdict"] == "FAIL"
               for f in findings)


def test_analysis_coverage_is_reported_never_gated():
    text = ("genre: sales\nstoryline: product-intro\n\n## G\n"
            "- A title that asserts 3 things\n"
            "analysis: bridge | finding: f | implication: i\n"
            "- Another title asserting 5 things\n")
    *_, findings = co.review(text)
    cov = next(f for f in findings if f["check"] == "analysis coverage")
    assert cov["verdict"] == "note" and "1 of 2" in str(cov["detail"])
