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


def _limb_point(a, b, view):
    """Bisect to where the edge a->b crosses the visibility boundary.

    build_geography.py has done this since it was written, and its comment says
    why: "a run ends up to one sample short of the limb, and an arc drawn from
    an interior point is not the horizon". This generator was cutting between
    samples instead, so a run could end 35 units inside the boundary at a two
    degree step — past the tolerance the limb walk matches on, so the walk was
    refused and the subpath closed with a chord. Those chords are the bands
    across the globe in the first live deliverable. The same failure, twice.
    """
    lon0, lat0, t, R, cx, cy = view
    inside, outside = a, b
    for _ in range(30):
        mid = ((inside[0] + outside[0]) / 2, (inside[1] + outside[1]) / 2)
        if gp.unrolled(mid[0], mid[1], lon0, lat0, t, R, cx, cy)[2]:
            inside = mid
        else:
            outside = mid
    x, y, _v = gp.unrolled(inside[0], inside[1], lon0, lat0, t, R, cx, cy)
    return (x, y)


def _project_ring(ring, view):
    """-> list of screen-space runs. Splits at the seam, clips at the boundary.

    Two separate cuts, and both are needed. The seam cut keeps a ring that
    crosses the moving antimeridian from drawing a streak across the map as t
    rises. The visibility cut is the limb, and it lands EXACTLY on it.
    """
    lon0, lat0, t, R, cx, cy = view
    runs = []
    for part in gp.split_at_seam(ring, lon0):
        dense = gp.densify(part, STEP_DEG) if len(part) > 1 else part
        cur, prev = [], None
        for lon, lat in dense:
            x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
            if vis:
                if prev is not None and not prev[1]:
                    cur.append(_limb_point((lon, lat), prev[0], view))
                cur.append((x, y))
            else:
                if prev is not None and prev[1]:
                    cur.append(_limb_point(prev[0], (lon, lat), view))
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            prev = ((lon, lat), vis)
        if len(cur) > 1:
            runs.append(cur)
    return runs


BOUNDARY_SAMPLES = 240


def _boundary(view):
    """The visibility boundary in screen space, as a closed polyline.

    A ring cut by the horizon has to be closed along the horizon, not with a
    chord between its two ends. build_geography.py has always walked the limb
    for this; the static globe generator did not, and Antarctica at t=0 closed
    across the bottom of the sphere. The boundary is where cos_c = -t: the
    horizon at t=0, and gone by t=1.
    """
    lon0, lat0, t, R, cx, cy = view
    if t >= 1.0:
        return None
    c = math.acos(max(-1.0, min(1.0, -t)))
    p0 = math.radians(lat0)
    out = []
    for i in range(BOUNDARY_SAMPLES):
        az = 2 * math.pi * i / BOUNDARY_SAMPLES
        lat = math.asin(math.sin(p0) * math.cos(c)
                        + math.cos(p0) * math.sin(c) * math.cos(az))
        lon = lon0 + math.degrees(math.atan2(
            math.sin(az) * math.sin(c) * math.cos(p0),
            math.cos(c) - math.sin(p0) * math.sin(lat)))
        x, y, _ = gp.unrolled(lon, math.degrees(lat), lon0, lat0, t, R, cx, cy)
        out.append((x, y))
    return out


def _nearest(pt, boundary):
    best, bd = 0, float("inf")
    for i, b in enumerate(boundary):
        d = (b[0] - pt[0]) ** 2 + (b[1] - pt[1]) ** 2
        if d < bd:
            bd, best = d, i
    return best, bd


def _boundary_walk(a, b, boundary, R):
    """The shorter way round the boundary FROM a TO b, or nothing if either end
    is not on it.

    Direction matters and getting it backwards is not subtle in the output: the
    first inserted point then sits beside b rather than beside a, so the segment
    out of a crosses the whole figure — which is what it did, on both the globe
    and the flat map, until this was read again.
    """
    ia, da = _nearest(a, boundary)
    ib, db = _nearest(b, boundary)
    tol = (R * 0.03) ** 2
    if da > tol or db > tol:
        return []
    n = len(boundary)
    fwd = (ib - ia + n) % n
    if fwd <= n - fwd:
        return [boundary[(ia + k) % n] for k in range(1, fwd + 1)]
    return [boundary[(ia - k + n) % n] for k in range(1, n - fwd + 1)]


