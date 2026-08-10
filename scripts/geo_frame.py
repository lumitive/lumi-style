#!/usr/bin/env python3
"""The frame assembly both static emitters share.

Extracted from globe_svg.py unchanged in 0.1.392 so the globe emitter and the
region-map emitter (specs/2026-08-10-globe-map-split-design.md) draw the same
geometry the same way. The move is byte-output-preserving and the reference
diffs in that release's PR are the proof.

Everything here is form-agnostic: loading and decoding the topology, projecting
open lines and filled rings (clip on the sphere, split at the seam, project —
the 0.1.389 order), closing along the map's cut edges, the guard, the rounding
rule the JS renderer mirrors, and the sampled extent. What differs between the
two components — which layers exist, their classes, their ARIA vocabulary —
stays in the emitters.

Standard library only.
"""
from __future__ import annotations

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

# ── the Earth ─────────────────────────────────────────────────────────────────
# The obliquity of the ecliptic: the angle between the rotation axis and the
# normal to the orbital plane. It is why the tropics sit where they do and why
# the terminator is not a meridian, so one constant serves the tilt, the two
# tropic rings and the solar declination.
OBLIQUITY_DEG = 23.4392811

# WGS84 flattening. HONESTLY SUB-PIXEL: at R=1000 the polar radius is 996.65,
# so the two axes differ by 3.4 units in a 2000-unit frame — under a pixel at
# any size this figure is drawn. It is applied as a display transform rather
# than inside the projection, and that is not a shortcut: changing `unrolled`
# would invalidate the 1300-sample golden grid that holds the JavaScript port
# to the Python authority, and the geodetic-vs-geocentric latitude difference
# this introduces peaks at 0.19 degrees — well inside the rounding this
# renderer already does. What makes the figure read as a sphere is the tilt,
# the graticule and the tropics, not the flattening.
FLATTENING = 1.0 / 298.257223563


def earth_transform(cx, cy, tilt_deg=OBLIQUITY_DEG):
    """The tilt-and-flatten transform, as one SVG transform string.

    Order matters and is physical: flatten along the ROTATION AXIS first, then
    tilt the axis. Written right-to-left the way SVG applies them.

    THE POLE LEANS RIGHT. SVG's rotate() is positive clockwise, so a positive
    angle carries the north pole to the reader's right. Which way it leans is a
    free choice — the obliquity is an angle between an axis and a normal and
    has no handedness a viewer can see — and it shipped leaning left from
    0.1.397 until the owner asked for the other one. Nothing downstream cares:
    pick.js reads this group's own CTM rather than assuming a sign.
    """
    return (f"translate({cx:g} {cy:g}) rotate({tilt_deg:g}) "
            f"scale(1 {1 - FLATTENING:.9f}) translate({-cx:g} {-cy:g})")


def solar_position(when):
    """-> (subsolar_lon, subsolar_lat) in degrees for a UTC datetime.

    The standard low-precision almanac: declination from the day of the year
    and the equation of time from the same series. Good to roughly a quarter of
    a degree, which at this figure's scale is a third of a pixel — the shape of
    the terminator is what a reader takes from it, not the minute.
    """
    day = when.timetuple().tm_yday
    frac = 2 * math.pi / 365.24 * (day - 1 + (when.hour - 12) / 24)
    decl = (0.006918
            - 0.399912 * math.cos(frac) + 0.070257 * math.sin(frac)
            - 0.006758 * math.cos(2 * frac) + 0.000907 * math.sin(2 * frac)
            - 0.002697 * math.cos(3 * frac) + 0.001480 * math.sin(3 * frac))
    eqtime = 229.18 * (0.000075
                       + 0.001868 * math.cos(frac) - 0.032077 * math.sin(frac)
                       - 0.014615 * math.cos(2 * frac)
                       - 0.040849 * math.sin(2 * frac))
    utc_minutes = when.hour * 60 + when.minute + when.second / 60
    lon = -((utc_minutes + eqtime) / 4 - 180)
    return (((lon + 180) % 360) - 180, math.degrees(decl))


