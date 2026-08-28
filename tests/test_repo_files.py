"""One way to ask git, and the two callers that used to go blind when it failed.

`git ls-files` was spelled thirteen ways with three failure policies. Most said
"a scan that did not run is not a scan that passed"; two returned an empty list,
and one of those fed the English-only red line — the FM-24 shape, printing on a
broken tree exactly what it prints on a clean one.
"""
import subprocess

import check_repo
import pytest
import repo_files as rf


def _repo(tmp_path, files):
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, body in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_tracked_files_lists_what_git_tracks(tmp_path):
    root = _repo(tmp_path / "r", {"a.md": "x", "b/c.json": "{}"})
    names, problem = rf.tracked_files(root=root)
    assert problem is None and sorted(names) == ["a.md", "b/c.json"]


def test_a_pathspec_narrows_it(tmp_path):
    root = _repo(tmp_path / "r", {"a.md": "x", "b/c.json": "{}"})
    names, _ = rf.tracked_files("*.json", root=root)
    assert names == ["b/c.json"]


def test_a_filename_with_a_newline_survives(tmp_path):
    """`-z` always. Five callers split on newlines, which is a bug waiting for
    a filename with one in it."""
    root = _repo(tmp_path / "r", {"two\nlines.md": "x"})
    names, problem = rf.tracked_files(root=root)
    assert problem is None and names == ["two\nlines.md"]


def test_no_git_is_a_problem_not_an_empty_repository(tmp_path):
    (tmp_path / "empty").mkdir()
    names, problem = rf.tracked_files(root=tmp_path / "empty")
    assert names == [] and problem and "did not run" in problem


def test_ignored_files_finds_what_is_present_and_excluded(tmp_path):
    root = _repo(tmp_path / "r", {".gitignore": "assets/*.png\n"})
    (root / "assets").mkdir(exist_ok=True)
    (root / "assets/hidden.png").write_text("x", encoding="utf-8")
    names, problem = rf.ignored_files("assets/", root=root)
    assert problem is None and names == ["assets/hidden.png"]


def test_run_git_returns_the_code_and_the_output(tmp_path):
    root = _repo(tmp_path / "r", {"a.md": "x"})
    rc, out = rf.run_git("status", "--porcelain", root=root)
    assert rc == 0 and "a.md" in out
    rc, _ = rf.run_git("cat-file", "-e", "deadbeef", root=root)
    assert rc != 0


def test_the_manifest_reader_raises_rather_than_scanning_nothing(tmp_path, monkeypatch):
    """It returned `[]` when git could not be asked, so `check_english_only`
    read no files and reported a clean tree. main() turns a raising guard into
    that guard's failure, which is the answer this needed.

    A `.git` that is there and unusable, not an absent one: a tarball checkout
    with no index is a THIRD answer the reader keeps, and it still returns [].
    """
    broken = tmp_path / "broken"
    (broken / ".git").mkdir(parents=True)
    monkeypatch.setattr(check_repo, "ROOT", broken)
    with pytest.raises(RuntimeError):
        check_repo._json_manifests()


def test_a_tarball_checkout_is_not_a_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", tmp_path / "no-git")
    (tmp_path / "no-git").mkdir()
    assert check_repo._json_manifests() == []
