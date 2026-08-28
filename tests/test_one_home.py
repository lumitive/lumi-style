"""`check_one_home`, proven able to pass AND to fail on synthetic trees.

It replaced `check_no_shadow_math` and `check_no_shadow_markup` at 0.1.634, so
their cases live here: a re-grown copy, a retired private spelling, a private
strip-tags and a private CJK-space rule. The rest are the register's own
failure modes — the answers this guard gives when it cannot look, which is a
different question from whether it can go red (FM-24 beside FM-01).
"""
import json

import check_repo

TAG_RE = r"""re\.(?:sub|compile)\(\s*r?["']<\[\^>\]\+>["']"""
CJK_RE = r"\(\?<=\[[^\]]+\]\) \(\?=\[[^\]]+\]\)"
SELF_TAG = 'x = re.sub(r"<[^>]+>", " ", raw)'
SELF_CJK = 'y = re.sub(r"(?<=[\\u4e00-\\u9fff]) (?=[\\u4e00-\\u9fff])", "", t)'


def _register(**over):
    fact = {
        "id": "colour-arithmetic",
        "fact": "sRGB linearisation",
        "owner": "scripts/lib/color_math.py",
        "defs": ["srgb_linear"],
        "retired_defs": ["_lin"],
        "patterns": [{"regex": TAG_RE, "what": "a private strip-tags",
                      "selftest": SELF_TAG}],
        "why": "0.1.415",
    }
    fact.update(over)
    return {"schema": 1, "facts": [fact], "waivers": []}


def _tree(tmp_path, extra="", register=None, owner=None):
    (tmp_path / "evals").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evals/single-source.json").write_text(
        json.dumps(register if register is not None else _register()),
        encoding="utf-8")
    lib = tmp_path / "scripts/lib"
    lib.mkdir(parents=True, exist_ok=True)
    (lib / "color_math.py").write_text(
        owner if owner is not None else "def srgb_linear(v):\n    return v\n",
        encoding="utf-8")
    (tmp_path / "scripts/consumer.py").write_text(
        "from color_math import srgb_linear\n" + extra, encoding="utf-8")
    return tmp_path


def _run(tmp_path, monkeypatch, **kw):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path, **kw))
    return check_repo.check_one_home()


def test_clean_tree_passes(tmp_path, monkeypatch):
    assert _run(tmp_path, monkeypatch) == []


def test_calls_and_imports_are_not_flagged(tmp_path, monkeypatch):
    assert _run(tmp_path, monkeypatch,
                extra="x = srgb_linear(0.5)\n# mentions srgb_linear( in prose\n") == []


def test_a_regrown_copy_fails(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch,
                  extra="def srgb_linear(c):\n    return c / 12.92\n")
    assert len(errors) == 1
    assert "srgb_linear" in errors[0] and "color_math" in errors[0]


def test_a_retired_private_spelling_fails(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch, extra="def _lin(c):\n    return c\n")
    assert len(errors) == 1 and "_lin" in errors[0]


def test_a_private_strip_tags_fails(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch, extra=SELF_TAG + "\n")
    assert len(errors) == 1 and "consumer.py:2" in errors[0]
    assert "strip-tags" in errors[0]


def test_the_cjk_shape_is_caught_in_either_spelling(tmp_path, monkeypatch):
    """The escaped range and the range written with the characters themselves.

    The regex this replaced matched only the escaped spelling, and
    `markup.py` — the owner — writes the other one, so a copy of the line
    actually in the tree could not have been seen.
    """
    reg = _register(patterns=[{"regex": CJK_RE, "what": "a private CJK-space rule",
                               "selftest": SELF_CJK}])
    for body in (SELF_CJK, 'y = re.sub(r"(?<=[一-鿿]) (?=[一-鿿])", "", t)'):
        monkeypatch.setattr(check_repo, "ROOT",
                            _tree(tmp_path, extra=body + "\n", register=reg))
        errors = check_repo.check_one_home()
        assert len(errors) == 1 and "CJK-space" in errors[0]


def test_a_waiver_permits_the_copy_and_names_a_reason(tmp_path, monkeypatch):
    reg = _register()
    reg["waivers"] = [{"path": "scripts/consumer.py", "fact": "colour-arithmetic",
                       "reason": "the bootstrap copy, which cannot import"}]
    assert _run(tmp_path, monkeypatch, register=reg,
                extra="def srgb_linear(c):\n    return c\n") == []


def test_an_unused_waiver_fails(tmp_path, monkeypatch):
    reg = _register()
    reg["waivers"] = [{"path": "scripts/consumer.py", "fact": "colour-arithmetic",
                       "reason": "no longer needed"}]
    errors = _run(tmp_path, monkeypatch, register=reg)
    assert len(errors) == 1 and "outlived" in errors[0]


def test_a_waiver_without_a_reason_fails(tmp_path, monkeypatch):
    reg = _register()
    reg["waivers"] = [{"path": "scripts/consumer.py", "fact": "colour-arithmetic"}]
    errors = _run(tmp_path, monkeypatch, register=reg,
                  extra="def srgb_linear(c):\n    return c\n")
    assert any("no reason" in e for e in errors)


# --- the third answer: what it prints when it cannot look (FM-24) ---

