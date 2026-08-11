#!/usr/bin/env python3
"""Verify the globe maths, and that the JavaScript port agrees with it.

assets/geo/projection.js is a hand port of scripts/geo_projection.py. Nothing
in this repository can compile JavaScript — there is no package.json, and CI runs
py_compile over the Python and bash -n over two shell scripts — so the port is
held to the Python authority by a golden grid instead of by a type checker.

    python3 scripts/check_globe.py --python-only   # properties only; runs in CI
    python3 scripts/check_globe.py                 # also the port; needs Playwright

Like check_prose.py, check_design.py and inspect_layout.py, the full run cannot
run in CI. --python-only can, and does.

Two halves, and they check different things:

  the properties     what the golden values cannot say, because a fixture only
                     records what the code did. Round-tripping, the poles not
                     smearing, the limb actually culling, the seam actually
                     splitting.
  the port           that the JavaScript computes the same numbers as the
                     Python, to 1e-9, over every sample in the grid.

A check that did not run is not a check that passed: a missing module, an
unreadable fixture or an absent browser is reported as a failure, never skipped
into silence.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import pathlib
import re
import subprocess
import sys
from collections.abc import Callable
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import geo_projection as gp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "fixtures" / "globe-golden.json"
JS = ROOT / "assets" / "geo" / "projection.js"
JS_DATA = ROOT / "assets" / "geo" / "worlddata.js"
JS_RENDER = ROOT / "assets" / "globe" / "render-svg.js"
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
REGIONS = ROOT / "assets" / "vectors" / "regions.json"

TOLERANCE = 1e-9      # agreement between the port and the authority
ROUND_TRIP = 1e-6     # degrees, invert(project(p)) back to p
# The inverse is ill-conditioned ON the limb, where the forward map's derivative
# goes to infinity: asin(rho) at rho=1. That is a property of an orthographic
# projection, not a defect, and the residual there measured 3.3e-6 degrees —
# 0.36 metres on the ground. Points within this much of the limb get the looser
# bound, and the bound is stated rather than the check quietly widened for all.
LIMB_BAND = 1e-3
ROUND_TRIP_LIMB = 1e-4
# A FLOOR on how much of its own viewBox a static frame's ink occupies. This is
# not the withdrawn page-fill floor in a new costume: it measures one generated
# figure against the box that same generator chose, where the only way to score
# low is to have reserved space for nothing. Correct output measures about 96%;
# a viewBox fixed at 2R square scores 50% at t=1, which renders a 2:1 map at
# half the height its cell allows.
FRAME_FILL_FLOOR = 0.80
# How far the rendered night side may sit from the closed-form area. A
# CEILING on error, and 0.5% is roughly six times the 0.08% the corrected
# clip achieves — loose enough to survive antialiasing, far too tight for
# either lens this check was written after.
TERMINATOR_AREA_TOLERANCE = 0.005


def _views(golden):
    return [(v["lon0"], v["lat0"], v["t"], v["R"], v["cx"], v["cy"])
            for v in golden["views"]]


# ── the properties ────────────────────────────────────────────────────────────
def check_round_trip(golden):
    """The screen-space round trip everywhere, and the exact one where the map
    is injective.

    The golden grid cannot assert either: it records what project returned, so a
    projection and an inverse wrong in the same direction would match it
    perfectly.

    Two properties, because mid-unroll the map is genuinely many-to-one — a
    front point and a back point share a pixel, and invert returns the nearer.
    So project(invert(x, y)) must land back on (x, y) ALWAYS, while
    invert(project(p)) == p only at t=0 and t=1 and wherever p is the front-most
    point at its pixel. Asserting only the second would have forced invert to
    lie; asserting only the first would miss a wholesale inversion.
    """
    errors = []
    for vi, (lon0, lat0, t, R, cx, cy) in enumerate(_views(golden)):
        for lon, lat in ((lo, la) for lo in range(-180, 181, 15)
                         for la in range(-75, 76, 15)):
            x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
            if not vis:
                continue
            back = gp.invert(x, y, lon0, lat0, t, R, cx, cy)
            if back is None:
                errors.append(f"view {vi}: ({lon}, {lat}) projects visible but "
                              f"inverts to None")
                continue
            # screen space: must hold for every visible point, at every t
            rx, ry, _ = gp.unrolled(back[0], back[1], lon0, lat0, t, R, cx, cy)
            if math.hypot(rx - x, ry - y) > 1e-6:
                errors.append(f"view {vi}: ({lon}, {lat}) at ({x:.6f}, {y:.6f}) "
                              f"inverts to a point that projects to "
                              f"({rx:.6f}, {ry:.6f})")
                continue
            # exact: only where the map is injective, or where p is front-most
            front_most = gp.cos_c(lon, lat, lon0, lat0) >= gp.cos_c(
                back[0], back[1], lon0, lat0) - 1e-9
            if not (t in (0.0, 1.0) or front_most):
                continue
            near_limb = abs(gp.cos_c(lon, lat, lon0, lat0)) < LIMB_BAND
            bound = ROUND_TRIP_LIMB if near_limb else ROUND_TRIP
            dlon = abs(((back[0] - lon + 180) % 360) - 180)
            if dlon > bound or abs(back[1] - lat) > bound:
                errors.append(f"view {vi}: ({lon}, {lat}) round-trips to "
                              f"({back[0]:.9f}, {back[1]:.9f}), bound {bound}")
    return errors


def check_poles(golden):
    """A pole is one point on the globe and a full edge on the flat map, and it
    opens monotonically between.

    The first version of this check asserted the pole stays a single point until
    t=1. That was wrong about the design, not about the code: an equirectangular
    map draws each pole as an edge, so the pole HAS to fan out as the sphere
    flattens. A pole that stayed a point and became an edge at t=1 would pop,
    which is the defect the interpolation exists to avoid. What is worth
    asserting is that the opening is monotone in t and exact at both ends.
    """
    errors = []
    for pole in (90, -90):
        widths = []
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            xs = [gp.unrolled(lon, pole, 0.0, 0.0, t, 150.0, 150.0, 150.0)[0]
                  for lon in range(-180, 181, 15)]
            widths.append(max(xs) - min(xs))
        if widths[0] > 1e-9:
            errors.append(f"the {pole} pole is {widths[0]:.6f} wide at t=0; "
                          f"on a globe it is a point")
        # Sampled every 15 degrees, and 180 wraps onto -180 because they are the
        # same meridian, so the widest observable span is 345 of 360 degrees.
        expected = 2 * 150.0 * (345.0 / 360.0)
        if abs(widths[-1] - expected) > 1e-6:
            errors.append(f"the {pole} pole spans {widths[-1]:.3f} at t=1, "
                          f"expected {expected:.3f} for a 15-degree sampling of "
                          f"the full map width")
        for a, b in zip(widths, widths[1:]):
            if b < a - 1e-9:
                errors.append(f"the {pole} pole narrows as t rises: {widths}; "
                              f"the opening must be monotone or it reads as a snap")
                break
    return errors


def check_culling(golden):
    """At t=0 the far side is hidden and the near side is not; at t=1 nothing is."""
    errors = []
    for vi, (lon0, lat0, t, R, cx, cy) in enumerate(_views(golden)):
        near = gp.unrolled(lon0, lat0, lon0, lat0, t, R, cx, cy)[2]
        far = gp.unrolled(lon0 + 180, -lat0, lon0, lat0, t, R, cx, cy)[2]
        if not near:
            errors.append(f"view {vi}: the projection centre is culled")
        if t == 0.0 and far:
            errors.append(f"view {vi}: the antipode is visible at t=0")
        if t == 1.0 and not far:
            errors.append(f"view {vi}: the antipode is culled at t=1, "
                          f"where nothing may be")
    return errors


def check_seam():
    """A ring crossing the moving antimeridian is split, and one that does not is
    left whole. Without the split, the ring draws a streak across the map."""
    errors = []
    crossing = [(170.0, 10.0), (175.0, 12.0), (-175.0, 12.0), (-170.0, 10.0)]
    if len(gp.split_at_seam(crossing, 0.0)) != 2:
        errors.append("a ring crossing the seam at lon0=0 was not split in two")
    if len(gp.split_at_seam(crossing, 180.0)) != 1:
        errors.append("a ring not crossing the seam at lon0=180 was split anyway")
    inner = [(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)]
    if len(gp.split_at_seam(inner, 0.0)) != 1:
        errors.append("a ring far from the seam was split")
    return errors


def check_static_svg():
    """Every coordinate globe_svg emits sits inside the viewBox it emits.

    inspect_layout --deliverable gates on a drawing clipped by its own viewBox,
    and that gate exists because check_design once reported all-clear on a
    figure whose band was cut off by exactly this. The globe's limb sits ON the
    edge, so it is the likeliest thing in this package to trip it.

    Checked at both ends and the middle. The PRODUCTS pin t — the globe to 0,
    the map to 1 — but the shared geometry keeps the parameter, and this sweep
    is part of what holds 0.1.389's winding work: the land layer runs the same
    clip path every ring in the topology runs, at every t.
    """
    import globe_svg
    import regionmap_svg

    errors = []
    R = globe_svg.DEFAULT_R
    frames = [(f"field t={t}", globe_svg.render((0.0, 0.0, t, R, R, R)))
              for t in (0.0, 0.5, 1.0)]
    frames.append(("regionmap", regionmap_svg.render()))
    if True:
        for name, svg in frames:
            m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', svg)
            if not m:
                errors.append(f"{name}: no viewBox emitted")
                continue
            vx, vy, vw, vh = (float(g) for g in m.groups())
            xs, ys = [], []
            for d in re.findall(r'\sd="([^"]+)"', svg):
                for xy in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", d):
                    xs.append(float(xy[0]))
                    ys.append(float(xy[1]))
            for c in re.finditer(r'<circle[^>]*cx="(-?[\d.]+)"[^>]*cy="(-?[\d.]+)"'
                                 r'[^>]*r="([\d.]+)"', svg):
                cxx, cyy, rr = (float(g) for g in c.groups())
                xs += [cxx - rr, cxx + rr]
                ys += [cyy - rr, cyy + rr]
            if not xs:
                errors.append(f"{name}: the frame drew nothing")
                continue
            if min(xs) < vx or max(xs) > vx + vw or min(ys) < vy or max(ys) > vy + vh:
                errors.append(
                    f"{name}: ink spans x {min(xs):.1f}..{max(xs):.1f}, "
                    f"y {min(ys):.1f}..{max(ys):.1f} but the viewBox is "
                    f"{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f} — clipped")
            # Not the smallest margin: one tight side hides three loose ones,
            # and a square viewBox around a 2:1 flat map passes that test while
            # rendering at half the height its cell allows. Area is what
            # inspect_layout calls aspect mismatch, and it is the real defect.
            fill = ((max(xs) - min(xs)) * (max(ys) - min(ys))) / (vw * vh)
            if fill < FRAME_FILL_FLOOR:
                errors.append(
                    f"{name}: the ink fills {fill:.0%} of its viewBox "
                    f"(floor {FRAME_FILL_FLOOR:.0%}); the box reserves space "
                    f"nothing draws in, so the figure renders small in its cell")
    return errors


# A segment running the full width of the figure is a ring that was cut and then
# rejoined across everything. Four causes were found and fixed in 0.1.387: the two
# inserted seam crossings landing on the same edge because lon0+180 wraps to -180;
# source vertices sitting exactly on the antimeridian, which have no side; a
# pole-edge close that fired on the globe, where the boundary is a disc and not a
# rectangle; and a limb walk that ran from the wrong end, so its first point sat
# beside the start of the run instead of beside the end.
#
# The renderers now also carry a last-resort guard — no real edge in this
# projection spans half the figure — which runs after every closure, because a
# closure can introduce the thing it guards against. This check is what proves
# the guard is not quietly hiding a fifth cause: it looks at every state.
def check_seam_segments():
    """No figure draws a line across itself, in any form at any t.

    A segment along a POLE EDGE is not this defect: a pole is a point on the
    sphere and a segment on the unrolled map, at y = cy -+ R(1 - t/2), so
    closing a world-wrapping ring like Antarctica along it is what a map does.
    That edge is real at every t > 0 and not only at t=1 — see _pole_close.
    Only segments away from an edge count.

    Nothing is recorded here any more. Until 0.1.389 three (form, t) pairs were
    carried as known flat closures, and the comment over them claimed a two-way
    lock: a fourth would fail, and so would fixing one without removing its
    line. **The second half was never implemented** — the set of pairs actually
    seen was collected into `seen_flat` and then never compared against
    anything, so all three could have silently healed and nothing would have
    said so. A lock that only turns one way is the failure mode item 3 of the
    backlog exists to find, and it was sitting in the check that found the
    defect this release fixes.
    """
    import globe_svg
    import regionmap_svg

    R = globe_svg.DEFAULT_R
    errors = []
    # The field frame sweeps t: its land layer runs every ring in the topology
    # through the shared clip, which is a superset of what the region layer ran
    # — the same rings grouped differently — so the land sweep IS the 0.1.389
    # winding guard. The map frame adds the region grouping at its own t=1.
    frames = [(f"field t={t}", t, globe_svg.render((0.0, 0.0, t, R, R, R)))
              for t in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)]
    frames.append(("regionmap", 1.0, regionmap_svg.render()))
    for name, t, svg in frames:
        if True:
            view = (0.0, 0.0, t, R, R, R)
            half = R * (1 - t / 2)
            top, bottom = view[5] - half, view[5] + half
            on_pole_edge = lambda y, top=top, bottom=bottom: (  # noqa: E731
                abs(y - top) < R * 0.03 or abs(y - bottom) < R * 0.03)
            for m in re.finditer(r'class="(?:gl-land|rg [^"]*)"[^>]*d="([^"]*)"', svg):
                pts = [(c.group(1), int(c.group(2)), int(c.group(3)))
                       for c in re.finditer(r"([ML])(-?\d+) (-?\d+)", m.group(1))]
                for i in range(1, len(pts)):
                    if pts[i][0] != "L":
                        continue          # an M is a move, not a drawn segment
                    if (abs(pts[i][1] - pts[i - 1][1]) < 1.2 * R
                            and abs(pts[i][2] - pts[i - 1][2]) < 1.2 * R):
                        continue
                    if on_pole_edge((pts[i][2] + pts[i - 1][2]) / 2):
                        continue
                    errors.append(f"{name}: a segment runs from "
                                  f"{pts[i - 1][1:]} to {pts[i][1:]}")
                    break
                # A long PERFECTLY HORIZONTAL segment away from a pole edge is
                # never real geography here: after projection a parallel is a
                # curve, so a run of constant y is a closure that took a
                # straight line instead of following the boundary. This is what
                # the bands across the globe were made of, and nothing else in
                # this package could see them — they are filled areas, not the
                # full-width jumps the test above looks for.
                #
                # This loop used to sit OUTSIDE the enclosing one, so it read
                # whatever `pts` the last path had left behind and examined ONE
                # path per frame — of 12 for the region layer. Every flat
                # closure it did report was found in that one path by luck.
                for i in range(1, len(pts)):
                    if pts[i][0] != "L" or pts[i][2] != pts[i - 1][2]:
                        continue
                    if abs(pts[i][1] - pts[i - 1][1]) < 0.25 * R:
                        continue
                    if on_pole_edge(pts[i][2]):
                        continue
                    errors.append(
                        f"{name}: a flat segment "
                        f"{abs(pts[i][1] - pts[i - 1][1])} units wide at "
                        f"y={pts[i][2]} — a parallel projects as a curve, so "
                        f"this is a closure that cut straight across instead of "
                        f"following the boundary")
                    break
    return errors


def _norm_path(d):
    """Path data with insignificant whitespace removed.

    The Python generator joins subpaths with a space and the JS renderer
    concatenates them; both are valid and the difference is not a defect.
    Everything else — every coordinate, in order — has to match.
    """
    return re.sub(r"\s*([MLZ])\s*", r"\1", d).strip()


# EMPTY, AND IT STAYS EMPTY. Two renderers that disagree anywhere are not one
# renderer with two back ends, which is what this package's globe design claims
# they are. 0.1.388 carried one entry here — at t=0.5 the oceania region closed
# a subpath in Python where the JS renderer continued it — because both sides
# picked their closing arc by index distance and the index-shorter arc was
# ambiguous there. 0.1.389 removed the cause rather than the symptom: the clip
# now happens on the sphere in the ring's own winding, which is the same
# decision in both implementations because it does not depend on sampling.
#
# The set is kept rather than deleted because it is also the lock: an entry that
# stops reproducing fails this check, so a recorded defect cannot heal in
# silence. That half was the half KNOWN_FLAT_CLOSURES never implemented.
KNOWN_RENDERER_DIVERGENCE: set[tuple[str, str]] = set()


def _commands(d):
    return [(c.group(1), c.group(2)) for c in
            re.finditer(r"([MLZ])\s*(-?\d*\s*-?\d*)", d) if c.group(1)]


def _path_diff(a, b):
    """-> a description of the first real difference, or None."""
    ca, cb = _commands(a), _commands(b)
    if len(ca) != len(cb):
        return (f"{len(ca)} path commands against {len(cb)} — one renderer "
                f"closed or split something the other did not")
    for i, ((oa, va), (ob, vb)) in enumerate(zip(ca, cb)):
        if oa != ob:
            return f"command {i} is {oa} in python and {ob} in js"
        if oa == "Z":
            continue
        pa = [float(x) for x in va.split()]
        pb = [float(x) for x in vb.split()]
        if len(pa) != len(pb) or any(abs(x - y) > 1.0 for x, y in zip(pa, pb)):
            return f"command {i}: python {pa} against js {pb}"
    return None


def check_renderer_parity():
    """The JS renderer draws what the Python generator drew, path for path.

    Two renderers over one projection is only safe if they agree. They did not:
    the pole-edge close was scoped to t=1 in Python and unscoped in JavaScript,
    so a static frame was clean and its first animated frame grew a band across
    the bottom of the globe. Nothing else in this package could see that — the
    static frame is what every gate reads.

    Compared as command sequences: same commands in the same order, and every
    coordinate within one unit.

    Two weaker versions were tried. Point counts with a percentage tolerance
    caught none of three deliberate divergences — a pole close firing at the
    wrong t adds two points to one region out of eleven. Byte-for-byte is too
    strict in the other direction: Python and V8 disagree in the last ulp of
    sin, so a true coordinate of 972.5 lands either side and rounds to 972 or
    973. That is a one-unit difference in a 2000-unit space, and demanding
    identical bytes across two languages' trigonometry is demanding something
    unachievable rather than something correct.
    """
    if not JS_DATA.exists() or not JS_RENDER.exists():
        return [f"{JS_RENDER.relative_to(ROOT)} is missing"]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so renderer parity was NOT checked."]
    import globe_svg

    R = globe_svg.DEFAULT_R
    # FIELD parity, since the split: the land path and the mark positions. The
    # land layer runs every ring in the topology through the shared clip, which
    # is a superset of the region grouping the old check compared — and the
    # regions moved to a component whose runtime never touches geometry, so
    # there is nothing on that side left to diverge. The canvas gap this check
    # could never see (a form branch keyed on state nobody set) was deleted
    # with the branch.
    #
    # Keys are passed explicitly rather than built on each side. JavaScript
    # renders 0.0 as "0", so a key composed independently in both languages did
    # not match and every path reported as "drew nothing" — a parity check
    # failing on its own bookkeeping.
    MARKS = [{"lon": 103.8, "lat": 1.35, "weight": 3, "id": "sg"},
             {"lon": -122.4, "lat": 37.8, "weight": 9, "id": "sf"},
             {"lon": 13.4, "lat": 52.5, "weight": 1, "id": "ber"}]
    cases = [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (0.0, -20.0)]
    keyed = [{"key": f"t{t}_lon{lon0}", "t": t, "lon0": lon0} for t, lon0 in cases]
    want = {}
    for t, lon0 in cases:
        svg = globe_svg.render((lon0, 0.0, t, R, R, R), marks=MARKS)
        land = re.search(r'class="gl-land" d="([^"]*)"', svg)
        marks = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
            r'data-mark="(\w+)"[^>]*cx="(-?\d+)" cy="(-?\d+)"', svg)}
        want[f"t{t}_lon{lon0}"] = {"land": _norm_path(land.group(1) if land else ""),
                                   "marks": marks}

    # Concatenation is embed_globe's job and it already knows the two traps —
    # unresolved imports and duplicate top-level consts. Doing it again here by
    # hand reproduced the second one and the module silently failed to define
    # itself, which is how a parity check reports a renderer that never ran.
    import embed_globe

    seen: dict[str, tuple[str, str]] = {}
    bundle: list[str] = []
    for name in ("geo/projection.js", "geo/worlddata.js", "globe/render-svg.js"):
        src = embed_globe.strip_module_syntax(
            (ROOT / "assets" / name).read_text(encoding="utf-8"))
        src, bad = embed_globe.dedupe_top_consts(name, src, seen)
        if bad:
            return bad
        bundle.append(src)
    render_src = "\n".join(bundle)
    modules = ""

    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    reg = json.loads(REGIONS.read_text(encoding="utf-8"))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto("about:blank")
        page.set_content("<div id=h></div>")
        page.add_script_tag(content=modules + "\n" + render_src
                            + "\nself.__r = { decode, createSvgRenderer };")
        # Raw: the JavaScript below carries a regex with \s in it, which Python
        # reads as an invalid escape and has warned about since 3.12. It is a
        # warning today and a SyntaxError later, printed on every run of this
        # check in the meantime.
        got = page.evaluate(r"""(payload) => {
          const data = self.__r.decode(payload.topo, payload.reg);
          const out = {};
          for (const c of payload.cases) {
            const svg = document.createElementNS(
              'http://www.w3.org/2000/svg', 'svg');
            const land = document.createElementNS(
              'http://www.w3.org/2000/svg', 'path');
            land.setAttribute('class', 'gl-land');
            svg.appendChild(land);
            for (const m of payload.marks) {
              const cEl = document.createElementNS(
                'http://www.w3.org/2000/svg', 'circle');
              cEl.setAttribute('class', 'gl-mark');
              cEl.dataset.mark = m.id;
              cEl.dataset.lon = String(m.lon);
              cEl.dataset.lat = String(m.lat);
              cEl.dataset.w = String(m.weight);
              svg.appendChild(cEl);
            }
            document.getElementById('h').appendChild(svg);
            try {
              const rend = self.__r.createSvgRenderer(svg, data);
              rend.draw({lon0: c.lon0, lat0: 0, t: c.t, R: payload.R,
                         cx: payload.R, cy: payload.R, zoom: 1}, {});
            } catch (e) { return {__error: String(e && e.stack || e)}; }
            const marks = {};
            for (const el of svg.querySelectorAll('.gl-mark')) {
              marks[el.dataset.mark] =
                [el.getAttribute('cx'), el.getAttribute('cy')];
            }
            out[c.key] = {
              land: (land.getAttribute('d') || '')
                .replace(/\s*([MLZ])\s*/g, '$1').trim(),
              marks,
            };
            svg.remove();
          }
          return out;
        }""", {"topo": topo, "reg": reg, "R": R, "cases": keyed,
               "marks": MARKS})
        browser.close()

    if got.get("__error"):
        return [f"the JS renderer threw: {got['__error'][:300]}"]
    errors, seen_div = [], set()
    for key, expect in want.items():
        m = got.get(key, {}).get("land")
        if not m:
            errors.append(f"{key} land: the JS renderer drew nothing")
        else:
            why = _path_diff(expect["land"], m)
            if why and (key, "land") in KNOWN_RENDERER_DIVERGENCE:
                seen_div.add((key, "land"))
            elif why:
                errors.append(f"{key} land: {why}")
        for mid, (px, py) in sorted(expect["marks"].items()):
            js = got.get(key, {}).get("marks", {}).get(mid)
            if js is None:
                errors.append(f"{key} mark {mid}: the JS renderer placed nothing")
            elif abs(int(js[0]) - int(px)) > 1 or abs(int(js[1]) - int(py)) > 1:
                errors.append(f"{key} mark {mid}: Python at ({px}, {py}), "
                              f"JS at ({js[0]}, {js[1]})")
    for div in sorted(KNOWN_RENDERER_DIVERGENCE - seen_div):
        errors.append(f"{div[0]} {div[1]}: recorded as a known divergence but "
                      f"the renderers agree — fixed? remove it from "
                      f"KNOWN_RENDERER_DIVERGENCE so the next one is caught")
    return errors[:8]


def check_viewbox_extent(golden):
    """Every projected sample sits inside the extent the static renderer would
    compute. inspect_layout --deliverable gates on a drawing clipped by its own
    viewBox, and the globe's limb sits exactly on that edge."""
    errors = []
    for vi, (lon0, lat0, t, R, cx, cy) in enumerate(_views(golden)):
        xs, ys = [], []
        for lon in range(-180, 181, 5):
            for lat in range(-90, 91, 5):
                x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
                if vis:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            errors.append(f"view {vi}: nothing is visible")
            continue
        span_x, span_y = max(xs) - min(xs), max(ys) - min(ys)
        if span_x > 2 * R + 1e-6 or span_y > 2 * R + 1e-6:
            errors.append(f"view {vi}: projected extent {span_x:.3f}x{span_y:.3f} "
                          f"exceeds the {2 * R:.0f} the renderer reserves")
    return errors


