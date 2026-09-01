"""Move -> registry -> tool -> a visible slot the reader's gate refuses.

The chain this asserts is the one 0.1.533 already taught once: the scaffold
named its candidates in a COMMENT and five deliverables used the shape library
zero times. So the assertion that matters is not that `tool_for` resolves — it
is that the command lands where `d14_placeholders` can see it, since that
function strips comments and `<svg>` before it looks.
"""
import check_design
import new_deck
import pytest

OUTLINE = """genre: sales
storyline: market-analysis

## Where support spending actually goes

- Adoption rises with support hours, up to a point
  analysis: correlate | finding: it flattens past forty | implication: More support stops buying adoption.
- Where the product stands against its two nearest rivals
  analysis: position | finding: broad and shallow | implication: Breadth is this quarter's order.
"""


def test_a_move_with_a_tooled_framework_resolves():
    name, run = new_deck.tool_for("correlate")
    assert name == "scatter"
    assert "scatter_svg.py" in run


def test_a_move_with_no_tooled_framework_resolves_to_nothing():
    assert new_deck.tool_for("position") == ("", "")


def test_a_named_framework_is_answered_or_not_at_all():
    """AR-1's rule, and `shape_for`'s: an author who names a framework is told
    nothing rather than handed a sibling's tool.

    It named `benchmark-table` until 0.1.668, when that framework got a tool of
    its own and the assertion started passing for the wrong reason.
    `harvey-scorecard` draws `compare` from library shapes and has none, which
    is the shape this rule is about. `two_per_move` below tests the same rule
    on a registry built to express it."""
    assert new_deck.tool_for("compare", "harvey-scorecard") == ("", "")


def test_an_empty_move_resolves_to_nothing():
    assert new_deck.tool_for("", "") == ("", "")


def _deck(tmp_path):
    src = tmp_path / "outline.md"
    src.write_text(OUTLINE, encoding="utf-8")
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), \
            contextlib.redirect_stderr(io.StringIO()), \
            contextlib.suppress(SystemExit):
        new_deck.main(["--outline", str(src), "--pages", "2", "--genre", "sales"])
    return buf.getvalue()


def test_the_command_reaches_the_visible_body(tmp_path):
    """Through the SAME functions the gate uses, not a hand-rolled copy.

    The first version of this test re-implemented d14's stripping inline and
    stopped there. Mutation review moved the command out of the `<code>`
    element into a `data-run=` attribute on the same paragraph — invisible to a
    reader and to `markup.visible_text` — and the test stayed green. That is
    0.1.533's regression in a new costume, so the assertion now runs the real
    reader.
    """
    import re

    import markup
    raw = _deck(tmp_path)
    assert "scatter_svg.py" in raw
    stripped = re.sub(r"<(script|style|svg)\b.*?</\1>", " ",
                      re.sub(r"<!--.*?-->", " ", raw, flags=re.S),
                      flags=re.S | re.I)
    assert "scatter_svg.py" in markup.visible_text(stripped), (
        "the command is in the file but not in the text a reader sees")


def test_the_figure_box_holds_no_drawing_where_a_tool_is_owed(tmp_path):
    """Two answers to one question is the defect the render found: page one's
    demo furniture put a `position` unit on a page declaring `correlate`,
    beside a line saying "draw this figure". Mutation review deleted the line
    that removes it and every test stayed green."""
    import re
    raw = _deck(tmp_path)
    page = next(p for p in re.findall(r"<section class=\"page\".*?</section>",
                                      raw, re.S)
                if "[TO FILL: draw this figure]" in p)
    fig = re.search(r"<div class=\"fig\">(.*?)<div class=\"cap\"", page, re.S)
    assert fig, "the slot's page has no figure box"
    assert "<use" not in fig.group(1), (
        "a library shape was drawn on a page that is also told to run a tool")


def test_the_slot_is_refused_by_d14(tmp_path):
    found = check_design.d14_placeholders(_deck(tmp_path))
    assert any("draw this figure" in f["text"] for f in found)


def test_a_page_that_gets_a_shape_gets_no_slot(tmp_path):
    """The `position` page above resolves to a library shape, so it must not
    also be told to run a tool: two answers to one question is the failure
    `shape_for` was corrected for at 0.1.596."""
    html = _deck(tmp_path)
    assert html.count("[TO FILL: draw this figure]") == 1


