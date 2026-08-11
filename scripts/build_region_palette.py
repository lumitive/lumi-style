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
from typing import Any

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
# A BRAND decision bounded by a measured floor, and the number moved once the
# figure was looked at. At the gamut maximum the hues are candy-bright — #F954BE
# beside an accent of #48633E — and 0.65 still read as loud on screen even though
# it measured comfortably. 0.52 is the lowest value that clears the delta-E floor
# with the proximity adjacency below and a +/-5 band spread: 23.4 light and 20.1
# dark against a floor of 20. That is the muted end of what stays separable;
# anything quieter needs fewer regions, not a lower floor.
CHROMA_FRACTION = 0.65
# Retired. The four-band construction is recorded in specs/ and in the CHANGELOG
# because its reasoning was sound and its result was not: with eleven regions it
# put three inside one narrow window, and the minimum separation over ALL pairs —
# not just adjacent ones — was delta-E00 5.0. Europe and Southeast Asia rendered
# as one colour on the same map. Even spacing plus a max-separation assignment
# does better on both counts and needs no constraint on the registry at all.
# A FLOOR on how far apart any two regions sit on the hue circle, whether or not
# they are adjacent. It is 360/N by construction — 32.7 degrees for the eleven
# shipped regions — because the hues are evenly spaced and each region takes one.
ALL_PAIRS_MIN_DEG = None   # computed as 360/N; recorded here as a named idea
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
# Regions closer than this are treated as adjacent even without a land border.
# A CEILING, and it is set by what a reader compares rather than by what touches:
# sharing a border under-counts adjacency badly across narrow water. Europe and
# North America have no land border, so the first version put them in the same
# hue band, and Greenland faces Iceland across 300km of the Atlantic — the two
# rendered as #D67CB0 and #D6819C, which is one colour. Gibraltar and the Bering
# Strait are the same failure. 2500km stops being 4-colourable; 1500 does not.
PROXIMITY_KM = 1500
EARTH_KM = 6371.0


def _decode_arcs(topo):
    q = topo["quantum"]
    out = []
    for flat in topo["arcs"]:
        n = len(flat) // 2
        x, y = flat[0], flat[1]
        pts = [(x / q, y / q)]
        for i in range(1, n):
            x += flat[i * 2]
            y += flat[i * 2 + 1]
            pts.append((x / q, y / q))
        out.append(pts)
    return out


