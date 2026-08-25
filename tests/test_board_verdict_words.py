"""Driven, attempted and earned are three different things.

The roll-up called all of them "driven", and the 0.1.605 board said so about
two agents at once: Hermes as `partial: 1 of 3 driven, all pass` after being
driven three times — two of the three wrote their deliverable outside the
working directory — and Gemini as `not run` after three runs that each ended
in HTTP 429. Both readings hand the agent's outcome to the harness's silence,
on the artifact this package publishes about other people's models.
"""
import json

import pytest
import run_conformance

_REAL_HISTORY = run_conformance.ROOT / "conformance" / "history.json"
VERSION = "0.1.999"
TASKS = ("T1", "T2", "T3")


@pytest.fixture(autouse=True)
def real_history_untouched():
    before = _REAL_HISTORY.read_bytes()
    yield
    assert _REAL_HISTORY.read_bytes() == before


def _tree(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        f'---\nmetadata:\n  version: "{VERSION}"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "a1", "name": "Agent One", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True)
    for t in TASKS:
        (tasks / f"{t}.json").write_text(json.dumps(
            {"id": t, "prompt": "p", "min_capability": "prompt",
             "score": ["prose"], "deliverable": "*.md"}), encoding="utf-8")
    return tmp_path


def _verdict(tmp_path, monkeypatch, capsys, per_task, attempted=True):
    root = _tree(tmp_path)
    monkeypatch.setattr(run_conformance, "ROOT", root)
    monkeypatch.setattr(run_conformance, "REGISTRY",
                        root / "adapters" / "platforms.json")
    monkeypatch.setattr(run_conformance, "TASKS", root / "conformance" / "tasks")
    monkeypatch.setattr(run_conformance, "RESULTS", root / "conformance" / "results")
    run = tmp_path / "run1"
    run.mkdir()
    (run / "scores.json").write_text(json.dumps({
        f"a1/{t}": {"verdict": v,
                    **({} if v != "not earned"
                       else {"attempted": "yes" if attempted else "no"}),
                    "task_hash": run_conformance.task_fingerprint(json.loads(
                        (root / "conformance" / "tasks" / f"{t}.json")
                        .read_text(encoding="utf-8")))}
        for t, v in per_task.items()}), encoding="utf-8")
    assert run_conformance.main(["report", "--run", str(run)]) == 0
    line = next(ln for ln in capsys.readouterr().out.splitlines()
                if ln.startswith("| Agent One"))
    return line.rsplit("|", 2)[1].strip().strip("*")


def test_all_three_earned_is_a_pass(tmp_path, monkeypatch, capsys):
    assert _verdict(tmp_path, monkeypatch, capsys,
                    dict.fromkeys(TASKS, "pass")) == "pass"


def test_a_partial_counts_what_was_earned_not_what_was_driven(
        tmp_path, monkeypatch, capsys):
    """Hermes's row. Three tasks driven; two wrote their file somewhere else."""
    v = _verdict(tmp_path, monkeypatch, capsys,
                 {"T1": "not earned", "T2": "pass", "T3": "not earned"})
    assert v == "partial: 1 of 3 earned, all pass"
    assert "driven" not in v, (
        "the roll-up called an attempt that earned nothing 'not driven', which "
        "is the harness taking the blame for the agent")


def test_an_agent_that_ran_and_earned_nothing_is_not_an_agent_that_did_not_run(
        tmp_path, monkeypatch, capsys):
    """Gemini's row. Three runs, three rate limits, and the board said 'not run'."""
    v = _verdict(tmp_path, monkeypatch, capsys,
                 dict.fromkeys(TASKS, "not earned"))
    assert v == "run, nothing earned: 3 of 3 attempted"


def test_an_agent_nobody_drove_still_reads_not_run(tmp_path, monkeypatch, capsys):
    """The other side: absence must stay distinguishable from failure."""
    assert _verdict(tmp_path, monkeypatch, capsys,
                    dict.fromkeys(TASKS, "not attempted")) == "not run"


def test_a_host_without_the_cli_did_not_run_the_agent(tmp_path, monkeypatch,
                                                      capsys):
    """`environment` is decided BEFORE the CLI is invoked.

    Reading "attempted" off "the verdict is not `not attempted`" published
    "ran three times, earned nothing" about a host where the binary is not
    installed — the mirror of the defect this release fixes, and on the same
    artifact. `score` records which kind of not-earned each cell was.
    """
    assert _verdict(tmp_path, monkeypatch, capsys,
                    dict.fromkeys(TASKS, "not earned"),
                    attempted=False) == "not run"


def test_a_partial_counts_every_task_not_only_the_scored_ones(
        tmp_path, monkeypatch, capsys):
    """One task of three may not publish a bare `pass`.

    `verdicts` was appended to only for tasks carrying a score entry, so
    `run --drive --task T1-deck` produced a row reading `pass` about an agent
    measured on a third of the suite.
    """
    v = _verdict(tmp_path, monkeypatch, capsys, {"T1": "pass"})
    assert v == "partial: 1 of 3 earned, all pass"
