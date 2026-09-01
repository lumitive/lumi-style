"""The arithmetic moves: `decompose` and `bridge`, red and green.

**These are the only assertions in this package about the author's DATA.**
Every other check asks something about the document — whether a class is
declared, a reference resolves, a mark is drawn in proportion. A decompose
whose parts do not sum to its total is wrong about the world, and no check
could say so until an artefact held both the total and the parts.
"""
import re

import breakdown_svg as bd
import figure_spec as fs
import pytest
import waterfall_svg as wf

BASE = {"period": "FY25", "reading": "two segments carry most of it",
        "cause": "shares are measured, not modelled",
        "source": "Illustrative figures, not measured.",
        "measure": {"name": "Addressable spend", "unit": "CNY m"}}


def _dec(**over):
    spec = dict(BASE, move="decompose", total={"label": "All", "value": 100},
                parts=[{"label": "Manufacturing", "value": 48},
                       {"label": "Logistics", "value": 32},
                       {"label": "Everything else", "value": 20}])
    spec.update(over)
    return spec


def _bri(**over):
    spec = dict(BASE, move="bridge", before={"label": "FY24", "value": 100},
                after={"label": "FY25", "value": 140},
                pieces=[{"label": "Price", "delta": 60},
                        {"label": "Volume", "delta": -20}])
    spec.update(over)
    return spec


# --- the arithmetic ---------------------------------------------------------

def test_parts_that_sum_to_the_total_are_accepted():
    assert fs.problems(_dec()) == []


def test_parts_that_do_not_sum_are_refused_and_the_message_names_the_gap():
    found = fs.problems(_dec(parts=[{"label": "a", "value": 48},
                                    {"label": "b", "value": 20}]))
    assert len(found) == 1
    assert "sum to 68 against a total of 100" in found[0]
    assert "32 unaccounted for" in found[0]
    assert "MECE" in found[0]


def test_rounding_is_not_a_defect():
    """A CEILING, not a target: parts stated to one decimal do not sum exactly
    and refusing that would fail correct data."""
    assert fs.problems(_dec(parts=[{"label": "a", "value": 33.3},
                                   {"label": "b", "value": 33.3},
                                   {"label": "c", "value": 33.4}])) == []


def test_a_residual_just_past_the_ceiling_is_refused():
    """The ceiling is 0.5% of the total, so a 1% gap must not pass."""
    assert fs.problems(_dec(parts=[{"label": "a", "value": 99}])) != []


def test_small_numbers_are_judged_on_the_same_share():
    """A total of 0.4 with parts of 0.1 and 0.2 is 25% out and must not pass
    because the numbers happen to be small."""
    found = fs.problems(_dec(total={"label": "All", "value": 0.4},
                             parts=[{"label": "a", "value": 0.1},
                                    {"label": "b", "value": 0.2}]))
    assert len(found) == 1


def test_pieces_that_reconcile_are_accepted():
    assert fs.problems(_bri()) == []


def test_pieces_that_do_not_reconcile_are_refused():
    found = fs.problems(_bri(pieces=[{"label": "Price", "delta": 60}]))
    assert len(found) == 1
    assert "60 against a move from 100 to 140" in found[0]
    assert "asserting a cause it has not found" in found[0]


def test_the_arithmetic_is_silent_when_a_value_cannot_be_read():
    """`problems` has already said the value is unreadable; two findings for
    one cause reads as two defects."""
    found = fs.problems(_dec(parts=[{"label": "a", "value": "lots"}]))
    assert len(found) == 1 and "is not a number" in found[0]


# --- the drawings -----------------------------------------------------------

def test_a_breakdown_draws_each_part_at_its_own_share():
    svg = bd.render(_dec())
    widths = [float(w) for w in
              re.findall(r'data-datum="[\d.]+"[^>]*width="([\d.]+)"', svg)]
    assert len(widths) == 3
    assert widths[1] / widths[0] == pytest.approx(32 / 48, rel=0.05)


def test_only_the_leading_part_takes_the_accent():
    """One colour one meaning. Alternating two tokens put the first and third
    segments in the same green on a three-part bar, which reads as a kind."""
    svg = bd.render(_dec())
    assert svg.count('fill="var(--acc)"') == 1
    assert svg.count('fill="var(--tx3)"') == 2


def test_a_waterfall_floats_its_pieces_from_the_running_total():
    svg = wf.render(_bri())
    ys = [float(y) for y in
          re.findall(r'data-datum="[\d.]+"[^>]*y="([\d.]+)"', svg)]
    assert len(ys) == 4
    # the two levels sit lower on the page (larger y) than the floating pieces
    assert ys[0] > ys[1] and ys[3] > ys[2]


def test_a_waterfall_declares_the_magnitude_it_draws():
    """The sign is in the colour and the label; a probe measuring pixels has no
    way to read a negative length."""
    svg = wf.render(_bri())
    assert re.findall(r'data-datum="([\d.]+)"', svg) == ["100", "60", "20", "140"]
    assert "\u221220" in svg