# ── the port ──────────────────────────────────────────────────────────────────
def check_port(golden):
    """Evaluate the JS module over the golden grid in headless Chromium.

    Playwright is imported here, never at module scope, so --python-only stays
    usable on a machine that has no browser — which is every CI runner this
    repository has.
    """
    if not JS.exists():
        return [f"{JS.relative_to(ROOT)} is missing; the port cannot be checked"]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so the JS port was NOT verified. "
                "pip install playwright && playwright install chromium, or run "
                "with --python-only and say the port is unverified."]

    source = JS.read_text(encoding="utf-8")
    views = golden["views"]
    samples = golden["samples"]
    script = """
    (payload) => {
      const { views, samples } = payload;
      const out = [];
      for (const s of samples) {
        const v = views[s[0]];
        const r = self.__globe.project(s[1], s[2], v);
        out.push([r.x, r.y, r.visible]);
      }
      const rt = [];
      for (const s of samples) {
        const v = views[s[0]];
        const r = self.__globe.project(s[1], s[2], v);
        if (!r.visible) { rt.push(null); continue; }
        rt.push(self.__globe.invert(r.x, r.y, v));
      }
      return { out, rt };
    }
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto("about:blank")
        page.add_script_tag(content=source.replace("export function", "function")
                            + "\nself.__globe = { project, invert, splitAtSeam };")
        result = page.evaluate(script, {"views": views, "samples": samples})
        browser.close()

    errors = []
    for (vi, lon, lat, px, py, pvis), (jx, jy, jvis) in zip(samples, result["out"]):
        if abs(jx - px) > TOLERANCE or abs(jy - py) > TOLERANCE:
            errors.append(f"view {vi} ({lon}, {lat}): python ({px:.9f}, {py:.9f}) "
                          f"vs js ({jx:.9f}, {jy:.9f})")
        if bool(jvis) != bool(pvis):
            errors.append(f"view {vi} ({lon}, {lat}): visible python {pvis} "
                          f"vs js {jvis}")
        if len(errors) > 12:
            errors.append("... further mismatches suppressed")
            break
    for (vi, lon, lat, _, _, pvis), back in zip(samples, result["rt"]):
        if not pvis:
            continue
        # Longitude is undefined at a pole: every meridian meets there, so a
        # round trip cannot preserve the one the sample happened to carry. The
        # Python half excludes the poles from its grid for the same reason; this
        # half reads the full golden grid and has to exclude them here.
        if abs(lat) == 90:
            continue
        if back is None:
            errors.append(f"view {vi} ({lon}, {lat}): js invert returned null "
                          f"for a visible point")
            break
        lon0, lat0, t = views[vi]["lon0"], views[vi]["lat0"], views[vi]["t"]
        # Same limb allowance as the Python half, and for the same reason: the
        # inverse is ill-conditioned where the forward derivative diverges.
        bound = (ROUND_TRIP_LIMB
                 if abs(gp.cos_c(lon, lat, lon0, lat0)) < LIMB_BAND
                 else ROUND_TRIP)
        # And the same injectivity allowance: mid-unroll an occluded point comes
        # back as its occluder, which is correct, so only the exact cases bind.
        if t not in (0.0, 1.0) and gp.cos_c(lon, lat, lon0, lat0) < gp.cos_c(
                back["lon"], back["lat"], lon0, lat0) - 1e-9:
            continue
        dlon = abs(((back["lon"] - lon + 180) % 360) - 180)
        if dlon > bound or abs(back["lat"] - lat) > bound:
            errors.append(f"view {vi} ({lon}, {lat}): js round-trip to "
                          f"({back['lon']:.9f}, {back['lat']:.9f})")
            break
    return errors


def _python_arc(flat, quantum):
    n = len(flat) // 2
    x, y = flat[0], flat[1]
    out = [(x / quantum, y / quantum)]
    for i in range(1, n):
        x += flat[i * 2]
        y += flat[i * 2 + 1]
        out.append((x / quantum, y / quantum))
    return out


def _python_rings(topo):
    """-> {code: (total ring points, total |signed area|)} the way the generator
    means them to assemble."""
    q = topo["quantum"]
    arcs = [_python_arc(a, q) for a in topo["arcs"]]
    out = {}
    for country in topo["countries"]:
        points, area = 0, 0.0
        for refs in country["rings"]:
            ring: list[Any] = []
            for idx in refs:
                arc = arcs[idx if idx >= 0 else ~idx]
                seq = arc if idx >= 0 else arc[::-1]
                ring.extend(seq[1:] if ring else seq)
            if len(ring) > 3:
                if abs(ring[0][0] - ring[-1][0]) > 1e-12 or abs(ring[0][1] - ring[-1][1]) > 1e-12:
                    ring.append(ring[0])
                points += len(ring)
                area += abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
                                for i in range(len(ring) - 1)) / 2.0)
        out[country["a"]] = (points, area)
    return out


def check_decoder():
    """The topology decoder, in the browser, against the Python that wrote it.

    Two things a JS-side assertion alone could not catch, so both sides are
    compared: the decoded point count against the arc lengths in the file, and
    the ring geometry against what build_worldmap intended. A decoder that
    dropped every junction point would still produce closed rings.
    """
    for path in (JS_DATA, TOPOLOGY, REGIONS):
        if not path.exists():
            return [f"{path.relative_to(ROOT)} is missing"]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so the decoder was NOT verified."]

    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    expect_points = sum(len(a) // 2 for a in topo["arcs"])
    q = topo["quantum"]
    # Ground truth for the two things a point count and a bounding box cannot
    # see, because both are order-insensitive: whether junction duplicates were
    # dropped, and whether backward arc references were actually reversed. A
    # ring assembled without reversing holds exactly the same points in a
    # scrambled order, so its bbox is identical and only its area is not.
    expect_rings = _python_rings(topo)

    script = """
    (payload) => {
      const d = self.__data.decode(payload.topo, payload.regions);
      const points = d.arcs.reduce((n, a) => n + a.length, 0);
      const closed = {};
      for (const code of ['USA', 'CHN', 'DEU', 'RUS']) {
        const rings = self.__data.ringsOf(code, d);
        closed[code] = rings.length > 0 && rings.every(
          r => r.length > 3
            && Math.abs(r[0][0] - r[r.length - 1][0]) < 1e-9
            && Math.abs(r[0][1] - r[r.length - 1][1]) < 1e-9);
      }
      let outOfRange = 0;
      for (const a of d.arcs) {
        for (const [lon, lat] of a) {
          if (lon < -180.001 || lon > 180.001 || lat < -90.001 || lat > 90.001) {
            outOfRange += 1;
          }
        }
      }
      const de = self.__data.ringsOf('DEU', d)[0];
      const shape = {};
      for (const code of payload.codes) {
        let pts = 0;
        let area = 0;
        for (const r of self.__data.ringsOf(code, d)) {
          pts += r.length;
          let a = 0;
          for (let i = 0; i < r.length - 1; i += 1) {
            a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1];
          }
          area += Math.abs(a / 2);
        }
        shape[code] = [pts, area];
      }
      return {
        points, closed, outOfRange, shape,
        countries: d.countries.size,
        regionOfDEU: d.regionOf.get('DEU'),
        regionOfUSA: d.regionOf.get('USA'),
        unmapped: [...d.countries.keys()].filter(c => !d.regionOf.has(c)),
        deuBbox: [Math.min(...de.map(p => p[0])), Math.min(...de.map(p => p[1])),
                  Math.max(...de.map(p => p[0])), Math.max(...de.map(p => p[1]))],
      };
    }
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto("about:blank")
        page.add_script_tag(content=JS_DATA.read_text(encoding="utf-8")
                            .replace("export function", "function")
                            + "\nself.__data = { decode, ringsOf };")
        r = page.evaluate(script, {"topo": topo,
                                   "regions": json.loads(
                                       REGIONS.read_text(encoding="utf-8")),
                                   "codes": sorted(expect_rings)})
        browser.close()

    errors = []
    if r["points"] != expect_points:
        errors.append(f"decoded {r['points']} points, the file holds "
                      f"{expect_points}")
    for code, ok in r["closed"].items():
        if not ok:
            errors.append(f"ringsOf({code}) did not return closed rings")
    if r["outOfRange"]:
        errors.append(f"{r['outOfRange']} decoded coordinates fall outside "
                      f"(-180..180, -90..90); the delta decode or the quantum "
                      f"({q}) is wrong")
    if r["countries"] != len(topo["countries"]):
        errors.append(f"decoded {r['countries']} countries, the file holds "
                      f"{len(topo['countries'])}")
    if r["unmapped"]:
        errors.append(f"no region for {r['unmapped'][:6]}")
    if r["regionOfDEU"] != "europe" or r["regionOfUSA"] != "north-america":
        errors.append(f"region index is wrong: DEU={r['regionOfDEU']}, "
                      f"USA={r['regionOfUSA']}")
    # Germany is roughly 5.9..15.0 E, 47.3..55.1 N. A decoder that swapped the
    # axes or lost the sign lands nowhere near it, and a bbox test says so in
    # one number where a screenshot would take a person.
    w, s_, e, n = r["deuBbox"]
    if not (5.0 < w < 7.0 and 46.5 < s_ < 48.0 and 14.0 < e < 16.0 and 54.0 < n < 56.0):
        errors.append(f"Germany decodes to bbox {r['deuBbox']}, which is not "
                      f"where Germany is")
    # The region bbox assertion lived here until 0.1.396, when decode() stopped
    # building that index: its consumer was the hit-test prefilter, which died
    # with pickRegion. The registry index the decoder still owes is asserted
    # above, at regionOfDEU / regionOfUSA.

    bad_count, bad_area = [], []
    for code, (pts, area) in sorted(expect_rings.items()):
        got = r["shape"].get(code)
        if not got:
            bad_count.append(f"{code}: no rings")
            continue
        if got[0] != pts:
            bad_count.append(f"{code}: {got[0]} ring points, expected {pts}")
        if area > 0 and abs(got[1] - area) > max(1e-6, area * 1e-9):
            bad_area.append(f"{code}: ring area {got[1]:.6f}, expected "
                            f"{area:.6f}")
    if bad_count:
        errors.append(f"ring point counts differ for {len(bad_count)} "
                      f"countries — junction duplicates kept, or arcs dropped: "
                      f"{bad_count[0]}")
    if bad_area:
        errors.append(f"ring areas differ for {len(bad_area)} countries — a "
                      f"backward arc reference was not reversed, which leaves "
                      f"the same points in a scrambled order: {bad_area[0]}")
    return errors


