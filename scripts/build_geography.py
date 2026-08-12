#!/usr/bin/env python3
"""Render assets/vectors/ from lat/lon data.

The cover mark and the trade-region map are geography, so they are generated
from coordinates rather than drawn by hand: a hand-drawn SVG cannot be re-centred,
cannot be checked, and drifts the moment someone nudges a point.

    python3 scripts/build_geography.py           # write both SVGs
    python3 scripts/build_geography.py --check   # verify they are current

Two outputs:
  globe-orthographic.svg  the cover and closing mark. Orthographic projection
                          centred on the Pacific, because every node of the chain
                          this design language was last exercised on sits on the
                          Pacific rim, and a globe that hides the subject is
                          decoration.
  world-flat.svg          equirectangular, all trade regions visible at once,
                          each an addressable <g> so a document can state that
                          region's coverage instead of implying it.

The coastlines are a deliberately coarse stylisation (roughly 2 degrees of
resolution, no islands under about 500 km). They are a design mark and must never
be presented as survey data or used to make a geographic claim.

No literal colour appears here. Every shape carries a class and the host document
paints it from tokens, per design-rules.md §1.
Standard library only.
"""
from __future__ import annotations

import argparse
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win (the stdlib-shadowing hijack documented in emergency_merge.sh
# stays dead; the emergency path's protection is trusted copies overwriting
# a PR's files at the same paths, not path order).
import pathlib as _bs_pathlib  # noqa: E402
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("", "lib", "render", "check", "build", "ops"):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import geo_projection as gp  # noqa: E402 — after the bootstrap, deliberately

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "vectors"

# ── coastlines, (lon, lat), coarse ────────────────────────────────────────────
LAND = {
    "north-america": [
        (-168, 66), (-155, 71), (-133, 70), (-115, 70), (-100, 69), (-85, 73),
        (-72, 68), (-62, 58), (-55, 50), (-66, 44), (-71, 42), (-76, 35),
        (-80, 25), (-84, 30), (-90, 29), (-97, 26), (-105, 20), (-110, 24),
        (-117, 32), (-124, 42), (-130, 54), (-140, 60), (-152, 59), (-168, 66),
    ],
    "central-america": [
        (-105, 20), (-97, 26), (-94, 18), (-88, 21), (-87, 15), (-83, 9),
        (-78, 8), (-83, 13), (-92, 16), (-100, 18), (-105, 20),
    ],
    "south-america": [
        (-78, 8), (-71, 12), (-60, 10), (-51, 4), (-45, -2), (-35, -6),
        (-38, -15), (-48, -25), (-54, -34), (-62, -41), (-66, -50), (-70, -55),
        (-74, -45), (-72, -33), (-70, -18), (-75, -14), (-79, -5), (-78, 8),
    ],
    "greenland": [
        (-45, 60), (-53, 66), (-57, 71), (-50, 77), (-38, 80), (-24, 82),
        (-19, 76), (-27, 70), (-36, 64), (-45, 60),
    ],
    "africa": [
        (-17, 14), (-16, 21), (-10, 29), (-2, 35), (10, 34), (20, 32), (32, 31),
        (35, 24), (39, 15), (43, 12), (51, 12), (50, 4), (42, -2), (40, -11),
        (36, -20), (32, -27), (25, -34), (18, -34), (14, -24), (12, -15),
        (9, -1), (4, 5), (-4, 5), (-11, 7), (-17, 14),
    ],
    "eurasia": [
        (-10, 36), (-9, 44), (-1, 49), (4, 52), (8, 58), (11, 58), (19, 65),
        (28, 71), (40, 68), (55, 71), (70, 73), (85, 74), (100, 76), (115, 73),
        (130, 72), (142, 72), (160, 70), (170, 66), (179, 65), (170, 60),
        (162, 58), (155, 52), (143, 46), (140, 40), (135, 35), (127, 35),
        (122, 31), (117, 23), (110, 20), (107, 11), (104, 9), (100, 6),
        (98, 10), (94, 16), (90, 22), (87, 21), (80, 15), (77, 8), (73, 17),
        (69, 23), (66, 25), (60, 25), (58, 20), (54, 17), (48, 13), (43, 13),
        (39, 21), (35, 28), (36, 32), (44, 37), (36, 36), (28, 38), (20, 40),
        (12, 44), (3, 42), (-6, 36), (-10, 36),
    ],
    "maritime-se-asia": [
        (95, 5), (100, 2), (104, -2), (106, -6), (112, -8), (118, -9),
        (119, -4), (117, 1), (112, 3), (105, 6), (100, 6), (95, 5),
    ],
    "australia": [
        (114, -22), (114, -33), (118, -35), (129, -32), (138, -35), (147, -38),
        (153, -28), (147, -19), (142, -11), (132, -11), (126, -14), (114, -22),
    ],
}

# The globe is centred on the Pacific, so its middle is ocean. That is not a gap
# to hide: the ocean is what the chain crosses, and the routes drawn over it are
# the mark's content. Greenland is dropped from the globe because it is nothing
# to do with the subject and its Arctic foreshortening dominates the top limb.
GLOBE_SKIP = {"greenland"}
ROUTES = [
    ("China", "Mexico"), ("Vietnam", "Mexico"), ("Thailand", "Mexico"),
    ("Mexico", "United States"),
]

# ── markers, with their coverage state ────────────────────────────────────────
# "live"  the chain the design language was last exercised on, built and running
# "zero"  a named market whose dictionary holds zero rows
# "out"   a region outside the current design scope
MARKERS = [
    ("China",         120.2,  30.3, "live"),
    ("Vietnam",       105.8,  21.0, "live"),
    ("Thailand",      100.5,  13.8, "live"),
    ("Mexico",       -100.3,  25.7, "live"),
    ("United States",  -98.0, 39.0, "live"),
    ("Canada",       -106.0,  56.0, "zero"),
    ("ASEAN",         110.0,   2.0, "zero"),
    ("Europe",         10.0,  50.0, "out"),
    ("Middle East",    45.0,  25.0, "out"),
    ("South America", -60.0, -15.0, "out"),
]

GLOBE_CENTRE = (-170.0, 20.0)   # Pacific. A globe centred here is mostly ocean,
                                # which is the point: the ocean is what the chain
                                # crosses. Compose it cropped at a page edge rather
                                # than centred, or the empty hemisphere dominates.
R = 150.0
STEP_DEG = 1.5                  # edge densification before projection


# ── projection ────────────────────────────────────────────────────────────────
# The maths lives in geo_projection.py, because three other callers need it:
# build_worldmap.py, globe_svg.py, and the JavaScript port in assets/globe/.
# It moved out of this file unchanged — --check below is what proves that — and
# these wrappers supply this file's fixed R, centre and densification step so no
# call site here had to change.
def _densify(ring):
    return gp.densify(ring, STEP_DEG)


def _great_circle(a, b, n=96):
    return gp.great_circle(a, b, n)


def _cos_c(lon, lat, lon0, lat0):
    return gp.cos_c(lon, lat, lon0, lat0)


def _project(lon, lat, lon0, lat0):
    return gp.project(lon, lat, lon0, lat0, R, R, R)


def _ortho(lon, lat, lon0, lat0):
    return gp.ortho(lon, lat, lon0, lat0, R, R, R)


def _crossing(inside, outside, lon0, lat0):
    return gp.crossing(inside, outside, lon0, lat0, R, R, R)


def _visible_runs(points, lon0, lat0, exact=True):
    return gp.visible_runs(points, lon0, lat0, R, R, R, exact=exact)


def _on_limb(p):
    return gp.on_limb(p, R, R, R)


def _limb_walk(a, b):
    return gp.limb_walk(a, b, R, R, R)


def _outer(ring):
    """The ring wound as an outer ring — interior on the right, seen from
    outside — which is what the limb walk needs to close it the right way.

    These eight rings are hand-authored coordinate tables and their winding is
    ACCIDENTAL: `maritime-se-asia` and `australia` score negative, with no hole
    to justify it, because of the order someone typed the coastline in. That did
    not matter while limb_walk took the shorter arc and it decides the arc now,
    so it is normalised here rather than by reordering two tables where a
    reviewer could not see the difference.

    Only the globe needs this. The flat map draws every ring whole and never
    closes one along a boundary, so winding says nothing there.
    """
    return ring if gp.signed_area(ring) > 0 else ring[::-1]


def _path(runs, close_on_limb):
    out = []
    for run in runs:
        pts = list(run)
        if close_on_limb and _on_limb(pts[0]) and _on_limb(pts[-1]):
            pts += _limb_walk(pts[-1], pts[0])
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}" + "".join(
            f"L{x:.1f} {y:.1f}" for x, y in pts[1:])
        if close_on_limb:
            d += "Z"
        out.append(d)
    return " ".join(out)


