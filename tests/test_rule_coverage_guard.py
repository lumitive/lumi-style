"""check_rule_coverage proven able to pass AND to fail, on synthetic trees.

Convention 11: a gate's first proof is that it can go red. This repository has
shipped three checks that ran green and were later found incapable of failing,
so each of this checker's five findings gets a tree that produces it — and the
reverse-direction one (a gate no rule cites) gets its own, because that is the
half nobody remembers to test.

The trees are synthetic on purpose. A test that pointed the checker at the real
repository would be testing the register, not the checker: the register is
hand-written and will change every time a rule does.
"""
import json

import check_rule_coverage as crc


def _tree(tmp_path, rules, *, rule_text="a title budgets two lines\n",
          gating_names=("D14", "collision"), all_names=("D14", "D9", "collision")):
    """A tree with one rule file, one register, and a stubbed checker vocabulary.

    `gating.py` reads the real checkers by AST, which a synthetic tree has none
    of — so the vocabulary is injected rather than parsed. What is under test
    here is the register audit, not the AST reader — the reader is covered
    against the live checkers at the bottom of this file.
    """
    (tmp_path / "SKILL.md").write_text("stub\n")
    refs = tmp_path / "references"
    refs.mkdir(exist_ok=True)   # a test may build the tree twice
    (refs / "design-rules.md").write_text(rule_text)
    evals = tmp_path / "evals"
    evals.mkdir(exist_ok=True)
    (evals / "rule-coverage.json").write_text(
        json.dumps({"schema": 1, "rules": rules}))
    return tmp_path, set(gating_names), set(all_names)


def _audit(monkeypatch, tmp_path, rules, **kw):
    root, gates, names = _tree(tmp_path, rules, **kw)
    monkeypatch.setattr(crc.gating, "every_gating_name", lambda r=None: gates)
    monkeypatch.setattr(crc.gating, "every_metric_name", lambda r=None: names)
    return crc.audit(root)


GOOD = [
    {"id": "R-1", "source": "references/design-rules.md:1",
     "quote": "budgets two lines", "gist": "Budget two lines for a title.",
     "page_kind": "all", "metric": "D14", "gates": True},
    {"id": "R-2", "source": "references/design-rules.md:1",
     "quote": "a title", "gist": "Every page carries a title.",
     "page_kind": "content", "metric": "collision", "gates": True},
]


def test_a_truthful_register_passes(tmp_path, monkeypatch):
    findings, counts = _audit(monkeypatch, tmp_path, GOOD)
    assert findings == []
    assert counts["rules"] == 2 and counts["gated"] == 2


def test_a_reworded_rule_reddens(tmp_path, monkeypatch):
    """The quote is the assertion. A rule rewritten out from under the register
    is the drift this whole register exists to make visible."""
    findings, _ = _audit(monkeypatch, tmp_path, GOOD,
                         rule_text="a title may run to three lines\n")
    assert any("nowhere in references/design-rules.md" in f for f in findings)


def test_a_moved_rule_says_where_it_went(tmp_path, monkeypatch):
    findings, _ = _audit(monkeypatch, tmp_path, GOOD,
                         rule_text="\n\na title budgets two lines\n")
    assert any("moved to line 3" in f for f in findings)


def test_a_metric_no_checker_emits_reddens(tmp_path, monkeypatch):
    rules = [dict(GOOD[0], metric="D99"), GOOD[1]]
    findings, _ = _audit(monkeypatch, tmp_path, rules)
    assert any("D99" in f and "no checker emits" in f for f in findings)


def test_claiming_a_gate_that_does_not_gate_reddens(tmp_path, monkeypatch):
    rules = [dict(GOOD[0], metric="D9", gates=True), GOOD[1]]
    findings, _ = _audit(monkeypatch, tmp_path, rules)
    assert any("says gates=True" in f and "D9" in f for f in findings)


def test_an_unchecked_rule_must_say_why(tmp_path, monkeypatch):
    rules = [dict(GOOD[0], metric=None, gates=False), GOOD[1]]
    findings, _ = _audit(monkeypatch, tmp_path, rules)
    assert any("no metric and no why_unchecked" in f for f in findings)
    rules[0]["why_unchecked"] = "candidate; needs a rendered measurement"
    findings, _ = _audit(monkeypatch, tmp_path, rules)
    assert findings == [] or all("why_unchecked" not in f for f in findings)


def test_a_gate_no_rule_cites_reddens(tmp_path, monkeypatch):
    """The reverse direction: a threshold nothing in references/ asks for."""
    findings, _ = _audit(monkeypatch, tmp_path, GOOD,
                         gating_names=("D14", "collision", "page_height"),
                         all_names=("D14", "D9", "collision", "page_height"))
    assert any("page_height" in f and "cited by no rule" in f for f in findings)


def test_an_empty_register_fails_rather_than_passing(tmp_path, monkeypatch):
    findings, _ = _audit(monkeypatch, tmp_path, [])
    assert any("declares no rules" in f for f in findings)


def test_a_duplicate_id_reddens(tmp_path, monkeypatch):
    findings, _ = _audit(monkeypatch, tmp_path, [GOOD[0], dict(GOOD[1], id="R-1")])
    assert any("two entries carry this id" in f for f in findings)