# The terminator is drawn this far INSIDE the true 90-degree cap. It is not a
# fudge: the ring is otherwise a hemisphere exactly, which is the one radius at
# which signed_area's branch flips (0.1.389 measured it: 89 degrees scores
# +6.17, 91 scores -6.17) and at which the ring can land exactly ON the limb —
# where the clip has to decide the winding of a curve that coincides with the
# boundary it is being clipped against. Facing the antisolar point it got that
# wrong and left a lens of daylight in the middle of the night side.
#
# 0.05 degrees is 5.5 km on the ground, an order of magnitude finer than the
# quarter-degree the solar position itself is good to. The terminator is drawn
# inside its own error bar, and the degenerate case stops existing.
TERMINATOR_INSET_DEG = 0.05


def night_ring(sun_lon, sun_lat, step_deg=2.0):
    """The terminator, as a closed (lon, lat) ring around the ANTISOLAR point.

    The night side is a spherical cap about the antipode of the sun — the same
    shape the clip already speaks, so this ring goes through _project_area like
    any country and comes back clipped to whatever the frame shows.
    """
    # The ANTIPODE, normalised to [-180, 180). Written for a while as a
    # conditional that subtracted 180 when the sun was east and reduced mod 360
    # when it was west — and the western branch returned the sun's OWN
    # longitude, so for every subsolar point in the western hemisphere the cap
    # was drawn around the sun and the figure shaded the daylight. Half of
    # every day was inverted, and check_terminator_area could not see it
    # because it held the sun at one eastern longitude and varied only the view
    # centre: a two-axis geometry checked along one axis.
    alon = ((sun_lon + 360.0) % 360.0) - 180.0
    alat = -sun_lat
    c = math.radians(90.0 - TERMINATOR_INSET_DEG)
    ring = [gp.cap_point(math.radians(a), c, alon, alat)
            for a in [i * step_deg for i in range(int(360 / step_deg))]]

    # UNWRAP the longitudes. cap_point returns lon0 + atan2(...), so the
    # sequence steps through a discontinuity of nearly 360 degrees once per
    # circuit — two adjacent points on the same meridian written 355 degrees
    # apart. densify() interpolates linearly in longitude and cannot know that,
    # so it filled the gap with 178 points sweeping the whole world, and the
    # clip closed the resulting tangle into a LENS of daylight sitting inside
    # the night side. Visible in every view where the terminator crossed that
    # index; invisible to every check, because a lens is a well-formed polygon.
    #
    # The same failure densify has had twice before, both times where a ring's
    # longitude representation jumps and nothing told the interpolator. A
    # continuously-unwrapped sequence is what the clip wants anyway: cos_c is
    # periodic in longitude and split_at_seam re-wraps afterwards.
    out = [ring[0]]
    for lon, lat in ring[1:]:
        prev = out[-1][0]
        while lon - prev > 180:
            lon -= 360
        while prev - lon > 180:
            lon += 360
        out.append((lon, lat))
    # Close it: the first point again, written near the last one.
    close = out[0][0]
    while close - out[-1][0] > 180:
        close -= 360
    while out[-1][0] - close > 180:
        close += 360
    out.append((close, out[0][1]))
    return out


# A city label's box, as multiples of the font size. No font metrics are
# available here, so the width is estimated per character — and the estimate
# has to be an OVER-estimate, because being too wide drops a label that would
# have fitted and being too narrow draws two labels through each other.
#
# 0.55 was the MEAN, which is not the same thing and is the wrong statistic:
# measured against the shipped D-DIN, real names run 0.48 em/char ("Paris") to
# 0.62 ("Hamburg"), so half of them were under-estimated and "Paris",
# "Hamburg" and "Antwerp" rendered on top of each other over northern Europe.
# 0.66 is above the measured maximum with headroom. What holds it there is
# check_city_labels_do_not_collide, which measures the RENDERED glyphs rather
# than recomputing this arithmetic and agreeing with itself.
CITY_EM_W = 0.66
CITY_EM_H = 1.15
CITY_GAP = 0.9                  # dot-to-text gap, in font sizes
# Boxes are padded before they are compared. Without it two labels that merely
# ABUT both pass the overlap test and render as one word — "ParisHamburg" over
# northern Europe, where the projection squeezes the two together. Touching is
# not colliding to a rectangle test and is very much colliding to a reader.
CITY_PAD_EM = 0.35


# A label anchored nearer the limb than this points at geography compressed to
# a sliver, and its own text runs off the disc. cos_c is the cosine of the
# angular distance from the view centre, so 0.25 is about 75 degrees out.
LABEL_LIMB_COS = 0.25


