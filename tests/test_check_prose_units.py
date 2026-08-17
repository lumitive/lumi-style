"""Unit tests for check_prose's M6 classification.

Same discipline as tests/test_check_design_units.py: each behaviour is proven
able to pass AND to fail on synthetic input, because a check only ever seen
passing is FM-01. The fixtures exercise M6 at the verdict level — deck-pass
carries a planted enumeration label, deck-degenerate a real unsourced range —
and these pin the pattern level: which dashed pair is read as a label, which
is not, and why.

The question M6 answers is not "how long is this block". It was, at forty
characters, and that proxy let go twice (FM-13): once for the short label it
was written for, and once against a truthful 61-character sentence in a
shipped deliverable whose author rewrote the sentence to satisfy it.
"""
import pathlib

import check_prose

# Enough prose that `measure` has something to average; M6's window is the
# block, so the padding cannot reach the sentence under test.
PAD = ("<p>The programme ran for two cycles. Crews were briefed each week. "
       "Nothing else about the schedule changed.</p>")


def _measure(tmp_path, sentence, genre="sales"):
    path = tmp_path / "doc.en.html"
    path.write_text(
        f"<html lang='en'><body><section class='page' id='p1'>"
        f"{PAD}<p>{sentence}</p>{PAD}</section></body></html>",
        encoding="utf-8")
    return check_prose.measure(path, genre)


# The counting noun — the pair identifies things rather than measuring them.

def test_m6_a_long_enumeration_label_is_reported_not_counted(tmp_path):
    # The shipped false positive, verbatim. 61 characters, so the old
    # short-block backstop could not reach it, and the author reworded a
    # correct sentence to get past the gate.
    s = "Answer confirmation questions in blocks 1&#8211;3 and cross-region."
    r = _measure(tmp_path, s)
    assert r["M6_unsourced_ranges"] == 0
    assert r["M6_label_enumerations"], "the label must be reported, not silent"


def test_m6_other_counting_nouns_read_the_same_way(tmp_path):
    s = "Read the meters on rows 4&#8211;9 of the schedule and log the result."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 0


# Quantitative context still counts — this branch is first on purpose.

def test_m6_a_percentage_range_still_counts(tmp_path):
    # deck-degenerate's plant. If this stops failing, M6 loses the only
    # fixture that fails it and check_fixtures' coverage report goes red.
    s = "Rural read success runs 62&#8211;78% depending on terrain."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 1


def test_m6_a_counting_noun_does_not_rescue_a_percentage(tmp_path):
    # The order of the tests is the point: quantitative context wins over the
    # noun in front of it, or "pages 10&#8211;20% of target" would walk through.
    s = "Coverage across sites 3&#8211;7 reached 44% before the second cycle."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 1


def test_m6_a_plain_unsourced_range_still_counts(tmp_path):
    # No figure shape, no counting noun, too long for the backstop.
    s = "Volumes ran 12&#8211;18 above the plan across the two regions this year."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 1


# The backstop the counting noun does not cover.

def test_m6_gap_001s_short_label_is_still_exempt(tmp_path):
    # "Plastics (1&#8211;2)." has no counting noun in front of the pair, so it
    # survives only on the short-block backstop. Removing that rule would
    # reopen GAP-001.
    r = _measure(tmp_path, "Plastics (1&#8211;2).")
    assert r["M6_unsourced_ranges"] == 0
    assert r["M6_label_enumerations"]


def test_m6_a_sourced_range_is_never_counted(tmp_path):
    # The metric's actual subject: a range that names where it came from.
    s = "Throughput held at 40&#8211;60 units per shift (source: the meter log)."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 0


def test_m8_cv_floor_is_050_and_a_035_rhythm_now_fails():
    FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"
    """The floor moved 0.35 -> 0.50 at 0.1.508, replayed against the rebuilt
    corpus first: real documents sit 0.593-0.687 and the degenerate fixture at
    0.347, so 0.35 separated nothing real from anything. A document whose
    rhythm sits between the two floors is the case the raise exists to catch —
    uniform enough to read machine-made, and green under the old number."""
    import contextlib
    import io
    import json
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        check_prose.main([str(FIXTURES / "deck-degenerate.en.html"), "--json"])
    r = json.loads(buf.getvalue())[0]
    assert r["M8_length_cv"] < 0.50
    assert r["verdicts"]["M8_length_cv"] == "FAIL"
    assert ">=0.50" in r["targets"]["M8_length_cv"]
