#!/usr/bin/env python3
"""Generate LUMIVATE's brand marks.

    python3 scripts/build_brand.py            # write
    python3 scripts/build_brand.py --check    # verify current (CI)

The globe is LUMIVATE's icon. It is generated from the same projection and the
same topology as the figures, rather than drawn, so the mark on a cover and the
figure inside it are the same object at two sizes — which is the whole reason a
company mark built from a component is worth having.

WHAT AN ICON DROPS. Everything that needs room to be read: cities, bloc fills,
bloc labels, trade lanes, signals, the terminator. At 96px a name is three
pixels tall and a lane is a scratch. What survives is the sphere, the
graticule, the coastline and the axis — and the axis is what makes a 96px disc
read as a planet rather than a circle with texture on it.

Two sizes, because one does not serve both ends:

    globe-mark.svg        coastline, graticule and axis, for 64px and up
    globe-mark-small.svg  coastline and axis, no graticule, for 16-48px

The small one is not the large one scaled down. Below about 48px a 15-degree
graticule falls closer together than the pixels and turns to moire, so it is
left out rather than shrunk — while the coastline, being a filled silhouette,
survives being small and is the only thing that says planet at 16px.

These files are LOCKED. See assets/brand/LOCKED.json.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import globe_svg                                                   # noqa: E402

OUT_DIR = ROOT / "assets" / "brand" / "lumivate"

# Centred on 20E so Europe, Africa and western Asia fill the disc: a mark wants
# land in it, and an ocean-centred globe reads as an empty circle at icon size.
VIEW = (20.0, 18.0, 0.0, 100.0, 100.0, 100.0)

# SELF-CONTAINED, AND THE SAME STYLE AS THE COVER.
#
# The first cut of this mark was monochrome — one ink at three strengths, on
# the reasoning that a logo has to print in one colour. The owner removed it:
# the mark on the closing page has to be the globe on the cover, not a second
# design of the same object. A company whose figure and whose mark disagree has
# two marks.
#
# So the styles below are the cover's, inlined. Inlined rather than referenced
# because a mark still has to render on a page that has never heard of
# tokens/ — dropped into a slide, an email, somebody else's site — and a var()
# in a mark is a var() that resolves to nothing there.
#
# It carries its own DARK MODE too, on prefers-color-scheme, so the same file
# is correct on a white page and a black one without the host doing anything.
def _vars(css, selector):
    """The custom-property declarations inside one rule, as a dict."""
    i = css.index(selector + " {")
    j = css.index("}", i)
    out = {}
    for line in css[i:j].splitlines():
        m = re.match(r"\s*(--[\w-]+)\s*:\s*([^;]+);", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def mark_style(force=None):
    """The cover's look, resolved to literals and scoped to the mark.

    `force` pins one palette instead of following prefers-color-scheme. A
    document that ships a light and a dark edition needs a file per edition —
    prefers-color-scheme follows the BROWSER, not the page it is dropped on, so
    an unforced mark on a light deck goes dark in a dark-mode browser.
    """
    theme = (ROOT / "tokens/lumi-theme.css").read_text(encoding="utf-8")
    # region-palette.css AND its trade-scoped sibling. The chrome variables —
    # --gl-plate, --gl-graticule, --gl-equator — are emitted only in the
    # UNSCOPED file, because a scoped instance is regions-only by design. Read
    # just the scoped one and every var() resolves to nothing, `fill` is
    # invalid, and an SVG with an invalid fill is a BLACK SVG. The whole ocean
    # came out black in both palettes and it looked deliberate.
    base = (ROOT / "tokens/region-palette.css").read_text(encoding="utf-8")
    trade = (ROOT / "tokens/region-palette-trade.css").read_text(encoding="utf-8")
    light = {**_vars(theme, ":root"), **_vars(base, ":root"), **_vars(trade, ".trade")}
    dark = {**light, **_vars(theme, "body.dark"), **_vars(base, "body.dark"),
            **_vars(trade, "body.dark .trade")}

    def decl(v):
        # One indirection deep is all the token files use, and resolving it
        # here is what makes the file standalone.
        seen = 0
        while v.startswith("var(") and seen < 4:
            v = light.get(v[4:v.index(")")].strip(), v)
            seen += 1
        return v

    def block(vals, scope):
        rows = [f"{scope}{{"]
        for k, v in sorted(vals.items()):
            rows.append(f"{k}:{v};")
        rows.append("}")
        return "".join(rows)

    rules = (
        ".lumivate-mark .gl-plate{fill:var(--gl-plate)}"
        ".lumivate-mark .gl-graticule{fill:none;stroke:var(--gl-graticule);"
        "stroke-width:1.4}"
        ".lumivate-mark .gl-equator{fill:none;stroke:var(--gl-equator);"
        "stroke-width:3}"
        ".lumivate-mark .gl-tropic{fill:none;stroke:var(--gl-tropic);"
        "stroke-width:2;stroke-dasharray:10 8}"
        ".lumivate-mark .gl-land{fill:none;stroke:none}"
        ".lumivate-mark .gl-rg{fill-opacity:.42;stroke:none}"
        ".lumivate-mark .gl-coast{fill:none;stroke:var(--tx2);stroke-width:2.6;"
        "stroke-linejoin:round;stroke-linecap:round}"
        ".lumivate-mark .gl-bloc-edge{fill:none;stroke:var(--tx2);stroke-width:2;"
        "stroke-opacity:.75;stroke-linejoin:round}"
        ".lumivate-mark .gl-border{fill:none;stroke:var(--ln1);stroke-width:.8}"
    )
    for rid in sorted({k[5:] for k in light if k.startswith("--rg-")
                       and not k.endswith(("-stroke", "-wash"))}):
        rules += f".lumivate-mark .rg-{rid}{{fill:var(--rg-{rid})}}"

    keep = lambda d: {k: decl(v) for k, v in d.items()
                      if k.startswith(("--rg-", "--gl-")) or k in
                      ("--tx1", "--tx2", "--tx3", "--ln1", "--ln2", "--ln3",
                       "--bg", "--nw", "--acc", "--acc-2")}
    if force == "light":
        return "<style>" + block(keep(light), ".lumivate-mark") + rules + "</style>"
    if force == "dark":
        return "<style>" + block(keep(dark), ".lumivate-mark") + rules + "</style>"
    return ("<style>"
            + block(keep(light), ".lumivate-mark")
            + rules
            + "@media (prefers-color-scheme: dark){"
            + block(keep(dark), ".lumivate-mark") + "}"
            + "</style>")


NOTE = ("<!-- LUMIVATE brand mark. GENERATED by scripts/build_brand.py and "
        "LOCKED: see assets/brand/LOCKED.json. Do not edit, and do not change "
        "what it is generated from without the brand owner's sign-off. -->")


def _strip(svg, classes):
    """Drop whole elements by class. An icon is what is left."""
    for cls in classes:
        svg = re.sub(rf'<(path|circle|line|text|g)\b[^>]*class="[^"]*\b{cls}\b'
                     rf'[^"]*"[^>]*/>\s*', "", svg)
        svg = re.sub(rf'<(path|circle|line|text|g)\b[^>]*class="[^"]*\b{cls}\b'
                     rf'[^"]*"[^>]*>.*?</\1>\s*', "", svg, flags=re.S)
    return svg


def build(small=False):
    svg = globe_svg.render(
        VIEW, night=None,
        regions_path=str(ROOT / "assets/vectors/regions-trade.json"))
    svg = _strip(svg, ["gl-night", "gl-node", "gl-equator", "gl-tropic",
                       "gl-axis-ref"])
    if small:
        # The SMALL mark drops the GRATICULE, not the land. Dropping the land
        # was the obvious cut and it was the wrong one: it left a plain disc
        # with a line through it, which reads as a prohibition sign and not as
        # a planet. Below 48px a 15-degree graticule is moire — the lines fall
        # closer together than the pixels — while a filled continent is a
        # silhouette, and a silhouette is exactly what survives being small.
        svg = _strip(svg, ["gl-graticule"])
    svg = svg.replace('class="gl"', 'class="gl lumivate-mark"', 1)
    svg = svg.replace('<g class="gl-earth"', mark_style() + '<g class="gl-earth"', 1)
    svg = svg.replace('aria-label="LUMI globe, field of marks"',
                      'aria-label="LUMIVATE"', 1)
    svg = re.sub(r"<!-- generated by scripts/globe_svg\.py[^>]*-->", NOTE, svg, count=1)
    return svg.rstrip() + "\n"


# The COVER globe: LUMIVATE's mark at the size a document opens with, in both
# palettes as separate files. A cover is a fixed frame — a deck's PDF and its
# projection both freeze it — so the static pair is what most documents need,
# and the live version is two lines away (see assets/brand/README.md).
COVER_VIEW = (-160.0, 10.0, 0.0, 1000.0, 1000.0, 1000.0)


def build_cover(dark=False):
    svg = globe_svg.render(
        COVER_VIEW, night=None,
        regions_path=str(ROOT / "assets/vectors/regions-trade.json"))
    svg = _strip(svg, ["gl-node"])
    svg = svg.replace('class="gl"', 'class="gl lumivate-mark"', 1)
    svg = svg.replace('aria-label="LUMI globe, field of marks"',
                      'aria-label="LUMIVATE"', 1)
    style = mark_style(force="dark" if dark else "light")
    svg = svg.replace('<g class="gl-earth"', style + '<g class="gl-earth"', 1)
    svg = re.sub(r"<!-- generated by scripts/globe_svg\.py[^>]*-->", NOTE, svg, count=1)
    return svg.rstrip() + "\n"


TARGETS = {"globe-mark.svg": False, "globe-mark-small.svg": True}
COVER_TARGETS = {"globe-cover.svg": False, "globe-cover.dark.svg": True}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    failed = 0
    for name, dark in COVER_TARGETS.items():
        path = OUT_DIR / name
        built = build_cover(dark)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if args.check:
            if current != built:
                print(f"FAIL  {path.relative_to(ROOT)} is stale or missing")
                failed = 1
            else:
                print(f"ok    {path.relative_to(ROOT)} is current")
        else:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(built, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}  ({len(built):,} bytes)")
    for name, small in TARGETS.items():
        path = OUT_DIR / name
        built = build(small)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if args.check:
            if current != built:
                print(f"FAIL  {path.relative_to(ROOT)} is stale or missing; "
                      f"re-run without --check")
                failed = 1
            else:
                print(f"ok    {path.relative_to(ROOT)} is current")
            continue
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(built, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}  ({len(built):,} bytes)")
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
