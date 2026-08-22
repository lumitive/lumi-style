"""What three adversarial reviews found in the guards themselves.

Every case here was demonstrated green-while-wrong, or red-while-right, against
the real repository before it was fixed. They are kept because a guard's first
proof is that it can go red, and its second is that it does not fire on
correct work.
"""
import json
import subprocess

import check_repo


def _tree(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


REG = {"schema": 1, "gates": {
    "D1_contrast": {"checker": "design", "family": "colour",
                    "severity": "gate", "since": "always"},
    "M4_banned_hits": {"checker": "prose", "family": "ban",
                       "severity": "gate", "since": "always"},
}}
ROWS = ('def grade():\n'
        '    rows: list = []\n'
        '    rows.append(("D1_contrast", 1, "=0 (gates)", False, False))\n'
        '    return rows\n')


def _repo(tmp_path, design_src, reg=None):
    return _tree(tmp_path, {
        "scripts/check/check_design.py": design_src,
        "scripts/check/check_prose.py": ('def grade():\n'
                                         '    rows = [\n'
                                         '        ("M4_banned_hits", 0, "=0 (gates)", 0, 0),\n'
                                         '    ]\n'
                                         '    return rows\n'),
        "evals/gates.json": json.dumps(reg or REG)})


def test_a_row_written_as_a_list_is_read(tmp_path, monkeypatch):
    """`rows.append([...])` emitted a verdict that BLOCKS delivery while the
    register never had to declare it — the AST reader required a tuple."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, ROWS.replace('    return rows',
                               '    rows.append(["D98_list", 1, "=0 (gates)", 0, 0])\n'
                               '    return rows')))
    monkeypatch.setattr(check_repo, "gating",
                        type("g", (), {"layout_verdicts": staticmethod(lambda r: set())})())
    errors = check_repo.check_gate_declarations()
    assert any("D98_list" in e for e in errors), errors


def test_a_row_name_built_at_runtime_is_a_finding(tmp_path, monkeypatch):
    """Skipping it silently is how an undeclared gate ships."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, ROWS.replace('    return rows',
                               '    f = "D97"\n'
                               '    rows.append((f"{f}_x", 1, "=0 (gates)", 0, 0))\n'
                               '    return rows')))
    monkeypatch.setattr(check_repo, "gating",
                        type("g", (), {"layout_verdicts": staticmethod(lambda r: set())})())
    errors = check_repo.check_gate_declarations()
    assert any("builds a row name at runtime" in e for e in errors), errors


def test_a_target_that_is_not_a_literal_is_a_finding(tmp_path, monkeypatch):
    """It used to read as the WEAKEST severity, so moving a target into a
    constant demoted a live gate and the guard then demanded the register agree
    with the demotion."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, 'Z = "=0 (gates)"\n' + ROWS.replace(
            '"=0 (gates)", False, False', 'Z, False, False')))
    monkeypatch.setattr(check_repo, "gating",
                        type("g", (), {"layout_verdicts": staticmethod(lambda r: set())})())
    errors = check_repo.check_gate_declarations()
    assert any("is not a literal" in e for e in errors), errors


def test_a_tuple_outside_the_rows_table_is_not_a_row(tmp_path, monkeypatch):
    """A three-element tuple in an unrelated helper overwrote the real row —
    `ast.walk` order decided the answer — and the guard reported the REGISTER
    as the liar, which would have talked an operator into demoting a live
    commercial gate."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, ROWS + '\n\ndef _docs():\n'
                         '    return [("D1_contrast", "design-rules.md", "section 6")]\n'))
    monkeypatch.setattr(check_repo, "gating",
                        type("g", (), {"layout_verdicts": staticmethod(lambda r: set())})())
    assert check_repo.check_gate_declarations() == []


def test_the_privacy_branch_is_read_as_a_branch(tmp_path):
    """The first version asked whether two strings appeared anywhere in the
    file. In the real one they are eighteen lines and one scope apart, so the
    guard was passing on evidence from unrelated code."""
    gates = ('def f():\n'
             '    for kind in k:\n'
             '        if kind == "metric":\n'
             '            gating.append(line)\n'
             '        if kind == "privacy":\n'
             '            (gating if held else not_held).append(line)\n')
    demoted = gates.replace('(gating if held else not_held).append(line)',
                            '(graded if held else not_held).append(line)')
    assert check_repo._privacy_branch_gates(gates)
    assert not check_repo._privacy_branch_gates(demoted)


def test_a_column_aligned_table_is_not_a_failure(tmp_path, monkeypatch):
    """The row pattern demanded exactly one space, so any markdown formatter
    turned a correct table into an accusation — and into the WRONG message,
    because a partial match routed past the "re-point the entry" branch."""
    reg = {"schema": 1, "gates": {
        "M4_banned_hits": {"checker": "prose", "family": "ban",
                           "severity": "gate", "since": "always"}}}
    tree = _tree(tmp_path, {
        "evals/gates.json": json.dumps(reg),
        "references/eval-rubric.md":
            "| id | Metric | Target | Predicate |\n|---|---|---|---|\n"
            "| M4   | Banned phrases | =0 — **gates** | hits |\n"
            "**M4 does gate**, because it is decidable.\n"})
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert check_repo.check_prose_gating_claims() == []


def test_a_real_identifier_is_not_a_wrong_verdict_name(tmp_path, monkeypatch):
    """`visual_share_median` and `page_share` are real output keys. The guard
    told the author to rename correct code, which is the wrong-gate-edits-prose
    failure this repository already has on record."""
    reg = {"schema": 1, "gates": {
        "visual_absent": {"checker": "layout", "family": "figure",
                          "severity": "gate", "since": "always"}}}
    tree = _tree(tmp_path, {
        "evals/gates.json": json.dumps(reg),
        "scripts/check/check_design.py":
            'def f(c):\n    return {"visual_share_median": c["page_share"]}\n',
        "references/design-rules.md":
            "it reports `visual_share_median` and `page_share`.\n"})
    monkeypatch.setattr(check_repo, "ROOT", tree)
    assert check_repo.check_verdict_names() == []


def test_a_name_that_exists_nowhere_still_fires(tmp_path, monkeypatch):
    """Fixing the false positive must not pull the teeth."""
    reg = {"schema": 1, "gates": {
        "visual_absent": {"checker": "layout", "family": "figure",
                          "severity": "gate", "since": "always"}}}
    tree = _tree(tmp_path, {
        "evals/gates.json": json.dumps(reg),
        "scripts/check/check_design.py": "x = 1\n",
        "references/design-rules.md": "the gate `visual_share` fails a page.\n"})
    monkeypatch.setattr(check_repo, "ROOT", tree)
    errors = check_repo.check_verdict_names()
    assert len(errors) == 1 and "`visual_share`" in errors[0]
