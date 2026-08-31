"""The credential table stays one table, and the rest of the 2026-08-20 audit.

The strip-tags half moved into `evals/single-source.json` at 0.1.634 and is
tested in test_one_home.py; `check_secret_patterns_parity` stayed a guard of
its own, because its table is computed at runtime from `secret_patterns.MARKERS`
rather than declared, so a register entry could only restate it. It ships with
the tree that fails it, because a guard only ever seen passing is FM-01.
"""
import pathlib

import check_repo
import markup
import secret_patterns


def _tree(tmp_path, files):
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp_path


IMPORTERS = {
    "scripts/check/check_repo.py": "import secret_patterns\n",
    "scripts/check/check_privacy.py": "import secret_patterns\n",
}


def test_secret_patterns_parity_passes_a_clean_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        **IMPORTERS, "scripts/ops/tool.py": 'X = re.compile(r"\\d+")\n'}))
    assert check_repo.check_secret_patterns_parity() == []


def test_a_private_credential_regex_fails(tmp_path, monkeypatch):
    private = 'BAD = re.compile(r"\\b' + "AK" + "IA" + '[0-9A-Z]{16}\\b")\n'
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        **IMPORTERS, "scripts/check/other.py": private}))
    errors = check_repo.check_secret_patterns_parity()
    assert len(errors) == 1 and "other.py:1" in errors[0]
    assert "second table" in errors[0]


def test_an_importer_that_stops_importing_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "scripts/check/check_repo.py": "import secret_patterns\n",
        "scripts/check/check_privacy.py": "CREDENTIALS = []\n"}))
    errors = check_repo.check_secret_patterns_parity()
    assert errors and "check_privacy.py does not import" in errors[0]


def test_the_shared_table_is_a_superset_of_both_old_tables():
    """The two old tables' distinguishing shapes, both caught now."""
    names = {n for n, _ in secret_patterns.PATTERNS}
    assert {"GitHub fine-grained token", "Slack token", "Google API key",
            "JSON web token", "AWS access key id"} <= names
    hit = {n for n, p in secret_patterns.PATTERNS
           if p.search("token = github_pat_" + "b2" * 12)}
    assert "GitHub fine-grained token" in hit
    hit = {n for n, p in secret_patterns.PATTERNS if p.search("xoxb-" + "a1" * 8)}
    assert "Slack token" in hit


def test_markup_helpers():
    assert markup.strip_tags("<b>a</b>&amp;<i>b</i>") == " a & b "
    assert markup.strip_tags("<b>a</b><i>b</i>", sep="") == "ab"
    assert markup.visible_text("  <p>one\n  two</p> ") == "one two"
    assert markup.join_cjk("每个 Agent 都会 这样") == "每个 Agent 都会这样"
    assert markup.join_cjk("a b") == "a b"


def test_the_live_tree_carries_no_copy():
    assert check_repo.check_secret_patterns_parity() == []
    assert pathlib.Path(check_repo.ROOT, "scripts/lib/secret_patterns.py").exists()


# 0.1.526 — the repo secrets guard runs the operator's OR-8 lists too.
import subprocess  # noqa: E402

import check_privacy  # noqa: E402


def _git_tree(tmp_path, files):
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _tree(tmp_path, files)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_a_declared_term_in_a_tracked_file_fails_the_secrets_guard(tmp_path, monkeypatch):
    terms = tmp_path / "terms"
    terms.mkdir()
    (terms / "x.terms.txt").write_text("Acme Widgets\n", encoding="utf-8")
    monkeypatch.setattr(check_privacy, "TERMS_DIR", terms)
    monkeypatch.setattr(check_repo, "ROOT", _git_tree(tmp_path / "repo", {
        "notes.md": "we built this for Acme Widgets last year\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1 and "notes.md:1" in errors[0]
    assert "Acme" not in errors[0]  # never echoed


def test_no_lists_means_the_term_half_simply_does_not_run(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "TERMS_DIR", tmp_path / "absent")
    monkeypatch.setattr(check_repo, "ROOT", _git_tree(tmp_path / "repo", {
        "notes.md": "we built this for Acme Widgets last year\n"}))
    assert check_repo.check_secrets() == []


# 0.1.527 — a claim of absence in the rubric must cite a ledger entry.

def test_rubric_unbuilt_claim_without_a_ledger_id_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "references/eval-rubric.md":
            "| ④ layout | **half held**: there is no font-count check — mechanisable, not built |\n"}))
    errors = check_repo.check_rubric_unbuilt_claims()
    assert len(errors) == 1 and "eval-rubric.md:1" in errors[0]


def test_rubric_unbuilt_claim_with_a_ledger_id_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "references/eval-rubric.md":
            "| ② terms | a terminology checker is not built — IDEA-12 tracks it |\n"}))
    assert check_repo.check_rubric_unbuilt_claims() == []


