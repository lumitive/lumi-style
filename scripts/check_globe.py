#!/usr/bin/env python3
"""Verify the globe maths, and that the JavaScript port agrees with it.

assets/globe/projection.js is a hand port of scripts/geo_projection.py. Nothing
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
import json
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import geo_projection as gp   # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "fixtures" / "globe-golden.json"
JS = ROOT / "assets" / "globe" / "projection.js"
JS_DATA = ROOT / "assets" / "globe" / "worlddata.js"
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

    Checked at both ends and the middle, in both forms, because the extent is
    computed per t and a viewBox correct at t=0 says nothing about t=1.
    """
    import globe_svg

    errors = []
    for form in ("field", "regions"):
        for t in (0.0, 0.5, 1.0):
            R = globe_svg.DEFAULT_R
            svg = globe_svg.render((0.0, 0.0, t, R, R, R), form=form)
            m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', svg)
            if not m:
                errors.append(f"{form} t={t}: no viewBox emitted")
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
                errors.append(f"{form} t={t}: the frame drew nothing")
                continue
            if min(xs) < vx or max(xs) > vx + vw or min(ys) < vy or max(ys) > vy + vh:
                errors.append(
                    f"{form} t={t}: ink spans x {min(xs):.1f}..{max(xs):.1f}, "
                    f"y {min(ys):.1f}..{max(ys):.1f} but the viewBox is "
                    f"{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f} — clipped")
            # Not the smallest margin: one tight side hides three loose ones,
            # and a square viewBox around a 2:1 flat map passes that test while
            # rendering at half the height its cell allows. Area is what
            # inspect_layout calls aspect mismatch, and it is the real defect.
            fill = ((max(xs) - min(xs)) * (max(ys) - min(ys))) / (vw * vh)
            if fill < FRAME_FILL_FLOOR:
                errors.append(
                    f"{form} t={t}: the ink fills {fill:.0%} of its viewBox "
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

    R = globe_svg.DEFAULT_R
    errors = []
    for form in ("field", "regions"):
        for t in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
            view = (0.0, 0.0, t, R, R, R)
            svg = globe_svg.render(view, form=form)
            half = R * (1 - t / 2)
            top, bottom = view[5] - half, view[5] + half
            on_pole_edge = lambda y: (abs(y - top) < R * 0.03      # noqa: E731
                                      or abs(y - bottom) < R * 0.03)
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
                    errors.append(f"{form} t={t}: a segment runs from "
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
                        f"{form} t={t}: a flat segment "
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
KNOWN_RENDERER_DIVERGENCE = set()


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
    # Keys are passed explicitly rather than built on each side. JavaScript
    # renders 0.0 as "0", so a key composed independently in both languages did
    # not match and every region reported as "drew nothing" — a parity check
    # failing on its own bookkeeping.
    cases = [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (0.0, -20.0)]
    keyed = [{"key": f"t{t}_lon{lon0}", "t": t, "lon0": lon0} for t, lon0 in cases]
    want = {}
    for t, lon0 in cases:
        svg = globe_svg.render((lon0, 0.0, t, R, R, R), form="regions")
        want[f"t{t}_lon{lon0}"] = {
            m.group(1): _norm_path(m.group(2))
            for m in re.finditer(r'data-region="([\w-]+)"[^>]*d="([^"]*)"', svg)}

    # Concatenation is embed_globe's job and it already knows the two traps —
    # unresolved imports and duplicate top-level consts. Doing it again here by
    # hand reproduced the second one and the module silently failed to define
    # itself, which is how a parity check reports a renderer that never ran.
    import embed_globe

    seen, bundle = {}, []
    for name in ("projection.js", "worlddata.js", "render-svg.js"):
        src = embed_globe.strip_module_syntax(
            (ROOT / "assets" / "globe" / name).read_text(encoding="utf-8"))
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
            for (const r of data.regions) {
              const p = document.createElementNS(
                'http://www.w3.org/2000/svg', 'path');
              p.setAttribute('data-region', r.id);
              svg.appendChild(p);
            }
            document.getElementById('h').appendChild(svg);
            try {
              const rend = self.__r.createSvgRenderer(svg, data);
              rend.draw({lon0: c.lon0, lat0: 0, t: c.t, R: payload.R,
                         cx: payload.R, cy: payload.R, zoom: 1}, {});
            } catch (e) { return {__error: String(e && e.stack || e)}; }
            const per = {};
            for (const p of svg.querySelectorAll('[data-region]')) {
              per[p.getAttribute('data-region')] =
                (p.getAttribute('d') || '').replace(/\s*([MLZ])\s*/g, '$1').trim();
            }
            out[c.key] = per;
            svg.remove();
          }
          return out;
        }""", {"topo": topo, "reg": reg, "R": R, "cases": keyed})
        browser.close()

    if got.get("__error"):
        return [f"the JS renderer threw: {got['__error'][:300]}"]
    errors, seen_div = [], set()
    for key, expect in want.items():
        for rid, n in sorted(expect.items()):
            m = got.get(key, {}).get(rid)
            if m is None:
                errors.append(f"{key} {rid}: the JS renderer drew nothing")
            else:
                why = _path_diff(n, m)
                if why and (key, rid) in KNOWN_RENDERER_DIVERGENCE:
                    seen_div.add((key, rid))
                elif why:
                    errors.append(f"{key} {rid}: {why}")
    for key in sorted(KNOWN_RENDERER_DIVERGENCE - seen_div):
        errors.append(f"{key[0]} {key[1]}: recorded as a known divergence but "
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
            ring = []
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
        bboxEurope: d.bboxOf.get('europe'),
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
    if not r["bboxEurope"]:
        errors.append("no bounding box for the europe region")

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
            c = math.acos(max(-1.0, min(1.0, -t)))
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


CHECKS = (
    ("round trip", check_round_trip, True),
    ("poles are points", check_poles, True),
    ("limb culling", check_culling, True),
    ("seam splitting", check_seam, False),
    ("viewbox extent", check_viewbox_extent, True),
    ("static svg fits its viewbox", check_static_svg, False),
    ("no line across the flat map", check_seam_segments, False),
    ("the spherical clip holds its invariants", check_clip_invariants, False),
)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--python-only", action="store_true",
                    help="skip the browser half; the port is then UNVERIFIED")
    args = ap.parse_args(argv)

    if not GOLDEN.exists():
        print(f"FAIL  {GOLDEN.relative_to(ROOT)} is missing; "
              f"run scripts/build_worldmap.py")
        return 1
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))

    failed = 0
    for label, fn, needs_golden in CHECKS:
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
        print(f"note  the JS port was NOT verified (--python-only); "
              f"{len(golden['samples'])} golden samples are waiting for it")
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
