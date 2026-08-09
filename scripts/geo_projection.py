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


# ── the unroll ────────────────────────────────────────────────────────────────
def unrolled(lon, lat, lon0, lat0, t, R, cx, cy):
    """Position on the sphere-to-plane interpolation, then orthographic.

    t=0 is the globe and t=1 an equirectangular map, and every value between is
    a real geometry rather than a crossfade. Crossfading two projections has no
    coherent state at t=0.5 and breaks limb clipping halfway through; flattening
    the sphere itself has one code path and no such state.

    The plane spans 2R by R, so the flat map is exactly as wide as the globe and
    the 2:1 equirectangular aspect holds. Longitude is taken relative to lon0 and
    wrapped, so the seam moves with the view — see split_at_seam.

    Visibility interpolates with t: back-face culling at t=0, nothing culled at
    t=1, and the threshold moves between so no polygon pops.

    Returns (x, y, visible).
    """
    lam = math.radians(lon - lon0)
    phi, phi0 = math.radians(lat), math.radians(lat0)
    cphi, sphi = math.cos(phi), math.sin(phi)
    xs = cphi * math.sin(lam)
    ys = math.cos(phi0) * sphi - math.sin(phi0) * cphi * math.cos(lam)
    zs = math.sin(phi0) * sphi + math.cos(phi0) * cphi * math.cos(lam)
    lon_rel = ((lon - lon0 + 180.0) % 360.0) - 180.0
    xp, yp = lon_rel / 180.0, (lat / 90.0) * 0.5
    x = xs + (xp - xs) * t
    y = ys + (yp - ys) * t
    return (cx + R * x, cy - R * y, zs >= -t)


def invert(x, y, lon0, lat0, t, R, cx, cy):
    """Screen back to (lon, lat), or None outside the figure.

    Analytic at both ends, where the map is injective. Between them it is NOT:
    a point on the front of the sphere and one on the back can land on the same
    pixel, so there is no single right answer and this returns the one nearest
    the viewer — what a reader pointing at that pixel means. Multi-start Newton
    on a finite-difference Jacobian, keeping the converged root with the largest
    cos_c.

    So invert(project(p)) == p holds at t=0 and t=1 and for anything front-most,
    and mid-unroll an occluded point correctly comes back as its occluder.
    check_globe.py asserts the screen-space round trip, which is the property
    that holds everywhere, and the exact one only where the map is injective.
    """
    u, v = (x - cx) / R, (cy - y) / R
    if t <= 0.0:
        rho = math.hypot(u, v)
        # A point exactly ON the limb computes rho = 1 plus or minus an ulp, and
        # a bare `rho > 1` rejects half of those. The limb is a legitimate place
        # to be — it is where the horizon is — so the guard has slack and rho is
        # then clamped for the asin. The JS port had this cliff on the other side
        # of the ulp from the Python, which is how it was found.
        if rho > 1.0 + 1e-9:
            return None
        rho = min(rho, 1.0)
        c = math.asin(max(-1.0, min(1.0, rho)))
        if rho < 1e-12:
            return (lon0, lat0)
        p0 = math.radians(lat0)
        lat = math.degrees(math.asin(math.cos(c) * math.sin(p0)
                                     + v * math.sin(c) * math.cos(p0) / rho))
        lon = lon0 + math.degrees(math.atan2(
            u * math.sin(c),
            rho * math.cos(c) * math.cos(p0) - v * math.sin(c) * math.sin(p0)))
        return (((lon + 180.0) % 360.0) - 180.0, lat)
    if t >= 1.0:
        if abs(u) > 1.0 or abs(v) > 0.5:
            return None
        lon = lon0 + u * 180.0
        return (((lon + 180.0) % 360.0) - 180.0, v * 180.0)

    # Mid-unroll the forward map is NOT injective, and no implementation fixes
    # that: the plane term is monotone in longitude while the sphere term is
    # not, so two distinct visible points share a pixel. What a reader is
    # pointing at is the one nearest the viewer, so that is what comes back —
    # the largest cos_c among the converged roots. A single Newton start
    # returned whichever branch it happened to be nearer, which for a
    # seam-adjacent point was often neither.
    best = None
    for seed_lon, seed_lat in _seeds(u, v, lon0, lat0, t):
        root = _newton(x, y, seed_lon, seed_lat, lon0, lat0, t, R, cx, cy)
        if root is None:
            continue
        lon_r, lat_r, residual, depth = root
        key = (-depth, residual)
        if best is None or key < best[0]:
            best = (key, (lon_r, lat_r))
    if best is None:
        return None
    lon_r, lat_r = best[1]
    return (((lon_r + 180.0) % 360.0) - 180.0, lat_r)


