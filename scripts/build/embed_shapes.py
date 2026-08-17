#!/usr/bin/env python3
"""Embed only the shapes a deliverable actually references.

A deliverable is one self-contained HTML file. The shape library is hundreds of
figure units and tens of thousands of primitives, so the two obvious approaches
both fail: inlining the library makes every document megabytes of geometry it
does not use, and pasting a shape in by hand at the point of use bypasses the
recolour layer and lands straight on D20.

So the same shape `embed_icons.py` uses for icons, made selective. A document
references a shape with `<use href="#shape-<id>">`, and this emits a sprite of
**only the symbols that document referenced**.

Two consequences fall out without new machinery:

**D19 becomes this pipeline's correctness check.** A reference that resolves to
no symbol already fails, so a shape that was referenced and not embedded is
caught by a gate that has been running for releases.

**Brand purity stops being a discipline and becomes an engineering fact.** Only
the recoloured library is a source here, so original-palette geometry has no
path into a deliverable at all — nobody has to remember not to use it.

Usage
  embed_shapes.py deck.html                 # rewrite in place, sprite injected
  embed_shapes.py deck.html --check         # is the sprite current?
  embed_shapes.py deck.html --list          # which shapes does it reference?
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())

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

import markup  # noqa: E402 — after the bootstrap

LIBRARY = ROOT / "assets" / "shapes"
SPRITE_OPEN = '<svg id="lumi-shape-sprite" aria-hidden="true" style="display:none">'
SPRITE_CLOSE = "</svg>"
SPRITE_RE = re.compile(
    re.escape(SPRITE_OPEN) + r".*?" + re.escape(SPRITE_CLOSE), re.S)
# Hex fallbacks inside var() are dead weight in a deliverable, where
# the token block always defines them.
_FALLBACK = re.compile(r"var\(\s*(--[\w-]+)\s*,\s*[^)]*\)")
_BBOX_RECT = re.compile(r'<rect[^>]*class="BoundingBox"[^>]*/>\s*')
USE_RE = re.compile(r'<use[^>]+href="#shape-([\w-]+)"')


def referenced(html: str) -> list[str]:
    """Shape ids this document uses, in first-appearance order and deduped."""
    seen: dict[str, None] = {}
    for m in USE_RE.finditer(SPRITE_RE.sub(" ", html)):
        seen[m.group(1)] = None
    return list(seen)


def symbol_for(shape_id: str) -> str:
    """-> a <symbol> carrying that shape's geometry, or raise."""
    path = LIBRARY / f"{shape_id}.svg"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} does not exist. A document may only reference a shape the "
            f"library ships: an id that resolves to nothing renders as empty "
            f"space, which is the failure D19 exists to catch.")
    svg = path.read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', svg)
    body = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S)
    box = f' viewBox="{view.group(1)}"' if view else ""
    # The library ships `var(--acc-4, #889A82)` so a unit renders standalone.
    # A deliverable always carries the token block, so the fallback can never
    # fire — and it lands in the document as a hex literal, which is exactly
    # what D4 counts. Strip it here rather than loosening D4: the library keeps
    # its fallbacks for standalone use, and the deliverable gets the variable
    # alone. Found the first time four shapes were embedded at once.
    body = _FALLBACK.sub(r"var(\1)", body)
    # LibreOffice emits an invisible `<rect class="BoundingBox" fill="none"
    # stroke="none">` beside each shape as layout scaffolding. It draws nothing
    # — and in 7 of the 206 units its x has overflowed to about -2^31, which is
    # what an export writes when an arc has a zero or full sweep. Invisible in
    # the preview, because the viewBox crops it. NOT invisible to getBBox: the
    # rendered-geometry check reported the figure as drawing 3.6 million units
    # outside its own frame, and it was right. Dropping them removes a defect
    # and a third of the sprite's bytes at once.
    body = _BBOX_RECT.sub("", body)
    return f'<symbol id="shape-{shape_id}"{box}>{body.strip()}</symbol>'


def build_sprite(ids) -> str:
    return SPRITE_OPEN + "".join(symbol_for(i) for i in ids) + SPRITE_CLOSE


SKIP_RE = re.compile(
    r"<!--.*?-->|<style\b.*?</style>|<script\b.*?</script>", re.S | re.I)


def _after_body(html: str, sprite: str) -> str:
    """Insert the sprite after the document's REAL <body>, never a quoted one.

    The first version matched `(<body[^>]*>)` and injected after the first hit.
    A deliverable's preamble explains the geometry rule in a CSS comment inside
    its `<style>` block, and that comment contains the literal text
    `<body data-geometry="landscape">` — hundreds of characters ahead of the
    real tag. So the sprite was injected into a stylesheet comment, the browser
    never saw it, and every `<use>` in the document resolved to nothing.

    It rendered as blank space on the page while `--check`, `--list` and D19 all
    reported the document correct — all three read the file, and the file was
    fine. It took a screenshot to see it, which is convention 8 exactly.

    So: comment, `<style>` and `<script>` spans are computed first, and any
    `<body` inside one of them is not the document's body.
    """
    m = markup.body_tag(html)
    if m is not None:
        return html[:m.end()] + "\n" + sprite + html[m.end():]
    raise ValueError(
        "no <body> outside a comment, <style> or <script> — the sprite has "
        "nowhere to go, and injecting it into one of those is how this failed "
        "silently before")


def apply(html: str) -> str:
    ids = referenced(html)
    sprite = build_sprite(ids) if ids else ""
    if SPRITE_RE.search(html):
        return SPRITE_RE.sub(lambda _m: sprite, html, count=1)
    if not sprite:
        return html
    return _after_body(html, sprite)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+", type=pathlib.Path)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the sprite is not what it should be")
    ap.add_argument("--list", action="store_true",
                    help="print the shapes each document references")
    a = ap.parse_args()

    if not LIBRARY.exists() and not a.list:
        sys.exit(f"{LIBRARY.relative_to(ROOT)} does not exist. The shape library "
                 f"has not been ingested yet — curation comes first, and a "
                 f"library ingested without it is a second figure vocabulary "
                 f"competing with the chart rules.")

    worst = 0
    for path in a.files:
        if not path.is_file():
            print(f"no such file: {path}", file=sys.stderr)
            worst = 2
            continue
        html = path.read_text(encoding="utf-8")
        ids = referenced(html)
        if a.list:
            print(f"{path}: {', '.join(ids) if ids else '(no shapes referenced)'}")
            continue
        try:
            want = apply(html)
        except FileNotFoundError as exc:
            print(f"FAIL  {path}: {exc}", file=sys.stderr)
            worst = max(worst, 1)
            continue
        if a.check:
            if want != html:
                print(f"FAIL  {path}: the embedded sprite is not the one its "
                      f"{len(ids)} reference(s) require")
                worst = max(worst, 1)
            else:
                print(f"ok    {path}: {len(ids)} shape(s), sprite current")
            continue
        path.write_text(want, encoding="utf-8")
        print(f"wrote {path}: {len(ids)} shape(s) embedded")
    sys.exit(worst)


if __name__ == "__main__":
    main()