def check_clip_invariants():
    """Five properties of the spherical clip, each with a way to fail.

    These exist because the clip had none. Every globe check before 0.1.389
    measured emitted MARKUP, so a closure that was wrong but well-formed — which
    is every closure this release fixes — read as clean. A path is not a proof
    that the polygon behind it is the right polygon.

    Written against the real topology rather than a synthetic ring, because the
    cases that broke were Antarctica, Russia and Oceania: rings that wrap the
    world, contain a pole, or leave and re-enter the cap more than once.
    """
    import globe_svg

    topo, _reg, arcs = globe_svg._load()
    rings = []
    for code in ("ATA", "RUS", "AUS", "ZAF", "BRA", "CAN", "IDN", "NZL"):
        country = next((c for c in topo["countries"] if c["a"] == code), None)
        if country is None:
            return [f"{code} is not in the topology; this check names its own "
                    f"fixtures and one of them has gone"]
        for ring in globe_svg._rings_of(country, arcs):
            rings.append((code, ring))

    errors = []
    for lon0, lat0 in ((0.0, 0.0), (-170.0, 0.0), (-170.0, 20.0),
                       (17.0, 40.0), (100.0, -30.0)):
        for t in (0.0, 0.25, 0.5, 0.75, 0.9):
            for code, ring in rings:
                out = gp.clip_to_cap(ring, lon0, lat0, t, 2.0)
                inside = [gp.cos_c(lo, la, lon0, lat0) >= -t for lo, la in ring]
                where = f"{code} lon0={lon0} t={t}"

                # 1 and 2. The clip is the identity on a ring the cap contains
                # and empty on one it excludes. Both were true by accident
                # before; neither was ever asserted.
                if all(inside) and out != [list(ring)]:
                    errors.append(f"{where}: wholly visible, and the clip did "
                                  f"not return it unchanged")
                if not any(inside) and out:
                    errors.append(f"{where}: wholly hidden, and the clip "
                                  f"returned {len(out)} ring(s)")
                for k, r in enumerate(out):
                    # 3. Closed, or it is not a polygon.
                    if r[0] != r[-1]:
                        errors.append(f"{where} ring {k}: not closed")
                    # 4. Every point visible. A closure that leaves the cap is
                    # the fill spilling across it, which is the reported defect.
                    worst = min(gp.cos_c(lo, la, lon0, lat0) for lo, la in r)
                    if worst < -t - 1e-6:
                        errors.append(
                            f"{where} ring {k}: a point sits at cos_c={worst:.6f}, "
                            f"outside the cap at -t={-t:.3f} — the closure left "
                            f"the visible region")
                    # 5. Winding survives the clip. If it does not, the arc was
                    # walked the wrong way, which is the whole defect.
                    #
                    # Read a failure here carefully before believing it: per
                    # signed_area's own docstring the measure is only valid well
                    # below a hemisphere, and a clipped ring that closes the long
                    # way round a cap larger than one can legitimately exceed it.
                    # No ring in this topology does at any t tested here. If one
                    # ever fails, establish which side is wrong before changing
                    # either — weakening this check to make it pass would remove
                    # the only assertion that the direction rule is applied.
                    if gp.signed_area(ring) > 0 and gp.signed_area(r) <= 0:
                        errors.append(f"{where} ring {k}: an outer ring came "
                                      f"back wound as a hole")
                # 7. A CLIP CAN ONLY REMOVE AREA. This is the check that would
                # have caught the defect the eye found and the six above did
                # not: a closure that walks the whole cap instead of the arc it
                # needs returns a closed path whose every point lies on or
                # inside the cap and whose winding is intact, so it satisfies
                # all of them — and paints Antarctica over the entire disc.
                # Convention 8 in CLAUDE.md, demonstrated on the check that
                # exists to enforce it.
                area_in = abs(gp.signed_area(ring))
                area_out = sum(abs(gp.signed_area(r)) for r in out)
                if area_out > area_in + 1e-9:
                    errors.append(
                        f"{where}: the clip returned {area_out:.4f} sr from an "
                        f"input of {area_in:.4f} sr — a clip removes area, so a "
                        f"closure walked further round the cap than it should")

                # 6. A ring the cap actually cut comes back with points ON the
                # cap — that is what closing along it means. Without this, a
                # clip that silently dropped its closure and returned only the
                # interior runs would satisfy every check above.
                if out and any(inside) and not all(inside):
                    on_cap = sum(
                        1 for r in out for lo, la in r
                        if abs(gp.cos_c(lo, la, lon0, lat0) + t) < 1e-9)
                    if on_cap < 2:
                        errors.append(
                            f"{where}: the cap cut this ring and {on_cap} point(s) "
                            f"of the result lie on the cap — the closure is missing")
    return errors




