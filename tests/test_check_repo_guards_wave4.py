"""Wave 4: the reorganization's enabling guards, both directions."""
import json as _json
import subprocess

import check_repo
import trace_schema

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


# The shape manifest described 206 files that existed on nobody's machine, and
# 70 of its records were written in a language the repository's first red line
# forbids. Both were invisible: one guard read only the SVGs, the other read
# only markdown.

def test_shape_library_a_manifest_path_the_package_does_not_ship_fails(
        tmp_path, monkeypatch):
    tags = ('{"schema": 3, "shapes": {"p001-flow-01": {"relation": "process", '
            '"relation_from": "looked-at", "preview": "previews/p001-flow-01.png"}}}')
    root = _repo(tmp_path, {"assets/shapes/tags.json": tags,
                            "assets/shapes/p001-flow-01.svg": _SVG,
                            "scripts/build/embed_shapes.py": _EMBEDDER})
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert any("does not ship" in e for e in check_repo.check_shape_library())


def test_shape_library_a_note_containing_a_slash_is_not_a_path(
        tmp_path, monkeypatch):
    """The first version of this matched on the slash alone and read a note —
    'illustrative / draft / for discussion only' — as a filename."""
    tags = ('{"schema": 3, "shapes": {"p001-flow-01": {"relation": "process", '
            '"relation_from": "looked-at", '
            '"note": "illustrative / draft / for discussion only stamps"}}}')
    root = _repo(tmp_path, {"assets/shapes/tags.json": tags,
                            "assets/shapes/p001-flow-01.svg": _SVG,
                            "scripts/build/embed_shapes.py": _EMBEDDER})
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert check_repo.check_shape_library() == []


def test_english_only_reaches_a_tracked_json_manifest(tmp_path, monkeypatch):
    """`check_stale_promises` learned this one guard over and the lesson was
    not carried across: every text scan here globbed *.md."""
    root = _repo(tmp_path, {"assets/shapes/tags.json":
                            '{"shapes": {"a": {"note": "\\u6837\\u5f0f\\u952e"}}}'})
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert any("tags.json" in e for e in check_repo.check_english_only())


def test_english_only_leaves_an_allowlisted_manifest_alone(tmp_path, monkeypatch):
    """A bilingual geography registry's `z` field is the string a Chinese
    reader sees on the map. Deleting it would not make the repo more English;
    it would make the Chinese map wrong."""
    root = _repo(tmp_path, {"assets/vectors/regions.json":
                            '{"regions":[{"n":"North America","z":"\\u5317\\u7f8e"}]}'})
    monkeypatch.setattr(check_repo, "ROOT", root)
    assert check_repo.check_english_only() == []


# --- the ground's contrast ceiling, held to tokens/ --------------------------
#
# 1.40 is written in six places and nothing joined them. The register now
# records that two rules state it for every page and neither knew about the
# other; this is the mechanical half of the same finding.

def _ground_tree(tmp_path, *, shipped="1.40", code="1.40", brand="1.40:1",
                 rules="1.40:1", layouts="1.40:1"):
    return _repo(tmp_path, {
        "tokens/lumi-theme.css": f"  --ground-ceiling: {shipped};\n",
        "scripts/check/inspect_layout.py": f"GROUND_CEILING = {code}\n",
        "references/brand.md": f"It may never exceed **{brand}** against its canvas\n",
        "references/design-rules.md": f"require it under {rules} against the canvas\n",
        "tokens/lumi-layouts.css": f"it never exceeds --ground-ceiling ({layouts})\n"})


def test_ground_ceiling_agreeing_everywhere_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _ground_tree(tmp_path))
    assert check_repo.check_ground_ceiling() == []


def test_ground_ceiling_drifting_in_the_checker_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _ground_tree(tmp_path, code="1.55"))
    errors = check_repo.check_ground_ceiling()
    assert len(errors) == 1 and "1.55" in errors[0]


def test_ground_ceiling_drifting_in_the_prose_fails(tmp_path, monkeypatch):
    # The measured case: the value moves in tokens/ and a prose copy keeps the
    # old number, which is this repository's most fixed defect class.
    monkeypatch.setattr(check_repo, "ROOT",
                        _ground_tree(tmp_path, shipped="1.35", code="1.35"))
    errors = check_repo.check_ground_ceiling()
    assert len(errors) == 3, errors
    assert all("1.35" in e for e in errors)


def test_ground_ceiling_with_no_token_is_a_finding_not_a_pass(tmp_path,
                                                              monkeypatch):
    tree = _ground_tree(tmp_path)
    (tree / "tokens" / "lumi-theme.css").write_text("  --ink: #000;\n")
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert "no --ground-ceiling" in check_repo.check_ground_ceiling()[0]


