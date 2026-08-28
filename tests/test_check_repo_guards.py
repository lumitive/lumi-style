"""check_repo guards proven able to pass AND to fail on synthetic trees.

How many is whatever this file covers today, never a number written here — a
count in a docstring is the drift this repository has fixed twenty-six times.

Same discipline as test_one_home.py: a guard tested only against the
live repo cannot demonstrate that a rewritten `return []` would be noticed,
and this repo has shipped exactly that defect (CHANGELOG 0.1.390). Every
guard here gets a passing tree and at least one failing tree per mode.
"""
import json
import subprocess

import check_repo

V = "0.1.1"


# check_versions — the five hand-stamped locations must agree.

def _version_tree(tmp_path, theme_version=V, json_header=f"LUMI design tokens v{V}"):
    (tmp_path / "SKILL.md").write_text(f'---\nversion: "{V}"\n---\n')
    (tmp_path / "CHANGELOG.md").write_text(f"## {V}\n\n- first.\n")
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "lumi-theme.css").write_text(f"/* LUMI visual theme · v{theme_version} */\n")
    # check_versions only regex-searches this file's text, so a stub suffices.
    (tokens / "design-tokens.json").write_text(json.dumps({"_comment": json_header}))
    (tokens / "lumi-layouts.css").write_text(f"/* LUMI page layouts · v{V} */\n")
    return tmp_path


def test_versions_agreeing_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _version_tree(tmp_path))
    assert check_repo.check_versions() == []


def test_versions_diverging_stamp_fails_naming_the_file(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _version_tree(tmp_path, theme_version="0.9.9"))
    errors = check_repo.check_versions()
    assert errors
    assert any("tokens/lumi-theme.css" in e and "0.9.9" in e for e in errors)


def test_versions_missing_stamp_fails_rather_than_skipping(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _version_tree(tmp_path, json_header="LUMI design tokens, unstamped"))
    errors = check_repo.check_versions()
    assert any("tokens/design-tokens.json" in e and "no version stamp" in e for e in errors)


# check_english_only — CJK outside the allowlist and outside code spans fails.

def test_english_only_english_tree_passes(tmp_path, monkeypatch):
    # Backticked CJK in a non-allowlisted file is quoted rule data, not prose.
    (tmp_path / "README.md").write_text("All prose is English. `赋能` is quoted data.\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_english_only() == []


def test_english_only_cjk_prose_fails(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text("Fine line.\n这是中文散文。\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_english_only()
    assert len(errors) == 1
    assert "README.md:2" in errors[0] and "CJK in prose" in errors[0]


def test_english_only_allowlisted_files_do_not_trip(tmp_path, monkeypatch):
    (tmp_path / "AGENTS.md").write_text("规则数据可以是中文。\n")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "lumi-style-core.md").write_text("这里也允许中文。\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_english_only() == []


# check_palette_parity — the parity half; the contrast floor is tested elsewhere.

def _palette_tree(tmp_path, acc_css="#0a5c5c", extra_key=None):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    palette = {
        "bg": "#ffffff",
        "card_bg": "#f7f7f7",
        "accent": "#0a5c5c",
        "ladder_base": "rgba(20,20,20,ALPHA)",
        "text_ladder": [0.95],
        "rule_ladder": [0.2],
    }
    if extra_key:
        palette[extra_key] = "#123456"
    (tokens / "design-tokens.json").write_text(json.dumps(
        {"palette": {"light": palette}, "contrast": {"floor_text": 4.5}}))
    (tokens / "lumi-theme.css").write_text(
        ":root {\n"
        "  --bg: #ffffff;\n"
        "  --card-bg: #f7f7f7;\n"
        f"  --acc: {acc_css};\n"
        "  --tx1: rgba(20,20,20,0.95);\n"
        "  --ln1: rgba(20,20,20,0.2);\n"
        "}\n"
        "body.dark {\n}\n")
    return tmp_path


def test_palette_parity_matching_pair_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _palette_tree(tmp_path))
    assert check_repo.check_palette_parity() == []


def test_palette_parity_diverging_hex_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _palette_tree(tmp_path, acc_css="#0b5c5c"))
    errors = check_repo.check_palette_parity()
    assert len(errors) == 1
    assert "palette.light.accent" in errors[0]
    assert "#0a5c5c" in errors[0] and "#0b5c5c" in errors[0]


def test_palette_parity_unmapped_json_key_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _palette_tree(tmp_path, extra_key="mystery"))
    errors = check_repo.check_palette_parity()
    assert any("palette.light.mystery" in e and "no CSS counterpart" in e for e in errors)


