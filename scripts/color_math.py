"""The one sRGB/WCAG color implementation, shared by every checker and
generator that used to carry its own copy.

Until 0.1.420 this math existed in four places with two different linearizer
thresholds: 0.03928 (the WCAG 2.0 text, in check_repo / check_design /
inspect_layout) and 0.04045 (IEC 61966-2-1, in build_region_palette — the
value the WCAG errata settled on). The 0.1.415 escape pattern — a fix landing
in one copy while the same class stays live in another — is exactly what a
single module ends.

THE THRESHOLD IS 0.04045, and the unification is byte-safe by measurement,
not by hope: no integer channel value c in 0..255 has c/255 inside
(0.03928, 0.04045], so for every hex- or pixel-derived color the two
thresholds compute identical luminance (tests/test_color_math.py pins this).
The only inputs in the band are the non-integer alpha mixes in check_repo's
contrast floor, where the difference is at most 2e-5 on a ratio floored at
whole tenths.

This module is held to strict mypy (disallow_untyped_defs) from birth —
see pyproject.toml.
"""
from __future__ import annotations

from collections.abc import Sequence

SRGB_LINEAR_THRESHOLD = 0.04045


def srgb_linear(v: float) -> float:
    """Linearize one sRGB channel, 0-1 domain."""
    return v / 12.92 if v <= SRGB_LINEAR_THRESHOLD else ((v + 0.055) / 1.055) ** 2.4


def srgb_encode(v: float) -> float:
    """The inverse: one linear channel back to gamma-encoded sRGB, 0-1 domain."""
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def luma255(rgb: Sequence[float]) -> float:
    """WCAG relative luminance of an (r, g, b) with channels in 0-255."""
    r, g, b = (srgb_linear(c / 255) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_from_luma(a: float, b: float) -> float:
    """WCAG contrast ratio between two relative luminances."""
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def contrast255(fg: Sequence[float], bg: Sequence[float]) -> float:
    """WCAG contrast ratio between two 0-255 (r, g, b) colors."""
    return contrast_from_luma(luma255(fg), luma255(bg))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """'#RRGGBB' (leading # optional) -> (r, g, b) ints in 0-255."""
    v = value.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def contrast_hex(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    return contrast255(hex_to_rgb(fg), hex_to_rgb(bg))


def mix255(ink: Sequence[float], surface: Sequence[float],
           alpha: float) -> tuple[float, float, float]:
    """ink at `alpha` composited over an opaque surface, channels 0-255.

    Deliberately returns floats: the alpha ladder produces non-integer
    channels, and rounding here would hide exactly the band where the old
    thresholds disagreed.
    """
    return (ink[0] * alpha + surface[0] * (1 - alpha),
            ink[1] * alpha + surface[1] * (1 - alpha),
            ink[2] * alpha + surface[2] * (1 - alpha))
