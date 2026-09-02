"""jsonio: the one writer keeps a file's own indent, and says which it used.

Each case is a shape a real file in this tree has — one-space (fourteen of the
hand-written JSON files), two-space (five), compact (three) — because the
defect this exists for was a writer that picked its own.
"""
import json
import os

import jsonio


def test_detect_indent_reads_the_first_indented_line():
    assert jsonio.detect_indent('{\n "a": 1\n}\n') == 1
    assert jsonio.detect_indent('{\n  "a": 1\n}\n') == 2
    assert jsonio.detect_indent('{\n    "a": [\n        1\n    ]\n}') == 4


def test_detect_indent_calls_a_single_line_document_compact():
    assert jsonio.detect_indent('{"a": 1}') is None
    assert jsonio.detect_indent('{"a":1}\n') is None


def test_dump_keeps_a_one_space_file_at_one_space(tmp_path):
    f = tmp_path / "one.json"
    f.write_text(json.dumps({"a": [1, 2]}, indent=1) + "\n")
    used = jsonio.dump_json(f, {"a": [1, 2, 3]})
    assert used == 1
    assert f.read_text() == json.dumps({"a": [1, 2, 3]}, indent=1) + "\n"


def test_dump_keeps_a_two_space_file_at_two_spaces(tmp_path):
    f = tmp_path / "two.json"
    f.write_text(json.dumps({"a": [1, 2]}, indent=2) + "\n")
    used = jsonio.dump_json(f, {"a": [1, 2, 3]})
    assert used == 2
    assert f.read_text().startswith('{\n  "a"')


def test_dump_keeps_a_compact_file_compact(tmp_path):
    f = tmp_path / "flat.json"
    f.write_text('{"a":[1,2]}\n')
    used = jsonio.dump_json(f, {"a": [1, 2, 3]})
    assert used == 0
    assert f.read_text() == '{"a":[1,2,3]}\n'


def test_a_new_file_gets_one_space(tmp_path):
    f = tmp_path / "new" / "fresh.json"        # the parent does not exist yet either
    used = jsonio.dump_json(f, {"a": 1})
    assert used == 1
    assert f.read_text() == '{\n "a": 1\n}\n'


def test_an_explicit_indent_wins_over_the_file(tmp_path):
    f = tmp_path / "one.json"
    f.write_text(json.dumps({"a": 1}, indent=1) + "\n")
    assert jsonio.dump_json(f, {"a": 1}, indent=2) == 2
    assert f.read_text().startswith('{\n  "a"')
    assert jsonio.dump_json(f, {"a": 1}, indent=0) == 0
    assert f.read_text() == '{"a":1}\n'


def test_non_ascii_is_written_as_itself_by_default(tmp_path):
    f = tmp_path / "zh.json"
    jsonio.dump_json(f, {"k": "赋能"})
    assert "赋能" in f.read_text(encoding="utf-8")
    jsonio.dump_json(f, {"k": "赋能"}, ensure_ascii=True)
    assert "\\u8d4b" in f.read_text(encoding="utf-8")


def test_sort_keys_is_honoured(tmp_path):
    f = tmp_path / "s.json"
    jsonio.dump_json(f, {"b": 1, "a": 2}, sort_keys=True)
    assert f.read_text().index('"a"') < f.read_text().index('"b"')


def test_atomic_replaces_the_file_and_leaves_no_temp_behind(tmp_path):
    f = tmp_path / "rec.json"
    f.write_text(json.dumps({"n": 1}, indent=1) + "\n")
    before = os.stat(f).st_ino
    used = jsonio.dump_json(f, {"n": 2}, atomic=True)
    assert used == 1                             # indent read from the target, not the temp
    assert json.loads(f.read_text()) == {"n": 2}
    assert os.stat(f).st_ino != before           # a new inode: replaced, not rewritten in place
    assert [p.name for p in tmp_path.iterdir()] == ["rec.json"]


def test_load_reads_utf8(tmp_path):
    f = tmp_path / "zh.json"
    f.write_text('{"k": "赋能"}', encoding="utf-8")
    assert jsonio.load_json(f) == {"k": "赋能"}