def test_palette_parity_mapped_key_missing_var_fails(tmp_path, monkeypatch):
    # "lime" is in PALETTE_KEY_TO_VAR but the synthetic CSS ships no --lime.
    monkeypatch.setattr(check_repo, "ROOT", _palette_tree(tmp_path, extra_key="lime"))
    errors = check_repo.check_palette_parity()
    assert any("--lime is not defined" in e for e in errors)


def test_palette_parity_css_colour_absent_from_json_fails(tmp_path, monkeypatch):
    # The reverse direction (0.1.443): a colour the CSS defines and the JSON
    # never heard of. --acc-live shipped exactly this way for dozens of
    # releases while the guard walked JSON→CSS only.
    tree = _palette_tree(tmp_path)
    css = (tree / "tokens" / "lumi-theme.css").read_text()
    (tree / "tokens" / "lumi-theme.css").write_text(
        css.replace("}\nbody.dark", "  --mystery-green: #3E7A2E;\n}\nbody.dark"))
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_palette_parity()
    assert any("--mystery-green" in e and "both ways" in e for e in errors)


def test_palette_parity_non_colour_css_var_is_not_mirrored(tmp_path, monkeypatch):
    # A type size is not palette; the reverse check reads values, not names.
    tree = _palette_tree(tmp_path)
    css = (tree / "tokens" / "lumi-theme.css").read_text()
    (tree / "tokens" / "lumi-theme.css").write_text(
        css.replace("}\nbody.dark", "  --fs-something: 42px;\n}\nbody.dark"))
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert check_repo.check_palette_parity() == []


# check_version_citations — stamps at their declared position, citations
# resolving to CHANGELOG headings, waivers honored. ENTRY_STAMP and
# the waiver table are data tables bound at import, so they are monkeypatched
# to fit the synthetic tree; the guard logic under test is unchanged.

def _citation_tree(tmp_path, monkeypatch, skill_version=V, extra_md=""):
    (tmp_path / "CHANGELOG.md").write_text(f"## {V}\n\n- first.\n\n## 0.1.0\n\n- zero.\n")
    (tmp_path / "SKILL.md").write_text(f'---\nversion: "{skill_version}"\n---\n')
    adapters = tmp_path / "adapters"
    adapters.mkdir()
    (adapters / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "claude-code", "entry_file": "SKILL.md"}]}))
    if extra_md:
        (tmp_path / "notes.md").write_text(extra_md)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    monkeypatch.setattr(check_repo, "ENTRY_STAMP", {"SKILL.md": r'^\s*version:\s*"{v}"'})


def test_version_citations_valid_tree_passes(tmp_path, monkeypatch):
    _citation_tree(tmp_path, monkeypatch, extra_md=f"Shipped in {V}.\n")
    assert check_repo.check_version_citations() == []


def test_version_citations_undefined_version_fails(tmp_path, monkeypatch):
    _citation_tree(tmp_path, monkeypatch, extra_md="Changed in 0.9.9.\n")
    errors = check_repo.check_version_citations()
    assert len(errors) == 1
    assert "notes.md:1" in errors[0] and "cites version 0.9.9" in errors[0]


def test_version_citations_waived_citation_passes(tmp_path, monkeypatch):
    _citation_tree(tmp_path, monkeypatch, extra_md="Changed in 0.9.9.\n")
    monkeypatch.setattr(check_repo, "VERSION_CITATION_WAIVERS",
                        {"0.9.9": "synthetic waiver for this test"})
    assert check_repo.check_version_citations() == []


def test_version_citations_stale_stamp_fails(tmp_path, monkeypatch):
    # 0.1.0 is a real heading, so the citation half stays legal — only the
    # stamp-position half can catch the stale entry point.
    _citation_tree(tmp_path, monkeypatch, skill_version="0.1.0")
    errors = check_repo.check_version_citations()
    assert len(errors) == 1
    assert "SKILL.md" in errors[0] and f"no {V} version stamp" in errors[0]


