#!/usr/bin/env python3
"""Put CONTENT into a library shape, at coordinates nobody has to guess.

**Why this exists.** The only way to put words into one of the 206 vendored
units was:

    shape_figure(shape, label_a, label_b)   # two words, bottom-left and
                                            # bottom-right of the drawing

Two words. So a `position` unit arrived as an empty box, a staircase carried no
dates, and an arrow chain named none of its stages — and the owner's review of
the first deck built that way said exactly that, page by page: the figures
were too simple, the time points a page stated appeared nowhere on its drawing,
and the quadrant was an empty box. It was never the author being brief; the
interface could not express more.

**The three traps this module exists to absorb**, all of which cost a
render-and-look cycle at least once:

1. **Every one of the 206 viewBoxes has a non-zero origin.** A `<use>` without
   explicit `x/y/width/height` renders shifted — often entirely off-canvas —
   and raises nothing. The values come from `assets/shapes/geometry.json`,
   never from a caller's arithmetic.
2. **`preserveAspectRatio` centres and scales to fit.** A near-square unit
   dropped into a wide box is painted about 245 units wide inside a 640-wide
   slot, so a slot position computed as a fraction of the SLOT lands outside
   the drawing. `fitted()` returns the rectangle actually painted.
3. **`fill="…"` on a `<text>` loses to the stylesheet.** Every reference figure
   in this package uses `style="fill:…"` without exception, and so does this.

Slots are addressed in the unit's own fractional space — `(0.25, 0.30)` is a
quarter across and a third down THE DRAWING — and this module maps them.

Standard library only.
"""
from __future__ import annotations

import html
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The scaffold's figure slot, and the box every composed figure is drawn into.
BOX_W, BOX_H = 640.0, 300.0
DRAW_H = 239.0          # the drawing; the rest is the axis name and the source

# Text roles inside a figure, and the sizes they render at. **12px is the
# floor**, and it is a decision rather than an inheritance: the reference deck
# the owner named goes to 9.3px, which its own spec justifies by scoping the
# audience to a meeting-room screen and a PDF read at arm's length, and states
# plainly that the layout is unfit for a large auditorium. LUMI's delivery includes a projected screen,
# so this package stops at 12 and says why.
ROLE = {
    "head": ("flbl", 13.5, "var(--tx1)", 700),
    "body": ("flbl", 12.0, "var(--tx2)", 400),
    "note": ("ftick", 12.0, "var(--tx3)", 400),
    "on-fill": ("flbl", 13.0, "var(--bg)", 700),
    "on-fill-sub": ("ftick", 12.0, "var(--bg)", 400),
}
TEXT_FLOOR = 12.0


class SlotError(ValueError):
    """A composition that cannot be drawn. Raised, never returned as an empty
    figure: a shape with no content is the defect this module was written for,
    so producing one silently would be the same failure one layer down."""


def geometry(shape_id: str) -> dict:
    """-> the unit's recorded geometry. Raises rather than guessing."""
    path = ROOT / "assets" / "shapes" / "geometry.json"
    try:
        units = json.loads(path.read_text(encoding="utf-8"))["units"]
    except (OSError, ValueError, KeyError) as exc:
        raise SlotError(f"{path}: the shape geometry manifest could not be "
                        f"read ({exc}), so no slot position can be computed — "
                        f"this is not a figure that composed cleanly") from exc
    if shape_id not in units:
        raise SlotError(
            f"{shape_id!r} is not in the geometry manifest. "
            f"`embed_shapes.py --list` names every unit the library ships; a "
            f"`<use>` at a guessed position renders off-canvas and says nothing")
    return units[shape_id]


def fitted(shape_id: str, box_w: float = BOX_W,
           box_h: float = DRAW_H) -> tuple[float, float, float, float]:
    """-> (x, y, w, h) of the rectangle the unit is ACTUALLY painted into.

    `<use>` maps a symbol under `preserveAspectRatio="xMidYMid meet"`, so a
    unit whose aspect differs from the slot's is scaled to fit and centred. A
    caller placing a label at a fraction of the SLOT puts it outside the
    drawing — which is what happened to the first 2x2 this package composed,
    twice, and was only visible in the render.
    """
    g = geometry(shape_id)
    sw, sh = float(g["viewBox"][2]), float(g["viewBox"][3])
    if sw <= 0 or sh <= 0:
        raise SlotError(f"{shape_id}: the manifest records a zero-sized "
                        f"viewBox, so nothing can be placed against it")
    scale = min(box_w / sw, box_h / sh)
    w, h = sw * scale, sh * scale
    return (box_w - w) / 2, (box_h - h) / 2, w, h


