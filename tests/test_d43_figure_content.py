"""D43 — a drawing names every member the page's own spec declares.

The gate that was missing while a two-by-two shipped as an empty box with an
axis word at each end and every other metric ran green. Three answers, and the
tests below hold all three APART: a clean document, a thin drawing, and a page
whose figure could not be read at all must produce three different results.
Proving only that it can fail is FM-01; proving only that it can pass on a
figure is FM-24, which is the defect this check was written after.
"""
import json
import pathlib

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
    assert r == {"checked": 1, "thin": [], "blind": [], "unasked": []}


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
    # THE ANSWERS ARE DIFFERENT ANSWERS. A blind page must not be reportable
    # as a clean one, which is the whole of FM-24.
    assert r != {"checked": 1, "thin": [], "blind": [], "unasked": []}


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


def test_correlate_is_reported_as_ungradeable_never_as_clean(base, tmp_path):
    """A scatter's points are dots, so this gate has nothing to ask of a
    `correlate` figure — and for one release it said so by saying NOTHING,
    returning `{"checked": 0, "thin": [], "blind": []}` whose row cell is the
    character `0`. Byte-identical to a document where every figure named every
    member. Found by mutation review, in the gate written after FM-24.

    Asserted on the BEHAVIOUR, not on the table. The first version of this test
    read `NAMED_MEMBERS` itself, so emptying rows of the table left it green —
    the "a test must not read the constant it pins" pattern, twice shipped
    here already."""
    spec = json.loads(json.dumps(SPEC))
    spec.update({"move": "correlate",
                 "x": {"name": "hours", "unit": "h"},
                 "y": {"name": "seats", "unit": "%"},
                 "points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]})
    for k in ("total", "parts"):
        spec.pop(k, None)
    (base / "figures" / "cost.json").write_text(json.dumps(spec))
    r = check_design.d43_figure_content(_doc(_fig("Installation")), base)
    assert r["checked"] == 0 and r["thin"] == [] and r["blind"] == []
    assert len(r["unasked"]) == 1 and r["unasked"][0]["move"] == "correlate"


@pytest.mark.parametrize("move,field,key,members", [
    ("decompose", "parts", "label", [{"label": "Installation", "value": 1}]),
    ("position", "items", "label",
     [{"label": "Gamma", "x": 0.3, "y": 0.4, "note": "n"}]),
    ("bridge", "pieces", "label", [{"label": "Price", "delta": 5}]),
    ("compare", "lanes", "name", [{"name": "transport", "note": "n"},
                                  {"name": "content", "note": "n"}]),
    ("compare", "references", "label", [{"label": "Gamma", "value": 3}]),
])
def test_every_row_of_the_table_is_exercised(base, move, field, key, members):
    """Only `decompose`/`parts` was. Mutation review deleted the `compare`,
    `bridge` and `position` rows one at a time and nothing in the suite or the
    fixtures noticed — on the gate that exists because a two-by-two shipped as
    an empty box, whose move is `position`."""
    spec = {"move": move, "period": "FY25", "reading": "r",
            "cause": "c", "source": "s",
            "measure": {"name": "m", "unit": "u"}, field: members}
    if move == "compare" and field == "lanes":
        spec["subject"] = {"label": "S", "lane": "transport", "value": 1}
    (base / "figures" / "cost.json").write_text(json.dumps(spec))
    names = [str(m[key]) for m in members]
    # Every member drawn -> clean; none drawn -> thin. Both directions, so the
    # row is proven to fire AND to stay quiet.
    clean = check_design.d43_figure_content(_doc(_fig(*names)), base)
    assert clean["thin"] == [] and clean["checked"] == 1
    thin = check_design.d43_figure_content(_doc(_fig("something else")), base)["thin"]
    assert thin and names[0] in thin[0]["missing"][0]


def test_the_row_a_reader_sees_keeps_the_answers_apart():
    """THE STRING, not the mapping. `measure()` kept the three answers apart
    and `grade()` collapsed them: a mutation deleting the `unreadable` clause
    survived the whole suite and check_fixtures both, because nothing tested
    what a reader actually reads."""
    # `grade` reads the whole result mapping, so the base is a real measurement
    # of a real document and only the D43 value is substituted. Faking the
    # mapping would test a shape this code never receives.
    doc = pathlib.Path("fixtures/deck-figure.en.html")
    base_result = check_design.measure(doc)

    def cell(d):
        row = next(r for r in check_design.grade(dict(base_result,
                                                      D43_figure_content=d))
                   if r[0] == "D43_figure_content")
        return str(row[1])

    # EVERY CASE CHECKS THE SAME NUMBER OF FIGURES, so the only thing that can
    # tell the four strings apart is the clause each answer adds. The first
    # version varied `checked` too, and three mutations that deleted a clause
    # stayed green because the counts still differed.
    clean = {"checked": 3, "thin": [], "blind": [], "unasked": []}
    thin = dict(clean, thin=[{"page": "p1", "ref": "f", "missing": ["x"]}])
    dark = dict(clean, blind=[{"page": "p1", "ref": "f", "why": "w"}])
    mute = dict(clean, unasked=[{"page": "p1", "ref": "f", "move": "correlate"}])
    seen = {cell(clean), cell(thin), cell(dark), cell(mute)}
    assert len(seen) == 4, f"answers that print the same string: {seen}"