# --- the gate register agrees with the checkers, or it is a second copy ------
#
# `check_rule_coverage` holds the RULE register to `gating`'s reader; this holds
# the GATE register to the checkers' own row tables. A register nobody compares
# is a second copy of a contract, and a second copy is what put
# `M4zh_banned_hits` in one reader's gate set and not another's.

def _gate_tree(tmp_path, gates, design_rows='("D9_x", 1, "=0 (gates)", True, False)',
               layout_names=("collision",)):
    import json
    adds = "\n".join(f'    add("{n}", 1, "why")' for n in layout_names)
    return _repo(tmp_path, {
        "SKILL.md": "stub\n",
        "evals/gates.json": json.dumps({"schema": 1, "gates": gates}),
        "scripts/check/check_design.py": f"rows.append({design_rows})\n",
        "scripts/check/check_prose.py": "rows = []\n",
        "scripts/check/inspect_layout.py":
            "def deliverable_verdicts(r):\n    out = {}\n" + adds + "\n    return out\n",
    })


D9 = {"checker": "design", "family": "layout-vocabulary", "severity": "gate",
      "since": "always"}
COLL = {"checker": "layout", "family": "fit", "severity": "gate", "since": "always"}


def test_gate_declarations_agreeing_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _gate_tree(tmp_path, {"D9_x": D9, "collision": COLL}))
    assert check_repo.check_gate_declarations() == []


def test_a_register_that_downgrades_a_gate_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _gate_tree(
        tmp_path, {"D9_x": dict(D9, severity="reported"), "collision": COLL}))
    errors = check_repo.check_gate_declarations()
    assert len(errors) == 1 and "severity" in errors[0]


def test_a_gate_the_register_never_heard_of_fails(tmp_path, monkeypatch):
    """The case that matters: somebody adds a gate to a checker and the register
    stays behind. A register that merely LISTS can be silently incomplete."""
    monkeypatch.setattr(check_repo, "ROOT", _gate_tree(tmp_path, {"D9_x": D9}))
    errors = check_repo.check_gate_declarations()
    assert len(errors) == 1 and "collision" in errors[0]


def test_a_register_naming_a_withdrawn_gate_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _gate_tree(
        tmp_path, {"D9_x": D9, "collision": COLL, "D99_gone": dict(D9)}))
    errors = check_repo.check_gate_declarations()
    assert len(errors) == 1 and "D99_gone" in errors[0]


def test_an_f_string_target_is_read_for_its_literal_parts(tmp_path, monkeypatch):
    """The guard's OWN first run got this wrong: reading only `ast.Constant`
    made two rows whose targets interpolate a threshold look `graded` when
    their literal text says `(reported)`. The guard was the half that was
    wrong."""
    monkeypatch.setattr(check_repo, "ROOT", _gate_tree(
        tmp_path,
        {"D9_x": dict(D9, severity="reported"), "collision": COLL},
        design_rows='("D9_x", 1, f">={T:g}% (reported)", True, False)'))
    assert check_repo.check_gate_declarations() == []


def test_an_empty_register_does_not_pass_by_agreeing_with_nothing(tmp_path,
                                                                  monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _gate_tree(tmp_path, {}))
    errors = check_repo.check_gate_declarations()
    assert errors and "declares nothing" in errors[0]


def test_the_privacy_gate_is_checked_where_its_gating_actually_lives(tmp_path,
                                                                     monkeypatch):
    """`check_privacy` fits no row table — it reports one `verdict` per FILE —
    and `check_deliverable` promotes a non-ok one into the gating bucket in
    code. So its parity is asserted against that promotion. Rename the
    promotion and the register is declaring a gate nothing emits."""
    tree = _gate_tree(tmp_path, {
        "D9_x": D9, "collision": COLL,
        "privacy_terms": {"checker": "privacy", "family": "handling-terms",
                          "severity": "gate", "since": "always"}})
    promoter = tree / "scripts" / "ops"
    promoter.mkdir(parents=True, exist_ok=True)
    (promoter / "check_deliverable.py").write_text(
        'if kind == "privacy":\n    gating.append("x")\n')
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert check_repo.check_gate_declarations() == []

    (promoter / "check_deliverable.py").write_text(
        'if kind == "PRIVACY_RENAMED":\n    gating.append("x")\n')
    errors = check_repo.check_gate_declarations()
    assert len(errors) == 1 and "privacy_terms" in errors[0]


# --- trace field writers: a declared field must record something ----------
# The mirror of `trace field readers`. Fill rate over stored traces, not static
# analysis of writers — the red-team review killed the static method. A field
# empty on every trace, not in ADDED_LATER, unwaived → red. Dead waivers (a
# waived field now filled, or gone from FIELDS) → red too. FM-24: no FIELDS,
# WAIVERS not a dict, or an empty store each fail rather than pass vacuously.


