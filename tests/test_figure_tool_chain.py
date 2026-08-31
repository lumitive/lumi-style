"""Move -> registry -> tool -> a visible slot the reader's gate refuses.

The chain this asserts is the one 0.1.533 already taught once: the scaffold
named its candidates in a COMMENT and five deliverables used the shape library
zero times. So the assertion that matters is not that `tool_for` resolves — it
is that the command lands where `d14_placeholders` can see it, since that
function strips comments and `<svg>` before it looks.
"""
import check_design
import new_deck

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
    """AR-1's rule, and `shape_for`'s: an author who asked for a benchmark
    table is told nothing rather than handed the scatter tool."""
    assert new_deck.tool_for("compare", "benchmark-table") == ("", "")


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
    html = _deck(tmp_path)
    assert "scatter_svg.py" in html
    # Not in a comment, and not inside the drawing: both are stripped before
    # D14 looks, and a slot no gate can refuse is furniture.
    body = html
    import re
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<svg\b.*?</svg>", " ", body, flags=re.S | re.I)
    assert "scatter_svg.py" in body


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
