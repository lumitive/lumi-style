#!/usr/bin/env python3
"""The deck's CONTENT, so the scaffold renders a document instead of prompts.

**Why this exists.** `new_deck.py` accepted structure — how many pages, which
parts, which moves — and nothing else. The author's only interface to the words
was regex surgery on the markup it had just emitted. Measured on the first deck
built that way: a 519-line assembly script, 19 hand-written substitutions, and
12 wrong guesses about the shape of the markup (a class name, a tag, a sprite
id, the agenda's structure, an icon id, two collapsed cells, an unclosed
`</div>`, a colophon that wrapped across lines and defeated a single-line
pattern, and a set of coordinates that ignored `preserveAspectRatio`). Each
wrong guess cost an edit, a rebuild, a render and a look — two to three minutes,
and none of it was about the deck.

Every one of those is a guess about a private shape. Handing the scaffold the
content removes the guess: the shape stays where it is written, once.

**Every refusal here is an input shape, never a gate.** A content file that
cannot be rendered stops the build, because the alternative is a deck that
silently drops what it was given — the failure convention 17 measured at eleven
facts lost between two builds of one document, with all forty gates green.

Standard library only.
"""
from __future__ import annotations

import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

# The top-level sections a content file may carry, and the fields each takes.
# A tuple means a mapping with exactly these keys; `None` means a list.
SECTIONS: dict[str, tuple[str, ...] | None] = {
    "cover": ("title", "subject", "sub", "attrs"),
    "closing": ("title", "subject", "sub", "attrs", "colophon"),
    "agenda": None,
    "parts": None,
    "pages": None,
}
# THE AGENDA ROW DOES NOT CARRY A CLAIM, and that is the point. D27 requires
# every agenda line to quote a title the document actually carries, so the row's
# claim IS its part opener's claim — written once in `parts`, quoted here by the
# scaffold. Letting an author write it twice means letting them write it twice
# DIFFERENTLY, which is the gate's failing subject and which the first content
# file built here reproduced on its first run.
AGENDA_FIELDS = ("run",)
PART_FIELDS = ("letter", "claim", "run")
PAGE_FIELDS = ("eyebrow", "title", "sup", "layout", "figlead", "figure",
               "cap", "finds", "take", "blocks")
FIND_FIELDS = ("head", "body", "sem")

# The four meanings the palette carries, and the class each maps to. NOT lane
# indices: `one colour one meaning` governs data, and an index-named set would
# let an author colour the third lane green because it is third.
SEM = {"built": "sem-built", "line": "sem-line",
       "part": "sem-part", "ref": "sem-ref"}

# tokens/lumi-layouts.css's ceiling, and it is a ceiling: `grid-auto-columns:
# 1fr` keeps dividing, and at five the box is narrower than the measure a 13px
# sentence needs. A page with five findings has an outline problem.
MAX_FINDS = 4


class ContentError(ValueError):
    """A content file that cannot be rendered. Raised, never worked around."""


def _keys(where: str, obj, allowed: tuple[str, ...]) -> None:
    if not isinstance(obj, dict):
        raise ContentError(f"{where} must be a mapping, not "
                           f"{type(obj).__name__}")
    stray = sorted(set(obj) - set(allowed))
    if stray:
        # A TYPO MUST NOT BE SILENT. `titel` accepted and ignored is the
        # content interface reproducing the defect it was built to remove:
        # something the author wrote that never reaches the page.
        raise ContentError(
            f"{where} carries {', '.join(repr(k) for k in stray)}, which "
            f"nothing renders. The fields are {', '.join(allowed)}.")


def load(path: pathlib.Path):
    """-> (content, base_dir). Raises ContentError on anything unrenderable."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ContentError(f"{path}: {exc}") from exc
    except ValueError as exc:
        raise ContentError(f"{path}: not valid JSON ({exc})") from exc
    if not isinstance(raw, dict):
        raise ContentError(f"{path}: the top level must be a mapping of "
                           f"{', '.join(SECTIONS)}")
    stray = sorted(set(raw) - set(SECTIONS))
    if stray:
        raise ContentError(
            f"{path}: {', '.join(repr(k) for k in stray)} is not a section. "
            f"The sections are {', '.join(SECTIONS)}.")
    base = path.parent
    for name, fields in SECTIONS.items():
        if name not in raw:
            continue
        if fields is not None:
            _keys(f"{path}: {name}", raw[name], fields)
            continue
        if not isinstance(raw[name], list):
            raise ContentError(f"{path}: {name} must be a list")
    for i, page in enumerate(raw.get("pages") or []):
        _keys(f"{path}: pages[{i}]", page, PAGE_FIELDS)
        _check_page(path, i, page, base)
    for i, row in enumerate(raw.get("agenda") or []):
        _keys(f"{path}: agenda[{i}]", row, AGENDA_FIELDS)
    for i, row in enumerate(raw.get("parts") or []):
        _keys(f"{path}: parts[{i}]", row, PART_FIELDS)
    return raw, base


def _check_page(path, i, page, base) -> None:
    finds = page.get("finds") or []
    if not isinstance(finds, list):
        raise ContentError(f"{path}: pages[{i}].finds must be a list")
    if len(finds) > MAX_FINDS:
        raise ContentError(
            f"{path}: pages[{i}] carries {len(finds)} findings and the row "
            f"holds {MAX_FINDS}. At five the box is narrower than a 13px "
            f"sentence needs and the row grows into the figure — that is an "
            f"outline problem, not a layout one.")
    for j, f in enumerate(finds):
        _keys(f"{path}: pages[{i}].finds[{j}]", f, FIND_FIELDS)
        if not str(f.get("head") or "").strip():
            raise ContentError(f"{path}: pages[{i}].finds[{j}] has no `head`")
        sem = f.get("sem")
        if sem is not None and sem not in SEM:
            raise ContentError(
                f"{path}: pages[{i}].finds[{j}].sem is {sem!r}; the meanings "
                f"are {', '.join(sorted(SEM))} — built/pass, red line, "
                f"partial, reference. Colour is meaning here, so there is no "
                f"free-text option.")
    if page.get("layout") == "dense" and not finds:
        # The layout IS the figure plus what it shows. A dense page with no
        # findings is a `stack` page with a wide drawing, and calling it dense
        # only removes the room the findings would have taken.
        raise ContentError(
            f"{path}: pages[{i}] asks for the `dense` layout and gives no "
            f"findings. Dense is one look-for line, the drawing, and two to "
            f"four findings; without them use `stack`.")
    ref = page.get("figure")
    if ref and not (base / ref).exists():
        # A REFERENCE THAT DOES NOT RESOLVE STOPS THE BUILD. Emitting the
        # placeholder instead would put a finished-looking page in front of a
        # reader with the drawing silently missing.
        raise ContentError(
            f"{path}: pages[{i}].figure names {ref!r}, which is not beside "
            f"the content file. Render it first — the renderers write to "
            f"stdout, so `> {ref}` is the whole step.")


def figure_svg(base: pathlib.Path, ref: str) -> str:
    """-> the drawing at `ref`, inlined. Raises rather than substituting."""
    text = (base / ref).read_text(encoding="utf-8").strip()
    if "<svg" not in text:
        raise ContentError(f"{ref} holds no <svg>; it cannot be a figure")
    return text
