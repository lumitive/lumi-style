"""The layer map: a comparison drawn as labelled bands.

Written from one review note — the drawing was complex, expressed none of the
prose beside it, and left the reader asking what the relation between its two
halves was. The page's claim was that a stack has two layers with different
properties, and the figure had no layer in it. Every refusal below is an INPUT
SHAPE: the drawing cannot be made from data that fails one.
"""
import re

import lanes_svg as ln
import pytest


def _spec(**over):
    s = {
        "move": "compare",
        "period": "2026-08",
        "reading": "the layer that moves bytes has donated; the one that draws has not",
        "cause": "a reading of each project's own governance",
        "source": "First-party reading, 2026-08-11.",
        "measure": {"name": "Who governs the layer", "unit": "body"},
        "subject": {"label": "A2UI", "lane": "content", "chip": "single vendor",
                    "state": "single", "value": 0},
        "lanes": [{"name": "transport", "note": "who carries the bytes"},
                  {"name": "content", "note": "who decides what is shown"}],
        "references": [{"label": "A2A", "lane": "transport",
                        "chip": "a foundation", "state": "neutral", "value": 1}],
    }
    s.update(over)
    return s


def test_every_layer_is_named_in_the_drawing():
    svg = ln.render(_spec())
    assert "TRANSPORT" in svg and "CONTENT" in svg


def test_every_item_and_its_criterion_reach_the_drawing():
    svg = ln.render(_spec())
    assert "A2UI" in svg and "single vendor" in svg
    assert "A2A" in svg and "a foundation" in svg


def test_one_lane_is_refused():
    """With one band there is nothing for the split to say and the figure is a
    row of chips — which is the figure this one replaces."""
    spec = _spec(lanes=[{"name": "content", "note": "n"}])
    spec["subject"]["lane"] = "content"
    spec["references"][0]["lane"] = "content"
    with pytest.raises(SystemExit, match="a split needs at least two"):
        ln.render(spec)


def test_an_item_in_no_declared_lane_is_refused():
    """NEVER A DEFAULT LANE. Dropping it into the first band draws a claim the
    spec does not make, and the reader cannot see that it was a guess."""
    spec = _spec()
    spec["references"][0]["lane"] = "wire"
    with pytest.raises(SystemExit, match="not one of"):
        ln.render(spec)


def test_a_free_text_verdict_is_refused():
    spec = _spec()
    spec["references"][0]["state"] = "quite good"
    with pytest.raises(SystemExit, match="the verdicts are"):
        ln.render(spec)


def test_an_item_with_no_chip_is_refused():
    """A name in a lane says only which lane. Without the chip the figure has
    one dimension, which is a grouped list."""
    spec = _spec()
    spec["references"][0]["chip"] = ""
    with pytest.raises(SystemExit, match="carries no `chip`"):
        ln.render(spec)


def test_the_subject_is_drawn_heavier_than_its_references():
    """The document's own subject is the one the reader is looking for."""
    svg = ln.render(_spec())
    assert 'stroke-width="2"' in svg


def test_the_source_is_the_last_text_node():
    """design-rules section 4 rule 17, and the owner's review put it exactly:
    the evidence line is a note above the footer rule, not a main position."""
    svg = ln.render(_spec())
    texts = re.findall(r'class="(\w+)"', svg)
    assert texts[-1] == "fnote"


def test_the_box_is_measured_from_the_drawing():
    """A fixed box leaves empty space that a `dense` page renders as a gap
    between the drawing and its own caption."""
    two = ln.render(_spec())
    spec = _spec()
    spec["lanes"].append({"name": "policy", "note": "who says what is allowed"})
    spec["references"].append({"label": "AP2", "lane": "policy",
                               "chip": "FIDO", "state": "neutral", "value": 1})
    three = ln.render(spec)
    def _h(svg):
        got = re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', svg)
        assert got, "the drawing declares no viewBox"
        return float(got.group(1))

    h2, h3 = _h(two), _h(three)
    assert h3 > h2, "a third band did not make the box taller"