def test_an_unreadable_register_is_a_finding(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path))
    (tmp_path / "evals/single-source.json").write_text("{not json", encoding="utf-8")
    errors = check_repo.check_one_home()
    assert len(errors) == 1 and "could not be read" in errors[0]


def test_an_empty_register_is_a_finding(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch, register={"schema": 1, "facts": []})
    assert len(errors) == 1 and "no facts" in errors[0]


def test_a_missing_owner_is_a_finding(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch,
                  register=_register(owner="scripts/lib/gone.py"))
    assert len(errors) == 1 and "not a file" in errors[0]


def test_a_def_the_owner_does_not_define_is_a_finding(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch, register=_register(defs=["moved_away"]))
    assert len(errors) == 1 and "does not define" in errors[0]


def test_a_retired_name_the_owner_took_back_is_a_finding(tmp_path, monkeypatch):
    errors = _run(tmp_path, monkeypatch,
                  owner="def srgb_linear(v):\n    return v\n\n\ndef _lin(c):\n    return c\n")
    assert len(errors) == 1 and "not retired" in errors[0]


def test_a_pattern_that_stopped_matching_its_selftest_is_a_finding(tmp_path, monkeypatch):
    reg = _register(patterns=[{"regex": r"re\.sub\(THIS-SHAPE-IS-GONE",
                               "what": "a private strip-tags",
                               "selftest": SELF_TAG}])
    errors = _run(tmp_path, monkeypatch, register=reg)
    assert len(errors) == 1 and "selftest" in errors[0]


def test_a_fact_declaring_nothing_to_look_for_is_a_finding(tmp_path, monkeypatch):
    """Nine facts stripped of their arrays left the LIVE guard returning `[]`.

    The register's own argument for `selftest`, one level up: an entry that has
    quietly stopped naming anything reads as coverage.
    """
    reg = _register()
    for key in ("defs", "retired_defs", "patterns"):
        reg["facts"][0].pop(key, None)
    errors = _run(tmp_path, monkeypatch, register=reg)
    assert len(errors) == 1 and "nothing to look for" in errors[0]


def test_a_key_the_schema_does_not_define_is_a_finding(tmp_path, monkeypatch):
    """`def` for `defs` disarmed an entry in silence — the likeliest editing
    mistake on a register whose promise is that a fact is one entry."""
    reg = _register()
    reg["facts"][0]["def"] = reg["facts"][0].pop("defs")
    errors = _run(tmp_path, monkeypatch, register=reg)
    assert any("schema does not define" in e for e in errors)


def test_two_facts_owning_one_name_is_a_finding(tmp_path, monkeypatch):
    """Otherwise the second silently overwrites the first, and the scan then
    accuses the FIRST fact's owner of copying its own implementation."""
    reg = _register()
    reg["facts"].append({
        "id": "second", "fact": "another", "owner": "scripts/lib/color_math.py",
        "defs": ["srgb_linear"], "why": "x"})
    errors = _run(tmp_path, monkeypatch, register=reg,
                  extra="def srgb_linear(c):\n    return c\n")
    assert any("both own srgb_linear()" in e for e in errors)


def test_a_scan_that_visited_nothing_is_a_finding(tmp_path, monkeypatch):
    """The guard going blind, which is a different question from the register
    going blind and was not asked until 0.1.640: a tree holding only the owner
    produced exactly what a clean repository produces."""
    monkeypatch.setattr(check_repo, "ROOT", _tree(tmp_path))
    (tmp_path / "scripts/consumer.py").unlink()
    errors = check_repo.check_one_home()
    assert len(errors) == 1 and "not a scan that passed" in errors[0]


def test_the_live_register_still_declares_what_the_consolidation_moved():
    """The register is DATA now, so deleting a pattern is a silent edit.

    `check_no_shadow_markup` had its regexes in the guard's own source and a
    test asserting them; the migration made the subject a JSON file that no
    test read. Deleting the two `visible-text` patterns passed every test in
    this suite and every guard in check_repo.
    """
    import json
    reg = json.loads((check_repo.ROOT / "evals/single-source.json")
                     .read_text(encoding="utf-8"))
    facts = {f["id"]: f for f in reg["facts"]}
    # Each of these consolidated a defect a release paid for; the entry is the
    # only thing keeping it consolidated.
    assert set(facts) >= {"colour-arithmetic", "css-token-reading",
                          "visible-text", "package-version",
                          "platform-registry", "conformance-history",
                          "gate-register", "agent-capability", "asking-git"}
    assert len(facts["visible-text"]["patterns"]) == 2      # tags, CJK space
    assert len(facts["package-version"]["patterns"]) == 3   # stamp x2, releases
    assert facts["asking-git"]["patterns"]                  # the git invocation
    assert "contrast_hex" in facts["colour-arithmetic"]["defs"]
    assert "same_model" in facts["agent-capability"]["defs"]
    assert "read_rows" in facts["conformance-history"]["defs"]


def test_a_pattern_that_does_not_compile_is_a_finding(tmp_path, monkeypatch):
    reg = _register(patterns=[{"regex": "([unclosed", "what": "x",
                               "selftest": "y"}])
    errors = _run(tmp_path, monkeypatch, register=reg)
    assert len(errors) == 1 and "does not compile" in errors[0]


def test_the_live_repo_is_clean():
    assert check_repo.check_one_home() == []