def check_regionmap_frame():
    """The map component's frame holds its own contract.

    Four properties, each of which the first delivered demo lacked somewhere:
    the ink fits the declared viewBox; every drawn region carries a label AT its
    anchor (the registry fields nothing read until regionmap_svg.py); every
    class the frame emits has a binding in tokens/region-palette.css, so no
    document can get a black map by including the frame and the tokens; and the
    aria vocabulary is name-with-VALUE where a value exists, name-with-state
    only where none does.
    """
    import regionmap_svg

    errors = []
    states = {"europe": {"state": "live", "value": 63}, "north-america": "partial"}
    for lon0 in (0.0, 150.0):
        svg = regionmap_svg.render(lon0=lon0, states=states)
        where = f"lon0={lon0:g}"
        m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', svg)
        if not m:
            errors.append(f"{where}: no viewBox emitted")
            continue
        vx, vy, vw, vh = (float(g) for g in m.groups())
        xs, ys = [], []
        for d in re.findall(r'\sd="([^"]+)"', svg):
            for xy in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", d):
                xs.append(float(xy[0]))
                ys.append(float(xy[1]))
        if min(xs) < vx or max(xs) > vx + vw or min(ys) < vy or max(ys) > vy + vh:
            errors.append(f"{where}: ink outside the declared viewBox")

        drawn = {m2.group(1) for m2 in
                 re.finditer(r'class="rg rg-([a-z-]+)[^"]*"[^>]*d="[^"]*[ML]', svg)}
        labelled = set(re.findall(r'data-region-label="([a-z-]+)"', svg))
        for rid in sorted(drawn - labelled):
            errors.append(f"{where}: region {rid} is drawn and carries no label — "
                          f"hue separates neighbours at a glance; text carries "
                          f"identity (design-rules section 1c)")

        css = (ROOT / "tokens" / "region-palette.css").read_text(encoding="utf-8")
        for rid in sorted(drawn):
            if f".rg-{rid} " not in css:
                errors.append(f"{where}: the frame emits rg-{rid} and "
                              f"tokens/region-palette.css binds no fill to it — "
                              f"that region renders in the UA default")

        if 'aria-label="Europe, 63"' not in svg:
            errors.append(f"{where}: a region with a value does not speak it — "
                          f"expected aria-label=\'Europe, 63\'")
        if 'aria-label="North America, partial"' not in svg:
            errors.append(f"{where}: a region with only a state does not fall "
                          f"back to it")
    return errors





def check_trade_layers():
    """The two-layer map states the bloc, not the drawing decision.

    A map of OVERLAPPING regions cannot fill by membership: Canada is in USMCA
    and in CPTPP, and a fill picks one. So the trade registry carries two lists
    and the frame draws both — `members`, the derived disjoint partition, as
    fill; `full`, the real membership, as a stroke-only overlay hidden until a
    reader selects the bloc. Four things have to hold or the map lies:

    1. the base partition is DISJOINT — no country fills twice, or one of the
       two fills is invisible under the other and the map has a hidden claim;
    2. every base member is a real member (`members` subset of `full`);
    3. the label counts `full`. This is the one a reader can be wrong about:
       eight members across these blocs have no shape at 110m — Malta,
       Singapore, Bahrain, five African island states — so a count taken from
       what got drawn says 26 for the EU. The count is a fact about the bloc;
    4. no overlay renders before it is asked for. The static frame is what
       prints with JavaScript off, and every bloc outlined at once is noise.
    """
    import regionmap_svg

    reg_path = ROOT / "assets" / "vectors" / "regions-trade.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    errors = []

    owner: dict[str, str] = {}
    for r in reg["regions"]:
        for code in r["members"]:
            if code in owner:
                errors.append(f"{code} fills for both {owner[code]} and {r['id']}; "
                              f"the base layer must be a partition — one country, "
                              f"one fill, or the map has a claim it cannot show")
            owner[code] = r["id"]
        extra = sorted(set(r["members"]) - set(r["full"]))
        if extra:
            errors.append(f"{r['id']}: {', '.join(extra)} fills the map and is not "
                          f"in the bloc's membership")
        if r["count"] != len(r["full"]):
            errors.append(f"{r['id']}: count says {r['count']}, membership has "
                          f"{len(r['full'])}")

    svg = regionmap_svg.render(lon0=150.0, regions_path=str(reg_path))
    for r in reg["regions"]:
        m = re.search(rf'data-region-label="{r["id"]}"[^>]*>(.*?)</text>', svg, re.S)
        if not m:
            errors.append(f"{r['id']}: drawn and unlabelled")
            continue
        printed = re.search(r'class="rg-label-n">(\d+)<', m.group(1))
        if not printed:
            errors.append(f"{r['id']}: the label prints no membership count")
        elif int(printed.group(1)) != r["count"]:
            errors.append(f"{r['id']}: the label says {printed.group(1)} and the "
                          f"bloc has {r['count']} members — a count taken from the "
                          f"shapes that happened to draw, not from the bloc")

    # Every member is nameable from the package alone. A panel is the intended
    # consumer of `full`, and a panel that can name 50 of 55 prints a list
    # shorter than the count above it — the same defect one layer down.
    topo = json.loads((ROOT / "assets/vectors/world-110m.json").read_text("utf-8"))
    nameable = ({c["a"] for c in topo["countries"]}
                | {n["id"] for n in reg.get("nodes", [])}
                | set(reg.get("names", {})))
    for r in reg["regions"]:
        lost = sorted(set(r["full"]) - nameable)
        if lost:
            errors.append(f"{r['id']}: nothing in the package names "
                          f"{', '.join(lost)}, so a panel built from this "
                          f"registry lists fewer members than the count claims")

    overlaid = set(re.findall(r'data-overlay="([a-z]+)"', svg))
    expected = {r["id"] for r in reg["regions"]
                if sorted(r["full"]) != sorted(r["members"])}
    for rid in sorted(expected - overlaid):
        errors.append(f"{rid}: its membership differs from its fill and it has no "
                      f"overlay, so no reader can ever see the difference")
    for el in re.findall(r'<path class="rg-outline[^>]*>', svg):
        if 'display="none"' not in el:
            ov = re.search(r'data-overlay="([a-z]+)"', el)
            if ov is None:
                raise ValueError(f"rg-outline path carries no data-overlay: {el}")
            rid = ov.group(1)
            errors.append(f"{rid}: its overlay renders in the static frame; "
                          f"overlays are what a click reveals, and all of them at "
                          f"once is every border on the map drawn twice")
    return errors


