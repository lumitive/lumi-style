"""The planted defects are present, and the split still covers every page.

**Why this file exists.** `build_fixtures.py` had no test of any kind, and the
thing it protects is subtle: a fixture that stops failing a metric turns that
metric into one nothing can tell from a rewrite that returns `ok`. That has
happened twice — 0.1.369 turned page 5 into a `stack` layout with no `.gd` and
D4's literal colour vanished with it; 0.1.549's re-split moved page 12 from a
content page to a part opener and took D4, D24 and D25 with it. Both times the
only net was `check_fixtures`' refusal to grade a metric no fixture fails, and
that net is per-METRIC: `opener_pacing` is failed by two fixtures, so the
deliberate overrun could be removed from the broken deck and the suite would
stay green on the degenerate one.

These tests assert the plants by their CONTENT, which is the same principle the
0.1.549 rewrite applied to the plants themselves.
"""
import build_fixtures as bf
import inspect_layout as il


def test_every_page_belongs_to_a_part():
    """A page added to PAGES with no split entry would fall off the last part."""
    assert sum(bf.SPLIT_PASS) == len(bf.PAGES)
    assert sum(bf.SPLIT_BROKEN) == len(bf.PAGES)
    assert len(bf.SPLIT_PASS) == len(bf.SPLIT_BROKEN) == 3


def test_the_broken_split_overruns_the_seam_ceiling_and_the_passing_one_does_not():
    """`opener_pacing`'s only deliberate red lives in this tuple. Two fixtures
    fail the metric, so `check_fixtures`' per-metric coverage rule would not
    notice if this one stopped."""
    assert max(bf.SPLIT_BROKEN) > il.OPENER_RUN_CEILING
    assert max(bf.SPLIT_PASS) <= il.OPENER_RUN_CEILING


def test_the_three_opener_marks_are_geometrically_distinct():
    """Three colours of one shape would leave the repetition check nothing real
    to separate."""
    marks = (bf.MARK_HEX, bf.MARK_TOWER, bf.MARK_WAVE)
    assert len(set(marks)) == 3
    import check_design as cd
    geoms = {cd._geometry(m) for m in marks}
    assert len(geoms) == 3


# Each planted defect, named by the text that makes it a defect rather than by
# the page it sits on. The metric each one feeds is in the comment.
PLANTS = (
    ("#ABCDEF", "D4_palette_literals: a literal colour"),
    ("[TO FILL]", "D14_placeholders: a slot that reached the reader"),
    ("i-handdrawn", "D33_icon_provenance: an icon in neither shipped set"),
    ('data-analysis="bridge"', "D32_shape_use: a declared move, no library shape"),
)


def test_every_planted_defect_is_in_the_broken_deck_and_none_in_the_passing_one():
    broken, passing = bf.build(broken=True), bf.build(broken=False)
    for needle, why in PLANTS:
        assert needle in broken, f"the plant for {why} is gone from the broken deck"
        assert needle not in passing, f"{why} leaked into the passing deck"


def test_the_broken_deck_repeats_a_mark_and_the_passing_deck_does_not():
    broken, passing = bf.build(broken=True), bf.build(broken=False)
    assert broken.count(bf.MARK_HEX) == 2          # part A and part C
    for mark in (bf.MARK_HEX, bf.MARK_TOWER, bf.MARK_WAVE):
        assert passing.count(mark) == 1


def test_a_split_that_does_not_cover_pages_refuses_to_build(monkeypatch):
    """The only protection against a new PAGES entry falling off the last part,
    and a guard whose red has never been seen is FM-01."""
    import pytest
    monkeypatch.setattr(bf, "SPLIT_PASS", (1, 1, 1))
    with pytest.raises(SystemExit) as exc:
        bf.build(broken=False)
    assert "belongs to" in str(exc.value)


def test_the_declared_total_is_the_number_of_pages_the_deck_holds():
    """0.1.549 dropped the cover from the total when the third opener landed, so
    both tracked fixtures shipped declaring one page fewer than they hold and
    the closing page repeated the previous page's number. Nothing caught it:
    `--check` compares the generator to its own artifact and they agreed, and D6
    asks only whether a total is PRESENT."""
    import re
    for broken in (True, False):
        doc = bf.build(broken=broken)
        pages = len(re.findall(r'<section class="page', doc))
        totals = {int(t) for t in re.findall(r"<span>\d+ / (\d+)</span>", doc)}
        assert totals == {pages}, (broken, pages, totals)
        numbers = re.findall(r"<span>(\d+) / \d+</span>", doc)
        assert len(numbers) == len(set(numbers)), (broken, "a page number repeats")
        assert numbers[-1] == str(pages)


def test_the_planted_altered_icon_does_not_reuse_an_id_the_sprite_holds():
    """It was `i-shield`, which the sprite already defines, so the document
    carried the id twice, every `<use>` resolved to the first (correct) one, and
    the planted defect existed in the markup and in no rendering of it."""
    import collections
    import re
    doc = bf.build(broken=True)
    ids = re.findall(r'<symbol[^>]*\bid="([^"]+)"', doc)
    assert [i for i, n in collections.Counter(ids).items() if n > 1] == []


def test_every_plant_keys_on_the_content_ordinal_not_the_page_number():
    """`page()`'s docstring says so; one plant still keyed on `i` after 0.1.549,
    which suppressed `.lead` on a different page in each deck."""
    import inspect
    import re
    src = inspect.getsource(bf.page)
    body = src[src.index('"""', src.index('"""') + 3):]
    assert not re.search(r"\bi == \d", body), "a plant still keys on the page number"
