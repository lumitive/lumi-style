"""No tracked file names an operator's home directory.

Six leaks of one username across five tracked files when this was written, and
one of them was written there by a generator: `report --record` put the run
directory's absolute path on the board's fourth line, so every recorded
conformance run carried the owner's username into git.
"""
import subprocess

import check_repo


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_a_tilde_path_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "conformance/CONFORMANCE.md": "Runs `~/Documents/x/r16-pinned`\n"}))
    assert check_repo.check_local_paths() == []


def test_a_home_path_fails_with_line_and_the_fix(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "conformance/CONFORMANCE.md":
            "board\nRuns `/Users/dana/Documents/x/r16-pinned`\n"}))
    errors = check_repo.check_local_paths()
    assert len(errors) == 1
    assert "conformance/CONFORMANCE.md:2" in errors[0]
    assert "/Users/dana" in errors[0] and "~/" in errors[0]


def test_a_linux_home_path_fails_too(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": "/home/dana/checkout\n"}))
    assert len(check_repo.check_local_paths()) == 1


def test_a_placeholder_name_is_not_a_person(tmp_path, monkeypatch):
    """An install instruction is the prose that most naturally names a home
    directory. Failing `/Users/you` accused the author of shipping a username
    they had not shipped, and told them to rewrite a correct sentence."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "README.md": "copy it to /Users/you/.claude/skills (or /home/you/...)\n",
        "specs/2026-01-01-x-plan.md": "cd /Users/x/project\n"}))
    assert check_repo.check_local_paths() == []


def test_the_tilde_user_form_leaks_too(tmp_path, monkeypatch):
    """`~dana/` leaks the username exactly as the absolute form does, and it is
    what a careless author writes after reading this guard's own advice."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": "the board recorded ~dana/Documents/run-01\n"}))
    errors = check_repo.check_local_paths()
    assert len(errors) == 1 and "~dana" in errors[0]


def test_a_tilde_that_is_not_a_path_passes(tmp_path, monkeypatch):
    """`~2.6s` is "about 2.6 seconds". The first draft of the tilde form failed
    on the CHANGELOG's own performance figures."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": "the step took ~2.6s, down from ~90s\n"}))
    assert check_repo.check_local_paths() == []


def test_an_untracked_file_is_not_scanned(tmp_path, monkeypatch):
    """Guards that walk the filesystem have failed this repository before: a
    checkout under the tree is not part of it."""
    root = _repo(tmp_path, {"README.md": "clean\n"})
    (root / "scratch.md").write_text("/Users/dana/thing\n")
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert check_repo.check_local_paths() == []


def test_a_waiver_silences_with_a_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": "the transcript named /Users/dana/deck.html\n"}))
    monkeypatch.setitem(check_repo.LOCAL_PATH_WAIVERS,
                        ("notes.md", "/Users/dana"),
                        "quoted evidence from a transcript")
    assert check_repo.check_local_paths() == []


def test_tests_are_not_scanned(tmp_path, monkeypatch):
    """A synthetic tree's fixtures name paths that exist only in tmp_path, and
    THIS FILE has to plant the string the guard looks for. Missing the
    exclusion shipped a guard that passed while its own tests were untracked
    and failed the moment they were committed — the scan reads git, not the
    disk."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "tests/test_x.py": 'assert "/Users/dana/x" in out\n'}))
    assert check_repo.check_local_paths() == []
