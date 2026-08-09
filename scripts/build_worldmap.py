#!/usr/bin/env python3
"""Build the shared-arc world topology from the vendored Natural Earth set.

Per-country simplification is the wrong algorithm for this figure. A border
simplified twice becomes two different lines, and at 0.35 degrees on a 1280px
world map that is a one-to-two-pixel sliver — exactly where form 2 of the globe
needs two countries of one region to merge seamlessly. So borders are extracted
as arcs, each simplified once, and referenced by both neighbours.

Adjacency falls out of the same structure: two countries are adjacent exactly
when they share an arc. That matters because the region palette is assigned by
four-colouring the adjacency graph, and a hand-maintained adjacency list beside
real geometry is correct on the day it is written and silently wrong after any
change to the registry.

    python3 scripts/build_worldmap.py           # write the topology and the fixture
    python3 scripts/build_worldmap.py --check   # verify both are current

Standard library only. Never touches the network; the upstream file is vendored
and NOTICE records why.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict

import geo_projection as gp

ROOT = pathlib.Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "assets" / "vectors" / "upstream" / "ne_110m_admin_0_countries.geojson"
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
GOLDEN = ROOT / "fixtures" / "globe-golden.json"

# A CEILING on simplification error. Coarser than this and the set starts losing
# countries: 0.6 drops thirteen, including Qatar and Cyprus, which a trade map
# cannot lose.
TOLERANCE = 0.35
# Coordinates are stored as integers, degrees * QUANTUM. Quantising BEFORE arcs
# are cut is what makes a shared border compare equal from both sides.
#
# 100 gives 0.01 degrees, about 1.1 km, which is 0.035 px on a 1280 px world map
# and 35 times finer than the 0.35 degree simplification tolerance. 10000 was the
# first value tried and cost 30 KB for resolution nothing can render: every
# coordinate became a seven-digit integer. Coarser quantisation also helps the
# arc cut, because more points snap together and compare equal.
QUANTUM = 100

# (lon0, lat0, t, R, cx, cy). cx and cy are deliberately not equal to R in two of
# these: the JS port takes them as separate parameters, and a fixture that only
# ever exercises cx == cy == R cannot catch a port that dropped them.
GOLDEN_VIEWS = [
    (0.0, 0.0, 0.0, 150.0, 150.0, 150.0),
    (-170.0, 20.0, 0.0, 150.0, 200.0, 180.0),
    (45.0, -10.0, 0.5, 150.0, 150.0, 150.0),
    (0.0, 0.0, 1.0, 120.0, 300.0, 90.0),
]


def _quantise(lon, lat):
    return (round(lon * QUANTUM), round(lat * QUANTUM))


def _rdp(pts, eps_q):
    """Douglas-Peucker on quantised integer coordinates.

    Iterative rather than recursive: a 177-country set goes deep enough that the
    recursive form is a stack risk for no benefit. First and last points are
    always kept, which is what preserves the junctions an arc runs between.
    """
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        den = dx * dx + dy * dy
        worst, wi = -1.0, i
        for k in range(i + 1, j):
            x, y = pts[k]
            if den == 0:
                d = (x - x1) ** 2 + (y - y1) ** 2
            else:
                t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / den))
                d = (x - (x1 + t * dx)) ** 2 + (y - (y1 + t * dy)) ** 2
            if d > worst:
                worst, wi = d, k
        if worst > (eps_q * eps_q):
            keep[wi] = True
            stack.append((i, wi))
            stack.append((wi, j))
    return [p for p, k in zip(pts, keep) if k]


def _cut_into_arcs(rings):
    """rings: list of (owner, [quantised points]) -> (arcs, refs).

    A point is a junction when the set of rings it belongs to DIFFERS from that
    of the point before or after it. The naive rule — "shared by more than one
    ring" — is wrong: every interior point of a shared border is shared by two
    rings, so it would cut a single border into one arc per point and produce a
    file larger than the GeoJSON it replaces. What ends an arc is the place
    where the sharing CHANGES: a third country arriving, or the coast beginning.

    Because both neighbours cut at the same junctions, the segment between two
    junctions is identical from both sides and is stored once. `~i` in a ref
    means arc i traversed backwards.
    """
    owners = defaultdict(set)
    for owner, pts in rings:
        for p in pts:
            owners[p].add(owner)
    arcs, index, refs = [], {}, []
    for owner, pts in rings:
        cuts = {0, len(pts) - 1}
        for i in range(1, len(pts) - 1):
            if owners[pts[i]] != owners[pts[i - 1]] or owners[pts[i]] != owners[pts[i + 1]]:
                cuts.add(i)
        ordered = sorted(cuts)
        ref = []
        for a, b in zip(ordered, ordered[1:]):
            seg = pts[a:b + 1]
            key, rkey = tuple(seg), tuple(reversed(seg))
            if key in index:
                ref.append(index[key])
            elif rkey in index:
                ref.append(~index[rkey])
            else:
                index[key] = len(arcs)
                arcs.append(seg)
                ref.append(index[key])
        refs.append((owner, ref))
    return arcs, refs


def _delta(arc):
    """Flat [x, y, dx, dy, ...]: first point absolute, the rest as deltas.

    Flat rather than a list of pairs. A nested pair costs two brackets and a
    comma per point, which over five thousand points is 10 KB of punctuation for
    a structure the decoder reconstructs anyway.
    """
    out = [arc[0][0], arc[0][1]]
    for (x0, y0), (x1, y1) in zip(arc, arc[1:]):
        out.append(x1 - x0)
        out.append(y1 - y0)
    return out


def build():
    raw = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    rings, meta = [], {}
    for feat in raw["features"]:
        props = feat["properties"]
        code = props["ADM0_A3"]
        meta[code] = {"a": code, "n": props["NAME"],
                      "z": props.get("NAME_ZH") or props["NAME"]}
        geom = feat["geometry"]
        polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        for poly in polys:
            for ring in poly:
                q = [_quantise(lon, lat) for lon, lat in ring]
                dedup = [q[0]] + [b for a, b in zip(q, q[1:]) if a != b]
                if len(dedup) >= 4:
                    rings.append((code, dedup))

    arcs, refs = _cut_into_arcs(rings)
    eps_q = TOLERANCE * QUANTUM
    arcs = [_rdp(a, eps_q) if len(a) > 2 else a for a in arcs]

    countries, owners_of_arc = {}, defaultdict(set)
    for code, ref in refs:
        countries.setdefault(code, {**meta[code], "rings": []})["rings"].append(ref)
        for i in ref:
            owners_of_arc[i if i >= 0 else ~i].add(code)
    neighbours = defaultdict(set)
    for owners in owners_of_arc.values():
        for a in owners:
            neighbours[a] |= (owners - {a})

    return {"schema": 1, "quantum": QUANTUM, "tolerance_deg": TOLERANCE,
            "arcs": [_delta(a) for a in arcs],
            "countries": [countries[c] for c in sorted(countries)],
            "neighbours": {c: sorted(neighbours[c]) for c in sorted(neighbours)}}


def build_golden():
    """A fixed grid of projection results, computed by the Python authority.

    assets/globe/projection.js is a hand port of geo_projection.py and nothing
    here can compile JavaScript, so the port is held to this instead. The grid is
    fixed and never sampled randomly: a fixture that changes between runs cannot
    tell a port regression from noise.
    """
    samples = []
    for vi, (lon0, lat0, t, R, cx, cy) in enumerate(GOLDEN_VIEWS):
        for lon in range(-180, 181, 15):
            for lat in range(-90, 91, 15):
                x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
                samples.append([vi, lon, lat, round(x, 9), round(y, 9), bool(vis)])
    return {"schema": 1,
            "views": [{"lon0": a, "lat0": b, "t": c, "R": d, "cx": e, "cy": f}
                      for a, b, c, d, e, f in GOLDEN_VIEWS],
            "samples": samples}


TARGETS = ((TOPOLOGY, build), (GOLDEN, build_golden))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    stale = []
    for path, builder in TARGETS:
        content = json.dumps(builder(), separators=(",", ":"), ensure_ascii=False)
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
            print("ok    world topology and golden grid are current")
        return 1 if stale else 0
    for path, _ in TARGETS:
        print(f"wrote {path.relative_to(ROOT)}  ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