# check_links — relative targets must exist; external schemes are not checked.

def test_links_valid_and_external_pass(tmp_path, monkeypatch):
    (tmp_path / "target.md").write_text("here\n")
    (tmp_path / "index.md").write_text(
        "# Top\n[ok](target.md) [anchor](#top) [mail](mailto:a@b.c)\n"
        "[ext](https://example.invalid/never-fetched) [ext2](http://example.invalid/x)\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_links() == []


def test_links_broken_relative_target_fails(tmp_path, monkeypatch):
    (tmp_path / "index.md").write_text("see [gone](missing.md).\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_links()
    assert len(errors) == 1
    assert "index.md:1" in errors[0] and "missing.md" in errors[0]


def test_links_dead_anchor_fails(tmp_path, monkeypatch):
    """0.1.442: anchors resolve too — the class the 0.1.441 Contents blocks
    shipped broken 28 times."""
    (tmp_path / "index.md").write_text("# A Title\n[toc](#0--wrong)\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_links()
    assert len(errors) == 1 and "matches no heading" in errors[0]


def test_links_middle_dot_slug_matches_github(tmp_path, monkeypatch):
    """The exact 0.1.441 bug shape: '0 · Output language' slugs with a
    DOUBLE hyphen on GitHub (the dot vanishes, both spaces survive)."""
    (tmp_path / "index.md").write_text(
        "## 0 · Output language\n[good](#0--output-language)\n")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_links() == []


# check_section_citations — a `<reference>.md §N` citation names a real section.
# P0's reorder proved the need: twenty-one citations pointed at moved sections
# while every guard stayed green, because check_links only sees link syntax.

def _section_citation_tree(tmp_path, citation, *, in_file="SKILL.md"):
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "design-rules.md").write_text(
        "# Design rules\n\n## 1 · Color\n\ntext\n\n### 1.2 · The mark\n\ntext\n\n"
        "## 8 · The verification matrix\n\ntext\n", encoding="utf-8")
    (tmp_path / in_file).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / in_file).write_text(f"prose citing {citation} here\n", encoding="utf-8")
    return tmp_path


def test_section_citations_resolving_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _section_citation_tree(tmp_path, "`references/design-rules.md` §8"))
    assert check_repo.check_section_citations() == []


def test_section_citations_moved_section_fails(tmp_path, monkeypatch):
    """The exact P0 failure: a citation left pointing at the old number."""
    monkeypatch.setattr(check_repo, "ROOT",
                        _section_citation_tree(tmp_path, "`references/design-rules.md` §7"))
    errors = check_repo.check_section_citations()
    assert errors
    assert any("SKILL.md" in e and "§7" in e for e in errors)


def test_section_citations_lettered_section_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _section_citation_tree(tmp_path, "design-rules.md §1d"))
    assert any("§1d" in e for e in check_repo.check_section_citations())


def test_section_citations_changelog_is_exempt(tmp_path, monkeypatch):
    """History cites the numbering that was true when it was written."""
    monkeypatch.setattr(check_repo, "ROOT",
                        _section_citation_tree(tmp_path, "design-rules.md §7", in_file="CHANGELOG.md"))
    assert check_repo.check_section_citations() == []


def test_section_citations_no_references_dir_fails_rather_than_passing(tmp_path, monkeypatch):
    """A guard that finds nothing to check must say so, not report clean."""
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_section_citations()


def test_section_citations_tests_dir_is_exempt(tmp_path, monkeypatch):
    """Fixtures cite broken sections on purpose; the guard must not eat them."""
    monkeypatch.setattr(check_repo, "ROOT",
                        _section_citation_tree(tmp_path, "design-rules.md §7",
                                       in_file="tests/test_x.py"))
    assert check_repo.check_section_citations() == []


# check_principle_trace — every rule family names the clause it serves.