def test_a_bridge_that_crosses_zero_is_refused():
    with pytest.raises(SystemExit, match="falls below zero"):
        wf.render(_bri(before={"label": "a", "value": 10},
                       after={"label": "b", "value": 40},
                       pieces=[{"label": "down", "delta": -30},
                               {"label": "up", "delta": 60}]))


def test_a_negative_part_is_refused_and_sent_to_the_bridge():
    with pytest.raises(SystemExit, match="a signed movement is a bridge"):
        bd.render(_dec(total={"label": "All", "value": 60},
                       parts=[{"label": "a", "value": 48},
                              {"label": "b", "value": 32},
                              {"label": "c", "value": -20}]))


def test_neither_tool_has_a_baseline_flag():
    import pathlib
    for name in ("waterfall_svg", "breakdown_svg"):
        src = (pathlib.Path(wf.ROOT) / f"scripts/render/{name}.py").read_text(
            encoding="utf-8")
        assert 'add_argument("--baseline"' not in src


@pytest.mark.parametrize("mod,move", [(bd, "decompose"), (wf, "bridge")])
def test_a_skeleton_is_refused(mod, move):
    with pytest.raises(SystemExit, match="still the skeleton"):
        mod.render(fs.skeleton(move))


@pytest.mark.parametrize("mod", [bd, wf])
def test_no_literal_colour_reaches_either_output(mod):
    svg = mod.render(_dec() if mod is bd else _bri())
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", svg), svg[:200]


@pytest.mark.parametrize("framework,fn", [("market-sizing", _dec),
                                          ("waterfall", _bri)])
def test_the_registrys_command_actually_runs(framework, fn, tmp_path):
    import json
    import pathlib
    import subprocess
    import sys

    import new_deck
    move = "decompose" if framework == "market-sizing" else "bridge"
    name, run = new_deck.tool_for(move, framework)
    assert name == framework, (framework, name, run)
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(fn()), encoding="utf-8")
    argv = [sys.executable if t == "python3" else t
            for t in run.replace("<spec.json>", str(spec)).split()]
    done = subprocess.run(argv, cwd=pathlib.Path(wf.ROOT),
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[:400]
    assert done.stdout.lstrip().startswith("<svg")


# --- what the first real deck built through this tool found ------------------

def _shares(*values):
    return _dec(total={"label": "All", "value": sum(values)},
                parts=[{"label": f"part {i}", "value": v}
                       for i, v in enumerate(values)])


def test_a_zero_part_gets_a_mark_and_not_a_sliver():
    """A zero part has no length, so it gets no segment — drawing one at a
    floor gives it ink proportional to nothing. It keeps its label, because
    "this category is empty" is often the whole finding: the first deck built
    through this tool existed to say that 0 of 27 changed files touched the
    specification."""
    svg = bd.render(_shares(17, 7, 3, 0))
    assert svg.count("<rect") == 3, "the zero part was drawn as a bar"
    assert 'data-datum="0"' in svg, "the zero lost its datum"
    assert "stroke-dasharray" in svg, "the zero has no mark at all"


def test_outside_labels_never_land_on_each_other():
    """Placing each label at its own segment's centre put two of them on top of
    each other, and clamping the overflow back inside the box — the first fix —
    pulled both to the right edge and did it again. They wrap to a second row
    now. Found by rendering the page and looking; the browser gate then
    confirmed it twice."""
    import re
    svg = bd.render(_dec(
        total={"label": "All", "value": 27},
        parts=[{"label": "samples/community", "value": 17},
               {"label": "agent_sdks/python", "value": 7},
               {"label": "docs, scripts and the lockfile", "value": 3},
               {"label": "specification/", "value": 0}]))
    outside = [(float(x), float(y), t) for x, y, t in re.findall(
        r'<text class="flbl" x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]*)</text>',
        svg) if "fill=" not in t]
    rows: dict[float, list] = {}
    for x, y, t in outside:
        rows.setdefault(y, []).append((x, len(t)))
    for y, labels in rows.items():
        labels.sort()
        for (x1, n1), (x2, _n2) in zip(labels, labels[1:]):
            assert x2 - x1 >= n1 * 4.0, (
                f"two labels on row {y} are {x2 - x1:.0f} apart and the left "
                f"one is {n1} characters wide")


def test_everything_below_the_bar_moves_with_the_label_rows():
    """A second row of labels that the axis name and the reading were drawn
    over would trade one collision for another."""
    import re
    one = bd.render(_shares(60, 40))
    two = bd.render(_dec(
        total={"label": "All", "value": 27},
        parts=[{"label": "samples/community", "value": 17},
               {"label": "agent_sdks/python", "value": 7},
               {"label": "docs, scripts and the lockfile", "value": 3},
               {"label": "specification/", "value": 0}]))

    def axis_y(svg):
        m = re.search(r'<text class="axname-x"[^>]*y="([\d.]+)"', svg)
        assert m, "the drawing names no x axis"
        return float(m.group(1))
    assert axis_y(two) > axis_y(one), (
        "the axis name did not move down for the second row of labels")
