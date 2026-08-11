"""The one CSS custom-property reader, shared by every script that used to
carry its own copy.

The 0.1.415 escape is the reason this module exists: comment-stripping was
fixed in check_repo's `css_vars` while `build_brand._vars` kept parsing
declaration-shaped prose out of multi-line comments (verified live:
`{'--bg': '2.71 against white'}` read out of a comment), and additionally
truncated its block at the first `}` in the file. One implementation, fixed
once.

Held to strict mypy (disallow_untyped_defs) from birth — see pyproject.toml.
"""
from __future__ import annotations

import re

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_DECL = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")


def strip_comments(css: str, repl: str = "") -> str:
    """Remove /* ... */ comments. `repl` is what a comment becomes: parsing
    wants "" (check_repo's historical behavior); prose extraction wants " "
    so stripping never joins two tokens (check_design's historical behavior).
    """
    return _COMMENT.sub(repl, css)


def css_block(css: str, opener: str) -> str:
    """Return the declarations inside `opener { ... }`, to the MATCHING
    closing brace (nested blocks stay inside). Raises on an unterminated
    block rather than returning a truncation that parses plausibly.
    """
    start = css.index(opener) + len(opener)
    depth = 1
    for i in range(start, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return css[start:i]
    raise ValueError(f"unterminated block: {opener}")


def css_vars(block: str) -> dict[str, str]:
    """-> {name: value} for the custom properties a block declares, names
    WITHOUT the leading `--` (check_repo's historical shape).

    COMMENTS ARE STRIPPED FIRST, and that is not tidiness. Every token in
    this package is documented in prose beside it, and that prose cites token
    names and the contrast numbers they were chosen for. A comment reading
    "measured against --bg: 2.71 / 1.82" parses as a declaration of --bg
    otherwise (the 0.1.415 escape).
    """
    return {m.group(1): m.group(2).strip()
            for m in _DECL.finditer(strip_comments(block))}


def rule_vars(css: str, selector: str) -> dict[str, str]:
    """-> {'--name': value} for the custom properties inside `selector { }`,
    names WITH the leading `--` (build_brand's historical shape), comments
    stripped, block read to the matching brace.

    Comments are stripped BEFORE the block is located: css_block counts
    braces character-by-character, so an unbalanced brace inside a comment
    would otherwise truncate or extend the block.
    """
    return {f"--{k}": v
            for k, v in css_vars(css_block(strip_comments(css),
                                           selector + " {")).items()}
