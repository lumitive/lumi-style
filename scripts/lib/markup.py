#!/usr/bin/env python3
"""Where a deliverable's real markup begins, and nothing else.

One function, because one sentence in this package's own stylesheet has now
cost four separate defects:

    /* ... a document says so with <body data-geometry="landscape"> ... */

That comment sits hundreds of characters ahead of the real `<body>` tag, in
every deliverable, and it contains a literal `<body …>` with a literal
`data-geometry` value. Anything that reaches for the first match finds the
comment:

  * 0.1.492 — `embed_shapes.py` injected the shape sprite after it, so the
    sprite landed inside a CSS comment, the browser never saw it, and every
    `<use>` in the document resolved to nothing. `--check`, `--list` and D19
    all reported the document correct, because all three read the file and the
    file was fine. It took a screenshot to see.
  * 0.1.505 — D9's layout-equivalence lookup read the comment's `landscape`
    on a portrait document, so it looked for the wrong geometry's rules and
    found no equivalences at all.

Both were the same mistake, and the second was made while reading the first
one's comment. So the skip logic lives here now instead of being described.
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import re
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

# A comment, a stylesheet or a script is not markup. Computed first, so a
# `<body` inside one of them is never mistaken for the document's own.
SKIP_RE = re.compile(r"<!--.*?-->|<style\b.*?</style>|<script\b.*?</script>",
                     re.S | re.I)
_BODY_RE = re.compile(r"<body[^>]*>", re.I)


def body_tag(html: str) -> re.Match[str] | None:
    """-> the match for the document's real opening <body> tag, or None."""
    skip = [m.span() for m in SKIP_RE.finditer(html)]
    for m in _BODY_RE.finditer(html):
        if any(a <= m.start() < b for a, b in skip):
            continue
        return m
    return None


def body_attr(html: str, name: str) -> str | None:
    """-> the value of an attribute on the real <body>, or None.

    None means the document does not declare it — never "the first thing that
    looked like it elsewhere in the file".
    """
    m = body_tag(html)
    if m is None:
        return None
    got = re.search(rf'\b{re.escape(name)}="([^"]*)"', m.group(0))
    return got.group(1) if got else None


# --- the words a reader sees ------------------------------------------------
# Four checkers carried their own `re.sub(r"<[^>]+>", " ", s)` plus an
# unescape, each a little different (one lowercased, one collapsed whitespace,
# one did neither), found by the 2026-08-20 audit. A private copy of a shared
# operation is how 0.1.492 and 0.1.505 happened, so the operation lives here
# and the `no shadow markup` guard refuses a fifth copy.
_TAG_RE = re.compile(r"<[^>]+>")
_CJK_GAP_RE = re.compile(r"(?<=[一-鿿]) (?=[一-鿿])")


def strip_tags(fragment: str, sep: str = " ") -> str:
    """Tags become `sep` (a space by default), entities resolve. Whitespace is
    NOT collapsed and case is NOT changed — callers that need either do it,
    visibly. `sep=""` is for a caller asking "is anything left at all"."""
    import html as _html
    return _html.unescape(_TAG_RE.sub(sep, fragment))


def visible_text(fragment: str, sep: str = " ") -> str:
    """strip_tags, then one space between words: the form a quotation, a fact
    scan or a term scan compares against."""
    return " ".join(strip_tags(fragment, sep).split())


def join_cjk(text: str) -> str:
    """Drop the space BETWEEN two CJK characters and nothing else.

    Stripping an inline highlight span leaves a separator where the tag was.
    English needs it, because it lands on a word boundary; Chinese does not,
    because it invents one. On the zh build an agenda line identical to its
    opener read as an orphan and D27 — which gates — failed a correct
    document; the outline mirror failed a pure-CJK title against itself for
    the same reason. Spaces around Latin words are untouched, so
    `每个 Agent 都会` keeps both.
    """
    return _CJK_GAP_RE.sub("", text)
