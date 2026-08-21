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


# `--run` names a run, and only sometimes names a path.

def _resolve(runs, results):
    """The resolution `run` performs on `--run`, isolated.

    Kept as a helper mirroring the branch rather than calling `main()`, because
    reaching that line means driving agents. What it must never do again is
    resolve a bare name against the working directory.
    """
    import pathlib
    given = pathlib.Path(runs[0]).expanduser()
    return (given if given.is_absolute() or len(given.parts) > 1
            else results / given)


def test_a_bare_run_id_lands_under_the_results_root(tmp_path):
    """`--run r13` from inside the checkout wrote the whole run INTO the
    checkout — transcripts, driver records and an agent's deck — which is the
    one place the owner directive says conformance results may not go."""
    assert _resolve(["r13-phase3"], tmp_path) == tmp_path / "r13-phase3"


def test_an_explicit_path_is_still_honoured(tmp_path):
    """An operator pointing at a scratch directory means it."""
    absolute = tmp_path / "elsewhere" / "run1"
    assert _resolve([str(absolute)], tmp_path / "results") == absolute
    assert _resolve(["sub/dir"], tmp_path).as_posix() == "sub/dir"


def test_agent_is_repeatable_and_every_name_has_to_resolve(tmp_path):
    """Two things at once, because one caused the other.

    `--agent` took a SINGLE value until 0.1.550, so `--agent a --agent b
    --agent c` kept the last and a round announced as three agents drove one.
    And the selection failed only when NOTHING matched, so a round with one
    good name and two typos would have run the good one and said nothing.

    Driven through the real CLI rather than by reading the parser: what is
    under test is what an operator's command line does.
    """
    import subprocess
    import sys
    proc = subprocess.run(
        [sys.executable, str(rc.ROOT / "scripts" / "ops" / "run_conformance.py"),
         "run", "--agent", "claude-code", "--agent", "no-such-agent",
         "--run", str(tmp_path / "unused")],
        capture_output=True, text=True, cwd=rc.ROOT)
    assert proc.returncode == 1, proc.stdout
    # The bad name is named; the good one is not mistaken for the failure.
    assert "no-such-agent" in proc.stdout
    assert "claude-code" not in proc.stdout.split("no platform")[-1]
