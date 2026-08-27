"""The trace store's dictionary and index — generated, and load-bearing.

The store holds three times more files than records: 182 of the 273 are build
traces pytest leaked in before 2026-08-26, set aside by
`trace_store.suite_artifact()` — a rule that lived only in code and in CHANGELOG
prose. A reader who counts files gets a denominator this repository has already
been wrong about once, when `ledger.py` reported "4 of 251 build(s)" over a
store holding seventeen.

So the preface and the `suite_artifact` column are not decoration; they are the
reason the artifacts exist.
"""
import json

import build_trace_dictionary as btd
import pytest
import trace_schema


def _rec(tid, **kw):
    base = dict.fromkeys(trace_schema.FIELDS)
    base.update(trace_id=tid, opened_at="2026-08-20T00:00:00+00:00",
                source="build", entry_path="B", genre="internal",
                storyline="proposal", geometry="16x9", pages=10,
                content_pages=8, phase_seconds={}, outline_reviewed=False,
                titles_changed_after_approval=0, gates={}, graded={},
                thresholds={}, principle_yields=[], skill_version="0.1.630")
    base.update(kw)
    return base


# --- the index --------------------------------------------------------------

def test_every_trace_gets_a_line():
    rows = btd.index_rows([_rec("t-000000000001"), _rec("t-000000000002")])
    assert [r["trace_id"] for r in rows] == ["t-000000000001", "t-000000000002"]


def test_the_index_is_ordered_by_time_not_by_id():
    """The ids are uuid4-derived and sort randomly, so the directory listing
    tells a reader nothing about sequence. This is the only place it appears."""
    rows = btd.index_rows([
        _rec("t-zzzzzzzzzzzz", opened_at="2026-08-01T00:00:00+00:00"),
        _rec("t-aaaaaaaaaaaa", opened_at="2026-08-09T00:00:00+00:00")])
    assert [r["trace_id"] for r in rows] == ["t-zzzzzzzzzzzz", "t-aaaaaaaaaaaa"]


def test_the_suite_artifact_filter_travels_as_a_column():
    """The load-bearing one. A service reading the directory cannot know this
    package's filter; carrying it as data is what stops the denominator being
    three times too large."""
    leak = _rec("t-000000000001", source="build", entry_path="B", pages=0,
                recipe_hash=None, closed_at=None,
                opened_at="2026-08-01T00:00:00+00:00")
    real = _rec("t-000000000002", closed_at="2026-08-20T00:00:00+00:00")
    rows = {r["trace_id"]: r for r in btd.index_rows([leak, real])}
    assert rows["t-000000000001"]["suite_artifact"] is True
    assert rows["t-000000000002"]["suite_artifact"] is False


def test_the_index_carries_no_verdict_blocks():
    """They are 44% of the store's bytes and they belong in the trace, which
    every index line points at."""
    rows = btd.index_rows([_rec("t-000000000001",
                                gates={"D12_commercial_footer": "FAIL"})])
    for banned in ("gates", "graded", "thresholds"):
        assert banned not in rows[0]
    assert rows[0]["path"] == "evals/traces/t-000000000001.json"


def test_a_fail_count_stands_in_for_the_blocks_it_omits():
    rows = btd.index_rows([_rec("t-000000000001",
                                closed_at="2026-08-20T00:00:00+00:00",
                                gates={"a": "FAIL", "b": "ok"},
                                graded={"c": "FAIL"})])
    assert rows[0]["fail_count"] == 2


def test_an_open_trace_reports_no_fail_count_rather_than_zero():
    """An unclosed trace has no verdicts at all. Zero would say it passed
    everything, which is FM-24's shape in a column."""
    rows = btd.index_rows([_rec("t-000000000001", closed_at=None)])
    assert rows[0]["fail_count"] is None


def test_annotations_flatten_into_two_columns():
    """One object per line is the point; a nested block in it defeats grep,
    which is why a human opens the index instead of the trace."""
    rows = btd.index_rows([_rec("t-000000000001",
                                annotations={"note": "why", "tags": ["a"]})])
    assert rows[0]["note"] == "why" and rows[0]["tags"] == ["a"]


def test_a_trace_with_no_annotations_still_has_the_columns():
    rows = btd.index_rows([_rec("t-000000000001")])
    assert rows[0]["note"] is None and rows[0]["tags"] == []


def test_every_line_parses_on_its_own():
    text = btd.render_index([_rec("t-000000000001"), _rec("t-000000000002")])
    lines = text.splitlines()
    assert len(lines) == 2
    for line in lines:
        assert json.loads(line)["trace_id"].startswith("t-")


# --- the dictionary ---------------------------------------------------------

def test_the_preface_names_both_counts_and_the_gap_between_them():
    leak = _rec("t-000000000001", pages=0, closed_at=None,
                opened_at="2026-08-01T00:00:00+00:00")
    text = btd.render_dictionary([leak, _rec("t-000000000002")])
    assert "2 JSON files" in text and "1 record" in text
    assert "suite_artifact" in text


