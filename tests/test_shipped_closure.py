"""The split boundary partitions the tracked tree.

A LIST of what ships can omit a file silently and still look complete. A
PARTITION cannot, which is the whole reason the manifest is written this way —
`check_assets_tracked`'s comment is the standing lesson: a guard that reads the
filesystem cannot tell "published" from "on the author's machine".
"""
import json
import subprocess

import check_repo
import shipped

RULES: list[dict] = [
    {"prefix": "references/", "side": "consumer", "why": "the rules"},
    {"prefix": "tests/", "side": "dev", "why": "the suite"},
    {"prefix": "SKILL.md", "side": "consumer", "why": "the entry"},
]
ADAPTERS = {"prefix": "adapters/", "side": "consumer", "why": "this file"}
MANIFEST = {
    "schema": 1,
    "consumer_seeds": ["helper"],
    "rules": RULES,
}
FILES = {
    "SKILL.md": "run `python3 scripts/check/check_x.py`\n",
    "references/brand.md": "the water thesis\n",
    "tests/test_a.py": "assert True\n",
    "scripts/check/check_x.py": "import helper\n",
    "scripts/lib/helper.py": "x = 1\n",
    "scripts/ops/devtool.py": "y = 2\n",
}


def _repo(tmp_path, manifest=None, files=None):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in (files or FILES).items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    m = tmp_path / "adapters" / "shipped.json"
    m.parent.mkdir(parents=True, exist_ok=True)
    m.write_text(json.dumps(manifest or MANIFEST))
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def _with(manifest):
    d = json.loads(json.dumps(MANIFEST))
    d.update(manifest)
    return d


def test_a_total_partition_passes(tmp_path, monkeypatch):
    m = _with({"rules": RULES + [ADAPTERS]})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, m))
    assert check_repo.check_shipped_closure() == []


def test_an_unclaimed_file_fails(tmp_path, monkeypatch):
    """The finding the manifest exists for: a file the projection cannot
    place. Silence here would ship a skill missing a file nobody listed."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, MANIFEST))
    errors = check_repo.check_shipped_closure()
    assert any("adapters/shipped.json is tracked and no rule" in e
               for e in errors), errors


def test_a_dead_rule_fails(tmp_path, monkeypatch):
    m = _with({"rules": RULES + [ADAPTERS,
               {"prefix": "nowhere/", "side": "dev", "why": "claims nothing"}]})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, m))
    errors = check_repo.check_shipped_closure()
    assert len(errors) == 1 and "`nowhere/` claims no tracked file" in errors[0]


def test_a_seed_naming_no_script_fails(tmp_path, monkeypatch):
    m = _with({"consumer_seeds": ["helper", "ghost"],
               "rules": RULES + [ADAPTERS]})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, m))
    errors = check_repo.check_shipped_closure()
    assert len(errors) == 1 and "`ghost` names no script" in errors[0]


def test_a_script_reached_from_the_skill_is_consumer(tmp_path):
    """SKILL.md names `check_x.py`, which imports `helper`. Both ship."""
    root = _repo(tmp_path, _with({"rules": RULES + [ADAPTERS]}))
    assert shipped.consumer_scripts(root) == {"check_x", "helper"}
    assert shipped.side_of("scripts/check/check_x.py", root) == "consumer"


def test_an_unreachable_script_is_development(tmp_path):
    """The safe direction: a dev script wrongly kept is dead weight, a consumer
    script wrongly dropped is a broken install."""
    root = _repo(tmp_path, _with({"rules": RULES + [ADAPTERS]}))
    assert shipped.side_of("scripts/ops/devtool.py", root) == "dev"


def test_a_subprocess_edge_counts_as_reachable(tmp_path):
    """This package's scripts invoke each other by subprocess as often as they
    import each other, and a boundary that saw only imports would cut a live
    edge."""
    files = dict(FILES)
    files["scripts/check/check_x.py"] = (
        'run(["python3", "scripts/ops/devtool.py"])\n')
    root = _repo(tmp_path, _with({"rules": RULES + [ADAPTERS]}), files)
    assert shipped.side_of("scripts/ops/devtool.py", root) == "consumer"
