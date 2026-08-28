"""Seven more check_repo guards proven able to pass AND to fail on synthetic trees.

Wave 3 of the discipline test_check_repo_guards.py states: a guard tested only
against the live repo cannot demonstrate that a rewritten `return []` would be
noticed. Every guard here gets a passing tree and at least one failing tree per
exercised failure mode.

Two guards do not run inside check_repo's own process:

- check_review_scores shells out to ROOT/scripts/ops/review_scores.py, so the
  synthetic tree carries the REAL delegate (copied in), which keeps the actual
  schema logic under test instead of a stub pretending to be it.
- check_brand_lock imports scripts/lib/lock.py, whose own module-level ROOT and
  LOCK are bound at import; the module is already cached (conftest puts
  scripts/ on sys.path), so monkeypatching those two attributes is the whole
  redirection — no fake module, no import machinery.
"""
import hashlib
import json
import pathlib
import shutil

import check_repo
import lock as brand_lock

REAL_SCRIPTS = next(p for p in pathlib.Path(check_repo.__file__).resolve().parents
                    if p.name == "scripts")

DIMS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]


# check_media_only_rules — no class styled only inside a @media block.
# Fully synthetic: the guard reads tokens/*.css and the MEDIA_ONLY_WAIVERS table.

def _media_tree(tmp_path, css):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "lumi-theme.css").write_text(css, encoding="utf-8")
    return tmp_path


BASE_AND_MEDIA = (
    ".title { font-size: 32px; }\n"
    ".note { color: #333333; }\n"
    "@media (max-aspect-ratio: 1/1) {\n"
    "  .title { font-size: 24px; }\n"
    "}\n")


def test_media_only_base_plus_override_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _media_tree(tmp_path, BASE_AND_MEDIA))
    assert check_repo.check_media_only_rules() == []


def test_media_only_class_without_base_fails(tmp_path, monkeypatch):
    css = BASE_AND_MEDIA + "@media (max-aspect-ratio: 1/1) {\n  .ghost { display: none; }\n}\n"
    monkeypatch.setattr(check_repo, "ROOT", _media_tree(tmp_path, css))
    errors = check_repo.check_media_only_rules()
    assert len(errors) == 1
    assert ".ghost" in errors[0] and "only inside a @media block" in errors[0]


def test_media_only_waived_class_passes(tmp_path, monkeypatch):
    css = BASE_AND_MEDIA + "@media (max-aspect-ratio: 1/1) {\n  .ghost { display: none; }\n}\n"
    monkeypatch.setattr(check_repo, "ROOT", _media_tree(tmp_path, css))
    monkeypatch.setattr(check_repo, "MEDIA_ONLY_WAIVERS",
                        {"ghost": "synthetic geometry switch for this test"})
    assert check_repo.check_media_only_rules() == []


def test_media_only_waiver_outliving_its_cause_fails(tmp_path, monkeypatch):
    # .title has a base rendering, .phantom is styled nowhere: both waivers are stale.
    monkeypatch.setattr(check_repo, "ROOT", _media_tree(tmp_path, BASE_AND_MEDIA))
    monkeypatch.setattr(check_repo, "MEDIA_ONLY_WAIVERS",
                        {"title": "stale", "phantom": "orphaned"})
    errors = check_repo.check_media_only_rules()
    assert any(".title" in e and "delete the waiver" in e for e in errors)
    assert any(".phantom" in e and "styles at all" in e for e in errors)


def test_media_only_missing_css_is_reported_not_vacuous(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)  # no tokens/ at all
    errors = check_repo.check_media_only_rules()
    assert len(errors) == 1 and "pass vacuously" in errors[0]


# check_layout_parity — tokens/'s .body.* layouts and check_design.py's LAYOUTS
# are one list. Fully synthetic: the checker side is parsed via AST, never run,
# so a two-line check_design.py stub carrying only LAYOUTS is a faithful fixture.

def _layout_tree(tmp_path, css=None, design_src='LAYOUTS = {"hero", "split"}\n'):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    if css is None:
        # .body.no-lede is on the guard's exclusion list and must not be flagged.
        css = ".body.hero { padding: 0; }\n.body.split { padding: 0; }\n.body.no-lede { }\n"
    (tokens / "lumi-layouts.css").write_text(css, encoding="utf-8")
    scripts = tmp_path / "scripts" / "check"
    scripts.mkdir(parents=True)
    (scripts / "check_design.py").write_text(design_src, encoding="utf-8")
    return tmp_path


