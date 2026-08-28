"""The conformance-freshness half of the evidence gate, both directions."""
import json
import pathlib

import check_evidence

CHANGELOG = "# Changelog\n\n" + "\n".join(
    f"## 0.1.{500 - i} — r{i}\n" for i in range(30))


def _tree(tmp_path, rows):
    (tmp_path / "conformance").mkdir()
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG)
    if rows is not None:
        (tmp_path / "conformance/history.json").write_text(json.dumps(rows))
    return tmp_path


def _row(version, agent="claude-code"):
    return {"skill_version": version, "agent": agent, "date": "2026-08-12",
            "run_dir": "x", "scores_sha256": "abc",
            "tasks": {"T1-deck": "fail", "T2-deaify": "pass",
                      "T3-recall": "pass"}}


def test_unarmed_without_history_file(tmp_path, monkeypatch):
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, None))
    assert check_evidence.conformance_fresh() is None


def test_fresh_with_two_recent_agents(tmp_path, monkeypatch):
    rows = [_row("0.1.500", "claude-code"), _row("0.1.495", "cursor")]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is True


def test_stale_with_one_recent_agent(tmp_path, monkeypatch):
    rows = [_row("0.1.500", "claude-code"), _row("0.1.450", "cursor")]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is False


def test_stale_when_rows_predate_the_window(tmp_path, monkeypatch):
    rows = [_row("0.1.450", "claude-code"), _row("pre-history", "cursor")]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is False


def test_freshness_ignores_pass_fail(tmp_path, monkeypatch):
    """The gate binds on recency, never on passing: two recent agents whose
    rows fail EVERY task still count as measurement, so the board is fresh
    (GAP-001 stays open on its own ledger; blocking releases on it would
    invite overclaim)."""
    all_fail = {"T1-deck": "fail", "T2-deaify": "fail", "T3-recall": "fail"}
    rows = [dict(_row("0.1.500", "claude-code"), tasks=all_fail),
            dict(_row("0.1.498", "cursor"), tasks=all_fail)]
    monkeypatch.setattr(check_evidence, "ROOT", _tree(tmp_path, rows))
    assert check_evidence.conformance_fresh() is True


# The board used to name the instrument alone, so a page rendering runs from
# 0.1.454 sat under the words "skill 0.1.502" — a version it had never measured
# anything at. That is the claim `built_version` exists to stop a CELL making,
# made by the page the cells sit on.

def _rc():
    import importlib.util
    root = pathlib.Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "rc_board", root / "scripts" / "ops" / "run_conformance.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_the_run_version_is_read_from_the_run_id():
    assert _rc()._board_run_version({"run_id": "conformance/results/0.1.454"}) == "0.1.454"


def test_an_unparseable_run_id_reads_none_rather_than_guessing():
    assert _rc()._board_run_version({"run_id": "nowhere"}) is None


def test_the_distance_is_counted_in_changelog_headings():
    """How many rule revisions have landed since, not arithmetic on integers.

    The function moved to `versioning` at 0.1.635, where it is SIGNED; the two
    copies it replaced differed by exactly that, and the board's caller takes
    `abs` at the site with its reason written there.
    """
    import versioning
    assert versioning.releases_between("0.1.454", "0.1.456") == 2
    assert versioning.releases_between("0.1.456", "0.1.454") == -2
    assert versioning.releases_between("0.1.454", None) is None
    assert versioning.releases_between("9.9.9", "0.1.456") is None


def test_the_header_keeps_the_word_the_stamp_guard_matches():
    """`skill <version>` is this file's version stamp.

    Dropping it for a better-reading word would redden CI the first time
    anyone regenerated the board — a trap laid by a cosmetic edit.

    ASSERTED ON THE OUTPUT, NOT ON THE SOURCE. This grepped
    `run_conformance.py` for the f-string literal, so extracting the header
    into one `board_header()` — which is the fix for that format having been
    transcribed three times — broke a test whose subject had not changed. A
    test that reads source text is coupled to how the answer is spelled
    rather than to what it is.
    """
    m = _rc()
    stale = m.board_header("0.1.607", "0.1.605")
    assert stale.startswith("# LUMI style conformance · skill 0.1.607")
    assert "newest run 0.1.605" in stale and "releases behind" in stale
    # A fresh board says the stamp and nothing else, which is the other half
    # of what the stamp guard has to find.
    assert m.board_header("0.1.607", "0.1.607") == \
        "# LUMI style conformance · skill 0.1.607"


def test_the_header_says_one_release_in_the_singular():
    """A distance of one is `1 release behind`, and it is easy to lose."""
    m = _rc()
    assert "1 release behind" in m.board_header("0.1.607", "0.1.606")
