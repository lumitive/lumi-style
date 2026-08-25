"""The ledger's denominators are claims about practice, so they must exclude pytest.

`suite_artifact` is the predicate; these tests hold it to both sides. The
expensive half is the false positive: a real build that was abandoned early
looks superficially like a suite artifact, and silently dropping it would turn
a fix for a bad denominator into a different bad denominator.
"""
import json
import sys

import ledger


def _trace(**over):
    t = {"trace_id": "t-real", "source": "build", "entry_path": "B",
         "pages": 12, "recipe_hash": "abc", "closed_at": "2026-08-26T00:00:00",
         "opened_at": "2026-08-01T00:00:00+00:00"}
    t.update(over)
    return t


LEAK = {"pages": 0, "recipe_hash": None, "closed_at": None,
        "opened_at": "2026-08-01T00:00:00+00:00"}


def test_the_suite_scaffold_is_recognised():
    assert ledger.suite_artifact(_trace(trace_id="t-leak", **LEAK))


def test_one_condition_short_of_the_fingerprint_is_not_set_aside():
    """Each condition carries its own weight, in all six directions.

    This does NOT mean a real build is safe. The docstring on `suite_artifact`
    used to claim exactly that, and a review took it apart: `trace.py cmd_open`
    writes `pages=0`, `closed_at=None` and `recipe_hash=None` on every trace it
    opens, and path B is what most real builds use — so three of the six are
    the initial state of anything. The date is what actually separates the two
    populations, and it has its own test below.
    """
    for field, value in (("pages", 1), ("recipe_hash", "abc"),
                         ("closed_at", "2026-08-26"), ("entry_path", "A"),
                         ("source", "conformance")):
        assert not ledger.suite_artifact(_trace(**{**LEAK, field: value})), field


def test_the_date_is_what_actually_closes_the_population():
    """The leak has a stop, and after it nothing pytest wrote can be added.

    The condition the docstring calls decisive, and until a review looked for
    it, the only one with no test: every fixture omitted `opened_at`, so the
    `or ""` branch made the comparison trivially true and the clause had never
    been exercised in either direction.
    """
    before = _trace(**{**LEAK, "opened_at": "2026-08-25T23:59:59+00:00"})
    on_the_day = _trace(**{**LEAK, "opened_at": ledger.SUITE_LEAK_STOPPED})
    after = _trace(**{**LEAK, "opened_at": "2026-09-01T00:00:00+00:00"})
    assert ledger.suite_artifact(before)
    assert not ledger.suite_artifact(on_the_day), (
        "a trace opened on the day the leak stopped was set aside; the "
        "population must be closed at the cutoff, not through it")
    assert not ledger.suite_artifact(after)


def test_a_trace_with_no_opened_at_is_set_aside():
    """Documented rather than accidental.

    A record with no `opened_at` falls through `or ""`, which sorts before any
    date. Every one of the 182 legacy records carries the field, so this is the
    behaviour on a shape that does not occur — recorded so that a later reader
    finds a decision instead of a coincidence.
    """
    assert ledger.suite_artifact(_trace(**{**LEAK, "opened_at": None}))


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


# ---------------------------------------------------------------- the report
#
# `load()` and the predicate were covered; what a READER sees was not, and a
# review's mutation test proved the difference: making `--with-suite-artifacts`
# a no-op in the report, deleting the disclosure line, and forcing the leaked
# denominators back all three left the suite green. The filter is only honest
# if the disclosure ships with it, so the disclosure is what these hold.

def _store(tmp_path, monkeypatch, n_leak=3, n_real=2):
    store = tmp_path / "traces"
    store.mkdir()
    for i in range(n_leak):
        (store / f"leak{i}.json").write_text(json.dumps(_trace(
            trace_id=f"t-leak{i}", pages=0, recipe_hash=None, closed_at=None,
            opened_at="2026-08-01T00:00:00+00:00")), encoding="utf-8")
    for i in range(n_real):
        (store / f"real{i}.json").write_text(json.dumps(
            _trace(trace_id=f"t-real{i}")), encoding="utf-8")
    monkeypatch.setattr(ledger, "TRACES", store)
    return store


def _run(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["ledger.py", *argv])
    ledger.main()
    return capsys.readouterr().out


def test_the_report_says_what_it_set_aside(tmp_path, monkeypatch, capsys):
    _store(tmp_path, monkeypatch)
    out = _run(monkeypatch, capsys)
    assert "2 trace(s)" in out
    assert "3 suite artifact(s) set aside" in out


def test_the_flag_puts_them_back_in_the_report(tmp_path, monkeypatch, capsys):
    """Not only in `load` — the flag exists so a person can audit the decision."""
    _store(tmp_path, monkeypatch)
    out = _run(monkeypatch, capsys, "--with-suite-artifacts")
    assert "5 trace(s)" in out
    assert "set aside" not in out


def test_json_discloses_the_filter(tmp_path, monkeypatch, capsys):
    """The output most likely to be pasted into something else."""
    _store(tmp_path, monkeypatch)
    doc = json.loads(_run(monkeypatch, capsys, "--json"))
    assert doc["traces"] == 2
    assert doc["suite_artifacts_set_aside"] == 3


def test_the_board_discloses_the_filter(tmp_path, monkeypatch, capsys):
    _store(tmp_path, monkeypatch)
    assert "3 suite artifact(s) set aside" in _run(monkeypatch, capsys, "--board")


def test_an_all_artifact_store_does_not_read_as_empty(tmp_path, monkeypatch, capsys):
    """"no traces yet" over a directory of hundreds is a false statement."""
    _store(tmp_path, monkeypatch, n_leak=4, n_real=0)
    out = _run(monkeypatch, capsys)
    assert "no traces yet" in out
    assert "4 suite artifact(s) set aside" in out


def test_the_abandoned_count_names_both_populations(tmp_path, monkeypatch, capsys):
    """The filter and this count select the same field, so subtracting hides it.

    Every set-aside record is unclosed, so filtering removes them from
    `abandoned` and from nothing else — reporting only the remainder turns a
    denominator fix into the loss of the signal the ledger exists to raise.
    """
    _store(tmp_path, monkeypatch, n_leak=3, n_real=2)
    out = _run(monkeypatch, capsys)
    assert "0 abandoned build(s)" in out
    assert "3 more unclosed records set aside" in out


def test_the_reviewed_outline_denominator_counts_builds(tmp_path, monkeypatch,
                                                        capsys):
    """It says `build(s)` and divided by every trace, conformance rows included."""
    store = _store(tmp_path, monkeypatch, n_leak=0, n_real=2)
    (store / "conf.json").write_text(json.dumps(_trace(
        trace_id="t-conf", source="conformance")), encoding="utf-8")
    out = _run(monkeypatch, capsys)
    assert "of 2 build(s) record a reviewed outline" in out


def test_a_store_file_that_is_not_an_object_does_not_crash(tmp_path, monkeypatch):
    store = tmp_path / "traces"
    store.mkdir()
    (store / "bad.json").write_text('["not an object"]', encoding="utf-8")
    monkeypatch.setattr(ledger, "TRACES", store)
    assert ledger.load() == [["not an object"]]
