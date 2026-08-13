"""The two metric-claim guards, proven able to pass AND to fail.

Same discipline as tests/test_check_repo_guards.py: a guard only ever seen
passing is FM-01. Both guards here were born red — they found nine live claims
on the tree that created them — but "it went red once" is not the same as "it
goes red for the right reason", which is what these pin.

Both guards read the checker with `ast` and shell out to `git ls-files`, so a
synthetic tree has to be a real git repository with a real (tiny) checker in it.
That is the whole cost of not importing the script under test.
"""
import json
import pathlib
import shutil
import subprocess

import check_repo


def _git_tree(tmp_path, files: dict[str, str]):
    """A committed git tree, because the guards enumerate with `git ls-files`."""
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


# A checker whose row table is the authority: D1 and D2 report, D3 gates.
CHECKER = '''
def verdict_rows(r):
    rows = []
    rows.append(("D1_contrast", 0, "reported", True, False))
    rows.append(("D2_type_scale", 0, "reported", True, False))
    rows.append(("D3_footer", 0, "=0 (gates)", True, False))
    return rows
'''


def _tree(tmp_path, prose: str, checker: str = CHECKER):
    return _git_tree(tmp_path, {
        "scripts/check/check_design.py": checker,
        "scripts/check/check_prose.py": "rows = []\n",
        "AGENTS.md": prose,
    })


# ── metric id ranges ─────────────────────────────────────────────────────────

def test_a_range_matching_the_checker_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "The script reports D1-D3 on a file.\n"))
    assert check_repo.check_metric_id_ranges() == []


def test_a_range_stopping_short_fails_naming_both_numbers(tmp_path, monkeypatch):
    # The shipped defect: five files said D1-D17 while D18 and D19 shipped rows.
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "The script reports D1-D2 on a file.\n"))
    errors = check_repo.check_metric_id_ranges()
    assert len(errors) == 1
    assert "AGENTS.md:1" in errors[0]
    assert "D1-D2" in errors[0] and "D3" in errors[0]


def test_an_en_dash_range_is_read_too(tmp_path, monkeypatch):
    # Prose uses en dashes; only the code comments use hyphens. Missing one
    # form would have left half the live instances invisible.
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "The script reports D1–D2 here.\n"))
    assert check_repo.check_metric_id_ranges()


def test_a_subset_range_is_deliberately_not_checked(tmp_path, monkeypatch):
    # "M8-M11" names a subset on purpose. Only a range written from 1 claims
    # the whole family, and only that claim is decidable.
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "The AI-flavor half is D2-D3 only.\n"))
    assert check_repo.check_metric_id_ranges() == []


def test_a_waived_quotation_is_not_counted(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, 'It once claimed "D1-D2 gate", wrongly.\n'))
    monkeypatch.setitem(check_repo.METRIC_RANGE_WAIVERS,
                        ("AGENTS.md", "D1-D2"), "quotes a corrected error")
    assert check_repo.check_metric_id_ranges() == []


def test_a_checker_that_stops_parsing_is_reported_not_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "D1-D3\n", checker="def broken(:\n"))
    errors = check_repo.check_metric_id_ranges()
    assert errors and "could not read the metric vocabularies" in errors[0]


# ── gating claims ────────────────────────────────────────────────────────────

def test_a_claim_naming_the_gating_set_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "Only D3 gates here.\n"))
    monkeypatch.setattr(check_repo, "GATING_CLAIM_SITES",
                        {"AGENTS.md": r"Only ((?:D\d+/?)+) gates"})
    assert check_repo.check_gating_claims() == []


def test_a_claim_missing_a_gate_fails_naming_both_sets(tmp_path, monkeypatch):
    # The shipped defect, in miniature: a gate was added and the sentence was not.
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "Only D1 gates here.\n"))
    monkeypatch.setattr(check_repo, "GATING_CLAIM_SITES",
                        {"AGENTS.md": r"Only ((?:D\d+/?)+) gates"})
    errors = check_repo.check_gating_claims()
    assert len(errors) == 1
    assert "names D1" in errors[0] and "gates on D3" in errors[0]


def test_a_reworded_claim_fails_rather_than_silently_passing(tmp_path, monkeypatch):
    # THE POINT OF THE DECLARED TABLE. A pattern that stops matching must be an
    # error: if a rewrite could retire the check on its own sentence, the guard
    # protects only sentences nobody edits.
    monkeypatch.setattr(check_repo, "ROOT",
                        _tree(tmp_path, "The gating set moved elsewhere.\n"))
    monkeypatch.setattr(check_repo, "GATING_CLAIM_SITES",
                        {"AGENTS.md": r"Only ((?:D\d+/?)+) gates"})
    errors = check_repo.check_gating_claims()
    assert len(errors) == 1
    assert "no longer matches its pattern" in errors[0]
    assert "do not drop the entry" in errors[0]


def test_a_declared_site_that_vanished_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, "prose\n"))
    monkeypatch.setattr(check_repo, "GATING_CLAIM_SITES",
                        {"GONE.md": r"Only ((?:D\d+/?)+) gates"})
    errors = check_repo.check_gating_claims()
    assert errors and "does not exist" in errors[0]


