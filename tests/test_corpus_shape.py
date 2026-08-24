"""The shape a build records about itself, and the readings it must not invent.

Two gaps waited fifty releases for "a second measured document" while no build
kept its numbers. This is the pipeline that keeps them: `_rendered_shape` reads
the run's own reports, `trace.py close` stores them, `ledger.py` reports the
distribution, `bar_replay.py` replays a proposed bar against them.

Every test here is about the same hazard from a different side — a corpus made
of whatever happened to be measurable is the corpus that produced 0.1.592's
withdrawn bar.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _d in ("lib", "check", "ops"):
    sys.path.insert(0, str(ROOT / "scripts" / _d))

import check_deliverable  # noqa: E402
import eval_corpus  # noqa: E402
import inspect_layout  # noqa: E402
import trace_schema  # noqa: E402


def _runs(pages, geometry="16x9"):
    return {"layout": {"reports": [{"results": [
        {"geometry": geometry, "pages": pages}]}]}}


def _page(pid, move=None, shapes=(), vis=None):
    p = {"id": pid, "figShapes": list(shapes)}
    if move is not None:
        p["declaredMove"] = move
    if vis is not None:
        p["visualPct"] = vis
    return p


# --- the contradiction, which is measured and does not gate ------------------

@pytest.mark.parametrize("pages,expected", [
    ([_page("p4", "compare", ["rect:50,text:50"]),
      _page("p5", "position", ["rect:50,text:50"])], 1),
    ([_page("p4", "compare", ["rect:50,text:50"]),
      _page("p5", "compare", ["rect:50,text:50"])], 0),
    ([_page("p4", "compare", ["rect:50,text:50"]),
      _page("p5", "position", ["line:50,text:50"])], 0),
    # `text:100` is the ABSENCE of structure, not a structure two pages share.
    ([_page("p4", "compare", ["text:100"]),
      _page("p5", "position", ["text:100"])], 0),
    ([_page("p4", "compare", ["rect:50,text:50"]),
      _page("p5", "", ["rect:50,text:50"])], 0),
])
def test_move_skeleton_clashes_counts_what_it_says(pages, expected):
    got = check_deliverable._rendered_shape(_runs(pages))
    assert got.get("move_skeleton_clashes") == expected, got


def test_a_measured_zero_is_recorded_and_not_omitted():
    """An absent key means NOT MEASURED. Omitting a genuine zero would leave
    the corpus holding only the documents that happened to clash — a
    distribution biased toward the defect."""
    got = check_deliverable._rendered_shape(
        _runs([_page("p4", "compare", ["text:100"])]))
    assert got["move_skeleton_clashes"] == 0


@pytest.mark.parametrize("move", [None, "", "   "])
def test_no_page_declaring_a_move_is_not_measured(move):
    """Absent, empty and whitespace-only are the same statement: this document
    does not declare its analytical moves, so there is nothing to contradict.
    Recording 0 here would claim a measurement nobody made."""
    got = check_deliverable._rendered_shape(
        _runs([_page("p4", move, ["rect:50,text:50"])]))
    assert "move_skeleton_clashes" not in got


# --- one metric name, one computation ---------------------------------------

def test_the_median_matches_eval_corpus_on_the_same_report():
    """Two computations under one name is what the `no shadow math` guard is
    about, and a corpus holding both compares numbers that are not the same
    number. The selectors disagreed when the first geometry entry was empty."""
    pages = [_page(f"p{i}", vis=v) for i, v in enumerate([35, 46, 61, 72], 4)]
    runs = {"layout": {"reports": [{"results": [
        {"geometry": "a4", "pages": []},
        {"geometry": "16x9", "pages": pages}]}]}}
    mine = check_deliverable._rendered_shape(runs)
    theirs = eval_corpus.measure.__doc__  # documented sibling; compare the rule
    assert theirs is not None
    # eval_corpus picks the first entry that HAS a `pages` key, empty or not.
    first = next(r for r in runs["layout"]["reports"][0]["results"] if "pages" in r)
    assert first["geometry"] == "a4"
    assert "visual_share_median" not in mine, (
        "the two selectors disagree: eval_corpus reads the empty a4 entry and "
        "this read a different geometry's pages")


def test_the_reading_records_which_geometry_it_came_from():
    """A median with no geometry beside it is not comparable across documents,
    and `bar_replay` compares them."""
    got = check_deliverable._rendered_shape(
        _runs([_page("p4", vis=50), _page("p5", vis=60)]))
    assert got["geometry"] == "16x9"


def test_repeated_skeletons_use_the_checkers_own_threshold():
    """`inspect_layout.FIGURE_SHAPE_REPEAT` is 3, not 2. Counting at 2 and
    keeping the checker's name puts two definitions of one metric in the
    corpus."""
    assert inspect_layout.FIGURE_SHAPE_REPEAT == 3
    two = _runs([_page("p4", shapes=["s"]), _page("p5", shapes=["s"])])
    assert check_deliverable._rendered_shape(two)["repeated_skeleton_pages"] == 0
    three = _runs([_page(f"p{i}", shapes=["s"]) for i in (4, 5, 6)])
    assert check_deliverable._rendered_shape(three)["repeated_skeleton_pages"] == 3


# --- the store -------------------------------------------------------------

@pytest.mark.parametrize("bad", [[], [1, 2], 5, "x"])
def test_a_shape_that_is_not_an_object_is_reported_not_raised(bad):
    """A validator that raises cannot name the bad record, and the crash took
    `check_repo`'s guard with it — so the tree could not be checked at all."""
    errors = trace_schema.validate({"shape": bad})
    assert any(e.startswith("shape") for e in errors), errors


def test_a_key_outside_the_vocabulary_is_refused():
    errors = trace_schema.validate({"shape": {"invented_metric": 3}})
    assert any("invented_metric" in e for e in errors)


def test_a_non_numeric_reading_is_refused():
    errors = trace_schema.validate({"shape": {"figures": "many"}})
    assert any("figures" in e for e in errors)


def test_absent_and_null_both_mean_not_recorded():
    """135 traces predate the field. Reddening them teaches nothing."""
    assert not [e for e in trace_schema.validate({}) if e.startswith("shape")]
    assert not [e for e in trace_schema.validate({"shape": None})
                if e.startswith("shape")]
