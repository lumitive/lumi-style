"""Seven more check_repo guards proven able to pass AND to fail on synthetic trees.

Wave 2 of the discipline test_check_repo_guards.py establishes: every guard gets
a passing tree and at least one failing tree per exercised failure mode, because
a guard tested only against the live repo cannot demonstrate that a rewritten
`return []` would be noticed. All seven guards here have a file surface small
enough to synthesize fully, so none needs the mutated-real-repo fallback.
Module-level tables bound at import from the real ROOT — PLATFORMS and the
waiver dicts — are monkeypatched alongside ROOT; the guard logic under test is
unchanged.
"""
import json

import check_repo

# check_output_default — every declared site names the same literal directory.

def _output_tree(tmp_path, folder="LUMI-Style", omit=None, blank=None):
    statement = "Deliverables default to ~/Documents/LUMI-Style unless the user says otherwise.\n"
    for name in ("references/design-rules.md", "SKILL.md", "AGENTS.md",
                 "prompts/lumi-style-core.md"):
        if name == omit:
            continue
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("The default is described but never named here.\n"
                        if name == blank else statement)
    scripts = tmp_path / "scripts" / "ops"
    scripts.mkdir(parents=True)
    (scripts / "output_dir.py").write_text(
        f'DOCUMENTS = "Documents"\nFOLDER = "{folder}"\n')
    return tmp_path


def test_output_default_agreeing_sites_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _output_tree(tmp_path))
    assert check_repo.check_output_default() == []


def test_output_default_missing_site_fails_rather_than_skipping(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _output_tree(tmp_path, omit="AGENTS.md"))
    errors = check_repo.check_output_default()
    assert len(errors) == 1
    assert "AGENTS.md" in errors[0] and "missing" in errors[0]


def test_output_default_site_without_the_literal_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _output_tree(tmp_path, blank="SKILL.md"))
    errors = check_repo.check_output_default()
    assert len(errors) == 1
    assert "SKILL.md" in errors[0] and "without naming" in errors[0]


def test_output_default_diverging_resolver_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _output_tree(tmp_path, folder="Deliverables"))
    errors = check_repo.check_output_default()
    assert len(errors) == 1
    assert "scripts/ops/output_dir.py" in errors[0]
    assert "Documents/Deliverables" in errors[0]


# check_stale_promises — a future-tense sentence may not name a shipped release.
# PLATFORMS is bound at import from the real ROOT, so it is repointed too: the
# registry is deliberately part of this guard's scan surface.

def _promise_tree(tmp_path, monkeypatch, notes, registry_note="nothing pending"):
    (tmp_path / "CHANGELOG.md").write_text("## 0.1.1\n\n- shipped.\n")
    (tmp_path / "notes.md").write_text(notes)
    adapters = tmp_path / "adapters"
    adapters.mkdir()
    platforms = adapters / "platforms.json"
    platforms.write_text(json.dumps({"platforms": [{"id": "x", "note": registry_note}]}))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "PLATFORMS", platforms)


def test_stale_promises_retrospective_and_unshipped_future_pass(tmp_path, monkeypatch):
    _promise_tree(tmp_path, monkeypatch,
                  "Carried over from 0.1.1, where it shipped.\n"
                  "The rest is planned for 0.9.9.\n")
    assert check_repo.check_stale_promises() == []


def test_stale_promises_shipped_version_in_future_tense_fails(tmp_path, monkeypatch):
    _promise_tree(tmp_path, monkeypatch, "A fix will land in 0.1.1.\n")
    errors = check_repo.check_stale_promises()
    assert len(errors) == 1
    assert "notes.md:1" in errors[0] and "promises work in 0.1.1" in errors[0]


def test_stale_promises_registry_json_is_scanned_too(tmp_path, monkeypatch):
    _promise_tree(tmp_path, monkeypatch, "Prose is clean.\n",
                  registry_note="loader support planned for 0.1.1")
    errors = check_repo.check_stale_promises()
    assert len(errors) == 1
    assert "adapters/platforms.json" in errors[0]


# check_platform_manifest — every claim has a file behind it, every unverified
# claim carries a waiver, and no install note is orphaned.

