"""How far the published package is behind, reported and never gated.

The projection advances only when `publish.sh --push` runs and this repository
advances on every merge, so nothing joins them. It fell behind once between
0.1.580 and 0.1.581, and a person noticing was the only thing that caught it.

Being behind is a NORMAL state — a maintainer may hold several releases before
publishing. What is not normal is not knowing, which is why this reports.
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "ops"),
                str(ROOT / "scripts" / "lib")]
import release  # noqa: E402


def _no_network(monkeypatch, out="", rc=0):
    monkeypatch.setattr(release, "run", lambda cmd, **kw: types.SimpleNamespace(
        returncode=rc, stdout=out, stderr=""))


def test_the_published_version_is_read_from_the_stamp(monkeypatch):
    _no_network(monkeypatch, 'metadata:\n  version: "0.1.500"\n')
    assert release.published_version() == "0.1.500"


def test_a_failed_fetch_is_none_rather_than_a_guess(monkeypatch):
    """A release must not fail because an advisory note could not be written,
    and a note that claimed 'current' on a failed fetch would be worse than
    none."""
    _no_network(monkeypatch, "", rc=7)
    assert release.published_version() is None


def test_a_stamp_that_does_not_parse_is_none(monkeypatch):
    _no_network(monkeypatch, "a file with no version stamp at all\n")
    assert release.published_version() is None


def test_in_sync_says_nothing_to_publish(monkeypatch, capsys):
    monkeypatch.setattr(release, "published_version", lambda **kw: "0.1.581")
    release.report_published("0.1.581")
    assert "nothing to publish" in capsys.readouterr().out


def test_behind_names_the_gap_and_the_command(monkeypatch, capsys):
    monkeypatch.setattr(release, "published_version", lambda **kw: "0.1.578")
    monkeypatch.setattr(release, "_releases_between", lambda a, b: 3)
    release.report_published("0.1.581")
    out = capsys.readouterr().out
    assert "3 release(s) ahead" in out and "publish.sh --push" in out


def test_a_newer_published_version_is_not_a_negative_gap(monkeypatch, capsys):
    """It means this checkout is behind its own remote, or something published
    from elsewhere. Either is worth saying plainly rather than dressing as a
    publishing gap of minus three."""
    monkeypatch.setattr(release, "published_version", lambda **kw: "0.1.581")
    monkeypatch.setattr(release, "_releases_between", lambda a, b: -3)
    release.report_published("0.1.578")
    out = capsys.readouterr().out
    assert "NEWER" in out and "-3" not in out


def test_an_unaskable_remote_says_so(monkeypatch, capsys):
    monkeypatch.setattr(release, "published_version", lambda **kw: None)
    release.report_published("0.1.581")
    out = capsys.readouterr().out
    assert "could not ask" in out and "unknown" in out


def test_the_gap_is_counted_from_the_changelog_not_from_git():
    """The projection's commits are REWRITTEN, so their hashes cannot be
    compared to this repository's at all."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    import re
    vs = re.findall(r"^## (\d+\.\d+\.\d+) — ", text, re.M)
    assert len(vs) > 2
    assert release._releases_between(vs[2], vs[0]) == 2
    assert release._releases_between("0.0.0", vs[0]) is None
