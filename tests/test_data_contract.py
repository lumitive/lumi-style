"""D21 — a figure that declares its data is held to it.

Opt-in by design: a figure declaring nothing is not failed. What is not
tolerated is a declaration that disagrees with the drawing, because a false
contract is worse than no contract.
"""
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