def test_the_live_rubric_carries_no_unheld_claim_of_absence():
    assert check_repo.check_rubric_unbuilt_claims() == []


# 0.1.530 — the prompt tier is held to the storylines, the ban list and two
# load-bearing sentences.

def _prompt_tree(tmp_path, body):
    return _tree(tmp_path, {"prompts/lumi-style-core.md": body})


def _full_prompt_text():
    import check_prose
    import deliverable_registry as d
    names = " ".join(f"`{n}`" for n in d.STORYLINES)
    bans = "; ".join(p for _, p in check_prose.BANNED)
    # BUILT FROM `PROMPT_MUST_CARRY`, not retyped beside it. Two sentences were
    # written here as literals, so adding a third to the constant failed this
    # test rather than the prompt — the guard was right and its own fixture was
    # the thing out of date.
    carried = "\n".join(sentence for sentence, _why
                        in check_repo.PROMPT_MUST_CARRY)
    return f"{names}\n{bans}\n{carried}\n"


def test_prompt_parity_passes_a_complete_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _prompt_tree(tmp_path, _full_prompt_text()))
    assert check_repo.check_prompt_parity() == []


def test_prompt_parity_fails_on_a_missing_storyline(tmp_path, monkeypatch):
    body = _full_prompt_text().replace("`pitch-deck`", "")
    monkeypatch.setattr(check_repo, "ROOT", _prompt_tree(tmp_path, body))
    errors = check_repo.check_prompt_parity()
    assert any("`pitch-deck`" in e for e in errors)


def test_prompt_parity_fails_on_a_missing_banned_phrase(tmp_path, monkeypatch):
    body = _full_prompt_text().replace("without further ado", "")
    monkeypatch.setattr(check_repo, "ROOT", _prompt_tree(tmp_path, body))
    errors = check_repo.check_prompt_parity()
    assert any("without further ado" in e for e in errors)


def test_prompt_parity_fails_on_a_missing_sentence(tmp_path, monkeypatch):
    body = _full_prompt_text().replace("the number first", "the gloss first")
    monkeypatch.setattr(check_repo, "ROOT", _prompt_tree(tmp_path, body))
    errors = check_repo.check_prompt_parity()
    assert any("the number first" in e for e in errors)


def test_the_live_prompt_is_at_parity():
    assert check_repo.check_prompt_parity() == []


# 0.1.535 — a manifest row for a file git does not track fails `assets tracked`.

def test_a_manifest_row_for_an_untracked_file_fails(tmp_path, monkeypatch):
    repo = _git_tree(tmp_path / "repo", {
        "assets/logos/SOURCES.md": "| File | Mark |\n|---|---|\n| `ghost.svg` | Ghost |\n",
        "assets/logos/real.svg": "<svg/>",
        ".gitignore": ""})
    monkeypatch.setattr(check_repo, "ROOT", repo)
    errors = check_repo.check_assets_tracked()
    assert len(errors) == 1 and "ghost.svg" in errors[0] and "SOURCES.md:3" in errors[0]


def test_a_manifest_row_for_a_tracked_file_passes(tmp_path, monkeypatch):
    repo = _git_tree(tmp_path / "repo", {
        "assets/logos/SOURCES.md": "| File | Mark |\n|---|---|\n| `real.svg` | Real |\n",
        "assets/logos/real.svg": "<svg/>",
        ".gitignore": ""})
    monkeypatch.setattr(check_repo, "ROOT", repo)
    assert check_repo.check_assets_tracked() == []


# 0.1.536 — AGENTS.md stays a map, and claim_sweep can scope to what changed.

def test_agents_over_the_ceiling_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "AGENTS.md": "x\n" * (check_repo.AGENTS_LINE_CEILING + 1)}))
    errors = check_repo.check_entry_restatement_ceiling()
    assert len(errors) == 1 and "ceiling" in errors[0]


def test_agents_at_the_ceiling_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "AGENTS.md": "x\n" * check_repo.AGENTS_LINE_CEILING}))
    assert check_repo.check_entry_restatement_ceiling() == []


def test_the_live_agents_is_under_the_ceiling():
    assert check_repo.check_entry_restatement_ceiling() == []


def test_claim_sweep_changed_scopes_to_the_touched_files(tmp_path, monkeypatch):
    import claim_sweep
    repo = _git_tree(tmp_path / "repo", {
        "README.md": "This package ships three guards.\n",
        "NOTES.md": "There are five checkers.\n",
        "scripts/check/check_repo.py": "CHECKS = ()\n"})
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "-m", "base"], cwd=repo, check=True)
    (repo / "NOTES.md").write_text("There are six checkers.\n", encoding="utf-8")
    monkeypatch.setattr(claim_sweep, "ROOT", repo)
    changed = claim_sweep.changed_since("HEAD")
    assert changed == {"NOTES.md"}
    scoped = claim_sweep.sweep_counts(changed)
    assert all(rel == "NOTES.md" for rel, _n, _c in scoped)