def _platform_record(**over):
    record = {
        "id": "claude-code",
        "capability": "full",
        "entry_file": "SKILL.md",
        "notes_path": "adapters/claude-code.md",
        "path_verified": True,
        "docs": "https://example.invalid/docs",
        "probe": ["claude", "--version"],
        # A vocabulary state since 0.1.619: what the agent can be RUN AS is
        # claimed the same way as whether it is there at all. The real
        # `claude-code` record carries the waiver rather than the argv, because
        # that CLI has no listing command; this fixture carries the argv so the
        # positive branch is the one under test here.
        "models": ["claude", "--list-models"],
        "capability_verified": True,
    }
    record.update(over)
    return record


def _manifest_tree(tmp_path, monkeypatch, records=None, orphan=None):
    (tmp_path / "SKILL.md").write_text("entry\n")
    adapters = tmp_path / "adapters"
    adapters.mkdir()
    (adapters / "claude-code.md").write_text("install note\n")
    if orphan:
        (adapters / orphan).write_text("nobody claims this\n")
    data = {
        "capabilities": {"full": {"means": "reads the files and runs scripts/"}},
        "platforms": records if records is not None else [_platform_record()],
    }
    platforms = adapters / "platforms.json"
    platforms.write_text(json.dumps(data))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "PLATFORMS", platforms)


def test_platform_manifest_fully_verified_record_passes(tmp_path, monkeypatch):
    _manifest_tree(tmp_path, monkeypatch)
    assert check_repo.check_platform_manifest() == []


def test_platform_manifest_missing_entry_file_fails(tmp_path, monkeypatch):
    _manifest_tree(tmp_path, monkeypatch,
                   records=[_platform_record(entry_file="GHOST.md")])
    errors = check_repo.check_platform_manifest()
    assert any("'GHOST.md' does not exist" in e for e in errors)


def test_platform_manifest_unverified_claim_without_waiver_fails(tmp_path, monkeypatch):
    record = _platform_record()
    del record["capability_verified"]
    _manifest_tree(tmp_path, monkeypatch, records=[record])
    errors = check_repo.check_platform_manifest()
    assert len(errors) == 1
    assert "capability tier" in errors[0] and "capability_waiver" in errors[0]


def test_platform_manifest_unverified_claim_with_waiver_passes(tmp_path, monkeypatch):
    record = _platform_record(capability_waiver="never watched an agent run the checkers")
    del record["capability_verified"]
    _manifest_tree(tmp_path, monkeypatch, records=[record])
    assert check_repo.check_platform_manifest() == []


def test_platform_manifest_probe_as_string_fails(tmp_path, monkeypatch):
    _manifest_tree(tmp_path, monkeypatch,
                   records=[_platform_record(probe="claude --version")])
    errors = check_repo.check_platform_manifest()
    assert any("must be a list of strings" in e for e in errors)


def test_platform_manifest_orphan_note_fails(tmp_path, monkeypatch):
    _manifest_tree(tmp_path, monkeypatch, orphan="stray.md")
    errors = check_repo.check_platform_manifest()
    assert len(errors) == 1
    assert "adapters/stray.md" in errors[0] and "no platform" in errors[0]


# check_retired_values — a withdrawn number restated without a withdrawal marker
# is the drift this repo is documented worst at.

def _retired_tree(tmp_path, monkeypatch, doc, retired=None):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    register = [{"value": "82%", "name": "page fill floor", "withdrawn_in": "0.1.340",
                 "context": ["fill floor", "page fill"]}]
    (tokens / "design-tokens.json").write_text(
        json.dumps({"retired": register if retired is None else retired}))
    (tmp_path / "notes.md").write_text(doc)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "RETIRED_VALUE_WAIVERS", {})


def test_retired_values_marked_restatement_and_bare_digits_pass(tmp_path, monkeypatch):
    _retired_tree(tmp_path, monkeypatch,
                  "The 82% page fill floor was withdrawn in 0.1.340.\n"
                  "\n"
                  "A chart in this deck happens to span 82% of its column.\n")
    assert check_repo.check_retired_values() == []


def test_retired_values_unmarked_restatement_fails(tmp_path, monkeypatch):
    _retired_tree(tmp_path, monkeypatch, "Keep every page above the 82% fill floor.\n")
    errors = check_repo.check_retired_values()
    assert len(errors) == 1
    assert "notes.md:1" in errors[0]
    assert "82%" in errors[0] and "without marking it withdrawn" in errors[0]


