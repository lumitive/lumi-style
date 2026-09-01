"""`benchmark_svg` and `radar_svg`, red and green.

Both draw AR-1's `compare` move, and both refuse the distortions their figure
form is easiest to lie with: a truncated axis for the bar, a per-axis range for
the radar. Neither can express one — there is no `--baseline` on either tool,
the same decision as `scatter_svg` having no minimum radius.
"""
import json
import re
import subprocess
import sys

import benchmark_svg as bm
import figure_spec as fs
import pytest
import radar_svg as rd

ROOT = __import__("pathlib").Path(bm.ROOT)

BASE = {"move": "compare", "period": "the first two quarters",
        "reading": "we sit above both references",
        "cause": "direction not tested",
        "source": "Illustrative figures, not measured.",
        "measure": {"name": "Time to first value", "unit": "days"}}


def _bench(**over):
    spec = dict(BASE, subject={"label": "Us", "value": 34},
                references=[{"label": "Peer median", "value": 21},
                            {"label": "Best in class", "value": 12}])
    spec.update(over)
    return spec


def _radar(**over):
    spec = dict(BASE,
                criteria=[{"name": "Breadth"}, {"name": "Depth"},
                          {"name": "Speed"}],
                subject={"label": "Us", "values": [8, 4, 7]},
                references=[{"label": "Peer", "values": [5, 7, 5]}])
    spec.update(over)
    return spec


# --- the benchmark ----------------------------------------------------------

def test_bar_length_is_linear_in_the_value_from_zero():
    """The axis starts at zero and there is no flag to move it. A truncated
    axis is this form's commonest distortion and the hardest to catch."""
    svg = bm.render(_bench())
    widths = [float(w) for w in re.findall(r'data-datum="\d+"[^>]*width="([\d.]+)"', svg)]
    assert len(widths) == 3
    # 34 : 21 : 12 — the ratios survive to the drawn length
    assert widths[1] / widths[0] == pytest.approx(21 / 34, rel=0.01)
    assert widths[2] / widths[0] == pytest.approx(12 / 34, rel=0.01)


def test_there_is_no_baseline_flag():
    assert "--baseline" not in bm.main.__doc__ if bm.main.__doc__ else True
    src = (ROOT / "scripts/render/benchmark_svg.py").read_text(encoding="utf-8")
    assert "add_argument(\"--baseline\"" not in src


def test_every_bar_declares_its_own_value():
    svg = bm.render(_bench())
    assert re.findall(r'data-datum="([\d.]+)"', svg) == ["34", "21", "12"]


def test_the_subject_and_its_references_differ_only_by_token():
    svg = bm.render(_bench())
    assert 'fill="var(--acc)"' in svg and 'fill="var(--tx3)"' in svg
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", svg)


def test_the_axis_carries_the_shipped_class_and_the_unit():
    svg = bm.render(_bench())
    assert 'class="axname-x"' in svg
    assert "Time to first value" in svg and "days" in svg


def test_the_source_is_the_last_text_node():
    """§4 rule 17: the source lives inside the drawing, and last."""
    svg = bm.render(_bench())
    texts = re.findall(r"<text[^>]*>", svg)
    assert 'class="fnote"' in texts[-1]


def test_a_compare_with_no_reference_is_refused_naming_ar1():
    with pytest.raises(SystemExit, match="AT LEAST ONE reference"):
        bm.render(_bench(references=[]))


def test_a_negative_value_is_refused_rather_than_drawn():
    with pytest.raises(SystemExit, match="negative value"):
        bm.render(_bench(subject={"label": "Us", "value": -3}))


def test_an_unreadable_value_is_refused_rather_than_guessed():
    """The CONTRACT catches it now, one layer before the renderer: a quantity
    that is not a number was "filled" until 0.1.669 and only the tools that
    happened to have a numeric guard refused it."""
    with pytest.raises(SystemExit, match="is not a number"):
        bm.render(_bench(subject={"label": "Us", "value": "many"}))


def test_all_zero_is_refused():
    with pytest.raises(SystemExit, match="every value is zero"):
        bm.render(_bench(subject={"label": "Us", "value": 0},
                         references=[{"label": "Peer", "value": 0}]))


def test_the_wrong_move_is_refused_and_names_the_registry():
    spec = dict(_bench(), move="correlate", x={"name": "a", "unit": "u"},
                y={"name": "b", "unit": "v"},
                points=[{"x": 1, "y": 2}, {"x": 3, "y": 4}])
    with pytest.raises(SystemExit, match="this tool draws"):
        bm.render(spec)