def check_ink_is_what_is_painted():
    """A drawing's measured ink stops at the edge of what the viewport paints.

    inspect_layout measures an SVG by getBBox(), which is the union of the
    children IN USER SPACE and knows nothing about the viewport. An SVG with a
    viewBox clips at its own edges, so anything outside is not painted — and
    the globe's plate carries a drop-shadow whose filter region inflates that
    bbox by a tenth of the viewBox in every direction. About 50 CSS px at a
    figure's size, which collided with the paragraph above the figure and
    spilled past the footer below it: two GATING findings on a document where
    nothing was out of place, and the gate exists to say a document is not
    shippable.

    Measured here rather than in inspect_layout because a check that guards a
    measurement cannot be the measurement. The planted case is the general
    property rather than the particular bug: a circle drawn far larger than the
    viewBox that frames it. A filter region is one way geometry lands outside a
    viewport and an oversized shape is another, and the clamp answers both.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so the ink clamp was NOT checked."]

    doc = """<!doctype html><meta charset=utf-8>
      <style>body{margin:0}svg{width:400px;height:400px;display:block}</style>
      <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="90"/></svg>"""
    js = """() => {
      const e = document.querySelector('svg');
      const r = e.getBoundingClientRect(), bb = e.getBBox(), m = e.getScreenCTM();
      return {box: [r.left, r.top, r.right, r.bottom],
              ink: [bb.x * m.a + m.e, bb.y * m.d + m.f,
                    (bb.x + bb.width) * m.a + m.e, (bb.y + bb.height) * m.d + m.f]};
    }"""
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 500, "height": 500})
        page.set_content(doc)
        page.wait_for_timeout(120)
        got = page.evaluate(js)
        browser.close()

    box, ink = got["box"], got["ink"]
    if not (ink[0] < box[0] - 1 or ink[1] < box[1] - 1
            or ink[2] > box[2] + 1 or ink[3] > box[3] + 1):
        errors.append(
            "the planted case no longer overflows: a filtered shape inside a "
            "clipping viewBox reported ink within its element box, so this "
            "check is measuring nothing. Either the browser changed how a "
            "filter region enters getBBox, or the case needs rewriting")

    src = (ROOT / "scripts" / "inspect_layout.py").read_text(encoding="utf-8")
    if "Math.max(r.top, bb.y * m.d + m.f)" not in src:
        errors.append(
            "inspect_layout's inkBox does not clamp getBBox to the element's "
            "own rect, so filter regions and any other geometry the viewport "
            "clips are measured as painted — the false collision and false "
            "content spill of 0.1.400")
    return errors


def check_globe_layers():
    """The bloc fills partition the land and the city labels never overlap.

    Two layers arrived together and each can fail silently in a way markup
    looks fine through.

    THE FILLS. Routing the land through a registry means every country ring is
    clipped once and lands in one bucket. If a country reached two buckets the
    upper fill would simply cover the lower one and the map would carry a claim
    no reader could see; if it reached none it would vanish from a figure that
    still drew its neighbours. So: every drawable member fills under its bloc,
    no code is claimed twice, and the leftover path is non-empty.

    THE LABELS. A name on a sphere collides where the projection crowds, and
    two labels that overlap render as one unreadable word. The placement pass
    drops rather than nudges precisely so this is decidable: no two PLACED
    boxes may intersect, at any rotation. Swept over eight rotations, because
    the crowding is different at every one — which is the lesson 0.1.399 cost.
    """
    import globe_svg
    from geo_frame import LABEL_LIMB_COS, place_city_labels

    reg_path = ROOT / "assets" / "vectors" / "regions-trade.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    cities = [
        {"lon": 103.82, "lat": 1.35, "n": "Singapore"},
        {"lon": 114.17, "lat": 22.32, "n": "Hong Kong"},
        {"lon": 114.06, "lat": 22.54, "n": "Shenzhen"},
        {"lon": 4.48, "lat": 51.92, "n": "Rotterdam"},
        {"lon": 9.99, "lat": 53.55, "n": "Hamburg"},
        {"lon": 2.35, "lat": 48.86, "n": "Paris"},
        {"lon": -0.13, "lat": 51.51, "n": "London"},
        {"lon": -74.01, "lat": 40.71, "n": "New York"},
    ]
    R = globe_svg.DEFAULT_R
    errors = []

    svg = globe_svg.render((103.8, 12.0, 0.0, R, R, R),
                           regions_path=str(reg_path), cities=cities)
    claimed: dict[str, str] = {}
    for m in re.finditer(r'data-bloc="([a-z]+)" data-members="([^"]*)"', svg):
        for code in m.group(2).split():
            if code in claimed:
                errors.append(f"{code} fills under both {claimed[code]} and "
                              f"{m.group(1)}; one of the two is painted over "
                              f"and the figure carries a claim nobody can see")
            claimed[code] = m.group(1)
    for r in reg["regions"]:
        missing = sorted(set(r["members"]) - set(claimed))
        if missing:
            errors.append(f"{r['id']}: {', '.join(missing)} is a drawable "
                          f"member and reached no path")
    rest = re.search(r'<path class="gl-land" d="([^"]*)"', svg)
    if not rest or len(rest.group(1)) < 100:
        errors.append("routing the land through the registry emptied gl-land; "
                      "the countries in no bloc stopped being drawn")

    # The far-side rule is decidable here; the OVERLAP rule is not. An
    # arithmetic check would rebuild the boxes from the same constants the
    # placer used and read its own arithmetic back — setting the padding to
    # zero left such a check green while labels visibly merged. Overlap is
    # measured in a browser, in check_city_labels_do_not_collide below, off
    # the glyphs themselves.
    for lon0 in range(0, 360, 45):
        pts = []
        for city in cities:
            px, py, vis = gp.unrolled(city["lon"], city["lat"], float(lon0),
                                      12.0, 0.0, R, R, R)
            pts.append((city["n"], px, py, vis))
        for name, _x, _y, _a, drawn in place_city_labels(pts, R, R, R, R * 0.026):
            src = next(c for c in cities if c["n"] == name)
            if drawn and gp.cos_c(src["lon"], src["lat"], float(lon0), 12.0) < 0:
                errors.append(f"lon0={lon0}: {name} is on the far side and its "
                              f"label is drawn")

    if 'rotate(-23.4393' not in svg:
        errors.append("no label carries the counter-rotation, so every name on "
                      "this globe is set at the obliquity and the reader tips "
                      "their head to read it")
    if LABEL_LIMB_COS <= 0:
        errors.append("LABEL_LIMB_COS is not positive, so a bloc label is only "
                      "hidden once it has left the disc entirely")
    return errors


def check_city_labels_do_not_collide():
    """No two drawn city names overlap, measured off the rendered glyphs.

    The companion to check_globe_layers, and separate from it on purpose: the
    placement pass decides overlap from an ESTIMATED text width, so a check
    that estimates the same way proves only that the code agrees with itself.
    Setting the padding constant to zero left exactly such a check green while
    "Paris" and "Hamburg" rendered as one word. This one asks the browser for
    each label's own box.

    Swept over eight rotations because the crowding is different at every one.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so label collision was NOT checked."]
    import globe_svg

    cities = [
        {"lon": 4.48, "lat": 51.92, "n": "Rotterdam"},
        {"lon": 9.99, "lat": 53.55, "n": "Hamburg"},
        {"lon": 2.35, "lat": 48.86, "n": "Paris"},
        {"lon": -0.13, "lat": 51.51, "n": "London"},
        {"lon": 4.40, "lat": 51.22, "n": "Antwerp"},
        {"lon": 103.82, "lat": 1.35, "n": "Singapore"},
        {"lon": 114.17, "lat": 22.32, "n": "Hong Kong"},
        {"lon": 114.06, "lat": 22.54, "n": "Shenzhen"},
    ]
    R = globe_svg.DEFAULT_R
    css = ("body{margin:0}svg{width:900px;height:900px;display:block}"
           ".gl-city{font-family:sans-serif;font-weight:500}")
    js = """() => {
      const out = [];
      for (const el of document.querySelectorAll('.gl-city')) {
        if (el.getAttribute('display') === 'none') continue;
        const b = el.getBoundingClientRect();
        if (b.width < 1) continue;
        out.push([el.dataset.cityLabel, b.left, b.top, b.right, b.bottom]);
      }
      return out;
    }"""
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 950, "height": 950})
        for lon0 in range(0, 360, 45):
            svg = globe_svg.render((float(lon0), 12.0, 0.0, R, R, R), cities=cities)
            page.set_content(f"<!doctype html><meta charset=utf-8>"
                             f"<style>{css}</style>{svg}")
            page.wait_for_timeout(90)
            boxes = page.evaluate(js)
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                        ov_w = min(a[3], b[3]) - max(a[1], b[1])
                        errors.append(
                            f"lon0={lon0}: {a[0]} and {b[0]} are both drawn and "
                            f"their rendered glyphs overlap by {ov_w:.0f}px — "
                            f"they read as one word")
        browser.close()
    return errors