def test_a_scaffold_with_no_outline_carries_no_slot():
    """The invariant that keeps this from changing every deck: without a
    declared move there is no framework, so there is nothing to run."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), \
            contextlib.redirect_stderr(io.StringIO()), \
            contextlib.suppress(SystemExit):
        new_deck.main(["--genre", "training", "--pages", "2"])
    assert "[TO FILL: draw this figure]" not in buf.getvalue()


def test_the_registrys_command_actually_runs(tmp_path):
    """**The defect this was written from.** The registry's first `run` line
    was `python3 scripts/render/scatter_svg.py <spec.json>` and the renderer
    takes `--data PATH`: the scaffold printed it on the page, an author would
    have typed it, and it would have exited 2. Existence, trackedness and side
    were all green — every static property held and the sentence did not work.

    So this runs it. `check_framework_tools` checks the flags statically
    (`_tool_flags_exist`), which catches the same class in CI without a
    subprocess; this is the end-to-end proof that the static check is checking
    the right thing.
    """
    import json
    import pathlib
    import subprocess
    import sys
    root = pathlib.Path(new_deck.ROOT)
    _name, run = new_deck.tool_for("correlate")
    assert run, "the correlate framework declares no tool"
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        # THE FULL CONTRACT. Before 0.1.667 a spec could omit `move`, `period`
        # and `reading` and still draw: four of the six things DR-20 demands of
        # any figure carrying a number were optional and nothing asked.
        "move": "correlate",
        "period": "the first twelve months",
        "reading": "adoption rises with support hours, then flattens",
        "cause": "direction not tested",
        "source": "illustrative, not measured",
        "x": {"name": "Support hours", "unit": "hours/quarter"},
        "y": {"name": "Adoption", "unit": "% of seats"},
        "points": [{"x": 8, "y": 21}, {"x": 20, "y": 44}, {"x": 34, "y": 58},
                   {"x": 50, "y": 63}, {"x": 66, "y": 65}],
    }), encoding="utf-8")
    argv = [sys.executable if tok == "python3" else tok
            for tok in run.replace("<spec.json>", str(spec)).split()]
    done = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, (
        f"the command the scaffold prints on the page exits "
        f"{done.returncode}: {done.stderr[:400]}")
    assert done.stdout.lstrip().startswith("<svg"), (
        "the command ran and produced no drawing")


# --- against a SYNTHETIC registry ------------------------------------------
# The real registry has one tooled framework and one framework per move, so
# `tool_for` is a one-point function there: mutation review replaced its body
# with `if move == "correlate": return "scatter", "…"` and all eight tests
# passed. These give the rules something they can actually be wrong about.

TWO_PER_MOVE = {
    "version": 1,
    "frameworks": {
        # one move, two frameworks, and the TOOLED one is not the named one.
        "tooled-sibling": {"question": "q?", "move": "compare",
                           "slots": ["a"], "misuse": "m", "drawn": "native",
                           "tool": {"module": "probe",
                                    "run": "python3 scripts/render/probe.py --data x"}},
        "asked-for": {"question": "q?", "move": "compare", "slots": ["a"],
                      "misuse": "m", "shapes": ["p001-unit-01"]},
    },
}


@pytest.fixture
def two_per_move(tmp_path, monkeypatch):
    import json
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "assets/frameworks.json").write_text(
        json.dumps(TWO_PER_MOVE), encoding="utf-8")
    monkeypatch.setattr(new_deck, "ROOT", tmp_path)
    return tmp_path


def test_a_named_framework_is_the_answer_not_the_head_of_a_queue(two_per_move):
    """0.1.596's rule, on a registry that can express it. An author who asks
    for `asked-for` must be told nothing rather than handed the SIBLING's
    tool — answering a request with a different framework is worse than
    answering it with nothing."""
    assert new_deck.tool_for("compare", "asked-for") == ("", "")
    assert new_deck.tool_for("compare")[0] == "tooled-sibling"


def test_frameworks_matching_orders_the_named_one_alone(two_per_move):
    named = new_deck.frameworks_matching("compare", "asked-for")
    assert [k for k, _ in named] == ["asked-for"]
    assert len(new_deck.frameworks_matching("compare")) == 2


def test_a_framework_the_registry_does_not_have_falls_back_to_the_move(two_per_move):
    """`named or hits` — a name nothing matches must not silence the move."""
    assert len(new_deck.frameworks_matching("compare", "no-such")) == 2


def test_an_unreadable_registry_is_not_an_empty_one(tmp_path, monkeypatch):
    """It returned `[]`, the same value as "this move has no framework", so a
    page declared its move, carried no slot, and D14 had nothing to refuse."""
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "assets/frameworks.json").write_text("{ truncated", encoding="utf-8")
    monkeypatch.setattr(new_deck, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="could not be read"):
        new_deck.tool_for("correlate")


def test_a_registry_without_its_own_key_is_not_an_empty_one(tmp_path, monkeypatch):
    import json
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "assets/frameworks.json").write_text(
        json.dumps({"registry": {}}), encoding="utf-8")
    monkeypatch.setattr(new_deck, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="not the registry"):
        new_deck.tool_for("correlate")
