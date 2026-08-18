"""The rule tier and the storyline are two axes, and the tier is derived.

The tier table is a claim about behaviour: that `internal` is the tier exempt
from the dash ban and `training` the tier with its own visual-share target. If
that claim stops matching the code it describes, the tier becomes a label with
nothing behind it — which is the state `genre` was in before the split.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_repo  # noqa: E402
import deliverable_registry as reg  # noqa: E402


def test_every_genre_has_a_tier():
    assert set(reg.TIERS) == set(reg.GENRES)


def test_there_are_three_tiers():
    """Three, because three is what the behaviour actually distinguishes."""
    assert len(set(reg.TIERS.values())) == 3


def test_tier_of_raises_loudly_on_an_unknown_genre():
    """A genre resolving to a default tier would grade a document against rules
    that are not its own and report it green."""
    try:
        reg.tier_of("pitch")
    except KeyError:
        return
    raise AssertionError("tier_of accepted a genre that does not exist")


def test_storyline_does_not_multiply_the_reference_obligation():
    """The obligation hangs off the tier. However many storylines the roster
    grows, three tiers, and the number of reference documents to accumulate
    is three."""
    assert len(set(reg.TIERS.values())) < len(reg.STORYLINES)


def test_the_live_tier_table_matches_the_code_it_describes():
    assert check_repo.check_two_axis_vocabulary() == []


def test_tier_table_diverging_from_dash_banned_fails(monkeypatch):
    monkeypatch.setattr(reg, "TIERS", dict(reg.TIERS, internal="sales"))
    errors = check_repo.check_two_axis_vocabulary()
    assert any("dash-exempt" in e for e in errors)


def test_tier_table_diverging_from_visual_share_fails(monkeypatch):
    monkeypatch.setattr(reg, "TIERS", dict(reg.TIERS, training="sales"))
    errors = check_repo.check_two_axis_vocabulary()
    assert any("visual-share" in e for e in errors)


def test_empty_storyline_vocabulary_fails(monkeypatch):
    monkeypatch.setattr(reg, "STORYLINES", ())
    assert any("decorative" in e for e in check_repo.check_two_axis_vocabulary())
