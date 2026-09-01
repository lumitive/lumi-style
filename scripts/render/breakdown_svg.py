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

    x = float(left)
    for i, (label, value) in enumerate(parts):
        w = plot_w * (value / total)
        drawn = max(w - (SEG_GAP if i < len(parts) - 1 else 0), 0.5)
        parts_out.append(
            f'<rect data-datum="{figure_scale.fmt(value)}" x="{x:.1f}" '
            f'y="{top:.1f}" width="{drawn:.1f}" height="{BAR_H}" '
            f'fill="{LEAD if i == 0 else REST}"/>')
        # A label goes INSIDE only where its slice can hold it; otherwise it
        # goes below with a leader. A label wider than its segment is the
        # commonest way this figure form becomes unreadable.
        text = f"{label} \u00b7 {figure_scale.fmt(value)}"
        if w >= len(f"{label} · {figure_scale.fmt(value)}") * 6.4 + 20:
            parts_out.append(
                f'<text class="flbl" x="{x + w / 2:.1f}" '
                f'y="{top + BAR_H / 2 + 5:.1f}" text-anchor="middle" '
                f'fill="var(--bg)">{text}</text>')
        else:
            parts_out.append(
                f'<line x1="{x + w / 2:.1f}" y1="{top + BAR_H:.1f}" '
                f'x2="{x + w / 2:.1f}" y2="{top + BAR_H + 16:.1f}" '
                f'stroke="var(--ln1)" stroke-width="1"/>')
            parts_out.append(
                f'<text class="flbl" x="{x + w / 2:.1f}" '
                f'y="{top + BAR_H + 32:.1f}" text-anchor="middle">'
                f'{text}</text>')
        x += w

    parts_out.append(
        f'<text class="axname-x" x="{left + plot_w / 2:.1f}" '
        f'y="{top + BAR_H + 66:.1f}" text-anchor="middle">'
        f'{html.escape(str(spec["measure"]["name"]))}'
        f'{" · " + html.escape(unit) if unit else ""}</text>')

    read_y = top + BAR_H + 104
    read_lines = figure_scale.wrap(str(spec["reading"]), plot_w)
    for j, line in enumerate(read_lines):
        parts_out.append(f'<text class="fread" x="{left:.1f}" '
                         f'y="{read_y + j * 20:.1f}">{html.escape(line)}</text>')
    parts_out.append(
        f'<text class="fnote" x="{left:.1f}" '
        f'y="{min(read_y + len(read_lines) * 20 + 24, H - 12):.1f}">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["period"]))} · '
        f'{html.escape(str(spec["cause"]))}</text>')
    parts_out.append("</svg>")
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