def test_an_unknown_page_kind_reddens(tmp_path, monkeypatch):
    rules = [dict(GOOD[0], page_kind="appendix"), GOOD[1]]
    findings, _ = _audit(monkeypatch, tmp_path, rules)
    assert any("page_kind" in f and "appendix" in f for f in findings)


# The AST reader the audit leans on. Held against the LIVE checkers on purpose:
# its whole job is to agree with them, and a synthetic tree would only prove it
# agrees with a fixture of its own.

def test_layout_verdicts_are_read_from_the_function_that_defines_them():
    import gating
    names = gating.layout_verdicts()
    # Sampled, not enumerated: a full list here would be a second copy of the
    # gate set, which is what this module was extracted to end.
    assert {"collision", "content_spill", "deck_structure"} <= names
    assert all(n.islower() and " " not in n for n in names)
    # `add(` appears elsewhere in that file; only the ones inside
    # deliverable_verdicts are gates, so the reader must not have swept them up.
    assert "visual_absent" in names and len(names) < 40
    # THE SECOND SPELLING. `datum` and `role_split` are assigned into the dict
    # directly rather than through `add(...)`, and the first version of this
    # reader knew only the common shape and reported one gate too few.
    assert {"datum", "role_split"} <= names


def test_the_gate_union_is_the_gating_metrics_plus_every_layout_verdict():
    import gating
    union = gating.every_gating_name()
    assert gating.layout_verdicts() <= union
    assert gating.metric_ids("D")[1] <= union
    # A metric that does NOT gate must stay out of the union — otherwise
    # check_rule_coverage's reverse check would demand a rule for a threshold
    # that cannot fail anything.
    non_gating = gating.metric_ids("D")[0] - gating.metric_ids("D")[1]
    assert non_gating and not (non_gating & union)


def test_an_unreadable_checker_raises_rather_than_reading_as_no_gates():
    """Fail loud, not open.

    An empty gate set turns every consumer green: the register would report
    zero uncited gates and `check_repo`'s gating-claims guard would hold prose
    to nothing. This repository has shipped three checks incapable of failing;
    a reader that swallows a missing file is how a fourth would happen.
    """
    import pathlib

    import gating
    import pytest
    with pytest.raises(OSError):
        gating.layout_verdicts(pathlib.Path("/nonexistent"))


# The generated page. A generator whose --check cannot fail is a generator that
# ships a stale file quietly, which is what `--check` exists to prevent.

def test_a_stale_contracts_page_fails_its_own_check(tmp_path, monkeypatch):
    import build_page_contracts as bpc
    out = tmp_path / "page-contracts.md"
    monkeypatch.setattr(bpc, "OUT", out)
    assert bpc.main([]) == 0
    assert bpc.main(["--check"]) == 0
    out.write_text(out.read_text(encoding="utf-8").replace("cover", "COVER", 1),
                   encoding="utf-8")
    assert bpc.main(["--check"]) == 1


def test_the_contracts_page_covers_every_page_kind_the_register_uses():
    """A section missing from SECTIONS would silently drop its rules."""
    import json

    import build_page_contracts as bpc
    import check_rule_coverage as crc
    register = json.loads(bpc.REGISTER.read_text(encoding="utf-8"))
    used = {r["page_kind"] for r in register["rules"]}
    assert used <= {k for k, _, _ in bpc.SECTIONS}
    assert {k for k, _, _ in bpc.SECTIONS} == set(crc.PAGE_KINDS)


def test_chinese_rule_data_is_marked_as_data_not_left_as_prose():
    """The english-only guard permits CJK only in backticks. A generator that
    emitted it bare reddened the build the first time it ran."""
    import build_page_contracts as bpc
    assert bpc._cell("Use 赋能 only in 销售赋能.") == "Use `赋能` only in `销售赋能`."


def test_the_registers_cjk_exemption_covers_quotes_and_nothing_else(tmp_path,
                                                                    monkeypatch):
    """The rule register quotes two rules that are ABOUT Chinese output, so its
    `quote` field may carry CJK. Nothing else in the file may, and the exemption
    is narrow enough to say so."""
    import json

    import check_repo
    root = tmp_path
    (root / "evals").mkdir()
    reg = root / "evals" / "rule-coverage.json"

    def errors_for(rule):
        reg.write_text(json.dumps({"rules": [rule]}), encoding="utf-8")
        monkeypatch.setattr(check_repo, "ROOT", root)
        monkeypatch.setattr(check_repo, "_json_manifests", lambda: [reg])
        monkeypatch.setattr(check_repo, "md_files", lambda: [])
        return check_repo.check_english_only()

    assert errors_for({"quote": "赋能 is allowed only in", "gist": "English."}) == []
    bad = errors_for({"quote": "fine", "gist": "这是中文散文"})
    assert bad and ".gist" in bad[0]

    # THE THIRD AXIS: the exemption is scoped to that one path. Dropping the
    # path condition is the natural "simplification" when someone generalises
    # this, and it would let Chinese into any tracked manifest's `quote` field.
    other = root / "evals" / "some-other-manifest.json"
    other.write_text(json.dumps({"rules": [{"quote": "赋能"}]}), encoding="utf-8")
    monkeypatch.setattr(check_repo, "_json_manifests", lambda: [other])
    elsewhere = check_repo.check_english_only()
    assert elsewhere and "some-other-manifest.json" in elsewhere[0]