def test_retired_values_empty_register_fails_rather_than_passing(tmp_path, monkeypatch):
    _retired_tree(tmp_path, monkeypatch, "No floors here.\n", retired=[])
    errors = check_repo.check_retired_values()
    assert len(errors) == 1
    assert "`retired` register is empty" in errors[0]


def test_retired_values_record_without_context_fails(tmp_path, monkeypatch):
    _retired_tree(tmp_path, monkeypatch, "The value 82% appears in passing.\n",
                  retired=[{"value": "82%", "name": "page fill floor",
                            "withdrawn_in": "0.1.340"}])
    errors = check_repo.check_retired_values()
    assert any("no `context` phrases" in e for e in errors)


def test_retired_values_stale_waiver_fails(tmp_path, monkeypatch):
    _retired_tree(tmp_path, monkeypatch, "Nothing restates the floor.\n")
    monkeypatch.setattr(check_repo, "RETIRED_VALUE_WAIVERS",
                        {("notes.md", "82%", "never matches"): "synthetic"})
    errors = check_repo.check_retired_values()
    assert len(errors) == 1
    assert "RETIRED_VALUE_WAIVERS" in errors[0] and "delete the waiver" in errors[0]


# check_token_references — every var() in tokens/ resolves, fallbacks honoured
# recursively, waivers only while their cause is live.

def _tokens_tree(tmp_path, monkeypatch, css):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    if css is not None:
        (tokens / "lumi-theme.css").write_text(css)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "UNDEFINED_VAR_WAIVERS", {})


def test_token_references_resolving_vars_and_fallbacks_pass(tmp_path, monkeypatch):
    _tokens_tree(tmp_path, monkeypatch,
                 ":root { --acc: #0a5c5c; }\n"
                 "h1 { color: var(--acc); }\n"
                 "h2 { transform: rotate(var(--knob, 22deg)); }\n"
                 "h3 { border-color: var(--ghost, var(--acc)); }\n")
    assert check_repo.check_token_references() == []


def test_token_references_undefined_var_without_fallback_fails(tmp_path, monkeypatch):
    _tokens_tree(tmp_path, monkeypatch,
                 ":root { --acc: #0a5c5c; }\n"
                 "p { color: var(--missing); }\n")
    errors = check_repo.check_token_references()
    assert len(errors) == 1
    assert errors[0].startswith("tokens/lumi-theme.css:2")
    assert "var(--missing)" in errors[0]


def test_token_references_empty_tokens_dir_fails_rather_than_vacuously_passing(
        tmp_path, monkeypatch):
    _tokens_tree(tmp_path, monkeypatch, css=None)
    errors = check_repo.check_token_references()
    assert len(errors) == 1
    assert "pass vacuously" in errors[0]


def test_token_references_stale_waiver_fails(tmp_path, monkeypatch):
    _tokens_tree(tmp_path, monkeypatch, ":root { --acc: #0a5c5c; }\n")
    monkeypatch.setattr(check_repo, "UNDEFINED_VAR_WAIVERS", {"--ghost": "synthetic"})
    errors = check_repo.check_token_references()
    assert len(errors) == 1
    assert "UNDEFINED_VAR_WAIVERS excuses --ghost" in errors[0]


# check_region_coverage — every country in exactly one region, every node's
# region defined.

def _region_tree(tmp_path, monkeypatch, members=("AAA", "BBB"), regions=None,
                 nodes=None, write_topo=True):
    vectors = tmp_path / "assets" / "vectors"
    vectors.mkdir(parents=True)
    if write_topo:
        (vectors / "world-110m.json").write_text(
            json.dumps({"countries": [{"a": "AAA"}, {"a": "BBB"}]}))
    registry = {
        "regions": (regions if regions is not None
                    else [{"id": "north", "members": list(members)}]),
        "nodes": nodes if nodes is not None else [{"id": "hub", "region": "north"}],
    }
    (vectors / "regions.json").write_text(json.dumps(registry))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)


def test_region_coverage_complete_partition_passes(tmp_path, monkeypatch):
    _region_tree(tmp_path, monkeypatch)
    assert check_repo.check_region_coverage() == []


def test_region_coverage_unassigned_country_fails(tmp_path, monkeypatch):
    _region_tree(tmp_path, monkeypatch, members=("AAA",))
    errors = check_repo.check_region_coverage()
    assert len(errors) == 1
    assert "BBB belongs to no region" in errors[0]


