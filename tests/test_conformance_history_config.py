"""A history row says what the run was configured as, and which trace holds it.

Thirty-six rows precede this field and none of them can be read as a
comparison: `cursor` on Auto and `cursor` pinned to `grok-4.6-high` are two
different runs wearing one agent id, and the row recorded the id. `config`
carries the model, the reasoning tier and the model that was ASKED for;
`traces` carries the join key to what the run COST, which until 0.1.617 was
recovered by matching `(agent, date)` — wrong the first time two agents run on
one day, which is every driven round this package has.

These drive `report --record` rather than re-implementing the row: a test that
rebuilds the loop in its own body passes when the loop is deleted, which is how
one of stage 2's planted reds failed to plant.
"""
import json
import shutil

import pytest
import run_conformance as rc

# THE REAL ROOT, captured at import. The helpers below monkeypatch `rc.ROOT`,
# so a second helper reading `rc.ROOT` in the same test copies from the first
# helper's synthetic tree and fails on a directory that was never there.
_REAL_ROOT = rc.ROOT


def _tree(tmp_path, scores):
    root = tmp_path / "repo"
    (root / "conformance").mkdir(parents=True)
    (root / "conformance" / "history.json").write_text("[]", encoding="utf-8")
    (root / "conformance" / "CONFORMANCE.md").write_text("# x\n", encoding="utf-8")
    (root / "SKILL.md").write_text('version: "0.1.999"\n', encoding="utf-8")
    shutil.copytree(_REAL_ROOT / "adapters", root / "adapters")
    run = tmp_path / "run"
    run.mkdir()
    (run / "scores.json").write_text(json.dumps(scores), encoding="utf-8")
    return root, run


def _record(tmp_path, monkeypatch, scores):
    root, run = _tree(tmp_path, scores)
    monkeypatch.setattr(rc, "ROOT", root)
    assert rc.main(["report", "--run", str(run), "--record"]) == 0
    rows = json.loads((root / "conformance" / "history.json").read_text())
    assert len(rows) == 1
    return rows[0]


_FULL = {"cursor/T1-deck": {"verdict": "pass", "model": "cursor-grok-4.6-high",
                            "effort": "high", "model_asked": "grok-4.6-high",
                            "trace_id": "t-0123456789ab"}}


def test_the_row_carries_the_configuration_the_cell_was_run_as(
        tmp_path, monkeypatch):
    row = _record(tmp_path, monkeypatch, _FULL)
    assert row["config"]["T1-deck"] == {"model": "cursor-grok-4.6-high",
                                        "effort": "high",
                                        "model_asked": "grok-4.6-high"}


def test_the_row_carries_the_trace_that_holds_what_the_run_cost(
        tmp_path, monkeypatch):
    row = _record(tmp_path, monkeypatch, _FULL)
    assert row["traces"] == {"T1-deck": "t-0123456789ab"}


def test_a_cell_scored_before_the_field_existed_adds_no_key(
        tmp_path, monkeypatch):
    """The thirty-six existing rows are this case, and inventing an
    '(unknown)' for them would make 'nobody recorded it' and 'this predates the
    field' the same string — FM-24's shape, one file over."""
    row = _record(tmp_path, monkeypatch, {"cursor/T1-deck": {"verdict": "pass"}})
    assert "config" not in row and "traces" not in row


def test_a_partly_recorded_cell_carries_the_half_that_exists(
        tmp_path, monkeypatch):
    row = _record(tmp_path, monkeypatch,
                  {"cursor/T1-deck": {"verdict": "pass", "model": "Auto"}})
    assert row["config"]["T1-deck"] == {"model": "Auto"}
    assert "traces" not in row


# `validate` is the gate that runs in CI, and what it guards against is a HAND
# EDIT: `history.json` is a tracked file an operator can open.

def _validate(tmp_path, monkeypatch, rows):
    root = tmp_path / "repo"
    (root / "conformance").mkdir(parents=True)
    (root / "conformance" / "history.json").write_text(
        json.dumps(rows), encoding="utf-8")
    shutil.copytree(_REAL_ROOT / "adapters", root / "adapters")
    shutil.copytree(_REAL_ROOT / "conformance" / "tasks",
                    root / "conformance" / "tasks")
    monkeypatch.setattr(rc, "ROOT", root)
    return rc.main(["validate"])


def _row(**kw):
    base = {"skill_version": "0.1.617", "agent": "cursor", "date": "2026-08-27",
            "run_dir": "~/x", "tasks": {"T1-deck": "pass"},
            "scores_sha256": "0" * 64}
    base.update(kw)
    return [base]


def test_validate_accepts_a_row_carrying_a_configuration(tmp_path, monkeypatch):
    assert _validate(tmp_path, monkeypatch, _row(
        config={"T1-deck": {"model": "m", "effort": "high"}},
        traces={"T1-deck": "t-0123456789ab"})) == 0


def test_validate_accepts_a_row_predating_the_field(tmp_path, monkeypatch):
    assert _validate(tmp_path, monkeypatch, _row()) == 0


def test_validate_rejects_a_configuration_for_a_task_the_row_never_scored(
        tmp_path, monkeypatch, capsys):
    assert _validate(tmp_path, monkeypatch, _row(
        config={"T9-invented": {"model": "m"}})) == 1
    assert "T9-invented" in capsys.readouterr().out


def test_validate_rejects_an_effort_outside_the_schema_s_own_tuple(
        tmp_path, monkeypatch, capsys):
    """The tuple is imported from `trace_schema`, never retyped. It WAS
    retyped once: 0.1.554 widened one copy and left the other at three, so a
    run pinned to `xhigh` could be driven and could not be recorded."""
    assert _validate(tmp_path, monkeypatch, _row(
        config={"T1-deck": {"effort": "ludicrous"}})) == 1
    out = capsys.readouterr().out
    assert "ludicrous" in out and "effort" in out


@pytest.mark.parametrize("key", ["config", "traces"])
def test_validate_rejects_a_per_task_map_that_is_not_a_map(
        tmp_path, monkeypatch, key):
    assert _validate(tmp_path, monkeypatch, _row(**{key: ["T1-deck"]})) == 1


# THE ROUND TRIP, because the two halves shipped one release apart and
# contradicted each other. 0.1.617 wrote `(not pinned)` into a score cell as a
# deliberate answer; 0.1.618 taught `validate` to hold `config.effort` to the
# schema's five tiers. Nothing ran both, so the next unpinned round would have
# turned CI red on a row the harness itself wrote. These drive score → record →
# validate in one test for that reason.

def test_an_unpinned_round_records_a_row_that_validate_accepts(
        tmp_path, monkeypatch):
    row = _record(tmp_path, monkeypatch, {
        "cursor/T1-deck": {"verdict": "pass", "model": "Auto",
                           "model_ran": "Auto", "effort_pinned": False,
                           "model_pinned": False, "trace_id": "t-0123456789ab"}})
    assert row["config"]["T1-deck"]["effort_pinned"] is False
    assert "effort" not in row["config"]["T1-deck"]
    fresh = tmp_path / "again"
    fresh.mkdir()
    assert _validate(fresh, monkeypatch, [row]) == 0, (
        "the row the harness just wrote must survive its own CI gate")


def test_a_sentinel_reaching_the_effort_field_is_still_refused(
        tmp_path, monkeypatch, capsys):
    """The guard stays. What changed is that the harness stopped producing the
    thing it refuses — a hand edit still cannot."""
    assert _validate(tmp_path, monkeypatch,
                     _row(config={"T1-deck": {"effort": "(not pinned)"}})) == 1
    assert "(not pinned)" in capsys.readouterr().out
