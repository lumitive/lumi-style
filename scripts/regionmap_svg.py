#!/usr/bin/env python3
"""Emit the static SVG frame of the LUMI region map.

The flat half of the component split (specs/2026-08-10-globe-map-split-design.md):
a map of trade regions coloured by identity, at the fixed flat geometry the old
globe called t=1. It does not rotate, unroll or animate — a static map has no
frame loop — so unlike the globe's frame this one is complete as emitted: the
runtime in assets/regionmap/ updates STATE (classes, values, labels) and never
touches geometry.

    python3 scripts/regionmap_svg.py                              # every region zero
    python3 scripts/regionmap_svg.py --states '{"europe":"live"}'
    python3 scripts/regionmap_svg.py --states '{"europe":{"state":"live","value":63}}'
    python3 scripts/regionmap_svg.py --labels zh                  # Chinese labels
    python3 scripts/regionmap_svg.py --lon0 150                   # Pacific-centred

Labels are emitted from the registry's `anchor` and `n`/`z` fields — declared
since the registry existed and read by nothing until this file. Each carries
`data-region-label`, which is the vocabulary check_design's D18 counts, so a
document using this frame satisfies the label rule without hand-authoring a
legend.

No literal colour appears here. Every shape carries a class and
`tokens/region-palette.css` ships the bindings, per design-rules.md section 1.

Standard library only.
"""
from __future__ import annotations

import argparse
import html
import json

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
from typing import Any

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("", "lib", "render", "check", "build", "ops"):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import geo_projection as gp  # noqa: E402
from geo_frame import (  # noqa: E402
    DEFAULT_R,
    GRATICULE,
    OBLIQUITY_DEG,
    PAD,
    _d,
    _load,
    _project_area,
    _project_ring,
    _r,
    _rings_of,
    extent,
)


def _norm_states(states):
    """id -> {"state": str, "value": number|None}. Two shapes are accepted —
    the bare string the globe's CLI taught, and the dict the runtime's hostData
    uses — because a document should not need to reshape its data to label it."""
    out = {}
    for rid, v in (states or {}).items():
        if isinstance(v, dict):
            out[rid] = {"state": v.get("state", "zero"), "value": v.get("value")}
        else:
            out[rid] = {"state": v, "value": None}
    return out


def _aria(name, entry):
    """Name and VALUE, the thing a sighted reader takes from the colour and the
    label together. The globe's first frame said "{name}, {state}" — a screen
    reader heard "Europe, live" where the page showed Europe's number — and the
    runtime never updated it, so it also went stale. State is the fallback only
    when there is no value to speak."""
    if entry and entry.get("value") is not None:
        return f"{name}, {entry['value']}"
    return f"{name}, {entry['state'] if entry else 'zero'}"


def _clip_runs(runs, x0, y0, x1, y1):
    """Keep only the pieces of each polyline inside the box."""
    out = []
    for run in runs:
        cur = []
        for x, y in run:
            if x0 <= x <= x1 and y0 <= y <= y1:
                cur.append((x, y))
            else:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
        if len(cur) > 1:
            out.append(cur)
    return out