def _trace_tree(tmp_path, serves="P-1", clauses="**P-1 · Brand.** MUST.\n\n**P-2 · Grounded.** MUST.\n"):
    refs = tmp_path / "references"
    refs.mkdir()
    (refs / "PRINCIPLES.md").write_text("# LUMI principles\n\n" + clauses, encoding="utf-8")
    body = "# Rules\n\n## 1 · Colour\n"
    if serves:
        body += f"\n*Serves: **{serves}**.*\n"
    body += "\ntext\n"
    (refs / "design-rules.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_principle_trace_declared_family_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path))
    assert check_repo.check_principle_trace() == []


def test_principle_trace_goal_is_a_legitimate_parent(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, serves="GOAL"))
    assert check_repo.check_principle_trace() == []


def test_principle_trace_orphan_family_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, serves=None))
    assert any("declares no parent" in e for e in check_repo.check_principle_trace())


def test_principle_trace_undefined_clause_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, serves="P-9"))
    assert any("P-9" in e for e in check_repo.check_principle_trace())


def test_principle_trace_missing_constitution_fails(tmp_path, monkeypatch):
    tree = _trace_tree(tmp_path)
    (tree / "references" / "PRINCIPLES.md").unlink()
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert any("missing" in e for e in check_repo.check_principle_trace())


def test_principle_trace_empty_constitution_fails_rather_than_passing(tmp_path, monkeypatch):
    """A constitution with no clauses must not make the guard vacuous."""
    monkeypatch.setattr(check_repo, "ROOT", _trace_tree(tmp_path, clauses="no clauses here\n"))
    assert any("vacuously" in e for e in check_repo.check_principle_trace())


# check_red_line_parity — AGENTS.md's hand-written summary still covers SKILL.md.

def _red_line_tree(tmp_path, skill_items, agents_summary, skill_word="Six",
                   agents_word="Six"):
    numbered = "\n".join(f"{i}. {t}" for i, t in enumerate(skill_items, 1))
    (tmp_path / "SKILL.md").write_text(
        f"# Skill\n\n## {skill_word} non-negotiable red lines (every scenario)\n\n"
        f"{numbered}\n\n## Next section\n\ntext\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        f"# Agents\n\n**{agents_word} hard red lines**: {agents_summary}\n\nother prose\n",
        encoding="utf-8")
    return tmp_path


SIX = ["No invented facts; every number carries provenance;",
       "No coined Chinese: concepts with no established term stay English;",
       "Sales storyline is value and future;",
       "Every title names its subject and carries a verifiable datum;",
       "Charts: one accent colour, conclusion titles, a source line;",
       "AI never signs; money conclusions come from a person."]
COVERS = "provenance; established; future; verifiable; accent; a person signs."


def test_red_line_parity_covering_summary_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _red_line_tree(tmp_path, SIX, COVERS))
    assert check_repo.check_red_line_parity() == []


def test_red_line_parity_paraphrase_passes(tmp_path, monkeypatch):
    """A summary may reword and still pass — the real case that forced this.

    AGENTS.md says "standard Chinese term" where SKILL.md says "established
    Chinese term". The guard's first version demanded the single longest
    distinguishing word and failed exactly here, which would have meant editing
    AGENTS.md to satisfy a checker rather than a reader. Asking for ANY anchor
    lets the rewording through while a dropped rule still fails.

    The limit this leaves, stated rather than hidden: a summary that rewords
    EVERY distinguishing word of one rule is indistinguishable from dropping it.
    """
    paraphrase = ("provenance; standard terms rather than established ones, "
                  "kept in English; future; verifiable; accent; person.")
    monkeypatch.setattr(check_repo, "ROOT", _red_line_tree(tmp_path, SIX, paraphrase))
    assert check_repo.check_red_line_parity() == []


def test_red_line_parity_dropped_rule_fails(tmp_path, monkeypatch):
    dropped = "provenance; future; verifiable; accent; person."
    monkeypatch.setattr(check_repo, "ROOT", _red_line_tree(tmp_path, SIX, dropped))
    assert any("drops red line 2" in e for e in check_repo.check_red_line_parity())


def test_red_line_parity_count_drift_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _red_line_tree(tmp_path, SIX + ["A seventh rule about zebras."],
                                       COVERS))
    errors = check_repo.check_red_line_parity()
    assert any("lists 7" in e for e in errors)


