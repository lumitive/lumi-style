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
LIBRARY = ROOT / "assets" / "shapes"
SPRITE_OPEN = '<svg id="lumi-shape-sprite" aria-hidden="true" style="display:none">'
SPRITE_CLOSE = "</svg>"
SPRITE_RE = re.compile(
    re.escape(SPRITE_OPEN) + r".*?" + re.escape(SPRITE_CLOSE), re.S)
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
    return f'<symbol id="shape-{shape_id}"{box}>{body.strip()}</symbol>'


def build_sprite(ids) -> str:
    return SPRITE_OPEN + "".join(symbol_for(i) for i in ids) + SPRITE_CLOSE


def apply(html: str) -> str:
    ids = referenced(html)
    sprite = build_sprite(ids) if ids else ""
    if SPRITE_RE.search(html):
        return SPRITE_RE.sub(lambda _m: sprite, html, count=1)
    if not sprite:
        return html
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + sprite,
                  html, count=1)


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