def test_layout_parity_matching_lists_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _layout_tree(tmp_path))
    assert check_repo.check_layout_parity() == []


def test_layout_parity_shipped_but_ungraded_fails(tmp_path, monkeypatch):
    tree = _layout_tree(tmp_path, css=".body.hero { }\n.body.split { }\n.body.extra { }\n")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_layout_parity()
    assert len(errors) == 1
    assert ".body.extra" in errors[0] and "does not grade" in errors[0]


def test_layout_parity_graded_but_unshipped_fails(tmp_path, monkeypatch):
    tree = _layout_tree(tmp_path, design_src='LAYOUTS = {"hero", "split", "phantom"}\n')
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_layout_parity()
    assert len(errors) == 1
    assert "'phantom'" in errors[0] and "no tokens/" in errors[0]


def test_layout_parity_missing_layouts_table_fails(tmp_path, monkeypatch):
    tree = _layout_tree(tmp_path, design_src="GRADES = None\n")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_layout_parity()
    assert len(errors) == 1 and "no longer defines LAYOUTS" in errors[0]


# Shared fixtures for the three prose-parity guards. Both sides are fully
# synthetic: writing-rules.md is written in the exact shapes the guards parse
# (section 2's [zh-output] line, qualified ban, [en-output] groups; section 4
# rule 6's marker bullets), and check_prose.py is a four-assignment stub —
# legitimate because every guard reads it via ast.parse and never executes it.

EN_GROUPS = (
    "1. **Significance inflation** — stands as · a testament to.\n"
    '2. **Filler, with the fix** — "in order to" → "to".')


def _write_rules(tmp_path, en_groups=EN_GROUPS,
                 zh_list="值得注意的是 · 综上所述",
                 markers=("source", "as of", "n="), declarations=()):
    """`declarations` marks bullets the way the real rule 6 marks them.

    The guard reads the word *declaration* off the rules file rather than off
    a constant in `check_design.py` — an anchor a guarded file owns is not an
    anchor, and the first version could be emptied into a vacuous pass.
    """
    refs = tmp_path / "references"
    refs.mkdir(exist_ok=True)
    bullets = "\n".join(
        f"   - `{m}` — a declaration" if m in declarations
        else f"   - `{m}` — what it marks" for m in markers)
    (refs / "writing-rules.md").write_text(
        "## 2 · Banned AI-tell phrases (hard block)\n\n"
        f"**[zh-output]** rule data: {zh_list}.\n\n"
        "Qualified ban (rule data): 赋能 is allowed **only** in the fixed\n"
        "collocations the script label names.\n\n"
        "**[en-output] — hard block.** Grouped by tell.\n\n"
        f"{en_groups}\n\n"
        "Attribution: adapted.\n\n"
        "## 3 · Punctuation\n\nNone.\n\n"
        "## 4 · Number discipline\n\n"
        "6. **What counts as a source marker, and how far it may sit.**\n"
        "   The markers are literal:\n\n"
        f"{bullets}\n\n"
        "   **The window is the page.**\n\n"
        "## 5 · Voice\n",
        encoding="utf-8")
    return tmp_path


DEFAULT_BANNED = [("pat-a", "stands as"), ("pat-b", "a testament to")]
DEFAULT_ZH = [("值得注意的是", "值得注意的是"), ("综上所述", "综上所述"),
              ("赋能", "赋能 outside the two fixed collocations")]


def _write_prose_script(tmp_path, banned=None, waived=None, zh=None, markers=None):
    scripts = tmp_path / "scripts" / "check"
    scripts.mkdir(parents=True, exist_ok=True)
    banned = DEFAULT_BANNED if banned is None else banned
    waived = {"in order to": "left to the reviewer"} if waived is None else waived
    zh = DEFAULT_ZH if zh is None else zh
    markers = ["source", "as of", "n="] if markers is None else markers
    (scripts / "check_prose.py").write_text(
        f"BANNED = {banned!r}\n"
        f"NOT_MECHANIZED = {waived!r}\n"
        f"BANNED_ZH = {zh!r}\n"
        f"SOURCE_MARKERS = {markers!r}\n",
        encoding="utf-8")
    return tmp_path


# check_ban_list_parity — section 2 [en-output] against BANNED / NOT_MECHANIZED.

