"""The sheet is in the reviewer's language, and it cannot outlive its rubric.

The last sheet described H1-H6 for two releases after C1-C7 replaced them,
because nothing held it to the rubric. The wording table is the price of writing
in the reviewer's language; the parity guard is the price of the wording table.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_repo  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import rubric_items as ss  # noqa: E402


def test_the_live_wording_matches_the_live_rubric():
    assert check_repo.check_scoring_sheet_parity() == []


def _tree(tmp_path, drop=None, add=None):
    """A synthetic repo: the guard loads rubric_items.py off disk by path, so a
    monkeypatched module object is invisible to it — which is deliberate, since
    check_repo may not import from scripts/ops (the emergency closure would then
    run the pull request's own copy)."""
    (tmp_path / "SKILL.md").write_text('version: "0.0.1"\n', encoding="utf-8")
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "eval-rubric.md").write_text(
        ROOT.joinpath("references", "eval-rubric.md").read_text(encoding="utf-8"),
        encoding="utf-8")
    ops = tmp_path / "scripts" / "lib"
    ops.mkdir(parents=True)
    src = ROOT.joinpath("scripts", "lib", "rubric_items.py").read_text(encoding="utf-8")
    if drop:
        src = src.replace(f'    ("{drop[0]}", "{drop[1]}"): ', '    ("ZZ", "zz"): ', 1)
    if add:
        src = src.replace("WORDING = {",
                          f'WORDING = {{\n    ("{add[0]}", "{add[1]}"): "x",', 1)
    (ops / "rubric_items.py").write_text(src, encoding="utf-8")
    return tmp_path


def test_a_missing_wording_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, drop=("C3", "①")))
    assert any("has no wording" in e for e in check_repo.check_scoring_sheet_parity())


def test_a_wording_for_an_item_that_is_gone_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, add=("C9", "①")))
    assert any("no longer exists" in e for e in check_repo.check_scoring_sheet_parity())


def test_the_sheet_carries_no_mechanical_number(tmp_path):
    """A reader who has seen the machine's answer is no longer an independent
    measurement, and the agreement study exists only because that independence
    does."""
    doc = tmp_path / "deck.en.html"
    doc.write_text("<html></html>", encoding="utf-8")
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import scoring_sheet
    text = scoring_sheet.sheet([str(doc)], ["A1"])
    for forbidden in ("%", "M1_", "D12", "verdict", "FAIL"):
        assert forbidden not in text, f"the sheet leaked {forbidden!r}"


def test_every_item_reaches_the_sheet_in_the_reviewers_language(tmp_path):
    doc = tmp_path / "deck.en.html"
    doc.write_text("<html></html>", encoding="utf-8")
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import scoring_sheet
    text = scoring_sheet.sheet([str(doc)], ["A1"])
    for (_did, _marker), wording in ss.WORDING.items():
        assert wording in text, f"missing from the sheet: {wording[:30]}"
