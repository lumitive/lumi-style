"""Tests for scripts/lib/css_tokens.py — the one CSS custom-property reader.

Written first (0.1.419) as characterization tests against the duplicated
copies, with build_brand's two comment bugs pinned as strict xfails; when
0.1.420 replaced build_brand._vars with css_tokens.rule_vars the xfails
XPASSed as designed and were promoted to the plain regression tests below.
"""
import check_design
import css_tokens
import pytest

# ── css_block ────────────────────────────────────────────────────────────────

def test_css_block_extracts_nested():
    css = ":root { --a: 1; @media x { --b: 2; } --c: 3; } .after { --d: 4; }"
    block = css_tokens.css_block(css, ":root {")
    assert "--a: 1" in block and "--c: 3" in block
    assert "--d" not in block


def test_css_block_unterminated_raises():
    with pytest.raises(ValueError, match="unterminated"):
        css_tokens.css_block(":root { --a: 1;", ":root {")


# ── css_vars ─────────────────────────────────────────────────────────────────

def test_css_vars_parses_declarations():
    assert css_tokens.css_vars("--bg: #FFF;\n--ink: #1A1A1A;") == {
        "bg": "#FFF", "ink": "#1A1A1A"}


def test_css_vars_ignores_comment_prose():
    """The 0.1.415 regression: a comment citing a token name must not parse
    as a declaration of that token."""
    block = ("/* measured against --bg: 2.71 / 1.82, from the audit */\n"
             "--ink: #1A1A1A;\n")
    assert css_tokens.css_vars(block) == {"ink": "#1A1A1A"}


def test_strip_comments_repl_variants():
    css = "a/*x*/b"
    assert css_tokens.strip_comments(css) == "ab"
    assert css_tokens.strip_comments(css, " ") == "a b"


# ── check_design: token blocks (stay in check_design — light/dark semantics) ─

def test_token_blocks_accumulate_repeated_root():
    """The 0.1.387 fix: a second :root appends rather than replacing."""
    css = ":root { --bg: #FFF; }\n:root { --rg-a: #123456; }\n"
    blocks = check_design.token_blocks(css)
    assert "--bg" in blocks["light"] and "--rg-a" in blocks["light"]


def test_token_blocks_split_light_dark():
    css = ":root { --bg: #FFF; }\nbody.dark { --bg: #111; }\n"
    bodies = check_design.token_block_bodies(css)
    assert list(bodies) == ["light", "dark"]


# ── rule_vars: the promoted build_brand regressions ──────────────────────────
# The old build_brand._vars parsed line-anchored declarations without comment
# stripping and truncated at the first `}` in the file. Verified live before
# the fix: {'--bg': '2.71 against white'} read out of a comment. These were
# strict xfails until the shared module fixed both.

def test_rule_vars_parses_declarations():
    css = ".mark {\n  --gold: #B08D2E;\n  --ink: #1A1A1A;\n}\n"
    assert css_tokens.rule_vars(css, ".mark") == {
        "--gold": "#B08D2E", "--ink": "#1A1A1A"}


def test_rule_vars_ignores_comment_prose():
    css = (".mark {\n"
           "  /* measured:\n"
           "  --bg: 2.71 against white;\n"
           "  */\n"
           "  --gold: #B08D2E;\n"
           "}\n")
    assert css_tokens.rule_vars(css, ".mark") == {"--gold": "#B08D2E"}


def test_rule_vars_survives_brace_in_comment():
    css = ".mark { /* like { this } */\n  --gold: #B08D2E;\n}\n"
    assert css_tokens.rule_vars(css, ".mark") == {"--gold": "#B08D2E"}


def test_rule_vars_survives_unbalanced_brace_in_comment():
    # css_block counts braces blind, so rule_vars strips comments first —
    # otherwise this lone '}' would end the block before --gold.
    css = ".mark {\n  /* } */\n  --gold: #B08D2E;\n}\n"
    assert css_tokens.rule_vars(css, ".mark") == {"--gold": "#B08D2E"}
