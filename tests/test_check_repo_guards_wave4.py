"""Wave 4: the reorganization's enabling guards, both directions."""
import subprocess

import check_repo

BOOTSTRAP_STUB = (
    "# --- scripts path " + "bootstrap (canonical) ---\n"
    + 'for _sub in ("lib", "render", "check", "build", "ops", ""):\n'
    + "    _bs_sys.path.append(_p)\n")


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_script_paths_resolving_mentions_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "README.md": "run `python3 scripts/tool.py` to begin\n"}))
    assert check_repo.check_script_paths() == []


def test_script_paths_dangling_mention_fails_with_line(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "README.md": "intro\nrun `python3 scripts/gone.py` to begin\n"}))
    errors = check_repo.check_script_paths()
    assert len(errors) == 1
    assert "README.md:2" in errors[0] and "scripts/gone.py" in errors[0]


def test_script_paths_frozen_history_is_excluded(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "CHANGELOG.md": "## 0.1.1 — ran scripts/old_name.py back then\n",
        "specs/2026-01-01-x-design.md": "cited scripts/old_name.py\n"}))
    assert check_repo.check_script_paths() == []


def test_script_paths_waiver_silences_with_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "threat.md": "imagine a scripts/hijack.py planted by a PR\n"}))
    monkeypatch.setitem(check_repo.SCRIPT_PATH_WAIVERS,
                        ("threat.md", "scripts/hijack.py"),
                        "hypothetical illustration, not a reference")
    assert check_repo.check_script_paths() == []


def test_bootstrap_sibling_import_without_block_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/consumer.py": "import color_math\n",
        "scripts/color_math.py": "def f():\n    return 1\n"}))
    errors = check_repo.check_bootstrap()
    assert len(errors) == 1
    assert "consumer.py" in errors[0] and "color_math" in errors[0]


def test_bootstrap_block_present_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/consumer.py": BOOTSTRAP_STUB + "import color_math\n",
        "scripts/color_math.py": "def f():\n    return 1\n"}))
    assert check_repo.check_bootstrap() == []


def test_bootstrap_module_does_not_flag_itself(tmp_path, monkeypatch):
    # color_math.py mentioning its own name in a docstring is not an import
    # of a sibling; and a module importing ITSELF is not a thing.
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/color_math.py": '"""import color_math is how consumers use '
                                 'this."""\nX = 1\n'}))
    assert check_repo.check_bootstrap() == []


def test_live_repo_is_clean():
    assert check_repo.check_script_paths() == []
    assert check_repo.check_bootstrap() == []


def test_script_paths_constructed_path_fails_when_dangling(tmp_path, monkeypatch):
    """The 0.1.438 lesson: `ROOT / "scripts" / "x.py"` is invisible to the
    string form; the constructed form must resolve too."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py":
            'import subprocess\n'
            'subprocess.run([str(ROOT / "scripts" / "gone.py")])\n'}))
    errors = check_repo.check_script_paths()
    assert len(errors) == 1
    assert "builds the path scripts/gone.py" in errors[0]


def test_script_paths_constructed_path_resolving_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py":
            'import subprocess\n'
            'subprocess.run([str(ROOT / "scripts" / "lib" / "there.py")])\n',
        "scripts/lib/there.py": "x = 1\n"}))
    assert check_repo.check_script_paths() == []


def test_bootstrap_marker_without_code_fails(tmp_path, monkeypatch):
    """0.1.442: a marker comment with no sys.path code behind it is a
    vacancy wearing a badge — the guard reads the load-bearing lines now."""
    marker_only = "# --- scripts path " + "bootstrap (canonical) ---\n"
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/consumer.py": marker_only + "import color_math\n",
        "scripts/color_math.py": "def f():\n    return 1\n"}))
    errors = check_repo.check_bootstrap()
    assert len(errors) == 1 and "vacancy" in errors[0]


def test_bootstrap_lib_module_outside_sibling_list_fails(tmp_path, monkeypatch):
    """A new lib/ module whose importers were never checked is enumeration
    rot; the guard now holds SIBLING_MODULES to lib/'s contents."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/lib/brand_new_helper.py": "X = 1\n"}))
    errors = check_repo.check_bootstrap()
    assert any("brand_new_helper" in e and "SIBLING_MODULES" in e
               for e in errors)


