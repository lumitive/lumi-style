"""The sprite goes after the document's real <body>, never a quoted one.

The failure this was written from: a deliverable's preamble explains the
geometry rule in a CSS comment inside its `<style>` block, and that comment
contains the literal text `<body data-geometry="landscape">`. The injector
matched the first `<body[^>]*>` in the file, so the sprite landed inside a
stylesheet comment. The browser never saw it, every `<use>` resolved to
nothing, and the figure rendered as blank space — while `--check`, `--list`
and D19 all reported the document correct, because all three read the file and
the file was fine. It took a screenshot to find it.
"""
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "build"))

import embed_shapes  # noqa: E402

SPRITE = '<svg id="lumi-shape-sprite">S</svg>'
REAL = '<body class="deck" data-geometry="landscape">'


def _doc(decoy):
    return f'<!doctype html><html><head>{decoy}</head>{REAL}<p>x</p></body></html>'


@pytest.mark.parametrize("decoy", [
    '<style>/* one geometry per document: `<body data-geometry="landscape">` */</style>',
    '<!-- the declaration is <body data-geometry="portrait"> -->',
    '<script>/* <body> */</script>',
    '<style>/* <body> */</style><!-- <body> -->',
])
def test_a_quoted_body_is_not_the_insertion_point(decoy):
    out = embed_shapes._after_body(_doc(decoy), SPRITE)
    assert out.index(SPRITE) > out.index(REAL), \
        "the sprite landed before the real <body> — it is inside the decoy"
    # And nothing inside a skipped span may hold it.
    for m in embed_shapes.SKIP_RE.finditer(out):
        assert SPRITE not in m.group(0), f"sprite ended up inside {m.group(0)[:60]!r}"


def test_the_ordinary_document_still_works():
    out = embed_shapes._after_body(f"<html><head></head>{REAL}<p>x</p></body></html>", SPRITE)
    assert out.index(SPRITE) == out.index(REAL) + len(REAL) + 1


def test_no_body_at_all_raises_rather_than_guessing():
    with pytest.raises(ValueError, match="nowhere to go"):
        embed_shapes._after_body("<html><head></head></html>", SPRITE)


def test_a_body_only_inside_a_comment_raises():
    """The dangerous middle case: a decoy and no real tag. Silently injecting
    into the comment is exactly the bug."""
    with pytest.raises(ValueError):
        embed_shapes._after_body("<html><!-- <body> --></html>", SPRITE)


def test_the_real_deliverable_shape_is_covered():
    """Anchored on the actual preamble, not on my memory of it: if new_deck ever
    stops carrying a quoted <body>, this test says so instead of passing on a
    decoy that no longer exists."""
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import new_deck
    pre = new_deck.preamble("internal", "landscape")
    quoted = [m for m in re.finditer(r"<body[^>]*>", pre)
              if any(a <= m.start() < b
                     for a, b in (s.span() for s in embed_shapes.SKIP_RE.finditer(pre)))]
    assert quoted, ("the scaffold no longer quotes a <body> tag inside a comment "
                    "or style block; this guard's real-world case is gone")