def check_trade_lanes():
    """A lane is the shortest path, it is clipped like everything else, and
    every signal on it has a code behind it.

    THE GEOMETRY. great_circle is asserted against the thing it claims to be:
    every sample must lie on the unit sphere, and the path must be no longer
    than any other path between the same two ends. The second is the whole
    claim of this treatment — that the drawing IS the shortest route rather
    than a picture of one — so it is checked by comparing against a detour
    through a third point, which is longer for every non-degenerate triple.

    THE CLIPPING. A lane runs over the far side of the Earth for most of its
    length and none of that may be drawn. Lanes go through _project_ring, which
    culls at the limb, so this asserts the property rather than the plumbing: at
    a rotation where both ends are behind the globe, the lane draws nothing.

    THE FIELD. A signal with no code behind it is decoration, and
    references/brand.md forbids decoration outright. So: no signals are emitted
    without codes, every signal names a lane that exists, and every signal's
    code index is inside the list it indexes.
    """
    import globe_svg
    from geo_frame import great_circle, great_circle_route

    errors = []

    # On the sphere, and shortest.
    for a, b in (((121.47, 31.23), (4.48, 51.92)),
                 ((103.82, 1.35), (-118.24, 33.74)),
                 ((-46.63, -23.55), (139.69, 35.69)),
                 ((0.0, 89.0), (0.0, -89.0))):
        pts = great_circle(a, b, 48)

        def vec(lon, lat):
            return (math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
                    math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
                    math.sin(math.radians(lat)))

        # COPLANAR WITH THE ENDS AND THE CENTRE. "On the unit sphere" is not the
        # test — every (lon, lat) pair is on the sphere by construction, so an
        # arithmetic mean of the two ENDPOINTS' coordinates passes it while
        # tracing a rhumb line that is not the shortest path at all. A great
        # circle is the intersection of the sphere with a plane through its
        # centre, and that is a property linear interpolation does not have.
        va, vb = vec(*a), vec(*b)
        nrm = (va[1] * vb[2] - va[2] * vb[1],
               va[2] * vb[0] - va[0] * vb[2],
               va[0] * vb[1] - va[1] * vb[0])
        nlen = math.sqrt(sum(c * c for c in nrm))
        if nlen > 1e-9:
            worst = max(abs(sum(x * y for x, y in zip(nrm, vec(lo, la)))) / nlen
                        for lo, la in pts)
            if worst > 1e-9:
                errors.append(
                    f"great_circle {a}->{b} leaves the plane through its two "
                    f"ends and the centre by {worst:.4f} — it is some other "
                    f"curve between the same points, and a lane's whole claim "
                    f"is that it is the shortest one")
        if pts[0] != tuple(a) and abs(pts[0][0] - a[0]) > 1e-6:
            errors.append(f"great_circle {a}->{b} does not start at its origin")

        def arc(p, q):
            return math.acos(max(-1.0, min(1.0, gp.cos_c(p[0], p[1], q[0], q[1]))))

        direct = arc(a, b)
        for via in ((0.0, 0.0), (30.0, 45.0), (-150.0, -20.0)):
            if arc(a, via) + arc(via, b) < direct - 1e-9:
                errors.append(f"a detour through {via} is shorter than the lane "
                              f"{a}->{b}, so the drawing is not the claim")

    # A globe may carry lanes and NO codes — scenery with routes on it — and
    # both checks below render exactly that, so a break in the signal layer's
    # guard surfaces here as a crash rather than as its own message. Named
    # once so it reads as one property with two witnesses.
    def render_lanes(view, links_):
        try:
            return globe_svg.render(view, links=links_)
        except Exception as exc:                   # noqa: BLE001
            errors.append(f"a globe with lanes and no codes raised "
                          f"{type(exc).__name__}; the signal layer must skip "
                          f"itself when there is nothing for a signal to carry")
            return None

    # CONTINUOUS IN LONGITUDE. atan2 returns (-180, 180], so a lane crossing the
    # antimeridian steps 355 degrees between two points five degrees apart —
    # and densify, which interpolates linearly in longitude, fills that gap by
    # sweeping the whole world. The lane closes into a ring around the globe.
    # Every Pacific route did this and coplanarity could not see it: the samples
    # are all still on the right great circle, they are just written in a
    # representation that jumps.
    for a, b in (((-118.24, 33.74), (151.21, -33.87)),
                 ((139.69, 35.69), (-74.01, 40.71)),
                 ((151.21, -33.87), (-79.38, 43.65)),
                 ((103.82, 1.35), (-118.24, 33.74))):
        pts = great_circle(a, b, 48)
        worst = max(abs(pts[i + 1][0] - pts[i][0]) for i in range(len(pts) - 1))
        if worst > 90.0:
            errors.append(
                f"the lane {a}->{b} jumps {worst:.0f} degrees of longitude "
                f"between adjacent samples; densify interpolates straight "
                f"through that and the lane draws as a ring around the globe")

    # A route through chokepoints is one continuous ring, not several.
    route = great_circle_route([(121.47, 31.23), (100.5, 2.5), (43.4, 12.6),
                                (32.55, 30.0), (-5.6, 35.95), (4.48, 51.92)], 12)
    worst = max(abs(route[i + 1][0] - route[i][0]) for i in range(len(route) - 1))
    if worst > 90.0:
        errors.append(f"a route through waypoints jumps {worst:.0f} degrees at "
                      f"a leg joint; the unwrap has to carry across the joint "
                      f"or the seam reappears once per waypoint")
    for i in range(len(route) - 1):
        if route[i] == route[i + 1]:
            errors.append("a route repeats a point at a leg joint, so the "
                          "waypoint is drawn twice and any dash pattern stalls")
            break

    # NO LANE DRAWS LONGER THAN ITS OWN ARC, and this is the assertion that
    # matters. It took two wrong ones to reach.
    #
    # The first measured each lane's drawn WIDTH against the disc. That can
    # never fail: every path is clipped to the visible cap, so its extent is
    # bounded by the disc by construction. It reported "no ring" about a figure
    # full of them.
    #
    # The second — continuity of the ring the emitter builds, above — is real,
    # but it guards the ring only where it is constructed. split_at_seam
    # re-expresses longitudes relative to lon0 AFTERWARDS, and returned a part
    # spanning 376 degrees for seventeen degrees of route.
    #
    # A lane's projected length cannot exceed R times its angular length. A
    # lane sweeping the world exceeds it several times over, whatever caused
    # the sweep and wherever in the pipeline it happened.
    R = globe_svg.DEFAULT_R
    for ri, route in enumerate((
            [(121.47, 31.23), (103.82, 1.35)],
            [(-118.24, 33.74), (151.21, -33.87)],
            [(121.47, 31.23), (120.90, 20.50), (100.50, 2.50), (43.40, 12.60),
             (32.55, 29.95), (-5.60, 35.95), (4.48, 51.92)],
            [(4.48, 51.92), (-79.55, 8.95), (-118.24, 33.74)])):
        pts = great_circle_route(route)
        bound = R * sum(
            math.acos(max(-1.0, min(1.0, gp.cos_c(p[0], p[1], q[0], q[1]))))
            for p, q in zip(pts, pts[1:]))
        for lon0 in range(-180, 180, 15):
            lk = {"id": f"r{ri}", "a": list(route[0]), "b": list(route[-1]),
                  "via": [list(v) for v in route[1:-1]], "w": 0.8}
            frame = render_lanes((float(lon0), 12.0, 0.0, R, R, R), [lk])
            if frame is None:
                break
            got = re.search(r'<path class="gl-link"[^>]*d="([^"]*)"', frame)
            if not got or not got.group(1).strip():
                continue
            drawn = 0.0
            for run in got.group(1).split("M")[1:]:
                pp = [tuple(float(v) for v in q.split())
                      for q in run.split("L") if q.strip()]
                drawn += sum(math.dist(x, y) for x, y in zip(pp, pp[1:]))
            if bound > 0 and drawn > bound * 1.15:
                errors.append(
                    f"lane {ri} at lon0={lon0} draws {drawn:.0f} units against "
                    f"an arc of {bound:.0f} — {drawn / bound:.1f} times its own "
                    f"length, so part of it is sweeping the globe instead of "
                    f"following the route")
                break

    # Clipped at the limb like every other ring.
    link = {"id": "x", "a": [4.48, 51.92], "b": [9.99, 53.55], "w": 1.0}
    far = render_lanes((-170.0, -40.0, 0.0, R, R, R), [link])
    m = re.search(r'<path class="gl-link"[^>]*d="([^"]*)"', far) if far else None
    if m and m.group(1).strip():
        errors.append("a lane whose whole length is on the far side still drew "
                      f"{len(m.group(1))} characters of path")

    # Every signal is one real code on one real lane.
    links = [link, {"id": "y", "a": [103.82, 1.35], "b": [-118.24, 33.74], "w": 0.4}]
    codes = ["382499", "391732", "392051"]
    svg = globe_svg.render((60.0, 12.0, 0.0, R, R, R), links=links, codes=codes)
    lane_ids = set(re.findall(r'data-link="([^"]*)"', svg))
    sigs = re.findall(r'data-sig-link="([^"]*)" data-t="([\d.]+)" data-code="(\d+)"', svg)
    if not sigs:
        errors.append("lanes and codes were both supplied and no signal was "
                      "emitted; the runtime mutates markup and never makes it, "
                      "so nothing can ever move on this figure")
    for lid, t, ci in sigs:
        if lid not in lane_ids:
            errors.append(f"a signal rides lane {lid!r}, which is not on the frame")
        if not 0.0 <= float(t) < 1.0:
            errors.append(f"a signal starts at t={t}, outside the lane")
        if int(ci) >= len(codes):
            errors.append(f"a signal points at code {ci} of {len(codes)}")
    bare = render_lanes((60.0, 12.0, 0.0, R, R, R), links)
    if bare is not None and bare.count("gl-sig"):
        errors.append("signals were emitted with no codes to carry — a mark "
                      "with nothing behind it is decoration, which "
                      "references/brand.md forbids outright")
    return errors


# check_lanes_after_rotation lived here and was REMOVED the same hour it was
# written. It booted the runtime, let the globe autorotate, and measured each
# lane's drawn length against its arc — and reverting the repair it was meant
# to guard left it green. The routes it chose never reached a rotation where
# splitAtSeam bit, so it asserted nothing while reading like a guarantee, which
# is the exact failure this file has now recorded three times: a check that
# cannot fail is worse than no check, because it is also a claim.
#
# What DID verify the runtime repair was measuring the shipped demo over thirty
# samples of real rotation: worst drawn-to-arc ratio 0.99 against a 1.15 ceiling.
# That is a measurement, not a gate, and it is recorded in the release notes as
# one. The gap is real and named: assets/globe/ and the Python emitter are a
# hand-maintained port, the golden grid holds the projection maths between them,
# and nothing yet holds the ring-clipping pipeline on the JavaScript side.


def check_land_lines():
    """Three weights, one classification, and every arc in exactly one of them.

    The shared-arc topology is what makes this possible without new data: an
    arc between two countries is stored once and referenced by both, so its
    number of users says whether it is a coast. Three properties:

    1. the three sets PARTITION the arcs — every arc drawn once, none twice,
       none missing. A doubled arc is a doubled stroke and reads as a heavier
       line for no reason; a missing one is a gap in a coastline;
    2. a coast is an arc used by ONE country, and there are 548 of them. If
       this drifts, either the topology changed or the rule did, and both are
       worth stopping for;
    3. WITHOUT a registry there are no bloc edges at all. A globe carrying no
       blocs must not draw a boundary between blocs it does not have.

    Also asserted: the frame's arc lists match the classification, because the
    runtime trusts them and re-derives nothing.
    """
    import globe_svg
    from geo_frame import classify_arcs

    topo = json.loads((ROOT / "assets/vectors/world-110m.json").read_text("utf-8"))
    reg = json.loads((ROOT / "assets/vectors/regions-trade.json").read_text("utf-8"))
    owner = {c: r["id"] for r in reg["regions"] for c in r["members"]}
    errors = []

    all_arcs = set(range(len(topo["arcs"])))
    for label, own in (("no registry", {}), ("trade blocs", owner)):
        coast, edge, border = classify_arcs(topo, own)
        union = coast | edge | border
        if len(coast) + len(edge) + len(border) != len(union):
            errors.append(f"{label}: an arc is in more than one land layer, so "
                          f"it is stroked twice and reads heavier than its rule")
        missing = all_arcs - union
        if missing:
            errors.append(f"{label}: {len(missing)} arcs are in no layer and "
                          f"are simply not drawn — that is a gap in a coastline")
        if len(coast) != 548:
            errors.append(f"{label}: {len(coast)} coast arcs, expected 548. "
                          f"Either the topology changed or the one-user rule "
                          f"did; both are worth stopping for")
        if not own and edge:
            errors.append(f"no registry: {len(edge)} bloc edges on a globe that "
                          f"has no blocs")

    R = globe_svg.DEFAULT_R
    svg = globe_svg.render((0.0, 12.0, 0.0, R, R, R),
                           regions_path=str(ROOT / "assets/vectors/regions-trade.json"))
    coast, edge, border = classify_arcs(topo, owner)
    for cls, want in (("gl-coast", coast), ("gl-bloc-edge", edge),
                      ("gl-border", border)):
        m = re.search(rf'class="{cls}" data-arcs="([^"]*)"', svg)
        if not m:
            errors.append(f"the frame carries no {cls} layer")
            continue
        got = {int(v) for v in m.group(1).split()}
        if got != want:
            errors.append(f"{cls}: the frame lists {len(got)} arcs and the "
                          f"classification says {len(want)}; the runtime draws "
                          f"from this list and re-derives nothing, so a frame "
                          f"that disagrees with it is what ships")
    return errors


def check_rotation_is_continuous():
    """A clipped ring never encloses more of the sphere than the ring it came
    from. This is the closure family's invariant, asserted directly.

    Four releases of this family were each found by a reader watching the
    figure — a lens of daylight, a lane closing into a ring, a country painted
    over the whole disc for six frames once a minute — and each fix shipped
    without a check that would have caught it.

    THE FIRST VERSION OF THIS CHECK SAMPLED THE SYMPTOM and was useless. It
    rendered a revolution at 0.6-degree steps and compared adjacent frames,
    which is a fine description of what a reader sees and a bad test: the
    Venezuela defect occupies about two tenths of a degree, so the sweep
    stepped over it and reported ok with the bug reinstated. Sampling for a
    narrow event needs a step finer than the event, and nobody knows how narrow
    the next one is.

    So this asserts the PROPERTY instead. Clipping adds a cap arc, so a
    legitimate result is a little larger than its input — by the sliver between
    a chord and the limb, never by a hemisphere. A wrong-way closure encloses
    about 6.3 steradians whatever the input was. Every ring in the topology, at
    72 rotations, and the honest worst case measures 0.0000 sr of excess.
    """
    from geo_frame import _load, _rings_of

    # TESTED AT THE TANGENCY, NOT ON A GRID. This was the second thing the
    # check got wrong: a five-degree sweep of lon0 misses a defect two tenths
    # of a degree wide just as surely as the frame sweep did. The failure is
    # not distributed over the rotation — it happens when the ring GRAZES the
    # limb, and that longitude is computable from the ring itself. So each ring
    # is put on its own limb and nudged across it.
    topo, _reg, arcs = _load()
    lat0 = 10.0
    worst = (0.0, None, None)
    for country in topo["countries"]:
        for ring in _rings_of(country, arcs):
            source = abs(gp.signed_area(ring))
            lon = sum(p[0] for p in ring) / len(ring)
            lat = sum(p[1] for p in ring) / len(ring)
            # cos_c = 0 puts the ring's centre exactly on the limb. Solve for
            # the lon0 that does it, then walk a degree either side in
            # twentieths, which is finer than any window seen so far.
            import math as _m
            num = -_m.sin(_m.radians(lat0)) * _m.sin(_m.radians(lat))
            den = _m.cos(_m.radians(lat0)) * _m.cos(_m.radians(lat))
            base = []
            if den and abs(num / den) <= 1.0:
                d = _m.degrees(_m.acos(num / den))
                base = [lon - d, lon + d]
            tests = [b + k * 0.05 for b in base for k in range(-20, 21)]
            for lon0 in tests + [float(v) for v in range(0, 360, 15)]:
                for piece in gp.clip_to_cap(ring, float(lon0), lat0, 0.0, 2.0):
                    excess = abs(gp.signed_area(piece)) - source
                    if excess > worst[0]:
                        worst = (excess, country["a"], lon0)
    if worst[0] > gp.CLOSURE_SLACK:
        return [f"{worst[1]} at lon0={worst[2]} clips to a polygon enclosing "
                f"{worst[0]:.3f} steradians more than the ring it came from. A "
                f"clip adds a cap arc, not a hemisphere: this closure went the "
                f"wrong way round the cap, and on a rotating globe the country "
                f"is painted over the whole disc for as long as it lasts"]
    return []


