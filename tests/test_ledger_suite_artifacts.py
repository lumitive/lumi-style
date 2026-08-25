"""The ledger's denominators are claims about practice, so they must exclude pytest.

`suite_artifact` is the predicate; these tests hold it to both sides. The
expensive half is the false positive: a real build that was abandoned early
looks superficially like a suite artifact, and silently dropping it would turn
a fix for a bad denominator into a different bad denominator.
"""
import json

import ledger


def _trace(**over):
    t = {"trace_id": "t-real", "source": "build", "entry_path": "B",
         "pages": 12, "recipe_hash": "abc", "closed_at": "2026-08-26T00:00:00"}
    t.update(over)
    return t


def test_the_suite_scaffold_is_recognised():
    assert ledger.suite_artifact(_trace(
        trace_id="t-leak", pages=0, recipe_hash=None, closed_at=None))


def test_a_real_build_is_never_set_aside():
    """One condition short of the fingerprint is a build, in all four directions."""
    leak = {"pages": 0, "recipe_hash": None, "closed_at": None}
    assert not ledger.suite_artifact(_trace(**{**leak, "pages": 1}))
    assert not ledger.suite_artifact(_trace(**{**leak, "recipe_hash": "abc"}))
    assert not ledger.suite_artifact(_trace(**{**leak, "closed_at": "2026-08-26"}))
    assert not ledger.suite_artifact(_trace(**{**leak, "entry_path": "A"}))
    assert not ledger.suite_artifact(_trace(**{**leak, "source": "conformance"}))


def test_load_sets_them_aside_and_the_flag_puts_them_back(tmp_path, monkeypatch):
    store = tmp_path / "traces"
    store.mkdir()
    (store / "a.json").write_text(json.dumps(
        _trace(trace_id="t-real")), encoding="utf-8")
    (store / "b.json").write_text(json.dumps(_trace(
        trace_id="t-leak", pages=0, recipe_hash=None, closed_at=None)),
        encoding="utf-8")
    monkeypatch.setattr(ledger, "TRACES", store)

    assert [t["trace_id"] for t in ledger.load()] == ["t-real"]
    assert sorted(t["trace_id"] for t in ledger.load(True)) == ["t-leak", "t-real"]


def test_nothing_is_deleted(tmp_path, monkeypatch):
    """Set aside means set aside. The store is a record; the report is a reading."""
    store = tmp_path / "traces"
    store.mkdir()
    (store / "b.json").write_text(json.dumps(_trace(
        trace_id="t-leak", pages=0, recipe_hash=None, closed_at=None)),
        encoding="utf-8")
    monkeypatch.setattr(ledger, "TRACES", store)
    ledger.load()
    assert (store / "b.json").exists()
