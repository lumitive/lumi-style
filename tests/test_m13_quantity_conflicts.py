"""M13 — one quantity, one value.

The point of these tests is the false-positive side. A checker that fires on a
time series or a target/actual pair would make an author edit correct prose to
silence it, which this repository has shipped once already.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check"))

import check_prose as cp  # noqa: E402


def test_contradiction_is_found():
    text = ("The install backlog stood at 4.2 million units when the review began. "
            "Later analysis of the same install backlog put it at 4.5 million units.")
    found = cp.quantity_conflicts(text)
    assert found and found[0][0] == "install backlog"


def test_time_series_is_not_a_contradiction():
    text = "Revenue in 2024 was 4.2 million. Revenue in 2025 was 4.8 million."
    assert cp.quantity_conflicts(text) == []


def test_target_and_actual_are_not_a_contradiction():
    text = "The target coverage is 90 percent. Actual coverage is 87 percent."
    assert cp.quantity_conflicts(text) == []


def test_regional_split_is_not_a_contradiction():
    text = ("Meter density in the rural phase is 40 percent. "
            "Meter density in the urban phase is 78 percent.")
    assert cp.quantity_conflicts(text) == []


def test_consistent_repetition_is_silent():
    text = ("Network coverage is 87 percent today. "
            "Network coverage is 87 percent on the second measurement.")
    assert cp.quantity_conflicts(text) == []


def test_a_single_mention_cannot_contradict_anything():
    assert cp.quantity_conflicts("The install backlog is 4.2 million units.") == []


def test_units_must_match_before_anything_is_claimed():
    """4.2 million units and 4.2 percent are not the same quantity."""
    text = ("The install backlog is 4.2 million. "
            "The install backlog grew 7 percent.")
    assert cp.quantity_conflicts(text) == []