def test_region_coverage_double_claim_fails(tmp_path, monkeypatch):
    _region_tree(tmp_path, monkeypatch,
                 regions=[{"id": "north", "members": ["AAA", "BBB"]},
                          {"id": "south", "members": ["AAA"]}])
    errors = check_repo.check_region_coverage()
    assert any("AAA is claimed by both north and south" in e for e in errors)


def test_region_coverage_member_outside_topology_fails(tmp_path, monkeypatch):
    _region_tree(tmp_path, monkeypatch, members=("AAA", "BBB", "CCC"))
    errors = check_repo.check_region_coverage()
    assert len(errors) == 1
    assert "names CCC" in errors[0] and "not in the topology" in errors[0]


def test_region_coverage_node_with_unknown_region_fails(tmp_path, monkeypatch):
    _region_tree(tmp_path, monkeypatch, nodes=[{"id": "hub", "region": "ghost"}])
    errors = check_repo.check_region_coverage()
    assert len(errors) == 1
    assert "node hub" in errors[0] and "ghost" in errors[0]


def test_region_coverage_missing_topology_fails(tmp_path, monkeypatch):
    _region_tree(tmp_path, monkeypatch, write_topo=False)
    errors = check_repo.check_region_coverage()
    assert errors == ["assets/vectors/world-110m.json is missing; "
                      "run scripts/build/build_worldmap.py"]


# check_probe_vocabulary — contract selectors must be shipped and unwaivable,
# census selectors shipped or waived with a reason, and D16's two visual
# carriers must agree. The guard reads three sibling scripts by ast/regex plus
# tokens/, so the synthetic tree carries minimal stand-ins for all four;
# PROBE_NOT_SHIPPED is the module-level waiver table and is patched per test.