def test_red_line_parity_no_block_fails_rather_than_passing(tmp_path, monkeypatch):
    (tmp_path / "SKILL.md").write_text("# Skill\n\nno red lines here\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert any("vacuously" in e for e in check_repo.check_red_line_parity())


# check_rule_ids — ids are unique, present, and frozen once assigned.

def _rule_id_tree(tmp_path, lines):
    refs = tmp_path / "references"
    refs.mkdir()
    (refs / "design-rules.md").write_text("# Rules\n\n" + "\n".join(lines) + "\n",
                                          encoding="utf-8")
    return tmp_path


def test_rule_ids_unique_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "FROZEN_RULE_IDS", ("DR-1", "DR-2"))
    monkeypatch.setattr(check_repo, "ROOT", _rule_id_tree(
        tmp_path, ["*Serves: **P-1**.* · id `DR-1`", "*Serves: **P-2**.* · id `DR-2`"]))
    assert check_repo.check_rule_ids() == []


def test_rule_ids_duplicate_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "FROZEN_RULE_IDS", ("DR-1",))
    monkeypatch.setattr(check_repo, "ROOT", _rule_id_tree(
        tmp_path, ["*Serves: **P-1**.* · id `DR-1`", "*Serves: **P-2**.* · id `DR-1`"]))
    assert any("already used" in e for e in check_repo.check_rule_ids())


def test_rule_ids_missing_id_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "FROZEN_RULE_IDS", ("DR-1",))
    monkeypatch.setattr(check_repo, "ROOT", _rule_id_tree(
        tmp_path, ["*Serves: **P-1**.* · id `DR-1`", "*Serves: **P-2**.*"]))
    assert any("no id" in e for e in check_repo.check_rule_ids())


def test_rule_ids_vanished_id_fails(tmp_path, monkeypatch):
    """An id is a name, not an address: it does not disappear when a file is edited."""
    monkeypatch.setattr(check_repo, "FROZEN_RULE_IDS", ("DR-1", "DR-2"))
    monkeypatch.setattr(check_repo, "ROOT", _rule_id_tree(
        tmp_path, ["*Serves: **P-1**.* · id `DR-1`"]))
    assert any("no longer do" in e for e in check_repo.check_rule_ids())


def test_rule_ids_empty_tree_fails_rather_than_passing(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _rule_id_tree(tmp_path, ["no declarations"]))
    assert any("vacuously" in e for e in check_repo.check_rule_ids())


# check_brand_registry — thin, and every path it names exists.

def _brand_tree(tmp_path, rec=None, default="lumivate"):
    (tmp_path / "brands").mkdir()
    (tmp_path / "assets" / "brand" / "lumivate").mkdir(parents=True)
    (tmp_path / "assets" / "brand" / "lumivate" / "mark.svg").write_text("<svg/>")
    rec = rec if rec is not None else {"wordmark": "LUMI Style",
                                       "assets": "assets/brand/lumivate/",
                                       "cover_mark": "assets/brand/lumivate/mark.svg"}
    (tmp_path / "brands" / "registry.json").write_text(
        json.dumps({"schema": 1, "default": default, "brands": {"lumivate": rec}}),
        encoding="utf-8")
    return tmp_path


def test_brand_registry_valid_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _brand_tree(tmp_path))
    assert check_repo.check_brand_registry() == []


def test_brand_registry_missing_asset_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _brand_tree(
        tmp_path, rec={"wordmark": "x", "cover_mark": "assets/brand/lumivate/gone.svg"}))
    assert any("does not exist" in e for e in check_repo.check_brand_registry())


def test_brand_registry_default_must_be_a_brand(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _brand_tree(tmp_path, default="other"))
    assert any("default brand" in e for e in check_repo.check_brand_registry())


def test_brand_registry_refuses_to_carry_rules(tmp_path, monkeypatch):
    """Palette lives in tokens/, rules in references/. A brand record that
    started carrying either would be a fifth surface restating them."""
    monkeypatch.setattr(check_repo, "ROOT", _brand_tree(
        tmp_path, rec={"wordmark": "x", "accent": "#00ff00", "max_fonts": 2}))
    errors = check_repo.check_brand_registry()
    assert any("stay in references/ and tokens/" in e for e in errors)