# A trade lane is drawn just clear of the land so it does not fight the coast
# it runs over. 1.004 is four units at R=1000 — under a pixel of separation at
# any size this figure is drawn, and enough that the stroke reads as ON the
# sphere rather than IN it.
LINK_R = 1.004


def great_circle(a, b, n=64):
    """The shortest path between two places on the sphere, as (lon, lat).

    Spherical linear interpolation between the two unit vectors. This is the
    honest shape for a trade lane and it is why a Shanghai-to-Rotterdam link
    crosses Siberia rather than the Suez: the drawing states the geometry, and
    where a hull actually goes instead is a fact about canals and ice, not
    about distance.

    Returned as a plain ring so it goes through _project_ring like a graticule
    line — which is what gives it limb clipping, seam splitting and far-side
    culling without a line of new code.
    """
    def unit(lon, lat):
        p, q = math.radians(lon), math.radians(lat)
        return (math.cos(q) * math.cos(p), math.cos(q) * math.sin(p), math.sin(q))

    p, q = unit(*a), unit(*b)
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(p, q))))
    w = math.acos(dot)
    if w < 1e-9:
        return [tuple(a)]
    out = []
    for i in range(n + 1):
        t = i / n
        s1, s2 = math.sin((1 - t) * w) / math.sin(w), math.sin(t * w) / math.sin(w)
        v = tuple(s1 * x + s2 * y for x, y in zip(p, q))
        m = math.sqrt(sum(c * c for c in v))
        v = tuple(c / m for c in v)
        lon = math.degrees(math.atan2(v[1], v[0]))
        lat = math.degrees(math.asin(max(-1.0, min(1.0, v[2]))))
        # UNWRAP. atan2 returns (-180, 180], so a lane crossing the
        # antimeridian steps from -178.6 to +176.1 — a jump of 355 degrees
        # between two points that are five degrees apart. densify interpolates
        # linearly in longitude and cannot know that, so it filled the gap by
        # sweeping the entire world and the lane closed into a RING around the
        # globe. Visible on any Pacific route; invisible to every check.
        #
        # This is the FOURTH time this exact failure has been introduced here,
        # and the comment in night_ring below already named the first three.
        # A ring whose longitude representation jumps has to say so, or say
        # nothing and be continuous. split_at_seam re-wraps afterwards.
        if out:
            while lon - out[-1][0] > 180:
                lon -= 360
            while out[-1][0] - lon > 180:
                lon += 360
        out.append((lon, lat))
    return out


def great_circle_route(waypoints, n=24):
    """A route through a sequence of places, each leg the shortest path.

    A trade lane is not one great circle. A box from Shanghai to Rotterdam does
    not cross Siberia; it goes through the Malacca Strait, Bab-el-Mandeb, the
    Suez Canal and Gibraltar, because those are the gaps in the land. Modelling
    the route as legs between CHOKEPOINTS is what makes the drawing a shipping
    lane rather than a line on a sphere — and each leg is still the shortest
    path, so the geometry stays honest at the scale it is claimed at.

    The joint between two legs is dropped once, so the result is one continuous
    ring and the unwrapping above carries across the whole route.
    """
    if len(waypoints) < 2:
        return [tuple(waypoints[0])] if waypoints else []
    out = []
    for a, b in zip(waypoints, waypoints[1:]):
        leg = great_circle(a, b, n)
        if out:
            # Continue the unwrap across the joint rather than restarting it.
            shift = 0.0
            while leg[0][0] + shift - out[-1][0] > 180:
                shift -= 360
            while out[-1][0] - (leg[0][0] + shift) > 180:
                shift += 360
            leg = [(lo + shift, la) for lo, la in leg]
            leg = leg[1:]
        out += leg
    return out


def link_weight_attrs(w):
    """-> (stroke width in R-units, opacity) for a lane of weight `w` in [0,1].

    Weight is encoded TWICE, in width and in opacity, and that is deliberate
    rather than redundant: the light lanes have to survive being light, and a
    quantity carried on two channels reads at a glance where one channel makes
    the tail of the distribution vanish. Both have a floor — a 0.2 lane is
    still a lane, and a lane nobody can see is a lane that should not have been
    in the data.
    """
    w = max(0.0, min(1.0, float(w)))
    return (0.0009 + 0.0034 * w, 0.30 + 0.55 * w)