def _probe_tree(tmp_path, monkeypatch, *, ink="p, h2, .band, .gd", extra_role="",
                visual_blocks=("fig", "band"), waivers=None):
    scripts = tmp_path / "scripts" / "check"
    scripts.mkdir(parents=True)
    (scripts / "inspect_layout.py").write_text(
        'PROBE = """\n'
        "const CENTER = '.cover';\n"
        f"const INK = '{ink}';\n"
        "const TEXT_SEL = 'p, .gd';\n"
        "const DSEL = 'svg, .band';\n"
        "const VIS = '.fig, .band';\n"
        '"""\n'
        'CONSISTENCY_PROBE = """\n'
        "const ROLES = [\n"
        "  ['content title', 'h2.t', []],\n"
        f"  {extra_role}\n"
        "];\n"
        "const SCOPED = [\n"
        "  ['.k', ['.band']]\n"
        "];\n"
        '"""\n')
    (scripts / "check_prose.py").write_text(
        "def extract():\n"
        "    for wrapper, item, kind in ((\"swaps\", \"swap\", \"class\"),\n"
        "                                (\"notes\", \"p\", \"element\")):\n"
        "        pass\n")
    (scripts / "check_design.py").write_text(f"VISUAL_BLOCKS = {visual_blocks!r}\n")
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "lumi-theme.css").write_text(
        ".cover { display: grid; }\n"
        ".band { display: flex; }\n"
        ".gd { border: 1px solid; }\n"
        "h2.t { font-size: 34px; }\n"
        ".k { font-family: monospace; }\n"
        ".fig { display: block; }\n"
        ".swaps { display: grid; }\n"
        ".swap { display: flex; }\n"
        ".notes { font-size: 12px; }\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "PROBE_NOT_SHIPPED", waivers or {})


def test_probe_vocabulary_shipped_vocabulary_passes(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch)
    assert check_repo.check_probe_vocabulary() == []


def test_probe_vocabulary_unshipped_contract_class_fails(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch, extra_role="['ghost role', '.ghost', []],")
    errors = check_repo.check_probe_vocabulary()
    assert len(errors) == 1
    assert "asserts .ghost" in errors[0] and "may not be waived" in errors[0]


def test_probe_vocabulary_unshipped_census_class_fails(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch, ink="p, h2, .band, .gd, .mystery")
    errors = check_repo.check_probe_vocabulary()
    assert len(errors) == 1
    assert ".mystery" in errors[0] and "PROBE_NOT_SHIPPED" in errors[0]


def test_probe_vocabulary_waived_census_class_passes(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch, ink="p, h2, .band, .gd, .mystery",
                waivers={"mystery": "synthetic waiver for this test"})
    assert check_repo.check_probe_vocabulary() == []


def test_probe_vocabulary_orphan_waiver_fails(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch, waivers={"orphaned": "nothing names this"})
    errors = check_repo.check_probe_vocabulary()
    assert len(errors) == 1
    assert ".orphaned" in errors[0] and "no probe names" in errors[0]


def test_probe_vocabulary_waiver_on_shipped_class_fails(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch, waivers={"gd": "shipped since"})
    errors = check_repo.check_probe_vocabulary()
    assert len(errors) == 1
    assert ".gd" in errors[0] and "delete the waiver" in errors[0]


def test_probe_vocabulary_diverged_visual_carriers_fail(tmp_path, monkeypatch):
    _probe_tree(tmp_path, monkeypatch, visual_blocks=("fig",))
    errors = check_repo.check_probe_vocabulary()
    assert len(errors) == 1
    assert "visual vocabulary has diverged" in errors[0]


def test_platform_manifest_a_platform_claiming_no_vocabulary_state_fails(
        tmp_path, monkeypatch):
    """Neither a models probe nor a reason for having none. Twelve platforms
    ship here and eleven cannot enumerate their models — for three DIFFERENT
    reasons (no listing command, an interactive picker, nobody has installed
    it). A record that says nothing publishes those three as one."""
    record = _platform_record()
    del record["models"]
    _manifest_tree(tmp_path, monkeypatch, records=[record])
    errors = check_repo.check_platform_manifest()
    assert len(errors) == 1
    assert "model vocabulary probe" in errors[0] and "models_waiver" in errors[0]


def test_platform_manifest_a_vocabulary_waiver_is_accepted(tmp_path, monkeypatch):
    record = _platform_record(
        models_waiver="`hermes model` opens an interactive picker.")
    del record["models"]
    _manifest_tree(tmp_path, monkeypatch, records=[record])
    assert check_repo.check_platform_manifest() == []


def test_platform_manifest_a_models_probe_written_as_a_string_fails(
        tmp_path, monkeypatch):
    """The same defect the probe field had: a string is indexed character-wise,
    so `argv[0]` is `c` and `shutil.which` reports the agent as absent."""
    _platform = _platform_record(models="claude --list-models")
    _manifest_tree(tmp_path, monkeypatch, records=[_platform])
    errors = check_repo.check_platform_manifest()
    assert any("models must be a list of strings" in e for e in errors)


# check_version_citations and the second scoreboard. A CLI build id like
# `2026.08.25-3e8eec8` is three dot-separated numbers, so the guard's pattern
# reads it as a release this repository never made. `CONFIGURATIONS.md` gained
# a `cli` column at 0.1.626 and reddened the release that added it.

def _citation_tree(tmp_path, monkeypatch, files):
    (tmp_path / "CHANGELOG.md").write_text(
        "## 0.1.626 — a heading\n\nbody\n", encoding="utf-8")
    for rel_path, text in files.items():
        target = tmp_path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "md_files",
                        lambda: [tmp_path / p for p in files])
    # This guard also checks that every ENTRY_STAMP file exists, and a
    # synthetic tree has none of them. Narrowed to the citation half rather
    # than stubbing the other, so a change to either is still visible here.
    return [e for e in check_repo.check_version_citations() if "cites version" in e]


def test_a_cli_build_in_a_scoreboard_row_is_not_read_as_a_release(
        tmp_path, monkeypatch):
    errors = _citation_tree(tmp_path, monkeypatch, {
        "conformance/CONFIGURATIONS.md":
            "# board\n\n| cursor | m | high | 0.1.626 | 2026.08.25-3e8eec8 |\n"})
    assert errors == [], errors


def test_the_same_build_id_in_prose_still_fails(tmp_path, monkeypatch):
    """Scoped to table rows, not to the file. Exempting the whole file would
    also exempt a genuine miscitation in its prose — which is the mistake the
    CONFORMANCE.md entry's own comment records having made once."""
    errors = _citation_tree(tmp_path, monkeypatch, {
        "conformance/CONFIGURATIONS.md":
            "# board\n\nmeasured against skill 2026.08.25 throughout\n"})
    assert errors and "2026.08.25" in errors[0]


# check_trace_notes — the operator's sidecar. Hand-edited on purpose, which is
# exactly why it is guarded: a note keyed to an id nobody recorded is a note
# about nothing, and a third key is a schema invented in a text editor.

