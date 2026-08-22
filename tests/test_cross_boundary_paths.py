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
    {"prefix": "reviews/", "side": "dev", "why": "the score store"},
]


def _repo(tmp_path, script_body, extra=None):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in {**(extra or {}), **{
        "SKILL.md": "run `python3 scripts/check/check_x.py`\n",
        "references/brand.md": "water\n",
        "KNOWN_GAPS.md": "GAP-001\n",
        "scripts/check/check_x.py": script_body,
        "adapters/shipped.json": json.dumps(
            {"schema": 1, "consumer_seeds": [], "rules": RULES}),
    }}.items():
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


# --- the red team's attacks, kept as tests -----------------------------------

def test_a_single_quoted_path_is_seen(tmp_path, monkeypatch):
    """The first version matched double quotes with a regex, and this
    repository's lint config selects no quote rule — `inspect_layout.py` alone
    carries five hundred single-quoted strings, so half the tree went
    unscanned."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, "GAPS = 'KNOWN_GAPS.md'\n"))
    errors = check_repo.check_cross_boundary_paths()
    assert len(errors) == 1 and "`KNOWN_GAPS.md`" in errors[0]


def test_a_triple_quoted_and_implicitly_joined_path_is_seen(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'A = """KNOWN_GAPS.md"""\n'))
    assert len(check_repo.check_cross_boundary_paths()) == 1
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'B = "KNOWN_" "GAPS.md"\n'))
    assert len(check_repo.check_cross_boundary_paths()) == 1


def test_a_dev_directory_is_fatal_too(tmp_path, monkeypatch):
    """`(ROOT / "reviews")` resolves to nothing after the projection, and the
    first version compared only against tracked FILES."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'D = ROOT / "reviews"\n', extra={"reviews/scores.json": "{}\n"}))
    errors = check_repo.check_cross_boundary_paths()
    assert len(errors) == 1 and "directory `reviews`" in errors[0]


def test_a_three_segment_join_is_reconstructed(tmp_path, monkeypatch):
    """`joined` handled exactly two segments, so a three-segment path walked
    past it."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'P = ROOT / "reviews" / "old" / "scores.json"\n',
        extra={"reviews/old/scores.json": "{}\n"}))
    errors = check_repo.check_cross_boundary_paths()
    # the two parent directories are named too, and reporting them is correct
    assert any("reviews/old/scores.json" in e for e in errors), errors


def test_a_dynamic_import_of_a_dev_module_is_reported(tmp_path, monkeypatch):
    """An import the AST reachability cannot see: the module is classified
    development, and the script ImportErrors on its first use in the
    projection."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path,
        'import importlib\nG = importlib.import_module("devonly")\n',
        extra={"scripts/lib/devonly.py": "q = 1\n"}))
    errors = check_repo.check_cross_boundary_paths()
    assert len(errors) == 1 and "dynamically" in errors[0]


def test_a_state_dir_fallback_is_not_a_dependency(tmp_path, monkeypatch):
    """`state_dir.store(in_repo=("reviews", "scores.json"))` names the path
    that is ALLOWED to be absent — the resolver falls to the operator state
    directory when it is."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path,
        'import state_dir\n'
        'S = state_dir.store("scores.json", in_repo=("reviews", "scores.json"))\n',
        extra={"reviews/scores.json": "{}\n"}))
    assert check_repo.check_cross_boundary_paths() == []
