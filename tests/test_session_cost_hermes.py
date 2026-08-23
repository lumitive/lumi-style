"""The Hermes reading is the table's numbers, not twice them.

`hermes()` summed the four token fields and a second reader summed the same
rows into the same dict again, so every token field came back exactly doubled
while `api_calls` and `tool_calls` stayed right. That shape is the worst one an
instrument can have: the counts look sane, so the doubling reads as real usage.
It was found in the field at 0.1.591, when a platform comparison halved the
numbers by hand and said so in a footnote.
"""
import json
import sqlite3

import session_cost


def _db(tmp_path, rows, tool_blobs=()):
    p = tmp_path / "state.db"
    con = sqlite3.connect(p)
    con.execute("create table session_model_usage (session_id text, task text,"
                " api_call_count int, input_tokens int, output_tokens int,"
                " cache_read_tokens int, cache_write_tokens int)")
    con.execute("create table messages (session_id text, tool_calls text)")
    con.executemany("insert into session_model_usage values (?,?,?,?,?,?,?)", rows)
    con.executemany("insert into messages values (?,?)", tool_blobs)
    con.commit()
    con.close()
    return p


def test_tokens_are_not_doubled(tmp_path):
    db = _db(tmp_path, [("s1", "(main)", 7, 100, 200, 3000, 40)])
    out = session_cost.hermes(["s1"], db)
    assert out["input_tokens"] == 100
    assert out["output_tokens"] == 200
    assert out["cache_read_input_tokens"] == 3000
    assert out["cache_creation_input_tokens"] == 40


def test_calls_and_tasks_survive_the_fix(tmp_path):
    """The half that was always right stays right."""
    db = _db(tmp_path,
             [("s1", "(main)", 7, 100, 200, 3000, 40),
              ("s1", "approval", 3, 10, 20, 300, 4)],
             [("s1", json.dumps([{"n": 1}, {"n": 2}]))])
    out = session_cost.hermes(["s1"], db)
    assert out["api_calls"] == 10
    assert out["by_task"] == {"(main)": 7, "approval": 3}
    assert out["tool_calls"] == 2
    assert out["input_tokens"] == 110
    assert out["output_tokens"] == 220


def test_several_sessions_sum_once_each(tmp_path):
    db = _db(tmp_path, [("s1", "(main)", 1, 100, 200, 300, 4),
                        ("s2", "(main)", 1, 100, 200, 300, 4)])
    out = session_cost.hermes(["s1", "s2"], db)
    assert out["output_tokens"] == 400


def test_one_reader_only():
    """The two-readers-one-accumulator shape is what produced the doubling."""
    assert not hasattr(session_cost, "_hermes_tokens")


def test_a_row_with_null_columns_does_not_kill_the_reading(tmp_path):
    """The merge that removed the double-count guarded the TOKENS and left the
    call count unguarded, so one incomplete row raised TypeError and took the
    whole reading down. A counter that crashes on real data is a counter."""
    db = _db(tmp_path, [("s1", None, None, None, 5, None, None)])
    out = session_cost.hermes(["s1"], db)
    assert out["api_calls"] == 0
    assert out["output_tokens"] == 5
    assert out["by_task"] == {"(main)": 0}


def test_a_session_with_no_rows_reads_as_zero_not_as_everything(tmp_path):
    db = _db(tmp_path, [("s1", "(main)", 3, 10, 20, 30, 4)])
    out = session_cost.hermes(["nosuch"], db)
    assert out["api_calls"] == 0 and out["output_tokens"] == 0


def test_an_unknown_session_id_is_refused_not_reported_as_zero(tmp_path):
    """An all-zero table under a "1 session(s)" header says the work cost
    nothing. The Claude branch already hard-exits on a missing transcript."""
    import pytest
    db = _db(tmp_path, [("s1", "(main)", 3, 10, 20, 30, 4)])
    with pytest.raises(SystemExit) as e:
        session_cost.main(["--hermes", "nosuch", "--db", str(db)])
    assert "no rows for session id(s): nosuch" in str(e.value)
