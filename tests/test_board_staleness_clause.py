"""The board's "N releases behind" is recomputed on both sides.

Two failure shapes, and the guard has to see both: the clause frozen at a
number that was true once (0.1.592-0.1.604 shipped `3 releases behind` fourteen
times while the distance grew to twenty-six), and the clause missing entirely
(when a board is fresh the generator omits it, so the next stamp bump leaves a
header that discloses nothing rather than something wrong).
"""
import pathlib
import subprocess
import sys

import check_repo

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESTAMP = [sys.executable, str(ROOT / "scripts" / "ops" / "run_conformance.py"),
           "restamp"]


def test_the_shipped_board_states_its_own_distance():
    assert check_repo.check_board_staleness_clause() == []


def _tree(tmp_path, header, runs_version, changelog_versions, monkeypatch):
    (tmp_path / "conformance").mkdir()
    (tmp_path / "conformance" / "CONFORMANCE.md").write_text(
        f"<!-- generated -->\n{header}\n\n"
        f"Runs `~/x/_conformance/{runs_version}-2026-08-23` · run 2026-08-23\n",
        encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "".join(f"## {v} — a release\n\nbody\n\n" for v in changelog_versions),
        encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    return tmp_path


def test_a_frozen_clause_fails(tmp_path, monkeypatch):
    """The fourteen-release defect, in miniature."""
    _tree(tmp_path,
          "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
          "3 releases behind",
          "0.1.578", ["0.1.604", "0.1.603", "0.1.602", "0.1.601", "0.1.578"],
          monkeypatch)
    errors = check_repo.check_board_staleness_clause()
    assert errors, "a header claiming 3 behind when it is 4 behind passed"
    assert "4 releases behind" in errors[0]


def test_a_missing_clause_fails(tmp_path, monkeypatch):
    """The other side: silence where a distance belongs."""
    _tree(tmp_path, "# LUMI style conformance · skill 0.1.604",
          "0.1.578", ["0.1.604", "0.1.603", "0.1.578"], monkeypatch)
    errors = check_repo.check_board_staleness_clause()
    assert errors, "a header with no clause at all passed while 2 behind"
    assert "2 releases behind" in errors[0]


def test_a_fresh_board_needs_no_clause(tmp_path, monkeypatch):
    _tree(tmp_path, "# LUMI style conformance · skill 0.1.604",
          "0.1.604", ["0.1.604", "0.1.603"], monkeypatch)
    assert check_repo.check_board_staleness_clause() == []


def test_a_run_older_than_the_changelog_is_left_alone(tmp_path, monkeypatch):
    """Not every unknown is a failure. The guard checks the clause, not history."""
    _tree(tmp_path, "# LUMI style conformance · skill 0.1.604",
          "0.1.100", ["0.1.604", "0.1.603"], monkeypatch)
    assert check_repo.check_board_staleness_clause() == []


def test_restamp_is_idempotent_and_touches_only_the_header():
    """It runs on every release, so running it twice must change nothing."""
    board = ROOT / "conformance" / "CONFORMANCE.md"
    before = board.read_text(encoding="utf-8")
    first = subprocess.run(RESTAMP, capture_output=True, text=True, cwd=ROOT)
    assert first.returncode == 0, first.stderr
    assert board.read_text(encoding="utf-8") == before, (
        "restamp changed the shipped board; the guard says it is already correct")
    assert "already reads" in first.stdout