def _seeds(u, v, lon0, lat0, t):
    """Newton starts: the flat-map guess, the sphere guess when the point is on
    the disc, and four spread around the circle so a seam-adjacent point still
    has a start on the correct side."""
    out = [(lon0 + u * 180.0, max(-90.0, min(90.0, v * 180.0)))]
    rho = math.hypot(u, v)
    if rho <= 1.0:
        c = math.asin(max(-1.0, min(1.0, rho)))
        if rho > 1e-12:
            p0 = math.radians(lat0)
            lat_s = math.degrees(math.asin(math.cos(c) * math.sin(p0)
                                           + v * math.sin(c) * math.cos(p0) / rho))
            lon_s = lon0 + math.degrees(math.atan2(
                u * math.sin(c),
                rho * math.cos(c) * math.cos(p0) - v * math.sin(c) * math.sin(p0)))
            out.append((lon_s, lat_s))
    for k in range(4):
        out.append((lon0 + 90.0 * k, max(-90.0, min(90.0, v * 180.0))))
    return out


def _newton(x, y, lon, lat, lon0, lat0, t, R, cx, cy):
    """-> (lon, lat, residual, depth) or None if it did not converge.
    `depth` is cos_c: larger is nearer the viewer."""
    for _ in range(24):
        fx, fy, _vis = unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
        ex, ey = fx - x, fy - y
        if abs(ex) < 1e-11 and abs(ey) < 1e-11:
            break
        h = 1e-6
        ax, ay, _ = unrolled(lon + h, lat, lon0, lat0, t, R, cx, cy)
        bx, by, _ = unrolled(lon, lat + h, lon0, lat0, t, R, cx, cy)
        j11, j21 = (ax - fx) / h, (ay - fy) / h
        j12, j22 = (bx - fx) / h, (by - fy) / h
        det = j11 * j22 - j12 * j21
        if abs(det) < 1e-14:
            return None
        lon -= (ex * j22 - ey * j12) / det
        lat -= (ey * j11 - ex * j21) / det
        lat = max(-90.0, min(90.0, lat))
    fx, fy, vis = unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
    residual = math.hypot(fx - x, fy - y)
    if residual > 1e-6 or not vis:
        return None
    return (lon, lat, residual, cos_c(lon, lat, lon0, lat0))


def split_at_seam(ring, lon0):
    """Split a (lon, lat) ring where it crosses the moving antimeridian.

    Longitude is relative to lon0, so the seam turns with the globe. A ring that
    crosses it draws a horizontal streak across the whole map as t rises — the
    two ends of the world joined by a straight line. Splitting is not optional
    and it is not a review note.
    """
    def rel(lon):
        return ((lon - lon0 + 180.0) % 360.0) - 180.0

    parts, cur = [], []
    for i, (lon, lat) in enumerate(ring):
        if i and abs(rel(lon) - rel(ring[i - 1][0])) > 180.0:
            if len(cur) > 1:
                parts.append(cur)
            cur = []
        cur.append((lon, lat))
    if len(cur) > 1:
        parts.append(cur)
    return parts
