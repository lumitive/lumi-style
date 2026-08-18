"""The framework dictionary guard, red and green (FM-01 discipline).

The dictionary is the generation-side complement to the shape library
(analysis-rules.md AR-4); the guard holds every binding to the library and
every entry to usability. Each failure shape below is one the repo has
shipped in another guise: a dangling reference, a rule without its limit,
a vocabulary word from outside the set.
"""
import json
import subprocess

import check_repo


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


TAGS = json.dumps({"shapes": {"p001-unit-01": {"family": "unit",
                                               "relation": ["order"]}}})


def _fw(**entry):
    base = {"question": "q?", "move": "compare", "slots": ["a"],
            "misuse": "m", "shapes": ["p001-unit-01"], "drawn": None}
    base.update(entry)
    return json.dumps({"version": 1, "frameworks": {"probe": base}})


def test_a_resolving_usable_entry_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(),
        "assets/shapes/tags.json": TAGS}))
    assert check_repo.check_frameworks() == []


def test_a_dangling_shape_binding_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(shapes=["p999-gone-01"]),
        "assets/shapes/tags.json": TAGS}))
    errors = check_repo.check_frameworks()
    assert any("p999-gone-01" in e for e in errors)


def test_a_move_outside_the_five_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(move="vibes"),
        "assets/shapes/tags.json": TAGS}))
    assert any("five analytical moves" in e for e in check_repo.check_frameworks())


def test_a_missing_misuse_line_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(misuse=""),
        "assets/shapes/tags.json": TAGS}))
    assert any("misuse" in e for e in check_repo.check_frameworks())


def test_shapeless_without_native_declaration_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(shapes=[]),
        "assets/shapes/tags.json": TAGS}))
    assert any("native" in e for e in check_repo.check_frameworks())


def test_shapeless_with_native_declaration_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(shapes=[], drawn="native"),
        "assets/shapes/tags.json": TAGS}))
    assert check_repo.check_frameworks() == []