def check_runtime_closure():
    """The tangent guard is in the JAVASCRIPT, not only in the Python.

    This check exists because the repair for it shipped in
    scripts/geo_projection.py, the emitter's sweep went green, the release note
    was written — and every frame after the first is drawn by
    assets/geo/projection.js, which had no guard. A country grazing the limb
    went on being painted over the whole disc, six frames per revolution, with
    the fix sitting in a language the runtime does not run. The reader saw no
    change at all.

    That is the SECOND time a repair has reached one side of this
    hand-maintained port. 0.1.405 is the first and has its own paragraph saying
    so, which is exactly why a paragraph is not a check.

    So: drive the RUNTIME through the tangency and measure what it draws. Not
    the emitter, which has been green throughout both failures.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so the runtime closure was NOT checked."]
    import globe_svg

    R = globe_svg.DEFAULT_R
    reg = str(ROOT / "assets" / "vectors" / "regions-trade.json")
    # The rotations that put a ring on the limb. 20.3 is Venezuela's, measured;
    # the others sweep for any neighbour of it.
    svg = globe_svg.render((0.0, 10.0, 0.0, R, R, R), regions_path=reg)
    runtime = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "embed_globe.py")],
        capture_output=True, text=True, check=True).stdout

    js = """(lon0) => {
      const svg = document.querySelector('svg.gl');
      const g = window.__lumiGlobes && window.__lumiGlobes[0];
      if (!g) return null;
      g.pin(lon0);
      let total = 0;
      for (const el of svg.querySelectorAll('.gl-land, .gl-rg')) {
        total += (el.getAttribute('d') || '').length;
      }
      return total;
    }"""
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 700, "height": 700})
        page.set_content(
            f'<!doctype html><meta charset=utf-8>'
            f'<style>svg.gl{{width:600px;height:600px}}</style>'
            f'<div class="fig" data-globe>{svg}</div>{runtime}')
        page.wait_for_timeout(500)
        page.evaluate("window.__lumiGlobes = window.lumiGlobes")
        prev = None
        worst: tuple[float, float | None] = (0, None)
        lon = 19.0
        while lon < 22.0:
            cur = page.evaluate(js, lon)
            if cur is None:
                errors.append("the runtime did not register a globe; this check "
                              "measured nothing")
                break
            if prev is not None and abs(cur - prev) > worst[0]:
                worst = (abs(cur - prev), lon)
            prev = cur
            lon += 0.05
        browser.close()

    # 900 characters, the same ceiling the emitter's own honest change sits far
    # below. A wrong-way closure moved 2,060.
    if worst[0] > 900:
        errors.append(
            f"the RUNTIME's land geometry changes by {worst[0]} characters "
            f"between two frames 0.05 degrees apart, at lon0={worst[1]:.2f}. "
            f"The tangent guard is in scripts/geo_projection.py and not in "
            f"assets/geo/projection.js, so the emitter is green and every "
            f"frame a reader sees is not")
    return errors


def check_earth_is_tilted():
    """The earth layer carries the tilt, at the obliquity, leaning right.

    Unasserted from 0.1.397, when the tilt shipped, until the owner asked for
    the other lean and nothing failed either way. Three things are worth
    holding and one is not:

      * the group EXISTS and wraps the drawing — without it there is no tilt at
        all and the figure silently reverts to a flat disc;
      * the angle is the obliquity, not a number someone liked the look of.
        The tropics are drawn at OBLIQUITY_DEG and the terminator is computed
        from it, so a tilt that disagrees puts the axis at odds with the two
        circles that exist to show where it points;
      * the sign carries the pole to the RIGHT, which is the owner's call and
        the kind of thing that gets flipped back by accident.

    What is NOT asserted is the flattening: at 1/298 it is 3.4 units in a
    2000-unit frame and no rendering test can see it. It is in the transform
    because it is true, not because it shows.
    """
    import globe_svg
    from geo_frame import OBLIQUITY_DEG, earth_transform

    errors = []
    svg = globe_svg.render((0.0, 0.0, 0.0, globe_svg.DEFAULT_R,
                            globe_svg.DEFAULT_R, globe_svg.DEFAULT_R))
    m = re.search(r'<g class="gl-earth" transform="([^"]+)"', svg)
    if not m:
        return ["the frame has no gl-earth group, so the drawing is untilted "
                "and the tropics describe an axis that is not there"]
    rot = re.search(r"rotate\(([-\d.]+)\)", m.group(1))
    if not rot:
        errors.append(f"gl-earth carries no rotate(): {m.group(1)}")
        return errors
    angle = float(rot.group(1))
    # 1e-3, not 1e-6: the transform is written with %g, which keeps six
    # significant digits, so 23.4392811 reaches the markup as 23.4393. That
    # rounding is 1.9e-5 degrees. The tolerance still catches the mistake worth
    # catching — a tilt written as the 23.5 everyone quotes, which misses by
    # 0.061 and puts the axis at odds with tropics drawn from the real value.
    if abs(abs(angle) - OBLIQUITY_DEG) > 1e-3:
        errors.append(f"the earth is tilted {abs(angle):.4f} degrees and the "
                      f"obliquity is {OBLIQUITY_DEG} — the tropics and the "
                      f"terminator are drawn from the obliquity, so this axis "
                      f"disagrees with the circles that show where it points")
    if angle < 0:
        errors.append(f"rotate({angle:g}) leans the north pole LEFT; SVG "
                      f"rotates clockwise on a positive angle and this figure "
                      f"leans right")
    # And the string the check reads is the one the emitter writes.
    if earth_transform(1000.0, 1000.0) not in svg:
        errors.append("the frame's transform is not the one earth_transform "
                      "builds, so this check is reading a coincidence")
    return errors


def check_field_has_no_strangers():
    """A globe stating a field draws no point that is not in the field.

    The registry's four city-states are a PLACE layer: they exist because no
    shape can be filled for Singapore or Malta, and on the flat map that is
    their whole job. On a globe carrying marks they are a second point
    vocabulary at nearly the same radius, and the first delivered globe demo
    drew Singapore twice — once as a datum of weight 9, once as a place — with
    no way for a reader to tell which circle was the number.

    So: scenery may name places, a field must ask for them. Asserted in all
    three directions, because the interesting one is the default.
    """
    import globe_svg

    R = globe_svg.DEFAULT_R
    view = (103.8, 10.0, 0.0, R, R, R)
    marks = [{"lon": 103.82, "lat": 1.35, "weight": 9, "id": "sin"}]
    errors = []
    if 'class="gl-node"' in globe_svg.render(view, marks=marks):
        errors.append("a globe with a field drew the registry's place layer "
                      "unasked; a reader cannot tell a datum from a city")
    if 'class="gl-node"' not in globe_svg.render(view):
        errors.append("a globe with no field drew no places either — scenery "
                      "that names nothing is scenery that says nothing")
    if 'class="gl-node"' not in globe_svg.render(view, marks=marks, nodes=True):
        errors.append("--nodes did not restore the place layer over a field")

    # MARK_R_MIN is NOT asserted here. It rose in this release, but the
    # justification that first suggested itself — a pointer target — is false:
    # pick.js hits on a fixed 12 CSS px radius (WCAG 2.5.8) whatever the mark
    # is drawn at, so hover never depended on the drawn size. What the floor
    # actually governs is whether the smallest datum is legible, and that is a
    # judgement for the eye, not a number for a gate. Recorded so the next
    # reader does not add the check that looked obvious.
    return errors


def check_globe_frame():
    """The globe frame's own contract, measured in Python.

    Companion to check_far_side_hidden below, which needs a browser. Here:
    the mark radius rule is monotone and bounded, every mark carries the data
    the runtime re-projects from, and a far-side point is marked non-rendering
    at all.
    """
    import globe_svg

    R = globe_svg.DEFAULT_R
    marks = [{"lon": 103.8, "lat": 1.35, "weight": 9, "id": "sin", "label": "Singapore"},
             {"lon": -122.4, "lat": 37.8, "weight": 1, "id": "sf", "label": "SF"},
             {"lon": 13.4, "lat": 52.5, "weight": 0, "id": "ber", "label": "Berlin"}]
    errors = []
    for lon0 in (0.0, 103.8, -122.4):
        svg = globe_svg.render((lon0, 0.0, 0.0, R, R, R), marks=marks)
        where = f"lon0={lon0:g}"
        for m in marks:
            found = re.search(rf'data-mark="{m["id"]}"[^>]*>|data-mark="{m["id"]}"[^>]*/>', svg)
            if not found:
                errors.append(f"{where}: mark {m['id']} is not in the frame — the "
                              f"runtime mutates markup and never creates it, so a "
                              f"mark absent here can never rotate into view")
                continue
            el = found.group(0)
            for attr in ("data-lon", "data-lat", "data-w"):
                if attr not in el:
                    errors.append(f"{where}: mark {m['id']} carries no {attr}; "
                                  f"the runtime re-projects from these")
            far = gp.cos_c(m["lon"], m["lat"], lon0, 0.0) < 0
            if far and 'display="none"' not in el:
                errors.append(
                    f"{where}: mark {m['id']} is on the far side and is not "
                    f"marked display=\"none\" — it will be drawn inside the "
                    f"visible disc")
            if not far and 'display="none"' in el:
                errors.append(f"{where}: mark {m['id']} is visible and hidden")
        # The radius rule: monotone in weight, and inside its stated bounds.
        rs = [globe_svg.mark_radius(w, 9, R) for w in (0, 1, 4, 9)]
        if rs != sorted(rs):
            errors.append(f"the mark radius is not monotone in weight: {rs}")
        if rs[0] < R * globe_svg.MARK_R_MIN - 1e-9 or rs[-1] > R * globe_svg.MARK_R_MAX + 1e-9:
            errors.append(f"the mark radius leaves its bounds: {rs[0]:.2f}..{rs[-1]:.2f} "
                          f"against {R * globe_svg.MARK_R_MIN:.2f}..{R * globe_svg.MARK_R_MAX:.2f}")
    return errors


def check_far_side_hidden():
    """A far-side mark RENDERS NOTHING — measured in a browser, not read.

    This is the check whose absence let the drifting-dots defect ship. The
    frame said `hidden`, every gate in this package reads markup, and `hidden`
    reads correct in markup — but the HTML `hidden` attribute does not hide an
    SVG shape. A <circle hidden> computes display:inline and keeps its full
    box, so every point on the BACK of the sphere kept drawing at its
    orthographic position, which for a far-side point lands INSIDE the visible
    disc. Twelve dots slid across the geography on every frame of a shipped
    deliverable.

    So this one measures getBoundingClientRect().width and refuses to believe
    an attribute. Both the STATIC frame and the frame after the runtime has
    re-projected it, because the two write that attribute independently.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so far-side hiding was NOT checked."]
    import embed_globe
    import globe_svg

    R = globe_svg.DEFAULT_R
    marks: list[dict[str, Any]]
    marks = [{"lon": 103.8, "lat": 1.35, "weight": 5, "id": "sin"},
             {"lon": -122.4, "lat": 37.8, "weight": 5, "id": "sf"},
             {"lon": 13.4, "lat": 52.5, "weight": 5, "id": "ber"},
             {"lon": -46.6, "lat": -23.5, "weight": 5, "id": "sao"}]
    lon0 = 60.0
    svg = globe_svg.render((lon0, 0.0, 0.0, R, R, R), marks=marks)
    far = {m["id"] for m in marks if gp.cos_c(m["lon"], m["lat"], lon0, 0.0) < 0}
    if not far:
        return ["the fixture put no mark on the far side; the check would pass "
                "on nothing"]

    runtime = embed_globe.build()
    page_html = ("<!doctype html><meta charset=utf-8><body>"
                 f'<div id="f" data-globe>{svg}</div>{runtime}</body>')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(page_html)
        page.wait_for_timeout(300)
        boxes = page.evaluate("""() => {
          const out = {};
          for (const el of document.querySelectorAll('.gl-mark, .gl-node')) {
            const k = el.dataset.mark || el.dataset.node;
            const r = el.getBoundingClientRect();
            out[k] = [Math.round(r.width), Math.round(r.height)];
          }
          return out;
        }""")
        browser.close()

    errors = []
    for mid in sorted(far):
        box = boxes.get(mid)
        if box is None:
            errors.append(f"mark {mid} is missing from the rendered page")
        elif box[0] > 0 or box[1] > 0:
            errors.append(
                f"mark {mid} is on the FAR SIDE and still renders "
                f"{box[0]}x{box[1]}px — it is drawn inside the visible disc and "
                f"drifts across the geography as the globe turns")
    near = [m["id"] for m in marks if m["id"] not in far]
    for mid in near:
        box = boxes.get(mid)
        if not box or box[0] == 0:
            errors.append(f"mark {mid} is on the near side and renders nothing")
    return errors


