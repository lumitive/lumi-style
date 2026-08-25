"""The board's "N releases behind" is recomputed on both sides.

Measured by walking `conformance/CONFORMANCE.md`'s whole history for the
longest span carrying one unchanged clause: `newest run 0.1.578 · 3 releases
behind` shipped in TWENTY-FOUR consecutive releases, 0.1.581 through 0.1.604.
It was true when written at 0.1.581 and wrong for the twenty-three after it,
understating a distance that reached 26 — already 14 by 0.1.592.

Two failure shapes, and both sides have to see them: the clause frozen at a
number that was true once, and the clause missing entirely (when a board is
fresh the generator omits it, so the next stamp bump leaves a header that
discloses nothing rather than something wrong).

EVERYTHING RUNS IN A SYNTHETIC TREE. The first version of this file drove the
real CLI against the real repository, and a review's mutation test proved the
cost: `restamp` writes before the assertion, so a red test left the tracked
board reading `skill 0.1.328 · 277 releases behind` and the next `check_repo`
failed on damage the suite had done. That is the sibling conftest change's own
rule — the suite must not write into what it measures — broken in the same
commit.
"""
import pathlib
import re

import check_repo
import run_conformance

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _tree(tmp_path, header, runs_line, changelog_versions):
    (tmp_path / "conformance").mkdir(exist_ok=True)
    (tmp_path / "conformance" / "CONFORMANCE.md").write_text(
        f"<!-- generated -->\n{header}\n\n{runs_line}\n\n"
        "| agent | verdict |\n|---|---|\n| x | pass |\n"
        "<!-- end generated -->\n\nprose below the marker\n",
        encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "".join(f"## {v} — a release\n\nbody\n\n" for v in changelog_versions),
        encoding="utf-8")
    return tmp_path


def _both(tmp_path, monkeypatch, header, runs_line, versions):
    """Point BOTH readers at the synthetic tree.

    They resolve their own ROOT from `__file__`, so patching one and not the
    other is how the guard's first test failed: it read the board from the
    temporary tree and the CHANGELOG from the real one.
    """
    _tree(tmp_path, header, runs_line, versions)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(run_conformance, "ROOT", tmp_path)
    return tmp_path / "conformance" / "CONFORMANCE.md"


RUNS = "Runs `~/x/_conformance/{v}-2026-08-23` · run 2026-08-23 · darwin"


# ---------------------------------------------------------------- the guard

def test_the_shipped_board_states_its_own_distance():
    assert check_repo.check_board_staleness_clause() == []


def test_the_guard_is_registered():
    """A guard with no CHECKS entry does not run, however green its own tests."""
    assert any(name == "board staleness clause" for name, _ in check_repo.CHECKS)


def test_a_frozen_clause_fails(tmp_path, monkeypatch):
    """The twenty-four-release defect, in miniature."""
    _both(tmp_path, monkeypatch,
          "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
          "3 releases behind",
          RUNS.format(v="0.1.578"),
          ["0.1.604", "0.1.603", "0.1.602", "0.1.601", "0.1.578"])
    errors = check_repo.check_board_staleness_clause()
    assert errors, "a header claiming 3 behind when it is 4 behind passed"
    assert "4 releases behind" in errors[0]


def test_a_missing_clause_fails(tmp_path, monkeypatch):
    """The other side: silence where a distance belongs."""
    _both(tmp_path, monkeypatch, "# LUMI style conformance · skill 0.1.604",
          RUNS.format(v="0.1.578"), ["0.1.604", "0.1.603", "0.1.578"])
    errors = check_repo.check_board_staleness_clause()
    assert errors, "a header with no clause at all passed while 2 behind"
    assert "2 releases behind" in errors[0]


def test_a_fresh_board_needs_no_clause(tmp_path, monkeypatch):
    _both(tmp_path, monkeypatch, "# LUMI style conformance · skill 0.1.604",
          RUNS.format(v="0.1.604"), ["0.1.604", "0.1.603"])
    assert check_repo.check_board_staleness_clause() == []


def test_a_fresh_board_may_not_keep_a_leftover_clause(tmp_path, monkeypatch):
    """`expected in header` accepted this; equality does not.

    A board brought up to date whose stale clause was never removed is the
    frozen-number shape in its most convincing form — the version is right,
    so the line reads current.
    """
    _both(tmp_path, monkeypatch,
          "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
          "3 releases behind",
          RUNS.format(v="0.1.604"), ["0.1.604", "0.1.603", "0.1.578"])
    errors = check_repo.check_board_staleness_clause()
    assert errors, "a fresh board carrying a leftover stale clause passed"


def test_an_uncomputable_distance_fails_rather_than_passing(tmp_path, monkeypatch):
    """FM-01: the state where the fix declines must not be the state the guard allows.

    `cmd_restamp` leaves the header alone when the run is not a release the
    CHANGELOG carries. If the guard also went quiet there, nothing would be
    watching — and a review reproduced the whole original defect through that
    hole with both reporting success.
    """
    _both(tmp_path, monkeypatch,
          "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
          "3 releases behind",
          RUNS.format(v="0.1.100"), ["0.1.604", "0.1.603"])
    errors = check_repo.check_board_staleness_clause()
    assert errors, "an unchecked clause passed as a checked one"
    assert "unchecked" in errors[0]


