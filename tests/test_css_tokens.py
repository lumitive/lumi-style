"""Characterization tests for the CSS custom-property parsing, written BEFORE
the dedup refactor extracts it into scripts/css_tokens.py.

Three copies exist today:
- check_repo.css_block / css_vars — the canonical one; css_vars strips
  comments first (the 0.1.415 fix, pinned below).
- check_design.token_blocks / token_block_bodies — accumulates repeated
  selectors (the 0.1.387 fix, pinned below).
- build_brand._vars — still carries the 0.1.415 bug class: it does not strip
  comments, and it truncates at the first `}` in the file after the selector.
  Pinned as strict xfail so the R4 fix is forced to flip them.
"""
import build_brand
import check_design
import check_repo
import pytest

# ── check_repo: css_block ────────────────────────────────────────────────────

def test_css_block_extracts_nested():
    css = ":root { --a: 1; @media x { --b: 2; } --c: 3; } .after { --d: 4; }"
    block = check_repo.css_block(css, ":root {")
    assert "--a: 1" in block and "--c: 3" in block
    assert "--d" not in block


def test_css_block_unterminated_raises():
    with pytest.raises(ValueError, match="unterminated"):
        check_repo.css_block(":root { --a: 1;", ":root {")


# ── check_repo: css_vars ─────────────────────────────────────────────────────

def test_css_vars_parses_declarations():
    assert check_repo.css_vars("--bg: #FFF;\n--ink: #1A1A1A;") == {
        "bg": "#FFF", "ink": "#1A1A1A"}


def test_css_vars_ignores_comment_prose():
    """The 0.1.415 regression: a comment citing a token name must not parse
    as a declaration of that token."""
    block = ("/* measured against --bg: 2.71 / 1.82, from the audit */\n"
             "--ink: #1A1A1A;\n")
    assert check_repo.css_vars(block) == {"ink": "#1A1A1A"}


# ── check_design: token blocks ───────────────────────────────────────────────

def test_token_blocks_accumulate_repeated_root():
    """The 0.1.387 fix: a second :root appends rather than replacing."""
    css = ":root { --bg: #FFF; }\n:root { --rg-a: #123456; }\n"
    blocks = check_design.token_blocks(css)
    assert "--bg" in blocks["light"] and "--rg-a" in blocks["light"]


def test_token_blocks_split_light_dark():
    css = ":root { --bg: #FFF; }\nbody.dark { --bg: #111; }\n"
    bodies = check_design.token_block_bodies(css)
    assert list(bodies) == ["light", "dark"]


# ── build_brand: _vars, the live bug class, pinned until R4 ─────────────────

# The repro shape: _vars parses line by line with re.match, so a SAME-line
# comment citation is missed harmlessly — the bug fires when a multi-line
# comment's continuation line begins with a declaration-shaped citation.
# Verified live: _vars returns {'--bg': '2.71 against white', ...} for this.
BRAND_CSS_WITH_COMMENT = (
    ".mark {\n"
    "  /* measured:\n"
    "  --bg: 2.71 against white;\n"
    "  */\n"
    "  --gold: #B08D2E;\n"
    "}\n")


def test_build_brand_vars_parses_declarations():
    css = ".mark {\n  --gold: #B08D2E;\n  --ink: #1A1A1A;\n}\n"
    assert build_brand._vars(css, ".mark") == {
        "--gold": "#B08D2E", "--ink": "#1A1A1A"}


@pytest.mark.xfail(
    strict=True,
    reason="build_brand._vars does not strip comments — the 0.1.415 bug "
           "class, still live here; R4's shared css_tokens module fixes it "
           "and must flip this test to passing",
)
def test_build_brand_vars_ignores_comment_prose():
    out = build_brand._vars(BRAND_CSS_WITH_COMMENT, ".mark")
    assert out == {"--gold": "#B08D2E"}


@pytest.mark.xfail(
    strict=True,
    reason="build_brand._vars truncates at the first '}' after the selector, "
           "so a comment containing '}' swallows the rest of the rule; fixed "
           "by R4's shared css_tokens module",
)
def test_build_brand_vars_survives_brace_in_comment():
    css = ".mark { /* like { this } */\n  --gold: #B08D2E;\n}\n"
    assert build_brand._vars(css, ".mark") == {"--gold": "#B08D2E"}