def test_the_bars_are_centred_and_the_rules_span_only_them():
    """Found by rendering it: a three-row figure left its bars at the top and
    ran full-height tick lines through two thirds of empty box."""
    svg = bm.render(_bench())
    ys = [float(y) for y in re.findall(r'data-datum="\d+"[^>]*y="([\d.]+)"', svg)]
    rule_tops = [float(y) for y in re.findall(r'<line [^>]*y1="([\d.]+)"', svg)]
    assert min(ys) > 34 + 20, "the bars still start at the top of the box"
    assert min(rule_tops) == pytest.approx(min(ys) - 9, abs=12)


# --- the radar --------------------------------------------------------------

def test_the_vertex_carries_the_datum_and_the_polygon_does_not():
    """A radar's area grows with the SQUARE of its values, so grading the shape
    would grade the square of what the reader is asked to compare."""
    svg = rd.render(_radar())
    assert "<polygon" in svg
    assert not re.search(r'<polygon[^>]*data-datum', svg)
    assert len(re.findall(r'<circle[^>]*data-datum', svg)) == 6


def test_the_vertices_declare_a_radial_encoding_and_a_centre():
    """Every vertex is the same dot, so a probe measuring bounding boxes reads
    them as equal and reports a correct radar as distorted. The centre is a
    rendered element so the probe stays a second implementation."""
    svg = rd.render(_radar())
    assert svg.count('data-encoding="radial"') == 6
    assert svg.count("data-radial-origin") == 1


def test_every_spoke_shares_one_zero_to_max_scale():
    svg = rd.render(_radar())
    pts = re.findall(r'<circle data-datum="([\d.]+)" data-encoding="radial" '
                     r'cx="([\d.]+)" cy="([\d.]+)"', svg)
    origin = re.search(r'data-radial-origin="1" cx="([\d.]+)" cy="([\d.]+)"', svg)
    assert origin, "the drawing declares no centre to measure from"
    ox, oy = float(origin.group(1)), float(origin.group(2))
    dist = {float(v): ((float(x) - ox) ** 2 + (float(y) - oy) ** 2) ** 0.5
            for v, x, y in pts}
    top = max(dist)
    for v, d in dist.items():
        assert d / dist[top] == pytest.approx(v / top, rel=0.02), (v, d)


def test_a_radar_with_two_criteria_is_refused():
    with pytest.raises(SystemExit, match="at least three"):
        rd.render(_radar(criteria=[{"name": "a"}, {"name": "b"}],
                         subject={"label": "Us", "values": [1, 2]},
                         references=[{"label": "P", "values": [2, 1]}]))


def test_a_radar_with_no_criteria_sends_the_author_to_the_bar():
    spec = _bench()
    with pytest.raises(SystemExit, match="benchmark_svg"):
        rd.render(spec)


def test_a_missing_spoke_is_refused():
    with pytest.raises(SystemExit, match="one value per criterion"):
        rd.render(_radar(subject={"label": "Us", "values": [8, 4]}))


def test_a_negative_score_is_refused_rather_than_mirrored():
    with pytest.raises(SystemExit, match="below zero"):
        rd.render(_radar(subject={"label": "Us", "values": [8, -4, 7]}))


def test_no_literal_colour_reaches_either_output():
    for svg in (bm.render(_bench()), rd.render(_radar())):
        assert not re.search(r"#[0-9a-fA-F]{3,6}\b", svg), svg[:200]


# --- both, through the registry ---------------------------------------------

@pytest.mark.parametrize("framework,spec_fn", [("benchmark-table", _bench),
                                               ("radar", _radar)])
def test_the_registrys_command_actually_runs(framework, spec_fn, tmp_path):
    """The 0.1.665 defect, replayed for both new tools: the command the
    scaffold prints on the page must be one an author can type."""
    import new_deck
    name, run = new_deck.tool_for("compare", framework)
    assert name == framework, (framework, name, run)
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(spec_fn()), encoding="utf-8")
    argv = [sys.executable if t == "python3" else t
            for t in run.replace("<spec.json>", str(spec)).split()]
    done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[:400]
    assert done.stdout.lstrip().startswith("<svg")


@pytest.mark.parametrize("mod", [bm, rd])
def test_a_skeleton_is_refused_by_both(mod):
    with pytest.raises(SystemExit, match="still the skeleton"):
        mod.render(fs.skeleton("compare"))
