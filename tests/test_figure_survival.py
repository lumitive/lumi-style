"""What survives a rebuild, a translation and a fact check.

The figure spec exists so a figure's numbers outlive the build that drew them.
These are the four properties that makes true, and each was unavailable before
the artefact existed: nothing held the numbers, so nothing could be inherited,
redrawn, compared or counted.
"""
import json
import pathlib
import re
import subprocess
import sys

import breakdown_svg as bd
import check_facts
import check_outline
import figure_spec as fs
import pytest
import scatter_svg as sc

ROOT = pathlib.Path(bd.ROOT)

DEC = {"move": "decompose", "period": "FY25",
       "reading": "two segments carry most of it",
       "cause": "shares are measured, not modelled",
       "source": "Illustrative figures, not measured.",
       "measure": {"name": "Addressable spend", "unit": "CNY m"},
       "total": {"label": "All segments", "value": 100},
       "parts": [{"label": "Manufacturing", "value": 48},
                 {"label": "Logistics", "value": 32},
                 {"label": "Other", "value": 20}]}

COR = {"move": "correlate", "period": "the first twelve months",
       "reading": "adoption rises then flattens",
       "cause": "direction not tested",
       "source": "Illustrative figures, not measured.",
       "x": {"name": "Support hours", "unit": "hours"},
       "y": {"name": "Adoption", "unit": "% of seats"},
       "points": [{"x": 8, "y": 21}, {"x": 20, "y": 44}, {"x": 34, "y": 58}]}


# --- a rebuild inherits ------------------------------------------------------

@pytest.mark.parametrize("mod,spec", [(bd, DEC), (sc, COR)])
def test_rebuilding_from_an_unchanged_spec_is_byte_identical(mod, spec):
    """The whole point of the artefact: the drawing is a function of the spec,
    so a rebuild that changed it would mean the numbers were not the input."""
    assert mod.render(spec) == mod.render(spec)


@pytest.mark.parametrize("mod,spec,key", [(bd, DEC, "total"), (sc, COR, "x")])
def test_changing_the_spec_changes_the_drawing(mod, spec, key):
    """The other half, and the one that says the first is not vacuous: a
    renderer that ignored its input would also be byte-identical."""
    other = json.loads(json.dumps(spec))
    if key == "total":
        other["total"]["value"] = 200
        other["parts"] = [{"label": "Manufacturing", "value": 200}]
    else:
        other["x"]["name"] = "Something else entirely"
    assert mod.render(other) != mod.render(spec)


# --- translation redraws -----------------------------------------------------

def test_translating_the_labels_leaves_the_geometry_identical():
    """A translated deck redraws from the same spec with translated labels, so
    every mark lands in the same place. Before the spec existed a translation
    had to copy the SVG, which is how a figure's numbers and its language got
    welded together."""
    zh = json.loads(json.dumps(DEC))
    zh["measure"]["name"] = "可触达支出"
    zh["total"]["label"] = "全部分部"
    for part, name in zip(zh["parts"], ("制造", "物流", "其他")):
        part["label"] = name
    en_svg, zh_svg = bd.render(DEC), bd.render(zh)

    def geometry(svg):
        return re.findall(r'<rect data-datum="([\d.]+)"[^>]*x="([\d.]+)"'
                          r'[^>]*width="([\d.]+)"', svg)
    assert geometry(en_svg) == geometry(zh_svg)
    assert en_svg != zh_svg, "the labels did not change at all"


# --- the fact contract reads the spec ---------------------------------------

def _deck(tmp_path, spec, ref="figures/f1.json"):
    (tmp_path / "figures").mkdir(parents=True, exist_ok=True)
    (tmp_path / ref).write_text(json.dumps(spec), encoding="utf-8")
    doc = tmp_path / "deck.html"
    doc.write_text(
        f'<html lang="en"><body><section class="page" id="p1" '
        f'data-figure-spec="{ref}"><h2>Spend by segment</h2>'
        f'<div class="fig"><svg><text>drawn</text></svg></div>'
        f'</section></body></html>', encoding="utf-8")
    return doc


CONTRACT = ("## FACTS\n\n- Addressable spend is 100 CNY m in FY25.\n"
            "- Manufacturing is 48 CNY m.\n- Logistics is 32 CNY m.\n")


def test_a_figures_numbers_reach_the_fact_check(tmp_path):
    """`_visible` strips `<svg>`, so before this a deck could state a market
    size only inside its chart and `unsourced` came back empty."""
    doc = _deck(tmp_path, DEC)
    r = check_facts.compare(CONTRACT, doc.read_text(encoding="utf-8"),
                            base=doc.parent)
    # EXACTLY four: total, and three parts. A `>=` passes anything that
    # over-collects, and this number is 4 only because DEC's values have two or
    # three digits — `check_facts.facts()` ignores a lone digit, so a radar
    # spec of `[8, 4, 7]` contributes nothing at all. That limit is stated in
    # `spec_quantities`' docstring and pinned below.
    assert r["spec_quantities"] == 4
    # ITS OWN VERDICT, against its own reading of the contract. Folding the
    # spec's exact numbers into the prose-scraped set compared two
    # vocabularies: `QUANTITY` cannot start on `0.` and ignores a lone digit,
    # so `0.08` came back as the quantity 8 and correct data failed red line 1
    # on a number neither file contained.
    assert "20" in r["unsourced_spec_values"], r["unsourced_spec_values"]


