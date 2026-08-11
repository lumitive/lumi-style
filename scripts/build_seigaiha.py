#!/usr/bin/env python3
"""Generate the Japanese water drawings: the seigaiha ground and the band.

Two drawings, two honesty contracts (references/brand.md; the design record is
specs/2026-08-11-expressive-register-design.md):

The GROUND is seigaiha-*inspired* and deliberately uncountable — overlapping
clusters of concentric arcs, no two clusters sharing a radius, arc count,
position or weight, crowding below the waterline with air above it. It obeys
the ground contract wholesale: colours from the ramp and chart hues via tokens
only, `<defs>`/`<use>`, drawn with `slice`, loudness governed by the
`--ground-*` alpha tiers. A true seigaiha repeat here would be a field
pretending to be water.

The BAND is a true seigaiha repeat — countable on purpose — and is therefore
legal only where nothing sits on it: covers, part openers, footer bands, in the
expressive register, never behind a figure, a table or a field. Its loudness
and height ride the `--seigaiha-*` tokens; the CSS class is `svg.seigaiha`
(`.band` is already the spec strip in lumi-layouts.css).

Every number is a fixed table (index arithmetic, no randomness): the tracked
assets and the fixtures built from these functions must be byte-stable.

    python3 scripts/build_seigaiha.py           # write both assets
    python3 scripts/build_seigaiha.py --check   # verify both are current

Standard library only.
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GROUND_ASSET = ROOT / "assets" / "vectors" / "seigaiha-ground.svg"
BAND_ASSET = ROOT / "assets" / "vectors" / "seigaiha-band.svg"

# The ground's palette, cycled — the same four hues the polyline ground used:
# the deep end of the ramp plus the two cool chart hues, lime nowhere (the lime
# marks a number panel, never water).
PALETTE = ("--acc-5", "--acc-4", "--d-teal", "--d-blue")

# The waterline sits at y=260 on the 1280x720 canvas with one line of air
# above it — the convention the polyline ground established. Row zero's arcs
# are clamped so no crest breaks the surface.
WATERLINE_Y = 260
SURFACE_CLEARANCE = 8


def _arc(cx: float, y: float, r: float, w: float, o: float, colour: str) -> str:
    return (f'<path d="M {cx - r:.1f} {y} A {r:.1f} {r:.1f} 0 0 1 '
            f'{cx + r:.1f} {y}" fill="none" stroke="var({colour})" '
            f'stroke-width="{w:.2f}" stroke-opacity="{o:.2f}"/>')


def ground_marks() -> list[str]:
    """The uncountable water: a waterline and seven rows of arc clusters."""
    pts = " ".join(f"{x} {WATERLINE_Y + 5.5 * math.sin(x / 230 + 0.9):.1f}"
                   for x in range(0, 1281, 40))
    marks = [f'<polyline points="{pts}" fill="none" stroke="var(--acc-4)" '
             f'stroke-width="0.80" stroke-opacity="0.50"/>']
    for r in range(8):
        base_y = 352 + 55 * r + (r * r * 11) % 19
        step = 104 + (r * 13) % 27
        x0 = -70 - (r % 2) * (step // 2) - (r * 7) % 23
        n = (1280 - x0) // step + 2
        for i in range(n):
            cx = x0 + i * step + (i * i * 5 + r * 3) % 15
            radius = 54 + (i * 17 + r * 29) % 25
            # No crest above the waterline: the water stays under the surface.
            radius = min(radius, base_y - WATERLINE_Y - SURFACE_CLEARANCE)
            arcs = 3 + (i * 3 + r) % 3
            width = 0.55 + r * 0.07 + (i % 3) * 0.06
            opacity = min(0.72, 0.18 + r * 0.055 + (i % 4) * 0.015)
            colour = PALETTE[(r + i) % 4]
            for j in range(arcs):
                rr = radius * (1 - j / (arcs + 1)) - (j * (i + r)) % 5
                if rr > 4:
                    marks.append(_arc(cx, base_y, rr, width, opacity, colour))
    return marks


def _fan(cx: float, y: float) -> list[str]:
    """One seigaiha fan: a filled half-disc and three concentric arcs.

    The fill is what makes the wave — each row's fans occlude the row behind.
    """
    R = 34
    fan = [f'<path d="M {cx - R} {y} A {R} {R} 0 0 1 {cx + R} {y} Z" '
           f'fill="var(--acc-1)" stroke="var(--acc-4)" '
           f'stroke-width="1.00" stroke-opacity="0.85"/>']
    for rr in (25.5, 17.0, 8.5):
        fan.append(f'<path d="M {cx - rr} {y} A {rr} {rr} 0 0 1 '
                   f'{cx + rr} {y}" fill="none" stroke="var(--acc-4)" '
                   f'stroke-width="1.00" stroke-opacity="0.85"/>')
    return fan


def band_marks() -> list[str]:
    """The countable water: a true seigaiha repeat, as one 68x64 pattern tile.

    Uniformity is the point here — this is the honest repeat the ground may
    never be. The tile is self-contained: pattern painting clips at the tile,
    so every crescent visible inside the tile is drawn inside the tile, and
    the fans a neighbouring tile would contribute are drawn again at this
    tile's own edges (y=64 is y=0 of the tile below; x=-34 is x=102's twin).
    Painted top-down so the fills occlude — the overlap that makes the wave.
    """
    tile = []
    for cx in (0, 68):          # top row
        tile.extend(_fan(cx, 0))
    for cx in (-34, 34, 102):   # middle row, staggered, with both edge twins
        tile.extend(_fan(cx, 32))
    for cx in (0, 68):          # bottom row: the tile below's top row, again
        tile.extend(_fan(cx, 64))
    return (['<pattern id="p-seigaiha" width="68" height="64" '
             'patternUnits="userSpaceOnUse">'] + tile + ["</pattern>",
            '<rect width="1280" height="96" fill="url(#p-seigaiha)"/>'])


def _defs_svg(gid: str, marks: list[str]) -> str:
    """The inline form: a zero-size defs block a document defines once."""
    return ('<svg width="0" height="0" style="position:absolute" '
            'aria-hidden="true"><defs><g id="' + gid + '">'
            + "".join(marks) + "</g></defs></svg>")


def ground_defs() -> str:
    """Drop-in for build_fixtures: the ground defs under the id `g-ground`."""
    return _defs_svg("g-ground", ground_marks())


def band_defs() -> str:
    return _defs_svg("g-seigaiha", band_marks())


def _asset_svg(viewbox: str, gid: str, marks: list[str]) -> str:
    """The tracked form: one valid SVG carrying the defs and one instance.

    Inline it once and it brings its defs; further instances are
    `<use href="#GID"/>`. Colours are `var()` references with no fallback —
    the drawing takes the palette of the document it lands in, which is the
    point; opened standalone it is intentionally unpainted.
    """
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + viewbox
            + '" preserveAspectRatio="xMidYMid slice" aria-hidden="true" '
            'focusable="false"><defs><g id="' + gid + '">' + "".join(marks)
            + '</g></defs><use href="#' + gid + '"/></svg>\n')


def ground_asset() -> str:
    return _asset_svg("0 0 1280 720", "g-ground", ground_marks())


def band_asset() -> str:
    return _asset_svg("0 0 1280 96", "g-seigaiha", band_marks())


TARGETS = ((GROUND_ASSET, ground_asset), (BAND_ASSET, band_asset))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    stale = []
    for path, builder in TARGETS:
        content = builder()
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if args.check:
            stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if args.check:
        for path in stale:
            print(f"FAIL  {path.relative_to(ROOT)} is stale or missing; "
                  f"re-run without --check")
        if not stale:
            print("ok    seigaiha ground and band are current")
        return 1 if stale else 0
    for path, _ in TARGETS:
        print(f"wrote {path.relative_to(ROOT)}  ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