def tilt_to_screen(x, y, cx, cy, tilt_deg=OBLIQUITY_DEG):
    """A point in the earth group's space, as the reader actually sees it.

    Everything on this globe is drawn inside `.gl-earth`, which rotates. Label
    placement is a question about SCREEN geometry — does this word land on that
    word, does this name run off the right edge — and asking it in group space
    gets a different answer, because rotating the scene moves the points while
    the label boxes stay axis-aligned to the screen.

    That is not a subtle discrepancy. At the obliquity a point 700 units above
    the centre moves about 280 units sideways, so the crowded corner of the
    frame is not the crowded corner of the picture, and five European labels
    that cleared each other by arithmetic rendered as a single blot.
    """
    a = math.radians(tilt_deg)
    dx, dy = x - cx, y - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a),
            cy + dx * math.sin(a) + dy * math.cos(a))


def screen_to_tilt(dx, dy, tilt_deg=OBLIQUITY_DEG):
    """A screen-space OFFSET, expressed in the earth group's space.

    The counter-rotation on each label makes its glyphs run horizontally on
    screen, so the gap between a dot and its name has to be horizontal on
    screen too — and a plain +x offset in group space comes out at 23 degrees.
    """
    a = math.radians(-tilt_deg)
    return (dx * math.cos(a) - dy * math.sin(a),
            dx * math.sin(a) + dy * math.cos(a))


def place_city_labels(points, R, cx, cy, size, reserved=()):
    """Decide which city labels are drawn, and on which side of their dot.

    `points` is [(name, x, y, visible)] in SCREEN space — pass them through
    tilt_to_screen first, or this compares boxes the reader never sees. Returns a list of
    (name, x, y, anchor, drawn) in the SAME ORDER, so a caller can pair it back
    to its input.

    Two rules, and both exist because a sphere is not a map:

    1. SIDE. Orthographic crowds everything toward the limb, so a label set to
       the right of a dot on the right half of the disc runs straight off the
       edge. Labels on the right half are set to the LEFT of their dot and vice
       versa, which turns the crowded direction into the empty one.

    2. COLLISION. Near the limb, points that are far apart on the sphere land
       within a few units of each other on the screen. Labels are placed in
       order of distance from the view CENTRE — the least foreshortened first,
       which is also the most readable — and one whose box overlaps a box
       already placed is dropped rather than shrunk or nudged. Dropping is what
       keeps this deterministic: the static frame and the live frame run the
       same comparison in the same order and agree, which a nudge would not.
    """
    order = sorted(
        (i for i, p in enumerate(points) if p[3]),
        key=lambda i: (points[i][1] - cx) ** 2 + (points[i][2] - cy) ** 2)
    out = [(p[0], p[1], p[2], "start", False) for p in points]
    # `reserved` is boxes already spoken for by another layer — the bloc labels,
    # which are anchored to their own geography and cannot move. Seeding them
    # here is what stops "EU 27 · 0.45B" and "Hamburg" from being drawn through
    # each other: one collision pass, two layers, and the layer that cannot
    # move goes in first.
    placed = list(reserved)
    for i in order:
        name, x, y, _vis = points[i]
        w = CITY_EM_W * size * len(name)
        h = CITY_EM_H * size
        gap = CITY_GAP * size
        right_half = x >= cx
        anchor = "end" if right_half else "start"
        x0 = (x - gap - w) if right_half else (x + gap)
        pad = CITY_PAD_EM * size
        box = (x0 - pad, y - h / 2, x0 + w + pad, y + h / 2)
        if any(box[0] < q[2] and q[0] < box[2]
               and box[1] < q[3] and q[1] < box[3] for q in placed):
            continue
        placed.append(box)
        out[i] = (name, x, y, anchor, True)
    return out


def _load(regions_path=None):
    """`regions_path` is the per-instance hook: a custom registry rides in
    while the topology stays the shipped one — regions group countries, they
    do not redraw them."""
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    reg = json.loads(pathlib.Path(regions_path).read_text(encoding="utf-8")
                     if regions_path else REGIONS.read_text(encoding="utf-8"))
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


def _unwrap_lons(points):
    """Make a sequence of (lon, lat) continuous in longitude.

    Any representation that wraps at +-180 puts a 360-degree step between two
    neighbouring points, and every consumer that interpolates between them —
    densify, above all — reads that step as a journey. This is the same repair
    night_ring and great_circle each carry, hoisted to where a caller can apply
    it to something it did not build.
    """
    if len(points) < 2:
        return list(points)
    out = [tuple(points[0])]
    for lon, lat in points[1:]:
        while lon - out[-1][0] > 180:
            lon -= 360
        while out[-1][0] - lon > 180:
            lon += 360
        out.append((lon, lat))
    return out


