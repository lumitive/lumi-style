#!/usr/bin/env python3
"""Sphere-to-screen maths, shared by the static generator and the runtime port.

Extracted from build_geography.py, where it lived as module-private functions
against a module constant R = 150.0 and an implicit centre at (R, R). Three more
callers need it parameterised: build_worldmap.py, globe_svg.py, and
assets/globe/projection.js, which is a hand port of exactly these functions and
is held to them by a golden grid in scripts/check_globe.py.

The extraction was byte-output-preserving and build_geography.py --check is the
proof of that: it runs in CI, and a single changed character in either emitted
SVG means the move was not faithful.

Nothing here does I/O and nothing here knows about colour. Standard library only.
"""
from __future__ import annotations

import math


def densify(ring, step_deg):
    """Insert intermediate points so an edge does not project as a straight line.

    A polygon edge is a great-circle segment on the sphere; sampling it before
    projection is what makes the projected edge curve.
    """
    out = []
    for i in range(len(ring) - 1):
        (x0, y0), (x1, y1) = ring[i], ring[i + 1]
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step_deg))
        for k in range(n):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    out.append(ring[-1])
    return out


def great_circle(a, b, n=96):
    """Sample the shortest path over the sphere between two (lon, lat) points.
    A straight line in projected space would cut through the planet; the route a
    shipment actually takes is the great circle."""
    def vec(p):
        lo, la = math.radians(p[0]), math.radians(p[1])
        return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))
    va, vb = vec(a), vec(b)
    dot = max(-1.0, min(1.0, sum(va[i] * vb[i] for i in range(3))))
    omega = math.acos(dot)
    out = []
    for k in range(n + 1):
        t = k / n
        if omega < 1e-9:
            v = va
        else:
            s0, s1 = math.sin((1 - t) * omega) / math.sin(omega), math.sin(t * omega) / math.sin(omega)
            v = tuple(s0 * va[i] + s1 * vb[i] for i in range(3))
        out.append((math.degrees(math.atan2(v[1], v[0])),
                    math.degrees(math.asin(max(-1.0, min(1.0, v[2]))))))
    return out


def cos_c(lon, lat, lon0, lat0):
    """Cosine of the angular distance from the projection centre. Non-negative
    exactly on the visible hemisphere."""
    lam, phi, p0 = math.radians(lon - lon0), math.radians(lat), math.radians(lat0)
    return math.sin(p0) * math.sin(phi) + math.cos(p0) * math.cos(phi) * math.cos(lam)


def project(lon, lat, lon0, lat0, R, cx, cy):
    lam, phi, p0 = math.radians(lon - lon0), math.radians(lat), math.radians(lat0)
    x = R * math.cos(phi) * math.sin(lam)
    y = R * (math.cos(p0) * math.sin(phi) - math.sin(p0) * math.cos(phi) * math.cos(lam))
    return (cx + x, cy - y)


def ortho(lon, lat, lon0, lat0, R, cx, cy):
    return (project(lon, lat, lon0, lat0, R, cx, cy)
            if cos_c(lon, lat, lon0, lat0) >= 0 else None)


def crossing(inside, outside, lon0, lat0, R, cx, cy):
    """Bisect to the exact point where an edge leaves the visible hemisphere.
    Without this, a run ends up to one sample short of the limb, and an arc drawn
    from an interior point is not the horizon: SVG rescales it and the fill
    balloons across the sphere. That was the first render's failure."""
    a, b = inside, outside
    for _ in range(40):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if cos_c(m[0], m[1], lon0, lat0) >= 0:
            a = m
        else:
            b = m
    return project(a[0], a[1], lon0, lat0, R, cx, cy)


def visible_runs(points, lon0, lat0, R, cx, cy, exact=True):
    """Split a densified ring into runs of visible points, each run beginning and
    ending exactly on the limb when it was clipped."""
    runs, cur = [], []
    prev = None
    for pt in points:
        vis = cos_c(pt[0], pt[1], lon0, lat0) >= 0
        if vis:
            if prev is not None and not prev[1] and exact:
                cur.append(crossing(pt, prev[0], lon0, lat0, R, cx, cy))
            cur.append(project(pt[0], pt[1], lon0, lat0, R, cx, cy))
        else:
            if prev is not None and prev[1]:
                if exact:
                    cur.append(crossing(prev[0], pt, lon0, lat0, R, cx, cy))
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
        prev = (pt, vis)
    if len(cur) > 1:
        runs.append(cur)
    return runs


def on_limb(p, R, cx, cy):
    return abs(math.hypot(p[0] - cx, p[1] - cy) - R) < 0.5


def limb_walk(a, b, R, cx, cy):
    """Return the points of the shorter limb arc from a to b, as a polyline.
    A polyline cannot pick the wrong sweep flag, which an SVG arc can."""
    a0 = math.atan2(a[1] - cy, a[0] - cx)
    a1 = math.atan2(b[1] - cy, b[0] - cx)
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi   # shorter direction, signed
    n = max(2, int(abs(d) / math.radians(2)))
    return [(cx + R * math.cos(a0 + d * k / n), cy + R * math.sin(a0 + d * k / n))
            for k in range(1, n + 1)]