def _trace_tree(tmp_path, traces):
    """A ROOT whose evals/traces holds the given records (list of dicts)."""
    d = tmp_path / "evals" / "traces"
    d.mkdir(parents=True, exist_ok=True)
    for i, rec in enumerate(traces):
        (d / f"t-{i:012x}.json").write_text(_json.dumps(rec))
    return tmp_path


def _full_record(**over):
    """A record with every FIELDS key filled with a plausible non-empty value,
    so the guard sees full coverage unless a test empties a field."""
    rec: dict[str, object] = {}
    for f, typ in trace_schema.FIELDS.items():
        rec[f] = 1 if typ is int or typ == (int, type(None)) else \
            [] if typ is list else {} if typ is dict else f"{f}-val"
    # lists/dicts must be NON-empty to count as filled
    for f, typ in trace_schema.FIELDS.items():
        if typ is list:
            rec[f] = ["x"]
        elif typ is dict:
            rec[f] = {"x": 1}
    rec.update(over)
    return rec


def test_trace_writers_full_coverage_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _trace_tree(tmp_path, [_full_record()]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {})
    assert check_repo.check_trace_field_writers() == []


def test_trace_writers_empty_field_without_waiver_is_red(tmp_path, monkeypatch):
    # principle_yields empty on every trace, no waiver -> names it.
    rec = _full_record(principle_yields=[])
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, [rec]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {})
    errors = check_repo.check_trace_field_writers()
    assert any("principle_yields" in e and "records nothing" in e for e in errors)


def test_trace_writers_empty_field_with_waiver_passes(tmp_path, monkeypatch):
    rec = _full_record(principle_yields=[])
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, [rec]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS",
                        {"principle_yields": "waited on the --assess hook"})
    assert check_repo.check_trace_field_writers() == []


def test_trace_writers_dead_waiver_on_filled_field_is_red(tmp_path, monkeypatch):
    # genre is filled, but a waiver claims it is empty -> dead waiver.
    monkeypatch.setattr(check_repo, "ROOT",
                        _trace_tree(tmp_path, [_full_record()]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {"genre": "stale"})
    errors = check_repo.check_trace_field_writers()
    assert any("genre" in e and "filled" in e for e in errors)


def test_trace_writers_dead_waiver_on_missing_field_is_red(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _trace_tree(tmp_path, [_full_record()]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {"ghost_field": "stale"})
    errors = check_repo.check_trace_field_writers()
    assert any("ghost_field" in e and "no longer declares" in e for e in errors)


def test_trace_writers_added_later_field_is_skipped(tmp_path, monkeypatch):
    # A field in ADDED_LATER empty on every trace is an honest absence, not red.
    added = next(iter(trace_schema.ADDED_LATER))
    rec = _full_record(**{added: None})
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, [rec]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {})
    errors = check_repo.check_trace_field_writers()
    assert not any(f"{added!r}" in e for e in errors)


def test_trace_writers_empty_store_is_a_finding(tmp_path, monkeypatch):
    # FM-24: scanning zero traces is not a clean tree.
    (tmp_path / "evals" / "traces").mkdir(parents=True)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {})
    errors = check_repo.check_trace_field_writers()
    assert errors and "scans nothing" in errors[0]


def test_trace_writers_waivers_not_a_dict_is_a_finding(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _trace_tree(tmp_path, [_full_record()]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", None)
    errors = check_repo.check_trace_field_writers()
    assert errors and "not a dict" in errors[0]


def test_trace_writers_falsy_field_value_is_not_empty(tmp_path, monkeypatch):
    # A recorded 0 / False is DATA, not absence. outline_reviewed=False on every
    # trace, titles_changed_after_approval=0 on every trace — both faithfully
    # written; the guard must NOT flag them. (Regression: the first emptiness
    # test treated falsy scalars as empty and reddened these on a normal corpus.)
    rec = _full_record(outline_reviewed=False, titles_changed_after_approval=0)
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, [rec]))
    monkeypatch.setattr(trace_schema, "WRITER_WAIVERS", {})
    errors = check_repo.check_trace_field_writers()
    assert not any("outline_reviewed" in e for e in errors)
    assert not any("titles_changed_after_approval" in e for e in errors)


def test_trace_writers_no_fields_is_a_finding(tmp_path, monkeypatch):
    # FM-24 fourth branch: FIELDS absent → fail, not a vacuous pass.
    monkeypatch.setattr(check_repo, "ROOT",
                        _trace_tree(tmp_path, [_full_record()]))
    monkeypatch.setattr(trace_schema, "FIELDS", {})
    errors = check_repo.check_trace_field_writers()
    assert errors and "no FIELDS" in errors[0]
