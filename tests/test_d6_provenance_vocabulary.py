"""D6's provenance vocabulary recognises the phrase, and still fails its absence.

Widening a pattern is the move that quietly disables a check, so this asserts
both directions. The case: a colophon reading "every claim traces to the
research report of 2026-08-11" was reported as missing its provenance on all
fifteen pages, because "traces to" was not on the list. The document was right
and the checker was wrong — and the cheapest way to clear that failure is to
edit correct prose until a pattern matches, which is the checker writing the
document.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import check_design  # noqa: E402


def _doc(colophon):
    return (
        '<!doctype html><html lang="en"><body>'
        '<section class="page"><div class="foot">A2UI · 1 / 1</div></section>'
        f'<p class="colophon">{colophon}</p>'
        "</body></html>"
    )


@pytest.mark.parametrize("colophon", [
    "Every claim traces to the research report of 2026-08-11.",
    "Every claim traces back to the research report of 2026-08-11.",
    "Figures are derived from the 2026 shipment dataset.",
    "Figures derive from the 2026 shipment dataset.",
    "Based on the operator interviews of March.",
    "Source: the 2026 shipment dataset.",
    "Provenance is recorded in the appendix.",
    "The numbers are drawn from the quarterly filing.",
    "Everything here comes from the audited accounts.",
])
def test_a_stated_provenance_is_recognised(colophon):
    result = check_design.d6_footer(_doc(colophon))
    assert result["missing_source"] == [], \
        f"a colophon that states its provenance was failed: {colophon!r}"


@pytest.mark.parametrize("colophon", [
    "Built with lumi-style 0.1.489. Internal analysis.",
    "Confidential. Do not forward.",
    "",
])
def test_no_provenance_still_fails(colophon):
    """The widening must not have turned the check off."""
    result = check_design.d6_footer(_doc(colophon))
    assert result["missing_source"] == [0], \
        f"a colophon with no provenance passed: {colophon!r}"
