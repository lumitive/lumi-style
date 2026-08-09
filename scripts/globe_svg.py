#!/usr/bin/env python3
"""Emit one static SVG frame of the LUMI globe.

This is the deliverable's renderer. A canvas is invisible to every gate this
package owns — d5_drawn_share counts a figure as drawn only if it holds an
<svg>, d5_figure_parity and d17_export_weight read markup, and inspect_layout
cannot see inside a canvas — so what ships in a document is SVG, and the
JavaScript runtime mutates this markup rather than replacing it.

    python3 scripts/globe_svg.py                       # the globe, form 1
    python3 scripts/globe_svg.py --t 1 --form regions  # the flat region map
    python3 scripts/globe_svg.py --lon0 -170 --lat0 20 --r 150

No literal colour appears here. Every shape carries a class and the host
document paints it from tokens, per design-rules.md section 1 — the same rule
build_geography.py states, for the same reason.

The viewBox is computed from the projected extent at the requested t, never a
fixed square. inspect_layout --deliverable gates on a drawing clipped by its own
viewBox, and the globe's limb sits exactly on that edge; that defect is how the
gate came to exist.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import geo_projection as gp   # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
REGIONS = ROOT / "assets" / "vectors" / "regions.json"

STEP_DEG = 2.0        # densification before projection, coarser than the mark's
                      # 1.5 because 110m geometry already carries its own detail
GRATICULE = 30        # degrees between graticule lines
PAD = 40.0            # viewBox padding in user units, over the widest stroke

# The SVG's user-unit space, chosen so INTEGER coordinates are still sub-pixel.
# A world at country resolution is about 7,000 path commands whatever else is
# done, and at R=150 with one decimal that is 55 KB for the globe and 86 for the
# flat map. Integers at R=1000 cut both by a third — 44 and 66 — because every
# number loses a point and a digit. The precision is not lost: the flat viewBox
# spans about 2,000 units, so a figure drawn 480px wide in a 1280x720 stage
# resolves one unit as 0.24px, and 0.64px even at full stage width.
DEFAULT_R = 1000.0


def _load():
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    reg = json.loads(REGIONS.read_text(encoding="utf-8"))
    q = topo["quantum"]
    arcs = []
    for flat in topo["arcs"]:
        n = len(flat) // 2
        x, y = flat[0], flat[1]
        pts = [(x / q, y / q)]
        for i in range(1, n):
            x += flat[i * 2]
            y += flat[i * 2 + 1]
            pts.append((x / q, y / q))
        arcs.append(pts)
    return topo, reg, arcs


def _rings_of(country, arcs):
    out = []
    for refs in country["rings"]:
        ring = []
        for idx in refs:
            arc = arcs[idx if idx >= 0 else ~idx]
            seq = arc if idx >= 0 else arc[::-1]
            ring.extend(seq[1:] if ring else seq)
        if len(ring) > 3:
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            out.append(ring)
    return out


def _project_ring(ring, view):
    """-> list of screen-space runs. Splits at the seam and drops hidden points.

    Two separate cuts, and both are needed. The seam cut keeps a ring that
    crosses the moving antimeridian from drawing a streak across the map as t
    rises. The visibility cut is the limb.
    """
    lon0, lat0, t, R, cx, cy = view
    runs = []
    for part in gp.split_at_seam(ring, lon0):
        dense = gp.densify(part, STEP_DEG) if len(part) > 1 else part
        cur = []
        for lon, lat in dense:
            x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
            if vis:
                cur.append((x, y))
            elif len(cur) > 1:
                runs.append(cur)
                cur = []
            else:
                cur = []
        if len(cur) > 1:
            runs.append(cur)
    return runs


def _d(runs, close):
    out = []
    for pts in runs:
        out.append(f"M{pts[0][0]:.0f} {pts[0][1]:.0f}"
                   + "".join(f"L{x:.0f} {y:.0f}" for x, y in pts[1:])
                   + ("Z" if close else ""))
    return " ".join(out)


def extent(view):
    """The bounding box of everything the frame can draw, before padding.

    Sampled on a fine grid rather than derived analytically, because the
    interpolated projection has no closed-form extent and an analytic guess is
    exactly the kind of thing that clips a limb by half a pixel.
    """
    lon0, lat0, t, R, cx, cy = view
    xs, ys = [], []
    for i in range(-180, 181, 2):
        for j in range(-90, 91, 2):
            x, y, vis = gp.unrolled(i, j, lon0, lat0, t, R, cx, cy)
            if vis:
                xs.append(x)
                ys.append(y)
    if t < 1.0:
        # The limb itself, which no lat/lon sample lands exactly on.
        for k in range(721):
            a = 2 * math.pi * k / 720
            xs.append(cx + R * math.cos(a))
            ys.append(cy + R * math.sin(a))
    return min(xs), min(ys), max(xs), max(ys)


def render(view, form="field", marks=None, states=None):
    """-> the <svg> element as a string.

    `form` is field, regions, or both. Both emits the two layers together, which
    is what a document needs if it will switch between them at runtime.

    `states` maps region id -> live | partial | zero | out. A region absent from
    it renders as zero, which is the honest default: no data is not coverage.
    """
    topo, reg, arcs = _load()
    lon0, lat0, t, R, cx, cy = view
    states = states or {}
    region_of = {c: r["id"] for r in reg["regions"] for c in r["members"]}

    body = []
    # the ground the sphere sits on
    if t < 1.0:
        body.append(f'<circle class="gl-plate" cx="{cx:.0f}" cy="{cy:.0f}" '
                    f'r="{R:.0f}" opacity="{1 - t:.3f}"/>')

    grat = []
    for lon in range(-180, 181, GRATICULE):
        grat.append(_d(_project_ring([(lon, la) for la in range(-90, 91, 3)], view), False))
    for lat in range(-90, 91, GRATICULE):
        grat.append(_d(_project_ring([(lo, lat) for lo in range(-180, 181, 3)], view), False))
    grat = " ".join(g for g in grat if g)
    if grat:
        body.append(f'<path class="gl-graticule" d="{grat}"/>')

    # A document that offers both forms needs BOTH layers in the file: the
    # runtime mutates markup and never creates it, so a region path that is not
    # here has nowhere to be drawn. Discovered by switching form on a frame
    # generated as "field" and getting a correctly unrolled, entirely empty map.
    if form in ("regions", "both"):
        for region in reg["regions"]:
            state = states.get(region["id"], "zero")
            d = []
            for code in region["members"]:
                country = next((c for c in topo["countries"] if c["a"] == code), None)
                if country:
                    for ring in _rings_of(country, arcs):
                        d.append(_d(_project_ring(ring, view), True))
            # Emitted even when nothing of it is visible in THIS frame, with an
            # empty d. The runtime mutates markup and never creates it, so a
            # region skipped here can never be drawn when it rotates into view —
            # the same trap the mark layer fell into one commit earlier.
            d = " ".join(x for x in d if x)
            body.append(f'<path class="rg rg-{region["id"]} is-{state}" '
                        f'data-region="{region["id"]}" role="img" '
                        f'aria-label="{region["n"]}, {state}" d="{d}"/>')
    if form in ("field", "both"):
        d = []
        for country in topo["countries"]:
            for ring in _rings_of(country, arcs):
                d.append(_d(_project_ring(ring, view), True))
        d = " ".join(x for x in d if x)
        body.append(f'<path class="gl-land" d="{d}"/>')

    # Every mark and node is in the DOM whether or not this frame shows it, with
    # its lat/lon on the element and visibility as an attribute. The runtime
    # mutates markup and never creates it, so a mark that rotates into view has
    # to already have somewhere to land; and a reader with JavaScript off still
    # gets exactly the frame that was generated, because `hidden` is honoured.
    for i, mark in enumerate(marks or []):
        px, py, vis = gp.unrolled(mark["lon"], mark["lat"], lon0, lat0, t, R, cx, cy)
        w = mark.get("weight", 1.0)
        body.append(f'<circle class="gl-mark" data-lon="{mark["lon"]:g}" '
                    f'data-lat="{mark["lat"]:g}" data-w="{w:g}" '
                    f'cx="{px:.0f}" cy="{py:.0f}" '
                    f'r="{R * (0.009 + 0.015 * w):.1f}"'
                    f'{"" if vis else " hidden"}/>')

    for node in reg.get("nodes", []):
        px, py, vis = gp.unrolled(node["lon"], node["lat"], lon0, lat0, t, R, cx, cy)
        body.append(f'<circle class="gl-node" data-node="{node["id"]}" '
                    f'data-lon="{node["lon"]:g}" data-lat="{node["lat"]:g}" '
                    f'cx="{px:.0f}" cy="{py:.0f}" r="{R * 0.017:.1f}"'
                    f'{"" if vis else " hidden"}>'
                    f'<title>{node["n"]}</title></circle>')

    x0, y0, x1, y1 = extent(view)
    pad = PAD * (R / DEFAULT_R)
    vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    label = {"regions": "LUMI globe, trade regions",
             "field": "LUMI globe, coverage field",
             "both": "LUMI globe, coverage field and trade regions"}[form]
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" class="gl" '
            f'viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="{label}" data-t="{t:g}" '
            f'data-lon0="{lon0:g}" data-lat0="{lat0:g}" data-r="{R:g}" '
            f'data-cx="{cx:g}" data-cy="{cy:g}">')
    note = ("<!-- generated by scripts/globe_svg.py; the runtime in "
            "assets/globe/ mutates these paths and never replaces them -->")
    return "\n".join([head, note, *body, "</svg>"])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lon0", type=float, default=0.0)
    ap.add_argument("--lat0", type=float, default=0.0)
    ap.add_argument("--t", type=float, default=0.0)
    ap.add_argument("--r", type=float, default=DEFAULT_R)
    ap.add_argument("--form", choices=("field", "regions", "both"),
                    default="field",
                    help="both emits the land layer and the region layer; the "
                         "host stylesheet shows one at a time and the runtime "
                         "can switch between them")
    args = ap.parse_args(argv)
    view = (args.lon0, args.lat0, args.t, args.r, args.r, args.r)
    print(render(view, form=args.form))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
