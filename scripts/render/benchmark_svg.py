#!/usr/bin/env python3
"""Emit a LUMI benchmark as SVG, from its data.

`compare` is AR-1's first move: set a value against the ones a reader would
judge it against. Its input shape is **one value plus at least one reference
value**, and that is not decoration — a number standing alone, with no reader
able to say whether it is good, is the tell that the move is missing. So this
tool cannot draw a bar without a reference: the judgment anchor WR-5 rule 0
asks for is an input here, not a gate.

    python3 scripts/render/benchmark_svg.py --data spec.json
    python3 scripts/render/benchmark_svg.py --data spec.json --orientation portrait

The spec is the figure data contract (`scripts/lib/figure_spec.py`), `compare`
half:

    {
      "move": "compare",
      "measure":  {"name": "Median time to first value", "unit": "days"},
      "period":   "the first two quarters after launch",
      "reading":  "we sit above both references and the gap is widening",
      "cause":    "direction not tested",
      "source":   "Illustrative figures, not measured.",
      "subject":    {"label": "Us", "value": 34},
      "references": [{"label": "Peer median", "value": 21},
                     {"label": "Best in class", "value": 12}]
    }

**Length encodes the value, and the axis starts at zero. There is no
`--baseline`.** A truncated axis is the most common distortion in this figure
form and the hardest for a reader to catch, so the tool cannot express it —
the same decision as `scatter_svg` having no minimum radius. Each bar carries
`data-datum`, so `inspect_layout`'s proportion probe re-derives the expected
length with a second implementation and measures the rendered pixel.

**The subject reads differently from its references, and only by weight.** One
colour one meaning (design-rules §1): the subject takes the accent, the
references take the neutral rule colour. No literal colour reaches the output.

The source line is the drawing's own last text node (§4 rule 17), never the
caption — run together in one caption the two read as one sentence.

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

# The figure box, matching `scatter_svg`'s so two figures in one document are
# set at one size. Wide for a landscape page, tall for a portrait one.
BOX = {"landscape": (1180, 600), "portrait": (620, 820)}

# Room for the measure name and the source line below, and for the row labels
# on the left. A row label is prose and needs more room than a tick number.
FOOT = 132
LABEL_W = {"landscape": 250, "portrait": 168}

BAR_MAX = 46          # a bar thicker than this reads as a block, not a bar
BAR_GAP = 18


def _rows(spec):
    """-> [(label, value, is_subject)] in reading order, subject first.

    Subject first because the page's title is about the subject and a reader
    looks for it before the things it is set against.
    """
    out = [(str(spec["subject"]["label"]), figure_scale.num(spec["subject"]["value"]),
            True)]
    for ref in spec["references"]:
        out.append((str(ref["label"]), figure_scale.num(ref["value"]), False))
    return out


def render(spec, orientation="landscape", path="the spec"):
    if orientation not in BOX:
        raise SystemExit(f"orientation must be one of {sorted(BOX)}")
    figure_spec.refuse_if_unusable(spec, path)
    if str(spec.get("move")).lower() != "compare":
        raise SystemExit(
            f"{path} declares move {spec.get('move')!r}; this tool draws "
            f"`compare`. assets/frameworks.json says which tool draws which "
            f"move.")

    if spec.get("criteria"):
        # THE MIRROR OF `radar_svg`'s guard, which this file lacked. Both tools
        # declare `move: "compare"` and the registry maps `compare` to both, so
        # the move check above cannot separate them — and a correct radar spec
        # passes the contract clean (it carries `values`, not `value`) and then
        # died here on `spec["subject"]["value"]` with a raw KeyError. An
        # author who picks the wrong one of two tools for one move gets the
        # sentence, not a traceback.
        raise SystemExit(
            f"{path} carries `criteria`, so it compares across several axes at "
            f"once: `radar_svg` draws that. This tool draws one measure "
            f"against its references, where a bar is easier to read than a "
            f"polygon.")

    rows = _rows(spec)
    bad = [lab for lab, v, _ in rows if v is None]
    if bad:
        raise SystemExit(
            f"{path}: {', '.join(bad)} carries no number this tool can read. A "
            f"bar's length IS its value, so a value it cannot parse cannot be "
            f"drawn at any length that would be honest.")
    if any(v < 0 for _lab, v, _s in rows):
        raise SystemExit(
            f"{path}: a negative value cannot be drawn as a length from a zero "
            f"axis. Restate the measure so the comparison is of magnitudes, or "
            f"draw it as a bridge, which is the move for a signed change.")

    W, H = BOX[orientation]
    # THE BOX HEIGHT IS THE ROWS' HEIGHT, not a constant. At a fixed 600 a
    # four-bar figure carried 240 units of empty box, and on a `dense` page —
    # where the drawing takes what the text leaves — `max-height` then scaled
    # the whole thing down to about half the content width. The reader got a
    # small chart with a large margin. Measured on the page, which is the only
    # place a figure's size is visible.
    left = LABEL_W[orientation]
    top, right = 34, 40
    H = min(H, round(top + FOOT + (BAR_MAX + BAR_GAP) * max(len(rows), 1)))
    plot_w = W - left - right
    plot_h = H - top - FOOT

    vmax = max(v for _lab, v, _s in rows)
    hi = figure_scale.nice_ceiling(vmax)
    if hi <= 0:
        raise SystemExit(
            f"{path}: every value is zero, so no bar has a length. A figure "
            f"where nothing can be compared is not a comparison.")

    band = min(BAR_MAX + BAR_GAP, plot_h / max(len(rows), 1))
    bar_h = max(8.0, band - BAR_GAP)
    # THE BARS ARE CENTRED IN THE PLOT, and the rules are drawn only where the
    # bars are. `band` is capped so a three-row figure does not draw bars the
    # thickness of blocks — which is right — but the first cut then left the
    # rows at the top and ran full-height tick lines down through two thirds of
    # empty box. The gates were green; it was obvious the moment the page was
    # rendered and looked at.
    used = band * len(rows)
    plot_top = top + max(0.0, (plot_h - used) / 2)
    plot_bottom = plot_top + used

    measure = spec["measure"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{html.escape(str(measure["name"]))} against '
        f'{len(rows) - 1} reference value(s)">',
    ]

    # Ticks first, so no bar is drawn under a rule that should sit behind it.
    for t in figure_scale.ticks(hi):
        x = left + plot_w * (t / hi)
        parts.append(f'<line x1="{x:.1f}" y1="{plot_top:.1f}" x2="{x:.1f}" '
                     f'y2="{plot_bottom:.1f}" stroke="var(--ln1)" '
                     f'stroke-width="1"/>')
        parts.append(f'<text class="ftick" x="{x:.1f}" '
                     f'y="{plot_bottom + 26:.1f}" text-anchor="middle">'
                     f'{figure_scale.fmt(t)}</text>')

    for i, (label, value, is_subject) in enumerate(rows):
        y = plot_top + i * band + (band - bar_h) / 2
        w = plot_w * (value / hi)
        # THE BARS CARRY THE BRAND. They were `--tx3` for every reference, so
        # a figure whose SUBJECT is zero — the case this deck's catalog page
        # is — drew nothing in the palette at all, and the owner's review said
        # exactly that: the colours are wrong, there is no brand green. The
        # ramp is the right token: `tokens/lumi-theme.css` says it is for
        # fields and surfaces and carries no meaning, which is what a set of
        # bars counting the same thing needs. `--acc` stays the subject's, and
        # `one colour one meaning` is untouched.
        fill = "var(--acc)" if is_subject else "var(--acc-4)"
        if value > 0:
            parts.append(
                f'<rect data-datum="{figure_scale.fmt(value)}" x="{left:.1f}" '
                f'y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" '
                f'fill="{fill}"/>')
        else:
            # A ZERO IS OFTEN THE FINDING, and it has no length to carry it.
            # Drawn as a bar it is invisible, so a figure whose whole point was
            # "zero commerce primitives" showed three grey references and
            # nothing where the subject should be. It gets a mark at the axis
            # origin instead — in its own colour, so the subject still reads as
            # the subject. Found by rendering the first real deck and looking.
            parts.append(
                f'<line data-datum="0" x1="{left:.1f}" y1="{y:.1f}" '
                f'x2="{left:.1f}" y2="{y + bar_h:.1f}" stroke="{fill}" '
                f'stroke-width="3" stroke-dasharray="4 3"/>')
        parts.append(
            f'<text class="flbl" x="{left - 14:.1f}" '
            f'y="{y + bar_h / 2 + 5:.1f}" text-anchor="end">'
            f'{html.escape(label)}</text>')
        parts.append(
            f'<text class="fval" x="{left + w + 10:.1f}" '
            f'y="{y + bar_h / 2 + 5:.1f}">{figure_scale.fmt(value)}</text>')

    # The axis NAME, in the shipped class. `figure_axis_named` gates on it and
    # `figure_axis_orientation` reads the y name's writing mode; a generic class
    # let three conformance decks print an axis name across the plot.
    unit = str(measure.get("unit") or "")
    parts.append(
        f'<text class="axname-x" x="{left + plot_w / 2:.1f}" '
        f'y="{plot_bottom + 56:.1f}" text-anchor="middle" '
        # THE AXIS NAME IS READ FROM THE ROOM, so it is set at the size a
        # reader can read from it. The review: "the horizontal axis name is
        # not prominent enough". It inherited `.axname-x`'s base size, which
        # is written for a chart occupying half a page.
        f'style="font-size:14px;font-weight:700">'
        f'{html.escape(str(measure["name"]))}'
        f'{" \u00b7 " + html.escape(unit) if unit else ""}</text>')

    read_y = plot_bottom + 88
    read_lines = figure_scale.wrap(str(spec["reading"]), plot_w + left - right)
    for j, line in enumerate(read_lines):
        parts.append(f'<text class="fread" x="{left:.1f}" '
                     f'y="{read_y + j * 20:.1f}">{html.escape(line)}</text>')

    # LAST text node in the drawing, which is where §4 rule 17 puts a source.
    # UNDER the reading, not pinned to the box floor. §4 rule 17 asks for the
    # source to be the drawing's LAST TEXT NODE, which is an ordering rule; the
    # first cut read it as a position and left the source floating a third of a
    # page below the sentence it belongs to. The gates were green.
    note_y = min(read_y + len(read_lines) * 20 + 24, H - 14)
    parts.append(
        f'<text class="fnote" x="{left:.1f}" y="{note_y:.1f}">'
        f'{html.escape(str(spec["source"]))} \u00b7 '
        f'{html.escape(str(spec["period"]))} \u00b7 '
        f'{html.escape(str(spec["cause"]))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; the `compare` half of the figure "
                         "data contract")
    ap.add_argument("--orientation", choices=sorted(BOX), default="landscape",
                    help="the figure box: wide for a landscape page, tall for "
                         "a portrait one")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
