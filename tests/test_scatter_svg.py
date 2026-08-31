"""The scatter renderer: the one figure form the shape library cannot hold.

Every assertion here is a rule from `references/design-rules.md` DR-20, and
several were written only after LOOKING at the render — the collisions, the
clipping and the invisible axis names are all things the markup passed and the
picture did not.
"""
import math
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "render"))

import scatter_svg as sc  # noqa: E402


def _spec(**over):
    """A spec carrying the FULL contract — the universal half as well as the
    correlate half. Before 0.1.667 this builder omitted `move` and `period`,
    and the renderer drew happily: four of the six things DR-20 demands of any
    figure carrying a number were absent and nothing asked."""
    spec = {
        "move": "correlate",
        "period": "the first twelve months",
        "x": {"name": "Setup time", "unit": "days"},
        "y": {"name": "Retention", "unit": "% of teams"},
        "reading": "retention falls with setup time",
        "cause": "direction not tested",
        "source": "Illustrative.",
        "points": [{"x": i, "y": 100 - 2 * i} for i in range(1, 13)],
    }
    spec.update(over)
    return spec


def _radii(svg):
    return [float(m) for m in re.findall(r'r="([0-9.]+)"[^>]*data-datum', svg)]


# --- the encoding, which is the whole reason a bubble can lie ----------------

def test_size_is_encoded_by_area_not_by_radius():
    """A radius drawn linearly in the value exaggerates it by the square: a
    datum twice another would draw four times the ink. Four values in a 1:4:9:16
    ratio must draw radii in 1:2:3:4."""
    spec = _spec(size={"name": "Seats", "unit": "seats"},
                 points=[{"x": i, "y": i, "size": v}
                         for i, v in enumerate((1, 4, 9, 16), start=1)])
    r = _radii(sc.render(spec))
    assert len(r) == 4, r
    # `abs_tol` at the grain the SVG actually carries: radii are written to one
    # decimal, so 4.25 reaches the file as "4.2". A tolerance tighter than the
    # emitted precision tests the formatter, not the encoding.
    for i in range(4):
        assert math.isclose(r[i], r[3] * (i + 1) / 4, abs_tol=0.06), r


def test_there_is_no_minimum_radius():
    """THE DELIBERATE RED for the fix. A first cut carried
    `r = R_MIN + (R_MAX - R_MIN) * sqrt(v / vmax)`, which drew a datum of 25
    against a maximum of 100 at 62% of the largest radius where area
    proportionality says 50% — a 23% overstatement of exactly the marks a reader
    is least able to check, produced by the code whose docstring said it encoded
    area. A floor IS a distortion."""
    spec = _spec(size={"name": "Seats", "unit": "seats"},
                 points=[{"x": 1, "y": 1, "size": 25}, {"x": 2, "y": 2, "size": 100}])
    small, large = _radii(sc.render(spec))
    assert math.isclose(small / large, 0.5, rel_tol=1e-9), (small, large)


def test_a_sized_mark_declares_the_encoding_it_was_drawn_to():
    """`inspect_layout`'s proportion check grades a mark against its value. It
    assumed LENGTH encoding, so a correctly drawn bubble failed it. The mark
    says which rule it was drawn to; the check reads it."""
    svg = sc.render(_spec(size={"name": "Seats", "unit": "seats"},
                          points=[{"x": 1, "y": 1, "size": 4},
                                  {"x": 2, "y": 2, "size": 16}]))
    assert svg.count('data-encoding="area"') == 2, svg


def test_an_unsized_scatter_declares_no_datum():
    """Nothing is encoded by size, so nothing claims to be."""
    assert "data-datum" not in sc.render(_spec())


# --- what the renderer refuses, and why -------------------------------------

def test_a_bubble_without_a_named_measure_is_refused():
    """DR-20 rule 2: a bubble is a THIRD measure. Ink whose meaning is not
    stated is ink the reader cannot check."""
    try:
        sc.render(_spec(points=[{"x": 1, "y": 1, "size": 10},
                                {"x": 2, "y": 2, "size": 20}]))
    except SystemExit as exc:
        assert "THIRD measure" in str(exc), exc
    else:
        raise AssertionError("a sized scatter with no size name was accepted")


def test_a_zero_size_is_refused_rather_than_floored():
    """Zero has no area. Drawing it at a floor would overstate every small mark
    on the figure, which is the distortion this encoding exists to avoid — so
    the renderer says so instead of quietly choosing for the author."""
    try:
        sc.render(_spec(size={"name": "Seats", "unit": "seats"},
                        points=[{"x": 1, "y": 1, "size": 0},
                                {"x": 2, "y": 2, "size": 9}]))
    except SystemExit as exc:
        assert "floor" in str(exc), exc
    else:
        raise AssertionError("a zero-area bubble was accepted")


def test_a_spec_with_no_usable_point_is_refused():
    try:
        sc.render(_spec(points=[{"x": None, "y": 3}, {"y": 4}]))
    except SystemExit as exc:
        # The CONTRACT refuses it now, before the renderer looks: "fewer than
        # two points with both an x and a y" is the same finding said earlier
        # and in AR-1's words. The renderer's own `nothing to draw` survives
        # for the case the contract cannot see — points whose values are
        # non-empty strings, which satisfy "filled" and are not numbers.
        assert "fewer than two points" in str(exc), exc
    else:
        raise AssertionError("an empty scatter was accepted")


