#!/usr/bin/env python3
"""Generate the region hues and prove they clear their floors.

Hue encodes region identity in the globe's region form, which overrides the
default reading of "one colour one meaning". That is an owner directive, and it
is safe only because these hues are declared to carry no data meaning — exactly
the standing light_ramp already has. Semantic colour (accent, seal, amber, brass,
the chart triple) is untouched and still governs data.

OKLCH is the design space; sRGB hex is what ships. It must be hex: parse_color in
check_design.py reads only #rgb, #rrggbb, rgb() and rgba() and returns None
otherwise, so an oklch() token would make D1 skip every region hue in silence,
which is the failure mode this repository fears most.

    python3 scripts/build_region_palette.py            # write the CSS
    python3 scripts/build_region_palette.py --check    # verify current, and the floors
    python3 scripts/build_region_palette.py --selftest # the floors alone

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGIONS = ROOT / "assets" / "vectors" / "regions.json"
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
OUT = ROOT / "tokens" / "region-palette.css"

# Lightness is chosen for the label contrast floor and nothing else: at these
# values the worst hue carries --ink at 4.98:1 on the light canvas and 4.56:1 on
# the dark. Raising L improves the label and worsens the boundary, which is why
# the boundary is a stroke rather than the fill's edge against the canvas.
L_LIGHT, L_DARK = 0.70, 0.52
# Of the per-hue sRGB gamut maximum, found by bisection. A fixed chroma puts
# three to ten hues out of gamut, where clipping silently destroys the even
# spread the whole construction depends on.
#
# 0.65 is a BRAND decision bounded by a measured floor. At the gamut maximum the
# hues come out candy-bright — #F954BE for a region on a page whose accent is
# #48633E — and LUMI is a restrained palette. Pulling chroma back mutes them and
# costs separation, so the two meet here: 0.65 measures delta-E00 22.8 light and
# 21.7 dark against a floor of 20. **Below about 0.45 it stops working** (18.9
# light), and the selftest is what enforces that rather than this comment.
CHROMA_FRACTION = 0.65
# A REQUIREMENT on the registry, not a preference. Measured worst-case adjacent
# separation: B=4 gives delta-E00 24.3 light / 21.5 dark; B=5 gives 20.2 / 17.1,
# which is below the floor on the dark canvas; B=6 fails on both.
BANDS = 4
BAND_SPREAD = 15.0          # degrees either side of the band centre
DELTA_E_FLOOR = 20.0        # adjacent regions, CIEDE2000 — a FLOOR
LABEL_CONTRAST_FLOOR = 4.5  # a FLOOR, the repository's existing text floor
STROKE_CONTRAST_FLOOR = 3.0 # a FLOOR, WCAG 1.4.11 for the region's boundary
STROKE_L_OFFSET = 0.20      # darker on the light canvas, lighter on the dark

INK_LIGHT, INK_DARK = "#212621", "#F0F0FA"
BG_LIGHT, BG_DARK = "#FFFFFF", "#1D1D1F"


# ── colour ────────────────────────────────────────────────────────────────────
def oklch_to_srgb(L, C, h):
    """-> ((r, g, b) in 0..1 after clamping, in_gamut)."""
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
           -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
           -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    in_gamut = all(-0.001 <= v <= 1.001 for v in lin)

    def enc(v):
        v = max(0.0, min(1.0, v))
        return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return tuple(enc(v) for v in lin), in_gamut


def max_chroma(L, h):
    lo, hi = 0.0, 0.4
    for _ in range(40):
        mid = (lo + hi) / 2
        if oklch_to_srgb(L, mid, h)[1]:
            lo = mid
        else:
            hi = mid
    return lo


def hue_hex(L, h):
    rgb, _ = oklch_to_srgb(L, max_chroma(L, h) * CHROMA_FRACTION, h)
    return "#" + "".join(f"{round(v * 255):02X}" for v in rgb)


def stroke_hex(L, h, lighter):
    """The region's own hue at L offset toward the canvas's opposite, so the
    boundary reads as this region's edge rather than as a separate grid."""
    return hue_hex(L + STROKE_L_OFFSET if lighter else L - STROKE_L_OFFSET, h)


