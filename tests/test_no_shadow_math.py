"""The no-shadow-math guard, proven able to pass AND to fail on synthetic
trees — a guard tested only against the live repo cannot demonstrate that a
rewritten `return []` would be noticed.
"""
import check_repo


def _tree(tmp_path, extra=""):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "color_math.py").write_text("def srgb_linear(v):\n    return v\n")
    (scripts / "css_tokens.py").write_text("def css_vars(b):\n    return {}\n")
    (scripts / "consumer.py").write_text(
        "from color_math import srgb_linear\n" + extra)
    return tmp_path


def test_clean_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path))
    assert check_repo.check_no_shadow_math() == []


def test_regrown_copy_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(
        tmp_path,
        "def _lin(c):\n    return c / 12.92\n"))
    errors = check_repo.check_no_shadow_math()
    assert len(errors) == 1
    assert "_lin" in errors[0] and "color_math" in errors[0]


def test_calls_and_imports_are_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(
        tmp_path,
        "x = srgb_linear(0.5)\n# mentions css_vars( in prose\n"))
    assert check_repo.check_no_shadow_math() == []


def test_live_repo_is_clean():
    assert check_repo.check_no_shadow_math() == []
