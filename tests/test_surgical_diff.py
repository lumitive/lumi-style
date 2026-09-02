"""surgical_diff proven able to pass, to fail, and to say it could not look.

Real git repositories under tmp_path, because the measurement IS two git
commands and a fake would test the fake. Each test builds the smallest
history that shows one answer.
"""
import json
import pathlib
import subprocess

import check_repo
import pytest
import surgical_diff


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                          check=True).stdout


def _repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    # Versions past the gate's SINCE, so the HEAD-only guard is in force here;
    # one test below writes an older one to show it is not.
    (tmp_path / "CHANGELOG.md").write_text("## 9.9.9 — two\n\n## 9.9.8 — one\n")
    return tmp_path


def _commit(root, msg="c"):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)


def _doc(n=80):
    return {"rows": [{"id": i, "name": f"row {i}"} for i in range(n)]}


def _write(path, obj, indent):
    path.write_text(json.dumps(obj, indent=indent) + "\n")


# --- the measurement ---------------------------------------------------------

def test_a_reindent_is_a_reformat_and_the_finding_carries_both_numbers(tmp_path):
    root = _repo(tmp_path)
    f = root / "data.json"
    _write(f, _doc(), 1)
    _commit(root)
    _write(f, _doc(), 2)                      # the 0.1.681 shape: one indent to another
    found, problem = surgical_diff.reformats(root, "HEAD")
    assert problem is None
    assert [x.path for x in found] == ["data.json"]
    assert found[0].total >= 60                # the floor, as a literal: a test that
    assert found[0].real == 0                  # reads MIN_LINES holds however wrong it is
    assert "reformat, not an edit" in found[0].sentence()


def test_a_reindent_that_also_edits_is_still_a_reformat(tmp_path):
    root = _repo(tmp_path)
    f = root / "data.json"
    _write(f, _doc(), 1)
    _commit(root)
    doc = _doc()
    doc["rows"].append({"id": 999, "name": "new"})   # the 0.1.673 gates.json shape
    _write(f, doc, 2)
    found, _ = surgical_diff.reformats(root, "HEAD")
    assert [x.path for x in found] == ["data.json"]
    assert 0 < found[0].real < found[0].total / 5


def test_an_ordinary_edit_is_not_a_reformat(tmp_path):
    root = _repo(tmp_path)
    f = root / "data.json"
    _write(f, _doc(), 1)
    _commit(root)
    doc = _doc()
    for r in doc["rows"][:30]:
        r["name"] = r["name"].upper()          # thirty real changes, same indent
    _write(f, doc, 1)
    found, problem = surgical_diff.reformats(root, "HEAD")
    assert problem is None and found == []


def test_a_small_file_is_below_the_floor(tmp_path):
    root = _repo(tmp_path)
    f = root / "small.json"
    _write(f, _doc(5), 1)
    _commit(root)
    _write(f, _doc(5), 2)
    found, _ = surgical_diff.reformats(root, "HEAD")
    assert found == []


def test_a_committed_range_is_judged_the_same_way(tmp_path):
    root = _repo(tmp_path)
    f = root / "data.json"
    _write(f, _doc(), 1)
    _commit(root, "one")
    _write(f, _doc(), 2)
    _commit(root, "two")
    found, _ = surgical_diff.reformats(root, "HEAD~1", "HEAD")
    assert [x.path for x in found] == ["data.json"]


# --- the third answer --------------------------------------------------------

def test_a_revision_that_does_not_exist_is_could_not_look_not_clean(tmp_path):
    root = _repo(tmp_path)
    (root / "a.txt").write_text("x\n")
    _commit(root)
    found, problem = surgical_diff.reformats(root, "no-such-rev")
    assert found == [] and problem and "failed" in problem


def test_the_cli_exits_two_outside_a_git_tree(tmp_path, capsys):
    rc = surgical_diff.main(["--root", str(tmp_path)])
    assert rc == 2
    assert "could not look" in capsys.readouterr().out


# --- waivers -----------------------------------------------------------------

def _waive(root, file, release, why="meant"):
    (root / "evals").mkdir(exist_ok=True)
    (root / "evals" / "reformat-waivers.json").write_text(json.dumps(
        {"waivers": {file: {"release": release, "why": why}}}) + "\n")