# ── genre vocabulary ─────────────────────────────────────────────────────────
# Five scripts carried five different genre lists. The consequence was not
# cosmetic: a consulting deliverable could be scaffolded, layout-graded and
# review-scored, while `check_prose.py --genre consulting` refused the value,
# so its prose had to be graded under a genre it is not.

_GENRE_FILES = ("evals/thresholds.json",
                "scripts/lib/deliverable_registry.py",
                "scripts/check/check_prose.py",
                "scripts/check/inspect_layout.py",
                "scripts/ops/new_deck.py",
                "scripts/ops/review_scores.py",
                "scripts/ops/export_pdf.py",
                "scripts/ops/eval_corpus.py")


def _genre_tree(tmp_path, **overwrite):
    """The live files, with named ones replaced by a one-line stand-in."""
    for name in _GENRE_FILES:
        dst = tmp_path / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pathlib.Path(check_repo.ROOT) / name, dst)
    for name, body in overwrite.items():
        (tmp_path / name.replace(".", "/", name.count(".") - 1)).write_text(
            body, encoding="utf-8")
    return tmp_path


def test_the_live_tree_has_one_genre_vocabulary(monkeypatch, tmp_path):
    monkeypatch.setattr(check_repo, "ROOT", _genre_tree(tmp_path))
    assert check_repo.check_genre_vocabulary() == []


def test_a_second_genre_list_is_named_and_refused(monkeypatch, tmp_path):
    tree = _genre_tree(tmp_path)
    (tree / "scripts/ops/review_scores.py").write_text(
        'GENRES = ("sales", "internal")\n', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert len(errors) == 1
    assert "review_scores.py declares its own GENRES" in errors[0]


def test_a_genre_with_no_visual_target_is_named(monkeypatch, tmp_path):
    # The live failure mode: inspect_layout grades an unknown genre NOT
    # MEASURED and D16 goes quiet on it, which reads as agreement.
    tree = _genre_tree(tmp_path)
    (tree / "scripts/check/inspect_layout.py").write_text(
        'VISUAL_SHARE_TARGET = {"sales": 50}\n', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert errors
    assert any("no visual-share target for 'training'" in e for e in errors)


def test_a_scaffold_for_an_unknown_genre_is_refused(monkeypatch, tmp_path):
    tree = _genre_tree(tmp_path)
    (tree / "scripts/ops/new_deck.py").write_text(
        'SCAFFOLDED = ("sales", "webinar")\n', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert len(errors) == 1 and "'webinar'" in errors[0]


def test_a_scaffold_subset_is_allowed(monkeypatch, tmp_path):
    # SCAFFOLDED is deliberately a subset — `marketing` has no skeleton of its
    # own — so a subset must not be an error or the guard forbids the truth.
    tree = _genre_tree(tmp_path)
    (tree / "scripts/ops/new_deck.py").write_text(
        'SCAFFOLDED = ("sales",)\n', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert check_repo.check_genre_vocabulary() == []


def test_a_missing_authority_is_reported_not_skipped(monkeypatch, tmp_path):
    tree = _genre_tree(tmp_path)
    (tree / "scripts/lib/deliverable_registry.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert errors and "no authority" in errors[0]


def test_an_indirect_binding_to_a_private_list_is_refused(monkeypatch, tmp_path):
    # `GENRES = _G` is not a literal, so it used to return the same answer as
    # "this file declares no GENRES" — and the caller read that as compliance.
    # The guard was blessing the exact indirection it exists to catch.
    tree = _genre_tree(tmp_path)
    (tree / "scripts/ops/review_scores.py").write_text(
        '_G = ("sales",)\nGENRES = _G\n', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert errors and "cannot verify" in errors[0] and "_G" in errors[0]


def test_importing_the_registry_under_an_alias_is_allowed(monkeypatch, tmp_path):
    # The legitimate shape must stay legitimate, or the guard forbids the fix.
    tree = _genre_tree(tmp_path)
    (tree / "scripts/ops/review_scores.py").write_text(
        "from deliverable_registry import GENRES as registry_genres\n"
        "GENRES = registry_genres\n", encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert check_repo.check_genre_vocabulary() == []


def test_a_genre_with_no_dash_decision_is_named(monkeypatch, tmp_path):
    # M9 is skipped for it and PRINTED as "(exempt for internal documents)",
    # which is false for any other genre.
    tree = _genre_tree(tmp_path)
    src = (tree / "scripts/check/check_prose.py").read_text(encoding="utf-8")
    (tree / "scripts/check/check_prose.py").write_text(
        src.replace('DASH_BANNED = ("sales", "marketing", "consulting", "training")',
                    'DASH_BANNED = ("sales",)'), encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert any("no dash decision" in e and "training" in e for e in errors)


def test_a_threshold_table_missing_a_genre_is_named(monkeypatch, tmp_path):
    tree = _genre_tree(tmp_path)
    table = json.loads((tree / "evals/thresholds.json").read_text(encoding="utf-8"))
    for spec in table["metrics"].values():
        spec["genres"].pop("consulting", None)
    (tree / "evals/thresholds.json").write_text(json.dumps(table), encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_genre_vocabulary()
    assert any("no entry for genre 'consulting'" in e for e in errors)
