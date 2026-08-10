#!/usr/bin/env python3
"""Sphere-to-screen maths, shared by the static generator and the runtime port.

Extracted from build_geography.py, where it lived as module-private functions
against a module constant R = 150.0 and an implicit centre at (R, R). Three more
callers need it parameterised: build_worldmap.py, globe_svg.py, and
assets/geo/projection.js, which is a hand port of exactly these functions and
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


def limb_walk(a, b, R, cx, cy, forward=True):
    """Return the points of the limb arc from a to b, as a polyline.

    A polyline cannot pick the wrong sweep flag, which an SVG arc can.

    `forward` is the winding, not a preference. Until 0.1.389 this took the
    arc that was shorter, which is a distance question, and the arc that closes
    a clipped ring is the one that keeps the ring's interior on the correct
    side — a winding question. The two agree for most rings and disagree exactly
    where the fill then spills across the cap. Screen y runs downward, so an
    increasing atan2 angle here is the same traversal as increasing azimuth on
    the sphere: see signed_area for which way that is.
    """
    a0 = math.atan2(a[1] - cy, a[0] - cx)
    a1 = math.atan2(b[1] - cy, b[0] - cx)
    d = (a1 - a0) % (2 * math.pi)
    if not forward:
        d -= 2 * math.pi
    n = max(2, int(abs(d) / math.radians(2)))
    return [(cx + R * math.cos(a0 + d * k / n), cy + R * math.sin(a0 + d * k / n))
            for k in range(1, n + 1)]


# ── winding ───────────────────────────────────────────────────────────────────
def signed_area(ring):
    """Chamberlain-Duquette signed spherical area of a (lon, lat) ring, in
    steradians. The SIGN is the ring's handedness and is what callers want.

    Positive means the interior lies to the RIGHT of the traversal seen from
    outside the sphere, which is the convention this package's topology carries:
    over all 278 rings in assets/vectors/world-110m.json, 277 are positive and
    the one negative ring is South Africa's second, the six-point hole that is
    Lesotho. So the sign distinguishes an outer ring from a hole, and that is
    exactly what the clip needs to decide which way to close.

    ONLY MEANINGFUL WELL BELOW A HEMISPHERE. The value is the area of the region
    on one side, and past a hemisphere the branch wraps: a cap of radius 91
    degrees scores -6.1732 where one of 89 degrees scores +6.1732. Every country
    ring is far below that ceiling (the largest, Russia, is 0.41 sr against
    12.57 for the sphere) and the visible cap is far above it for every t > 0,
    which is why clip_to_cap takes the cap's handedness from its azimuth
    parameterisation instead of from this function.
    """
    r = ring if ring[0] == ring[-1] else list(ring) + [ring[0]]
    s = 0.0
    for (lo1, la1), (lo2, la2) in zip(r, r[1:]):
        s += (math.radians(((lo2 - lo1 + 180.0) % 360.0) - 180.0)
              * (2 + math.sin(math.radians(la1)) + math.sin(math.radians(la2))))
    return s / 2


def azimuth(lon, lat, lon0, lat0):
    """Initial bearing from the projection centre to a point, in [0, 2pi).

    The inverse of cap_point, and the parameter the cap boundary is walked in.
    """
    lam = math.radians(lon - lon0)
    phi, p0 = math.radians(lat), math.radians(lat0)
    return math.atan2(
        math.sin(lam) * math.cos(phi),
        math.cos(p0) * math.sin(phi) - math.sin(p0) * math.cos(phi) * math.cos(lam)
    ) % (2 * math.pi)


def cap_point(az, c, lon0, lat0):
    """-> (lon, lat) at angular distance c and bearing az from the centre.

    Azimuth increasing runs N-E-S-W, so it traverses the cap with the interior
    on the RIGHT seen from outside — the same handedness signed_area calls
    positive. That correspondence is the whole direction rule: a ring with
    positive area closes along the cap in increasing azimuth, a hole in
    decreasing.
    """
    p0 = math.radians(lat0)
    lat = math.asin(max(-1.0, min(1.0, math.sin(p0) * math.cos(c)
                                  + math.cos(p0) * math.sin(c) * math.cos(az))))
    lon = lon0 + math.degrees(math.atan2(
        math.sin(az) * math.sin(c) * math.cos(p0),
        math.cos(c) - math.sin(p0) * math.sin(lat)))
    return (lon, math.degrees(lat))


CAP_STEP_DEG = 1.5              # azimuth resolution of a closure arc

# A point this close to the cap is ON it, and a point on the boundary is not
# INSIDE it. The distinction is not pedantry: Natural Earth closes Antarctica
# along the lat = -90 edge of its rectangular source map, so 181 of its 433
# densified points are a pole artifact rather than coastline, and at t=0 — where
# the cap passes exactly through both poles — every one of them evaluates to
# cos_c = +-6.1e-17. Counted as interior they form a second phantom run whose
# ends carry the pole's own azimuth, the closure links to it, and the fill walks
# the entire limb: Antarctica painted over the whole disc. Counted as boundary
# they contribute no area, the crossing logic puts an exact point on the cap
# where one belongs, and the wedge closes over 40 degrees of arc as it should.
CAP_EPS = 1e-9


def clip_to_cap(ring, lon0, lat0, t, step_deg, forward=None):
    """Intersect a (lon, lat) ring with the visible cap. -> list of closed rings.

    THE CLIP HAPPENS ON THE SPHERE, before projection, and that is the point.
    Clipping in screen space means closing along a projected boundary, and the
    projected boundary is not a closed curve: unrolled wraps longitude into
    (-180, 180] before mixing in the plane term, so a sampled cap jumps the full
    width of the seam twice at every t > 0 — 511 units at t=0.25 and 1004 at
    t=0.5, against R=1000. Every flat closure this package recorded in 0.1.388
    is one of those jumps. On the sphere the cap is a circle in azimuth with no
    seam in it at all, so the closure cannot cross a discontinuity that is not
    there. Splitting at the seam then happens afterwards, to a ring that is
    already correctly closed.

    The visible set is cos_c >= -t: the hemisphere at t=0, everything at t=1.
    Runs are LINKED rather than each closed on itself, so a country the cap cuts
    into two visible pieces comes back as one polygon when that is what it is.
    """
    if t >= 1.0:
        return [list(ring)]
    c = math.acos(max(-1.0, min(1.0, -t)))
    dense = densify(ring, step_deg) if len(ring) > 1 else list(ring)
    if len(dense) < 3:
        return []

    def vis(p):
        return cos_c(p[0], p[1], lon0, lat0) > -t + CAP_EPS

    def cross(inside, outside):
        """The crossing, snapped exactly onto the cap so the closure meets it."""
        a, b = inside, outside
        for _ in range(40):
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if vis(m):
                a = m
            else:
                b = m
        return cap_point(azimuth(a[0], a[1], lon0, lat0), c, lon0, lat0)

    # Rotate so the walk BEGINS AT A RUN's first vertex — a visible vertex whose
    # predecessor is hidden — not merely at a visible one. Starting anywhere
    # inside a run splits that run across the seam of the traversal, and the
    # tail then has no exit crossing of its own: for a ring whose hidden stretch
    # sits just before the start, the tail is [entry, start] and gets dropped as
    # degenerate, taking the entry crossing with it. What is left is linked to
    # an INTERIOR point, so the closure walks to an azimuth that is not on the
    # cap and cuts across the figure. Found by asserting that a ring the cap cut
    # comes back with points on the cap; nothing else could see it.
    if dense[0] == dense[-1]:
        dense = dense[:-1]
    n = len(dense)
    seen = [vis(p) for p in dense]
    if all(seen):
        return [list(ring)]
    if not any(seen):
        return []
    first = next(i for i in range(n) if seen[i] and not seen[i - 1])
    order = [dense[(first + k) % n] for k in range(n)]

    # prev starts on the hidden vertex before the rotation point, so the first
    # run gets its entry crossing like any other.
    runs, cur = [], []
    prev = (dense[first - 1], False)
    for pt in order:
        v = vis(pt)
        if v:
            if not prev[1]:
                cur.append(cross(pt, prev[0]))
            cur.append(pt)
        else:
            if prev[1]:
                cur.append(cross(prev[0], pt))
                if len(cur) > 2:
                    runs.append(cur)
                cur = []
        prev = (pt, v)
    # The last vertex walked is the one before the rotation point and is hidden,
    # so every run has been closed by the loop. Nothing is left over.
    if not runs:
        return []

    # `forward` is the ring's handedness, and a caller that KNOWS it must be
    # able to say so. signed_area's own docstring says it is meaningless within
    # a hair of a hemisphere, and the day/night terminator is exactly a
    # hemisphere: its sign there tracks which pole the cap happens to enclose,
    # so every subsolar point south of the equator classified the ring backwards
    # and the figure shaded its daylight. Rings built by cap_point traverse with
    # the interior on the right by construction and pass forward=True; a country
    # ring, far below the ceiling, still asks.
    if forward is None:
        forward = signed_area(ring) > 0
    step = math.radians(CAP_STEP_DEG)
    ends = [(azimuth(r[0][0], r[0][1], lon0, lat0),
             azimuth(r[-1][0], r[-1][1], lon0, lat0), r) for r in runs]

    out, used = [], set()
    for start in range(len(ends)):
        if start in used:
            continue
        seq, k = [], start
        while k not in used:
            used.add(k)
            _entry, exit_az, run = ends[k]
            seq += run
            # From this run's exit, the next entry met walking in the ring's own
            # direction. With one run that is its own entry, the long way round
            # when the ring wraps the cap — which is the case the index-shortest
            # rule got wrong.
            best, bestd = k, None
            for j, (e2, _x, _r) in enumerate(ends):
                d = (e2 - exit_az) % (2 * math.pi) if forward else \
                    (exit_az - e2) % (2 * math.pi)
                # An entry sitting ON this run's exit is a JOIN when it belongs
                # to another run and a FULL WRAP when it is this run's own. Both
                # occur: Antarctica's source ring carries an artificial break at
                # lon 180, so at a Pacific-centred view its visible coastline
                # arrives as two runs meeting exactly at that point. Reading
                # that zero as a wrap drew a 360 degree arc and painted the
                # whole disc — with every check green, because the result is a
                # closed path of points that all lie on the cap.
                if d <= 1e-12 and j == k:
                    d = 2 * math.pi
                if bestd is None or d < bestd:
                    bestd, best = d, j
            steps = max(1, int(math.ceil(bestd / step)))
            span = bestd
            for s in range(1, steps):
                az = exit_az + (span * s / steps) * (1 if forward else -1)
                seq.append(cap_point(az % (2 * math.pi), c, lon0, lat0))
            k = best
        if len(seq) > 2:
            out.append(seq + [seq[0]])
    return out


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


def seam_crossing(a, b, lon0):
    """The exact (lon, lat) where the edge a->b crosses the antimeridian.

    split_at_seam used to cut between the two samples and leave each part ending
    a fraction short of the edge. Those two ends then sat on OPPOSITE sides of
    the map, and closing the part with a straight line drew a chord clean across
    it — the line through Russia in the 0.1.387 demo deck.
    """
    ra = ((a[0] - lon0 + 180.0) % 360.0) - 180.0
    rb = ((b[0] - lon0 + 180.0) % 360.0) - 180.0
    # Walk b's relative longitude the short way from a's, so the interpolation
    # parameter is taken across the seam rather than across the whole world.
    rb_unwrapped = rb + (360.0 if rb < ra else -360.0)
    edge = 180.0 if rb_unwrapped > ra else -180.0
    span = rb_unwrapped - ra
    f = 0.0 if span == 0 else (edge - ra) / span
    f = max(0.0, min(1.0, f))
    lat = a[1] + (b[1] - a[1]) * f
    # Nudged a hair INSIDE each side. Exactly lon0+180 wraps to -180, so both
    # points would land on the same edge of the map and the segment between them
    # would run the full width — which is the band across northern Russia in the
    # first 0.1.387 demo. A millionth of a degree is 10cm on the ground and half
    # a thousandth of a pixel at any size this figure is drawn.
    inset = 1e-6
    return (lon0 + edge - inset * (1 if edge > 0 else -1), lat), \
           (lon0 - edge + inset * (1 if edge > 0 else -1), lat)


def split_at_seam(ring, lon0, exact=True):
    """Split a (lon, lat) ring where it crosses the moving antimeridian.

    Longitude is relative to lon0, so the seam turns with the globe. A ring that
    crosses it draws a horizontal streak across the whole map as t rises — the
    two ends of the world joined by a straight line. Splitting is not optional
    and it is not a review note.
    """
    def rel(lon):
        return ((lon - lon0 + 180.0) % 360.0) - 180.0

    # A vertex sitting EXACTLY on the seam has no side, and wrap180 sends it to
    # the left edge whichever side it belongs to. Natural Earth carries such
    # vertices — Russia's arctic coast has several at exactly 180 — and the one
    # next to a neighbour at 177.99 drew a line the full width of the map. Give
    # each of them the side its predecessor is on, before anything else looks at
    # them.
    if exact and len(ring) > 1:
        fixed = []
        prev_rel = None
        for lon, lat in ring:
            r = rel(lon)
            if abs(abs(r) - 180.0) < 1e-9 and prev_rel is not None:
                side = 1.0 if prev_rel >= 0 else -1.0
                lon = lon0 + side * (180.0 - 1e-6)
                r = side * (180.0 - 1e-6)
            fixed.append((lon, lat))
            prev_rel = r
        ring = fixed

    parts, cur = [], []
    for i, (lon, lat) in enumerate(ring):
        if i and abs(rel(lon) - rel(ring[i - 1][0])) > 180.0:
            if exact:
                out_pt, in_pt = seam_crossing(ring[i - 1], (lon, lat), lon0)
                cur.append(out_pt)
            if len(cur) > 1:
                parts.append(cur)
            cur = [in_pt] if exact else []
        cur.append((lon, lat))
    if len(cur) > 1:
        parts.append(cur)
    # A closed ring's last piece and its first piece are contiguous, and joining
    # them looks right until a ring wraps the world: Antarctica crosses the seam
    # once, so the join hands back a single piece whose two ends are on opposite
    # edges and whose close runs the full width. With the crossings inserted
    # exactly, each piece already ends on the edge it left by, and a plain close
    # follows that edge. So they are left apart — the visible seam between two
    # halves of one country is one pixel of edge, and the alternative is a line
    # across the map.
    return parts