def test_a_live_waiver_clears_the_file_and_only_that_file(tmp_path):
    root = _repo(tmp_path)
    for name in ("a.json", "b.json"):
        _write(root / name, _doc(), 1)
    _commit(root)
    for name in ("a.json", "b.json"):
        _write(root / name, _doc(), 2)
    _waive(root, "a.json", "9.9.9")           # 9.9.9 is the newest CHANGELOG heading
    found, dead, problem = surgical_diff.judge(root, "HEAD")
    assert problem is None and dead == []
    assert [x.path for x in found] == ["b.json"]


def test_a_dead_waiver_is_itself_a_finding(tmp_path):
    root = _repo(tmp_path)
    (root / "a.txt").write_text("x\n")
    _commit(root)
    _waive(root, "a.json", "9.9.8")           # one release behind the newest
    found, dead, problem = surgical_diff.judge(root, "HEAD")
    assert problem is None and found == []
    assert len(dead) == 1 and "dead waiver" in dead[0]


def test_an_unreadable_waiver_table_is_could_not_look(tmp_path):
    root = _repo(tmp_path)
    (root / "a.txt").write_text("x\n")
    _commit(root)
    (root / "evals").mkdir()
    (root / "evals" / "reformat-waivers.json").write_text("{not json")
    _, _, problem = surgical_diff.judge(root, "HEAD")
    assert problem and "could not be read" in problem


# --- the check_repo guard on HEAD~1..HEAD ------------------------------------

def test_guard_passes_a_surgical_commit_and_fails_a_reformatting_one(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    f = root / "data.json"
    _write(f, _doc(), 1)
    _commit(root, "one")
    doc = _doc()
    doc["rows"][0]["name"] = "edited"
    _write(f, doc, 1)
    _commit(root, "two")
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert check_repo.check_surgical_diff() == []
    _write(f, doc, 2)
    _commit(root, "three")
    errors = check_repo.check_surgical_diff()
    assert len(errors) == 1 and "data.json" in errors[0]


def test_guard_leaves_a_commit_older_than_the_gate_alone(tmp_path, monkeypatch):
    """History is not retroactively reddened: 0.1.681 carries the reformat
    that prompted this gate, and HEAD~1..HEAD on that commit must not fail
    the tree that introduces the gate. The committed CHANGELOG says which
    release a commit belongs to."""
    root = _repo(tmp_path)
    (root / "CHANGELOG.md").write_text("## 0.1.681 — before the gate\n")
    f = root / "data.json"
    _write(f, _doc(), 1)
    _commit(root, "one")
    _write(f, _doc(), 2)
    _commit(root, "two")
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert check_repo.check_surgical_diff() == []
    # The working-tree path release.py takes has no such exemption.
    _write(f, _doc(), 1)
    found, _ = surgical_diff.reformats(root, "HEAD")
    assert [x.path for x in found] == ["data.json"]


def test_guard_has_nothing_to_say_on_a_root_commit_or_without_git(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_surgical_diff() == []
    root = _repo(tmp_path)
    (root / "a.txt").write_text("x\n")
    _commit(root)
    assert check_repo.check_surgical_diff() == []


# --- the real history this was written against -------------------------------

@pytest.mark.parametrize("version, path, real_ceiling", [
    ("0.1.681", "adapters/shipped.json", 5),
    ("0.1.673", "evals/gates.json", 8),
    ("0.1.674", "evals/rule-coverage.json", 144),
])
def test_it_names_the_reformats_this_repository_actually_shipped(version, path, real_ceiling):
    root = pathlib.Path(__file__).resolve().parents[1]
    if not (root / ".git").exists():
        pytest.skip("not a git checkout")
    rev = subprocess.run(["git", "log", "--format=%H", "--grep", f"^{version} ", "-1"],
                         cwd=root, capture_output=True, text=True).stdout.strip()
    if not rev:
        pytest.skip(f"{version} is not in this clone's history")
    found, problem = surgical_diff.reformats(root, f"{rev}~1", rev)
    assert problem is None
    hit = {x.path: x for x in found}
    assert path in hit and hit[path].real <= real_ceiling
