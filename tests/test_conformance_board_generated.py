"""The conformance board's prose about a run is generated from that run's
scores, and the header carries the run's date and version.

Until 0.1.528 the table under `<!-- generated -->` was regenerated and the
paragraph under it was not, so the board said "Both agents fail T1-deck"
beneath a table in which Cursor passed all three, for six days. A sentence
derived from scores.json cannot disagree with a table derived from it.
"""
import json

import run_conformance as rc


def _scores(tmp_path, doc):
    run = tmp_path / "0.1.999-2026-08-20"
    run.mkdir()
    (run / "scores.json").write_text(json.dumps(doc), encoding="utf-8")
    return run


def test_findings_name_every_non_pass_and_nothing_else(tmp_path):
    run = _scores(tmp_path, {
        "cursor/T1-deck": {"verdict": "pass", "failed": []},
        "claude-code/T1-deck": {"verdict": "not earned",
                                "detail": "the driver reports 'timeout'"},
        "claude-code/T2-deaify": {"verdict": "fail",
                                  "failed": ["M2_number_sourcing", "D12_commercial_footer"]},
    })
    lines = rc._findings([str(run)])
    assert len(lines) == 2
    assert any("claude-code/T1-deck" in x and "not earned" in x and "timeout" in x
               for x in lines)
    assert any("T2-deaify" in x and "M2_number_sourcing, D12_commercial_footer" in x
               for x in lines)
    assert not any("cursor" in x for x in lines)


def test_run_date_is_read_from_the_scores_file(tmp_path):
    run = _scores(tmp_path, {})
    assert rc._scores_date([str(run)]) is not None
    assert rc._scores_date([str(tmp_path / "absent")]) is None


def test_board_version_falls_back_to_the_scores_instrument_version(tmp_path):
    run = tmp_path / "latest"
    run.mkdir()
    (run / "scores.json").write_text(json.dumps({
        "a/T1": {"verdict": "pass", "instrument_version": "0.1.522"},
        "b/T1": {"verdict": "pass", "instrument_version": "0.1.520"}}), encoding="utf-8")
    assert rc._board_run_version({"run_id": f"`{run}`"}) == "0.1.522"
    assert rc._board_run_version({"run_id": "`x/0.1.501-2026-08-01`"}) == "0.1.501"


def test_render_carries_the_date_and_the_generated_findings(tmp_path):
    run = _scores(tmp_path, {"a/T1": {"verdict": "fail", "failed": ["M4"]}})
    record = {"version": "0.1.999", "run_id": f"`{run}`", "host": "test",
              "agents": 1, "detected": 1, "repeat": 1, "structural": 0,
              "task_ids": ["T1"], "rows": [],
              "run_date": rc._scores_date([str(run)]),
              "findings": rc._findings([str(run)])}
    text = rc.render(record)
    assert "· run 20" in text.splitlines()[2]
    assert "`a/T1` · **fail** · M4" in text
    assert "Everything below the generated marker is history" in text


def test_a_detect_only_board_does_not_claim_everything_passed():
    record = {"version": "0.1.999", "run_id": "detect-only", "host": "test",
              "agents": 0, "detected": 0, "repeat": 0, "structural": 0,
              "task_ids": [], "rows": [], "run_date": None, "findings": []}
    assert "nothing was scored" in rc.render(record)


def test_the_table_names_the_model_behind_each_row(tmp_path):
    # A run may drive one agent on a small model and another on its default —
    # a free-tier quota is enough to force it — and three rows on one table
    # with nothing to tell the configurations apart read as three comparable
    # agents. The column is what stops that reading.
    record = {"version": "0.1.999", "run_id": "detect-only", "host": "test",
              "agents": 2, "detected": 2, "repeat": 1, "structural": 0,
              "task_ids": ["T1"], "run_date": None, "findings": [],
              "rows": [{"name": "Agent One", "capability": "full", "cli": "1.0",
                        "model": "a-lite-model", "tasks": {"T1": "pass"},
                        "verdict": "pass", "runs": 1},
                       {"name": "Agent Two", "capability": "full", "cli": "2.0",
                        "model": None, "tasks": {"T1": "pass"},
                        "verdict": "pass", "runs": 1}]}
    text = rc.render(record)
    header = next(x for x in text.splitlines() if x.startswith("| agent |"))
    assert "| model |" in header
    # The separator row must gain a column with the header, or every cell
    # after it shifts one left in any renderer that counts them.
    sep = next(x for x in text.splitlines() if x.startswith("|---"))
    assert sep.count("---") == header.count("|") - 1
    assert "a-lite-model" in text
    # A row whose model was never recorded says so rather than borrowing the
    # row above it.
    two = next(x for x in text.splitlines() if x.startswith("| Agent Two"))
    assert "| — |" in two
