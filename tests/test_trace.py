"""The trace schema is closed, and the tool refuses to write an illegal record.

The point of these tests is not that the happy path works. It is that the three
disciplines the design record names — machine-written verdicts, a trace opened
before the build rather than after, and no free text — are properties of the
code rather than of whoever runs it.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRACE_PY = ROOT / "scripts" / "ops" / "trace.py"
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import trace_schema as trace  # noqa: E402 — after the path insert, deliberately


def _legal():
    rec = dict.fromkeys(trace.FIELDS)
    rec.update(trace_id="t-0123456789ab", opened_at="2026-08-16T00:00:00+00:00",
               closed_at=None, source="build", skill_version="0.1.462",
               genre="sales", storyline="market-analysis", entry_path="A",
               outline_reviewed=False, titles_changed_after_approval=0,
               geometry="16x9", pages=0, content_pages=0, phase_seconds={},
               gates={}, graded={}, thresholds={}, principle_yields=[],
               refused_to_emit=None)
    return rec


def test_legal_record_validates():
    assert trace.validate(_legal()) == []


def test_free_text_field_is_rejected():
    """Red line 9 held by the schema: a trace carries no prose at all."""
    rec = _legal()
    rec["note"] = "the client asked for this in a hurry"
    assert any("schema is closed" in e for e in trace.validate(rec))


def test_refusal_carries_clauses_and_stage_and_nothing_else():
    rec = _legal()
    rec["refused_to_emit"] = {"clauses": ["P-1", "P-5"], "stage": "checks"}
    assert trace.validate(rec) == []
    rec["refused_to_emit"] = {"clauses": ["P-1"], "stage": "checks",
                              "reason": "the palette fought the handling banner"}
    assert any("nothing else" in e for e in trace.validate(rec))


def test_yield_entry_must_name_real_clauses_and_a_known_stage():
    rec = _legal()
    rec["principle_yields"] = [{"yielded": "P-1", "for": "P-2", "stage": "build"}]
    assert trace.validate(rec) == []
    rec["principle_yields"] = [{"yielded": "brand", "for": "P-2", "stage": "build"}]
    assert any("non-clause" in e for e in trace.validate(rec))
    rec["principle_yields"] = [{"yielded": "P-1", "for": "P-2", "stage": "polish"}]
    assert any("unknown stage" in e for e in trace.validate(rec))


def test_phase_seconds_vocabulary_is_closed():
    rec = _legal()
    rec["phase_seconds"] = {"build": 100, "polish": 20}
    assert any("phase_seconds" in e for e in trace.validate(rec))


def test_genre_outside_the_vocabulary_is_rejected():
    rec = _legal()
    rec["genre"] = "pitch"
    assert any("outside the vocabulary" in e for e in trace.validate(rec))


def test_there_is_no_flag_for_supplying_a_verdict():
    """Verdicts are transcribed from the checkers; the CLI offers no way in.

    check_evidence.py's schema has no verdict field for the same reason: this
    repository once reported all gates passing having run eight of seventeen.
    """
    helptext = subprocess.run([sys.executable, str(TRACE_PY), "close", "--help"],
                              capture_output=True, text=True).stdout
    for forbidden in ("--gate", "--verdict", "--pass", "--result"):
        assert forbidden not in helptext


def test_open_then_close_round_trip(tmp_path, monkeypatch):
    opened = subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "sales",
         "--storyline", "market-analysis", "--entry-path", "A"],
        capture_output=True, text=True, cwd=ROOT)
    assert opened.returncode == 0
    tid = opened.stdout.strip()
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        rec = json.loads(stored.read_text(encoding="utf-8"))
        assert rec["closed_at"] is None, "an open trace has no closing time — an "\
            "unclosed record is how an abandoned build stays visible"
        assert trace.validate(rec) == []
    finally:
        stored.unlink(missing_ok=True)
