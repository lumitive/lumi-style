"""Two constants named EXTERNAL_GENRES answer two different questions.

`check_design.EXTERNAL_GENRES` means *whose reader is outside the building*,
and decides which documents owe a quotable takeaway (D28). Sales, marketing and
consulting all qualify.

`inspect_layout.EXTERNAL_GENRES` means *who states provenance once for the
document instead of under every figure* — design-rules.md §4 rule 9, which
scopes that to sales and marketing and says in terms that "consulting
deliverables and internal analysis keep per-page sourcing, because there the
reader is auditing the claim rather than being sold to."

The second one shipped with the first one's members, borrowed along with the
name. A consulting deck that had dropped its per-page sources was then told
`n/a, a consulting document states its provenance once in the colophon` — the
opposite of the rule — and the branch skipped `unmeasured += 1`, so the run
stopped exiting 1 on a check it had not performed.

Both directions are asserted, because the repair here is one word and the
tempting "consistency" edit is to put it back.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts" / "check"))

import check_design  # noqa: E402
import inspect_layout  # noqa: E402


def test_provenance_once_is_sales_and_marketing_only():
    """Rule 9's scope, in the constant that acts on it."""
    assert inspect_layout.EXTERNAL_GENRES == ("sales", "marketing")


def test_the_takeaway_constant_keeps_consulting():
    """D28 asks a different question and consulting is in scope for it."""
    assert "consulting" in check_design.EXTERNAL_GENRES


def test_the_two_constants_are_deliberately_different():
    """Pinned so a later 'these should match' edit fails instead of landing."""
    assert set(inspect_layout.EXTERNAL_GENRES) < set(check_design.EXTERNAL_GENRES)


def test_rule_9_still_says_consulting_keeps_per_page_sourcing():
    """The prose is the authority; if it changes, this test should be revisited
    rather than the constant quietly re-aligned."""
    rules = (ROOT / "references" / "design-rules.md").read_text(encoding="utf-8")
    assert "consulting deliverables" in rules
    assert "keep per-page sourcing" in rules