def check_terminator_area():
    """The night side covers the fraction of the disc that geometry says.

    Closed form, so this is a real assertion and not a snapshot: a great circle
    whose pole sits at angular distance d from the view centre projects to an
    ellipse of semi-axes R and R|cos d|, which cuts the disc into a night part
    of exactly (1 - cos d) / 2. Measured by COUNTING PIXELS in a browser,
    because the two defects this check exists for were both well-formed
    polygons that no markup reader could fault:

      * the terminator ring is a hemisphere, the one radius at which
        signed_area's branch flips, and facing the antisolar point it lay
        exactly ON the limb — the clip then had to decide the winding of a
        curve coincident with the boundary it was being clipped against, and
        left a lens of daylight inside the night side;
      * cap_point returns unwrapped longitudes, so the ring stepped through a
        355-degree discontinuity once per circuit and densify interpolated
        straight through it, sweeping the whole world and closing into a second
        lens. The same failure densify has now had three times, always where a
        ring's longitude representation jumps and nothing tells the
        interpolator.

      * the antipode was computed by a two-branch expression whose western
        branch returned the sun's own longitude, so for every subsolar point in
        the western hemisphere the cap was drawn around the SUN and the figure
        shaded its daylight. Found by looking at a demo page showing Singapore
        midnight fully lit; invisible to this check, which held the sun at one
        eastern longitude and varied only the view centre.

    Before the first two fixes the worst error was 13.5%; the third was 87
    percentage points on a single frame. The lesson is in the case list below:
    a geometry with two inputs has to be swept along both.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["Playwright is not installed, so the terminator was NOT checked."]
    import geo_frame
    import globe_svg

    # TWO axes, and the check used to sweep one. The view centre moved across
    # nine positions while the sun stayed at a single eastern longitude, so the
    # antipode expression's western branch — which returned the sun's own
    # longitude, shading the daylight — was never once evaluated. Half of every
    # day was inverted and this check reported 0.08%. Hours now sweep a full
    # rotation, which is where a subsolar longitude goes negative.
    cases = []
    for lon0, lat0 in [(120.3, 23.45), (90.0, 10.0), (60.0, 0.0), (30.0, -10.0),
                       (0.0, -20.0), (-59.7, -23.45), (180.0, 0.0),
                       (-120.0, 40.0), (45.0, -60.0)]:
        cases.append((lon0, lat0, globe_svg.DEFAULT_SUN_UTC))
    for hour in range(0, 24, 3):
        cases.append((103.8, 10.0, f"2026-06-21T{hour:02d}:00:00"))
    # And a date either side of the solstice, so the declination's sign is
    # exercised too rather than pinned at its June extreme.
    for when in ("2026-12-21T04:00:00", "2026-03-20T22:00:00"):
        cases.append((103.8, 10.0, when))
    R = globe_svg.DEFAULT_R
    # The plate and the land take one colour, night another, so the disc is
    # what either painted and the ratio needs no assumption about the viewBox.
    css = ("body{margin:0;background:#fff}svg{width:500px;height:500px;display:block}"
           "*{fill:none;stroke:none}.gl-plate{fill:#f00}.gl-land{fill:#f00}"
           ".gl-night{fill:#00f}")
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for lon0, lat0, when in cases:
            sun = geo_frame.solar_position(datetime.datetime.fromisoformat(when))
            svg = globe_svg.render((lon0, lat0, 0.0, R, R, R), night=sun)
            page = browser.new_page(viewport={"width": 500, "height": 500})
            page.set_content(f"<!doctype html><meta charset=utf-8>"
                             f"<style>{css}</style>{svg}")
            page.wait_for_timeout(120)
            shot = page.screenshot()
            page.close()
            night, disc = _count_night(shot)
            if not disc:
                errors.append(f"lon0={lon0:g} lat0={lat0:g} at {when}: "
                              f"nothing drew")
                continue
            d = math.degrees(math.acos(max(-1.0, min(1.0,
                gp.cos_c(sun[0], sun[1], lon0, lat0)))))
            want = (1 - math.cos(math.radians(d))) / 2
            have = night / disc
            if abs(have - want) > TERMINATOR_AREA_TOLERANCE:
                errors.append(
                    f"lon0={lon0:g} lat0={lat0:g} at {when} (subsolar "
                    f"{sun[0]:.1f}): the sun is {d:.1f} degrees "
                    f"from the view centre, so night should cover {want:.1%} of "
                    f"the disc and it covers {have:.1%} — off by {have - want:+.1%}")
        browser.close()
    return errors


def _count_night(png_bytes):
    """-> (night pixels, disc pixels) from the two-colour render above.

    Pillow is optional here and its absence is reported by the caller as a
    failure to measure, never as a pass: a check that did not run is not a
    check that passed.
    """
    try:
        from PIL import Image
    except ImportError:
        return (0, 0)
    import io
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data")
              else im.getdata())
    night = sum(1 for r, _g, b in px if b > 150 and r < 120)
    day = sum(1 for r, _g, b in px if r > 150 and b < 120)
    return night, night + day

# (label, fn, needs_golden, suite, needs_browser). The suites follow the
# component split:
# `shared` is the projection core and the t-sweeps that guard 0.1.389's winding
# work — they outlive the products' pinned t — `globe` and `map` are each
# component's own contract. Default runs everything; CI's --python-only line is
# unchanged.
CHECKS: tuple[tuple[str, Callable[..., list[str]], bool, str, bool], ...] = (
    ("round trip", check_round_trip, True, "shared", False),
    ("poles are points", check_poles, True, "shared", False),
    ("limb culling", check_culling, True, "shared", False),
    ("seam splitting", check_seam, False, "shared", False),
    ("viewbox extent", check_viewbox_extent, True, "shared", False),
    ("static svg fits its viewbox", check_static_svg, False, "shared", False),
    ("no line across the flat map", check_seam_segments, False, "shared", False),
    ("the spherical clip holds its invariants", check_clip_invariants, False, "shared", False),
    ("the globe frame holds its contract", check_globe_frame, False, "globe", False),
    ("the earth is tilted, right, at the obliquity", check_earth_is_tilted, False, "globe", False),
    ("the globe's layers hold their contract", check_globe_layers, False, "globe", False),
    ("the land is drawn in three weights", check_land_lines, False, "globe", False),
    ("a revolution is continuous", check_rotation_is_continuous, False, "globe", False),
    ("the runtime closes its rings too", check_runtime_closure, False, "globe", True),
    ("a lane is the shortest path, and carries a code", check_trade_lanes, False, "globe", False),
    ("city names never overlap", check_city_labels_do_not_collide, False, "globe", True),
    ("a field draws no strangers", check_field_has_no_strangers, False, "globe", False),
    ("measured ink is painted ink", check_ink_is_what_is_painted, False, "shared", True),
    ("a far-side mark renders nothing", check_far_side_hidden, False, "globe", True),
    ("the night side covers what geometry says", check_terminator_area, False, "globe", True),
    ("the region map frame holds its contract", check_regionmap_frame, False, "map", False),
    ("the trade map states the bloc, not the drawing", check_trade_layers, False, "map", False),
)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--python-only", action="store_true",
                    help="skip the browser half; the port is then UNVERIFIED")
    ap.add_argument("--suite", choices=("shared", "globe", "map", "all"),
                    default="all",
                    help="which component's checks to run; shared is the "
                         "projection core both stand on")
    args = ap.parse_args(argv)

    if not GOLDEN.exists():
        print(f"FAIL  {GOLDEN.relative_to(ROOT)} is missing; "
              f"run scripts/build_worldmap.py")
        return 1
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))

    failed = 0
    skipped = []
    for label, fn, needs_golden, suite, needs_browser in CHECKS:
        if args.suite != "all" and suite != args.suite:
            continue
        # A browser check under --python-only is SKIPPED and named, not run and
        # failed. It reached CI as a failure once: "Playwright is not installed"
        # is a fact about the machine, and reporting a fact about the machine as
        # a defect in the code is the noise that teaches people to ignore a
        # gate. Named rather than silent, per this file's own posture.
        if needs_browser and args.python_only:
            skipped.append(label)
            continue
        try:
            errors = fn(golden) if needs_golden else fn()
        except Exception as exc:                       # noqa: BLE001
            errors = [f"the check itself raised {type(exc).__name__}: {exc}"]
        if errors:
            failed += 1
            print(f"FAIL  {label}")
            for e in errors[:8]:
                print(f"        {e}")
        else:
            print(f"ok    {label}")

    if args.python_only:
        for label in skipped:
            print(f"note  SKIPPED (--python-only, needs a browser): {label}")
        print(f"note  the JS port was NOT verified (--python-only); "
              f"{len(golden['samples'])} golden samples are waiting for it")
    elif args.suite == "map":
        # The map runtime never touches geometry, so there is no browser half
        # for it: nothing it does can disagree with the Python emitter.
        pass
    else:
        errors = check_port(golden)
        if errors:
            failed += 1
            print("FAIL  js port agrees with the python authority")
            for e in errors[:8]:
                print(f"        {e}")
        else:
            print(f"ok    js port agrees with the python authority on "
                  f"{len(golden['samples'])} samples")
        errors = check_renderer_parity()
        if errors:
            failed += 1
            print("FAIL  the two renderers agree")
            for e in errors[:6]:
                print(f"        {e}")
        else:
            print("ok    the two renderers agree")
        errors = check_decoder()
        if errors:
            failed += 1
            print("FAIL  js topology decoder")
            for e in errors[:8]:
                print(f"        {e}")
        else:
            print("ok    js topology decoder")

    if failed:
        print(f"\n{failed} of {len(CHECKS) + (0 if args.python_only else 2)} "
              f"globe checks failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
