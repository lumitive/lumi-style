"""A `var()` naming nothing renders black, and every gate called it clean.

Reported by the owner, looking at a deck this package had passed. Two pages of
a conformance deck drew their figures in black instead of the brand green:
`fill="var(--bg1)"` seven times, against a token block that declares `--bg` and
never `--bg1`.

`var(--undefined)` with no fallback is not an error to a browser. The property
is invalid at computed-value time and the element takes the INITIAL value, and
for `fill` on an SVG shape that is black. Confirmed in Chromium on the real
artifact: `getComputedStyle(shape).fill === "rgb(0, 0, 0)"`, four of four
shapes on one page and three of eight on the other.

**Why nothing saw it.** D20 compares the values a document DECLARES against
`tokens/` and has nothing to say about a name never declared at all. D1 measures
a declared text colour against a declared surface, and the surface here declares
nothing — so it reported `0`, which is what it prints when a document is clean.
That is the shape: a check that could not look printing what a check that looked
prints.

`check_repo` has held THIS repository to the same rule for releases — every
`var()` in `tokens/` must resolve. D19 is that sentence turned to face the
deliverable.
"""
import pathlib

import check_design

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _doc(style, body=""):
    return (f"<html><head><style>{style}</style></head><body>"
            f'<section class="page">{body}</section></body></html>')


def _vars(doc):
    return check_design._dangling_vars(doc)


def test_a_name_that_resolves_to_nothing_is_a_dangling_reference():
    doc = _doc(":root{--bg:#fff}", '<svg><rect fill="var(--bg1)"/></svg>')
    assert _vars(doc) == ["--bg1 (1x)"]


def test_it_counts_the_uses_so_a_reader_knows_the_blast_radius():
    doc = _doc(":root{--bg:#fff}",
               '<svg><rect fill="var(--bg1)"/><rect fill="var(--bg1)"/></svg>')
    assert _vars(doc) == ["--bg1 (2x)"]


def test_a_declared_name_is_not_dangling():
    doc = _doc(":root{--bg1:#fff}", '<svg><rect fill="var(--bg1)"/></svg>')
    assert _vars(doc) == []


def test_a_fallback_is_a_definition():
    """`var(--display, Georgia, serif)` renders what its author asked for.

    Two of the four undefined names in the reported deck carry one. Counting
    them would be a checker failing a document that did the right thing — the
    direction this package treats as the dangerous one.
    """
    doc = _doc(":root{--bg:#fff}",
               '<svg><rect fill="var(--bg1, #fff)"/></svg>'
               '<p style="font-family:var(--display, Georgia, serif)">x</p>')
    assert _vars(doc) == []


def test_a_comment_is_not_a_reference():
    """The first run of this check failed all three of this package's fixtures.

    `tokens/lumi-layouts.css` carries a note reading "`var(--accent)` until
    0.1.367" — prose about a property this package RETIRED. A gate whose first
    act is to fail the passing fixture is the mistake D19's own docstring warns
    about, made again four hundred lines below it.
    """
    doc = _doc("/* var(--accent) until 0.1.367 */\n:root{--bg:#fff}",
               "<!-- var(--legacy) was here -->")
    assert _vars(doc) == []


def test_a_var_inside_a_script_is_a_string():
    doc = _doc(":root{--bg:#fff}",
               "<script>const s = 'var(--not-css)';</script>")
    assert _vars(doc) == []


def test_the_shipped_fixtures_carry_none():
    """Including deck-broken and deck-degenerate, whose plants are elsewhere."""
    for name in ("deck-pass", "deck-broken", "deck-degenerate"):
        raw = (ROOT / "fixtures" / f"{name}.en.html").read_text(encoding="utf-8")
        assert check_design._dangling_vars(raw) == [], name


def test_it_reaches_the_gating_row():
    """D19 gates, so a dangling name has to change the verdict, not just a dict."""
    doc = _doc(":root{--bg:#fff}", '<svg><rect fill="var(--bg1)"/></svg>')
    r = check_design.d19_vocabulary(doc)
    assert r["dangling_vars"] == ["--bg1 (1x)"]
    clean = check_design.d19_vocabulary(
        _doc(":root{--bg1:#fff}", '<svg><rect fill="var(--bg1)"/></svg>'))
    assert clean["dangling_vars"] == []