def test_ban_list_parity_matching_pair_passes(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_ban_list_parity() == []


def test_ban_list_parity_rule_without_machine_decision_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path, en_groups=EN_GROUPS + "\n3. **AI vocabulary** — delve.")
    _write_prose_script(tmp_path)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_ban_list_parity()
    assert len(errors) == 1
    assert "'delve'" in errors[0] and "neither" in errors[0]


def test_ban_list_parity_script_inventing_a_ban_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path, banned=[*DEFAULT_BANNED, ("pat-c", "leverage")])
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_ban_list_parity()
    assert len(errors) == 1
    assert "'leverage'" in errors[0] and "the rules are the source" in errors[0]


def test_ban_list_parity_matched_and_waived_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path, waived={"in order to": "reviewer",
                                          "stands as": "also matched above"})
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_ban_list_parity()
    assert any("'stands as'" in e and "both matched and waived" in e for e in errors)


# check_zh_ban_list_parity — the [zh-output] list plus the qualified ban against
# BANNED_ZH labels, matched by prefix so a label may carry its exception.

def test_zh_ban_list_parity_matching_pair_passes(tmp_path, monkeypatch):
    # The qualified 赋能 is covered by a label that STARTS with it and carries
    # its exception — the exact shape the prefix rule exists for.
    _write_rules(tmp_path)
    _write_prose_script(tmp_path)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_zh_ban_list_parity() == []


def test_zh_ban_list_parity_rule_unmatched_by_script_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path, zh_list="值得注意的是 · 综上所述 · 不可否认")
    _write_prose_script(tmp_path)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_zh_ban_list_parity()
    assert len(errors) == 1
    assert "不可否认" in errors[0] and "BANNED_ZH does not match" in errors[0]


def test_zh_ban_list_parity_script_inventing_a_ban_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path, zh=[*DEFAULT_ZH, ("众所周知", "众所周知")])
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_zh_ban_list_parity()
    assert len(errors) == 1
    assert "众所周知" in errors[0] and "the rules are the source" in errors[0]


# check_source_marker_parity — section 4 rule 6's bullets against SOURCE_MARKERS.

def test_source_marker_parity_matching_pair_passes(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_source_marker_parity() == []


def test_source_marker_parity_rule_marker_missing_from_script_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path, markers=("source", "as of", "n=", "derived from"))
    _write_prose_script(tmp_path)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert len(errors) == 1
    assert "'derived from'" in errors[0] and "does not match" in errors[0]


def test_source_marker_parity_script_inventing_a_marker_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path, markers=["source", "as of", "n=", "mock"])
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert len(errors) == 1
    assert "'mock'" in errors[0] and "the rules are the source" in errors[0]


# check_review_scores — delegated to review_scores.py over subprocess, so the
# synthetic tree carries the real delegate script; its own ROOT resolves
# relative to its file, which is why the copy lands in <tree>/scripts/.

def _scores_tree(tmp_path, overrides=None):
    scripts = tmp_path / "scripts"
    (scripts / "ops").mkdir(parents=True)
    shutil.copyfile(REAL_SCRIPTS / "ops" / "review_scores.py",
                    scripts / "ops" / "review_scores.py")
    # review_scores.py imports the genre vocabulary from the shared registry
    # (0.1.455 — five scripts had five copies of it), so the delegate needs its
    # sibling here or it exits on the import and the guard reports "unknown
    # failure" for a reason that has nothing to do with the store.
    (scripts / "lib").mkdir(parents=True)
    shutil.copyfile(REAL_SCRIPTS / "lib" / "deliverable_registry.py",
                    scripts / "lib" / "deliverable_registry.py")
    # and the corpus reader (0.1.534), for the same reason
    shutil.copyfile(REAL_SCRIPTS / "lib" / "corpus.py", scripts / "lib" / "corpus.py")
    # and the store resolver (0.1.571): review_scores.py asks it where the
    # score store lives, and without it here the delegate exits on the import.
    shutil.copyfile(REAL_SCRIPTS / "lib" / "state_dir.py",
                    scripts / "lib" / "state_dir.py")
    # and the version reader (0.1.635): the release list it validates against
    # comes from `versioning.releases`, not from a regex of its own.
    shutil.copyfile(REAL_SCRIPTS / "lib" / "versioning.py",
                    scripts / "lib" / "versioning.py")
    (tmp_path / "CHANGELOG.md").write_text("## 0.1.1\n\n- first.\n", encoding="utf-8")
    record = {"release": "0.1.1", "genre": "sales", "corpus_id": "A1",
              "self": dict.fromkeys(DIMS, 4), "reader": dict.fromkeys(DIMS, 4),
              "outcome": "no-change"}
    record.update(overrides or {})
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "scores.json").write_text(json.dumps(
        {"dimensions": DIMS,
         "outcomes": ["rule-change", "anchor-revision", "no-change"],
         "reviews": [record]}), encoding="utf-8")
    return tmp_path


