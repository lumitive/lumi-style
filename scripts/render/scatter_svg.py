#!/usr/bin/env python3
"""Emit a LUMI scatter as SVG, from its data.

A scatter is the one figure form the shape library cannot hold: its units are
placed whole and encode a RELATION, while a scatter's marks ARE its data
(references/design-rules.md DR-20, KNOWN_GAPS GAP-032). So `correlate` is
`drawn: "native"` in assets/frameworks.json, and this is the tool that draws it
— the same way regionmap_svg.py draws the flat map rather than shipping one.

    python3 scripts/render/scatter_svg.py --data spec.json
    python3 scripts/render/scatter_svg.py --data spec.json --orientation portrait
    python3 scripts/render/scatter_svg.py --data spec.json --trend smooth

The spec is JSON, and every field DR-20 requires is a field here, because a
drawing that cannot state its units should not be easy to emit:

    {
      "x":      {"name": "Median setup time", "unit": "days"},
      "y":      {"name": "12-month retention", "unit": "% of teams"},
      "size":   {"name": "Seats at signup", "unit": "seats"},   // optional
      "series": {"onboarded": "blue", "self-serve": "red"},     // optional
      "points": [{"x": 3, "y": 94, "size": 120, "series": "onboarded"}, ...],
      "reading": "retention falls about 1.2 points per setup day, then flattens",
      "cause":   "direction not tested",
      "source":  "Illustrative pilot data, 24 teams, first 12 months.",
      "mark":    {"at": 21, "label": "three weeks"}             // optional
    }

**Size is encoded by AREA, never by radius, and with no floor.** A radius drawn
linearly in the value exaggerates it by the square: a datum twice another draws
four times the ink. `r = R_MAX * sqrt(v / vmax)` is the whole rule — there is no
minimum radius, because a floor is itself a distortion and would overstate
exactly the marks a reader is least able to check. Each sized mark carries
`data-datum` with its value and `data-encoding="area"`, so inspect_layout's
proportion check grades it against the square root rather than against the
length; that check assumed length encoding and would otherwise fail a correctly
drawn bubble.

**The trend line is a claim and says so.** `--trend smooth` draws a local mean
through a moving window, as a Catmull-Rom spline, and labels itself with its
form and window. It is never fitted silently: DR-20's misuse line is a line
drawn by eye through a cloud that has no relation.

No literal colour: every mark takes a `var(--token)` from tokens/, so the
drawing follows the document's palette and its dark override.

Standard library only.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The CVD-validated triple, tokens/design-tokens.json `chart`. A series name
# maps to one of these; the names are the author's, the values are the
# package's, and nothing here writes a hex.
SERIES_TOKENS = {"blue": "--d-blue", "red": "--d-red", "teal": "--d-teal"}
DEFAULT_SERIES = "blue"

# Mark radii in user units. **There is no minimum for a sized mark**, and that
# is a decision rather than an oversight: a floor is itself a distortion. A
# first cut carried `r = R_MIN + (R_MAX - R_MIN) * sqrt(v / vmax)`, which drew
# a datum of 25 against a maximum of 100 at 62% of the largest radius where
# area-proportionality says 50% — a 23% overstatement of the smallest marks,
# committed by the code whose docstring said it encoded area. `R_PLAIN` is the
# radius when NOTHING is encoded, so it distorts nothing.
R_MAX, R_PLAIN = 17.0, 6.0

# The figure box, and the room the FOOT of it needs. Everything below the plot
# stacks in a fixed order — ticks, axis name + reading, size key, source — and
# the first cut let the size key land on top of both its neighbours because the
# box had no room for it. The foot is computed from what the figure actually
# carries, never assumed.
# **Every label gets its own baseline.** Sharing one between two end-anchored
# labels works only while the box is wide enough to keep them apart, so the
# landscape figure looked right and the portrait one — 620 wide — ran the trend
# label through the marker label and the axis name through the reading line.
# A layout that depends on the box being wide is a layout that is wrong in the
# orientation nobody looked at.
BOX = {"landscape": (1180, 600), "portrait": (620, 820)}
FOOT = 150
# The size key sits ABOVE the plot, not below it. `figure_axis_overlap` takes
# the plot to be every drawn thing that is not text — which a legend RING is,
# so a key below the baseline drags the plot's bottom edge past the x-axis name
# and the name reads as lying across the plot it names. The check cannot tell a
# legend ring from a datum without a declaration, and moving the key is a
# smaller change than teaching it a second exemption. Above the plot is also
# where a reader meets the scale before the marks that use it.
HEAD_SIZED = 76


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _nice(lo, hi):
    """-> (lo, hi, step) covering the data on round numbers.

    A range chosen to hug the data is how an axis manufactures a relation
    (DR-20 rule 5), so this rounds OUTWARD and never inward.
    """
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    raw = span / 4.0
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1.0
    step = next((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), 10 * mag)
    return math.floor(lo / step) * step, math.ceil(hi / step) * step, step


def _wrap(text, width_units, per_char=5.6):
    """-> the line broken to fit `width_units`, as a list of lines.

    Estimated from the character count rather than measured, because this tool
    ships no font metrics — so the estimate is deliberately CONSERVATIVE. The
    portrait box is 620 wide and the reading line ran 34 units outside its own
    viewBox, where `figure_clipped` found it: a sentence that fits the wide
    figure is not a sentence that fits the tall one.
    """
    budget = max(12, int(width_units / per_char))
    lines, cur = [], ""
    for word in str(text).split():
        if cur and len(cur) + 1 + len(word) > budget:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines


def _fmt(v, step):
    return f"{v:.0f}" if step >= 1 and abs(v - round(v)) < 1e-9 else f"{v:g}"


def _catmull_rom(pts):
    """-> a cubic path through pts, so the trend reads as a curve not a chain.

    Catmull-Rom converted to Bezier: it passes THROUGH every point it is given,
    which matters because those points are computed means. A spline that only
    approaches them would be a second smoothing nobody declared.
    """
    if len(pts) < 2:
        return ""
    d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[0]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        d.append(
            f"C{p1[0] + (p2[0] - p0[0]) / 6:.1f} {p1[1] + (p2[1] - p0[1]) / 6:.1f}"
            f" {p2[0] - (p3[0] - p1[0]) / 6:.1f} {p2[1] - (p3[1] - p1[1]) / 6:.1f}"
            f" {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d)


def _trend_points(pts, window):
    """-> local means, in x order. The window is stated on the drawing."""
    ordered = sorted(pts, key=lambda p: p[0])
    if len(ordered) < window:
        return []
    out = []
    for i in range(len(ordered) - window + 1):
        chunk = ordered[i:i + window]
        out.append((sum(c[0] for c in chunk) / window,
                    sum(c[1] for c in chunk) / window))
    return out


def render(spec, orientation="landscape", trend="none", window=5):
    if orientation not in BOX:
        raise SystemExit(f"orientation must be one of {sorted(BOX)}")
    W, H = BOX[orientation]

    pts = []
    for p in spec.get("points") or []:
        x, y = _num(p.get("x")), _num(p.get("y"))
        if x is None or y is None:
            continue
        pts.append({"x": x, "y": y, "size": _num(p.get("size")),
                    "series": str(p.get("series") or "")})
    if not pts:
        raise SystemExit("no point carries both an x and a y — nothing to draw")

    xa, ya = spec.get("x") or {}, spec.get("y") or {}
    size_meta = spec.get("size") or {}
    sized = [p for p in pts if p["size"] is not None and p["size"] > 0]
    nonpositive = [p for p in pts if p["size"] is not None and p["size"] <= 0]
    if nonpositive:
        raise SystemExit(
            f"{len(nonpositive)} point(s) declare a size of zero or less. Area "
            f"encoding gives them no ink at all, and drawing them at a floor "
            f"would overstate every small mark on the figure — a floor is the "
            f"distortion this encoding exists to avoid. Draw zero as its own "
            f"mark, or leave those points unsized.")
    if sized and not size_meta.get("name"):
        raise SystemExit(
            "points carry `size` and the spec does not name that measure — a "
            "bubble is a THIRD measure and DR-20 requires its name and unit, "
            "or the reader is reading ink of unknown meaning")

    # Room for: the y name above, the x ticks + x name + reading + source below.
    # Room for the vertical axis name AND the tick numbers beside it.
    left = 126 if orientation == "landscape" else 104
    X0, X1 = left, W - 40
    Y0 = 44 + (HEAD_SIZED if sized else 0)
    Y1 = H - FOOT

    xlo, xhi, xstep = _nice(min(p["x"] for p in pts), max(p["x"] for p in pts))
    ylo, yhi, ystep = _nice(min(p["y"] for p in pts), max(p["y"] for p in pts))

    def sx(v):
        return X0 + (v - xlo) / (xhi - xlo) * (X1 - X0)

    def sy(v):
        return Y1 - (v - ylo) / (yhi - ylo) * (Y1 - Y0)

    vmax = max((p["size"] for p in sized), default=0.0)

    def radius(p):
        """r ∝ sqrt(v), so AREA is proportional to the value. Nothing else."""
        if p["size"] is None or vmax <= 0:
            return R_PLAIN
        return R_MAX * math.sqrt(p["size"] / vmax)

    o = []
    e = html.escape

    def ylabel():
        n, u = e(str(ya.get("name", ""))), e(str(ya.get("unit", "")))
        return f"{n}, {u}" if u else n

    def xlabel():
        n, u = e(str(xa.get("name", ""))), e(str(xa.get("unit", "")))
        return f"{n}, {u}" if u else n

    # `.axname-y`, the package's own vocabulary: left of the vertical axis, set
    # upright reading bottom to top. tokens/lumi-layouts.css owns the rotation —
    # a hand-rolled `transform` here is how every y-axis name this package
    # shipped before 0.1.594 ended up outside its own viewBox, invisible, with
    # the probe agreeing because it measured the untransformed box.
    o.append(f'<text class="axname-y" x="{X0 - 52}" y="{(Y0 + Y1) / 2:.1f}" '
             f'text-anchor="middle">{ylabel()}</text>')
    if sized:
        # the key, in the band reserved above the plot
        o.extend(_size_legend(sized, size_meta, radius, X0, Y0 - 30, e))

    v = ylo
    while v <= yhi + 1e-9:
        y = sy(v)
        o.append(f'<path d="M{X0} {y:.1f} L{X1} {y:.1f}" style="stroke:var(--ln3);'
                 f'stroke-width:1;fill:none"/>')
        o.append(f'<text x="{X0 - 10}" y="{y + 4:.1f}" text-anchor="end" class="flbl" '
                 f'style="fill:var(--tx3)">{_fmt(v, ystep)}</text>')
        v += ystep

    o.append(f'<path d="M{X0} {Y0} L{X0} {Y1} L{X1} {Y1}" '
             f'style="stroke:var(--tx3);stroke-width:1.25;fill:none"/>')

    v = xlo
    while v <= xhi + 1e-9:
        x = sx(v)
        o.append(f'<path d="M{x:.1f} {Y1} L{x:.1f} {Y1 + 6}" '
                 f'style="stroke:var(--tx3);stroke-width:1"/>')
        o.append(f'<text x="{x:.1f}" y="{Y1 + 22}" text-anchor="middle" class="flbl" '
                 f'style="fill:var(--tx3)">{_fmt(v, xstep)}</text>')
        v += xstep

    mark = spec.get("mark") or {}
    if _num(mark.get("at")) is not None:
        mx = sx(_num(mark.get("at")))
        o.append(f'<path d="M{mx:.1f} {Y0} L{mx:.1f} {Y1}" style="stroke:var(--tx3);'
                 f'stroke-width:1;stroke-dasharray:4 4;fill:none"/>')
        if mark.get("label"):
            o.append(f'<text x="{mx + 8:.1f}" y="{Y0 + 14}" class="flbl" '
                     f'style="fill:var(--tx2)">{e(str(mark["label"]))}</text>')

    if trend == "smooth":
        tp = _trend_points([(p["x"], p["y"]) for p in pts], window)
        if tp:
            d = _catmull_rom([(sx(a), sy(b)) for a, b in tp])
            o.append(f'<path d="{d}" style="stroke:var(--acc);stroke-width:2.5;'
                     f'fill:none;stroke-linecap:round"/>')
            # its own baseline, below the marker label's
            o.append(f'<text x="{X1}" y="{Y0 + 34}" text-anchor="end" class="flbl" '
                     f'style="fill:var(--acc)">trend: local mean, {window}-point '
                     f'window (not a fitted model)</text>')

    palette = spec.get("series") or {}
    for p in pts:
        # `paint`, not `token`: the secret scanner reads an assignment to a
        # name like `token` as a credential, and it is right to — the cost of
        # teaching it an exception is higher than the cost of the clearer name,
        # and this IS a paint value.
        paint = SERIES_TOKENS.get(palette.get(p["series"], DEFAULT_SERIES),
                                  SERIES_TOKENS[DEFAULT_SERIES])
        r = radius(p)
        # `data-datum` + `data-encoding` so the proportion check grades the
        # mark against the rule it was actually drawn to.
        datum = (f' data-datum="{p["size"]:g}" data-encoding="area"'
                 if p["size"] is not None else "")
        o.append(f'<circle cx="{sx(p["x"]):.1f}" cy="{sy(p["y"]):.1f}" r="{r:.1f}"'
                 f'{datum} style="fill:var({paint});fill-opacity:.78"/>')

    o.append(f'<text class="axname-x" x="{(X0 + X1) / 2:.1f}" y="{Y1 + 44}" '
             f'text-anchor="middle">{xlabel()}</text>')

    reading = str(spec.get("reading") or "").strip()
    cause = str(spec.get("cause") or "").strip()
    line = f"n = {len(pts)}"
    if reading:
        line += f" · {reading}"
    if cause:
        line += f" · {cause}"
    # Y1+44 is the axis name's line; the reading gets its own at Y1+66, and
    # wraps rather than running out of the viewBox.
    read_lines = _wrap(line, X1 - X0)
    for i, ln in enumerate(read_lines):
        o.append(f'<text x="{X0}" y="{Y1 + 66 + i * 18}" class="flbl" '
                 f'style="fill:var(--tx2)">{e(ln)}</text>')

    srcy = Y1 + 66 + len(read_lines) * 18 + 8
    if spec.get("source"):
        o.append(f'<text x="{X0}" y="{srcy}" class="fnote" style="fill:var(--tx3)">'
                 f'Source: {e(str(spec["source"]))}</text>')

    alt = e(f"{ya.get('name','y')} against {xa.get('name','x')}, {len(pts)} points"
            + (f"; {reading}" if reading else ""))
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{alt}">\n  '
            + "\n  ".join(o) + "\n</svg>")


def _size_legend(sized, meta, radius, x, y, e):
    """The size key. A bubble whose scale is not shown is ink of unknown value."""
    vals = sorted({p["size"] for p in sized})
    picks = [vals[0], vals[len(vals) // 2], vals[-1]] if len(vals) >= 3 else vals
    out, cx = [], x + R_MAX
    name = e(str(meta.get("name", "")))
    unit = e(str(meta.get("unit", "")))
    out.append(f'<text x="{x}" y="{y - R_MAX - 12:.1f}" class="flbl" '
               f'style="fill:var(--tx3)">{name}{", " + unit if unit else ""}'
               f' — circle AREA, not width</text>')
    for v in picks:
        r = radius({"size": v})
        out.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                   f'style="fill:none;stroke:var(--tx3);stroke-width:1"/>')
        out.append(f'<text x="{cx:.1f}" y="{y + R_MAX + 14:.1f}" text-anchor="middle" '
                   f'class="flbl" style="fill:var(--tx3)">{v:g}</text>')
        cx += 2 * R_MAX + 26
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; see this file's docstring for the fields")
    ap.add_argument("--orientation", choices=sorted(BOX), default="landscape",
                    help="the figure box: wide for a landscape page, tall for a "
                         "portrait one")
    ap.add_argument("--trend", choices=("none", "smooth"), default="none",
                    help="draw a smoothed local mean; it labels its own form")
    ap.add_argument("--window", type=int, default=5,
                    help="points per trend window (default 5)")
    a = ap.parse_args(argv)
    path = pathlib.Path(a.data)
    if not path.is_file():
        sys.exit(f"no such spec: {path}")
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"{path}: not valid JSON — {exc}")
    if a.window < 2:
        sys.exit("--window needs at least 2 points to be a mean")
    print(render(spec, orientation=a.orientation, trend=a.trend, window=a.window))


if __name__ == "__main__":
    main()
