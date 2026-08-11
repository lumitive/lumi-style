"""The ledgers guard on synthetic trees — passing and failing both ways."""
import check_repo

GAP_OK = """# Known gaps

## GAP-001 · something broke

- status: open
- opened: 0.1.400
- surface: scripts/x.py
- symptom: it is broken
- check: python3 scripts/x.py
"""

FM_OK = """# Failure modes

## FM-01 · the check that could not fail

- detection: only ever seen passing
- prevention: deliberate-red runs
"""

IDEAS_OK = """# Ideas

## IDEA-1 · do a thing
"""

CHANGELOG_OK = """# Changelog

## 0.1.401 — a release

## 0.1.400 — opened things
"""


def _tree(tmp_path, gaps=GAP_OK, fm=FM_OK, ideas=IDEAS_OK,
          changelog=CHANGELOG_OK, script="x = 1\n"):
    (tmp_path / "Pipeline").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "references").mkdir()
    (tmp_path / "specs").mkdir()
    (tmp_path / "KNOWN_GAPS.md").write_text(gaps)
    (tmp_path / "FAILURE_MODES.md").write_text(fm)
    (tmp_path / "Pipeline/ideas-prd.md").write_text(ideas)
    (tmp_path / "CHANGELOG.md").write_text(changelog)
    (tmp_path / "scripts/x.py").write_text(script)
    (tmp_path / "references/rules.md").write_text("# rules\n")
    return tmp_path


def test_clean_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path))
    assert check_repo.check_ledgers() == []


def test_bad_status_fails(tmp_path, monkeypatch):
    gaps = GAP_OK.replace("- status: open", "- status: probably-fine")
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, gaps=gaps))
    errors = check_repo.check_ledgers()
    assert any("probably-fine" in e for e in errors)


def test_fixed_without_closed_fails(tmp_path, monkeypatch):
    gaps = GAP_OK.replace("- status: open", "- status: fixed")
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, gaps=gaps))
    errors = check_repo.check_ledgers()
    assert any("requires '- closed:'" in e for e in errors)


def test_closed_version_must_exist_and_cite(tmp_path, monkeypatch):
    # closed: names a real release whose entry does NOT cite GAP-001
    gaps = GAP_OK.replace("- status: open",
                          "- status: fixed\n- closed: 0.1.401")
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, gaps=gaps))
    errors = check_repo.check_ledgers()
    assert any("does not cite GAP-001" in e for e in errors)

    # and a closure the CHANGELOG records passes
    changelog = CHANGELOG_OK.replace("a release", "closed GAP-001 here")
    (tmp_path / "b").mkdir()
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path / "b", gaps=gaps, changelog=changelog))
    assert [e for e in check_repo.check_ledgers()
            if "GAP-001" in e and "cite" in e] == []


def test_dangling_citation_fails(tmp_path, monkeypatch):
    changelog = CHANGELOG_OK + "\nAlso cites GAP-009 in passing.\n"
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, changelog=changelog))
    errors = check_repo.check_ledgers()
    assert any("GAP-009" in e and "no ledger defines" in e for e in errors)


def test_todo_citing_gap_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(
        tmp_path, script="# TODO fix GAP-001 someday\n"))
    errors = check_repo.check_ledgers()
    assert any("TODO/FIXME cites a GAP id" in e for e in errors)


def test_fm_missing_prevention_fails(tmp_path, monkeypatch):
    fm = FM_OK.replace("- prevention: deliberate-red runs\n", "")
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, fm=fm))
    errors = check_repo.check_ledgers()
    assert any("FM-01" in e and "prevention" in e for e in errors)


def test_live_repo_is_clean():
    assert check_repo.check_ledgers() == []
