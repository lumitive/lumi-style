"""The commit-convention guard on synthetic git repositories."""
import subprocess

import check_repo


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True, text=True)


def _repo(tmp_path, subject, touch_changelog=True, heading="0.1.500"):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "CHANGELOG.md").write_text(f"# Changelog\n\n## {heading} — x\n")
    (tmp_path / "other.md").write_text("hi\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "0.1.499 — base")
    if touch_changelog:
        (tmp_path / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## {heading} — x\n\nmore\n")
    else:
        (tmp_path / "other.md").write_text("changed\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", subject)
    return tmp_path


def test_conforming_release_commit_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _repo(tmp_path, "0.1.500 — did the thing"))
    assert check_repo.check_commit_convention() == []


def test_missing_prefix_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _repo(tmp_path, "did the thing"))
    errors = check_repo.check_commit_convention()
    assert len(errors) == 1 and "does not follow" in errors[0]


def test_version_mismatch_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _repo(tmp_path, "0.1.999 — did the thing"))
    errors = check_repo.check_commit_convention()
    assert len(errors) == 1 and "lying" in errors[0]


def test_non_changelog_commit_is_exempt(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _repo(tmp_path, "specs — notes", touch_changelog=False))
    assert check_repo.check_commit_convention() == []


def test_no_git_tree_is_exempt(tmp_path, monkeypatch):
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 0.1.500 — x\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_commit_convention() == []


def test_live_repo_head_conforms():
    assert check_repo.check_commit_convention() == []