def _notes_tree(tmp_path, monkeypatch, doc, trace_ids=("t-0123456789ab",)):
    (tmp_path / "evals" / "traces").mkdir(parents=True)
    for tid in trace_ids:
        (tmp_path / "evals" / "traces" / f"{tid}.json").write_text(
            "{}", encoding="utf-8")
    if doc is not None:
        (tmp_path / "evals" / "trace-notes.json").write_text(
            json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    return check_repo.check_trace_notes()


def test_trace_notes_absent_is_a_legal_state(tmp_path, monkeypatch):
    """A store with no notes is the normal starting condition."""
    assert _notes_tree(tmp_path, monkeypatch, None) == []


def test_trace_notes_a_well_formed_entry_passes(tmp_path, monkeypatch):
    assert _notes_tree(tmp_path, monkeypatch, {
        "t-0123456789ab": {"note": "why this run", "tags": ["r19"]}}) == []


def test_trace_notes_an_id_with_no_trace_fails(tmp_path, monkeypatch):
    errors = _notes_tree(tmp_path, monkeypatch,
                         {"t-ffffffffffff": {"note": "about nothing"}})
    assert errors and "names no trace" in errors[0]


def test_trace_notes_a_third_key_fails(tmp_path, monkeypatch):
    errors = _notes_tree(tmp_path, monkeypatch,
                         {"t-0123456789ab": {"verdict": "pass"}})
    assert errors and "invented in an editor" in errors[0]


def test_trace_notes_a_mistyped_note_fails(tmp_path, monkeypatch):
    errors = _notes_tree(tmp_path, monkeypatch, {"t-0123456789ab": {"note": 12}})
    assert errors and "a sentence a person wrote" in errors[0]


def test_trace_notes_mistyped_tags_fail(tmp_path, monkeypatch):
    errors = _notes_tree(tmp_path, monkeypatch,
                         {"t-0123456789ab": {"tags": "r19"}})
    assert errors and "a list of labels" in errors[0]


def test_trace_notes_a_key_that_is_not_a_trace_id_fails(tmp_path, monkeypatch):
    errors = _notes_tree(tmp_path, monkeypatch, {"whatever": {"note": "x"}})
    assert errors and "is not a trace id" in errors[0]


def test_trace_notes_that_do_not_parse_are_a_finding_not_a_silence(
        tmp_path, monkeypatch):
    (tmp_path / "evals" / "traces").mkdir(parents=True)
    (tmp_path / "evals" / "trace-notes.json").write_text("{not json",
                                                         encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_trace_notes()
    assert errors and "hand-edited" in errors[0]


# THE SIDECAR'S LANGUAGE EXEMPTION IS NARROW, and narrowness is the whole
# point: `note` is a sentence the owner writes in the language she thinks in;
# `tags` are labels a machine groups by. Widening it to the FILE re-creates the
# hole 0.1.631 nearly opened, when a prose field inside a trace would have
# falsified the reason `evals/traces/` is skipped at all.

def _english_tree(tmp_path, monkeypatch, notes_doc):
    import subprocess
    (tmp_path / "evals" / "traces").mkdir(parents=True)
    (tmp_path / "evals" / "trace-notes.json").write_text(
        json.dumps(notes_doc, ensure_ascii=False), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    return check_repo.check_english_only()


def test_a_chinese_note_in_the_sidecar_is_allowed(tmp_path, monkeypatch):
    errors = _english_tree(tmp_path, monkeypatch,
                           {"t-0123456789ab": {"note": "四档基准的 high 档"}})
    assert errors == [], errors


def test_a_chinese_tag_in_the_sidecar_is_still_refused(tmp_path, monkeypatch):
    """A label is grouped by a machine and compared across runs. The exemption
    covers the sentence and nothing else."""
    errors = _english_tree(tmp_path, monkeypatch,
                           {"t-0123456789ab": {"tags": ["基准"]}})
    assert errors and "tags" in errors[0]


def test_a_chinese_value_under_an_invented_key_is_refused(tmp_path, monkeypatch):
    """A key this guard has never heard of gets no exemption. `check_trace_notes`
    refuses the key separately; neither guard may be the only one looking."""
    errors = _english_tree(tmp_path, monkeypatch,
                           {"t-0123456789ab": {"note": "ok", "comment": "中文"}})
    assert errors and "comment" in errors[0]
