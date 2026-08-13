"""The conformance driver, proven able to drive, to time out, and to refuse.

Until 0.1.454 nothing in this repository invoked an agent: `run` wrote a prompt
file and asked a person to do it. So this file is the first test of a code path
that did not exist, and the discipline is the usual one — every outcome is
demonstrated, not just the good one, because a driver only ever seen succeeding
is FM-01 with a subprocess in it.

No real agent is invoked here. The registry's `drive` argv is replaced with a
python one-liner that behaves like an agent would: writes the deliverable, or
hangs, or exits non-zero, or is not on PATH at all.
"""
import json
import sys

import run_conformance as rc

TASK = {"id": "T-test", "prompt": "write the file", "deliverable": "*.md"}


def _agent(argv):
    return {"id": "fake", "capability": "full", "drive": argv}


def _writes(name="answers.md", body="done"):
    return [sys.executable, "-c",
            f"import pathlib,sys; pathlib.Path({name!r}).write_text({body!r}); "
            f"print('wrote', {name!r})"]


def test_a_driven_task_returns_its_artifact_and_its_transcript(tmp_path):
    out = rc.drive(_agent(_writes()), TASK, tmp_path)
    assert out["verdict"] == "driven"
    assert out["exit_code"] == 0
    assert out["produced"] == ["answers.md"]
    assert (tmp_path / "answers.md").read_text() == "done"
    # The transcript is the evidence that a run happened at all.
    assert "wrote" in (tmp_path / "transcript.txt").read_text()


def test_the_agent_runs_outside_this_repository(tmp_path):
    # THE ONE THAT MATTERS. An agent started inside the tree reads this repo's
    # maintenance CLAUDE.md and behaves like a maintainer of the skill rather
    # than a consumer of it.
    argv = [sys.executable, "-c",
            "import pathlib; pathlib.Path('cwd.md').write_text(str(pathlib.Path.cwd()))"]
    rc.drive(_agent(argv), TASK, tmp_path)
    where = (tmp_path / "cwd.md").read_text()
    assert str(rc.ROOT) not in where, f"the agent ran inside the repository: {where}"


def test_a_hanging_agent_is_abandoned_and_says_so(tmp_path):
    slow = [sys.executable, "-c", "import time; time.sleep(30)"]
    out = rc.drive(_agent(slow), TASK, tmp_path, timeout=1)
    assert out["verdict"] == "timeout"
    assert out["exit_code"] is None


def test_a_failing_agent_is_recorded_with_its_exit_code(tmp_path):
    out = rc.drive(_agent([sys.executable, "-c", "raise SystemExit(3)"]), TASK, tmp_path)
    assert out["verdict"] == "driven" and out["exit_code"] == 3
    assert out["produced"] == [], "a failed run must not claim an artifact"


def test_an_agent_that_cannot_start_is_reported_not_raised(tmp_path):
    out = rc.drive(_agent([str(tmp_path / "no_such_binary")]), TASK, tmp_path)
    assert out["verdict"] == "could not start"


def test_a_platform_with_no_drive_argv_is_refused_by_name(tmp_path):
    out = rc.drive({"id": "an-ide", "capability": "full"}, TASK, tmp_path)
    assert out["verdict"] == "no driver"
    assert "an-ide" in out["detail"] and "by hand" in out["detail"]


def test_a_pinned_model_is_passed_through_and_recorded(tmp_path):
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('m.md').write_text(' '.join(sys.argv[1:]))"]
    out = rc.drive(_agent(argv), TASK, tmp_path, model="a-model")
    assert out["model"] == "a-model"
    assert "--model a-model" in (tmp_path / "m.md").read_text()


def test_an_unpinned_run_records_that_it_was_unpinned(tmp_path):
    # Not blank: a board cell that says nothing about the model reads as a
    # claim about the agent rather than about one of its configurations.
    out = rc.drive(_agent(_writes()), TASK, tmp_path)
    assert "default" in out["model"]


def test_the_two_shipped_drivers_are_argv_lists(tmp_path):
    # The registry's `invoke` field is prose for a human ("say 'in LUMI
    # style…'"), and driving on it would try to execute a sentence.
    agents = {a["id"]: a for a in json.loads(
        rc.REGISTRY.read_text(encoding="utf-8"))["platforms"]}
    for pid in ("claude-code", "cursor"):
        argv = agents[pid].get("drive")
        assert isinstance(argv, list) and argv, f"{pid} declares no drive argv"
        assert all(isinstance(x, str) for x in argv)
        assert "-p" in argv, f"{pid} must be driven non-interactively"
