"""The verdict on a PR's check rollup is about EVERY job, never any job.

`ci_wait.sh` used to judge the rollup with a bash substring match,
`*COMPLETED/SUCCESS*`, so one finished job made the whole PR "Passed" while
the required job was still running. PR #204 (2026-09-02) is the fixture: the
rollup read `IN_PROGRESS/,COMPLETED/SUCCESS,COMPLETED/SUCCESS`, the script
printed Passed, and GitHub refused the merge. The first test here is that
string, verbatim.
"""
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import ci_rollup  # noqa: E402

CI_WAIT = ROOT / "scripts" / "ops" / "ci_wait.sh"

# The live string from PR #204, the moment ci_wait.sh said "Passed".
PR_204 = "IN_PROGRESS/,COMPLETED/SUCCESS,COMPLETED/SUCCESS"


@pytest.mark.parametrize("rollup, expected", [
    (PR_204, "pending"),
    ("COMPLETED/SUCCESS,COMPLETED/SUCCESS,COMPLETED/SUCCESS", "pass"),
    ("COMPLETED/SUCCESS", "pass"),
    ("COMPLETED/SKIPPED,COMPLETED/SUCCESS", "pass"),
    ("QUEUED/,QUEUED/,QUEUED/", "pending"),
    ("COMPLETED/SUCCESS,COMPLETED/FAILURE,IN_PROGRESS/", "fail"),
    ("COMPLETED/FAILURE", "fail"),
    ("COMPLETED/TIMED_OUT,COMPLETED/SUCCESS", "fail"),
    ("COMPLETED/CANCELLED,COMPLETED/SUCCESS", "cancelled"),
    ("COMPLETED/CANCELLED,COMPLETED/FAILURE", "fail"),
    # A commit-status context (not an Actions job) reports its state twice.
    ("SUCCESS/SUCCESS,COMPLETED/SUCCESS", "pass"),
    ("PENDING/PENDING,COMPLETED/SUCCESS", "pending"),
])
def test_verdict_reads_every_job(rollup, expected):
    assert ci_rollup.verdict(rollup) == expected


def test_no_checks_reported_is_not_a_pass():
    """The third answer (convention 11): an empty rollup must not read as clean.

    `gh` prints an empty string for a PR whose checks have not registered yet,
    and the old substring match happened to say pending there only because
    the empty string contains nothing. The new rule says so on purpose.
    """
    assert ci_rollup.verdict("") == "pending"
    assert ci_rollup.verdict("   ") == "pending"
    assert ci_rollup.verdict(",,") == "pending"


def test_one_success_among_running_jobs_is_not_a_pass():
    """The defect, stated as the property the substring rule lacked."""
    for rollup in (PR_204, "COMPLETED/SUCCESS,IN_PROGRESS/", "IN_PROGRESS/,COMPLETED/SUCCESS"):
        assert ci_rollup.verdict(rollup) != "pass", rollup


def test_cli_prints_the_verdict():
    out = subprocess.run([sys.executable, str(ROOT / "scripts/lib/ci_rollup.py"), PR_204],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "pending"


def test_ci_wait_asks_the_module_and_no_longer_matches_a_substring():
    """Closure: the shell script must route its judgement through `verdict`.

    A fix that lived only in Python while the script kept its `case` would
    pass every test above and change nothing an operator sees.
    """
    src = CI_WAIT.read_text(encoding="utf-8")
    assert "ci_rollup.py" in src, "ci_wait.sh does not call scripts/lib/ci_rollup.py"
    assert not re.search(r"\*COMPLETED/SUCCESS\*", src), (
        "ci_wait.sh still judges the rollup by substring — one green job "
        "would read as a green PR")
