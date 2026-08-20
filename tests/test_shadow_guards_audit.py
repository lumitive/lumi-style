"""Two guards from the 2026-08-20 audit: one credential table, one strip-tags.

Both are the `no shadow math` shape — a shared implementation and a guard that
refuses a private copy — and both ship with the tree that fails them, because
a guard only ever seen passing is FM-01.
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


def test_no_shadow_markup_passes_a_clean_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "scripts/lib/markup.py": '_TAG_RE = re.compile(r"<[^>]+>")\n',
        "scripts/check/fine.py": "text = markup.visible_text(raw)\n"}))
    assert check_repo.check_no_shadow_markup() == []


def test_a_private_strip_tags_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "scripts/check/copy.py": 'x = re.sub(r"<[^>]+>", " ", raw)\n'}))
    errors = check_repo.check_no_shadow_markup()
    assert len(errors) == 1 and "copy.py:1" in errors[0]


def test_a_private_cjk_space_rule_fails(tmp_path, monkeypatch):
    rule = 'y = re.sub(r"(?<=[\\u4e00-\\u9fff]) (?=[\\u4e00-\\u9fff])", "", t)\n'
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, {
        "scripts/check/copy.py": rule}))
    errors = check_repo.check_no_shadow_markup()
    assert len(errors) == 1 and "CJK-space" in errors[0]


def test_markup_helpers():
    assert markup.strip_tags("<b>a</b>&amp;<i>b</i>") == " a & b "
    assert markup.strip_tags("<b>a</b><i>b</i>", sep="") == "ab"
    assert markup.visible_text("  <p>one\n  two</p> ") == "one two"
    assert markup.join_cjk("每个 Agent 都会 这样") == "每个 Agent 都会这样"
    assert markup.join_cjk("a b") == "a b"


def test_the_live_tree_carries_no_copy():
    assert check_repo.check_no_shadow_markup() == []
    assert check_repo.check_secret_patterns_parity() == []
    assert pathlib.Path(check_repo.ROOT, "scripts/lib/secret_patterns.py").exists()
