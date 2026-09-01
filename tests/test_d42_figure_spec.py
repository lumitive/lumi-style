"""D42 — a page that declares its data must be able to produce it.

**Written because the gate had no pytest test at all.** A mutation review found
seven mutations of `d42_figure_spec` surviving a green suite, two of them
surviving CI as well: deleting the branch that reports a malformed spec — the
reason the gate exists — and collapsing its could-not-look answer back into
`n/a`. Its only coverage was three fixture verdicts, of which the one red was
the easiest branch `load()` has.
"""
import json
import pathlib

import check_design
import pytest

GOOD = {"move": "decompose", "period": "FY25",
        "reading": "two segments carry most of it",
        "cause": "shares are measured, not modelled",
        "source": "Synthetic, not measured.",
        "measure": {"name": "Spend", "unit": "CNY m"},
        "total": {"label": "All", "value": 100},
        "parts": [{"label": "a", "value": 60}, {"label": "b", "value": 40}]}


def _page(tmp_path, spec=GOOD, ref="figures/f.json", analysis="decompose",
          write=True, order="analysis-first"):
    if write and spec is not None:
        (tmp_path / ref).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / ref).write_text(json.dumps(spec) if isinstance(spec, dict)
                                    else spec, encoding="utf-8")
    adecl = f' data-analysis="{analysis}"' if analysis else ""
    sdecl = f' data-figure-spec="{ref}"'
    attrs = adecl + sdecl if order == "analysis-first" else sdecl + adecl
    return (f'<html lang="en"><body><section class="page" id="p1"{attrs}>'
            f'<div class="fig"><svg><rect/></svg></div></section></body></html>')


# --- the four answers -------------------------------------------------------

def test_a_document_declaring_nothing_is_n_a_not_ok(tmp_path):
    """`n/a` and `ok` must not be the same line: a document never asked and a
    document that declared its data and delivered it are different facts, and
    `evals/gates.json`'s `na_means` is where that silence is declared honest."""
    assert check_design.d42_figure_spec("<html><body></body></html>",
                                        tmp_path) is None


def test_a_declared_spec_that_resolves_is_clean(tmp_path):
    r = check_design.d42_figure_spec(_page(tmp_path), tmp_path)
    assert r == {"declared": 1, "broken": []}


def test_a_missing_spec_is_reported(tmp_path):
    r = check_design.d42_figure_spec(_page(tmp_path, write=False), tmp_path)
    assert len(r["broken"]) == 1
    assert "could not be read" in r["broken"][0]["why"]


def test_a_spec_that_parses_and_is_wrong_is_reported(tmp_path):
    """The branch that had no failing case anywhere in the repository. Deleting
    it left preflight, CI and pytest entirely green."""
    bad = dict(GOOD, parts=[{"label": "a", "value": 60},
                            {"label": "b", "value": 28}])
    r = check_design.d42_figure_spec(_page(tmp_path, bad), tmp_path)
    assert len(r["broken"]) == 1
    assert "do not account for the total" in r["broken"][0]["why"]


def test_an_unresolvable_reference_is_broken_not_absent(tmp_path):
    """A declaration nobody could resolve is a broken declaration. Collapsing
    this into the `n/a` above was invisible to every test."""
    r = check_design.d42_figure_spec(_page(tmp_path), None)
    assert len(r["broken"]) == 1
    assert "directory is unknown" in r["broken"][0]["why"]


def test_a_skeleton_is_a_finding(tmp_path):
    """It was skipped, on the reasoning that D14 refuses the slot beside it —
    and D14 reads the document, never this file. A spec with real numbers and
    one leftover `[TO FILL]` source passed both gates."""
    sk = dict(GOOD, source="[TO FILL: where these observations came from]")
    r = check_design.d42_figure_spec(_page(tmp_path, sk), tmp_path)
    assert len(r["broken"]) == 1
    assert "still the scaffold's skeleton" in r["broken"][0]["why"]


def test_unparseable_json_is_reported(tmp_path):
    r = check_design.d42_figure_spec(_page(tmp_path, "{ truncated"), tmp_path)
    assert len(r["broken"]) == 1 and "not JSON" in r["broken"][0]["why"]


# --- every finding, not the first -------------------------------------------

def test_every_finding_reaches_the_report(tmp_path):
    """`problems()` appends the arithmetic LAST, so reporting `found[0]` made
    the one assertion in this package about the author's data surface only when
    it was the sole problem on a spec."""
    bad = dict(GOOD, parts=[{"label": "a", "value": 60},
                            {"label": "b", "value": 28}])
    bad.pop("period")
    r = check_design.d42_figure_spec(_page(tmp_path, bad), tmp_path)
    whys = [b["why"] for b in r["broken"]]
    assert len(whys) == 2, whys
    assert any("do not account for the total" in w for w in whys)


# --- the page and its spec must agree ---------------------------------------

@pytest.mark.parametrize("order", ["analysis-first", "spec-first"])
def test_a_page_disagreeing_with_its_spec_is_reported_either_attribute_order(
        tmp_path, order):
    """Searching backwards a fixed number of characters found nothing when the
    page wrote `data-figure-spec` first — printing exactly what a correct page
    prints, inside a check written to fix that class."""
    r = check_design.d42_figure_spec(
        _page(tmp_path, analysis="bridge", order=order), tmp_path)
    assert len(r["broken"]) == 1
    assert 'data-analysis="bridge"' in r["broken"][0]["why"]


def test_the_two_can_sit_far_apart(tmp_path):
    (tmp_path / "figures").mkdir(exist_ok=True)
    (tmp_path / "figures/f.json").write_text(json.dumps(GOOD), encoding="utf-8")
    raw = ('<section class="page" id="p1" data-analysis="bridge">'
           + "<p>filler</p>" * 900
           + '<div data-figure-spec="figures/f.json"></div></section>')
    r = check_design.d42_figure_spec(raw, tmp_path)
    assert len(r["broken"]) == 1, "a character window let the two drift apart"


def test_the_page_id_survives_attribute_order(tmp_path):
    raw = _page(tmp_path).replace('<section class="page" id="p1"',
                                  '<section id="p9" class="page"')
    r = check_design.d42_figure_spec(
        raw.replace('data-analysis="decompose"', 'data-analysis="bridge"'),
        tmp_path)
    assert r["broken"][0]["page"] == "p9", "the finding lost its address"


# --- it is registered and it gates ------------------------------------------

def test_the_metric_is_produced_and_graded():
    """A metric absent from `measure`'s dict, or from `grade`'s rows, runs on
    nothing — and both mutations survived the whole suite."""
    src = (pathlib.Path(check_design.__file__)).read_text(encoding="utf-8")
    assert '"D42_figure_spec": d42_figure_spec(raw, path.parent)' in src
    assert '"D42_figure_spec",' in src
    assert '"=0 (gates)"' in src
