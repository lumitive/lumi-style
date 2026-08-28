"""The producer half of the conformance-history contract (GAP-003).

`report --record` is what writes conformance/history.json rows; until now only
the consumer (check_evidence.conformance_fresh) was tested, against hand-written
rows — FM-07's one-sided-contract shape. These tests drive the real producer,
run_conformance.main(), in-process against a synthetic ROOT: a stub SKILL.md
(same `version: "…"` stamp format the real one carries, so the version parsing
is exercised), a stub platform registry, one stub task, and a run directory
holding a scores.json. The monkeypatched ROOT isolates the real
conformance/history.json; the autouse fixture asserts it byte-identical anyway.
"""
import datetime
import hashlib
import json

import pytest
import run_conformance

# Captured at import time, before any test monkeypatches the module.
_REAL_HISTORY = run_conformance.ROOT / "conformance" / "history.json"

VERSION = "0.1.999"
SCORES = {"agentA/T1": {"verdict": "pass", "task_hash": "aaaaaaaaaaaa"},
          "agentB/T1": {"verdict": "fail", "task_hash": "bbbbbbbbbbbb",
                        "failed": ["prose exited 1"]}}


@pytest.fixture(autouse=True)
def real_history_untouched():
    """The tracked history is evidence; a test run may not move a byte of it."""
    before = _REAL_HISTORY.read_bytes()
    yield
    assert _REAL_HISTORY.read_bytes() == before


def _tree(tmp_path):
    """A synthetic ROOT with everything main() dereferences on the report path."""
    (tmp_path / "SKILL.md").write_text(
        f'---\nmetadata:\n  version: "{VERSION}"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir()
    # No `probe` key: detect() then records "no probe declared" without ever
    # spawning a subprocess, which keeps these tests hermetic.
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [
            {"id": "agentA", "name": "Agent A", "capability": "prompt"},
            {"id": "agentB", "name": "Agent B", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "T1.json").write_text(json.dumps(
        {"id": "T1", "prompt": "p", "min_capability": "prompt",
         "score": ["prose"], "deliverable": "*.md"}), encoding="utf-8")
    return tmp_path


def _patch(monkeypatch, root):
    # `REGISTRY` was a dead constant here — 0.1.640 deleted it, and the roster
    # now comes from `platform_registry.platforms(ROOT)`, so patching ROOT is
    # what points the driver at this tree.
    monkeypatch.setattr(run_conformance, "ROOT", root)
    monkeypatch.setattr(run_conformance, "TASKS", root / "conformance" / "tasks")
    monkeypatch.setattr(run_conformance, "RESULTS",
                        root / "conformance" / "results")


def _run_dir(tmp_path, name, scores):
    d = tmp_path / name
    d.mkdir()
    body = scores if isinstance(scores, str) else json.dumps(scores, indent=2)
    (d / "scores.json").write_text(body, encoding="utf-8")
    return d


def _record(run_dirs):
    argv = ["report", "--record"]
    for d in run_dirs:
        argv += ["--run", str(d)]
    return run_conformance.main(argv)


def _history(root):
    return json.loads((root / "conformance" / "history.json").read_text(
        encoding="utf-8"))


def test_record_writes_one_row_per_agent(tmp_path, monkeypatch):
    root = _tree(tmp_path)
    _patch(monkeypatch, root)
    run1 = _run_dir(tmp_path, "run1", SCORES)
    assert _record([run1]) == 0
    rows = _history(root)
    assert [r["agent"] for r in rows] == ["agentA", "agentB"]
    digest = hashlib.sha256((run1 / "scores.json").read_bytes()).hexdigest()
    today = datetime.date.today().isoformat()
    for row, verdict in zip(rows, ("pass", "fail")):
        assert row["skill_version"] == VERSION  # SKILL.md stamp parsed, not guessed
        assert row["run_dir"] == str(run1)
        assert row["date"] == today
        assert row["tasks"] == {"T1": verdict}  # agent/task key split, one map per agent
        assert row["scores_sha256"] == digest  # pinned to the artifact's bytes


def test_record_twice_appends_nothing(tmp_path, monkeypatch, capsys):
    root = _tree(tmp_path)
    _patch(monkeypatch, root)
    run1 = _run_dir(tmp_path, "run1", SCORES)
    assert _record([run1]) == 0
    first = _history(root)
    assert _record([run1]) == 0
    assert _history(root) == first
    assert "recorded 0 new history row(s)" in capsys.readouterr().out


def test_new_digest_appends_and_never_overwrites(tmp_path, monkeypatch):
    root = _tree(tmp_path)
    _patch(monkeypatch, root)
    run1 = _run_dir(tmp_path, "run1", SCORES)
    assert _record([run1]) == 0
    before = _history(root)
    # Same agent, new run directory, different verdict — a different digest.
    rerun = {"agentA/T1": {"verdict": "fail", "task_hash": "aaaaaaaaaaaa"}}
    run2 = _run_dir(tmp_path, "run2", rerun)
    assert _record([run2]) == 0
    rows = _history(root)
    assert rows[:len(before)] == before  # history accumulates, never overwrites
    assert len(rows) == len(before) + 1
    new = rows[-1]
    assert new["agent"] == "agentA"
    assert new["run_dir"] == str(run2)
    assert new["tasks"] == {"T1": "fail"}
    assert new["scores_sha256"] == hashlib.sha256(
        (run2 / "scores.json").read_bytes()).hexdigest()
    digests = {r["scores_sha256"] for r in rows if r["agent"] == "agentA"}
    assert len(digests) == 2


def test_corrupt_scores_fails_loudly_and_writes_nothing(tmp_path, monkeypatch,
                                                        capsys):
    root = _tree(tmp_path)
    _patch(monkeypatch, root)
    run1 = _run_dir(tmp_path, "run1", "{not json")
    assert _record([run1]) == 1
    assert "does not parse" in capsys.readouterr().out
    assert not (root / "conformance" / "history.json").exists()
