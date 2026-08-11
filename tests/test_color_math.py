"""Tests for scripts/color_math.py — the one sRGB/contrast implementation.

Written first (0.1.419) as characterization tests against the four duplicated
copies; re-pointed here when 0.1.420 extracted the module. The byte-safety
argument for the threshold unification (0.03928 -> 0.04045) is preserved
below as pure-math tests so the decision stays recorded and enforced.
"""
import check_repo
import color_math
import pytest


def _old_lin_03928(c: float) -> float:
    """The retired 0.03928-threshold linearizer, kept HERE ONLY as the
    reference the byte-safety tests compare against."""
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def test_lin_endpoints():
    assert color_math.srgb_linear(0.0) == 0.0
    assert color_math.srgb_linear(1.0) == pytest.approx(1.0)


def test_lin_branches():
    assert color_math.srgb_linear(0.04) == pytest.approx(0.04 / 12.92)
    assert color_math.srgb_linear(0.05) == pytest.approx(
        ((0.05 + 0.055) / 1.055) ** 2.4)


def test_encode_inverts_linear():
    for v in (0.0, 0.001, 0.0031308, 0.04, 0.2, 0.7, 1.0):
        assert color_math.srgb_encode(color_math.srgb_linear(v)) == pytest.approx(v)


def test_black_on_white_is_21():
    assert color_math.contrast255((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)
    assert color_math.contrast_hex("#FFFFFF", "#000000") == pytest.approx(21.0)


def test_hex_to_rgb():
    assert color_math.hex_to_rgb("#B08D2E") == (0xB0, 0x8D, 0x2E)
    assert color_math.hex_to_rgb("1A1A1A") == (26, 26, 26)


def test_mix255_endpoints():
    ink, surface = (0, 0, 0), (255, 255, 255)
    assert color_math.mix255(ink, surface, 1.0) == (0.0, 0.0, 0.0)
    assert color_math.mix255(ink, surface, 0.0) == (255.0, 255.0, 255.0)


def test_threshold_unification_is_integer_channel_safe():
    """The recorded byte-safety argument: no integer channel value c has
    c/255 inside (0.03928, 0.04045], so against the retired threshold every
    hex- or pixel-derived color computes identical luminance."""
    for c in range(256):
        assert color_math.srgb_linear(c / 255) == pytest.approx(
            _old_lin_03928(c), abs=1e-12)


def test_threshold_band_difference_is_immaterial():
    """Between the two lines (non-integer mixes only — the alpha ladder),
    the difference exists and is at most ~2e-5 in linear light."""
    v = 0.040  # 0.03928 < v ≤ 0.04045
    assert color_math.srgb_linear(v) != _old_lin_03928(v * 255)
    assert color_math.srgb_linear(v) == pytest.approx(
        _old_lin_03928(v * 255), abs=2e-5)


def _tokens(text_ladder, floor=4.5):
    return {
        "contrast": {"floor_text": floor},
        "palette": {
            "light": {
                "ladder_base": "rgba(0,0,0,ALPHA)",
                "bg": "#FFFFFF",
                "card_bg": "#F5F5F2",
                "text_ladder": text_ladder,
            },
        },
    }


def test_contrast_floor_guard_passes_readable_ladder():
    assert check_repo._check_contrast_floor(_tokens([1.0, 0.87, 0.66])) == []


def test_contrast_floor_guard_fails_unreadable_ladder():
    # A 0.2-alpha black on white is ~1.5:1 — the 0.1.337 defect shape. The
    # guard must be able to fail, which is the whole point of the guard. It
    # reports once per surface (bg and card_bg), so two errors, same step.
    errors = check_repo._check_contrast_floor(_tokens([1.0, 0.2]))
    assert len(errors) == 2
    assert all("text_ladder[1]" in e for e in errors)
