"""The two figures the owner's review said were missing or too simple.

Her review, page by page, is the specification these were built against: of
the development path, that the figure was too simple, carried no time axis, and
showed none of the time points the page stated; of the quadrant, that it was
too simple. Every refusal below is an INPUT SHAPE, not a gate: the drawing cannot
be made from data that fails one, so nothing here can be satisfied by adding a
token to placate a checker.
"""
import re

import figure_slots
import pytest
import quadrant_svg as qd
import timeline_svg as tl

BASE = {"period": "2025-12 to 2026-08", "reading": "three shipped, one pending",
        "cause": "direction not tested; a release history",
        "source": "The project's own version line.",
        "measure": {"name": "Public releases", "unit": "version"}}


def _path(**over):
    spec = dict(BASE, move="bridge", stages=[
        {"date": "2025-12", "name": "Announced", "body": "Apache 2.0", "state": "done"},
        {"date": "2026-04", "name": "v0.9 stable", "body": "four months on", "state": "done"},
        {"date": "2026-06", "name": "v0.9.1", "body": "recommended", "state": "now"},
        {"date": "Q4 2026", "name": "v1.0 final", "body": "certification", "state": "open"}])
    spec.update(over)
    return spec


def _quad(**over):
    spec = dict(BASE, move="position",
                axes={"x": {"name": "renders A2UI", "unit": "ordinal",
                            "low": "no renderer", "high": "full host"},
                      "y": {"name": "generated live", "unit": "ordinal",
                            "low": "static", "high": "generative"}},
                items=[{"label": "A2UI over A2A", "x": .82, "y": .86,
                        "note": "agent drives from the conversation", "state": "ours"},
                       {"label": "MCP Apps alone", "x": .14, "y": .34,
                        "note": "self-contained, own brand"}],
                open={"at": "upper-right", "head": "generative and host-framed",
                      "body": "the row v0.1.140 builds"})
    spec.update(over)
    return spec


# --- the timeline carries time ----------------------------------------------

@pytest.mark.parametrize("tier", tl.TIERS)
def test_every_stage_reaches_the_drawing(tier):
    """The defect this was written from: a staircase with four stages and two
    words on it. Every stage's date AND name must be in the SVG."""
    svg = tl.render(_path(), tier=tier)
    for s in _path()["stages"]:
        assert s["date"] in svg, (tier, s["date"])
        assert s["name"] in svg, (tier, s["name"])


@pytest.mark.parametrize("tier", tl.TIERS)
def test_a_stage_with_no_date_is_refused(tier):
    """The CONTRACT catches it first, and names which stage — a better message
    than the renderer's own. The renderer keeps its check as the last line of
    defence for a caller that reaches `render()` directly with a dict."""
    spec = _path()
    spec["stages"][1].pop("date")
    with pytest.raises(SystemExit, match=r"`stages\[1\]` does not give its date"):
        tl.render(spec, tier=tier)


def test_one_stage_is_not_a_path():
    with pytest.raises(SystemExit, match="at least two `stages`"):
        tl.render(_path(stages=[{"date": "2025-12", "name": "Announced"}]))


def test_a_state_outside_the_three_is_refused():
    """`open` is what draws a stage dashed. A free-text state would draw solid
    and read as delivered."""
    spec = _path()
    spec["stages"][3]["state"] = "maybe"
    with pytest.raises(SystemExit, match="not one of"):
        tl.render(spec)


def test_general_draws_the_unbuilt_stage_dashed():
    """The honesty of this tier: nothing dashed is built."""
    svg = tl.render(_path(), tier="general")
    assert "stroke-dasharray" in svg
    assert svg.count("stroke-dasharray") == 1, "only the `open` stage is dashed"


def test_pro_states_a_status_for_every_stage():
    svg = tl.render(_path(), tier="pro")
    for pill in ("shipped", "current", "not built"):
        assert pill in svg, pill


def test_light_flips_its_labels_past_the_midpoint():
    """So the last label does not hang off the right edge."""
    svg = tl.render(_path(), tier="light")
    assert 'text-anchor="start"' in svg and 'text-anchor="end"' in svg


@pytest.mark.parametrize("tier", tl.TIERS)
def test_the_axis_is_named_and_the_source_is_last(tier):
    svg = tl.render(_path(), tier=tier)
    assert 'class="axname-x"' in svg
    texts = re.findall(r"<text[^>]*>", svg)
    assert 'class="fnote"' in texts[-1], "the source is not the last text node"


@pytest.mark.parametrize("tier", tl.TIERS)
def test_no_literal_colour_reaches_the_timeline(tier):
    svg = tl.render(_path(), tier=tier)
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", svg), svg[:200]


