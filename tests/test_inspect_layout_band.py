"""A stat band that renders outside its own box is a finding, not a judgement.

The measurement needs Chromium; the decision does not, so the decision is a
function and lives here — the pattern `test_inspect_layout_aspect.py` set.

Why the check exists at all: `.body > *` carries `min-height: 0` so a figure
can give back space it does not need. A band cannot give any back — its cells
are text at `align-items: start` — so the same declaration lets its grid row
collapse below the height the cells need, and they hang out of the bottom.
Found on a conformance deck whose band row computed to 35px for content
needing 61px; its labels landed on the footer. `collision` caught that one
only because the footer was there to be hit.
"""
import inspect_layout as il


def _page(pid, escapes=None, band=False):
    return {"id": pid, "hasBand": band or bool(escapes),
            "bandEscape": escapes or []}


def test_a_contained_band_is_not_a_finding():
    live = [_page("p1", band=True), _page("p2", band=True)]
    assert il._band_escaped(live) == []
    assert il._band_escape_worst(live) is None


def test_a_page_with_no_band_at_all_is_not_a_finding():
    assert il._band_escaped([{"id": "p1"}]) == []


def test_an_escaping_band_names_its_page():
    live = [_page("p1", band=True),
            _page("p9", [{"out": 45, "boxPx": 15, "needPx": 61}])]
    assert [r["id"] for r in il._band_escaped(live)] == ["p9"]


def test_the_worst_escape_wins_across_pages_and_bands():
    # Two bands on one page and a worse one on another: the report names the
    # single worst, and it must come from the right page rather than the first.
    live = [_page("p4", [{"out": 9, "boxPx": 52, "needPx": 61},
                         {"out": 20, "boxPx": 41, "needPx": 61}]),
            _page("p9", [{"out": 60, "boxPx": 0, "needPx": 61}])]
    worst = il._band_escape_worst(live)
    assert worst == {"out": 60, "boxPx": 0, "needPx": 61}


def test_the_box_and_the_need_are_both_reported():
    # "45px of labels are outside" is the symptom; "a 15px row for 61px of
    # content" is the defect, and a report carrying only the first sends the
    # reader looking at the labels.
    worst = il._band_escape_worst(
        [_page("p9", [{"out": 45, "boxPx": 15, "needPx": 61}])])
    assert worst["boxPx"] == 15 and worst["needPx"] == 61