def _great_circle_km(a, b):
    la1, lo1, la2, lo2 = (math.radians(v) for v in (a[1], a[0], b[1], b[0]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return EARTH_KM * 2 * math.asin(min(1.0, math.sqrt(h)))


def region_neighbours(reg):
    """Region adjacency, read out of the topology. Never maintained by hand: a
    hand-written list beside real geometry is correct on the day it is written
    and silently wrong after any change to the registry.

    Two regions are adjacent when they share a border OR come within
    PROXIMITY_KM of each other. The second clause is not a refinement — without
    it the four-colouring is solving the wrong problem, because what has to be
    separable is what a reader sees side by side, and an ocean strait is not a
    visual separation.
    """
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    of = {c: r["id"] for r in reg["regions"] for c in r["members"]}
    out: dict[str, set[str]] = {r["id"]: set() for r in reg["regions"]}
    for country, others in topo["neighbours"].items():
        for other in others:
            a, b = of.get(country), of.get(other)
            if a and b and a != b:
                out[a].add(b)
                out[b].add(a)

    arcs = _decode_arcs(topo)
    pts: dict[str, list[Any]] = {}
    for country in topo["countries"]:
        rid = of.get(country["a"])
        if not rid:
            continue
        for ring in country["rings"]:
            for idx in ring:
                pts.setdefault(rid, []).extend(
                    arcs[idx if idx >= 0 else ~idx][::3])
    ids = sorted(pts)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if b in out[a]:
                continue
            near = any(_great_circle_km(p, r) <= PROXIMITY_KM
                       for p in pts[a][::4] for r in pts[b][::4])
            if near:
                out[a].add(b)
                out[b].add(a)
    return out


def hue_angles(regions, neighbours):
    """-> {region_id: hue in degrees}.

    N regions take N evenly spaced hues, and the assignment maximises the
    smallest hue distance between ADJACENT regions. Two things fall out that the
    earlier four-band construction could not deliver:

    * every pair of regions is at least 360/N apart, adjacent or not. The band
      scheme guaranteed 60 degrees between bands and nothing at all within one,
      and on the shipped registry that meant three regions inside a narrow
      window: Europe and Southeast Asia measured delta-E00 5.0 apart and read as
      one colour on the same map.
    * there is no constraint on the registry. Four bands only worked if the
      adjacency graph was 4-colourable, which the four-colour theorem does not
      guarantee for non-contiguous trade blocs; an assignment over N slots always
      exists, and the delta-E floor is what says whether it is good enough.

    Greedy in descending-degree order, taking the free slot furthest from the
    slots this region's already-placed neighbours hold. On the shipped registry
    that leaves 65.5 degrees between the closest adjacent pair.
    """
    ids = sorted(neighbours)
    n = len(ids)
    if n == 0:
        return {}
    step = 360.0 / n

    def circular(i, j):
        d = abs(i - j) % n
        return min(d, n - d) * step

    def greedy(order, prefer_spread):
        slot: dict[str, int]
        slot, used = {}, set()
        for rid in order:
            placed = [slot[x] for x in neighbours[rid] if x in slot]
            best = None
            for s in range(n):
                if s in used:
                    continue
                nearest = min((circular(s, t) for t in placed),
                              default=float("inf"))
                total = sum(circular(s, t) for t in placed)
                key = (nearest, total if prefer_spread else -total)
                if best is None or key > best[0]:
                    best = (key, s)
            if best is None:  # unreachable: used holds fewer than n slots, so one was free
                raise AssertionError("no free hue slot")
            slot[rid] = best[1]
            used.add(best[1])
        return slot

    def score(slot):
        worst = float("inf")
        for a in ids:
            for b in neighbours[a]:
                worst = min(worst, circular(slot[a], slot[b]))
        return worst

    # A single greedy pass is order-dependent and its tie-break matters more than
    # it looks: two reasonable choices produced 65.5 and 32.7 degrees of worst-case
    # adjacent separation on the same graph, and the second fails the floor. So
    # several deterministic orderings are tried and the best is kept. No
    # randomness — the palette has to be reproducible, and --check compares bytes.
    orders = [
        sorted(ids, key=lambda r: (-len(neighbours[r]), r)),
        sorted(ids, key=lambda r: (len(neighbours[r]), r)),
        sorted(ids),
        sorted(ids, reverse=True),
    ]
    best = None
    for order in orders:
        for prefer_spread in (True, False):
            slot = greedy(order, prefer_spread)
            key = (score(slot), tuple(slot[r] for r in ids))
            if best is None or key[0] > best[0][0]:
                best = (key, slot)
    if best is None:  # unreachable: orders is non-empty, so a candidate was kept
        raise AssertionError("no hue assignment kept")
    return {rid: (best[1][rid] * step) % 360 for rid in ids}


# ── floors ────────────────────────────────────────────────────────────────────
def selftest(reg=None):
    """The floors, asserted against whatever registry is given.

    A palette that stopped clearing its floors would otherwise ship quietly: the
    numbers are invisible on screen and a reviewer cannot compute CIEDE2000 by
    eye. The floors are the contract, not the registry — a custom registry gets
    exactly the same assertion the shipped one does.
    """
    if reg is None:
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
def render(reg=None, prefix=None):
    """The CSS. With `prefix`, a SCOPED block for one instance: variables and
    region rules under `.<prefix>`, and no global chrome — the shipped default
    file already carries `.gl-*`, hover and focus once, and a second copy per
    instance would fight it. Two maps with different registries coexist on one
    page by each taking a prefix."""
    if reg is None:
        reg = json.loads(REGIONS.read_text(encoding="utf-8"))
    neigh = region_neighbours(reg)
    angles = hue_angles(reg["regions"], neigh)
    ids = sorted(angles)
    scope = f".{prefix} " if prefix else ""
    root_sel = f".{prefix}" if prefix else ":root"
    dark_sel = f"body.dark .{prefix}" if prefix else "body.dark"
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
        " * SHIPS THE BINDINGS TOO, since 0.1.391. The variables alone were a",
        " * palette nobody could use: globe_svg.py emits class='rg rg-europe' and",
        " * nothing joined the class to the variable, so any document that did not",
        " * hand-write ~90 rules drew every region in the UA default — black — and",
        " * every check passed, because none reads rendered colour. The reference",
        " * fixture carried the join privately; a package asset should not need a",
        " * private companion to render (maintenance convention 5).",
        " *",
        f" * L {L_LIGHT} light / {L_DARK} dark, chroma {CHROMA_FRACTION:.0%} of the",
        f" * per-hue gamut maximum, {len(ids)} hues evenly spaced at "
        f"{360 / max(1, len(ids)):.1f} degrees, assigned so adjacent regions sit",
        " * as far apart on the circle as the graph allows.",
        " */",
        root_sel + " {",
    ]
    for rid in ids:
        h = angles[rid]
        lines.append(f"  --rg-{rid}: {hue_hex(L_LIGHT, h)};")
        lines.append(f"  --rg-{rid}-stroke: {stroke_hex(L_LIGHT, h, False)};")
        lines.append(f"  --rg-{rid}-wash: {hue_hex(0.94, h)};")
    # The globe chrome variables, beside the region hues. render-canvas.js has
    # read these four via getPropertyValue since it was written, falling back to
    # 'transparent' — so the canvas back end painted nothing, silently, on every
    # host that did not define them, which was every host. They live here rather
    # than in lumi-theme.css because that file's palette is mirrored value-for-
    # value in design-tokens.json under the palette-parity guard; these are
    # figure chrome, they indirect to theme tokens, and the guard has no
    # business learning them.
    if not prefix:
        lines.append("  --gl-plate: var(--ln3);")
        lines.append("  --gl-graticule: var(--ln2);")
        lines.append("  --gl-land: var(--acc-2);")
        lines.append("  --gl-land-edge: var(--ln1);")
    lines.append("  --gl-night: rgba(43,46,51,.28);")
    # The equator is the globe's WATERLINE — brand.md's one horizon where the
    # light collects, applied to a sphere. It had been drawn in the graticule's
    # own ink, so the figure offered four candidate horizons at nearly equal
    # weight and a reader had no datum to read against. One horizon, and it is
    # this one; the tropics stay dashed and quiet because they are context for
    # the tilt rather than a line to measure from.
    # THE THREE NAMED PARALLELS ARE GOLD, and this is the only gold in the
    # package. The graticule is a grid somebody chose; the equator and the
    # tropics are where the planet's axial tilt puts the sun overhead. Drawing
    # them in the same grey as every other line said they were the same kind
    # of thing. A true metallic gold measures 1.7:1 on this plate and the
    # stroke floor is 3.0, so this is antique gold rather than leaf.
    lines.append("  --gold: #A07800;")           # 3.18:1 on the light plate
    lines.append("  --gl-equator: var(--gold);")
    lines.append("  --gl-tropic: var(--gold);")
    lines.append("}")
    lines.append("")
    lines.append(dark_sel + " {")
    lines.append("  --gold: #E8C25A;")           # 8.82:1 on the dark plate
    lines.append("  --gl-equator: var(--gold);")
    lines.append("  --gl-tropic: var(--gold);")
    if not prefix:
        # On the dark canvas the night side cannot be a darker wash — there is
        # nowhere darker to go. It becomes a cool veil instead, which still
        # reads as "not lit" against the land.
        lines.append("  --gl-night: rgba(10,12,20,.45);")
        # THE SPHERE HAS TO BE THERE. The chrome indirects to theme tokens and
        # those redefine under dark, which is true and was not sufficient:
        # --gl-plate resolves to --ln3, and on a #1D1D1F page --ln3 is so close
        # to the background that the ocean and the page became one black field.
        # The globe read as a scatter of continents floating on nothing.
        #
        # Water on a dark page is not the absence of light, it is a surface
        # with less of it — so the plate lifts just clear of the background,
        # and the graticule and the equator lift with it, because a sphere cue
        # nobody can see is not a cue. These are the FOUR VALUES the comment
        # this replaces said were not needed.
        lines.append("  --gl-plate: #26262B;")
        lines.append("  --gl-graticule: rgba(240,240,250,.16);")
    for rid in ids:
        h = angles[rid]
        lines.append(f"  --rg-{rid}: {hue_hex(L_DARK, h)};")
        lines.append(f"  --rg-{rid}-stroke: {stroke_hex(L_DARK, h, True)};")
        lines.append(f"  --rg-{rid}-wash: {hue_hex(0.30, h)};")
    lines.append("}")
    lines.append("")
    if prefix:
        # A scoped palette is regions only: hues, strokes, washes and the
        # class joins, under the instance's own ancestor class. The chrome,
        # hover, focus and state rules ship once, in the default file.
        lines += [f"{scope}.rg {{ stroke-width: 1; }}"]
        for rid in ids:
            lines.append(f"{scope}.rg-{rid} {{ fill: var(--rg-{rid}); "
                         f"stroke: var(--rg-{rid}-stroke); }}")
            lines.append(f"{scope}.rg-{rid}.is-zero "
                         f"{{ fill: var(--rg-{rid}-wash); }}")
        return "\n".join(lines) + "\n"

    lines += [
        "/* The join between the classes the emitters write and the variables",
        " * above. globe_svg.py / the runtime emit these classes; without these",
        " * rules the classes bind to nothing.",
        " *",
        " * Two of the state colours are SEMANTIC in a file whose header says hue",
        " * carries identity only — deliberately: is-out and is-partial are not",
        " * region identity, they are the standing status vocabulary (--brass =",
        " * reference / out of scope, --amber = partial), and painting them from",
        " * the region hue would claim a measurement the hue does not make.",
        " * is-live is the UNMARKED state: the plain region fill IS live, and an",
        " * explicit .is-live rule would just restate the binding above it.",
        " */",
        "/* The plate, with the shadow that lifts the globe off the page. A flat",
        " * filled disc reads as a circle printed on the paper; a shadow under",
        " * it reads as a sphere in front of it, and it costs one declaration",
        " * against a lighting model. Scoped to the plate so the marks and the",
        " * land are not smeared by it. */",
        ".gl-plate { fill: var(--gl-plate); "
        "filter: drop-shadow(0 6px 26px rgba(43,46,51,.22)); }",
        ".gl-graticule { fill: none; stroke: var(--gl-graticule); }",
        ".gl-land { fill: var(--gl-land); stroke: var(--gl-land-edge); stroke-width: 1; }",
        "/* The equator and the tropics are NAMED lines, not graticule: a reader",
        " * can point at them, so they are gold, drawn well above the grid, and",
        " * the tropics are dashed to say they are a pair. At 3 and 2 they read",
        " * as heavier graticule; the weight is what separates a line you can",
        " * name from a line that is scaffolding. */",
        ".gl-equator { fill: none; stroke: var(--gl-equator); "
        "stroke-width: 5; }",
        ".gl-tropic { fill: none; stroke: var(--gl-tropic); stroke-width: 3.5; "
        "stroke-dasharray: 12 9; }",
        "/* Night is a lighting condition laid over the geography, so it is a",
        " * wash rather than a fill and it takes no pointer events — a reader",
        " * aiming at a mark in the dark must still hit the mark. */",
        ".gl-night { fill: var(--gl-night); stroke: none; pointer-events: none; }",
        ".gl-mark { fill: var(--acc); }",
        ".gl-node { fill: var(--bg); stroke: var(--tx2); stroke-width: 1.5; }",
        ".rg { stroke-width: 1; }",
    ]
    for rid in ids:
        lines.append(f"{scope}.rg-{rid} {{ fill: var(--rg-{rid}); "
                     f"stroke: var(--rg-{rid}-stroke); }}")
        lines.append(f"{scope}.rg-{rid}.is-zero {{ fill: var(--rg-{rid}-wash); }}")
    lines += [
        ".rg.is-out { fill: var(--brass); }",
        "/* A bloc's FULL membership, outlined when a reader selects it. No",
        " * fill: the countries underneath keep their own bloc's colour, which",
        " * is the point — the outline says 'these too' without claiming they",
        " * stopped belonging where they were. */",
        "/* The globe's own layers. A city is a NAME on the sphere and a bloc",
        " * label is an identifier over a fill, so both are set in the utility",
        " * face at a weight that survives being drawn over land — and both",
        " * carry a halo, because a label on a globe has no white box to sit",
        " * in the way a map label does. paint-order puts the stroke behind",
        " * the glyph so the halo never eats the letterform. */",
        ".gl-city, .gl-rg-label { font-family: var(--din); "
        "paint-order: stroke fill; stroke: var(--bg); stroke-width: 3.5; "
        "stroke-linejoin: round; pointer-events: none; }",
        ".gl-city { fill: var(--tx2); font-weight: 500; }",
        ".gl-city-dot { fill: var(--tx3); }",
        ".gl-rg-label { fill: var(--nw); font-weight: 700; text-anchor: middle; "
        "letter-spacing: .02em; }",
        ".gl-rg-n { font-variant-numeric: tabular-nums; }",
        "/* The people count recedes: the reader is identifying a bloc, and the",
        " * magnitude is context for the identification rather than the point",
        " * of it. Same relationship .rg-label-v has to .rg-label. */",
        ".gl-rg-p { fill: var(--tx2); font-weight: 400; "
        "font-variant-numeric: tabular-nums; }",
        "/* A BLOC ON THE GLOBE IS QUIETER THAN THE SAME BLOC ON A MAP. The flat",
        " * map is a choropleth and the fill IS the subject; the globe is a",
        " * field of marks and the fill is where they sit. At full strength the",
        " * eight hues buried the marks — Australia read hotter than the datum",
        " * on top of it — so the globe takes the same hue at reduced strength",
        " * and keeps one palette across both figures rather than minting a",
        " * second set of colours that would have to be kept in step. */",
        ".gl-rg { fill-opacity: .42; stroke-opacity: .55; }",
        "/* THE LAND, IN THREE WEIGHTS. Every land line used to be one weight,",
        " * so a coastline and a provincial border looked alike and the eye had",
        " * nothing to group by. A reader asked to compare where one bloc sits",
        " * against another needs the continents to read as shapes first, and",
        " * that is what a hierarchy of line is for.",
        " *",
        " * The FILLS carry no stroke at all now; all linework is here. */",
        ".gl-rg { fill-opacity: .42; stroke: none; }",
        ".gl-land { fill: none; stroke: none; }",
        "/* A coast is a continent's edge, and it is the heaviest line on the",
        " * figure after the data. This is also what puts Oceania back: an",
        " * island coast is a coast whether or not the island is in a bloc, and",
        " * 0.1.405's outline-only rule had left Papua New Guinea, Fiji, the",
        " * Solomons and Vanuatu as 1.2px hairlines. */",
        ".gl-coast { fill: none; stroke: var(--tx2); stroke-width: 2.6; "
        "stroke-linejoin: round; stroke-linecap: round; }",
        "/* Where one trade bloc meets another. Heavier than a border inside a",
        " * bloc and lighter than a coast, which is the order of the question a",
        " * reader is asking. */",
        ".gl-bloc-edge { fill: none; stroke: var(--tx2); stroke-width: 2; "
        "stroke-opacity: .75; stroke-linejoin: round; }",
        "/* A border between two countries in the SAME bloc. Present, because",
        " * the countries are real; faint, because the figure is not about",
        " * them. */",
        ".gl-border { fill: none; stroke: var(--ln1); stroke-width: .8; }",
        ".gl-link { fill: none; stroke: var(--acc); stroke-linecap: round; }",
        ".gl-hub { fill: var(--acc); stroke: var(--bg); stroke-width: 2; }",
        "/* A signal is one code in transit: the dot is where, the text is",
        " * what. The halo is the same one city names carry — a label on a",
        " * sphere has no white box to sit in. */",
        ".gl-sig circle { fill: var(--acc); }",
        ".gl-sig text { fill: var(--acc); font-family: var(--mono); "
        "text-anchor: middle; letter-spacing: .03em; paint-order: stroke fill; "
        "stroke: var(--bg); stroke-width: 3; stroke-linejoin: round; }",
        ".rg-full { pointer-events: none; }",
        ".rg-outline { fill: none; stroke: var(--nw); stroke-width: 4; "
        "stroke-linejoin: round; }",
        ".rg.is-selected { stroke: var(--nw); stroke-width: 3; }",
        ".rg.is-partial { stroke: var(--amber); stroke-width: 2; }",
        "/* Region labels, set in the ink the contrast floor is computed against:",
        " * selftest() asserts every fill carries INK_LIGHT / INK_DARK at 4.5:1 or",
        " * better, and --nw is those two values. A label in any other colour is",
        " * outside the floor's guarantee. */",
        ".rg-label { fill: var(--nw); font-family: var(--din); "
        "font-weight: 600; text-anchor: middle; pointer-events: none; }",
        "/* The two tspans a label can carry. Both have existed as CLASSES since",
        " * labels shipped and neither had a rule, so a value and a membership",
        " * count set identically to the bloc name beside them — the same",
        " * class-with-no-rendering defect the 0.1.396 audit found on the",
        " * globe's hover state, one file away. */",
        ".rg-label-n { font-weight: 700; font-variant-numeric: tabular-nums; }",
        ".rg-label-v { font-weight: 400; fill: var(--tx2); "
        "font-variant-numeric: tabular-nums; }",
        "/* No font-size here: the emitter sets it as an attribute scaled to the",
        " * frame's R, because a fixed pixel size inside a 2R-unit viewBox",
        " * renders at whatever the layout divides it to — 13px became ~7 at a",
        " * typical figure width. CSS would override the attribute, so CSS",
        " * stays silent about size. */",
        "/* Hover and keyboard focus. The runtime has toggled is-hover since the",
        " * globe shipped and no stylesheet anywhere defined it, so hovering",
        " * worked and showed nothing; and the first delivered demo set",
        " * outline:none on a tabindex='0' element with no :focus-visible to",
        " * replace it. Both affordances ship here so no document re-decides",
        " * them. Not inside any media query, per the media-only-rules guard. */",
        ".rg.is-hover { stroke-width: 2.5; }",
        "/* The globe's points need their own hover rule. 0.1.393 shipped the",
        " * region one and the globe kept toggling is-hover on marks and nodes",
        " * against no CSS at all — the same defect, moved rather than closed.",
        " * A mark grows; a node takes the accent so it reads as selected. */",
        ".gl-mark.is-hover { stroke: var(--nw); stroke-width: 3; }",
        ".gl-node.is-hover { fill: var(--acc); stroke: var(--nw); }",
        "/* The drag affordance. The arcball has worked since the globe shipped",
        " * and nothing ever said so: no cursor, no chrome, no hint. A figure",
        " * that can be turned should look like it. */",
        "svg.gl { cursor: grab; }",
        "svg.gl.is-dragging { cursor: grabbing; }",
        "svg.gl:focus-visible, svg.regionmap:focus-visible {",
        "  outline: 2px solid var(--acc); outline-offset: 2px;",
        "}",
    ]
    return "\n".join(lines) + "\n"


def validate_registry(reg, require_full=False):
    """A custom registry's contract, checked before any colour is computed.

    Weaker than check_repo's guard on the shipped registry, on purpose: a
    scoped map — Asia only, say — legitimately covers less than the world, so
    full coverage is opt-in. What is never legitimate: a country claimed by two
    regions (the hue assignment would be ambiguous), a member the topology does
    not carry (a silent no-draw), or a node pointing at a region that is not
    there.
    """
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    known = {c["a"] for c in topo["countries"]}
    seen: dict[str, Any]
    errors, seen = [], {}
    ids = {r["id"] for r in reg.get("regions", [])}
    for r in reg.get("regions", []):
        for want in ("id", "n", "z", "anchor", "members"):
            if want not in r:
                errors.append(f"region {r.get('id', '?')} is missing {want!r}")
        for code in r.get("members", []):
            if code in seen:
                errors.append(f"{code} is claimed by both {seen[code]} and "
                              f"{r['id']} — a country has one region or the "
                              f"hue assignment is ambiguous")
            seen[code] = r.get("id")
            if code not in known:
                errors.append(f"{r.get('id')}: member {code} is not in the "
                              f"topology — it would silently draw nothing")
    for node in reg.get("nodes", []):
        if node.get("region") not in ids:
            errors.append(f"node {node.get('id')} names region "
                          f"{node.get('region')!r}, which this registry does "
                          f"not define")
    if require_full:
        missing = known - set(seen)
        if missing:
            errors.append(f"{len(missing)} topology countries are in no region "
                          f"({', '.join(sorted(missing)[:6])}…) and "
                          f"--require-full-coverage is set")
    return errors


# THE SHIPPED INSTANCES. A registry that ships in assets/vectors/ ships its
# palette too — otherwise every deliverable that uses it hand-rolls one, which
# is convention 5 (a rule may not mandate an asset the package does not ship)
# in the small. A bare --check verifies every row, so adding a registry here is
# the whole of adding it to CI.
SHIPPED = [
    (ROOT / "assets/vectors/regions-trade.json",
     ROOT / "tokens/region-palette-trade.css", "trade"),
]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--regions", metavar="PATH", default=None,
                    help="a custom registry. The floors are asserted against "
                         "it exactly as against the shipped one; coverage of "
                         "the whole topology is opt-in via "
                         "--require-full-coverage, because a scoped map "
                         "legitimately covers less than the world.")
    ap.add_argument("--out", metavar="PATH", default=None,
                    help="where to write. Default: the shipped tokens file "
                         "for the shipped registry; required with --regions, "
                         "because a custom palette must never overwrite the "
                         "tokens the default registry's documents include.")
    ap.add_argument("--prefix", metavar="CLS", default=None,
                    help="scope the emitted variables and rules under this "
                         "ancestor class, so two maps with different "
                         "registries coexist on one page")
    ap.add_argument("--require-full-coverage", action="store_true")
    args = ap.parse_args(argv)

    reg = None
    out_path: pathlib.Path | None = OUT
    if args.regions:
        if not args.out and not args.selftest:
            raise SystemExit("FAIL  --regions needs --out: a custom palette "
                             "must never overwrite tokens/region-palette.css")
        reg = json.loads(pathlib.Path(args.regions).read_text(encoding="utf-8"))
        bad = validate_registry(reg, require_full=args.require_full_coverage)
        if bad:
            for b in bad:
                print(f"FAIL  {b}")
            return 1
        out_path = pathlib.Path(args.out) if args.out else None
    elif args.prefix:
        raise SystemExit("FAIL  --prefix without --regions scopes the SHIPPED "
                         "registry, and the shipped registry's palette is the "
                         "unscoped tokens file; name the registry you mean")

    if args.selftest:
        return selftest(reg)
    if out_path is None:  # unreachable: --regions without --out is refused above unless --selftest
        raise AssertionError("no output path")
    built = render(reg, prefix=args.prefix)
    current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
    if args.check:
        failed = selftest(reg)
        if current != built:
            print(f"FAIL  {out_path} is stale or missing; re-run without --check")
            failed = 1
        elif not failed:
            print(f"ok    {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path} is current")
        if not args.regions:
            # A bare --check is CI's, and CI has to see every shipped palette,
            # not only the default one.
            for reg_path, css_path, prefix in SHIPPED:
                failed |= main(["--check", "--regions", str(reg_path),
                                "--out", str(css_path), "--prefix", prefix])
        return failed
    out_path.write_text(built, encoding="utf-8")
    print(f"wrote {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}"
          f"  ({len(built):,} bytes)")
    if not args.regions:
        # A BARE WRITE COVERS WHAT A BARE CHECK COVERS. It did not: --check
        # recursed over SHIPPED and the write did not, so the only way to
        # refresh the trade palette was to know its three-argument incantation.
        # A change to shared chrome landed in one file, the repo checks passed
        # because they do not run this generator, and CI failed on the other.
        # A build and its check that disagree about what "everything" means is
        # a trap whichever way round it is.
        for reg_path, css_path, prefix in SHIPPED:
            main(["--regions", str(reg_path), "--out", str(css_path),
                  "--prefix", prefix])
    # The registry that was just written, not the shipped one: asserting the
    # default's floors after writing a custom palette would bless a custom
    # registry that clears nothing.
    return selftest(reg)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
