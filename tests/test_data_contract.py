"""D21 — a figure that declares its data is held to it.

Opt-in by design: a figure declaring nothing is not failed. What is not
tolerated is a declaration that disagrees with the drawing, because a false
contract is worse than no contract — nor one that asserts nothing, because a
contract with no measured point cannot disagree with anything and would read as
coverage while grading nothing (0.1.660).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_design as cd  # noqa: E402

FIG = """<figure>
  <svg><text>Rural</text><text>40</text><text>Urban</text><text>78</text></svg>
  <figcaption>Fig 1. Rural density trails urban</figcaption>
  <script type="application/json" class="f-data">%s</script>
</figure>"""

AGREES = '{"series":[{"label":"Rural","value":40},{"label":"Urban","value":78}]}'


def _mismatches(payload):
    return cd.d21_data_contract(FIG % payload)["mismatches"]


def test_an_agreeing_declaration_passes():
    assert _mismatches(AGREES) == []


def test_a_value_not_on_the_drawing_fails():
    assert _mismatches('{"series":[{"label":"Urban","value":85}]}')


def test_a_series_not_on_the_drawing_fails():
    assert _mismatches('{"series":[{"label":"Suburban","value":78}]}')


def test_the_declaration_is_not_checked_against_itself():
    """With the script block left in the haystack, every declared value found
    itself and the check passed on figures that contradicted their drawing."""
    bad = _mismatches('{"series":[{"label":"Urban","value":85}]}')
    assert bad, "the declaration was matched against its own text"


def test_a_figure_that_declares_nothing_is_not_failed():
    """Opt-in: a checker that failed every undeclared figure would be off in a day."""
    plain = "<figure><svg><text>Rural</text></svg></figure>"
    result = cd.d21_data_contract(plain)
    assert result["declared"] == 0 and result["mismatches"] == []


def test_unparseable_declared_data_fails():
    """A contract nobody can read is not a contract."""
    assert _mismatches("{not json at all}")


def test_a_declaration_with_no_series_fails():
    assert _mismatches('{"note": "nothing here"}')


def _mfig(contract, drawn):
    marks = "".join(f"<text>{t}</text>" for t in drawn)
    return (f'<div class="fig"><svg>{marks}</svg>'
            f'<script type="application/json" class="f-data">'
            f'{json.dumps(contract)}</script></div>')


def test_a_contract_with_no_measured_point_is_the_finding():
    """The deliberate red. Both labels are on the drawing, so the existing
    checks all pass — and the contract still says nothing."""
    r = cd.d21_data_contract(
        _mfig({"series": [{"label": "North"}, {"label": "South"}]},
             ["North", "South"]))
    assert r["declared"] == 1
    assert any("no measured point" in m for m in r["mismatches"])


def test_a_contract_that_measures_and_agrees_passes():
    r = cd.d21_data_contract(
        _mfig({"series": [{"label": "A", "value": 42}]}, ["A", "42"]))
    assert r["mismatches"] == []


def test_a_contract_that_measures_and_disagrees_still_fails():
    """The guard must not shadow what D21 was already for."""
    r = cd.d21_data_contract(
        _mfig({"series": [{"label": "A", "value": 42}]}, ["A"]))
    assert any("nowhere on the drawing" in m for m in r["mismatches"])


def test_zero_is_a_measured_value_not_an_absent_one():
    """`0` is a reading, and `None` is "not recorded". Treating the two alike is
    the defect this repository has shipped more than once — a falsy scalar read
    as absence."""
    r = cd.d21_data_contract(
        _mfig({"series": [{"label": "A", "value": 0}]}, ["A", "0"]))
    assert r["mismatches"] == [], (
        "a declared 0 is a measurement; the contract asserts something")


def test_one_measured_point_among_labels_is_enough():
    """A chart may label many series and quantify one; the contract is not
    required to be exhaustive, only to assert something."""
    r = cd.d21_data_contract(
        _mfig({"series": [{"label": "A"}, {"label": "B", "value": 7}]},
             ["A", "B", "7"]))
    assert r["mismatches"] == []


# --- 0.1.662: the guard that was bypassed one character later ----------------

def test_an_empty_string_value_asserts_nothing():
    """THE BYPASS, found by two independent reviewers on the release that
    shipped the guard.

    `""` is not `None`, so it cleared a `value is not None` test — and then
    `shown` was `""` and the agreement search compiled to `(?<![\\d.])(?![\\d])`,
    an empty pattern matching almost anywhere. The contract passed BOTH halves
    having asserted nothing, printing output byte-identical to a measured,
    agreeing one, and flipping `evals/gates.json`'s D21 subject from "held
    nothing" to "held 1, ok". That is this guard's own accusation, committed by
    this guard.

    It is also the LIKELIER shape than the one the guard was written for: an
    unfilled numeric slot in a template emits `""` far more naturally than it
    omits the key, and D14 cannot see it because `""` is not `[TO FILL]`."""
    for empty in ('""', '"  "', '"\\t"'):
        found = _mismatches(
            '{"series":[{"label":"Rural","value":' + empty + '}]}')
        assert found and "no measured point" in found[0], (empty, found)


def test_a_boolean_is_not_a_reading():
    """`isinstance(False, int)` is true in Python, so `{"value": false}` went
    through `f"{v:g}"` and reported *"declares Rural = 0"* — a number the
    contract never wrote, checked against a drawing that never claimed it."""
    found = _mismatches('{"series":[{"label":"Rural","value":false}]}')
    assert found and "no measured point" in found[0], found
    assert "= 0" not in found[0], f"invented a number the contract never wrote: {found[0]}"


def test_zero_still_passes_after_the_string_fix():
    """The other direction, and the trap this repository has fallen into
    before (0.1.650 read a recorded `0` as "never recorded"). The test is on
    the emptiness of the RENDERING, never on the truthiness of the value."""
    assert cd.d21_data_contract(
        '<figure><svg><text>Rural</text><text>0</text></svg>'
        '<script type="application/json" class="f-data">'
        '{"series":[{"label":"Rural","value":0}]}</script></figure>'
    )["mismatches"] == []


def test_a_contract_of_non_objects_keeps_its_own_message():
    """The guard sits above the per-point loop, and its first cut `continue`d
    past it — so `{"series":["a","b"]}` lost the accurate *"a series point is
    not an object"* and got told to add a `value` to a string. Both FAIL, so no
    gate moved; the author was simply handed the wrong repair."""
    found = _mismatches('{"series":["Rural","Urban"]}')
    assert found and "not an object" in found[0], found


def test_a_measured_point_among_non_objects_is_still_read():
    """The mixed case must not regress into either message alone."""
    found = _mismatches('{"series":[{"label":"Rural","value":40},"junk"]}')
    assert any("not an object" in m for m in found), found
    assert not any("no measured point" in m for m in found), found
