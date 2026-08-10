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
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import geo_projection as gp   # noqa: E402
from geo_frame import (       # noqa: E402
    REGIONS, TOPOLOGY, GRATICULE, PAD, DEFAULT_R,
    _load, _rings_of, _project_ring, _project_area, _d, _r, extent,
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


def render(lon0=0.0, R=DEFAULT_R, states=None, labels="en"):
    """-> the <svg class="regionmap"> element as a string."""
    topo, reg, arcs = _load()
    states = _norm_states(states)
    view = (lon0, 0.0, 1.0, R, R, R)

    body = []
    grat = []
    for lon in range(-180, 181, GRATICULE):
        grat.append(_d(_project_ring([(lon, la) for la in range(-90, 91, 3)], view), False))
    for lat in range(-90, 91, GRATICULE):
        grat.append(_d(_project_ring([(lo, lat) for lo in range(-180, 181, 3)], view), False))
    grat = " ".join(g for g in grat if g)
    if grat:
        body.append(f'<path class="gl-graticule" d="{grat}"/>')

    for region in reg["regions"]:
        entry = states.get(region["id"])
        state = entry["state"] if entry else "zero"
        d = []
        for code in region["members"]:
            country = next((c for c in topo["countries"] if c["a"] == code), None)
            if country:
                for ring in _rings_of(country, arcs):
                    d.append(_d(_project_area(ring, view), True, view))
        d = " ".join(x for x in d if x)
        body.append(f'<path class="rg rg-{region["id"]} is-{state}" '
                    f'data-region="{region["id"]}" role="img" '
                    f'aria-label="{html.escape(_aria(region["n"], entry))}" d="{d}"/>')

    if labels != "none":
        for region in reg["regions"]:
            lon, lat = region["anchor"]
            x, y, _vis = gp.unrolled(lon, lat, lon0, 0.0, 1.0, R, R, R)
            text = region["z"] if labels == "zh" else region["n"]
            entry = states.get(region["id"])
            value = ("" if not entry or entry["value"] is None
                     else f' <tspan class="rg-label-v">{entry["value"]}</tspan>')
            # font-size as an ATTRIBUTE, scaled to R. The tokens rule carries
            # family and weight only: a fixed CSS pixel size inside this
            # viewBox renders at whatever the layout divides it to.
            body.append(f'<text class="rg-label" data-region-label="{region["id"]}" '
                        f'x="{_r(x)}" y="{_r(y)}" font-size="{R * 0.030:.0f}">'
                        f'{html.escape(text)}{value}</text>')

    for node in reg.get("nodes", []):
        px, py, _vis = gp.unrolled(node["lon"], node["lat"], lon0, 0.0, 1.0, R, R, R)
        body.append(f'<circle class="gl-node" data-node="{node["id"]}" '
                    f'cx="{_r(px)}" cy="{_r(py)}" r="{R * 0.014:.1f}">'
                    f'<title>{html.escape(node["n"])}</title></circle>')

    x0, y0, x1, y1 = extent(view)
    pad = PAD * (R / DEFAULT_R)
    vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
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
    args = ap.parse_args(argv)
    states = json.loads(args.states) if args.states else None
    print(render(lon0=args.lon0, R=args.r, states=states, labels=args.labels))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