def test_a_versionless_run_id_is_read_through_the_generator(tmp_path, monkeypatch):
    """`results/latest` is a board `report --record` writes, not a broken file.

    `_board_run_version` falls back to the newest `instrument_version` in the
    run's scores.json for exactly this case. A second, lossier reader here
    failed the repository on a correct board — and, through the realigner,
    made every release impossible.
    """
    run_dir = tmp_path / "results" / "latest"
    run_dir.mkdir(parents=True)
    (run_dir / "scores.json").write_text(
        '{"a/T1": {"instrument_version": "0.1.578"}}', encoding="utf-8")
    _both(tmp_path, monkeypatch,
          "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
          "26 releases behind",
          f"Runs `{run_dir}` · run 2026-08-23 · darwin",
          ["0.1.604"] + [f"0.1.{n}" for n in range(603, 577, -1)])
    assert check_repo.check_board_staleness_clause() == []


# -------------------------------------------------------------- the restamp

def _restamp(tmp_path, monkeypatch, header, runs_line, versions, version=None):
    board = _both(tmp_path, monkeypatch, header, runs_line, versions)
    rc = run_conformance.cmd_restamp(version or versions[0])
    return rc, board.read_text(encoding="utf-8")


def test_restamp_rewrites_a_frozen_clause(tmp_path, monkeypatch, capsys):
    """The actor, observed acting. Every mutation inside it used to survive."""
    rc, text = _restamp(
        tmp_path, monkeypatch,
        "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
        "3 releases behind",
        RUNS.format(v="0.1.578"),
        ["0.1.604", "0.1.603", "0.1.602", "0.1.601", "0.1.578"])
    assert rc == 0
    assert "4 releases behind" in text.splitlines()[1]
    assert "restamped" in capsys.readouterr().out
    # AND ONLY THE HEADER. The table, the failure list and the prose below the
    # generated marker are the run's, not this command's.
    assert "prose below the marker" in text and "| x | pass |" in text


def test_restamp_says_one_release_in_the_singular(tmp_path, monkeypatch):
    rc, text = _restamp(
        tmp_path, monkeypatch, "# LUMI style conformance · skill 0.1.604",
        RUNS.format(v="0.1.603"), ["0.1.604", "0.1.603"])
    assert rc == 0
    assert "1 release behind" in text.splitlines()[1]
    assert "1 releases behind" not in text


def test_restamp_is_idempotent(tmp_path, monkeypatch, capsys):
    """It runs on every release, so the second run must change nothing."""
    rc, first = _restamp(
        tmp_path, monkeypatch,
        "# LUMI style conformance · skill 0.1.604 · newest run 0.1.578 · "
        "3 releases behind",
        RUNS.format(v="0.1.578"), ["0.1.604", "0.1.603", "0.1.578"])
    assert rc == 0
    capsys.readouterr()
    assert run_conformance.cmd_restamp("0.1.604") == 0
    board = tmp_path / "conformance" / "CONFORMANCE.md"
    assert board.read_text(encoding="utf-8") == first
    assert "already reads" in capsys.readouterr().out


def test_restamp_refuses_a_version_the_changelog_does_not_carry(tmp_path,
                                                                monkeypatch,
                                                                capsys):
    """Naming the side that is actually missing.

    `_releases_between` returns None when EITHER argument is absent, and the
    first version blamed the board unconditionally — so asking for a version
    that has no CHANGELOG entry reported that the BOARD predated the file, and
    sent a reader to look at run directories.
    """
    rc, _ = _restamp(tmp_path, monkeypatch,
                     "# LUMI style conformance · skill 0.1.604",
                     RUNS.format(v="0.1.604"), ["0.1.604"], version="0.1.608")
    assert rc == 1
    out = capsys.readouterr().out
    assert "0.1.608 is not a CHANGELOG heading" in out


def test_restamp_leaves_a_pre_history_board_alone(tmp_path, monkeypatch, capsys):
    """Exit 0 and no write — but the guard fails on the same state, so it is
    not silence."""
    rc, text = _restamp(tmp_path, monkeypatch,
                        "# LUMI style conformance · skill 0.1.604",
                        RUNS.format(v="0.1.100"), ["0.1.604", "0.1.603"])
    assert rc == 0
    assert text.splitlines()[1] == "# LUMI style conformance · skill 0.1.604"
    assert "not a release this CHANGELOG carries" in capsys.readouterr().out
    assert check_repo.check_board_staleness_clause(), (
        "restamp declined and the guard passed: nothing is watching")


def test_restamp_refuses_a_misshapen_board(tmp_path, monkeypatch, capsys):
    board = _both(tmp_path, monkeypatch, "not a header at all",
                  "not a Runs line", ["0.1.604"])
    assert run_conformance.cmd_restamp("0.1.604") == 1
    assert "not in the shape" in capsys.readouterr().out
    assert "not a header at all" in board.read_text(encoding="utf-8")


def test_restamp_refuses_a_missing_board(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_conformance, "ROOT", tmp_path)
    assert run_conformance.cmd_restamp("0.1.604") == 1
    assert "does not exist" in capsys.readouterr().out


def test_the_header_has_one_author(tmp_path, monkeypatch):
    """`render`, `restamp` and the guard must not transcribe the format thrice.

    Change the title in `board_header` and every consumer changes with it; if
    one of them kept its own copy, `restamp` would silently rewrite `render`'s
    output back on the next release — a drift bomb inside a drift fix.
    """
    src = (ROOT / "scripts" / "ops" / "run_conformance.py").read_text(encoding="utf-8")
    guard = (ROOT / "scripts" / "check" / "check_repo.py").read_text(encoding="utf-8")
    literal = "# LUMI style conformance · "
    assert src.count(f'f"{literal}') == 1, (
        "the header format is written more than once in run_conformance.py")
    assert literal not in guard, (
        "check_repo transcribes the header format instead of calling "
        "run_conformance.board_header")
    assert len(re.findall(r"release\{'' if behind == 1 else 's'\}", src)) == 1, (
        "the singular/plural rule is written more than once")
