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


# --- the red team's attacks, kept as tests -----------------------------------

def test_a_prefix_claims_only_on_a_path_boundary(tmp_path):
    """`NOTICE` must not claim `NOTICE_TO_MAINTAINERS.md`. A bare startswith
    published two maintainer files through a partition that reported itself
    total, and this repository has now shipped that missing boundary five
    times."""
    m = _with({"rules": RULES + [ADAPTERS,
               {"prefix": "NOTICE", "side": "consumer", "why": "attributions"}]})
    root = _repo(tmp_path, m, {**FILES, "NOTICE": "x\n"})
    assert shipped.side_of("NOTICE", root) == "consumer"
    assert shipped.side_of("NOTICE_TO_MAINTAINERS.md", root) is None
    assert shipped.matches("a/b/c", "a/b") and not shipped.matches("ab/c", "a")


def test_a_misspelled_side_fails_rather_than_disarming_the_teeth(tmp_path, monkeypatch):
    """One capitalised letter made a whole directory invisible to the
    cross-boundary scan while the closure still reported a total partition."""
    m = _with({"rules": [dict(r, side="Dev") if r["prefix"] == "tests/" else r
                         for r in RULES] + [ADAPTERS]})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, m))
    errors = check_repo.check_shipped_closure()
    assert any("declares side 'Dev'" in e for e in errors), errors


def test_a_rule_with_no_reason_fails(tmp_path, monkeypatch):
    m = _with({"rules": [dict(r, why="") if r["prefix"] == "tests/" else r
                         for r in RULES] + [ADAPTERS]})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, m))
    errors = check_repo.check_shipped_closure()
    assert any("gives\nno reason" in e or "no reason" in e for e in errors), errors


def test_a_dev_pin_that_is_imported_fails(tmp_path, monkeypatch):
    """A pin may override a MENTION, never a live import — that is the half a
    mention cannot fake, and the only thing that makes a pin auditable."""
    files = {**FILES, "scripts/ops/pinned.py": "z = 3\n"}
    files["scripts/check/check_x.py"] = "import helper\nimport pinned\n"
    m = _with({"dev_pins": [{"stem": "pinned", "why": "prose only"}],
               "rules": RULES + [ADAPTERS]})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, m, files))
    errors = check_repo.check_shipped_closure()
    assert any("pinned" in e and "live import" in e for e in errors), errors


def test_a_dev_pin_over_a_mention_is_accepted(tmp_path, monkeypatch):
    """Two development tools rode a docstring into the consumer half."""
    files = {**FILES, "scripts/ops/pinned.py": "z = 3\n"}
    files["scripts/lib/helper.py"] = '"""see scripts/ops/pinned.py for the grid."""\n'
    m = _with({"dev_pins": [{"stem": "pinned", "why": "named in a docstring only"}],
               "rules": RULES + [ADAPTERS]})
    root = _repo(tmp_path, m, files)
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert check_repo.check_shipped_closure() == []
    assert shipped.side_of("scripts/ops/pinned.py", root) == "dev"


def test_a_with_name_edge_counts_as_reachable(tmp_path):
    """`pathlib.Path(__file__).with_name("trace.py")` is new_deck.py's edge to
    the trace store, and the regex that was added to catch assembled paths
    could not see it — there is no `scripts/<drawer>/` in the string."""
    files = {**FILES, "scripts/check/sibling.py": "w = 4\n"}
    files["scripts/check/check_x.py"] = (
        'import pathlib\n'
        'T = pathlib.Path(__file__).with_name("sibling.py")\n')
    root = _repo(tmp_path, _with({"rules": RULES + [ADAPTERS]}), files)
    assert shipped.side_of("scripts/check/sibling.py", root) == "consumer"


def test_a_drawer_has_no_side(tmp_path):
    """`scripts/check/` holds both sides, so calling it development reported
    every consumer script that named its own drawer."""
    root = _repo(tmp_path, _with({"rules": RULES + [ADAPTERS]}))
    assert shipped.side_of("scripts/check", root) is None
