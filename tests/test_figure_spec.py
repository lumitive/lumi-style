"""The figure data contract, red and green, per move (FM-01 discipline).

Every refusal below is an INPUT SHAPE rather than a gate: the drawing cannot be
made from a spec that fails one, so nothing here can be satisfied by an author
adding a token to placate a checker. That distinction is AG-10's, and this file
is where it is held.
"""
import json
import re

import figure_spec as fs
import pytest

UNIVERSAL = {"period": "the first twelve months",
             "reading": "it flattens past the midpoint",
             "cause": "direction not tested",
             "source": "Illustrative, not measured."}
MEASURE = {"name": "Revenue", "unit": "CNY m"}


def _spec(move, **over):
    spec = dict(UNIVERSAL, move=move)
    if move == "correlate":
        spec.update(x=dict(MEASURE), y={"name": "Adoption", "unit": "%"},
                    points=[{"x": 1, "y": 2}, {"x": 3, "y": 4}])
    elif move == "position":
        spec.update(axes={"x": dict(MEASURE), "y": {"name": "Depth", "unit": "score"}},
                    items=[{"label": "us", "x": 1, "y": 2},
                           {"label": "them", "x": 3, "y": 4}])
    elif move == "compare":
        spec.update(measure=dict(MEASURE), subject={"label": "us", "value": 10},
                    references=[{"label": "peer median", "value": 14}])
    elif move == "decompose":
        spec.update(measure=dict(MEASURE), total={"label": "all", "value": 10},
                    parts=[{"label": "a", "value": 6}, {"label": "b", "value": 4}])
    elif move == "bridge":
        spec.update(measure=dict(MEASURE), before={"label": "FY prior", "value": 10},
                    after={"label": "FY now", "value": 14},
                    pieces=[{"label": "price", "delta": 4}])
    spec.update(over)
    return spec


# --- every move has a shape that can be satisfied ---------------------------

@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_a_complete_spec_of_every_move_is_drawable(move):
    assert fs.problems(_spec(move)) == []


@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
@pytest.mark.parametrize("field", sorted(fs.UNIVERSAL_FIELDS))
def test_the_universal_half_is_required_of_every_move(move, field):
    spec = _spec(move)
    spec.pop(field)
    found = fs.problems(spec)
    assert found, f"{move} without {field} was accepted"
    if field != "move":
        assert any("DR-20" in x and "WR-5" in x for x in found), found


@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_every_move_names_a_measure_with_a_unit(move):
    """Where it lives is the move's business — `measure` for the
    single-quantity moves, the axes for the two-axis ones — and a spec that
    names none is refused whichever move it declares."""
    named = fs.measures_of(_spec(move))
    assert named, move
    for where, obj in named:
        assert obj.get("name") and obj.get("unit"), (move, where)
    spec = _spec(move)
    where = fs.measures_of(spec)[0][0]
    if "." in where:
        spec["axes"]["x"].pop("unit")
    elif where == "measure":
        spec["measure"].pop("unit")
    else:
        spec[where].pop("unit")
    assert any("unit" in x for x in fs.problems(spec)), fs.problems(spec)


# --- the shapes, one per move ------------------------------------------------

def test_a_compare_with_no_reference_is_refused_naming_ar1():
    """WR-5 rule 0, the judgment anchor, made structural. It was unchecked
    prose with `metric: null` and no candidate; here it is not a gate at all —
    a compare figure with nothing to compare against cannot be drawn."""
    found = fs.problems(_spec("compare", references=[]))
    assert len(found) == 1
    assert "AT LEAST ONE reference" in found[0]
    assert "AR-1" in found[0] and "WR-5" in found[0]


def test_an_absent_references_field_says_something_different():
    """Two states, two findings. Testing 'filled' reported both, and the one a
    reader saw first was the wrong one."""
    spec = _spec("compare")
    spec.pop("references")
    found = fs.problems(spec)
    assert len(found) == 1 and "does not carry it" in found[0]


def test_a_decompose_with_no_parts_is_refused():
    found = fs.problems(_spec("decompose", parts=[]))
    assert len(found) == 1 and "breaks a whole into parts" in found[0]


def test_a_bridge_with_no_pieces_is_refused():
    found = fs.problems(_spec("bridge", pieces=[]))
    assert len(found) == 1 and "is a comparison, not a bridge" in found[0]


def test_a_position_with_one_item_is_refused():
    found = fs.problems(_spec("position", items=[{"label": "us", "x": 1, "y": 2}]))
    assert len(found) == 1 and "not a position" in found[0]


def test_a_correlate_with_one_point_is_refused():
    found = fs.problems(_spec("correlate", points=[{"x": 1, "y": 2}]))
    assert len(found) == 1 and "One point is not a relation" in found[0]


def test_a_move_outside_the_five_is_refused_and_says_no_more():
    """One cause, one finding. Reporting the move AND every field its unknown
    shape lacks would bury the only sentence the author can act on."""
    found = fs.problems(dict(_spec("correlate"), move="vibes"))
    assert len(found) == 1 and "analysis-rules.md AR-1" in found[0]


def test_a_spec_that_is_not_an_object_is_refused():
    assert fs.problems(["a", "list"]) == [
        "the spec is list, not an object"]


# --- the skeleton -----------------------------------------------------------

@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_the_skeleton_invents_no_number(move):
    """IDEA-18 measured four invented numbers reaching a reader from this
    package's own sample block. A scaffold that writes a number hands the
    author a figure that looks sourced and is not."""
    assert re.search(r"[0-9]", json.dumps(fs.skeleton(move))) is None


@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_the_skeleton_carries_every_field_the_move_needs(move):
    sk = fs.skeleton(move)
    for field in fs.UNIVERSAL_FIELDS:
        assert field in sk, (move, field)
    for field in fs.MOVE_FIELDS[move]:
        assert field in sk, (move, field)


@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_the_skeleton_is_refused_by_the_renderers(move):
    """A skeleton that renders is a slot no gate can refuse: the drawing goes
    on the page, looks finished, and carries nobody's numbers."""
    assert fs.is_skeleton(fs.skeleton(move))
    with pytest.raises(SystemExit, match="still the skeleton"):
        fs.refuse_if_unusable(fs.skeleton(move))


def test_a_filled_spec_is_not_a_skeleton():
    assert not fs.is_skeleton(_spec("compare"))
    fs.refuse_if_unusable(_spec("compare"))          # must not raise


def test_a_skeleton_for_an_unknown_move_raises_rather_than_half_writing():
    with pytest.raises(ValueError, match="no skeleton for move"):
        fs.skeleton("vibes")


# --- loading: three answers, not two ----------------------------------------

def test_a_missing_spec_is_reported_not_silently_empty(tmp_path):
    spec, problem = fs.load(tmp_path / "nope.json")
    assert spec is None and problem and "could not be read" in problem


def test_an_unparseable_spec_is_reported(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{ truncated", encoding="utf-8")
    spec, problem = fs.load(p)
    assert spec is None and problem and "is not JSON" in problem


def test_a_json_list_is_reported_rather_than_returned(tmp_path):
    p = tmp_path / "list.json"
    p.write_text("[1, 2]", encoding="utf-8")
    spec, problem = fs.load(p)
    assert spec is None and problem and "not an object" in problem


def test_a_good_spec_loads_with_no_problem(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text(json.dumps(_spec("compare")), encoding="utf-8")
    spec, problem = fs.load(p)
    assert problem is None and spec is not None and spec["move"] == "compare"