def globe():
    lon0, lat0 = GLOBE_CENTRE
    size = R * 2
    L = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-12 -12 {size + 24:.0f} '
         f'{size + 24:.0f}" role="img" aria-label="Orthographic globe centred on '
         f'the Pacific, with the supply chain\'s nodes marked">',
         "<!-- generated by scripts/build_geography.py; edit the coordinates there -->",
         f'<circle class="geo-halo" cx="{R}" cy="{R}" r="{R + 9:.0f}"/>',
         f'<circle class="geo-sphere" cx="{R}" cy="{R}" r="{R:.0f}"/>']

    grat = []
    lon: float
    lat: float
    for lon in range(-180, 180, 30):
        grat.append(_path(_visible_runs(
            _densify([(lon, la) for la in range(-90, 91, 5)]), lon0, lat0, False), False))
    for lat in range(-60, 61, 30):
        grat.append(_path(_visible_runs(
            _densify([(lo, lat) for lo in range(-180, 181, 5)]), lon0, lat0, False), False))
    L.append(f'<path class="geo-graticule" d="{" ".join(g for g in grat if g)}"/>')

    for name, ring in LAND.items():
        if name in GLOBE_SKIP:
            continue
        d = _path(_visible_runs(_densify(_outer(ring)), lon0, lat0), True)
        if d:
            L.append(f'<path class="geo-land" id="geo-{name}" d="{d}"/>')

    place = {n: (lo, la) for n, lo, la, _ in MARKERS}
    for a, b in ROUTES:
        d = _path(_visible_runs(_great_circle(place[a], place[b]), lon0, lat0), False)
        if d:
            L.append(f'<path class="geo-route" data-route="{a} to {b}" d="{d}"/>')

    for name, lon, lat, state in MARKERS:
        if state != "live":
            continue
        p = _ortho(lon, lat, lon0, lat0)
        if p is None:
            continue
        L.append(f'<circle class="geo-mark geo-live" data-place="{name}" '
                 f'cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3.4"/>')
    L.append("</svg>")
    return "\n".join(L) + "\n"


