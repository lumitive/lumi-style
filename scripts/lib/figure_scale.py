#!/usr/bin/env python3
"""Axis arithmetic and text fitting, shared by every figure renderer.

**Why it is a module.** `scatter_svg` carried `_num`, `_nice`, `_wrap` and
`_fmt` privately, and the second renderer arrived. Two copies of "how an axis
picks its round numbers" is exactly the class `evals/single-source.json` exists
to prevent: one gets corrected and one does not, and the two figures in one
document then disagree about their own ticks. The register's entry is
`figure-scale` and `check_one_home` holds it.

Every function here is about honesty rather than convenience:

- `nice_ceiling` and `nice_range` round **outward**, never inward. A range
  chosen to hug the data is how an axis manufactures a relation
  (design-rules.md DR-20 rule 5).
- `wrap` estimates from the character count and is deliberately conservative,
  because this package ships no font metrics. The portrait box is 620 units
  wide and a reading line once ran 34 units outside its own viewBox, where
  `figure_clipped` found it: a sentence that fits the wide figure is not a
  sentence that fits the tall one.
- `num` returns `None` rather than a substitute. A value a renderer cannot read
  has no honest length, and every caller refuses instead of guessing.

Standard library only.
"""
from __future__ import annotations

import math


def num(v):
    """-> the value as a float, or None. Never a fallback."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def step_for(span: float) -> float:
    """-> a round step covering `span` in about four intervals."""
    raw = span / 4.0
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1.0
    return next((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw),
                10 * mag)


def nice_range(lo: float, hi: float) -> tuple[float, float, float]:
    """-> (lo, hi, step) covering the data on round numbers, rounded OUTWARD."""
    if hi <= lo:
        hi = lo + 1.0
    step = step_for(hi - lo)
    return math.floor(lo / step) * step, math.ceil(hi / step) * step, step


def nice_ceiling(hi: float) -> float:
    """-> a round top for an axis that starts at ZERO.

    Separate from `nice_range` because a length encoding has no choice about
    its floor: a bar measured from anywhere but zero misstates every ratio on
    the figure, and that is the distortion the benchmark tool refuses to be
    able to express.
    """
    if hi <= 0:
        return 0.0
    step = step_for(hi)
    return math.ceil(hi / step) * step


def ticks(hi: float) -> list[float]:
    """-> the tick values from zero to `hi` inclusive, on round numbers."""
    if hi <= 0:
        return []
    step = step_for(hi)
    out, t = [], 0.0
    while t <= hi + step / 1000:
        out.append(round(t, 10))
        t += step
    return out


def fmt(v, step: float = 1.0) -> str:
    """-> the value as a reader would write it."""
    return (f"{v:.0f}" if step >= 1 and abs(v - round(v)) < 1e-9
            else f"{v:g}")


# Advance per character as a share of the font size, MEASURED rather than
# guessed: a 34-character card body set at 12px occupied 221 units where the
# 5.6 default budgeted 205, so it ran into the neighbouring card. 6.5 / 12 is
# 0.54, and the ratio is rounded up because this estimate must err wide.
#
# The 5.6 default stays for callers that do not say their size. It corresponds
# to a 10px face and is safe where it is used — every other caller wraps a
# reading line into a box hundreds of units wide, where a loose estimate costs
# a wasted line rather than an overflow. Passing `at_px` is how a caller
# wrapping into a TIGHT box gets an estimate that holds.
PER_CHAR_RATIO = 0.55


def wrap(text, width_units: float, per_char: float = 5.6,
         at_px: float | None = None) -> list[str]:
    """-> `text` broken to fit `width_units`, as a list of lines.

    `at_px` is the size the text will actually be set at. Give it whenever the
    box is narrow enough that being wrong by a character matters.
    """
    if at_px is not None:
        per_char = PER_CHAR_RATIO * float(at_px)
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
