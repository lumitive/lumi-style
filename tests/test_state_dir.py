"""Operator-owned stores resolve to one place, and it is not always the repo.

Four stores resolved against the repository root — the trace store, the local
corpus registry, the price table and the review scores. Three are gitignored on
purpose (one machine's facts with dates on them), and all four would have no
directory to live in once the skill is installed from a projection that carries
no `evals/` or `reviews/`.
"""
import pathlib

import state_dir

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_lumi_state_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMI_STATE", str(tmp_path))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    assert state_dir.state_dir() == tmp_path


def test_xdg_is_next(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMI_STATE", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert state_dir.state_dir() == tmp_path / "lumi"


def test_the_home_default_is_last(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMI_STATE", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert state_dir.state_dir() == tmp_path / ".lumi"


def test_an_existing_in_repo_store_keeps_its_data(tmp_path, monkeypatch):
    """The migration is a no-op for a maintainer's checkout ON PURPOSE: no
    release moves an operator's file, and a directory that already holds data
    goes on holding it."""
    monkeypatch.setenv("LUMI_STATE", str(tmp_path / "state"))
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "traces").mkdir()
    assert state_dir.store("traces", in_repo=("evals", "traces"),
                           root=tmp_path) == tmp_path / "evals" / "traces"


def test_an_absent_in_repo_store_falls_to_state(tmp_path, monkeypatch):
    """What an installed skill sees: no `evals/` at all."""
    monkeypatch.setenv("LUMI_STATE", str(tmp_path / "state"))
    assert state_dir.store("traces", in_repo=("evals", "traces"),
                           root=tmp_path) == tmp_path / "state" / "traces"


def test_nothing_is_created_by_resolving(tmp_path, monkeypatch):
    """`check_privacy.py`'s LUMI_TERMS_DIR is the precedent and the 2026-08-09
    instruction is explicit: create on an explicit write, never on import and
    never on a read."""
    monkeypatch.setenv("LUMI_STATE", str(tmp_path / "state"))
    state_dir.store("traces", in_repo=("evals", "traces"), root=tmp_path)
    assert not (tmp_path / "state").exists()


def test_no_store_resolves_its_own_path():
    """A fifth store resolved by hand is the drift this module ends.

    Asserted on the SOURCE, not on the resolved constants. The first version
    ran the four modules and checked their basenames — but every basename is
    identical under the pre-0.1.571 `ROOT / "evals" / "corpus.local.json"`, so
    reverting the fix passed it. And it cannot be asserted on the values
    either: `in_repo` correctly wins in a maintainer's checkout, which is where
    the suite runs.
    """
    stores = {
        "scripts/lib/corpus.py": "corpus.local.json",
        "scripts/ops/ledger.py": "prices.local.json",
        "scripts/ops/review_scores.py": "scores.json",
        "scripts/lib/trace_store.py": "traces",
    }
    for rel, leaf in stores.items():
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert "state_dir.store(" in src, f"{rel} does not ask state_dir"
        assert leaf in src, f"{rel} no longer names {leaf}"
        # and nobody builds the in-repo path themselves any more
        for hand in ('ROOT / "evals" / "', 'ROOT / "reviews" / "'):
            assert hand not in src, f"{rel} resolves {hand!r} by hand"
