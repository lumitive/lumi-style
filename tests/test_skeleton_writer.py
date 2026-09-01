"""`new_deck.write_spec_skeletons`, which had no test of any kind.

Mutation review: `return []` from the writer, never emitting the page's
`data-figure-spec`, and removing the never-overwrite guard all survived a green
suite. The third is the one that matters — the docstring promises *"never over
an existing file … a rebuild that overwrote them would destroy the one artefact
this whole chain exists to hold"*, and nothing enforced it. A rebuild silently
replacing an author's filled spec with a numberless skeleton is data loss they
would find only by rendering.
"""
import json

import figure_spec as fs
import new_deck
import pytest


def _plan(move="decompose", ref="figures/f.json"):
    return [{"title": "A page", "move": move, "framework": "", "data": ref,
             "finding": "f", "implication": "I."}]


def test_it_writes_a_skeleton_for_a_served_beat(tmp_path):
    out = tmp_path / "deck.html"
    wrote, notes = new_deck.write_spec_skeletons(_plan(), out)
    assert notes == []
    assert [m for _t, m in wrote] == ["decompose"]
    spec = json.loads((tmp_path / "figures/f.json").read_text(encoding="utf-8"))
    assert fs.is_skeleton(spec) and spec["move"] == "decompose"


def test_it_never_overwrites_an_existing_spec(tmp_path):
    """The author's numbers are the artefact. A rebuild that replaced them
    would destroy the thing the whole chain exists to hold."""
    out = tmp_path / "deck.html"
    (tmp_path / "figures").mkdir()
    mine = {"move": "decompose", "period": "FY25", "reading": "r",
            "cause": "c", "source": "s",
            "measure": {"name": "Spend", "unit": "CNY m"},
            "total": {"label": "All", "value": 100},
            "parts": [{"label": "a", "value": 60}, {"label": "b", "value": 40}]}
    (tmp_path / "figures/f.json").write_text(json.dumps(mine), encoding="utf-8")
    wrote, notes = new_deck.write_spec_skeletons(_plan(), out)
    assert wrote == [], "it wrote over a spec that was already there"
    assert notes == [], "an unchanged, matching spec is not worth a note"
    assert json.loads((tmp_path / "figures/f.json").read_text(
        encoding="utf-8")) == mine


def test_a_stale_spec_is_left_alone_and_said_out_loud(tmp_path):
    """Not overwriting is right; being silent about it is not. A beat whose
    move changed leaves a file behind that no longer describes it."""
    out = tmp_path / "deck.html"
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures/f.json").write_text(
        json.dumps(fs.skeleton("compare")), encoding="utf-8")
    wrote, notes = new_deck.write_spec_skeletons(_plan("bridge"), out)
    assert wrote == []
    assert len(notes) == 1
    assert "declares move 'compare'" in notes[0] and "'bridge'" in notes[0]


def test_a_move_the_scaffold_cannot_serve_is_said_not_skipped(tmp_path):
    wrote, notes = new_deck.write_spec_skeletons(_plan("comapre"),
                                                 tmp_path / "deck.html")
    assert wrote == [] and len(notes) == 1
    assert "NOT written" in notes[0] and "comapre" in notes[0]


def test_a_reference_outside_the_deck_is_refused(tmp_path):
    """`mkdir(parents=True)` would have built a tree anywhere the process can
    write — a silent success in the wrong place."""
    out = tmp_path / "deck" / "deck.html"
    out.parent.mkdir()
    wrote, notes = new_deck.write_spec_skeletons(
        _plan(ref="../../escaped.json"), out)
    assert wrote == [] and len(notes) == 1
    assert "outside the deck's own directory" in notes[0]
    assert not (tmp_path.parent / "escaped.json").exists()


def test_an_unreadable_existing_spec_is_reported(tmp_path):
    out = tmp_path / "deck.html"
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures/f.json").write_text("{ truncated", encoding="utf-8")
    wrote, notes = new_deck.write_spec_skeletons(_plan(), out)
    assert wrote == [] and len(notes) == 1
    assert "could not be read" in notes[0]


def test_no_out_path_writes_nothing_and_claims_nothing(tmp_path):
    assert new_deck.write_spec_skeletons(_plan(), None) == ([], [])


# --- what the page says about it --------------------------------------------

OUTLINE = """genre: sales
storyline: market-analysis

## Where the spend goes

- A page whose beat names its data
  analysis: decompose | data: figures/ok.json | finding: f | implication: I.
- A page whose move is a typo
  analysis: decompse | data: figures/typo.json | finding: f | implication: I.
"""


def _build(tmp_path):
    src = tmp_path / "o.md"
    src.write_text(OUTLINE, encoding="utf-8")
    out = tmp_path / "deck.html"
    import contextlib
    import io
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), \
            contextlib.redirect_stderr(err), contextlib.suppress(SystemExit):
        new_deck.main(["--outline", str(src), "--pages", "2", "--genre",
                       "sales", "--no-trace", "--out", str(out)])
    return out.read_text(encoding="utf-8"), err.getvalue()


def test_the_page_names_the_spec_the_scaffold_wrote(tmp_path):
    html, _err = _build(tmp_path)
    assert 'data-figure-spec="figures/ok.json"' in html


def test_the_page_does_not_name_one_the_scaffold_refused(tmp_path):
    """One predicate answers "will this be served" in both places. They
    disagreed, so a beat the writer refused still got a declaration and the
    author met the problem later, through another tool, as "could not be read"
    — pointed at a file nobody said was never written."""
    html, err = _build(tmp_path)
    assert "figures/typo.json" not in html
    assert "NOT written" in err


@pytest.mark.parametrize("move", sorted(fs.MOVE_FIELDS))
def test_every_move_the_contract_shapes_is_one_the_scaffold_can_serve(move):
    assert new_deck.spec_servable(move, "figures/f.json", None)
