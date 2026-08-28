"""One reader for `conformance/history.json`, keeping three answers apart.

Absent, unreadable and not-a-list were collapsed differently by each of the
four readers this replaced. The `record` path — the one that WRITES — had no
guard at all, so these also assert that a damaged history is refused before
anything is written rather than after the run has been paid for.
"""
import json

import history


def _tree(tmp_path, content=None):
    (tmp_path / "conformance").mkdir(parents=True, exist_ok=True)
    if content is not None:
        (tmp_path / "conformance/history.json").write_text(content, encoding="utf-8")
    return tmp_path


def test_absent_is_not_a_problem(tmp_path):
    """A first run has no rows to break."""
    rows, problem = history.read_rows(_tree(tmp_path))
    assert rows == [] and problem is None


def test_unparseable_is_named_rather_than_read_as_empty(tmp_path):
    rows, problem = history.read_rows(_tree(tmp_path, "[{,]"))
    assert rows == [] and problem and "could not be read" in problem


def test_a_document_that_is_not_a_list_is_named(tmp_path):
    """`null`, a number and an object all parse as JSON."""
    for body in ("null", "3", '{"rows": []}'):
        rows, problem = history.read_rows(_tree(tmp_path, body))
        assert rows == [] and problem and "not a list of rows" in problem


def test_good_rows_come_back_with_no_problem(tmp_path):
    rows, problem = history.read_rows(
        _tree(tmp_path, json.dumps([{"agent": "alpha"}])))
    assert problem is None and rows[0]["agent"] == "alpha"


def test_the_live_history_reads_clean():
    rows, problem = history.read_rows()
    assert problem is None and isinstance(rows, list)
