"""The conformance-freshness half of the evidence gate, both directions."""
import json

import check_evidence

CHANGELOG = "# Changelog\n\n" + "\n".join(
    f"## 0.1.{500 - i} — r{i}\n" for i in range(30))


def _tree(tmp_path, rows):
    (tmp_path / "conformance").mkdir()
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG)
    if rows is not None:
        (tmp_path / "conformance/history.json").write_text(json.dumps(rows))
    return tmp_path


def _row(version, agent="claude-code"):
    return {"skill_version": version, "agent": agent, "date": "2026-08-12",
            "run_dir": "x", "scores_sha256": "abc",
            "tasks": {"T1-deck": "fail", "T2-deaify": "pass",
                      "T3-recall": "pass"}}


def test_unarmed_without_history_file(tmp_path, monkeypatch):
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, None))
    assert check_evidence.conformance_fresh() is None


def test_fresh_with_two_recent_agents(tmp_path, monkeypatch):
    rows = [_row("0.1.500", "claude-code"), _row("0.1.495", "cursor")]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is True


def test_stale_with_one_recent_agent(tmp_path, monkeypatch):
    rows = [_row("0.1.500", "claude-code"), _row("0.1.450", "cursor")]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is False


def test_stale_when_rows_predate_the_window(tmp_path, monkeypatch):
    rows = [_row("0.1.450", "claude-code"), _row("pre-history", "cursor")]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is False


def test_freshness_ignores_pass_fail():
    """The gate binds on recency, never on passing: a failing verdict in a
    fresh row still counts as measurement (GAP-001 stays open on its own
    ledger; blocking releases on it would invite overclaim)."""
    assert _row("x")["tasks"]["T1-deck"] == "fail"  # the fixture IS a failure
