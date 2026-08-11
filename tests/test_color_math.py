"""Characterization tests for the sRGB/contrast math, written BEFORE the
dedup refactor extracts it into scripts/color_math.py.

The repository currently carries this math in several places with two
different linearizer thresholds:

- check_design._lin      takes 0-255, threshold 0.03928 (the WCAG 2.0 text)
- build_region_palette._lin takes 0-1, threshold 0.04045 (IEC 61966-2-1,
  what the WCAG errata settled on)
- check_repo's copy is nested inside _check_contrast_floor (tested through
  that guard), threshold 0.03928
- inspect_layout's copy is nested inside its ground audit (Playwright path,
  not tested here), threshold 0.03928

These tests pin today's behavior of each copy, including the exact spot the
thresholds disagree, so the extraction can prove it changed nothing it did
not mean to change.
"""
import build_region_palette
import check_design
import check_repo
import pytest


def test_check_design_lin_endpoints():
    assert check_design._lin(0) == 0.0
    assert check_design._lin(255) == pytest.approx(1.0)


def test_check_design_lin_branches():
    # 10/255 = 0.0392… ≤ 0.03928 → linear branch; 11/255 = 0.0431… → gamma.
    assert check_design._lin(10) == pytest.approx((10 / 255) / 12.92)
    assert check_design._lin(11) == pytest.approx(
        ((11 / 255 + 0.055) / 1.055) ** 2.4)


def test_check_design_black_on_white_is_21():
    assert check_design.contrast((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)
    assert check_design.contrast((255, 255, 255), (0, 0, 0)) == pytest.approx(21.0)


def test_region_palette_lin_branches():
    # 0-1 domain, 0.04045 threshold.
    assert build_region_palette._lin(0.04) == pytest.approx(0.04 / 12.92)
    assert build_region_palette._lin(0.05) == pytest.approx(
        ((0.05 + 0.055) / 1.055) ** 2.4)


def test_region_palette_black_on_white_is_21():
    assert build_region_palette.contrast("#000000", "#FFFFFF") == pytest.approx(21.0)


def test_thresholds_agree_on_every_integer_channel():
    """Why the two thresholds never produced a divergent shipped byte: no
    integer channel value c has c/255 inside (0.03928, 0.04045], so for real
    pixel data the two copies compute identical luminance. The unification to
    0.04045 is therefore byte-safe for everything generated from hex colours.
    """
    for c in range(256):
        assert check_design._lin(c) == pytest.approx(
            build_region_palette._lin(c / 255), abs=1e-12)


def test_thresholds_disagree_between_the_two_lines():
    """The band where they DO differ — non-integer channels, which only the
    alpha-mix path in check_repo's contrast floor can produce. Documented so
    the refactor's choice of 0.04045 is a recorded decision, not an accident.
    """
    v = 0.040  # 0.03928 < v ≤ 0.04045
    gamma_side = check_design._lin(v * 255)
    linear_side = build_region_palette._lin(v)
    assert gamma_side != linear_side
    assert gamma_side == pytest.approx(linear_side, abs=2e-5)  # and immaterially so


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
