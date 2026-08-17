"""The unshipped-release counter, and the rebase it has to survive.

Forty releases once accumulated on a branch that was never pushed while every
local check stayed green. The counter exists so that is a number somebody sees.
It must be right in the one situation this repository actually lands work in:
a rebase-merge, which gives every commit a new hash and would make a naive
`origin/main..HEAD` count report the whole branch as unshipped immediately
after shipping it.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import shipping  # noqa: E402


def _git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@example.org", "-c", "user.name=T", *args],
        cwd=cwd, capture_output=True, text=True, check=True)


def _commit(cwd, subject, body="x"):
    (cwd / "CHANGELOG.md").write_text(f"{body}\n{subject}\n")
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-q", "-m", subject)


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    return tmp_path


def _set_origin_main(cwd, ref="HEAD"):
    sha = _git(cwd, "rev-parse", ref).stdout.strip()
    _git(cwd, "update-ref", "refs/remotes/origin/main", sha)


def test_everything_shipped_reads_zero(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "0.1.1 — first")
    _commit(r, "0.1.2 — second")
    _set_origin_main(r)
    monkeypatch.setattr(shipping, "ROOT", r)
    count, _ = shipping.unshipped()
    assert count == 0


def test_a_release_committed_and_not_pushed_is_counted(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "0.1.1 — first")
    _set_origin_main(r)
    _commit(r, "0.1.2 — second")
    _commit(r, "0.1.3 — third")
    monkeypatch.setattr(shipping, "ROOT", r)
    count, _ = shipping.unshipped()
    assert count == 2


def test_a_rebase_does_not_resurrect_shipped_releases(tmp_path, monkeypatch):
    """The regression this counter was rewritten for.

    origin/main carries the same two releases under DIFFERENT hashes, which is
    exactly what `gh pr merge --rebase` produces. Counting commits would say 2;
    counting versions says 0, which is the truth.
    """
    r = _repo(tmp_path)
    _commit(r, "0.1.1 — first")
    _commit(r, "0.1.2 — second")
    branch_head = _git(r, "rev-parse", "HEAD").stdout.strip()

    _git(r, "checkout", "-q", "--orphan", "rebased")
    _commit(r, "0.1.1 — first", body="rewritten")
    _commit(r, "0.1.2 — second", body="rewritten")
    _set_origin_main(r, "HEAD")
    _git(r, "checkout", "-q", branch_head)

    monkeypatch.setattr(shipping, "ROOT", r)
    ahead = _git(r, "rev-list", "--count", "refs/remotes/origin/main..HEAD").stdout.strip()
    assert ahead == "2", "the commits really are distinct — this is the trap"
    count, _ = shipping.unshipped()
    assert count == 0


def test_a_non_release_commit_is_not_a_release(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "0.1.1 — first")
    _set_origin_main(r)
    _commit(r, "fix a typo in the readme")
    monkeypatch.setattr(shipping, "ROOT", r)
    count, _ = shipping.unshipped()
    assert count == 0


def test_no_origin_main_is_not_counted_as_nothing_owed(tmp_path, monkeypatch):
    """None is not zero. A checkout that cannot be asked must say so."""
    r = _repo(tmp_path)
    _commit(r, "0.1.1 — first")
    monkeypatch.setattr(shipping, "ROOT", r)
    count, note = shipping.unshipped()
    assert count is None
    assert "origin/main" in note


def test_no_git_at_all_is_not_counted(tmp_path, monkeypatch):
    monkeypatch.setattr(shipping, "ROOT", tmp_path)
    count, _ = shipping.unshipped()
    assert count is None
