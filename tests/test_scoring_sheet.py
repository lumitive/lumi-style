"""The sheet is in the reviewer's language, and it cannot outlive its rubric.

The last sheet described H1-H6 for two releases after C1-C8 replaced them,
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


def _sheet(tmp_path):
    doc = tmp_path / "deck.en.html"
    doc.write_text("<html></html>", encoding="utf-8")
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import scoring_sheet
    return scoring_sheet.sheet([str(doc)], ["A1"])


def _dimensions():
    return [d for d, _t, _r in ss.items()]


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


def test_a_condition_for_a_withdrawn_item_fails(tmp_path, monkeypatch):
    """A condition is a second list keyed like the wording, and drifts alike."""
    tree = _tree(tmp_path)
    src = (tree / "scripts" / "lib" / "rubric_items.py").read_text(encoding="utf-8")
    src = src.replace("CONDITION = {", 'CONDITION = {\n    ("C9", "①"): "x",', 1)
    (tree / "scripts" / "lib" / "rubric_items.py").write_text(src, encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert any("has a condition" in e for e in check_repo.check_scoring_sheet_parity())


def test_the_score_is_computed_from_the_ticks_not_chosen():
    """The sheet said "score from the ticks" and never said how, so the same
    ticks could produce different numbers on two readings — and an agreement
    study built on that measures the reviewer's mood."""
    assert ss.score(5, 5) == 5
    assert ss.score(4, 5) == 4
    assert ss.score(1, 5) == 1
    assert ss.score(0, 5) == 1


def test_inapplicable_items_leave_the_denominator():
    """A document with no executive summary could tick at most two of C1's five.
    Without the third state that reads as a failure; with it, the dimension is
    scored on what applied."""
    assert ss.score(2, 2) == 5, "two of two applicable items met is a five"


def test_a_dimension_where_nothing_applies_is_not_a_one():
    assert ss.score(0, 0) is None


def test_every_conditional_item_exists_in_the_rubric():
    live = {(d, m) for d, _t, rows in ss.items() for m, _e in rows}
    assert set(ss.CONDITION) <= live


def test_an_item_nobody_can_read_leaves_the_denominator():
    """The fourth state exists because five items were marked unreadable on the
    first real use, and two of them dragged a dimension to 1 that the document
    had not earned. An item nobody can read is a defect in the item."""
    assert ss.score(0, 3, unclear=2) == 1, "one real judgement remains"
    assert ss.score(2, 4, unclear=1) == 3
    assert ss.score(0, 2, unclear=2) is None, "nothing readable left to score on"


def test_the_sheet_asks_the_reviewer_to_compute_nothing(tmp_path):
    """The first version asked for a count and a division whose quotient was not
    the score, and every row came back with satisfied greater than applicable.

    The instrument changed shape at 0.1.489 — the reviewer now gives one rating
    per dimension instead of ticking items — so the assertion is written against
    the property rather than the old layout: no arithmetic is asked for anywhere.
    """
    text = _sheet(tmp_path)
    for arithmetic in ("÷", "满足数", "适用数", "分母"):
        assert arithmetic not in text, f"the sheet asks for {arithmetic}"


def test_every_dimension_offers_the_unreadable_answer(tmp_path):
    """A reviewer who cannot read a question must have somewhere to put that.

    Without it, "I did not understand this" lands in the same place as "the
    document failed", and on the first real use five such answers were recorded
    as failures — two of them dragging a dimension to 1 the document had not
    earned. The escape used to be a fourth column per item; it is now a legal
    answer in place of the rating, and it must appear on EVERY dimension rather
    than once in the header, because that is where the reviewer is when they get
    stuck.
    """
    text = _sheet(tmp_path)
    slots = [ln for ln in text.splitlines() if ln.startswith("**分数**")]
    assert len(slots) == len(_dimensions()), "a dimension has no rating slot"
    for ln in slots:
        assert "看不懂" in ln, f"no unreadable answer offered: {ln}"
        assert "不适用" in ln, f"no inapplicable answer offered: {ln}"


def test_each_dimension_states_its_purpose_and_shows_an_answer(tmp_path):
    """The three things the owner reported missing, asserted on the artifact.

    The parity guard holds the TABLES to the dimension set; this holds the
    RENDERED SHEET to the tables, which is a different failure — a table can be
    complete and the template can still not print it.
    """
    text = _sheet(tmp_path)
    for label in ("**这一条防的是**", "**看哪里**", "**这样答就够**"):
        assert text.count(label) == len(_dimensions()), \
            f"{label} does not appear once per dimension"


def test_the_items_are_a_hint_and_not_a_form(tmp_path):
    """The evidence items still ship — they are what each dimension MEANS — but
    they may not be presented as rows to fill in. Handing a human the machine
    judge's checklist is the mistake 0.1.489 corrected."""
    text = _sheet(tmp_path)
    assert "☐" not in text, "the sheet still offers boxes to tick"
    assert "不用逐条回答" in text, "the items are not marked as optional prompts"