def test_review_scores_valid_store_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _scores_tree(tmp_path))
    assert check_repo.check_review_scores() == []


def test_review_scores_unknown_key_fails(tmp_path, monkeypatch):
    # The engagement-fact defence: a record key the schema does not define.
    monkeypatch.setattr(check_repo, "ROOT",
                        _scores_tree(tmp_path, overrides={"client": "ACME"}))
    errors = check_repo.check_review_scores()
    assert len(errors) == 1
    assert "reviews[0]" in errors[0] and "schema does not define" in errors[0]


def test_review_scores_self_five_without_reader_fails(tmp_path, monkeypatch):
    tree = _scores_tree(tmp_path, overrides={
        "self": {**dict.fromkeys(DIMS, 4), "C1": 5},
        "reader": dict.fromkeys(DIMS)})
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_review_scores()
    assert any("self-scored 5 on C1" in e for e in errors)


# check_brand_lock — every locked file hashes to what LOCKED.json records.

def _lock_tree(tmp_path, monkeypatch, with_lock_file=True):
    brand = tmp_path / "assets" / "brand"
    brand.mkdir(parents=True)
    mark = brand / "mark.svg"
    mark.write_bytes(b"<svg>the published mark</svg>")
    if with_lock_file:
        (brand / "LOCKED.json").write_text(json.dumps(
            {"component": "wordmark", "locked_at": "0.1.1",
             "why": "synthetic lock for this test",
             "files": {"assets/brand/mark.svg":
                       hashlib.sha256(mark.read_bytes()).hexdigest()}}),
            encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(brand_lock, "ROOT", tmp_path)
    monkeypatch.setattr(brand_lock, "LOCK", brand / "LOCKED.json")
    return mark


def test_brand_lock_matching_hashes_pass(tmp_path, monkeypatch):
    _lock_tree(tmp_path, monkeypatch)
    assert check_repo.check_brand_lock() == []


def test_brand_lock_changed_contents_fail(tmp_path, monkeypatch):
    mark = _lock_tree(tmp_path, monkeypatch)
    mark.write_bytes(b"<svg>silently edited</svg>")
    errors = check_repo.check_brand_lock()
    assert len(errors) == 1
    assert "LOCKED" in errors[0] and "contents changed" in errors[0]


def test_brand_lock_deleted_file_fails(tmp_path, monkeypatch):
    mark = _lock_tree(tmp_path, monkeypatch)
    mark.unlink()
    errors = check_repo.check_brand_lock()
    assert len(errors) == 1 and "has been deleted" in errors[0]


def test_brand_lock_missing_lock_file_fails(tmp_path, monkeypatch):
    _lock_tree(tmp_path, monkeypatch, with_lock_file=False)
    errors = check_repo.check_brand_lock()
    assert len(errors) == 1 and "missing" in errors[0]


# --- the D6 half of source-marker parity ------------------------------------
# It had no guard at all: `check_design`'s D6_PROVENANCE was English-only while
# `check_prose`'s SOURCE_MARKERS had carried Chinese for releases, so a correct
# Chinese colophon was reported as missing its provenance on every page.


def _write_design_script(root, provenance=("source", "based on"), labels=()):
    """The stub models the real file, including the constant it must declare.

    `labels` defaults to empty because these trees test the Chinese half: an
    empty declaration-label set makes no assertions and leaves the CJK
    comparison the only thing under test. The guard still fails a tree whose
    check_design.py declares no D6_DECLARATION_LABELS at all — dropping the
    constant must not be a way past it, which is the whole point of naming it.
    """
    d = root / "scripts" / "check"
    d.mkdir(parents=True, exist_ok=True)
    (d / "check_design.py").write_text(
        "D6_PROVENANCE = " + repr(tuple(provenance)) + "\n"
        "D6_DECLARATION_LABELS = " + repr(tuple(labels)) + "\n",
        encoding="utf-8")


_ZH_MARKERS = ("source", "as of", "n=", "\u6765\u6e90")


def test_a_design_vocabulary_blind_to_chinese_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path, markers=_ZH_MARKERS)
    _write_prose_script(tmp_path, markers=list(_ZH_MARKERS))
    _write_design_script(tmp_path)          # English only
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("recognises none" in e for e in errors), errors


