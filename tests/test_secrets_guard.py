"""The secrets guard on synthetic git trees — pass, fail, waiver, binary."""
import subprocess

import check_privacy
import check_repo
import pytest


@pytest.fixture(autouse=True)
def _no_operator_terms(monkeypatch, tmp_path_factory):
    """Pin ~/.lumi/terms to a NON-existent path by default, so the client-name
    half takes its documented structural skip (no_dir) and these credential
    tests are deterministic regardless of the host's real list. The tests that
    exercise the client-name half override TERMS_DIR themselves. Without this
    pin the guard read the host's real ~/.lumi/terms (the host-machine-state
    fragility class GAP-050 part 2 names)."""
    monkeypatch.setattr(check_privacy, "TERMS_DIR",
                        tmp_path_factory.mktemp("no_lumi") / "absent")


def _repo(tmp_path, files):
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_clean_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": "the api key concept is discussed here, no value\n"}))
    assert check_repo.check_secrets() == []


def test_aws_key_fails_with_line(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "config.md": "x\nkey = AKIAIOSFODNN7EXAMPLE\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1
    assert "config.md:2" in errors[0] and "AWS" in errors[0]


def test_private_key_block_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "deploy.pem": "-----BEGIN RSA PRIVATE KEY-----\nabc\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1
    assert "private key block" in errors[0] and "deploy.pem:1" in errors[0]


def test_api_key_assignment_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "conf.py": 'api_key = "abcdefghijklmnopqrstuv123456"\n'}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1
    assert "assignment of a secret" in errors[0] and "conf.py:1" in errors[0]


def test_github_token_fails_naming_the_pattern(tmp_path, monkeypatch):
    token = "ghp_" + "a1" * 18  # synthetic: 36 alnum chars after the prefix
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": f"x\ntoken = {token}\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1
    assert "GitHub token" in errors[0] and "notes.md:2" in errors[0]


def test_github_fine_grained_token_fails(tmp_path, monkeypatch):
    token = "github_pat_" + "b2" * 12  # synthetic 24-char tail
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "notes.md": f"token = {token}\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1
    assert "GitHub fine-grained token" in errors[0]


def test_waiver_silences_with_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "rules.md": "banned example: AKIAIOSFODNN7EXAMPLE\n"}))
    monkeypatch.setitem(check_repo.SECRET_WAIVERS, "rules.md",
                        "rule data: the banned-example string itself")
    assert check_repo.check_secrets() == []


def test_binary_files_are_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "asset.woff2": b"\x00\x01AKIA" + bytes(range(200))}))
    assert check_repo.check_secrets() == []


def test_live_repo_is_clean():
    assert check_repo.check_secrets() == []


# --- the client-name half: GAP-047, the four outcomes keyed on len(terms) ---

def test_provisioned_but_empty_dir_fails(tmp_path, monkeypatch):
    """~/.lumi/terms/ exists but holds no *.terms.txt — provisioned, nothing to
    search for. Must fail, not silently pass (the 2026-08-20 hole)."""
    terms_dir = tmp_path / "terms"
    terms_dir.mkdir()
    monkeypatch.setattr(check_privacy, "TERMS_DIR", terms_dir)
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path / "r", {
        "notes.md": "the Acme rollout\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1 and "no usable" in errors[0]


def test_provisioned_but_comment_only_file_fails(tmp_path, monkeypatch):
    """A *.terms.txt that EXISTS but is comment-only loads as ([], 'loaded').
    The is_dir()-only first draft would have passed this; keying on len(terms)
    catches it — the empty-FILE path, distinct from the empty-DIR path."""
    terms_dir = tmp_path / "terms"
    terms_dir.mkdir()
    (terms_dir / "x.terms.txt").write_text("# only a comment\n\n")
    monkeypatch.setattr(check_privacy, "TERMS_DIR", terms_dir)
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path / "r", {
        "notes.md": "the Acme rollout\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1 and "no usable" in errors[0]


def test_no_terms_dir_skips_the_client_half(tmp_path, monkeypatch, capsys):
    """No ~/.lumi/terms/ at all — the delegated structural skip. Returns [] (a
    client name is NOT caught here, by design) but says so on stderr (FM-24:
    the skip is visible, not mute)."""
    monkeypatch.setattr(check_privacy, "TERMS_DIR", tmp_path / "absent")
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path / "r", {
        "notes.md": "the Acme rollout\n"}))
    assert check_repo.check_secrets() == []
    assert "client-name half skipped" in capsys.readouterr().err


def test_client_name_with_a_real_list_is_caught(tmp_path, monkeypatch):
    """A non-empty list with an engagement term present in the tree — red line 9,
    the whole point of the half."""
    terms_dir = tmp_path / "terms"
    terms_dir.mkdir()
    (terms_dir / "c.terms.txt").write_text("Acme\n")
    monkeypatch.setattr(check_privacy, "TERMS_DIR", terms_dir)
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path / "r", {
        "CHANGELOG.md": "the Acme rollout went well\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1 and "red line 9" in errors[0]
    assert "Acme" not in errors[0]  # the term is never echoed


def test_a_populated_list_with_no_hit_is_clean(tmp_path, monkeypatch):
    """A non-empty list whose term is absent from the tree — the 'loaded, clean'
    outcome. Guards the scan wiring against a false positive."""
    terms_dir = tmp_path / "terms"
    terms_dir.mkdir()
    (terms_dir / "c.terms.txt").write_text("Acme\n")
    monkeypatch.setattr(check_privacy, "TERMS_DIR", terms_dir)
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path / "r", {
        "notes.md": "nothing sensitive in here at all\n"}))
    assert check_repo.check_secrets() == []


def test_a_file_at_the_terms_path_fails_rather_than_skipping(tmp_path, monkeypatch):
    """LUMI_TERMS_DIR pointed at the list FILE (not its directory) — a populated
    list the glob cannot read. Keyed on .exists() not .is_dir(), this is
    provisioned_empty (a finding), not the silent no_dir skip: the guard's own
    message invites pointing the env var 'at it', so this misconfig is likely."""
    list_file = tmp_path / "mylist.terms.txt"
    list_file.write_text("Acme\n")  # a real, populated list — just at a file path
    monkeypatch.setattr(check_privacy, "TERMS_DIR", list_file)
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path / "r", {
        "notes.md": "the Acme rollout\n"}))
    errors = check_repo.check_secrets()
    assert len(errors) == 1 and "no usable" in errors[0]
