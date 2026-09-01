#!/usr/bin/env python3
"""Emit a LUMI two-by-two as SVG, from its data.

**Why this exists.** `position` was drawable only as a bare library unit
carrying two words, so the first 2x2 this package composed was an empty green
box with an axis name at each end. The owner's review called it too simple
and named the standard: `_calibration/calib2-market` Figure 4. Six things that figure does and the empty box did not:

1. The **answer quadrant** is washed and carries a headline AND a subline. Only
   that one is labelled; naming all four turns a finding into a legend.
2. Both axes are drawn **outside** the plot, arrowed, and each carries a
   low → high ramp gloss, so an axis is a capability scale rather than a word.
3. Every item is a dot **plus a name plus a qualifier** — the qualifier is what
   makes the map an argument instead of a scatter of logos.
4. A player who **exited** is kept and dimmed. Deleting them loses the finding;
   dimming them states it.
5. Our own position is marked in a distinct token and said to be a **target**,
   not a claim about today.
6. A placement-provenance footnote, and the truth condition DR-11 requires:
   the two axes are independent.

    python3 scripts/render/quadrant_svg.py --data spec.json

The spec is the contract's `position` half, plus the fields that carry those
six things:

    {
      "move": "position",
      "axes": {"x": {"name": "…", "unit": "…", "low": "templates",
                     "high": "brand-governed system"},
               "y": {"name": "…", "unit": "…", "low": "layout only",
                     "high": "checkable analysis"}},
      "items": [{"label": "Gamma", "x": 0.26, "y": 0.31,
                 "note": "25M+ users, speed-led", "state": "rival"}],
      "open": {"at": "upper-right", "head": "…", "body": "…"}
    }

`state` is `rival` / `exited` / `ours`, and it is not decoration: `exited`
draws dimmed and `ours` takes the lime. `x` and `y` are fractions of each axis,
because a 2x2's axes are ordinal — a number on them would claim a precision the
placement does not have, and `open` says which quadrant is the finding.

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

BOX = {"landscape": (660, 400), "portrait": (620, 560)}
# The left gutter holds TWO upright text runs (the axis name and its ramp),
# so it is wider than the reference figure's, which parked a horizontal
# name in the corner instead.
PLOT = {"x": 92.0, "y": 30.0, "w": 500.0, "h": 270.0}

STATES = ("rival", "exited", "ours")
QUADRANTS = {"upper-right": (0.5, 0.0), "upper-left": (0.0, 0.0),
             "lower-right": (0.5, 0.5), "lower-left": (0.0, 0.5)}

MARK = {"rival": ("var(--tx3)", 1.0), "exited": ("var(--tx3)", 0.45),
        "ours": ("var(--lime)", 1.0)}


def _check(spec, path):
    figure_spec.refuse_if_unusable(spec, path)
    items = spec.get("items") or []
    bad = [i for i, it in enumerate(items)
           if (it.get("state") or "rival") not in STATES]
    if bad:
        raise SystemExit(
            f"{path}: item(s) {bad} declare a state outside "
            f"{', '.join(STATES)}. `exited` is what dims a player who left the "
            f"market, and dimming one is a finding; a free-text state draws "
            f"like a live rival.")
    naked = [i for i, it in enumerate(items) if not str(it.get("note") or "").strip()]
    if naked:
        raise SystemExit(
            f"{path}: item(s) {naked} carry no `note`. A name on a map is a "
            f"logo; the qualifier is what makes the placement an argument — "
            f"the difference the review named.")
    for k in ("x", "y"):
        ax = (spec.get("axes") or {}).get(k) or {}
        if not (str(ax.get("low") or "").strip() and str(ax.get("high") or "").strip()):
            raise SystemExit(
                f"{path}: axis `{k}` gives no `low`/`high` ramp. An axis named "
                f"but not scaled is a word, and a reader cannot tell which end "
                f"is more.")
    opening = spec.get("open") or {}
    if opening and opening.get("at") not in QUADRANTS:
        raise SystemExit(
            f"{path}: `open.at` is {opening.get('at')!r}; it names the quadrant "
            f"that carries the finding and must be one of "
            f"{', '.join(sorted(QUADRANTS))}.")
    return items


def render(spec, orientation="landscape", path="the spec"):
    if orientation not in BOX:
        raise SystemExit(f"orientation must be one of {sorted(BOX)}")
    items = _check(spec, path)
    if str(spec.get("move")).lower() != "position":
        raise SystemExit(
            f"{path} declares move {spec.get('move')!r}; this tool draws "
            f"`position`. assets/frameworks.json says which tool draws which "
            f"move.")

    W, H = BOX[orientation]
    px, py, pw, ph = PLOT["x"], PLOT["y"], PLOT["w"], PLOT["h"]
    axes = spec["axes"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{html.escape(str(spec["reading"]))}">',
        '<defs><marker id="q-ar" viewBox="0 0 8 8" refX="7" refY="4" '
        'markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0 0 L8 4 L0 8 z" fill="var(--tx1)"/></marker></defs>',
        # ONE plot rect and two crossing lines, never four rects: four boxes
        # read as four categories, and the point of a 2x2 is two continua.
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" '
        f'fill="var(--card-bg)" stroke="var(--ln1)"/>',
    ]

    opening = spec.get("open") or {}
    if opening:
        qx, qy = QUADRANTS[opening["at"]]
        parts.append(
            f'<rect x="{px + qx * pw:.1f}" y="{py + qy * ph:.1f}" '
            f'width="{pw / 2:.1f}" height="{ph / 2:.1f}" '
            f'fill="var(--acc-wash)" opacity="0.6"/>')

    parts += [
        f'<line x1="{px + pw / 2:.1f}" y1="{py}" x2="{px + pw / 2:.1f}" '
        f'y2="{py + ph}" stroke="var(--ln1)"/>',
        f'<line x1="{px}" y1="{py + ph / 2:.1f}" x2="{px + pw}" '
        f'y2="{py + ph / 2:.1f}" stroke="var(--ln1)"/>',
    ]

    if opening:
        qx, qy = QUADRANTS[opening["at"]]
        lx, ly = px + qx * pw + 8, py + qy * ph + 20
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" class="flbl" '
            f'style="fill:var(--acc);font-size:13px;font-weight:700">'
            f'{html.escape(str(opening.get("head") or ""))}</text>')
        if opening.get("body"):
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + 16:.1f}" class="flbl" '
                f'style="fill:var(--tx2);font-size:12px">'
                f'{html.escape(str(opening["body"]))}</text>')

    # AXES OUTSIDE THE PLOT, each with its ramp. The y name is horizontal in
    # the left gutter rather than rotated: the reference figure parks it there,
    # and rotated text at 12px is the thing `figure_axis_orientation` exists
    # to catch.
    parts += [
        f'<path d="M{px} {py + ph + 16} L{px + pw} {py + ph + 16}" '
        f'stroke="var(--tx1)" stroke-width="1.6" marker-end="url(#q-ar)"/>',
        f'<text x="{px}" y="{py + ph + 36}" class="axname-x" '
        f'style="font-size:13px;font-weight:600">'
        f'{html.escape(str(axes["x"]["name"]))} →</text>',
        f'<text x="{px}" y="{py + ph + 52}" class="flbl" '
        f'style="fill:var(--tx2);font-size:12px">'
        f'{html.escape(str(axes["x"]["low"]))} → '
        f'{html.escape(str(axes["x"]["high"]))}</text>',
        f'<path d="M{px - 16} {py + ph} L{px - 16} {py}" '
        f'stroke="var(--tx1)" stroke-width="1.6" marker-end="url(#q-ar)"/>',
        # THE Y RAMP RIDES THE Y AXIS. `.axname-y` is set upright by `tokens/`
        # and reads bottom to top, so two horizontal lines parked beside it
        # crossed straight through it — three runs of text in one place, which
        # the render showed at once. The ramp is one string on one upright
        # line, in the axis's own direction.
        f'<text x="{px - 34}" y="{py + ph / 2:.1f}" class="axname-y" '
        f'text-anchor="middle" style="font-size:13px;font-weight:600">'
        f'{html.escape(str(axes["y"]["name"]))} ↑</text>',
        f'<text x="{px - 50}" y="{py + ph / 2:.1f}" class="axname-y" '
        f'text-anchor="middle" style="font-size:12px;fill:var(--tx2)">'
        f'{html.escape(str(axes["y"]["low"]))} → '
        f'{html.escape(str(axes["y"]["high"]))}</text>',
    ]

    for it in items:
        fx = figure_scale.num(it.get("x"))
        fy = figure_scale.num(it.get("y"))
        if fx is None or fy is None or not (0 <= fx <= 1 and 0 <= fy <= 1):
            raise SystemExit(
                f"{path}: {it.get('label')!r} sits at ({it.get('x')}, "
                f"{it.get('y')}); a placement is a fraction of each axis "
                f"between 0 and 1, because a 2x2's axes are ordinal and a "
                f"number on them would claim a precision the placement has not.")
        cx = px + fx * pw
        cy = py + (1 - fy) * ph        # y grows upward on the page
        state = it.get("state") or "rival"
        fill, op = MARK[state]
        parts += [
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" style="fill:{fill}" '
            f'opacity="{op}"/>',
            f'<text x="{cx + 12:.1f}" y="{cy + 1:.1f}" class="flbl" '
            f'style="fill:var(--tx1);font-size:13px;font-weight:700" '
            f'opacity="{op if state != "exited" else 0.55}">'
            f'{html.escape(str(it["label"]))}</text>',
            f'<text x="{cx + 12:.1f}" y="{cy + 15:.1f}" class="flbl" '
            f'style="fill:var(--tx2);font-size:12px" '
            f'opacity="{op if state != "exited" else 0.7}">'
            f'{html.escape(str(it["note"]))}</text>',
        ]

    # The truth condition DR-11 requires of any 2x2, and where the placements
    # came from. Last text node in the drawing, §4 rule 17.
    parts.append(
        f'<text x="{px}" y="{H - 8}" class="fnote" '
        f'style="fill:var(--tx3);font-size:12px">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["period"]))} · the two axes are '
        f'independent capabilities</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; the `position` half of the contract")
    ap.add_argument("--orientation", choices=sorted(BOX), default="landscape")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