# ── equirectangular ───────────────────────────────────────────────────────────
W, H = 720.0, 360.0


def _flat(lon, lat):
    return ((lon + 180) * W / 360, (90 - lat) * H / 180)


def world_flat():
    L = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
         f'role="img" aria-label="World map with each trade region marked by its '
         f'coverage state">',
         "<!-- generated by scripts/build_geography.py; edit the coordinates there -->"]
    for name, ring in LAND.items():
        pts = [_flat(lo, la) for lo, la in _densify(ring)]
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}" + "".join(
            f"L{x:.1f} {y:.1f}" for x, y in pts[1:]) + "Z"
        L.append(f'<path class="geo-land" id="geo-{name}" d="{d}"/>')
    for name, lon, lat, state in MARKERS:
        x, y = _flat(lon, lat)
        slug = name.lower().replace(" ", "-")
        L.append(f'<g class="geo-mark geo-{state}" id="mark-{slug}" data-place="{name}">'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5"/></g>')
    L.append("</svg>")
    return "\n".join(L) + "\n"


TARGETS = {"globe-orthographic.svg": globe, "world-flat.svg": world_flat}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="verify the committed files match a fresh render")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    failed = False
    for name, fn in TARGETS.items():
        path, want = OUT / name, fn()
        if args.check:
            have = path.read_text(encoding="utf-8") if path.exists() else None
            if have != want:
                print(f"FAIL  {name} is stale or missing; re-run without --check")
                failed = True
            else:
                print(f"ok    {name}  ({len(want):,} bytes)")
        else:
            path.write_text(want, encoding="utf-8")
            print(f"wrote {name}  ({len(want):,} bytes)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
