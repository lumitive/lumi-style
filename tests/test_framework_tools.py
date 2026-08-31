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


# "no `tool` key at all" and "a `tool` key holding null" are different states
# and `None` cannot express both. Mutation review found the second one ungraded.
ABSENT = object()


def _tree(tmp_path, tool):
    entry = {"question": "q?", "move": "correlate", "slots": ["a"],
             "misuse": "m", "drawn": "native"}
    if tool is not ABSENT:
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
    out = _run(tmp_path, monkeypatch, ABSENT)
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


def test_the_guard_is_registered():
    """A guard with no CHECKS entry does not run, however green its own tests.
    Found by mutation: deleting both new rows left the whole suite passing."""
    assert any(fn is check_repo.check_framework_tools
               for _name, fn in check_repo.CHECKS)


def test_a_run_line_missing_a_required_flag_fails(tmp_path, monkeypatch):
    """The defect 0.1.665 shipped, replayed. `_tool_flags_exist`'s first
    version checked only the flags a command DID pass and returned nothing when
    it passed none — which was the defect's exact shape."""
    (tmp_path / "probe.py").write_text("")           # placeholder; see below
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, GOOD))
    (tmp_path / "scripts/render/shipper.py").write_text(
        'import argparse\n'
        'p = argparse.ArgumentParser()\n'
        'p.add_argument("--data", required=True)\n', encoding="utf-8")
    import subprocess as sp
    sp.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    out = check_repo.check_framework_tools()
    assert len(out) == 1
    assert "does not pass --data" in out[0]
    assert "declares required" in out[0]


def test_a_run_line_passing_an_undefined_flag_fails(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch,
               {"module": "shipper",
                "run": "python3 scripts/render/shipper.py --dat x"})
    assert len(out) == 1 and "which scripts/render/shipper.py does not define" in out[0]


def test_an_empty_tool_object_is_reported(tmp_path, monkeypatch):
    """Found by mutation: `e.get("tool")` dropped a falsy tool out of the
    graded population, so it was ungraded AND left the blind branch quiet."""
    empties: tuple[object, ...] = ({}, None, "")
    for empty in empties:
        out = _run(tmp_path, monkeypatch, empty)
        assert len(out) == 1, f"{empty!r} produced {out}"
        assert "declares an empty `tool`" in out[0], f"{empty!r} -> {out}"


def test_two_scripts_in_one_run_line_are_both_graded(tmp_path, monkeypatch):
    """Found by mutation: `for path in hits[:1]` — only the first — survived."""
    out = _run(tmp_path, monkeypatch,
               {"module": "shipper",
                "run": "python3 scripts/build/private_tool.py "
                       "&& python3 scripts/render/gone.py"})
    assert len(out) == 2, out


def test_the_module_name_must_match_exactly(tmp_path, monkeypatch):
    """Found by mutation: `module not in stem` would let 'scatter' pass for
    scatter_svg.py — the two-names defect, one character weaker."""
    out = _run(tmp_path, monkeypatch,
               {"module": "ship", "run": "python3 scripts/render/shipper.py"})
    assert len(out) == 1 and "two names for one tool" in out[0]
