"""The secrets guard on synthetic git trees — pass, fail, waiver, binary."""
import subprocess

import check_repo


def _repo(tmp_path, files):
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
    assert len(check_repo.check_secrets()) == 1


def test_api_key_assignment_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "conf.py": 'api_key = "abcdefghijklmnopqrstuv123456"\n'}))
    assert len(check_repo.check_secrets()) == 1


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
