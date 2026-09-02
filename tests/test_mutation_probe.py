"""The probe that breaks this release's code to see whether the tests notice.

It asked for these itself on its first run in the release flow: no test file
imported `mutation_probe`, so every mutation of it survived by construction —
the same finding it had just made about `check_fixtures`.
"""
import json

import mutation_probe as mp


def test_a_flipped_comparison_is_offered(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("def go(n):\n    if n < 3:\n        return 1\n    return 2\n")
    got = [(w, new.strip()) for _l, w, _o, new in mp.mutations(f)]
    assert ("< -> >=", "if n >= 3:") in got


def test_a_container_constant_is_offered(tmp_path):
    f = tmp_path / "m.py"
    f.write_text('TABLE = {"a": 1}\n')
    assert any("TABLE emptied" in w for _l, w, _o, _n in mp.mutations(f))


def test_the_shared_bootstrap_is_never_mutated(tmp_path):
    """It is identical in every module and held by check_repo's own guard, so
    mutating it reported a survivor in every file that carries it. Skipped by
    RANGE rather than waived per file: a waiver list with one row per module is
    the hand-written inventory FM-20 refuses."""
    f = tmp_path / "m.py"
    f.write_text(
        "# --- scripts path bootstrap (canonical) ---\n"
        'import pathlib as _bs_pathlib\n'
        '_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).parents\n'
        '                     if p.name == "scripts")\n'
        "del _bs_pathlib\n"
        "def go(n):\n    return n == 1\n")
    lines = [line for line, _w, _o, _n in mp.mutations(f)]
    assert lines and all(line >= 6 for line in lines), \
        f"a bootstrap line was offered for mutation: {lines}"


def test_a_second_bootstrap_form_is_also_skipped(tmp_path):
    """`ROOT = next(... if p.name == "scripts").parent` is the same boilerplate
    outside the marked block, and it reported a survivor until 0.1.679."""
    f = tmp_path / "m.py"
    f.write_text('import pathlib\n'
                 'ROOT = next(p for p in pathlib.Path(__file__).parents\n'
                 '            if p.name == "scripts").parent\n'
                 "def go(n):\n    return n == 1\n")
    assert all(line >= 4 for line, _w, _o, _n in mp.mutations(f))


def test_a_waiver_is_keyed_on_the_source_line_not_its_number(tmp_path,
                                                             monkeypatch):
    """A waiver keyed `file:line` stops matching the moment anything above it
    moves — and worse, silently comes to waive a DIFFERENT mutation. That is
    the citation-drift class this repository fixed the same week, inside the
    mechanism written against it."""
    waivers = tmp_path / "w.json"
    waivers.write_text(json.dumps({"survivors": {
        "a.py :: < -> >= :: if n < 3:": "a reason"}}))
    monkeypatch.setattr(mp, "WAIVERS", waivers)
    assert "a.py :: < -> >= :: if n < 3:" in mp.waived()
    # The key carries no line number at all, so it cannot rot when one moves.
    assert not any(":" + str(n) in k for k in mp.waived() for n in range(1, 200))


def test_an_unreadable_waiver_file_waives_nothing(tmp_path, monkeypatch):
    """Failing open here would let a broken file silence every survivor."""
    bad = tmp_path / "w.json"
    bad.write_text("{not json")
    monkeypatch.setattr(mp, "WAIVERS", bad)
    assert mp.waived() == {}


def test_a_module_no_test_imports_is_itself_the_finding(tmp_path, monkeypatch):
    """Every mutation of an unimported module survives by construction, so
    saying "0 alive" about it would be the FM-24 answer."""
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(mp, "ROOT", tmp_path)
    assert mp.tests_reaching("anything") == []


def test_a_run_that_mutated_nothing_says_so(tmp_path, monkeypatch, capsys):
    """A scan that visited nothing is not a clean scan — it must not print the
    line a clean run prints. Pointed at an empty tree rather than at the real
    one: the first version of this test ran the probe over the working tree and
    took three minutes and forty-one seconds, which is a test nobody keeps."""
    monkeypatch.setattr(mp, "ROOT", tmp_path)
    monkeypatch.setattr(mp, "changed_files", lambda base: [])
    rc = mp.main(["--base", "HEAD"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "nothing was mutated" in out
    assert "every mutation was caught" not in out
