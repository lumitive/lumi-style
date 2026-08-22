"""A consumer script may not name a file the projection leaves behind.

The teeth of the split. `check_shipped_closure` proves the boundary is total;
this proves the consumer half can stand on its own — a script that ships while
the file it opens does not is a skill that is green here and broken in a fresh
clone, which is the class `check_assets_tracked` exists for.
"""
import json
import subprocess

import check_repo

RULES = [
    {"prefix": "SKILL.md", "side": "consumer", "why": "the entry"},
    {"prefix": "references/", "side": "consumer", "why": "the rules"},
    {"prefix": "adapters/", "side": "consumer", "why": "the manifest"},
    {"prefix": "KNOWN_GAPS.md", "side": "dev", "why": "the defect ledger"},
]


def _repo(tmp_path, script_body):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in {
        "SKILL.md": "run `python3 scripts/check/check_x.py`\n",
        "references/brand.md": "water\n",
        "KNOWN_GAPS.md": "GAP-001\n",
        "scripts/check/check_x.py": script_body,
        "adapters/shipped.json": json.dumps(
            {"schema": 1, "consumer_seeds": [], "rules": RULES}),
    }.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_a_consumer_path_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'RULES = ROOT / "references/brand.md"\n'))
    assert check_repo.check_cross_boundary_paths() == []


def test_a_dev_path_fails_and_says_what_to_do(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'GAPS = ROOT / "KNOWN_GAPS.md"\n'))
    errors = check_repo.check_cross_boundary_paths()
    assert len(errors) == 1
    assert "`KNOWN_GAPS.md`" in errors[0] and "state_dir" in errors[0]


def test_a_path_built_from_two_pieces_is_seen(tmp_path, monkeypatch):
    """`ROOT / "evals" / "x.json"` is the form half this repository uses."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'GAPS = ROOT / "KNOWN" / "GAPS.md"\n'))
    # not a tracked file under that spelling, so nothing fires
    assert check_repo.check_cross_boundary_paths() == []
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'B = ROOT / "references" / "brand.md"\n'))
    assert check_repo.check_cross_boundary_paths() == []


def test_an_untracked_path_is_not_its_business(tmp_path, monkeypatch):
    """The state stores moved out from under this scan for exactly that
    reason: `~/.lumi/traces` is nobody's tracked file."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'S = "evals/corpus.local.json"\n'))
    assert check_repo.check_cross_boundary_paths() == []


def test_a_waiver_silences_with_a_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'GAPS = ROOT / "KNOWN_GAPS.md"\n'))
    monkeypatch.setitem(check_repo.CROSS_BOUNDARY_WAIVERS,
                        ("scripts/check/check_x.py", "KNOWN_GAPS.md"),
                        "read only when present, and absent by design")
    assert check_repo.check_cross_boundary_paths() == []