def _rgb(value):
    v = value.lstrip("#")
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(fg, bg):
    """WCAG 2.1 relative-luminance ratio between two hex colours."""
    def luma(hexcol):
        r, g, b = (_lin(c) for c in _rgb(hexcol))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    a, b = luma(fg) + 0.05, luma(bg) + 0.05
    return max(a, b) / min(a, b)


def lab_of(hexcol):
    r, g, b = (_lin(c) for c in _rgb(hexcol))
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29
    fx, fy, fz = f(x / 0.95047), f(y), f(z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def ciede2000(c1, c2):
    L1, a1, b1 = c1
    L2, a2, b2 = c2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb > 0 else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif dh > 180:
        dhp = dh - 360
    elif dh < -180:
        dhp = dh + 360
    else:
        dhp = dh
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp > 0 else 0.0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * (30 * math.exp(-((hbp - 275) / 25) ** 2)))) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


# ── assignment ────────────────────────────────────────────────────────────────
def region_neighbours(reg):
    """Region adjacency, read out of the topology. Never maintained by hand: a
    hand-written list beside real geometry is correct on the day it is written
    and silently wrong after any change to the registry."""
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    of = {c: r["id"] for r in reg["regions"] for c in r["members"]}
    out = {r["id"]: set() for r in reg["regions"]}
    for country, others in topo["neighbours"].items():
        for other in others:
            a, b = of.get(country), of.get(other)
            if a and b and a != b:
                out[a].add(b)
                out[b].add(a)
    return out


def assign_bands(neighbours):
    """Greedy four-colouring in descending-degree order.

    It fails rather than reaching for a fifth band. The four-colour theorem does
    not cover this graph — it is about contiguous regions of a planar map, and
    trade blocs are routinely non-contiguous — so 4-colourability is a
    requirement on the registry that has to be checked, not a guarantee that can
    be assumed.
    """
    order = sorted(neighbours, key=lambda r: (-len(neighbours[r]), r))
    band, load = {}, {k: 0 for k in range(BANDS)}
    for rid in order:
        taken = {band[n] for n in neighbours[rid] if n in band}
        # Least-loaded free band, not the lowest-numbered one. Plain greedy
        # colouring is correct and badly unbalanced: on the shipped registry it
        # used three bands and put six regions inside one 30-degree window, so
        # six regions rendered as six shades of the same pink. They never share
        # a border, so the delta-E floor did not notice, and a floor that cannot
        # see the defect is not the thing to argue with — balancing is.
        free = sorted((k for k in range(BANDS) if k not in taken),
                      key=lambda k: (load[k], k))
        if not free:
            raise SystemExit(
                f"FAIL  the region adjacency graph needs more than {BANDS} "
                f"colours: {rid} borders {sorted(neighbours[rid])} and every "
                f"band is taken. Only four bands clear the delta-E floor on "
                f"both canvases, so merge or re-cut those regions in "
                f"assets/vectors/regions.json.")
        band[rid] = free[0]
        load[free[0]] += 1
    return band


def hue_angles(regions, neighbours):
    """-> {region_id: hue in degrees}.

    Bands sit at 90k degrees and members spread +/-15 within their band, so two
    regions in different bands are at least 60 degrees apart. Same-band regions
    may be close and by construction never share a border.
    """
    band = assign_bands(neighbours)
    per_band = {}
    for rid in sorted(band):
        per_band.setdefault(band[rid], []).append(rid)
    out = {}
    for k, members in sorted(per_band.items()):
        n = len(members)
        for i, rid in enumerate(members):
            offset = 0.0 if n == 1 else -BAND_SPREAD + 2 * BAND_SPREAD * i / (n - 1)
            out[rid] = (90.0 * k + offset) % 360
    return out