def render(lon0=0.0, R=DEFAULT_R, states=None, labels="en", regions_path=None):
    """-> the <svg class="regionmap"> element as a string."""
    topo, reg, arcs = _load(regions_path)
    states = _norm_states(states)
    view = (lon0, 0.0, 1.0, R, R, R)

    def paths_for(codes):
        """-> (path data, screen runs) for a set of country codes."""
        d, runs = [], []
        for code in codes:
            country = next((c for c in topo["countries"] if c["a"] == code), None)
            if not country:
                continue
            for ring in _rings_of(country, arcs):
                r_ = _project_area(ring, view)
                runs += r_
                d.append(_d(r_, True, view))
        return " ".join(x for x in d if x), runs

    body = []
    region_runs = {}
    for region in reg["regions"]:
        entry = states.get(region["id"])
        state = entry["state"] if entry else "zero"
        d, runs = paths_for(region["members"])
        region_runs[region["id"]] = runs
        count = region.get("count")
        label = region["n"] if count is None else f'{region["n"]}, {count} members'
        body.append(f'<path class="rg rg-{region["id"]} is-{state}" '
                    f'data-region="{region["id"]}" role="img" '
                    f'aria-label="{html.escape(_aria(label, entry))}" d="{d}"/>')

    # The viewBox fits the INK, not the world. For the shipped registry the two
    # are the same box; for a scoped registry — Asia alone, say — a world-wide
    # frame renders the subject as a sliver with an ocean of empty graticule on
    # either side, which is exactly the reserved-space-nothing-draws-in defect
    # the frame-fill floor exists to catch.
    xs = [pt[0] for runs in region_runs.values() for run in runs for pt in run]
    ys = [pt[1] for runs in region_runs.values() for run in runs for pt in run]
    if not xs:
        x0, y0, x1, y1 = extent(view)
    else:
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    pad = PAD * (R / DEFAULT_R)
    vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    vw = vb[2]                     # the ruler labels and nodes scale against

    # The graticule is emitted last and CLIPPED to the ink box: a scoped map
    # must not carry world-spanning lines outside its own viewBox — the
    # fits-in-viewBox check reads that as clipped ink, and it is.
    grat: Any = []
    lat: float
    for lon in range(-180, 181, GRATICULE):
        grat.append(_d(_clip_runs(_project_ring(
            [(lon, la) for la in range(-90, 91, 3)], view), x0, y0, x1, y1), False))
    for lat in range(-90, 91, GRATICULE):
        grat.append(_d(_clip_runs(_project_ring(
            [(lo, lat) for lo in range(-180, 181, 3)], view), x0, y0, x1, y1), False))
    grat = " ".join(g for g in grat if g)
    if grat:
        body.insert(0, f'<path class="gl-graticule" d="{grat}"/>')

    # The three named latitudes, above the graticule and below the fills, and
    # clipped to the same ink box for the same reason. They are named lines and
    # not just heavier graticule: the tropics are where the sun stands overhead
    # at a solstice, which is the same 23.44 the globe tilts by. A map and a
    # globe of one world should agree about them.
    for cls, lat in (("gl-equator", 0.0),
                     ("gl-tropic", OBLIQUITY_DEG), ("gl-tropic", -OBLIQUITY_DEG)):
        d = _d(_clip_runs(_project_ring(
            [(lo, lat) for lo in range(-180, 181, 3)], view), x0, y0, x1, y1), False)
        if d:
            body.insert(1, f'<path class="{cls}" d="{d}"/>')

    # The FULL membership of each bloc, stroke-only and hidden until a reader
    # asks for it. The base fill above has to pick one bloc per country, so a
    # map of overlapping blocs can never show CPTPP by fill alone — Canada is
    # coloured USMCA and Japan RCEP-or-CPTPP by the partition rule, whichever
    # way it fell. This layer is how the overlap becomes visible without
    # stacking translucent fills and losing every contrast floor the palette
    # clears. Emitted only when a registry actually carries overlapping
    # membership, so the geographic registry pays nothing for it.
    overlays = [r for r in reg["regions"]
                if r.get("full") and sorted(r["full"]) != sorted(r["members"])]
    if overlays:
        body.append('<g class="rg-full">')
        for region in overlays:
            d, _runs = paths_for(region["full"])
            body.append(f'<path class="rg-outline rg-outline-{region["id"]}" '
                        f'data-overlay="{region["id"]}" d="{d}" '
                        f'display="none" aria-hidden="true"/>')
        body.append("</g>")

    if labels != "none":
        for region in reg["regions"]:
            lon, lat = region["anchor"]
            x, y, _vis = gp.unrolled(lon, lat, lon0, 0.0, 1.0, R, R, R)
            text = region["z"] if labels == "zh" else region["n"]
            if labels != "zh" and region.get("abbr"):
                text = region["abbr"]      # "CPTPP" reads better on a map than its full name
            entry = states.get(region["id"])
            # The count is the bloc's MEMBERSHIP, not the number of shapes
            # filled beneath the label: Malta and Singapore are members that
            # this geometry cannot draw, and a count that dropped them would be
            # a different, smaller claim than the one the reader is owed.
            count = region.get("count")
            value = ("" if not entry or entry["value"] is None
                     else f' <tspan class="rg-label-v">{entry["value"]}</tspan>')
            if count is not None:
                value = f' <tspan class="rg-label-n">{count}</tspan>' + value
            # font-size as an ATTRIBUTE, scaled to the INK BOX, not to R. The
            # tokens rule carries family and weight only (a fixed CSS pixel
            # size inside this viewBox renders at whatever the layout divides
            # it to), and R is the wrong ruler: a scoped Asia map fits a box a
            # third the world's width, so an R-scaled label tripled relative
            # to its own frame — found by the first scoped demo page, where
            # "Central Asia" was set wider than Kazakhstan.
            # CLAMPED inside the frame. The label is text-anchor:middle on an
            # anchor chosen for the bloc's shape, and a bloc whose shape touches
            # the frame edge — Mercosur at 150E — hangs half its name outside
            # the viewBox, where it is simply not drawn. Width is estimated
            # rather than measured (no font metrics here), at 0.58em per
            # character for the DIN-ish face at 600: an over-estimate keeps the
            # text in, and the cost of over-estimating is a label a few units
            # further from its anchor than it needed to be.
            fs = vw * 0.0145
            half = 0.58 * fs * len(f"{text} {count if count is not None else ''}") / 2
            x = min(max(x, vb[0] + half), vb[0] + vb[2] - half)
            body.append(f'<text class="rg-label" data-region-label="{region["id"]}" '
                        f'x="{_r(x)}" y="{_r(y)}" font-size="{fs:.0f}">'
                        f'{html.escape(text)}{value}</text>')

    for node in reg.get("nodes", []):
        px, py, _vis = gp.unrolled(node["lon"], node["lat"], lon0, 0.0, 1.0, R, R, R)
        if xs and not (x0 <= px <= x1 and y0 <= py <= y1):
            continue
        body.append(f'<circle class="gl-node" data-node="{node["id"]}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{vw * 0.0068:.1f}">'
                    f'<title>{html.escape(node["n"])}</title></circle>')

    head = (f'<svg xmlns="http://www.w3.org/2000/svg" class="regionmap" '
            f'viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="LUMI region map" '
            f'data-lon0="{lon0:g}" data-r="{R:g}">')
    note = ("<!-- generated by scripts/regionmap_svg.py; the runtime in "
            "assets/regionmap/ updates state and never touches geometry -->")
    return "\n".join([head, note, *body, "</svg>"])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lon0", type=float, default=0.0,
                    help="centre longitude; the seam sits opposite it")
    ap.add_argument("--r", type=float, default=DEFAULT_R)
    ap.add_argument("--states", metavar="JSON", default=None,
                    help='region states, e.g. \'{"europe":"live"}\' or '
                         '\'{"europe":{"state":"live","value":63}}\'. Without it '
                         "every region renders as zero, which is the honest "
                         "default and also why a coverage map generated without "
                         "it says nothing.")
    ap.add_argument("--labels", choices=("en", "zh", "none"), default="en",
                    help="label language, from the registry's n / z fields; "
                         "none only when the host draws its own legend")
    ap.add_argument("--regions", metavar="PATH", default=None,
                    help="a custom registry (validated by "
                         "build_region_palette.py --regions, which also emits "
                         "its scoped palette). The topology stays shipped: "
                         "regions group countries, they do not redraw them.")
    args = ap.parse_args(argv)
    states = json.loads(args.states) if args.states else None
    print(render(lon0=args.lon0, R=args.r, states=states, labels=args.labels,
                 regions_path=args.regions))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
