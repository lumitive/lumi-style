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


def test_a_layer_map_needs_no_value_it_never_draws(tmp_path):
    """AG-10: a gate a correct answer cannot satisfy does not get obeyed, it
    gets satisfied. `lanes_svg` reads no `value` at all, and for one release
    the spec layer demanded one on the subject and on every reference — so a
    correct six-item layer map was refused until fake numbers were invented,
    and `check_facts` then required those inventions in the fact contract too.
    """
    import figure_spec
    spec = _spec()
    for item in [spec["subject"], *spec["references"]]:
        item.pop("value", None)
    assert figure_spec.problems(spec) == []
    svg = ln.render(spec)
    assert "A2UI" in svg and "single vendor" in svg


def test_a_radar_still_needs_its_values():
    """The relief is the layer map's, not compare's. A radar with no values
    draws a shape the data does not have."""
    import figure_spec
    spec = _spec()
    spec.pop("lanes")
    spec["criteria"] = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
    assert any("value per criterion" in p for p in figure_spec.problems(spec))


def test_a_declared_lane_with_no_items_is_refused():
    """The mirror of the undeclared-lane refusal, and it was missing: a spec
    whose items all sat in one band drew the other full-width and empty, which
    is a two-layer claim on evidence for one."""
    spec = _spec()
    spec["subject"]["lane"] = "transport"
    with pytest.raises(SystemExit, match="carry no items"):
        ln.render(spec)


def test_a_lane_declared_twice_is_refused():
    spec = _spec()
    spec["lanes"].append({"name": "transport", "note": "again"})
    with pytest.raises(SystemExit, match="declared twice"):
        ln.render(spec)


def test_a_chip_that_needs_three_lines_is_refused():
    """It ran past the chip's own bottom edge. `wrap` keeps emitting lines
    however narrow the box, so nothing stopped it."""
    spec = _spec()
    # A CROWDED LANE, which is where it bit: five chips share the band, so
    # each is narrow and a sentence-length criterion runs past the bottom.
    spec["references"] = [
        dict(spec["references"][0], label=f"P{i}",
             chip=("a governance arrangement described at such length that it "
                   "stops being a criterion and becomes the explanation of one"))
        for i in range(5)]
    with pytest.raises(SystemExit, match="chip holds two"):
        ln.render(spec)


def test_every_chip_stays_inside_its_own_box():
    """Measured rather than asserted: the last chip line's baseline against the
    chip rectangle's bottom edge."""
    svg = ln.render(_spec())
    chips = [(float(m.group(1)), float(m.group(2))) for m in
             re.finditer(r'<rect x="[\d.]+" y="([\d.]+)" width="[\d.]+" '
                         r'height="([\d.]+)" rx="6"', svg)]
    assert chips, "no chip was drawn"
    bottoms = [top + h for top, h in chips]
    texts = [float(y) for y in re.findall(r'class="ftick" x="[\d.]+" y="([\d.]+)"', svg)]
    for y in texts:
        assert any(y <= b for b in bottoms), f"chip text at {y} is below every chip"
