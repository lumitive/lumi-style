"""debug_log.py proven able to pass AND to fail (FM-01 discipline).

The log is the debug mode's whole product, so each promise gets both sides:
what a subcommand writes, and what `validate` refuses.
"""
import json

import debug_log
import pytest


def _init(tmp_path):
    deliverable = tmp_path / "doc.en.html"
    deliverable.write_text("<html></html>")
    rc = debug_log.main(["init", str(deliverable), "--platform", "claude-code"])
    assert rc == 0
    return tmp_path / "doc.debug.json"


def test_init_writes_the_closed_shape(tmp_path, capsys):
    log = json.loads(_init(tmp_path).read_text())
    assert set(log) == debug_log.TOP_KEYS
    assert log["deliverable"] == "doc.en.html"
    assert log["platform"] == "claude-code"


def test_init_refuses_a_platform_the_registry_does_not_claim(tmp_path):
    deliverable = tmp_path / "doc.en.html"
    deliverable.write_text("x")
    with pytest.raises(SystemExit):
        debug_log.main(["init", str(deliverable), "--platform", "hermas"])


def test_run_records_machine_written_evidence(tmp_path, capsys):
    path = _init(tmp_path)
    rc = debug_log.main(["run", str(path), "--label", "true-step", "--",
                         "python3", "-c", "print('hello')"])
    assert rc == 0
    log = json.loads(path.read_text())
    entry = log["commands"][0]
    assert entry["exit_code"] == 0
    assert len(entry["stdout_sha256"]) == 64
    assert log["steps"][0]["label"] == "true-step"


def test_run_passes_the_exit_code_through(tmp_path, capsys):
    path = _init(tmp_path)
    rc = debug_log.main(["run", str(path), "--",
                         "python3", "-c", "raise SystemExit(3)"])
    assert rc == 3
    assert json.loads(path.read_text())["commands"][0]["exit_code"] == 3


def test_assess_refuses_a_self_scored_five(tmp_path, capsys):
    path = _init(tmp_path)
    with pytest.raises(SystemExit):
        debug_log.main(["assess", str(path), "--dim", "H1", "--score", "5",
                        "--reason", "perfect"])


def test_assess_refuses_an_empty_reason(tmp_path, capsys):
    path = _init(tmp_path)
    with pytest.raises(SystemExit):
        debug_log.main(["assess", str(path), "--dim", "H1", "--score", "4",
                        "--reason", "   "])


def test_validate_clean_log_passes(tmp_path, capsys):
    path = _init(tmp_path)
    debug_log.main(["assess", str(path), "--dim", "H1", "--score", "4",
                    "--reason", "holds"])
    assert debug_log.main(["validate", str(path)]) == 0


def test_validate_fails_an_unknown_key(tmp_path, capsys):
    path = _init(tmp_path)
    log = json.loads(path.read_text())
    log["client"] = "somebody"
    path.write_text(json.dumps(log))
    assert debug_log.main(["validate", str(path)]) == 1


def test_validate_fails_cjk_content(tmp_path, capsys):
    path = _init(tmp_path)
    log = json.loads(path.read_text())
    log["notes"].append("这不是英文")
    path.write_text(json.dumps(log, ensure_ascii=False))
    assert debug_log.main(["validate", str(path)]) == 1


def test_validate_fails_a_hand_written_command_entry(tmp_path, capsys):
    # An entry without a digest is a claim someone typed, not a run.
    path = _init(tmp_path)
    log = json.loads(path.read_text())
    log["commands"].append({"command": "checks all pass", "exit_code": 0})
    path.write_text(json.dumps(log))
    assert debug_log.main(["validate", str(path)]) == 1