def _project_ring(ring, view):
    """-> list of screen-space runs, for an OPEN line such as a graticule.

    No closure and no cap clipping beyond dropping what is not visible: a
    meridian is a line, and a line that leaves the figure simply stops.
    """
    lon0, lat0, t, R, cx, cy = view
    runs = []
    for part in gp.split_at_seam(ring, lon0):
        # RE-UNWRAP EACH PART BEFORE DENSIFYING. split_at_seam re-expresses
        # longitudes relative to lon0, and a part can come back straddling that
        # rewrap: a lane spanning 103.8 to 121.5 degrees came out spanning -255
        # to 121.5, a span of 376 degrees for seventeen degrees of route.
        # densify interpolates linearly in longitude, so it filled that with a
        # sweep right around the world and the lane drew as a ring.
        #
        # Normalising the whole part would reintroduce the jump; unwrapping it
        # makes the part continuous, which is what densify needs and what a
        # part IS — one unbroken piece of line. For a part that is already
        # continuous, and every graticule and coastline part is, this is a
        # no-op.
        part = _unwrap_lons(part)
        dense = gp.densify(part, STEP_DEG) if len(part) > 1 else part
        cur = []
        for lon, lat in dense:
            x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
            if vis:
                cur.append((x, y))
            else:
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
        if len(cur) > 1:
            runs.append(cur)
    return runs


def _project_area(ring, view, forward=None):
    """-> list of screen-space runs for a FILLED ring, already closed.

    Three steps in this order, and the order is the fix that 0.1.389 is.

    1. Clip to the visible cap ON THE SPHERE (gp.clip_to_cap), closing along the
       cap in the ring's own winding — `forward` overrides how that winding
       is determined, for a ring whose handedness is known by construction and
       whose radius is too near a hemisphere for signed_area to read. Doing this in screen space means closing
       along a projected cap, and a projected cap is not a closed curve — it
       jumps the width of the seam twice at every t > 0.
    2. Split the closed result at the seam, which is what keeps a ring that
       crosses the moving antimeridian from drawing a streak across the map.
    3. Project, and close each piece along the map's own cut edges.
    """
    lon0, lat0, t, R, cx, cy = view
    runs = []
    for closed in gp.clip_to_cap(ring, lon0, lat0, t, STEP_DEG, forward):
        for part in gp.split_at_seam(closed, lon0):
            pts = [gp.unrolled(lo, la, lon0, lat0, t, R, cx, cy)[:2]
                   for lo, la in part]
            if len(pts) > 1:
                runs.append(pts)
    return runs


def _pole_close(a, b, view):
    """Close a piece whose two ends sit on OPPOSITE sides of the seam.

    Only a ring that wraps the world does this — Antarctica crosses the seam
    once, so it comes back as a piece running edge to edge — and the way a map
    draws it is around the pole, not straight across.

    Both edges are exact rather than fitted. At lon_rel = +-180 the sphere term
    cos(phi) sin(lam) vanishes at every latitude, so THE SEAM IS A PAIR OF
    VERTICAL LINES at x = cx +- tR. A pole is a point on the sphere and a
    SEGMENT on the unrolled map, at y = cy -+ R(1 - t/2), spanning those two
    verticals. Both collapse at t=0 and both are the whole boundary at t=1.

    Until 0.1.389 this was restricted to t=1 and measured against x = cx +- R,
    the seam's position at t=1 only. That restriction was a symptom: at
    intermediate t it matched pieces against an edge that was nowhere near them,
    and drew a box under the globe.
    """
    lon0, lat0, t, R, cx, cy = view
    if t <= 0.0:
        return []
    left, right, eps = cx - t * R, cx + t * R, max(R * 0.002, t * R * 0.02)
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


def _d(runs, close, view=None):
    closed = []
    for pts in runs:
        seq = list(pts)
        # Runs of fewer than three points are left alone. Closing one produces a
        # degenerate sliver, and the JS renderer already skipped them — a
        # divergence the parity check found and neither renderer's own output
        # would have shown.
        if close and view is not None and len(seq) > 2:
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