def _pole_close(a, b, view):
    """Close a piece whose two ends sit on OPPOSITE edges of the FLAT map.

    Only a ring that wraps the world does this — Antarctica crosses the seam
    once, so it comes back as a piece running edge to edge — and the way a map
    draws it is along the pole edge, not straight across.

    t=1 only. At t<1 the figure is bounded by the horizon, not by a rectangle,
    and this fired there too: it drew a line across the bottom of the sphere and
    closed a box back to the equator, which is the frame visible under the globe
    in the first 0.1.387 demo.
    """
    lon0, lat0, t, R, cx, cy = view
    if t < 1.0:
        return []
    left, right, eps = cx - R, cx + R, R * 0.02
    on = lambda p, e: abs(p[0] - e) < eps          # noqa: E731
    if not ((on(a, left) or on(a, right)) and (on(b, left) or on(b, right))):
        return []
    if (on(a, left) and on(b, left)) or (on(a, right) and on(b, right)):
        return []
    half = R * (1 - t / 2)
    edge_y = cy + half if (a[1] + b[1]) / 2 > cy else cy - half
    return [(a[0], edge_y), (b[0], edge_y)]


def _r(v):
    """Round half away from zero, the same rule the JS renderer uses.

    Python's format spec rounds half to EVEN and JavaScript's toFixed rounds
    half away from zero, so 1040.5 became 1040 in the static frame and 1041 in
    the animated one. One pixel, in a figure nobody would compare by hand — and
    the two renderers have to be the same renderer or the whole two-back-end
    design is a claim rather than a fact. Found by the parity check; invisible to
    everything else.
    """
    return int(math.floor(abs(v) + 0.5)) * (1 if v >= 0 else -1)


def _guard(runs, R):
    """Split any run wherever consecutive points are more than R apart.

    An invariant, not a patch over one bug: in this projection no real polygon
    edge spans half the figure. A pair that does means a cut that did not take,
    and drawing it is always wrong whatever the cause. Three causes were found
    and fixed by hand in 0.1.387; this is what stops the fourth from reaching a
    reader while it is being found.
    """
    out = []
    for run in runs:
        cur = [run[0]]
        for prev, pt in zip(run, run[1:]):
            if math.hypot(pt[0] - prev[0], pt[1] - prev[1]) > R:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
            cur.append(pt)
        if len(cur) > 1:
            out.append(cur)
    return out


def _d(runs, close, view=None, boundary=None):
    closed = []
    for pts in runs:
        seq = list(pts)
        # Runs of fewer than three points are left alone. Closing one along the
        # boundary produces a degenerate sliver, and the JS renderer already
        # skipped them — a divergence the parity check found and neither
        # renderer's own output would have shown.
        if close and view is not None and len(seq) > 2:
            if boundary:
                seq += _boundary_walk(seq[-1], seq[0], boundary, view[3])
            seq += _pole_close(seq[-1], seq[0], view)
        closed.append(seq)
    # The guard runs LAST, after every closure, because a closure can introduce
    # the very thing it guards against — and running it first left one stray
    # segment in the mid-unroll frames for exactly that reason.
    out = []
    for seq in (_guard(closed, view[3]) if view else closed):
        out.append(f"M{_r(seq[0][0])} {_r(seq[0][1])}"
                   + "".join(f"L{_r(x)} {_r(y)}" for x, y in seq[1:])
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

    boundary = _boundary(view)
    body = []
    # the ground the sphere sits on
    if t < 1.0:
        body.append(f'<circle class="gl-plate" cx="{_r(cx)}" cy="{_r(cy)}" '
                    f'r="{_r(R)}" opacity="{1 - t:.3f}"/>')

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
                        d.append(_d(_project_ring(ring, view), True, view, boundary))
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
                d.append(_d(_project_ring(ring, view), True, view, boundary))
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
                    f'cx="{_r(px)}" cy="{_r(py)}" '
                    f'r="{R * (0.009 + 0.015 * w):.1f}"'
                    f'{"" if vis else " hidden"}/>')

    for node in reg.get("nodes", []):
        px, py, vis = gp.unrolled(node["lon"], node["lat"], lon0, lat0, t, R, cx, cy)
        body.append(f'<circle class="gl-node" data-node="{node["id"]}" '
                    f'data-lon="{node["lon"]:g}" data-lat="{node["lat"]:g}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{R * 0.017:.1f}"'
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
    ap.add_argument("--states", metavar="JSON", default=None,
                    help='region states, e.g. \'{"europe":"live"}\'. Without '
                         "this every region renders as zero, which is the honest "
                         "default and is also why a coverage map generated "
                         "without it says nothing.")
    ap.add_argument("--form", choices=("field", "regions", "both"),
                    default="field",
                    help="both emits the land layer and the region layer; the "
                         "host stylesheet shows one at a time and the runtime "
                         "can switch between them")
    args = ap.parse_args(argv)
    view = (args.lon0, args.lat0, args.t, args.r, args.r, args.r)
    states = json.loads(args.states) if args.states else None
    print(render(view, form=args.form, states=states))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