def test_both_vocabularies_reading_chinese_passes(tmp_path, monkeypatch):
    # `declarations` names one bullet: the guard now fails a rules file that
    # marks none, so a tree exercising only the CJK half still has to say
    # which marker is a declaration and honour it.
    _write_rules(tmp_path, markers=_ZH_MARKERS, declarations=("source",))
    _write_prose_script(tmp_path, markers=list(_ZH_MARKERS))
    _write_design_script(tmp_path, ("source", "based on", "\u6765\u6e90"),
                         labels=("source",))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_source_marker_parity() == []


def test_a_design_checker_with_no_vocabulary_at_all_fails(tmp_path, monkeypatch):
    _write_rules(tmp_path)
    _write_prose_script(tmp_path)
    (tmp_path / "scripts" / "check" / "check_design.py").write_text(
        "# no D6_PROVENANCE here\n", encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("D6_PROVENANCE" in e for e in errors), errors


def test_rules_marking_no_declaration_at_all_fails(tmp_path, monkeypatch):
    """Losing the marking loses the check, so losing it is a failure.

    The comparison is a subset test against the declaration set. An empty set
    satisfies it vacuously, which is exactly how the first version — anchored
    on a constant in check_design.py — could be switched off by emptying that
    constant, with the FM-13 it repairs fully reinstated and the guard green.
    """
    _write_rules(tmp_path, markers=("source",))
    _write_prose_script(tmp_path, markers=["source"])
    _write_design_script(tmp_path, ("source",))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("marks no bullet as a declaration" in e for e in errors), errors


def test_a_declaration_label_d6_will_not_accept_fails(tmp_path, monkeypatch):
    """The measured defect: a colophon saying what its numbers ARE, failed.

    writing-rules §4 rule 6 rules on `illustrative` and the three labels beside
    it — "declarations rather than sources, and they satisfy the same
    obligation" — and D6 carried none of them, so "all figures illustrative; no
    engagement data" was reported as missing provenance on every page of a
    twenty-page deck.
    """
    _write_rules(tmp_path, markers=("source", "illustrative"),
                 declarations=("illustrative",))
    _write_prose_script(tmp_path, markers=["source", "illustrative"])
    _write_design_script(tmp_path, ("source",), labels=("illustrative",))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("D6_PROVENANCE does not accept it" in e for e in errors), errors


def test_a_constant_that_disagrees_with_the_rules_fails(tmp_path, monkeypatch):
    """The rules are the source; the constant is documentation held to them."""
    _write_rules(tmp_path, markers=("source", "illustrative"),
                 declarations=("illustrative",))
    _write_prose_script(tmp_path, markers=["source", "illustrative"])
    _write_design_script(tmp_path, ("source", "illustrative", "indicative"),
                         labels=("illustrative", "indicative"))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("the rules are the source, not the script" in e
               for e in errors), errors


def test_an_emptied_constant_no_longer_buys_a_pass(tmp_path, monkeypatch):
    """The bypass a review found, held shut.

    Emptying `D6_DECLARATION_LABELS` and stripping the labels from
    D6_PROVENANCE used to satisfy every assertion vacuously.
    """
    _write_rules(tmp_path, markers=("source", "illustrative"),
                 declarations=("illustrative",))
    _write_prose_script(tmp_path, markers=["source", "illustrative"])
    _write_design_script(tmp_path, ("source",), labels=())
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("D6_PROVENANCE does not accept it" in e for e in errors), errors


def test_a_tree_declaring_no_labels_at_all_fails(tmp_path, monkeypatch):
    """Deleting the constant may not be the way past the guard either."""
    _write_rules(tmp_path, markers=("source", "illustrative"),
                 declarations=("illustrative",))
    _write_prose_script(tmp_path, markers=["source", "illustrative"])
    d = tmp_path / "scripts" / "check"
    d.mkdir(parents=True, exist_ok=True)
    (d / "check_design.py").write_text(
        'D6_PROVENANCE = ("source", "illustrative")\n', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_source_marker_parity()
    assert any("declares no D6_DECLARATION_LABELS" in e for e in errors), errors
