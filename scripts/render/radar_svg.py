#!/usr/bin/env python3
"""Emit a LUMI radar as SVG, from its data.

A radar is `compare` across several criteria at once: where is this strong, and
where is it thin. It draws from the `compare` half of the figure data contract
with its `criteria` refinement — one value per criterion for the subject and
for every reference.

    python3 scripts/render/radar_svg.py --data spec.json

    {
      "move": "compare",
      "measure": {"name": "Capability score", "unit": "0-10"},
      "period":  "as assessed this quarter",
      "reading": "we lead on breadth and trail on depth",
      "cause":   "direction not tested",
      "source":  "Illustrative scores, not measured.",
      "criteria":   [{"name": "Breadth"}, {"name": "Depth"}, {"name": "Speed"}],
      "subject":    {"label": "Us",   "values": [7, 4, 8]},
      "references": [{"label": "Peer", "values": [5, 7, 6]}]
    }

**Every spoke runs from zero to one shared maximum, and the maximum is a round
number above the largest value.** A radar whose axes differ, or whose rings
start anywhere but zero, draws a shape the data does not have — and unlike a
bar, the distortion is invisible because the reader has no baseline to compare
against. So the tool cannot express either: there is no per-axis range and no
`--baseline`, the same decision as `benchmark_svg`'s zero axis and
`scatter_svg`'s absent minimum radius.

**A radar with fewer than three criteria is refused** by the contract, because
two axes are a pair of bars drawn as a triangle. That is an input shape, not a
gate.

**The area is not the datum.** A radar's polygon area grows with the SQUARE of
its values, which is why this form is easy to mislead with — so every vertex
carries `data-datum` and no polygon does. `inspect_layout`'s proportion probe
grades the vertices, whose distance from the centre is linear in the value.

The source line is the drawing's own last text node (§4 rule 17).

Standard library only.
"""
from __future__ import annotations

import argparse
import html
import math
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import figure_scale  # noqa: E402
import figure_spec  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]

BOX = {"landscape": (1180, 600), "portrait": (620, 820)}
FOOT = 132
RINGS = 4


def _xy(cx, cy, radius, i, n):
    """-> the point for spoke `i`, first spoke straight up."""
    a = -math.pi / 2 + 2 * math.pi * i / n
    return cx + radius * math.cos(a), cy + radius * math.sin(a)


