#!/usr/bin/env python3
"""Emit a LUMI waterfall as SVG, from its data.

`bridge` is AR-1's move for a change: a before, an after, and the pieces that
account for the distance between them. Its whole claim is that the pieces
CLOSE — and the contract refuses a spec whose deltas do not reconcile before to
after, so this tool cannot draw a bridge that does not add up. That is an
assertion about the author's data rather than about the drawing, and it is the
one no check in this package could make until the spec existed to hold both
ends and the middle.

    python3 scripts/render/waterfall_svg.py --data spec.json

    {
      "move": "bridge",
      "measure": {"name": "Contribution", "unit": "CNY m"},
      "period":  "FY24 to FY25",
      "reading": "price carries the rise and volume gives a third of it back",
      "cause":   "attribution from the finance walk, not a model",
      "source":  "Illustrative figures, not measured.",
      "before": {"label": "FY24", "value": 100},
      "after":  {"label": "FY25", "value": 140},
      "pieces": [{"label": "Price", "delta": 60}, {"label": "Volume", "delta": -20}]
    }

**Every bar is measured from the same zero and the axis says so.** A waterfall's
floating bars make a truncated axis unusually easy to hide, so there is no
`--baseline` here either. Each bar carries `data-datum` with the MAGNITUDE it
draws, because that is the length a reader compares; the sign is carried by the
colour and by the label.

**Rise and fall differ by token, not by hue invention**: a rise takes the
accent, a fall the seal. The two ends take the neutral rule colour, because
they are levels rather than movements and a reader should not read them as a
third kind of change.

Standard library only.
"""
from __future__ import annotations

import argparse
import html
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
FOOT = 150
COL_MAX = 96
COL_GAP = 26


def _columns(spec):
    """-> [(label, base, height, kind)] left to right, in reading order.

    `base` is the value the bar starts at and `height` its signed extent, so a
    caller draws from `min(base, base + height)` and never has to know the sign.
    """
    before = figure_scale.num(spec["before"]["value"])
    after = figure_scale.num(spec["after"]["value"])
    out = [(str(spec["before"]["label"]), 0.0, before, "level")]
    running = before
    for piece in spec["pieces"]:
        d = figure_scale.num(piece["delta"])
        out.append((str(piece["label"]), running, d, "rise" if d >= 0 else "fall"))
        running += d
    out.append((str(spec["after"]["label"]), 0.0, after, "level"))
    return out


def render(spec, orientation="landscape", path="the spec"):
    if orientation not in BOX:
        raise SystemExit(f"orientation must be one of {sorted(BOX)}")
    figure_spec.refuse_if_unusable(spec, path)
    if str(spec.get("move")).lower() != "bridge":
        raise SystemExit(
            f"{path} declares move {spec.get('move')!r}; this tool draws "
            f"`bridge`. assets/frameworks.json says which tool draws which "
            f"move.")

    for where, key in (("before", "value"), ("after", "value")):
        if figure_scale.num(spec[where][key]) is None:
            raise SystemExit(
                f"{path}: `{where}` carries no number this tool can read. A "
                f"bar's height IS its value, so a value it cannot parse cannot "
                f"be drawn at any height that would be honest.")
    for piece in spec["pieces"]:
        if figure_scale.num(piece["delta"]) is None:
            raise SystemExit(
                f"{path}: {piece.get('label')!r} carries no delta this tool can "
                f"read.")

    cols = _columns(spec)
    lo = min(min(b, b + h) for _lab, b, h, _k in cols)
    hi = max(max(b, b + h) for _lab, b, h, _k in cols)
    if lo < 0:
        raise SystemExit(
            f"{path}: the running total falls below zero, and this tool draws "
            f"from a zero axis. A bridge that crosses zero is two stories; "
            f"split it, or restate the measure.")
    top_v = figure_scale.nice_ceiling(hi)
    if top_v <= 0:
        raise SystemExit(f"{path}: every level is zero, so no bar has a "
                         f"height. There is no change to attribute.")

    W, H = BOX[orientation]
    left, right, top = 96, 48, 40
    plot_w = W - left - right
    plot_h = H - top - FOOT
    band = plot_w / len(cols)
    col_w = min(COL_MAX, band - COL_GAP)

    def y_of(v):
        return top + plot_h * (1 - v / top_v)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{html.escape(str(spec["measure"]["name"]))} from '
        f'{html.escape(str(spec["before"]["label"]))} to '
        f'{html.escape(str(spec["after"]["label"]))}, with '
        f'{len(spec["pieces"])} attributed piece(s)">',
    ]

    for t in figure_scale.ticks(top_v):
        y = y_of(t)
        parts.append(f'<line x1="{left:.1f}" y1="{y:.1f}" '
                     f'x2="{left + plot_w:.1f}" y2="{y:.1f}" '
                     f'stroke="var(--ln1)" stroke-width="1"/>')
        parts.append(f'<text class="ftick" x="{left - 12:.1f}" y="{y + 5:.1f}" '
                     f'text-anchor="end">{figure_scale.fmt(t)}</text>')

    for i, (label, base, height, kind) in enumerate(cols):
        x = left + i * band + (band - col_w) / 2
        y0, y1 = y_of(base), y_of(base + height)
        y, h = min(y0, y1), abs(y1 - y0)
        fill = {"level": "var(--tx3)", "rise": "var(--acc)",
                "fall": "var(--seal)"}[kind]
        # The MAGNITUDE, because that is the length a reader compares. The sign
        # is in the colour and in the label; a probe measuring pixels has no
        # way to read a negative length.
        parts.append(
            f'<rect data-datum="{figure_scale.fmt(abs(height))}" x="{x:.1f}" '
            f'y="{y:.1f}" width="{col_w:.1f}" height="{max(h, 1):.1f}" '
            f'fill="{fill}"/>')
        sign = "+" if kind == "rise" else ("\u2212" if kind == "fall" else "")
        parts.append(
            f'<text class="fval" x="{x + col_w / 2:.1f}" y="{y - 10:.1f}" '
            f'text-anchor="middle">{sign}'
            f'{figure_scale.fmt(abs(height))}</text>')
        for j, line in enumerate(figure_scale.wrap(label, col_w + COL_GAP)):
            parts.append(
                f'<text class="flbl" x="{x + col_w / 2:.1f}" '
                f'y="{top + plot_h + 24 + j * 17:.1f}" text-anchor="middle">'
                f'{html.escape(line)}</text>')

    unit = str(spec["measure"].get("unit") or "")
    parts.append(
        f'<text class="axname-y" x="26" y="{top + plot_h / 2:.1f}" '
        f'text-anchor="middle">{html.escape(str(spec["measure"]["name"]))}'
        f'{" · " + html.escape(unit) if unit else ""}</text>')

    read_y = top + plot_h + 74
    read_lines = figure_scale.wrap(str(spec["reading"]), plot_w)
    for j, line in enumerate(read_lines):
        parts.append(f'<text class="fread" x="{left:.1f}" '
                     f'y="{read_y + j * 20:.1f}">{html.escape(line)}</text>')
    parts.append(
        f'<text class="fnote" x="{left:.1f}" '
        f'y="{min(read_y + len(read_lines) * 20 + 24, H - 12):.1f}">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["period"]))} · '
        f'{html.escape(str(spec["cause"]))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; the `bridge` half of the contract")
    ap.add_argument("--orientation", choices=sorted(BOX), default="landscape",
                    help="the figure box")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