# ── floors ────────────────────────────────────────────────────────────────────
def selftest():
    """The floors, asserted against the shipped registry.

    A palette that stopped clearing its floors would otherwise ship quietly: the
    numbers are invisible on screen and a reviewer cannot compute CIEDE2000 by
    eye.
    """
    reg = json.loads(REGIONS.read_text(encoding="utf-8"))
    neigh = region_neighbours(reg)
    angles = hue_angles(reg["regions"], neigh)
    errors, worst = [], {}
    for L, ink, bg, name, lighter in ((L_LIGHT, INK_LIGHT, BG_LIGHT, "light", False),
                                      (L_DARK, INK_DARK, BG_DARK, "dark", True)):
        hexes = {rid: hue_hex(L, h) for rid, h in angles.items()}
        wl = min(contrast(ink, hexes[rid]) for rid in hexes)
        ws = min(contrast(stroke_hex(L, angles[rid], lighter), bg) for rid in hexes)
        pairs = [(a, b) for a in neigh for b in neigh[a] if a < b]
        wd = min((ciede2000(lab_of(hexes[a]), lab_of(hexes[b])) for a, b in pairs),
                 default=float("inf"))
        worst[name] = (wl, ws, wd)
        for rid in sorted(hexes):
            c = contrast(ink, hexes[rid])
            if c < LABEL_CONTRAST_FLOOR:
                errors.append(f"{name}: label on {rid} is {c:.2f}:1, "
                              f"floor {LABEL_CONTRAST_FLOOR}")
            s = contrast(stroke_hex(L, angles[rid], lighter), bg)
            if s < STROKE_CONTRAST_FLOOR:
                errors.append(f"{name}: stroke of {rid} is {s:.2f}:1 on the "
                              f"canvas, floor {STROKE_CONTRAST_FLOOR}")
        for a, b in pairs:
            d = ciede2000(lab_of(hexes[a]), lab_of(hexes[b]))
            if d < DELTA_E_FLOOR:
                errors.append(f"{name}: {a} and {b} are adjacent and only "
                              f"ΔE00 {d:.1f} apart, floor {DELTA_E_FLOOR}")
    for e in sorted(set(errors)):
        print(f"FAIL  {e}")
    if errors:
        return 1
    for name, (wl, ws, wd) in worst.items():
        print(f"ok    {name}: worst label {wl:.2f}:1 (floor 4.5), "
              f"worst stroke {ws:.2f}:1 (floor 3.0), "
              f"worst adjacent ΔE00 {wd:.1f} (floor 20)")
    return 0


# ── emit ──────────────────────────────────────────────────────────────────────
def render():
    reg = json.loads(REGIONS.read_text(encoding="utf-8"))
    neigh = region_neighbours(reg)
    angles = hue_angles(reg["regions"], neigh)
    ids = sorted(angles)
    lines = [
        "/* LUMI region palette — GENERATED by scripts/build_region_palette.py.",
        " * Do not edit: run the script. --check fails on a stale file.",
        " *",
        " * Hue encodes region IDENTITY and carries no data meaning, the standing",
        " * light_ramp already has. One colour one meaning still governs data.",
        " * Identity is a label, not a measurement, so text carries it: every",
        " * coloured region takes a label or a legend entry, checked by D18.",
        " *",
        " * Generated in OKLCH and shipped as sRGB hex, never as an oklch() value:",
        " * parse_color in check_design.py cannot read that form and would skip D1",
        " * on every hue here without saying so.",
        " *",
        f" * L {L_LIGHT} light / {L_DARK} dark, chroma {CHROMA_FRACTION:.0%} of the",
        f" * per-hue gamut maximum, {BANDS} bands at 90 degrees, members +/-"
        f"{BAND_SPREAD:.0f} within a band.",
        " */",
        ":root {",
    ]
    for rid in ids:
        h = angles[rid]
        lines.append(f"  --rg-{rid}: {hue_hex(L_LIGHT, h)};")
        lines.append(f"  --rg-{rid}-stroke: {stroke_hex(L_LIGHT, h, False)};")
        lines.append(f"  --rg-{rid}-wash: {hue_hex(0.94, h)};")
    lines.append("}")
    lines.append("")
    lines.append("body.dark {")
    for rid in ids:
        h = angles[rid]
        lines.append(f"  --rg-{rid}: {hue_hex(L_DARK, h)};")
        lines.append(f"  --rg-{rid}-stroke: {stroke_hex(L_DARK, h, True)};")
        lines.append(f"  --rg-{rid}-wash: {hue_hex(0.30, h)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    built = render()
    current = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if args.check:
        failed = selftest()
        if current != built:
            print(f"FAIL  {OUT.relative_to(ROOT)} is stale or missing; "
                  f"re-run without --check")
            failed = 1
        elif not failed:
            print(f"ok    {OUT.relative_to(ROOT)} is current")
        return failed
    OUT.write_text(built, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(built):,} bytes)")
    return selftest()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
