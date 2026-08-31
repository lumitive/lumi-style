"""The framework-tool guard, red, green and blind (FM-01 + FM-24).

`scatter_svg` shipped at 0.1.664 with a published rule pointing at it and zero
callers, and every check in this package printed the same lines it prints on a
healthy registry. This guard is the answer, and the blind case below is the
one it exists for: an empty `tool` set is not a clean registry.
"""
import json
import subprocess

import check_repo

SHIPPED = json.dumps({
    "schema": 1, "$comment": "probe",
    "consumer_seeds": ["shipper"], "seeds_comment": "probe",
    "dev_pins": [], "pins_comment": "probe",
    "rules": [{"prefix": "references/", "side": "consumer", "why": "rule prose"},
              {"prefix": "SKILL.md", "side": "consumer", "why": "entry point"},
              {"prefix": "adapters/", "side": "consumer", "why": "registry"},
              {"prefix": "assets/", "side": "consumer", "why": "the library"}],
})


def _tree(tmp_path, tool):
    entry = {"question": "q?", "move": "correlate", "slots": ["a"],
             "misuse": "m", "drawn": "native"}
    if tool is not None:
        entry["tool"] = tool
    files = {
        "adapters/shipped.json": SHIPPED,
        "SKILL.md": "the entry point names scripts/render/shipper.py\n",
        "scripts/render/shipper.py": "x = 1\n",
        "scripts/build/private_tool.py": "y = 1\n",
        "assets/frameworks.json": json.dumps({"version": 1,
                                              "frameworks": {"probe": entry}}),
    }
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def _run(tmp_path, monkeypatch, tool):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, tool))
    return check_repo.check_framework_tools()


GOOD = {"module": "shipper", "run": "python3 scripts/render/shipper.py <spec>"}


def test_a_resolving_tool_passes(tmp_path, monkeypatch):
    assert _run(tmp_path, monkeypatch, GOOD) == []


def test_a_development_side_tool_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch,
               {"module": "private_tool",
                "run": "python3 scripts/build/private_tool.py"})
    assert len(out) == 1 and "does not carry" in out[0]


def test_an_untracked_tool_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch,
               {"module": "gone", "run": "python3 scripts/render/gone.py"})
    assert len(out) == 1 and "not a tracked file" in out[0]


def test_two_names_for_one_tool_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch,
               {"module": "elsewhere", "run": "python3 scripts/render/shipper.py"})
    assert len(out) == 1 and "two names for one tool" in out[0]


def test_a_run_line_naming_no_script_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch, {"module": "shipper", "run": "draw it"})
    assert len(out) == 1 and "told to run nothing" in out[0]


def test_a_tool_that_is_not_an_object_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch, "scripts/render/shipper.py")
    assert len(out) == 1
    assert "is str, not an object" in out[0]


def test_a_half_declared_tool_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch, {"module": "shipper"})
    assert len(out) == 1 and "needs both" in out[0]


def test_a_registry_with_no_tool_at_all_is_not_a_pass(tmp_path, monkeypatch):
    """FM-24, and the state this guard was written from."""
    out = _run(tmp_path, monkeypatch, None)
    assert len(out) == 1
    assert "no framework declares a `tool`" in out[0]
    assert "looked at nothing" in out[0]


def test_an_unreadable_registry_is_not_a_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, GOOD))
    (tmp_path / "assets" / "frameworks.json").write_text("{ not json")
    out = check_repo.check_framework_tools()
    assert len(out) == 1 and "could not read the registry" in out[0]


def test_an_uncomputable_boundary_is_not_a_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, GOOD))
    (tmp_path / "SKILL.md").unlink()
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    out = check_repo.check_framework_tools()
    assert len(out) == 1 and "has not been checked" in out[0]