# --- the quadrant is an argument --------------------------------------------

def test_every_item_carries_a_qualifier():
    """A name on a map is a logo. The qualifier is the difference the review
    named."""
    spec = _quad()
    spec["items"][0].pop("note")
    with pytest.raises(SystemExit, match="carry no `note`"):
        qd.render(spec)


def test_an_axis_with_no_ramp_is_refused():
    spec = _quad()
    spec["axes"]["x"].pop("high")
    with pytest.raises(SystemExit, match="no `low`/`high` ramp"):
        qd.render(spec)


def test_the_answer_quadrant_is_washed_and_named():
    svg = qd.render(_quad())
    assert "var(--acc-wash)" in svg
    assert "generative and host-framed" in svg
    assert "the row v0.1.140 builds" in svg


def test_only_one_quadrant_is_labelled():
    """Naming all four turns a finding into a legend."""
    svg = qd.render(_quad())
    assert svg.count("var(--acc-wash)") == 1


def test_an_exited_player_is_kept_and_dimmed():
    """Deleting them loses the finding; dimming them states it."""
    spec = _quad()
    spec["items"].append({"label": "Tome", "x": .3, "y": .55,
                          "note": "exited slides, 2025-03", "state": "exited"})
    svg = qd.render(spec)
    assert "Tome" in svg
    assert 'opacity="0.45"' in svg


def test_our_position_takes_its_own_token():
    svg = qd.render(_quad())
    assert "var(--lime)" in svg


def test_the_plot_is_one_rect_and_two_lines():
    """Four rects read as four categories; a 2x2 is two continua."""
    svg = qd.render(_quad())
    assert svg.count("<rect") == 2, "one plot rect plus the answer wash"


def test_a_placement_outside_the_axes_is_refused():
    spec = _quad()
    spec["items"][0]["x"] = 1.4
    with pytest.raises(SystemExit, match="fraction of each axis"):
        qd.render(spec)


def test_the_truth_condition_is_stated():
    """DR-11: a 2x2 must say its axes are independent."""
    assert "independent capabilities" in qd.render(_quad())


def test_both_axes_are_named_with_the_shipped_classes():
    svg = qd.render(_quad())
    assert 'class="axname-x"' in svg and 'class="axname-y"' in svg


# --- the slot interface ------------------------------------------------------

def test_a_shape_composed_with_no_content_is_refused():
    """The interface this replaces could express two words, so a `position`
    unit arrived as an empty box."""
    with pytest.raises(figure_slots.SlotError, match="composed with no slots"):
        figure_slots.compose("p126-2x2-01", [])


def test_a_slot_position_is_a_fraction_of_the_unit_not_the_box():
    """`preserveAspectRatio` scales a near-square unit to about 245 of the 640
    units available and centres it, so a fraction of the BOX lands outside the
    drawing. Measured: it did, twice, and only the render showed it."""
    x, _y, w, _h = figure_slots.fitted("p126-2x2-01")
    assert x > 100 and w < 400, (x, w)
    svg = figure_slots.compose("p126-2x2-01",
                               [{"at": (0.5, 0.5), "head": "centre"}])
    hit = re.search(r'<text[^>]*x="([\d.]+)"', svg)
    assert hit, "the composition emitted no text at all"
    got = float(hit.group(1))
    assert abs(got - (x + w / 2)) < 1.0, "the slot did not land on the drawing"


def test_a_slot_outside_the_unit_is_refused():
    with pytest.raises(figure_slots.SlotError, match="outside the drawing"):
        figure_slots.compose("p126-2x2-01", [{"at": (1.4, 0.5), "head": "x"}])


def test_text_is_styled_never_attributed():
    """A `fill=` attribute on a `<text>` loses to the stylesheet — the trap
    every reference figure in this package avoids without exception."""
    svg = figure_slots.compose("p126-2x2-01", [{"at": (.5, .5), "head": "x"}])
    assert 'style="fill:' in svg
    assert not re.search(r'<text[^>]*\sfill="', svg)


def test_the_use_takes_the_units_own_geometry():
    """All 206 viewBoxes have non-zero origins; a `<use>` without explicit
    x/y/width/height renders off-canvas and raises nothing."""
    svg = figure_slots.compose("p126-2x2-01", [{"at": (.5, .5), "head": "x"}])
    found = re.search(r'<use[^>]*>', svg)
    assert found, "the composition references no shape"
    use = found.group(0)
    for attr in ("x=", "y=", "width=", "height="):
        assert attr in use, attr
