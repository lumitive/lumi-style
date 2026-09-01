"""D43 — a drawing names every member the page's own spec declares.

The gate that was missing while a two-by-two shipped as an empty box with an
axis word at each end and every other metric ran green. Three answers, and the
tests below hold all three APART: a clean document, a thin drawing, and a page
whose figure could not be read at all must produce three different results.
Proving only that it can fail is FM-01; proving only that it can pass on a
figure is FM-24, which is the defect this check was written after.
"""
import json

import check_design
import pytest

FOOT = ('<div class="foot"><span class="conf">Confidential</span>'
        '<span class="site">www.example.org</span><span>01 / 01</span></div>')

SPEC = {
    "move": "decompose",
    "period": "FY25",
    "reading": "installation carries most of the cost",
    "cause": "an allocation from the cost ledger, not a model",
    "source": "Synthetic figures for a test, not measured.",
    "measure": {"name": "Programme cost", "unit": "CNY m"},
    "total": {"label": "Programme cost", "value": 100},
    "parts": [{"label": "Installation", "value": 60},
              {"label": "Survey", "value": 25},
              {"label": "Reconciliation", "value": 15}],
}

# Every page carries the ground behind it and an icon in its eyebrow. They are
# in every document here on purpose: the first version of this check counted
# them as the figure, so a page with NO drawing reported `thin` and blamed the
# drawing for the page's defect.
DECOR = ('<svg class="ground" viewBox="0 0 1280 720" aria-hidden="true">'
         '<use href="#g-ground"/></svg>'
         '<svg class="ic" aria-hidden="true"><use href="#i-bell"/></svg>')


def _fig(*labels):
    bars = "".join(
        f'<rect x="40" y="{60 + 70 * i}" width="{300 - 60 * i}" height="34"/>'
        f'<text class="flbl" x="40" y="{52 + 70 * i}">{lab}</text>'
        for i, lab in enumerate(labels))
    return f'<div class="fig"><svg role="img" viewBox="0 0 640 300">{bars}</svg></div>'


def _doc(figure, ref="figures/cost.json"):
    return ('<!doctype html><html><head><title>T</title></head><body>'
            f'<section class="page" id="p1" data-figure-spec="{ref}">{DECOR}'
            f'<div class="body stack">{figure}</div>{FOOT}</section>'
            '</body></html>')


@pytest.fixture()
def base(tmp_path):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "cost.json").write_text(json.dumps(SPEC))
    return tmp_path


def test_a_drawing_that_names_every_part_is_clean(base):
    r = check_design.d43_figure_content(
        _doc(_fig("Installation", "Survey", "Reconciliation")), base)
    assert r == {"checked": 1, "thin": [], "blind": []}


def test_a_drawing_that_leaves_one_part_anonymous_is_thin(base):
    r = check_design.d43_figure_content(
        _doc(_fig("Installation", "Survey")), base)
    assert r["thin"] and r["thin"][0]["page"] == "p1"
    assert r["thin"][0]["missing"] == ["parts[2] 'Reconciliation'"]
    assert r["blind"] == []


def test_a_page_with_no_figure_is_blind_and_not_thin(base):
    """The distinction the first implementation could not make. A page that
    declares a spec and draws nothing has a defect, and it is D32's — blaming
    the drawing here would report the wrong thing about the right page, and
    would fail a document whose figure is a raster (AG-10)."""
    r = check_design.d43_figure_content(_doc("<p>Prose only.</p>"), base)
    assert r["thin"] == []
    assert len(r["blind"]) == 1
    assert "no inline <svg>" in r["blind"][0]["why"]
    # THE THREE ANSWERS ARE THREE STRINGS. A blind page must not be reportable
    # as a clean one, which is the whole of FM-24.
    assert r != {"checked": 1, "thin": [], "blind": []}


def test_a_spec_that_cannot_be_read_is_blind(base):
    r = check_design.d43_figure_content(
        _doc(_fig("Installation"), ref="figures/absent.json"), base)
    assert r["thin"] == [] and len(r["blind"]) == 1
    assert r["checked"] == 0


def test_a_document_declaring_nothing_is_never_asked(base):
    raw = ('<!doctype html><html><head><title>T</title></head><body>'
           f'<section class="page" id="p1">{DECOR}<div class="body">'
           f'<p>No spec here.</p></div>{FOOT}</section></body></html>')
    assert check_design.d43_figure_content(raw, base) is None


def test_the_source_line_does_not_count_as_naming_a_part(base):
    """A figure's citation is provenance, not the drawing naming a member.
    Measured on this package's own breakdown, whose source string carries a
    word that is also a part label — counting it would let a figure pass
    because of its own footnote."""
    spec = json.loads(json.dumps(SPEC))
    spec["source"] = "Reconciliation ledger, FY25."
    (base / "figures" / "cost.json").write_text(json.dumps(spec))
    fig = _fig("Installation", "Survey").replace(
        "</svg>", '<text class="fnote">Reconciliation ledger, FY25.</text></svg>')
    r = check_design.d43_figure_content(_doc(fig), base)
    assert r["thin"] and r["thin"][0]["missing"] == ["parts[2] 'Reconciliation'"]


def test_a_shortened_label_still_counts_as_named(base):
    """A drawing legitimately shortens a long label to fit. Refusing that would
    be a gate a correct figure cannot satisfy, so the longest word counts."""
    r = check_design.d43_figure_content(
        _doc(_fig("Installation", "Survey", "Reconciliation of the ledger")), base)
    assert r["thin"] == []


def test_correlate_points_are_never_required_to_be_named(base):
    """A scatter's points are dots. This is the one move deliberately outside
    NAMED_MEMBERS, and it is a declared exemption rather than an oversight —
    the test exists so removing it from the table is a red run, not a silence.
    """
    assert not [k for k in check_design.NAMED_MEMBERS if k[0] == "correlate"]