def test_a_spec_the_document_names_and_cannot_produce_is_reported(tmp_path):
    doc = _deck(tmp_path, DEC)
    (tmp_path / "figures/f1.json").unlink()
    r = check_facts.compare(CONTRACT, doc.read_text(encoding="utf-8"),
                            base=doc.parent)
    assert r["spec_problems"], "a missing spec read as a document with no numbers"


def test_without_a_base_the_specs_are_not_silently_skipped(tmp_path):
    """`compare` is a library entry point and `base=None` is its default, so
    the blind branch was the one a careless caller got. It now says so."""
    doc = _deck(tmp_path, DEC)
    r = check_facts.compare(CONTRACT, doc.read_text(encoding="utf-8"))
    assert r["spec_quantities"] == 0
    assert r["spec_problems"], (
        "a declared spec nobody could resolve printed what a document with no "
        "specs prints — the hole this function was written to close, reopened "
        "by its own default argument")


def test_the_spec_may_not_be_the_contract(tmp_path):
    """One file as both makes `unsourced` empty by construction and red line
    1's only instrument goes blind. The refusal is a mechanism, not a note."""
    doc = _deck(tmp_path, DEC)
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_facts.py"),
         str(tmp_path / "figures/f1.json"), str(doc)],
        capture_output=True, text=True)
    assert done.returncode != 0
    assert "cannot be its own fact contract" in done.stderr


# --- the loss is visible -----------------------------------------------------

OUTLINE = """genre: sales
storyline: market-analysis

## Where the spending goes

- Adoption rises with support hours
  analysis: correlate | finding: it flattens | implication: More support stops buying adoption.
- Where we stand against rivals
  analysis: position | finding: broad and shallow | implication: Breadth is the order.
"""


def _landing(html):
    found = check_outline.drift(OUTLINE, html)
    rows = [f for f in found if f["check"] == "analysis landing"]
    assert len(rows) == 1, found
    return rows[0]


def test_a_document_that_carries_every_move_says_so():
    html = ('<section class="page" data-analysis="correlate"></section>'
            '<section class="page" data-analysis="position"></section>')
    assert "declares 2 analytical move(s); the document carries 2" in \
        _landing(html)["detail"]


def test_a_document_that_dropped_them_names_the_loss():
    """Measured across 17 shipped documents: the outlines declared 17 moves and
    the documents carried zero. No change here can move that number; what this
    does is make the deletion visible."""
    row = _landing('<section class="page"></section>')
    assert "carries 0" in row["detail"]
    assert "did not reach the page" in row["detail"]
    assert row["verdict"] == "note", "this reports; AG-9 declined the gate"


def test_the_landing_line_never_gates():
    assert "analysis landing" not in check_outline.GATING_CHECKS


# --- and the skeleton still refuses to draw ----------------------------------

@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_a_skeleton_never_becomes_a_drawing(move):
    for mod in (bd, sc):
        with pytest.raises(SystemExit):
            mod.render(fs.skeleton(move))


def test_a_single_digit_value_does_not_reach_the_comparison(tmp_path):
    """The instrument's reach, stated rather than assumed. `_canonical` gives
    `8` and the contract side reads every number, so a lone digit DOES compare
    — this pins which, because the first version of `spec_quantities` sent the
    values through the prose scanner and lost them."""
    spec = dict(DEC, total={"label": "All", "value": 9},
                parts=[{"label": "a", "value": 5}, {"label": "b", "value": 4}])
    doc = _deck(tmp_path, spec)
    r = check_facts.compare("## FACTS\n\n- All is 9, a is 5, b is 4.\n",
                            doc.read_text(encoding="utf-8"), base=doc.parent)
    assert r["spec_quantities"] == 3
    assert r["unsourced_spec_values"] == []


def test_the_text_mode_exit_code_carries_every_gating_verdict(tmp_path):
    """`scripts/ops/build.py` invokes check_facts WITHOUT `--json`, so the text
    path is the one that gates a real build — and dropping `spec_problems` from
    its exit expression survived the whole suite."""
    import subprocess
    import sys
    doc = _deck(tmp_path, DEC)
    (tmp_path / "figures/f1.json").unlink()
    contract = tmp_path / "c.md"
    contract.write_text(CONTRACT, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_facts.py"),
         str(contract), str(doc)], capture_output=True, text=True)
    assert done.returncode != 0, (
        "a declared spec that could not be read exited 0 in the mode that "
        "gates a build")
    assert "figure spec" in done.stdout
