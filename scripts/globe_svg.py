#!/usr/bin/env python3
"""Emit one static SVG frame of the LUMI globe — a field of marks on a sphere.

The globe half of the component split
(specs/2026-08-10-globe-map-split-design.md): a rotating orthographic globe
whose subject is a FIELD of marks, one per datum, intensity from the datum.
The flat region map is its own component now — scripts/regionmap_svg.py — and
this emitter no longer takes a `--form`: it emits the field frame, always at
the spherical geometry (the t the old one-figure design animated is pinned to 0
here; the shared projection core keeps the parameter and its checks).

This is the deliverable's renderer. A canvas is invisible to every gate this
package owns — d5_drawn_share counts a figure as drawn only if it holds an
<svg>, d5_figure_parity and d17_export_weight read markup, and inspect_layout
cannot see inside a canvas — so what ships in a document is SVG, and the
JavaScript runtime mutates this markup rather than replacing it.

    python3 scripts/globe_svg.py                                  # empty field
    python3 scripts/globe_svg.py --marks '[{"lon":103.8,"lat":1.35,"weight":3,"label":"Singapore"}]'
    python3 scripts/globe_svg.py --marks @marks.json --lon0 -170 --lat0 20

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
import html
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import geo_projection as gp   # noqa: E402
from geo_frame import (   # noqa: E402,F401  (re-exported: render() and callers use them)
    ROOT, TOPOLOGY, REGIONS, STEP_DEG, GRATICULE, PAD, DEFAULT_R,
    _load, _rings_of, _project_ring, _project_area, _pole_close,
    _r, _guard, _d, extent,
)

# The mark radius, as fractions of R. MIN is a floor (a datum must survive being
# small), MAX a ceiling (a mark is a point, not a region), and between them the
# square root of the normalised weight — area encodes quantity.
MARK_R_MIN = 0.008
MARK_R_MAX = 0.028


def mark_radius(weight, wmax, R):
    """Shared with render-canvas.js by value, held together by the parity check."""
    w = max(0.0, float(weight))
    u = math.sqrt(w / wmax) if wmax > 0 else 0.0
    return R * (MARK_R_MIN + (MARK_R_MAX - MARK_R_MIN) * u)


def render(view, marks=None):
    """-> the <svg class="gl"> element as a string.

    `view` is (lon0, lat0, t, R, cx, cy). t stays in the signature because the
    shared suite sweeps it — the winding guard from 0.1.389 outlives the pinned
    product — but the PRODUCT frame is t=0 and main() does not expose it.
    """
    topo, reg, arcs = _load()
    lon0, lat0, t, R, cx, cy = view
    marks = marks or []

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

    d = []
    for country in topo["countries"]:
        for ring in _rings_of(country, arcs):
            d.append(_d(_project_area(ring, view), True, view))
    d = " ".join(x for x in d if x)
    body.append(f'<path class="gl-land" d="{d}"/>')

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

    for node in reg.get("nodes", []):
        px, py, vis = gp.unrolled(node["lon"], node["lat"], lon0, lat0, t, R, cx, cy)
        body.append(f'<circle class="gl-node" data-node="{node["id"]}" '
                    f'data-lon="{node["lon"]:g}" data-lat="{node["lat"]:g}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{R * 0.017:.1f}"'
                    f'{"" if vis else " display=\"none\""}>'
                    f'<title>{html.escape(node["n"])}</title></circle>')

    x0, y0, x1, y1 = extent(view)
    pad = PAD * (R / DEFAULT_R)
    vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" class="gl" '
            f'viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="LUMI globe, field of marks" data-t="{t:g}" '
            f'data-lon0="{lon0:g}" data-lat0="{lat0:g}" data-r="{R:g}" '
            f'data-cx="{cx:g}" data-cy="{cy:g}">')
    note = ("<!-- generated by scripts/globe_svg.py; the runtime in "
            "assets/globe/ mutates these paths and never replaces them -->")
    return "\n".join([head, note, *body, "</svg>"])


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
    ap.add_argument("--marks", metavar="JSON|@FILE", default=None,
                    help="the field's data: a JSON list of "
                         '{"lon","lat","weight","label"?,"id"?}. Without it the '
                         "globe is scenery, and scenery should say so rather "
                         "than pretend to state data.")
    args = ap.parse_args(argv)
    view = (args.lon0, args.lat0, 0.0, args.r, args.r, args.r)
    print(render(view, marks=_load_marks(args.marks)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