def _text(x: float, y: float, s: str, role: str = "body",
          anchor: str = "middle") -> str:
    if role not in ROLE:
        raise SlotError(f"{role!r} is not a text role; the roles are "
                        f"{', '.join(sorted(ROLE))}")
    cls, size, colour, weight = ROLE[role]
    if size < TEXT_FLOOR:
        raise SlotError(f"role {role!r} is set at {size}px, below the {TEXT_FLOOR}px "
                        f"floor design-rules.md states for figure text")
    return (f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" '
            f'text-anchor="{anchor}" style="fill:{colour};font-size:{size}px;'
            f'font-weight:{weight}">{html.escape(str(s))}</text>')


def compose(shape_id: str, slots, *, axis_x: str = "", axis_y: str = "",
            source: str = "", aria: str = "") -> str:
    """-> an `<svg>` carrying the unit AND the words that belong in it.

    `slots` is a list of `{at: (fx, fy), head, body?, note?, on_fill?}` where
    `at` is the position in the DRAWING's own fractional space. `on_fill` picks
    the light text roles for a slot that sits on a filled region.

    Raises when `slots` is empty: a library shape composed with no words is an
    icon wearing a caption, and shipping one is the defect this replaces.
    """
    if not slots:
        raise SlotError(
            f"{shape_id} was composed with no slots. A library unit carrying "
            f"no content is decoration — design-rules.md P-4: a figure that "
            f"carries no argument violates that clause rather than satisfying "
            f"it. Give it the page's own names and numbers, or draw something "
            f"else.")
    g = geometry(shape_id)
    use = g["use"]
    x0, y0, w, h = fitted(shape_id)

    parts = [
        f'<svg viewBox="0 0 {BOX_W:.0f} {BOX_H:.0f}" role="img" '
        f'aria-label="{html.escape(aria or shape_id)}">',
        f'<use href="#shape-{shape_id}" x="{use["x"]:.2f}" y="{use["y"]:.2f}" '
        f'width="{use["width"]:.2f}" height="{use["height"]:.2f}"/>',
    ]
    for i, slot in enumerate(slots):
        at = slot.get("at")
        if not (isinstance(at, (list, tuple)) and len(at) == 2):
            raise SlotError(f"slot {i} has no `at: (fx, fy)` position")
        fx, fy = float(at[0]), float(at[1])
        if not (0.0 <= fx <= 1.0 and 0.0 <= fy <= 1.0):
            raise SlotError(
                f"slot {i} sits at ({fx}, {fy}), outside the drawing. Slot "
                f"positions are fractions of the UNIT, not of the figure box — "
                f"a fraction of the box lands outside a unit that was scaled "
                f"to fit")
        if not slot.get("head"):
            raise SlotError(f"slot {i} has no `head`; a slot with no name "
                            f"labels nothing")
        px, py = x0 + fx * w, y0 + fy * h
        on = slot.get("on_fill")
        parts.append(_text(px, py, slot["head"],
                           "on-fill" if on else "head",
                           slot.get("anchor", "middle")))
        if slot.get("body"):
            parts.append(_text(px, py + 16, slot["body"],
                               "on-fill-sub" if on else "body",
                               slot.get("anchor", "middle")))
        if slot.get("note"):
            parts.append(_text(px, py + 31, slot["note"], "note",
                               slot.get("anchor", "middle")))

    if axis_y:
        parts.append(f'<text class="axname-y" x="14" y="{DRAW_H / 2:.0f}" '
                     f'text-anchor="middle">{html.escape(axis_y)}</text>')
    if axis_x:
        parts.append(f'<text class="axname-x" x="{BOX_W / 2:.0f}" '
                     f'y="{DRAW_H + 26:.0f}" text-anchor="middle">'
                     f'{html.escape(axis_x)}</text>')
    if source:
        # LAST text node in the drawing — design-rules §4 rule 17. The owner's
        # review put it precisely: the evidence line belongs above the footer
        # rule as a note, not in a main position.
        parts.append(f'<text class="fnote" x="0" y="{BOX_H - 6:.0f}" '
                     f'style="fill:var(--tx4);font-size:12px">'
                     f'{html.escape(source)}</text>')
    parts.append("</svg>")
    return "\n      ".join(parts)