def test_waiver_covers_one_citation_not_the_file(tmp_path, monkeypatch):
    """0.1.442: waiving one illustrative mention must not exempt the rest
    of the file (the emergency runbook was entirely unguarded before)."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "threat.md": "imagine scripts/hijack.py; but scripts/also_gone.py "
                     "is a REAL dangling mention\n"}))
    monkeypatch.setitem(check_repo.SCRIPT_PATH_WAIVERS,
                        ("threat.md", "scripts/hijack.py"), "illustration")
    errors = check_repo.check_script_paths()
    assert len(errors) == 1 and "also_gone" in errors[0]


# check_shape_library asked the FILESYSTEM. It globbed assets/shapes/*.svg,
# found 206 files, and passed while .gitignore excluded every one of them — the
# library existed on one machine and in no clone. It now asks git, so these
# trees are real repositories and the difference between "on disk" and
# "shipped" is expressible.

_TAGS = ('{"schema": 3, "shapes": {"p001-flow-01": '
         '{"relation": "process", "relation_from": "looked-at"}}}')
_SVG = '<svg viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
_EMBEDDER = "LIBRARY = ROOT / 'assets' / 'shapes'\n"


def _shape_repo(tmp_path, ignore="", embedder=True):
    files = {"assets/shapes/tags.json": _TAGS,
             "assets/shapes/p001-flow-01.svg": _SVG,
             ".gitignore": ignore}
    if embedder:
        files["scripts/build/embed_shapes.py"] = _EMBEDDER
    return _repo(tmp_path, files)


def test_shape_library_tracked_library_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _shape_repo(tmp_path))
    assert check_repo.check_shape_library() == []


def test_shape_library_untracked_unit_is_not_shipped(tmp_path, monkeypatch):
    """The live defect, in miniature: the file is on disk and git ignores it."""
    # `git add -A` never stages it, because .gitignore excludes it. The file
    # is on disk and in no clone — which is the whole defect, reproduced.
    root = _shape_repo(tmp_path, ignore="*.svg\n")
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert any("p001-flow-01" in e and "not shipped" in e
               for e in check_repo.check_shape_library())


def test_shape_library_deleted_library_fails_while_its_build_step_ships(
        tmp_path, monkeypatch):
    """`git rm -r assets/shapes` used to pass the whole of check_repo."""
    root = _repo(tmp_path, {"scripts/build/embed_shapes.py": _EMBEDDER})
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert any("does not exist" in e for e in check_repo.check_shape_library())


def test_shape_library_absent_with_no_build_step_is_still_a_legal_state(
        tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {"README.md": "x\n"}))
    assert check_repo.check_shape_library() == []


# check_trace_schema had no test of its own. Its docstring and its CHANGELOG
# entry both claimed "the synthetic tests are what prove this can fail" — but
# that deliberate-red was run against trace_schema.validate, the LIBRARY. The
# guard's own layer (the directory walk, the JSON parse, the vacuity floor)
# survived being replaced with `return []` and the whole suite stayed green.
# FM-01, recorded as prevented in the entry that introduced it.

def _trace_repo(tmp_path, traces):
    files = dict(traces)
    return _repo(tmp_path, files)


def _legal_trace():
    import trace_schema
    rec = dict.fromkeys(trace_schema.FIELDS)
    rec.update(trace_id="t-0123456789ab", opened_at="2026-08-17T00:00:00+00:00",
               closed_at=None, source="build", skill_version="0.1.497",
               genre="internal", storyline="proposal", entry_path="B",
               outline_reviewed=False, titles_changed_after_approval=0,
               geometry="16x9", pages=0, content_pages=0, phase_seconds={},
               gates={}, graded={}, thresholds={}, principle_yields=[],
               refused_to_emit=None)
    return rec


def test_trace_schema_guard_passes_on_a_legal_stored_trace(tmp_path, monkeypatch):
    import json as _json
    monkeypatch.setattr(check_repo, "ROOT", _trace_repo(
        tmp_path, {"evals/traces/t-0123456789ab.json": _json.dumps(_legal_trace())}))
    assert check_repo.check_trace_schema() == []


def test_trace_schema_guard_fails_on_a_stored_trace_carrying_free_text(
        tmp_path, monkeypatch):
    import json as _json
    rec = _legal_trace()
    rec["note"] = "the client asked for this in a hurry"
    monkeypatch.setattr(check_repo, "ROOT", _trace_repo(
        tmp_path, {"evals/traces/t-0123456789ab.json": _json.dumps(rec)}))
    errors = check_repo.check_trace_schema()
    assert errors and any("t-0123456789ab" in e for e in errors)


def test_trace_schema_guard_fails_on_a_stored_trace_that_does_not_parse(
        tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _trace_repo(
        tmp_path, {"evals/traces/t-0123456789ab.json": "{not json"}))
    assert check_repo.check_trace_schema()


def test_trace_schema_guard_no_traces_is_a_legal_state(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _trace_repo(tmp_path, {}))
    assert check_repo.check_trace_schema() == []


# check_trace_field_readers — a field nobody reads is worse than an absent one,
# because it looks like coverage. `entry_path` was the case: the owner ruled
# that entry path B is held to the current constitution, trace.py wrote the
# field faithfully, and ledger.py read eleven fields and never that one. The
# rule had no consumer, so it could not be true or false about anything.

def _field_repo(tmp_path, fields, reader_text):
    schema = ("FIELDS = {" + ", ".join(f'"{f}": str' for f in fields) + "}\n")
    return _repo(tmp_path, {"scripts/lib/trace_schema.py": schema,
                            "scripts/ops/trace.py": "# the writer\n",
                            "scripts/ops/ledger.py": reader_text})


def test_field_readers_every_field_read_passes(tmp_path, monkeypatch):
    import trace_schema
    monkeypatch.setattr(trace_schema, "FIELDS", {"alpha": str, "beta": str})
    monkeypatch.setattr(check_repo, "ROOT",
                        _field_repo(tmp_path, ["alpha", "beta"],
                                    'x = rec["alpha"] + rec["beta"]\n'))
    assert check_repo.check_trace_field_readers() == []


def test_field_readers_a_write_only_field_fails_by_name(tmp_path, monkeypatch):
    import trace_schema
    monkeypatch.setattr(trace_schema, "FIELDS", {"alpha": str, "entry_path": str})
    monkeypatch.setattr(check_repo, "ROOT",
                        _field_repo(tmp_path, ["alpha", "entry_path"],
                                    'x = rec["alpha"]\n'))
    errors = check_repo.check_trace_field_readers()
    assert any("entry_path" in e for e in errors)
    assert not any("'alpha'" in e for e in errors)


def test_field_readers_the_writer_itself_is_not_a_reader(tmp_path, monkeypatch):
    """trace.py writes every field; counting it would make the guard vacuous."""
    import trace_schema
    monkeypatch.setattr(trace_schema, "FIELDS", {"solo": str})
    root = _repo(tmp_path, {"scripts/lib/trace_schema.py": 'FIELDS = {"solo": str}\n',
                            "scripts/ops/trace.py": 'rec["solo"] = 1\n',
                            "scripts/ops/ledger.py": "# reads nothing\n"})
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert any("solo" in e for e in check_repo.check_trace_field_readers())


def test_field_readers_empty_schema_is_not_a_vacuous_pass(tmp_path, monkeypatch):
    import trace_schema
    monkeypatch.setattr(trace_schema, "FIELDS", {})
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {"a.py": "x=1\n"}))
    assert check_repo.check_trace_field_readers()