# --- the vocabulary the package already ships -------------------------------

def test_axis_names_use_the_packages_own_classes():
    """`.axname-x` / `.axname-y` are not decoration: `figure_axis_named` gates
    on them, and `figure_axis_orientation` reads the y name's writing mode. A
    first cut labelled both axes with a generic class and the browser gate
    reported the figure as naming no axis at all."""
    svg = sc.render(_spec())
    assert 'class="axname-y"' in svg and 'class="axname-x"' in svg, svg
    assert "Retention, % of teams" in svg and "Setup time, days" in svg


def test_no_literal_colour_reaches_the_output():
    """design-rules §1: every mark takes a token, so the drawing follows the
    document's palette and its dark override."""
    svg = sc.render(_spec(series={"a": "red"},
                          points=[{"x": 1, "y": 1, "series": "a"},
                                  {"x": 2, "y": 3, "series": "a"}]))
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", svg), svg
    assert "var(--d-red)" in svg


def test_an_unknown_series_falls_back_rather_than_vanishing():
    """A typo in a series name must not drop the mark or emit a broken token."""
    svg = sc.render(_spec(series={"known": "teal"},
                          points=[{"x": 1, "y": 1, "series": "mystery"},
                                  {"x": 2, "y": 3, "series": "mystery"}]))
    assert svg.count("<circle") == 2
    assert "var(--d-blue)" in svg


# --- the trend line is a claim ----------------------------------------------

def test_the_trend_line_states_its_form_and_window():
    """DR-20: a fitted line is a claim. It may not appear silently, and it says
    plainly that it is not a fitted model."""
    svg = sc.render(_spec(), trend="smooth", window=4)
    assert "trend: local mean, 4-point window" in svg
    assert "not a fitted model" in svg


def test_no_trend_line_by_default():
    assert "trend:" not in sc.render(_spec())


def test_the_trend_is_a_curve_through_its_own_points():
    """`圆滑线` — a smooth curve, not a chain of segments. Catmull-Rom passes
    THROUGH each computed mean, so the curve is not a second smoothing nobody
    declared."""
    svg = sc.render(_spec(), trend="smooth")
    curve = re.search(r'<path d="(M[^"]*C[^"]*)"[^>]*stroke:var\(--acc\)', svg)
    assert curve, "the trend is not drawn as a cubic curve"
    assert curve.group(1).count("C") >= 3


# --- both orientations, because a layout that only works wide is wrong -------

def test_both_orientations_render_and_differ_in_shape():
    wide = sc.render(_spec(), orientation="landscape")
    tall = sc.render(_spec(), orientation="portrait")
    for svg, (w, h) in ((wide, sc.BOX["landscape"]), (tall, sc.BOX["portrait"])):
        assert f'viewBox="0 0 {w} {h}"' in svg
    assert sc.BOX["landscape"][0] > sc.BOX["landscape"][1]
    assert sc.BOX["portrait"][1] > sc.BOX["portrait"][0]


def test_the_reading_line_wraps_inside_the_narrow_box():
    """MEASURED, not guessed: in the 620-wide portrait box the reading line ran
    34 units outside its own viewBox, where `figure_clipped` found it. A
    sentence that fits the wide figure is not a sentence that fits the tall
    one."""
    long_reading = ("retention falls about 1.2 points per setup day up to "
                    "three weeks and then flattens completely for every team")
    tall = sc.render(_spec(reading=long_reading), orientation="portrait")
    wide = sc.render(_spec(reading=long_reading), orientation="landscape")
    assert tall.count("<text") > wide.count("<text"), (
        "the narrow box did not wrap a line the wide box fits on one")
    # The wrap must stay INSIDE the drawing. `|` bound across the whole pattern
    # in the first version of this assertion, so its second alternative was the
    # bare substring `then flattens` — supplied by the test itself — and it
    # held regardless of what the renderer did. The measured defect was
    # geometric (a reading line ran 34 units past its own viewBox), so the
    # assertion is geometric.
    box = re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', tall)
    assert box, "the portrait figure declares no viewBox to measure against"
    box_h = float(box.group(1))
    ys = [float(y) for y in re.findall(r'<text[^>]*\by="([\d.]+)"', tall)]
    assert ys and max(ys) <= box_h, (
        f"a text run sits at y={max(ys)} in a box {box_h} tall — the wrap "
        f"escaped the viewBox, which is the defect this test is named for")


def test_an_unknown_orientation_is_refused():
    try:
        sc.render(_spec(), orientation="diagonal")
    except SystemExit as exc:
        assert "orientation" in str(exc)
    else:
        raise AssertionError("an unknown orientation was accepted")


# --- the CLI, which is what an author actually runs --------------------------

def test_the_cli_emits_a_drawing_and_refuses_a_bad_spec(tmp_path):
    import json
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_spec()), encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render/scatter_svg.py"),
         "--data", str(good), "--trend", "smooth"],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    assert out.stdout.lstrip().startswith("<svg")

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render/scatter_svg.py"),
         "--data", str(bad)], capture_output=True, text=True, cwd=ROOT)
    assert out.returncode != 0 and "is not JSON" in out.stderr

    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render/scatter_svg.py"),
         "--data", str(tmp_path / "nope.json")],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode != 0 and "could not be read" in out.stderr