def render(spec, orientation="landscape", path="the spec"):
    if orientation not in BOX:
        raise SystemExit(f"orientation must be one of {sorted(BOX)}")
    figure_spec.refuse_if_unusable(spec, path)
    if str(spec.get("move")).lower() != "compare":
        raise SystemExit(
            f"{path} declares move {spec.get('move')!r}; this tool draws "
            f"`compare` across criteria. assets/frameworks.json says which "
            f"tool draws which move.")
    if not spec.get("criteria"):
        raise SystemExit(
            f"{path} carries no `criteria`, so there are no axes to compare "
            f"across. A single measure against its references is a benchmark: "
            f"`benchmark_svg` draws that, and a bar is easier to read than a "
            f"triangle.")

    crit = [str(c["name"]) for c in spec["criteria"]]
    series = [(str(spec["subject"]["label"]), spec["subject"]["values"], True)]
    series += [(str(r["label"]), r["values"], False) for r in spec["references"]]

    values = []
    for label, vals, _s in series:
        for j, v in enumerate(vals):
            n = figure_scale.num(v)
            if n is None:
                raise SystemExit(
                    f"{path}: {label} carries no number this tool can read on "
                    f"{crit[j]!r}. A vertex's distance from the centre IS its "
                    f"value, so a value it cannot parse has no honest place.")
            if n < 0:
                raise SystemExit(
                    f"{path}: {label} scores below zero on {crit[j]!r}. A "
                    f"radial axis has no room below its centre, so a negative "
                    f"score would be drawn on the opposite spoke and read as "
                    f"its neighbour's.")
            values.append(n)
    hi = figure_scale.nice_ceiling(max(values))
    if hi <= 0:
        raise SystemExit(f"{path}: every value is zero, so every shape is a "
                         f"point. Nothing can be compared.")

    W, H = BOX[orientation]
    cx, cy = W / 2, (H - FOOT) / 2 + 20
    radius = min(W, H - FOOT) / 2 - 96
    n = len(crit)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{html.escape(str(spec["measure"]["name"]))} across '
        f'{n} criteria for {len(series)} entities">',
    ]

    # The origin, as a rendered element: `inspect_layout`'s proportion probe
    # measures pixels and has no way to read SVG user units, so the centre is
    # something it can call getBoundingClientRect on.
    parts.append(f'<circle data-radial-origin="1" cx="{cx:.1f}" cy="{cy:.1f}" '
                 f'r="0.5" fill="none" stroke="none"/>')
    for ring in range(1, RINGS + 1):
        r = radius * ring / RINGS
        ring_pts = " ".join(f"{x:.1f},{y:.1f}"
                            for x, y in (_xy(cx, cy, r, i, n) for i in range(n)))
        parts.append(f'<polygon points="{ring_pts}" fill="none" '
                     f'stroke="var(--ln1)" stroke-width="1"/>')
    for i in range(n):
        x, y = _xy(cx, cy, radius, i, n)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" '
                     f'y2="{y:.1f}" stroke="var(--ln1)" stroke-width="1"/>')
        lx, ly = _xy(cx, cy, radius + 30, i, n)
        anchor = ("middle" if abs(lx - cx) < 1 else
                  "start" if lx > cx else "end")
        parts.append(f'<text class="axname-x" x="{lx:.1f}" y="{ly + 5:.1f}" '
                     f'text-anchor="{anchor}">{html.escape(crit[i])}</text>')

    legend_row = [0]
    for label, vals, is_subject in series:
        colour = "var(--acc)" if is_subject else "var(--tx3)"
        pts = []
        for i, v in enumerate(vals):
            r = radius * (figure_scale.num(v) / hi)
            pts.append(_xy(cx, cy, r, i, n))
        parts.append(
            f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" '
            f'fill="none" stroke="{colour}" stroke-width="2.5"/>')
        # THE VERTEX carries the datum, never the polygon: a radar's area grows
        # with the SQUARE of its values, so grading the shape would grade the
        # square of the thing the reader is asked to compare.
        #
        # And it declares `radial`, because what encodes the value is the
        # vertex's DISTANCE FROM THE CENTRE, not its own size. Every vertex is
        # the same 4-unit dot, so a probe measuring bounding boxes reads them
        # all as equal and reports a correctly drawn radar as distorted —
        # which is exactly what happened the first time this was rendered and
        # graded. `data-radial-origin` below gives that probe the centre to
        # measure from, as a rendered element rather than as user coordinates,
        # so it stays a second independent implementation.
        for i, (x, y) in enumerate(pts):
            parts.append(
                f'<circle data-datum="'
                f'{figure_scale.fmt(figure_scale.num(vals[i]))}" '
                f'data-encoding="radial" '
                f'cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{colour}"/>')
        # A LEGEND AT THE SIDE, not labels stacked over the top spoke. The
        # first cut put every series name above the vertical axis, so two
        # series, the top criterion's name and the maximum tick were four text
        # runs in one place — legible in the SVG source and a pile-up on the
        # page. Found by rendering it and looking.
        ly = 40 + legend_row[0] * 26
        parts.append(f'<line x1="60" y1="{ly - 5:.1f}" x2="92" '
                     f'y2="{ly - 5:.1f}" stroke="{colour}" stroke-width="2.5"/>')
        parts.append(f'<text class="flbl" x="100" y="{ly:.1f}">'
                     f'{html.escape(label)}</text>')
        legend_row[0] += 1

    # The scale reads UP the vertical spoke, offset to its right, so neither end
    # sits under the top criterion's name.
    parts.append(f'<text class="ftick" x="{cx + 8:.1f}" y="{cy + 16:.1f}">'
                 f'0</text>')
    # Inside the outer ring and clear of the top vertex, which sits exactly on
    # it whenever the subject scores the maximum — as it did the first time
    # this was rendered, printing the scale over the mark.
    parts.append(f'<text class="ftick" x="{cx + 16:.1f}" '
                 f'y="{cy - radius + 26:.1f}">{figure_scale.fmt(hi)}</text>')

    read_y = H - FOOT + 46
    for j, line in enumerate(figure_scale.wrap(str(spec["reading"]), W - 120)):
        parts.append(f'<text class="fread" x="60" y="{read_y + j * 20:.1f}">'
                     f'{html.escape(line)}</text>')
    unit = str(spec["measure"].get("unit") or "")
    parts.append(
        f'<text class="fnote" x="60" y="{H - 14:.1f}">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["measure"]["name"]))}'
        f'{" · " + html.escape(unit) if unit else ""} · '
        f'{html.escape(str(spec["period"]))} · '
        f'{html.escape(str(spec["cause"]))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; the `compare` half with `criteria`")
    ap.add_argument("--orientation", choices=sorted(BOX), default="landscape",
                    help="the figure box")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
