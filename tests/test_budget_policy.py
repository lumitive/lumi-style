"""One parameter carrying one policy.

`--budget` and `--hard-cap` were two peer integers with no stated relationship,
which reads as two names for one thing — and the owner read it that way. They
are not: the floor is granted outright, the ceiling is what renewal may never
pass, and `_run_with_budget` needs both. A single maximum deletes the floor,
which is the failure `DRIVE_TIMEOUT = 1800` produced on 2026-08-21.
"""
import pytest
import run_conformance as rc


def test_the_default_is_todays_two_constants():
    assert rc.parse_budget(None) == (rc.DRIVE_BASE_BUDGET, rc.DRIVE_HARD_CAP)
    assert rc.parse_budget("") == (rc.DRIVE_BASE_BUDGET, rc.DRIVE_HARD_CAP)


@pytest.mark.parametrize("text,want", [
    ("1800:3600", (1800, 3600)),
    ("30m:1h",    (1800, 3600)),
    ("600",       (600, rc.DRIVE_HARD_CAP)),
    ("2h",        (7200, 7200)),          # a floor above the default ceiling
    ("3600:3600", (3600, 3600)),          # no renewal, expressible on purpose
])
def test_the_policy_is_one_string(text, want):
    assert rc.parse_budget(text) == want


@pytest.mark.parametrize("text,says", [
    ("1:2:3",     "FLOOR or FLOOR:CEILING"),
    ("abc",       "not a duration"),
    ("0",         "not positive"),
    ("-5",        "not positive"),
    ("3600:1800", "below"),
    (":",         "an empty half"),
])
def test_a_budget_that_cannot_hold_says_why(text, says):
    with pytest.raises(ValueError) as exc:
        rc.parse_budget(text)
    assert says in str(exc.value)


def test_a_ceiling_below_the_floor_is_refused_rather_than_clamped():
    """Clamping would make the floor unspendable and say nothing."""
    with pytest.raises(ValueError):
        rc.parse_budget("3600:60")
