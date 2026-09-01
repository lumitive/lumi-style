#!/usr/bin/env python3
"""Emit a LUMI timeline as SVG, from its data. Three tiers, one input shape.

**Why this exists.** This package had no timeline component and no timeline
renderer. `grep -n timeline tokens/lumi-layouts.css` returns two comment lines;
`references/design-rules.md` says only that a wide timeline goes in the
`full-bleed` row, and then leaves the drawing to the author. So a page about a
product's development path got a bare library staircase carrying two words, and
the owner's review said what that looks like: the figure is too simple, it
has no time axis, and the time points the page states appear nowhere on it.

    python3 scripts/render/timeline_svg.py --data spec.json
    python3 scripts/render/timeline_svg.py --data spec.json --tier general

Three tiers, because the owner named three and they answer different questions:

**light** — points on one axis. Each event is a dot ON the axis, a stem, and
two lines at the stem's head: the name, then the description. Stems use three
heights only, cycled, so neighbouring labels never collide; labels flip from
`start` to `end` past the midpoint so the last one does not hang off the edge.
This is the tier for "what happened, and when".

**general** — blocks on a spine. Solid = now, outlined = already happened,
**dashed = forecast**, and a forecast's value hangs BELOW its block in the
accent, because a number inside a dashed box reads as measured. Arrow stubs
carry direction between the future blocks. This is the tier for "how we get
from here to there", and its dashes are the honesty: nothing to the right of
today is built.

**pro** — staged cards over a gradient band. Each card carries four levels:
the date, the name, the body line, and a state pill. The band beneath ramps its
axis from the accent at 22% to the accent at full, so the HUE carries past →
present. The ramp starts at a visible tint rather than at the rule colour: at
2px from `--ln2` it was a hairline nobody could see, and a gradient nobody sees
carries nothing. This is the tier for "what each era could and could
not do", and it is the only tier that states a limit per stage.

The spec is the figure data contract's **`bridge` half with its `stages`
refinement** — not a sixth analytical move. AR-1 declares five and
`check_repo`'s `figure spec moves` holds `figure_spec.MOVE_FIELDS` to
`check_outline.ANALYTICAL_MOVES` in both directions, so a sixth would need
convention 2's documented case. A version history IS a bridge: a before, an
after, and the steps between them — its steps are named rather than numeric,
which is what `stages` says and `pieces` does not. The same shape `criteria`
has for `compare`.

    {
      "move": "bridge",
      "measure": {"name": "Public releases", "unit": "version"},
      "period":  "2025-12 to 2026-08",
      "reading": "three shipped in eight months; the fourth is still a candidate",
      "cause":   "direction not tested; this is a release history",
      "source":  "the project's own version line, read 2026-08-11.",
      "stages": [{"date": "2025-12", "name": "Announced", "body": "Apache 2.0",
                  "state": "done"}, ...]
    }

`state` is one of `done` / `now` / `open`, and it is not decoration: `general`
draws `open` dashed and `pro` colours its pill. A stage with no `date` is
refused — a timeline whose points carry no time is a row of boxes.

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

TIERS = ("light", "general", "pro")
# THE WIDTH IS A DESIGN DECISION; THE HEIGHT IS MEASURED. It used to be a pair
# — 1180 x 420 landscape — and the pro tier's ink stopped at y=276, so a third
# of the box was empty. `.fig` sizes an SVG with `height: auto`, which makes
# the box and the art the same thing only when the box IS the art: on the page
# that emptiness rendered as 115px between the drawing and its own caption,
# and as a drawing scaled down to fit a height it did not need. Every metric
# was green. Found by looking at the rendered page — convention 8.
#
# The floor is a floor: a two-stage timeline should not become a letterbox.
BOX_W = {"landscape": 1180, "portrait": 620}
BOX_H_FLOOR = {"landscape": 220, "portrait": 420}

STATES = ("done", "now", "open")

# `light`'s geometry, taken coordinate for coordinate from the figure the owner
# cited as the standard. Three stem heights, cycled — two adjacent labels can
# never share a baseline, which is what keeps a dense run readable without any
# collision solver.
STEMS = (48.0, 82.0, 116.0)
AXIS_Y = 176.0
DOT_R = 6.0


def _states(stages):
    bad = [s.get("state") for s in stages
           if s.get("state") and s["state"] not in STATES]
    if bad:
        raise SystemExit(
            f"stage state(s) {bad} are not one of {', '.join(STATES)}. "
            f"`open` draws dashed and is what says a stage is not built; a "
            f"free-text state would draw solid and read as delivered.")


def _check(spec, path):
    figure_spec.refuse_if_unusable(spec, path)
    stages = spec.get("stages")
    if not isinstance(stages, list) or len(stages) < 2:
        raise SystemExit(
            f"{path}: a timeline needs at least two stages, and this spec "
            f"carries {0 if not isinstance(stages, list) else len(stages)}. "
            f"One point in time is a date, not a path.")
    undated = [i for i, s in enumerate(stages)
               if not (isinstance(s, dict) and str(s.get("date") or "").strip())]
    if undated:
        raise SystemExit(
            f"{path}: stage(s) {undated} carry no `date`. A timeline whose "
            f"points carry no time is a row of boxes — the exact defect this "
            f"renderer was written from.")
    unnamed = [i for i, s in enumerate(stages) if not str(s.get("name") or "").strip()]
    if unnamed:
        raise SystemExit(f"{path}: stage(s) {unnamed} carry no `name`.")
    _states(stages)
    return stages


def _light(stages, spec, W, H):
    left, right = 54.0, W - 54.0
    n = len(stages)
    step = (right - left) / max(n - 1, 1)
    parts = [f'<line x1="{left}" y1="{AXIS_Y}" x2="{right}" y2="{AXIS_Y}" '
             f'stroke="var(--ln1)" stroke-width="1"/>']
    for i, s in enumerate(stages):
        x = left + i * step
        top = STEMS[i % len(STEMS)]
        # THE LABEL FLIPS PAST THE MIDPOINT so the last one does not hang off
        # the right edge — the reference figure's own rule.
        after = x > (left + right) / 2
        anchor, lx = ("end", x - 10) if after else ("start", x + 10)
        parts += [
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{AXIS_Y}" '
            f'stroke="var(--ln2)"/>',
            f'<circle cx="{x:.1f}" cy="{AXIS_Y}" r="{DOT_R}" '
            f'style="fill:{"var(--acc)" if s.get("state") == "now" else "var(--acc-live)"}"/>',
            f'<line x1="{x:.1f}" y1="{AXIS_Y}" x2="{x:.1f}" y2="{AXIS_Y + 5}" '
            f'stroke="var(--ln1)"/>',
            f'<text x="{x:.1f}" y="{AXIS_Y + 20}" text-anchor="middle" '
            f'class="flbl" style="fill:var(--tx3);font-size:12px">'
            f'{html.escape(str(s["date"]))}</text>',
            f'<text x="{lx:.1f}" y="{top - 8}" text-anchor="{anchor}" '
            f'class="flbl" style="fill:var(--tx1);font-size:13px;'
            f'font-weight:700">{html.escape(str(s["name"]))}</text>',
        ]
        if s.get("body"):
            parts.append(
                f'<text x="{lx:.1f}" y="{top + 7}" text-anchor="{anchor}" '
                f'class="flbl" style="fill:var(--tx3);font-size:12px">'
                f'{html.escape(str(s["body"]))}</text>')
    return parts, AXIS_Y + 38


def _general(stages, spec, W, H):
    """Blocks on a spine. Dashed is the honesty: nothing dashed is built."""
    spine = 92.0
    n = len(stages)
    gap = 18.0
    bw = (W - gap * (n - 1)) / n
    parts = [f'<line x1="0" y1="{spine}" x2="{W}" y2="{spine}" '
             f'stroke="var(--ln2)" stroke-width="1.5"/>',
             '<defs><marker id="tl-ar" viewBox="0 0 8 8" refX="7" refY="4" '
             'markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0 0 L8 4 L0 8 z" fill="var(--acc)"/></marker></defs>']
    for i, s in enumerate(stages):
        x = i * (bw + gap)
        state = s.get("state") or "done"
        if state == "now":
            parts.append(f'<rect x="{x:.1f}" y="62" width="{bw:.1f}" '
                         f'height="60" fill="var(--acc)"/>')
            ink = "var(--on-acc)"
        elif state == "open":
            parts.append(f'<rect x="{x:.1f}" y="62" width="{bw:.1f}" '
                         f'height="60" fill="none" stroke="var(--ln2)" '
                         f'stroke-dasharray="5 4"/>')
            ink = "var(--tx1)"
            # The arrow stub lives in the gap BEFORE a future block, so
            # direction is carried by the drawing rather than by reading order.
            if i:
                parts.append(
                    f'<path d="M{x - gap + 2:.1f} {spine} L{x - 2:.1f} {spine}" '
                    f'stroke="var(--acc)" stroke-width="1.6" '
                    f'marker-end="url(#tl-ar)"/>')
        else:
            parts.append(f'<rect x="{x:.1f}" y="62" width="{bw:.1f}" '
                         f'height="60" fill="none" stroke="var(--seal)" '
                         f'stroke-width="1.6"/>')
            ink = "var(--tx1)"
        parts += [
            f'<text x="{x + 14:.1f}" y="86" class="flbl" '
            f'style="fill:{ink};font-size:12px">{html.escape(str(s["date"]))}</text>',
            f'<text x="{x + 14:.1f}" y="107" class="flbl" '
            f'style="fill:{ink};font-size:13.5px;font-weight:700">'
            f'{html.escape(str(s["name"]))}</text>',
        ]
        if s.get("body"):
            # A FORECAST'S VALUE HANGS BELOW ITS BLOCK. Inside a dashed box a
            # number reads as measured; outside it, in the accent, it reads as
            # the claim it is.
            below = state == "open"
            parts.append(
                f'<text x="{x + 14:.1f}" y="{140 if below else 122:.0f}" '
                f'class="flbl" style="fill:'
                f'{"var(--acc);font-weight:700" if below else "var(--tx3)"};'
                f'font-size:12px">{html.escape(str(s["body"]))}</text>')
    return parts, 170.0


def _pro(stages, spec, W, H):
    """Staged cards over a gradient band. The hue carries past → present."""
    n = len(stages)
    gap = 14.0
    cw = (W - gap * (n - 1)) / n
    top, ch = 20.0, 132.0
    parts = ['<defs>'
             '<linearGradient id="tl-era" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0" stop-color="var(--ln2)"/>'
             '<stop offset="1" stop-color="var(--acc)"/>'
             '</linearGradient></defs>']
    for i, s in enumerate(stages):
        x = i * (cw + gap)
        state = s.get("state") or "done"
        # The card's own vertical tint, 11% to 2% — volume without a shadow,
        # and the fill never competes with the text on it.
        parts += [
            f'<defs><linearGradient id="tl-c{i}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="var(--acc)" stop-opacity="0.11"/>'
            f'<stop offset="1" stop-color="var(--acc)" stop-opacity="0.02"/>'
            f'</linearGradient></defs>',
            f'<rect x="{x:.1f}" y="{top}" width="{cw:.1f}" height="{ch}" '
            f'rx="10" fill="url(#tl-c{i})" stroke="var(--ln1)"/>',
            f'<rect x="{x:.1f}" y="{top + ch - 3}" width="{cw:.1f}" height="3" '
            f'fill="{"var(--acc)" if state != "open" else "var(--ln2)"}"/>',
            f'<text x="{x + 12:.1f}" y="{top + 20}" class="ftick" '
            f'style="fill:var(--tx3);font-size:12px;letter-spacing:.14em">'
            f'{html.escape(str(s["date"]))}</text>',
            f'<text x="{x + 12:.1f}" y="{top + 44}" class="flbl" '
            f'style="fill:var(--tx1);font-size:15px;font-weight:800">'
            f'{html.escape(str(s["name"]))}</text>',
        ]
        if s.get("body"):
            # `at_px`, because this is the one box in the package narrow
            # enough for the default estimate to overflow — and it did,
            # into the next card, with every gate green.
            for j, line in enumerate(
                    figure_scale.wrap(str(s["body"]), cw - 24, at_px=12)):
                parts.append(
                    f'<text x="{x + 12:.1f}" y="{top + 66 + j * 16:.0f}" '
                    f'class="flbl" style="fill:var(--tx2);font-size:12px">'
                    f'{html.escape(line)}</text>')
        pill = {"done": "shipped", "now": "current", "open": "not built"}[state]
        parts.append(
            f'<text x="{x + 12:.1f}" y="{top + ch - 12}" class="ftick" '
            f'style="fill:{"var(--acc)" if state != "open" else "var(--tx3)"};'
            f'font-size:12px;font-weight:700;letter-spacing:.12em">{pill}</text>')
    band = top + ch + 34
    # 3px, and the ramp starts at a visible tint rather than at `--ln2`: at
    # 2px from the rule colour the gradient was a hairline nobody could see,
    # so the hue that carries past -> present carried nothing. Found by
    # rendering it.
    parts.append(f'<line x1="0" y1="{band}" x2="{W}" y2="{band}" '
                 f'stroke="url(#tl-era)" stroke-width="3"/>')
    for i, s in enumerate(stages):
        x = i * (cw + gap) + cw / 2
        parts += [
            f'<circle cx="{x:.1f}" cy="{band}" r="5" fill="var(--bg)" '
            f'stroke="{"var(--acc)" if (s.get("state") or "done") != "open" else "var(--ln2)"}" '
            f'stroke-width="2"/>',
            f'<text x="{x:.1f}" y="{band + 22}" text-anchor="middle" '
            f'class="ftick" style="fill:var(--tx3);font-size:12px">'
            f'{html.escape(str(s["date"]))}</text>',
        ]
    return parts, band + 40


RENDERERS = {"light": _light, "general": _general, "pro": _pro}


def render(spec, tier: str = "light", orientation: str = "landscape",
           path: str = "the spec") -> str:
    if tier not in TIERS:
        raise SystemExit(f"tier must be one of {', '.join(TIERS)}")
    if orientation not in BOX_W:
        raise SystemExit(f"orientation must be one of {sorted(BOX_W)}")
    stages = _check(spec, path)
    W = BOX_W[orientation]
    body, foot_y = RENDERERS[tier](stages, spec, W, BOX_H_FLOOR[orientation])

    measure = spec["measure"]
    unit = str(measure.get("unit") or "")
    read_lines = figure_scale.wrap(str(spec["reading"]), W - 40)
    note_y = foot_y + 30 + len(read_lines) * 20
    H = max(BOX_H_FLOOR[orientation], round(note_y + 8))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" role="img" '
           f'aria-label="{html.escape(str(spec["reading"]))}">']
    out += body
    out += [
        f'<text class="axname-x" x="0" y="{foot_y:.0f}">'
        f'{html.escape(str(measure["name"]))}'
        f'{" · " + html.escape(unit) if unit else ""}</text>',
    ]
    for j, line in enumerate(read_lines):
        out.append(f'<text class="fread" x="0" y="{foot_y + 26 + j * 20:.0f}" '
                   f'style="font-size:14px;font-weight:600">{html.escape(line)}</text>')
    # LAST, and small: the evidence line is a note, not the page's subject.
    out.append(
        f'<text class="fnote" x="0" y="{note_y:.0f}" '
        f'style="fill:var(--tx4);font-size:12px">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["period"]))} · '
        f'{html.escape(str(spec["cause"]))}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; the `order` half of the contract")
    ap.add_argument("--tier", choices=TIERS, default="light",
                    help="light: points on an axis. general: blocks on a "
                         "spine, dashed where not built. pro: staged cards "
                         "over a gradient band, one limit stated per stage")
    ap.add_argument("--orientation", choices=sorted(BOX_W), default="landscape")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, tier=a.tier, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