def test_every_schema_field_appears_with_a_citation():
    """A field the dictionary omits is a field a service author cannot look
    up — and the citation is the whole reason this is generated: the meaning
    stays in trace_schema.py's comment and is never copied."""
    text = btd.render_dictionary([_rec("t-000000000001")])
    for name in trace_schema.FIELDS:
        assert f"`{name}`" in text, f"{name} is missing from the dictionary"
    assert text.count("trace_schema.py:") >= len(trace_schema.FIELDS)


def test_the_hand_editable_column_matches_the_allow_list():
    text = btd.render_dictionary([_rec("t-000000000001")])
    for name in btd.HAND_EDITABLE:
        assert name in trace_schema.FIELDS, (
            f"{name} is offered as hand-editable and is not in the schema")
    row = next(ln for ln in text.splitlines() if ln.startswith("| `gates` |"))
    assert "| no |" in row, "a verdict block was offered as hand-editable"


def test_the_language_exemption_is_stated_where_a_contributor_reads_it():
    """`check_repo`'s english-only guard excludes `evals/traces/`. Its stated
    reason was "a closed schema with nowhere to put prose", which stopped being
    true when `annotations` gave it somewhere."""
    text = btd.render_dictionary([_rec("t-000000000001")])
    assert "any language" in text and "English-only" in text


def test_an_enum_field_lists_its_values():
    text = btd.render_dictionary([_rec("t-000000000001")])
    row = next(ln for ln in text.splitlines() if ln.startswith("| `effort` |"))
    for level in trace_schema.ENUMS["effort"]:
        assert f"`{level}`" in row


def test_a_field_added_after_records_existed_says_so():
    text = btd.render_dictionary([_rec("t-000000000001")])
    for name in trace_schema.ADDED_LATER:
        row = next(ln for ln in text.splitlines() if ln.startswith(f"| `{name}` |"))
        assert "optional" in row


def test_an_empty_store_does_not_pretend_to_describe_one():
    """What it prints when it cannot look. Every count is zero and every
    example is a dash — and the field table is still complete, because the
    schema is the source for that half."""
    text = btd.render_dictionary([])
    assert "**0 JSON files**" in text and "**0 records**" in text
    for name in trace_schema.FIELDS:
        assert f"`{name}`" in text


# --- the generator's contract ----------------------------------------------

def test_check_refuses_a_hand_edited_artifact(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(btd, "DICT_OUT", tmp_path / "README.md")
    monkeypatch.setattr(btd, "INDEX_OUT", tmp_path / "index.jsonl")
    assert btd.main([]) == 0
    (tmp_path / "index.jsonl").write_text("somebody typed this\n", encoding="utf-8")
    assert btd.main(["--check"]) == 1
    assert "stale or missing" in capsys.readouterr().out


def test_check_refuses_a_missing_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(btd, "DICT_OUT", tmp_path / "gone.md")
    monkeypatch.setattr(btd, "INDEX_OUT", tmp_path / "gone.jsonl")
    assert btd.main(["--check"]) == 1


def test_the_render_reads_no_clock():
    """Every date comes from a trace. A `date.today()` would make `--check` go
    red on the day after it was written."""
    import pathlib as _p
    src = _p.Path(btd.__file__).read_text(encoding="utf-8")
    assert "today" not in src and "datetime.now" not in src


# NOT TESTED HERE: that the SHIPPED dictionary and index match the shipped
# store. The suite writes to a scratch trace store (conftest, deliberately), so
# a test of that here would compare the tracked artifacts against an empty
# store and fail for a reason unrelated to either.
# `build_trace_dictionary.py --check` is a CI step for exactly that claim.


@pytest.mark.parametrize("name", ["annotations"])
def test_the_new_field_is_in_the_partition(name):
    sides = (trace_schema.DOCUMENT_FIELDS, trace_schema.PRODUCER_FIELDS,
             trace_schema.RUN_FIELDS)
    assert sum(name in side for side in sides) == 1


def test_the_column_list_itself_excludes_the_verdict_blocks():
    """The test above asserts the OUTPUT has no verdict blocks, and the final
    projection makes that structurally true — so a planted `row["gates"] = …`
    could not break it. This asserts the thing that actually decides: the
    column list. Adding `gates` to `INDEX_FIELDS` is the real mistake, and it
    would put 44% of the store's bytes into a file meant to be greppable."""
    for banned in ("gates", "graded", "thresholds"):
        assert banned not in btd.INDEX_FIELDS


def test_every_declared_column_is_produced():
    """The mirror. A column named and never filled would be a header over
    nothing."""
    rows = btd.index_rows([_rec("t-000000000001")])
    assert list(rows[0]) == list(btd.INDEX_FIELDS)
