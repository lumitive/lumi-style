#!/usr/bin/env python3
"""Route between two places over water, using the shipped 110m topology.

    python3 scripts/render/sea_route.py 121.47 31.23 4.48 51.92     # Shanghai -> Rotterdam
    python3 scripts/render/sea_route.py --check                     # the self-test

WHY THIS EXISTS. A trade lane drawn as a great circle goes through the planet's
surface — the Shanghai-to-Rotterdam arc crosses Siberia, and the one to Los
Angeles crosses Mexico. The first fix named the canals and straits as waypoints,
which is what an atlas does, and it was not enough: the legs BETWEEN the named
gaps still ran straight across Spain, France, Australia and South Africa.
Measured against this topology, 586 of 1,494 samples on twelve of thirteen lanes
were inside a country polygon.

The second fix was more waypoints, and it went from 39% of samples on land to
14% and stopped converging. Hand-placed waypoints are whack-a-mole: every point
you add fixes one leg and the two new legs it creates each clip something else.

So this routes over water BY CONSTRUCTION. It rasterizes the land polygons into
a quarter-degree mask, carves the canals and the straits narrower than a cell,
and runs Dijkstra over the water cells.
A route it returns cannot cross land, because a path through a land cell does
not exist in the graph — which is a different kind of guarantee than a route
that has been checked and found clean.

THE CANALS ARE CARVED BY HAND, and that is the honest part rather than the
cheat. Suez is about 200 metres wide and Panama's cut is narrower still; no
raster of a coastline at any resolution contains them, because they are not
coastline. A ship goes through them because people dug them. So they are named,
with their coordinates, below — Panama, Suez and Malacca among them.

Standard library only. The mask builds in about eight seconds and is cached
under the caller's own directory, never in this repository.
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
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

from geo_frame import _load, _rings_of  # noqa: E402 — after the bootstrap, deliberately

RES = 4                                  # cells per degree: a quarter-degree grid
NX, NY = 360 * RES, 180 * RES

# THE CANALS. Each is (name, lon0, lat0, lon1, lat1) — a segment of cells forced
# to water. A canal is not a coastline feature and no rasterization finds one;
# it is in the mask because somebody dug it, and saying so is the point.
CANALS = [
    ("Suez", 32.35, 29.90, 32.30, 31.30),
    ("Panama", -79.92, 8.95, -79.55, 9.40),
    ("Kiel", 9.15, 54.37, 9.95, 54.37),
]

# STRAITS TOO NARROW FOR THE GRID. These are real, natural water and a ship
# needs no permission to use them; they are listed for a different reason than
# the canals. A quarter-degree cell is about 28km at the equator, and Gibraltar
# is 14km across, Hormuz 39, Bab-el-Mandeb 29, Dover 33. Rasterizing a coastline
# at any resolution closes some strait narrower than the cell, so the mask says
# there is no way from the Gulf to the Indian Ocean — which is how the first run
# of this router returned NO ROUTE for Dubai to Durban.
#
# Raising the resolution moves the line without removing it: at 1/8 degree
# Gibraltar opens and the Bosphorus (700m) still does not. So the straits a
# route needs are named, the way the canals are, and the distinction between
# the two lists is the honest part — a canal is open because someone dug it,
# a strait here is open because the raster is coarser than the water.
NARROWS = [
    ("Gibraltar", -5.90, 35.95, -5.30, 35.90),
    ("Hormuz", 56.20, 26.60, 56.80, 26.30),
    ("Bab-el-Mandeb", 43.20, 12.80, 43.60, 12.40),
    ("Dover", 1.20, 51.00, 1.70, 51.10),
    ("Bosphorus", 28.95, 41.20, 29.15, 41.00),
    ("Dardanelles", 26.20, 40.20, 26.70, 40.00),
    ("Singapore Strait", 103.50, 1.20, 104.20, 1.20),
    ("Tsugaru", 140.30, 41.60, 141.20, 41.50),
    ("Torres", 141.80, -10.60, 142.60, -10.40),
]

# Water a route must not take even though it is water: the Northwest and
# Northeast Passages are open for a few weeks a year and a trade lane drawn
# through them states something false about shipping. Everything above this
# parallel is closed to the router.
ICE_LAT = 66.0


def _mask_path(cache_dir):
    return pathlib.Path(cache_dir) / f"sea-mask-{RES}.json"


def build_mask():
    """-> a bytearray of NX*NY, 1 where a ship can be.

    Scanline rasterization, one row of cells per ring rather than a
    point-in-polygon test per cell: the grid holds 1,036,800 cells and the
    topology has some thirteen hundred rings, so the naive product is a billion
    polygon tests and this is under a million edge crossings.
    """
    topo, _reg, arcs = _load()
    land = bytearray(NX * NY)
    for c in topo["countries"]:
        for ring in _rings_of(c, arcs):
            if len(ring) < 3:
                continue
            ys = [p[1] for p in ring]
            j0 = max(0, int((min(ys) + 90) * RES))
            j1 = min(NY - 1, int((max(ys) + 90) * RES) + 1)
            for j in range(j0, j1 + 1):
                lat = (j + 0.5) / RES - 90
                xs = []
                n = len(ring)
                k = n - 1
                for i in range(n):
                    y_i, y_k = ring[i][1], ring[k][1]
                    if (y_i > lat) != (y_k > lat):
                        t = (lat - y_i) / (y_k - y_i)
                        xs.append(ring[i][0] + t * (ring[k][0] - ring[i][0]))
                    k = i
                xs.sort()
                for a, b in zip(xs[0::2], xs[1::2]):
                    ia = max(0, int((a + 180) * RES))
                    ib = min(NX - 1, int((b + 180) * RES) + 1)
                    for i in range(ia, ib + 1):
                        land[j * NX + i] = 1

    sea = bytearray(1 if not v else 0 for v in land)
    for _name, lon0, lat0, lon1, lat1 in CANALS + NARROWS:
        steps = int(max(abs(lon1 - lon0), abs(lat1 - lat0)) * RES * 4) + 1
        for s in range(steps + 1):
            t = s / steps
            lon = lon0 + t * (lon1 - lon0)
            lat = lat0 + t * (lat1 - lat0)
            i = int((lon + 180) * RES) % NX
            j = int((lat + 90) * RES)
            for dj in (-1, 0, 1):                # a canal a cell wide is a
                jj = j + dj                      # canal a router can thread
                if 0 <= jj < NY:
                    sea[jj * NX + i] = 1
    for j in range(int((ICE_LAT + 90) * RES), NY):
        for i in range(NX):
            sea[j * NX + i] = 0
    return sea


def coast_cost(sea):
    """-> per-cell extra cost, so a lane runs offshore rather than hugging.

    A shortest path over water hugs every coastline, because the coast is the
    short way round. That is geometrically correct and it draws a lane that
    looks like it is aground. Three cells of graded penalty buys open water at
    a cost the router will still pay to use a strait.
    """
    cost = bytearray(NX * NY)
    frontier = []
    for j in range(NY):
        for i in range(NX):
            if not sea[j * NX + i]:
                continue
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                jj, ii = j + dj, (i + di) % NX
                if 0 <= jj < NY and not sea[jj * NX + ii]:
                    cost[j * NX + i] = 3
                    frontier.append((j, i))
                    break
    for level in (2, 1):
        nxt = []
        for j, i in frontier:
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                jj, ii = j + dj, (i + di) % NX
                if 0 <= jj < NY and sea[jj * NX + ii] and not cost[jj * NX + ii]:
                    cost[jj * NX + ii] = level
                    nxt.append((jj, ii))
        frontier = nxt
    return cost


def _cell(lon, lat):
    return (min(NY - 1, max(0, int((lat + 90) * RES))),
            int((lon + 180) * RES) % NX)


def _lonlat(j, i):
    return ((i + 0.5) / RES - 180, (j + 0.5) / RES - 90)


def _snap(sea, lon, lat):
    """-> the nearest water cell to a port, which is itself on land.

    Every hub is a port and every port is on the land side of a coastline, so
    the endpoints are never in the graph. Spiralling out to the nearest water
    is what makes the lane end at a quay instead of failing to exist.
    """
    j0, i0 = _cell(lon, lat)
    for r in range(0, 12):
        best = None
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                if max(abs(dj), abs(di)) != r:
                    continue
                j, i = j0 + dj, (i0 + di) % NX
                if 0 <= j < NY and sea[j * NX + i]:
                    d = dj * dj + di * di
                    if best is None or d < best[0]:
                        best = (d, j, i)
        if best:
            return best[1], best[2]
    raise ValueError(f"no water within 6 degrees of {lon},{lat}")


def _great_circle(a, b, n):
    """The straight-line-on-a-sphere route, kept only so --check can prove the
    router is doing something: this is what a lane looked like before it."""
    def unit(lon, lat):
        p, q = math.radians(lon), math.radians(lat)
        return (math.cos(q) * math.cos(p), math.cos(q) * math.sin(p), math.sin(q))
    u, v = unit(*a), unit(*b)
    w = math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(u, v)))))
    out = []
    for k in range(n + 1):
        t = k / n
        s1, s2 = math.sin((1 - t) * w) / math.sin(w), math.sin(t * w) / math.sin(w)
        c = tuple(s1 * x + s2 * y for x, y in zip(u, v))
        m = math.sqrt(sum(z * z for z in c))
        c = tuple(z / m for z in c)
        out.append((math.degrees(math.atan2(c[1], c[0])),
                    math.degrees(math.asin(max(-1.0, min(1.0, c[2]))))))
    return out


def _hav(a, b):
    (x1, y1), (x2, y2) = a, b
    p1, p2 = math.radians(y1), math.radians(y2)
    dp, dl = p2 - p1, math.radians(x2 - x1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * math.asin(min(1.0, math.sqrt(h)))


def dijkstra(sea, cost, start, goal):
    """-> the cell path from start to goal, both as (j, i)."""
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    seen = set()
    while pq:
        d, cur = heapq.heappop(pq)
        if cur in seen:
            continue
        seen.add(cur)
        if cur == goal:
            break
        j, i = cur
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                if not dj and not di:
                    continue
                jj, ii = j + dj, (i + di) % NX
                if not (0 <= jj < NY) or not sea[jj * NX + ii]:
                    continue
                step = _hav(_lonlat(j, i), _lonlat(jj, ii))
                w = d + step * (1 + 0.9 * cost[jj * NX + ii])
                if w < dist.get((jj, ii), 1e18):
                    dist[(jj, ii)] = w
                    prev[(jj, ii)] = cur
                    heapq.heappush(pq, (w, (jj, ii)))
    if goal not in prev and goal != start:
        return None
    out = [goal]
    while out[-1] != start:
        out.append(prev[out[-1]])
    return out[::-1]


def _wet_chord(a, b, sea):
    """-> True if the straight line from a to b stays on water.

    THIS IS THE CONSTRAINT THAT MAKES SIMPLIFICATION SAFE. Plain
    Douglas-Peucker undoes the routing: it collapses the coastal detour into
    the chord that the detour existed to avoid, so every corner is on water and
    the line between two corners is through Holland. Measured that way, every
    lane ending at Rotterdam ran 22 samples up the Dutch coast, and every lane
    leaving Singapore ran 42 through Malaysia.
    """
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) * RES))
    return all(on_water(sea, a[0] + (b[0] - a[0]) * k / n,
                        a[1] + (b[1] - a[1]) * k / n)
               for k in range(n + 1))


def _simplify(pts, sea, tol_deg=0.6):
    """Douglas-Peucker on the cell path, so a lane is waypoints and not pixels.

    A raster path is a staircase and drawing it shows the grid. Simplifying to
    a tolerance below the cell size keeps the route and loses the steps — but
    only where the shortcut is itself over water, which is what `sea` decides.
    """
    if len(pts) < 3:
        return list(pts)
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-9
    worst, at = 0.0, 0
    for k in range(1, len(pts) - 1):
        p = pts[k]
        d = abs(dy * (p[0] - a[0]) - dx * (p[1] - a[1])) / n
        if d > worst:
            worst, at = d, k
    if worst <= tol_deg and _wet_chord(a, b, sea):
        return [a, b]
    if at == 0:                       # within tolerance but dry: split anyway
        at = len(pts) // 2
    return (_simplify(pts[:at + 1], sea, tol_deg)[:-1]
            + _simplify(pts[at:], sea, tol_deg))


def route(sea, cost, a, b, tol_deg=0.6):
    """-> [(lon, lat)] from port a to port b, over water the whole way.

    The two ends are the ports themselves; everything between them is a water
    cell. That is the contract, and `--check` is what holds it.
    """
    path = dijkstra(sea, cost, _snap(sea, *a), _snap(sea, *b))
    if path is None:
        return None
    pts = [_lonlat(j, i) for j, i in path]
    # UNWRAP THE WHOLE SEQUENCE, PORTS INCLUDED. A path across the antimeridian
    # steps from +179.75 to -179.75, and a straight line between those two runs
    # the wrong way round the planet.
    #
    # The first cut of this unwrapped `pts` and then appended the two ports at
    # their original longitudes, which is the same defect one level up: a route
    # ending at 363.88 followed by a port written 4.48 makes the final leg
    # measure 359 degrees, so it drew twenty-four samples inside half a degree
    # of Rotterdam quay. The arc was right and the sampling was nonsense, which
    # is the kind of wrong that passes a look and fails a count.
    out = [a] + _simplify(pts, sea, tol_deg) + [b]
    for k in range(1, len(out)):
        while out[k][0] - out[k - 1][0] > 180:
            out[k] = (out[k][0] - 360, out[k][1])
        while out[k][0] - out[k - 1][0] < -180:
            out[k] = (out[k][0] + 360, out[k][1])
    return out


def load_mask(cache_dir):
    p = _mask_path(cache_dir)
    if p.exists():
        d = json.loads(p.read_text())
        return bytearray(bytes.fromhex(d["sea"])), bytearray(bytes.fromhex(d["cost"]))
    sea = build_mask()
    cost = coast_cost(sea)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"res": RES, "sea": bytes(sea).hex(),
                             "cost": bytes(cost).hex()}))
    return sea, cost


def on_water(sea, lon, lat):
    j, i = _cell(((lon + 180) % 360) - 180, lat)
    return bool(sea[j * NX + i])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("coords", nargs="*", type=float,
                    help="lon0 lat0 lon1 lat1")
    ap.add_argument("--cache", default=".", help="where to keep the mask")
    ap.add_argument("--check", action="store_true",
                    help="assert the canals are open and four routes are wet")
    args = ap.parse_args(argv)

    sea, cost = load_mask(args.cache)
    water = sum(sea)
    print(f"mask {NX}x{NY} at 1/{RES} degree: {water} water cells "
          f"({100 * water / (NX * NY):.1f}%)")

    if args.check:
        bad = 0
        for kind, group in (("canal", CANALS), ("narrow", NARROWS)):
            for name, lon0, lat0, lon1, lat1 in group:
                ok = on_water(sea, (lon0 + lon1) / 2, (lat0 + lat1) / 2)
                print(f"  {kind} {name:17} {'open' if ok else 'CLOSED'}")
                bad += not ok
        # Four routes that each must use a canal or a strait, so a mask that
        # has quietly closed one fails here rather than in a deliverable.
        cases = [("Shanghai", (121.47, 31.23), "Rotterdam", (4.48, 51.92)),
                 ("Rotterdam", (4.48, 51.92), "Los Angeles", (-118.24, 33.74)),
                 ("Singapore", (103.82, 1.35), "Sydney", (151.21, -33.87)),
                 ("Dubai", (55.27, 25.27), "Durban", (31.02, -29.87))]
        for na, a, nb, b in cases:
            r = route(sea, cost, a, b)
            if r is None:
                print(f"  {na} -> {nb}: NO ROUTE")
                bad += 1
                continue
            dry = sum(not on_water(sea, lo, la) for lo, la in r[1:-1])
            # THE MUTATION HALF. A check that only ever passes has not been
            # shown to discriminate, and three checks in this repository were
            # written, run green, and later found incapable of failing. So the
            # naive great circle between the same two ports is measured too: it
            # is the thing this router exists to replace, and it MUST come back
            # dry. If it does not, the mask is wrong and the clean verdict on
            # the routed lane means nothing.
            naive = _great_circle(a, b, 200)
            naive_dry = sum(not on_water(sea, lo, la) for lo, la in naive[3:-3])
            ok = dry == 0 and naive_dry > 0
            print(f"  {na:10} -> {nb:12} {len(r):3d} waypoints, "
                  f"{dry} on land (great circle: {naive_dry}/194) "
                  f"{'ok' if ok else 'FAIL'}")
            bad += not ok
        return 1 if bad else 0

    if len(args.coords) != 4:
        ap.error("give lon0 lat0 lon1 lat1, or --check")
    r = route(sea, cost, tuple(args.coords[:2]), tuple(args.coords[2:]))
    print(json.dumps([[round(x, 3), round(y, 3)] for x, y in r]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
