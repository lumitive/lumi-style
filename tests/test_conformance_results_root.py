"""Where a multi-agent run writes, and what it refuses to create.

Owner directive (2026-08-21): the verification directories for LUMI Style all
live under the deliverable folder. The runs are documents a person reads —
decks, rewrites, transcripts — and they sat inside the checkout until 0.1.542.

The older directive this must not break is 2026-08-09's: nothing in this
package creates a directory in someone's home without being asked. So the
resolver READS the deliverable folder and never makes it, and a machine that
has not run `output_dir.py --create` keeps its runs where they were.
"""
import importlib

import run_conformance as rc


def _reload(monkeypatch, **env):
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)
    return importlib.reload(rc)


def test_the_override_wins_and_is_expanded(monkeypatch, tmp_path):
    m = _reload(monkeypatch, LUMI_CONFORMANCE_RESULTS=str(tmp_path / "elsewhere"))
    assert m.RESULTS == tmp_path / "elsewhere"
    _reload(monkeypatch, LUMI_CONFORMANCE_RESULTS=None)


def test_an_existing_deliverable_folder_takes_the_runs(monkeypatch, tmp_path):
    deliverables = tmp_path / "Documents" / "LUMI-Style"
    deliverables.mkdir(parents=True)
    monkeypatch.setattr(rc.output_dir, "output_dir", lambda: deliverables)
    assert rc._results_root() == deliverables / "_conformance"


def test_a_missing_deliverable_folder_is_not_created(monkeypatch, tmp_path):
    # The whole point of the 2026-08-09 directive: a package that silently
    # makes a folder in someone's home is one nobody installs twice.
    deliverables = tmp_path / "Documents" / "LUMI-Style"
    monkeypatch.setattr(rc.output_dir, "output_dir", lambda: deliverables)
    assert rc._results_root() == rc.IN_REPO_RESULTS
    assert not deliverables.exists(), "the resolver created the folder"


def test_an_unresolvable_home_falls_back_rather_than_raising(monkeypatch):
    def boom():
        raise rc.output_dir.Unresolvable("no home directory for this user")
    monkeypatch.setattr(rc.output_dir, "output_dir", boom)
    assert rc._results_root() == rc.IN_REPO_RESULTS
