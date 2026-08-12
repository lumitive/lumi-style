#!/usr/bin/env python3
"""Emit one static SVG frame of the LUMI globe — a field of marks on a sphere.

The globe half of the component split
(specs/2026-08-10-globe-map-split-design.md): a rotating orthographic globe
whose subject is a FIELD of marks, one per datum, intensity from the datum.
The flat region map is its own component now — scripts/render/regionmap_svg.py — and
this emitter no longer takes a `--form`: it emits the field frame, always at
the spherical geometry (the t the old one-figure design animated is pinned to 0
here; the shared projection core keeps the parameter and its checks).

This is the deliverable's renderer. A canvas is invisible to every gate this
package owns — d5_drawn_share counts a figure as drawn only if it holds an
<svg>, d5_figure_parity and d17_export_weight read markup, and inspect_layout
cannot see inside a canvas — so what ships in a document is SVG, and the
JavaScript runtime mutates this markup rather than replacing it.

    python3 scripts/render/globe_svg.py                                  # empty field
    python3 scripts/render/globe_svg.py --marks '[{"lon":103.8,"lat":1.35,"weight":3,"label":"Singapore"}]'
    python3 scripts/render/globe_svg.py --marks @marks.json --lon0 -170 --lat0 20

The mark contract: `[{lon, lat, weight, label?, id?}]`, weight >= 0. Radius
scales with the SQUARE ROOT of weight — area encodes quantity; a linear radius
inflates big values quadratically — normalised over the set so the largest mark
is readable and the smallest survives. The radius rule lives here and in the
canvas renderer, parity-held, not in tokens: CSS cannot size a canvas mark, and
a knob that binds one back end is a divergence wearing a token's clothes.

No literal colour appears here. Every shape carries a class and
`tokens/region-palette.css` ships the bindings, per design-rules.md section 1.

The viewBox is computed from the projected extent, never a fixed square.
inspect_layout --deliverable gates on a drawing clipped by its own viewBox, and
the globe's limb sits exactly on that edge; that defect is how the gate came to
exist.

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import math
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import sys
import sys as _bs_sys  # noqa: E402
from typing import Any

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import geo_projection as gp  # noqa: E402
from geo_frame import (  # noqa: E402,F401  (re-exported: render() and callers use them)
    CITY_EM_H,
    CITY_EM_W,
    CITY_GAP,
    DEFAULT_R,
    FLATTENING,
    GRATICULE,
    LABEL_LIMB_COS,
    LINK_R,
    OBLIQUITY_DEG,
    PAD,
    REGIONS,
    STEP_DEG,
    TOPOLOGY,
    _d,
    _guard,
    _load,
    _pole_close,
    _project_area,
    _project_ring,
    _r,
    _rings_of,
    arc_points,
    classify_arcs,
    earth_transform,
    extent,
    great_circle_route,
    link_weight_attrs,
    night_ring,
    place_city_labels,
    screen_to_tilt,
    solar_position,
    tilt_to_screen,
)

# A denser graticule than the 30 degrees the first cut used. The graticule is
# what makes a flat disc read as a sphere — it is the only cue that survives
# when the geography is quiet — and 15 degrees is where the convergence toward
# the poles becomes legible without the lines closing up at the limb.
GLOBE_GRATICULE = 15

# The default instant for the day/night terminator, in UTC. FIXED, not "now":
# a frame that changes every time it is generated cannot be byte-compared, and
# every generated artifact in this repository is. A document that wants its own
# moment passes --time.
ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
DEFAULT_SUN_UTC = "2026-06-21T04:00:00"

# The mark radius, as fractions of R. MIN is a floor (a datum must survive being
# small), MAX a ceiling (a mark is a point, not a region), and between them the
# square root of the normalised weight — area encodes quantity.
MARK_R_MIN = 0.011
MARK_R_MAX = 0.030


def mark_radius(weight, wmax, R):
    """Shared with render-canvas.js by value, held together by the parity check."""
    w = max(0.0, float(weight))
    u = math.sqrt(w / wmax) if wmax > 0 else 0.0
    return R * (MARK_R_MIN + (MARK_R_MAX - MARK_R_MIN) * u)


def _scaled(view, scale):
    """The same view at a different radius, concentric with the globe.

    unrolled already takes the centre, so a larger R alone gives a concentric
    sphere — no correction, and adding one pushes the drawing a full radius off
    the globe and out of the frame.
    """
    lon0, lat0, t, R, cx, cy = view
    return (lon0, lat0, t, R * scale, cx, cy)


def _upright(x, y):
    """Cancel the earth group's tilt for one element, about its own anchor.

    Every layer here lives inside `.gl-earth`, which is what makes the
    geography lean. Text has to lean back: a name set at 23 degrees is a name
    the reader tips their head for, and a figure that asks that of a label has
    stopped being a figure. The flattening is not cancelled — 3.4 units in 2000
    is nothing to a glyph, and undoing it would need a second transform to say
    so.
    """
    return f"rotate({-OBLIQUITY_DEG:g} {x:.1f} {y:.1f})"


def render(view, marks=None, night=None, nodes=False,
           regions_path=None, cities=None, links=None, codes=None):
    """-> the <svg class="gl"> element as a string.

    `view` is (lon0, lat0, t, R, cx, cy). t stays in the signature because the
    shared suite sweeps it — the winding guard from 0.1.389 outlives the pinned
    product — but the PRODUCT frame is t=0 and main() does not expose it.
    """
    topo, reg, arcs = _load(regions_path)
    lon0, lat0, t, R, cx, cy = view
    marks = marks or []
    cities = cities or []
    links = links or []
    codes = codes or []
    blocs = reg["regions"] if regions_path else []

    body = []
    # the ground the sphere sits on
    if t < 1.0:
        body.append(f'<circle class="gl-plate" cx="{_r(cx)}" cy="{_r(cy)}" '
                    f'r="{_r(R)}" opacity="{1 - t:.3f}"/>')

    grat: Any = []
    lat: float
    for lon in range(-180, 181, GLOBE_GRATICULE):
        grat.append(_d(_project_ring([(lon, la) for la in range(-90, 91, 3)], view), False))
    for lat in range(-90, 91, GLOBE_GRATICULE):
        if lat == 0:
            continue          # the equator is named below, not one line of many
        grat.append(_d(_project_ring([(lo, lat) for lo in range(-180, 181, 3)], view), False))
    grat = " ".join(g for g in grat if g)
    if grat:
        body.append(f'<path class="gl-graticule" d="{grat}"/>')

    # The three circles that are not graticule. They are where the Earth's tilt
    # shows up on its own surface: the tropics are the latitudes the sun reaches
    # overhead at the solstices, so they sit at exactly the obliquity used for
    # the tilt above, and the equator is the one line the reader can name.
    eq = _d(_project_ring([(lo, 0.0) for lo in range(-180, 181, 3)], view), False)
    if eq:
        body.append(f'<path class="gl-equator" d="{eq}"/>')
    trop: Any = []
    for lat in (OBLIQUITY_DEG, -OBLIQUITY_DEG):
        trop.append(_d(_project_ring([(lo, lat) for lo in range(-180, 181, 3)], view), False))
    trop = " ".join(x for x in trop if x)
    if trop:
        body.append(f'<path class="gl-tropic" d="{trop}"/>')

    # THE LAND, ROUTED. Without a registry every country goes into one path and
    # this is what it always was. With one, each country goes into its bloc's
    # path instead and the remainder keeps `gl-land` — the SAME total clipping
    # work, because a ring is clipped exactly once either way and only the
    # bucket it lands in changes. Membership is the registry's `members`, which
    # is already the disjoint base partition, so no country can be filled twice.
    #
    # The membership rides ON the element as data-members. The runtime redraws
    # these paths every frame and has no registry of its own; putting the codes
    # in the markup is how the flat map's per-instance registry idea reaches a
    # globe without shipping a second copy of anything.
    owner = {code: b["id"] for b in blocs for code in b["members"]}
    buckets: dict[Any, list[str]] = {b["id"]: [] for b in blocs}
    rest: list[str] = []
    for country in topo["countries"]:
        target = buckets.get(owner.get(country["a"]), rest)
        for ring in _rings_of(country, arcs):
            target.append(_d(_project_area(ring, view), True, view))
    for b in blocs:
        d = " ".join(x for x in buckets[b["id"]] if x)
        # `rg rg-<id>` is the SHIPPED region vocabulary, the same two classes
        # the flat map fills with, so one palette serves both figures and a
        # registry that coexists on a page cannot disagree with itself about
        # what colour a bloc is. `gl-rg` is the globe's own hook and carries
        # only what differs on a sphere.
        body.append(f'<path class="rg rg-{b["id"]} gl-rg" data-bloc="{b["id"]}" '
                    f'data-members="{" ".join(b["members"])}" d="{d}"/>')
    d = " ".join(x for x in rest if x)
    body.append(f'<path class="gl-land" d="{d}"/>')

    # THE LINEWORK, IN THREE WEIGHTS. The fills above carry no stroke; every
    # land line is drawn here instead, so a coastline, a boundary between two
    # trade blocs and a border inside one are three different marks rather than
    # the same mark three times.
    #
    # The arc indices ride in the markup because the runtime redraws these
    # every frame and must not re-derive which arc is which — see classify_arcs
    # in geo_frame.py for why that rule exists and what it cost to learn.
    coast, bloc_edge, border = classify_arcs(topo, owner)
    for cls, idxs in (("gl-border", border), ("gl-bloc-edge", bloc_edge),
                      ("gl-coast", coast)):
        if not idxs:
            continue
        order = sorted(idxs)
        d = " ".join(x for x in
                     (_d(_project_ring(arc_points(i, arcs), view), False)
                      for i in order) if x)
        body.append(f'<path class="{cls}" data-arcs="{" ".join(map(str, order))}" '
                    f'd="{d}"/>')

    # Night: the cap of the sphere the sun is not on. It goes through the same
    # clip every country goes through, so it comes back already cut at the limb.
    # Drawn OVER the land, under the marks — it is a lighting condition, not a
    # region, and a mark must stay readable in the dark.
    if night is not None:
        nd = " ".join(x for x in
                      [_d(_project_area(night_ring(*night), view, forward=True),
                          True, view)] if x)
        if nd:
            body.append(f'<path class="gl-night" d="{nd}" '
                        f'data-sun-lon="{night[0]:.3f}" data-sun-lat="{night[1]:.3f}"/>')

    # Every mark and node is in the DOM whether or not this frame shows it, with
    # its lat/lon on the element and visibility as an attribute. The runtime
    # mutates markup and never creates it, so a mark that rotates into view has
    # to already have somewhere to land.
    #
    # display="none", NOT the `hidden` attribute. `hidden` is an HTML attribute
    # and the UA stylesheet rule that acts on it does not reach an SVG shape: a
    # <circle hidden> computes display:inline and keeps its full bounding box.
    # So every far-side mark and node was still being drawn, at its orthographic
    # position — which for a point on the BACK of the sphere lands inside the
    # visible disc — and slid across the geography as the globe turned. That is
    # the drifting dots the owner reported, and nothing in this package could
    # see it: every gate reads markup, and `hidden` reads correct in markup.
    # display is a real SVG presentation attribute and needs no stylesheet, so
    # the JS-off frame hides them too.
    wmax = max((float(m.get("weight", 1.0)) for m in marks), default=1.0)
    for mark in marks:
        px, py, vis = gp.unrolled(mark["lon"], mark["lat"], lon0, lat0, t, R, cx, cy)
        w = float(mark.get("weight", 1.0))
        label = mark.get("label", "")
        extra = (f' data-mark="{html.escape(str(mark["id"]))}"' if "id" in mark else "")
        title = f"<title>{html.escape(label)}, {w:g}</title>" if label else ""
        attrs = (f'class="gl-mark"{extra} data-lon="{mark["lon"]:g}" '
                 f'data-lat="{mark["lat"]:g}" data-w="{w:g}" '
                 f'cx="{_r(px)}" cy="{_r(py)}" '
                 f'r="{mark_radius(w, wmax, R):.1f}"'
                 f'{"" if vis else " display=\"none\""}')
        body.append(f"<circle {attrs}>{title}</circle>" if title
                    else f"<circle {attrs}/>")

    # THE PLACE LAYER IS OPT-IN ONCE THERE IS A FIELD. regions.json carries
    # four city-states as points because no shape can be filled for them, and
    # on the flat map that is their whole reason to exist. On a globe whose
    # subject is a mark field they are a second point vocabulary at nearly the
    # same size — the first globe demo drew Singapore twice, once as a datum
    # of weight 9 and once as a place, and no reader could tell which circle
    # was the number. Scenery keeps them; a field has to ask.
    for node in (reg.get("nodes", []) if (nodes or not marks) else []):
        px, py, vis = gp.unrolled(node["lon"], node["lat"], lon0, lat0, t, R, cx, cy)
        body.append(f'<circle class="gl-node" data-node="{node["id"]}" '
                    f'data-lon="{node["lon"]:g}" data-lat="{node["lat"]:g}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{R * 0.017:.1f}"'
                    f'{"" if vis else " display=\"none\""}>'
                    f'<title>{html.escape(node["n"])}</title></circle>')

    # NO AXIS LINE. It was added in 0.1.404 to make the tilt legible and the
    # owner removed it one release later, correctly: this figure already
    # carries a graticule, an equator, two tropics, a terminator edge, eight
    # bloc borders and thirteen lanes, and a fourteenth line through the middle
    # of all that does not read as an axis — it reads as one more line. The
    # tilt is legible in the graticule for a reader who is looking for it, and
    # the sup text says 23.44 for one who is not. Recorded rather than deleted
    # silently: the reasoning that added it was sound and the answer was still
    # no, and the next person to notice the tilt is subtle should know that.

    # TRADE LANES, on the sphere. A great circle is the shortest path across a
    # sphere, so the drawing and the claim are one object — and because a lane
    # is just a ring, _project_ring gives it limb clipping, seam splitting and
    # far-side culling for free. A lane on the back of the Earth is not drawn
    # because there is nothing there to draw, which is the same reason a
    # coastline behind the globe is absent.
    #
    # Drawn OVER the land and UNDER the marks: a lane crosses geography and a
    # datum sits on top of everything.
    for link in links:
        a, b = tuple(link["a"]), tuple(link["b"])
        # `via` is the route's chokepoints, in order. A box from Shanghai to
        # Rotterdam does not cross Siberia — it goes Malacca, Bab-el-Mandeb,
        # Suez, Gibraltar, because those are the gaps in the land. Each leg is
        # still the shortest path, so the geometry stays honest at the scale it
        # is claimed at; what changes is that the claim is now a shipping lane
        # rather than a line on a sphere. WHICH straits a route uses is
        # editorial and belongs to the document, not to this package.
        route = [a] + [tuple(v) for v in link.get("via", [])] + [b]
        w, o = link_weight_attrs(link.get("w", 0.5))
        d = _d(_project_ring(great_circle_route(route), _scaled(view, LINK_R)), False)
        # EMITTED EVEN WHEN IT DRAWS NOTHING. The runtime mutates markup and
        # never creates it — the rule marks obey — so a lane whose whole length
        # is on the far side in THIS frame still needs somewhere to land when
        # the globe turns. Skipping it here meant a Los Angeles to Sydney lane
        # was absent from the document for good if the first frame happened not
        # to face the Pacific, which is the drifting-dots defect wearing a
        # different hat: the frame is a starting state, not a filter.
        body.append(f'<path class="gl-link" data-link="{html.escape(str(link.get("id", "")))}" '
                    f'data-route="{";".join(f"{x:g},{y:g}" for x, y in route)}" '
                    f'data-w="{float(link.get("w", 0.5)):.2f}" '
                    f'stroke-width="{w * R:.1f}" opacity="{o:.2f}" d="{d}"/>')

    # The hubs a lane runs between, drawn once each.
    for i, (hlon, hlat) in enumerate(sorted({tuple(lk[k]) for lk in links
                                             for k in ("a", "b")})):
        px, py, vis = gp.unrolled(hlon, hlat, lon0, lat0, t, R * LINK_R, cx, cy)
        body.append(f'<circle class="gl-hub" data-hub="{i}" '
                    f'data-lon="{hlon:g}" data-lat="{hlat:g}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{R * 0.010:.1f}"'
                    f'{"" if vis else " display=\"none\""}/>')

    # SIGNALS ARE EMITTED, NOT CREATED. The runtime mutates markup and never
    # makes it — the same rule marks obey — so a signal has to have somewhere to
    # land before it moves, and a document with JavaScript off shows the lanes
    # carrying codes rather than lanes carrying nothing.
    #
    # A heavier lane carries more of them, because traffic is the datum.
    if codes:
        n = 0
        for link in links:
            for k in range(2 if float(link.get("w", 0.5)) > 0.85 else 1):
                lid = html.escape(str(link.get("id", "")))
                body.append(
                    f'<g class="gl-sig" data-sig-link="{lid}" '
                    f'data-t="{(n * 0.37 + k * 0.5) % 1:.3f}" '
                    f'data-code="{n % len(codes)}">'
                    f'<circle r="{R * 0.0075:.1f}"/>'
                    f'<text font-size="{R * 0.020:.0f}">{html.escape(codes[n % len(codes)])}</text>'
                    f'</g>')
                n += 1

    # Named places. A city is not a mark: a mark's size is its datum and its
    # name lives in a title, while a city IS its name — so this layer carries
    # visible text, and text on a sphere collides in a way circles do not.
    #
    # THE DOT AND THE LABEL ARE HIDDEN SEPARATELY. A dot goes when its point
    # turns to the far side; a label goes when it would land on another label,
    # which happens near the limb where the projection crowds everything
    # together. A dot with no name still says a place is there, and that is
    # more honest than moving the name somewhere it does not point.
    # BLOC LABELS ARE PLACED FIRST and city labels give way to them. A bloc
    # label is anchored to a region and names the fill under it; a city label
    # names a dot and can be dropped without the dot losing meaning. So the one
    # that cannot move is drawn first and the one that can works around it.
    bsize = R * 0.030
    blabels = []
    for b in blocs:
        lon, lat = b["anchor"]
        px, py, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
        # Hidden well before the limb, not at it. A label whose anchor is 80
        # degrees out sits on geography squeezed to a sliver and trails its own
        # text off the edge of the disc, which is what AfCFTA did at every
        # rotation that put Africa near the left edge.
        sx, sy = tilt_to_screen(px, py, cx, cy)
        near = gp.cos_c(lon, lat, lon0, lat0) >= LABEL_LIMB_COS
        text = f'{b["abbr"]} {b["count"]} \u00b7 {b["pop_m"] / 1000:.2f}B'
        w = CITY_EM_W * bsize * len(text)
        h = CITY_EM_H * bsize
        blabels.append((b, px, py, vis and near,
                        (sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2)))

    csize = R * 0.026
    cpts = []
    for city in cities:
        px, py, vis = gp.unrolled(city["lon"], city["lat"], lon0, lat0, t, R, cx, cy)
        sx, sy = tilt_to_screen(px, py, cx, cy)
        cpts.append((city.get("n") or city.get("label", ""), px, py, vis, sx, sy))

    for city, (name, px, py, vis, _sx, _sy), lab in zip(
            cities, cpts, place_city_labels(
                [(n, sx, sy, v) for n, _x, _y, v, sx, sy in cpts],
                R, cx, cy, csize,
                reserved=[box for _b, _x, _y, shown, box in blabels if shown])):
        anchor, drawn = lab[3], lab[4]
        # The gap is horizontal ON SCREEN, so it is stated on screen and
        # converted — a plain +x here would run off at the obliquity.
        offx, offy = screen_to_tilt(
            (-1 if anchor == "end" else 1) * CITY_GAP * csize, 0.0)
        body.append(f'<circle class="gl-city-dot" data-city="{html.escape(name)}" '
                    f'data-lon="{city["lon"]:g}" data-lat="{city["lat"]:g}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{R * 0.0055:.1f}"'
                    f'{"" if vis else " display=\"none\""}>'
                    f'<title>{html.escape(name)}</title></circle>')
        body.append(f'<text class="gl-city" data-city-label="{html.escape(name)}" '
                    f'x="{_r(px + offx)}" y="{_r(py + offy + csize * 0.34)}" '
                    f'transform="{_upright(px + offx, py + offy)}" '
                    f'text-anchor="{anchor}" font-size="{csize:.0f}"'
                    f'{"" if (vis and drawn) else " display=\"none\""}>'
                    f'{html.escape(name)}</text>')

    for b, px, py, shown, _box in blabels:
        pop = f'{b["pop_m"] / 1000:.2f}B'
        body.append(f'<text class="gl-rg-label" data-bloc-label="{b["id"]}" '
                    f'data-lon="{b["anchor"][0]:g}" data-lat="{b["anchor"][1]:g}" '
                    f'x="{_r(px)}" y="{_r(py)}" font-size="{bsize:.0f}" '
                    f'transform="{_upright(px, py)}"'
                    f'{"" if shown else " display=\"none\""}>'
                    f'{html.escape(b["abbr"])} '
                    f'<tspan class="gl-rg-n">{b["count"]}</tspan>'
                    f'<tspan class="gl-rg-p"> \u00b7 {pop}</tspan></text>')

    x0, y0, x1, y1 = extent(view)
    pad = PAD * (R / DEFAULT_R)
    vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" class="gl" '
            f'viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="LUMI globe, field of marks" data-t="{t:g}" '
            f'data-lon0="{lon0:g}" data-lat0="{lat0:g}" data-r="{R:g}" '
            f'data-cx="{cx:g}" data-cy="{cy:g}">')
    note = ("<!-- generated by scripts/render/globe_svg.py; the runtime in "
            "assets/globe/ mutates these paths and never replaces them -->")
    # Everything drawn sits inside ONE group carrying the tilt and the
    # flattening. The projection stays untouched — see geo_frame.FLATTENING for
    # why that is a decision and not a shortcut — so every `d` and every cx/cy
    # in this file is in the projection's own frame and the runtime can keep
    # mutating them without knowing the group exists. assets/geo/pick.js undoes
    # the transform for hit testing.
    #
    # The viewBox needs no rework: at t=0 the ink is a disc centred on the
    # transform's own origin, a rotation maps that disc onto itself, and the
    # flattening only shrinks it. The box that held the untilted frame holds
    # this one.
    g_open = f'<g class="gl-earth" transform="{earth_transform(cx, cy)}">'
    return "\n".join([head, note, g_open, *body, "</g>", "</svg>"])


def _load_marks(arg):
    """Inline JSON, or @path to a file of it."""
    if arg is None:
        return None
    text = (pathlib.Path(arg[1:]).read_text(encoding="utf-8")
            if arg.startswith("@") else arg)
    marks = json.loads(text)
    if not isinstance(marks, list):
        raise SystemExit("FAIL  --marks must be a JSON list of "
                         '{"lon", "lat", "weight", "label"?, "id"?}')
    return marks


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lon0", type=float, default=0.0)
    ap.add_argument("--lat0", type=float, default=0.0)
    ap.add_argument("--r", type=float, default=DEFAULT_R)
    ap.add_argument("--time", metavar="ISO8601", default=DEFAULT_SUN_UTC,
                    help=f"UTC instant for the day/night terminator (default "
                         f"{DEFAULT_SUN_UTC}, the June solstice). A FIXED "
                         f"default, not 'now': a frame that changes every time "
                         f"it is generated cannot be byte-compared, and every "
                         f"generated artifact here is.")
    ap.add_argument("--nodes", action="store_true",
                    help="draw the registry's place layer (the city-states no "
                         "shape can be filled for) even when the globe carries "
                         "a field. Without a field they are drawn anyway — "
                         "scenery may name places; a field must not silently "
                         "gain points that are not its data.")
    ap.add_argument("--preset", choices=("cover",), default=None,
                    help="a named view this package ships. `cover` is LUMIVATE's "
                         "own: Pacific-centred at lon0=-160, the trade blocs "
                         "filled, the terminator on, and every data layer the "
                         "caller supplies drawn. It fixes the VIEW and the LAYER "
                         "SET so a document does not have to know four flags, "
                         "and so every document that draws the mark draws the "
                         "same one. Its first cut filled blocs and nothing else "
                         "— a preset named for the cover that omitted four of "
                         "the five layers, which a reader spotted immediately.")
    ap.add_argument("--regions", metavar="PATH", default=None,
                    help="a region registry. With one, the land is routed into "
                         "one path per region instead of a single path, and "
                         "the region's palette fills it. Without one the globe "
                         "is geography, which is the shipped default: a field "
                         "of marks should not silently gain political fills.")
    ap.add_argument("--cities", metavar="JSON|@FILE", default=None,
                    help='named places: [{"lon","lat","n"}]. Unlike a mark, a '
                         'city carries its NAME on the figure, so this layer '
                         'culls its own labels where they would collide.')
    ap.add_argument("--links", metavar="JSON|@FILE", default=None,
                    help='trade lanes: [{"id","a":[lon,lat],"b":[lon,lat],"w"}]. '
                         'Each is drawn as the great circle between its ends, '
                         'which is the shortest path across a sphere and so is '
                         'the claim itself rather than a picture of it.')
    ap.add_argument("--codes", metavar="JSON|@FILE", default=None,
                    help="strings to send along the lanes, one per signal. A "
                         "signal with no code behind it is decoration, which "
                         "the brand rules forbid, so this is what turns lanes "
                         "into a field.")
    ap.add_argument("--no-night", action="store_true",
                    help="omit the terminator; the globe is then uniformly lit")
    ap.add_argument("--marks", metavar="JSON|@FILE", default=None,
                    help="the field's data: a JSON list of "
                         '{"lon","lat","weight","label"?,"id"?}. Without it the '
                         "globe is scenery, and scenery should say so rather "
                         "than pretend to state data.")
    args = ap.parse_args(argv)
    view = (args.lon0, args.lat0, 0.0, args.r, args.r, args.r)
    if args.preset == "cover":
        # The named view. Set before the rest so an explicit flag still wins:
        # a preset is a starting point, not a lock.
        if args.lon0 == 0.0:
            args.lon0 = -160.0
        if args.lat0 == 0.0:
            args.lat0 = 10.0
        if args.regions is None:
            args.regions = str(ROOT / "assets" / "vectors" / "regions-trade.json")
        # The terminator stays. It is the globe's own waterline — the one
        # horizon where its light collects — and switching it off was the same
        # thinning that dropped the other layers.

    night = None if args.no_night else solar_position(
        datetime.datetime.fromisoformat(args.time))
    print(render(view, marks=_load_marks(args.marks), night=night,
                 nodes=args.nodes, regions_path=args.regions,
                 cities=_load_marks(args.cities),
                 links=_load_marks(args.links),
                 codes=_load_marks(args.codes)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