def test_brand_registry_empty_fails_rather_than_passing(tmp_path, monkeypatch):
    (tmp_path / "brands").mkdir()
    (tmp_path / "brands" / "registry.json").write_text('{"brands": {}}', encoding="utf-8")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert any("vacuously" in e for e in check_repo.check_brand_registry())


# check_shape_library — the manifest and the files are one set, and shapes draw.

def _shape_tree(tmp_path, files=("a", "b"), described=None, relation_from="tag",
                geometry=True):
    lib = tmp_path / "assets" / "shapes"
    lib.mkdir(parents=True)
    body = '<path d="M0 0h10v10H0z"/>' if geometry else "<title>nothing</title>"
    for f in files:
        (lib / f"{f}.svg").write_text(f'<svg viewBox="0 0 10 10">{body}</svg>',
                                      encoding="utf-8")
    described = files if described is None else described
    (lib / "tags.json").write_text(json.dumps({
        "schema": 3,
        "shapes": {f: {"family": f, "relation": [], "relation_from": relation_from}
                   for f in described}}), encoding="utf-8")
    return tmp_path


def test_shape_library_complete_tree_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _shape_tree(tmp_path))
    assert check_repo.check_shape_library() == []


def test_shape_library_absent_is_a_legal_state(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_shape_library() == []


def test_shape_library_undescribed_file_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _shape_tree(tmp_path, files=("a", "b"), described=("a",)))
    assert any("does not describe it" in e for e in check_repo.check_shape_library())


def test_shape_library_dangling_manifest_entry_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _shape_tree(tmp_path, files=("a",), described=("a", "gone")))
    assert any("not shipped" in e for e in check_repo.check_shape_library())


def test_shape_library_shape_without_geometry_fails(tmp_path, monkeypatch):
    """A file can exist, parse, and render as an empty frame."""
    monkeypatch.setattr(check_repo, "ROOT", _shape_tree(tmp_path, geometry=False))
    assert any("carries no geometry" in e for e in check_repo.check_shape_library())


def test_shape_library_unclassified_is_not_a_failure(tmp_path, monkeypatch):
    """Marking a shape unclassified is the alternative to guessing, and two
    curations of this library were wrong because a name was read as one."""
    monkeypatch.setattr(check_repo, "ROOT",
                        _shape_tree(tmp_path, relation_from="unclassified"))
    assert check_repo.check_shape_library() == []


def test_shape_library_invented_relation_source_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT",
                        _shape_tree(tmp_path, relation_from="guessed"))
    assert any("relation_from" in e for e in check_repo.check_shape_library())


# check_assets_tracked — an asset .gitignore excludes is not an asset that ships.
#
# This guard needs a real repository rather than a directory, because its whole
# point is that it asks git instead of the filesystem. The shape library was on
# disk for every local run and absent from every clone, and no filesystem guard
# could tell those apart.


def _asset_tree(tmp_path, ignore="", dotfile=False):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(ignore)
    assets = tmp_path / "assets" / "shapes"
    assets.mkdir(parents=True)
    (assets / "p001-flow-01.svg").write_text("<svg/>")
    if dotfile:
        (tmp_path / "assets" / ".DS_Store").write_bytes(b"\x00")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_assets_tracked_tracked_asset_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _asset_tree(tmp_path))
    assert check_repo.check_assets_tracked() == []


def test_assets_tracked_ignored_asset_fails_naming_the_path(tmp_path, monkeypatch):
    """The live defect: a blanket *.svg rule with no exception for this dir."""
    monkeypatch.setattr(check_repo, "ROOT", _asset_tree(tmp_path, ignore="*.svg\n"))
    errors = check_repo.check_assets_tracked()
    assert any("assets/shapes/p001-flow-01.svg" in e for e in errors)


def test_assets_tracked_dotfile_litter_is_exempt(tmp_path, monkeypatch):
    """.DS_Store is the platform's litter, not the package's material."""
    monkeypatch.setattr(check_repo, "ROOT",
                        _asset_tree(tmp_path, ignore=".DS_Store\n", dotfile=True))
    assert check_repo.check_assets_tracked() == []


def test_assets_tracked_tarball_checkout_asserts_nothing(tmp_path, monkeypatch):
    """No .git is a legal state; a tarball has no index to ask."""
    (tmp_path / "assets").mkdir()
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    assert check_repo.check_assets_tracked() == []
