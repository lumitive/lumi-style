#!/usr/bin/env python3
"""Emit a LUMI breakdown as SVG, from its data.

`decompose` is AR-1's move for a whole: break it into parts that are mutually
exclusive and collectively exhaustive, then find the part that carries the
story. The contract refuses a spec whose parts do not sum to its total, so this
tool cannot draw a breakdown that leaves a gap the reader cannot see.

    python3 scripts/render/breakdown_svg.py --data spec.json

    {
      "move": "decompose",
      "measure": {"name": "Addressable spend", "unit": "CNY m"},
      "period":  "FY25",
      "reading": "two segments carry four fifths of it",
      "cause":   "shares are measured, not modelled",
      "source":  "Illustrative figures, not measured.",
      "total": {"label": "All segments", "value": 100},
      "parts": [{"label": "Manufacturing", "value": 48},
                {"label": "Logistics",     "value": 32},
                {"label": "Everything else", "value": 20}]
    }

**One bar, in the order given, with each part's own length.** Not a pie: an
angle is read less accurately than a length, and a reader comparing two slices
of a circle is doing the one comparison the eye is worst at. The parts keep the
author's order rather than being sorted, because the order is often the story
(a funnel's stages, a period's months) and re-sorting would destroy it silently.

**Every part carries `data-datum`**, so `inspect_layout`'s proportion probe
re-derives the expected length independently and measures the rendered pixel.
The total is stated in words above the bar rather than drawn as a second bar,
which would invite the reader to compare a whole against its own parts.

There is no `--baseline` and no `--percent`: the bar IS the total, so the
shares are what it draws. A part is labelled with its value and, where the slice
is wide enough to hold it, inside its own segment.

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
BAR_H = 78

# THE FIRST PART TAKES THE ACCENT AND NOTHING ELSE DOES. Alternating two
# tokens was the first cut, and on a three-part bar it put the first and third
# segments in the same green — one colour one meaning (design-rules §1), and
# two segments sharing a colour read as two segments of a kind. Separability
# comes from a gap between neighbours instead, which asserts nothing.
LEAD, REST = "var(--acc)", "var(--tx3)"
SEG_GAP = 2.0


def render(spec, orientation="landscape", path="the spec"):
    if orientation not in BOX:
        raise SystemExit(f"orientation must be one of {sorted(BOX)}")
    figure_spec.refuse_if_unusable(spec, path)
    if str(spec.get("move")).lower() != "decompose":
        raise SystemExit(
            f"{path} declares move {spec.get('move')!r}; this tool draws "
            f"`decompose`. assets/frameworks.json says which tool draws which "
            f"move.")

    total = figure_scale.num(spec["total"]["value"])
    if total is None:
        raise SystemExit(f"{path}: the total carries no number this tool can "
                         f"read, so no part has a share of anything.")
    parts = []
    for part in spec["parts"]:
        v = figure_scale.num(part["value"])
        if v is None:
            raise SystemExit(
                f"{path}: {part.get('label')!r} carries no number this tool "
                f"can read. A segment's length IS its value.")
        if v < 0:
            raise SystemExit(
                f"{path}: {part.get('label')!r} is negative. A part of a whole "
                f"has no negative length; a signed movement is a bridge, which "
                f"is the move for that.")
        parts.append((str(part["label"]), v))
    if total <= 0:
        raise SystemExit(f"{path}: the total is zero or less, so there is "
                         f"nothing to break down.")

    W, H = BOX[orientation]
    left, right, top = 56, 56, 118
    plot_w = W - left - right

    unit = str(spec["measure"].get("unit") or "")
    parts_out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{html.escape(str(spec["measure"]["name"]))} broken into '
        f'{len(parts)} parts">',
        # The total in words above the bar, never as a second bar: a whole
        # drawn beside its own parts invites the reader to compare the two.
        f'<text class="fval" x="{left:.1f}" y="{top - 28:.1f}">'
        f'{html.escape(str(spec["total"]["label"]))} \u00b7 '
        f'{figure_scale.fmt(total)}'
        f'{" " + html.escape(unit) if unit else ""}</text>',
    ]

    # TWO PASSES. The first places every segment; the second lays the outside
    # labels out so they cannot overlap. Placing each at its own segment's
    # centre put "docs, scripts and the lockfile · 3" and "specification/ · 0"
    # on top of each other in the first real deck built through this tool —
    # and the zero was the finding the page existed to make. Found by
    # rendering it and looking.
    x = float(left)
    placed, outside = [], []
    for i, (label, value) in enumerate(parts):
        w = plot_w * (value / total)
        text = f"{html.escape(label)} \u00b7 {figure_scale.fmt(value)}"
        # A ZERO PART IS A FINDING, not a sliver. It has no length, so it gets
        # no segment — drawing one at a floor would give it ink proportional to
        # nothing, which is the distortion the whole package refuses. It keeps
        # its label, because "this category is empty" is often the point.
        if value > 0:
            drawn = max(w - (SEG_GAP if i < len(parts) - 1 else 0), 0.5)
            parts_out.append(
                f'<rect data-datum="{figure_scale.fmt(value)}" x="{x:.1f}" '
                f'y="{top:.1f}" width="{drawn:.1f}" height="{BAR_H}" '
                f'fill="{LEAD if i == 0 else REST}"/>')
        else:
            parts_out.append(
                f'<line data-datum="0" x1="{x:.1f}" y1="{top:.1f}" '
                f'x2="{x:.1f}" y2="{top + BAR_H:.1f}" stroke="{REST}" '
                f'stroke-width="1.5" stroke-dasharray="3 3"/>')
        inside = (value > 0
                  and w >= len(f"{label} \u00b7 {figure_scale.fmt(value)}") * 6.4 + 20)
        if inside:
            placed.append(
                f'<text class="flbl" x="{x + w / 2:.1f}" '
                f'y="{top + BAR_H / 2 + 5:.1f}" text-anchor="middle" '
                f'fill="var(--bg)">{text}</text>')
        else:
                # The LABEL'S OWN characters plus the separator and the value —
            # `len(label) + 6` under-counted a three-digit value and a long
            # separator, and the browser gate caught two labels still touching
            # after the first fix. The per-character estimate is `.flbl`'s
            # rendered width measured at the design viewport, rounded up.
            outside.append((x + w / 2,
                            len(f"{label} \u00b7 {figure_scale.fmt(value)}"),
                            text, x + w / 2))
        x += w
    parts_out += placed

    # Left to right, each label pushed right of the one before it — and moved
    # to a SECOND ROW when it will not fit, never clamped back inside the box.
    # Clamping was the first fix and it defeated the push: the last two labels
    # were both pulled to the right edge and landed on each other again, which
    # the browser gate reported and the eye had already seen.
    rows: list[float] = [float(left)]
    for centre, chars, text, tick in sorted(outside):
        half = chars * 4.6
        right = left + plot_w
        row = next((i for i, cursor in enumerate(rows)
                    if max(centre, cursor + half) + half <= right), None)
        if row is None:
            rows.append(float(left))
            row = len(rows) - 1
        at = max(centre, rows[row] + half)
        rows[row] = at + half + 14
        y = top + BAR_H + 32 + row * 20
        parts_out.append(
            f'<line x1="{tick:.1f}" y1="{top + BAR_H:.1f}" x2="{at:.1f}" '
            f'y2="{y - 14:.1f}" stroke="var(--ln1)" stroke-width="1"/>')
        parts_out.append(
            f'<text class="flbl" x="{at:.1f}" y="{y:.1f}" '
            f'text-anchor="middle">{text}</text>')
    label_rows = len(rows)

    parts_out.append(
        f'<text class="axname-x" x="{left + plot_w / 2:.1f}" '
        f'y="{top + BAR_H + 46 + label_rows * 20:.1f}" text-anchor="middle">'
        f'{html.escape(str(spec["measure"]["name"]))}'
        f'{" · " + html.escape(unit) if unit else ""}</text>')

    read_y = top + BAR_H + 84 + label_rows * 20
    read_lines = figure_scale.wrap(str(spec["reading"]), plot_w)
    for j, line in enumerate(read_lines):
        parts_out.append(f'<text class="fread" x="{left:.1f}" '
                         f'y="{read_y + j * 20:.1f}">{html.escape(line)}</text>')
    note_y = read_y + len(read_lines) * 20 + 24
    parts_out.append(
        f'<text class="fnote" x="{left:.1f}" y="{note_y:.1f}">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["period"]))} · '
        f'{html.escape(str(spec["cause"]))}</text>')
    parts_out.append("</svg>")
    # THE BOX IS THE DRAWING. At a fixed 600 a one-bar breakdown carried some
    # 180 units of empty box, and on a `dense` page — where the drawing takes
    # what the text leaves — `max-height` scaled the whole figure down to fit a
    # height a third of which was nothing. The reader got a small chart with a
    # large margin, on every gate green. The clamp above was doing the same
    # damage from the other side: it pinned the source to the box floor when
    # the labels ran long, which §4 rule 17 asks for as an ORDER and not as a
    # position.
    fitted_h = max(round(note_y + 12), top + BAR_H + 60)
    if fitted_h != H:
        parts_out[0] = parts_out[0].replace(
            f'viewBox="0 0 {W} {H}"', f'viewBox="0 0 {W} {fitted_h}"').replace(
            f'height="{H}"', f'height="{fitted_h}"')
    return "\n".join(parts_out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; the `decompose` half of the contract")
    ap.add_argument("--orientation", choices=sorted(BOX), default="landscape",
                    help="the figure box")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
