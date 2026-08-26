"""The guard that makes a held count mean something, held itself.

CLAUDE.md convention 11 asks every guard for synthetic-tree tests with at least
one failing fixture. This one shipped without them in its first draft, and a
review pointed at the consequence precisely: the house pattern for red-testing a
guard is a `tmp_path` tree with `check_repo.ROOT` monkeypatched, and the first
version's `if not baseline.is_file(): return []` meant that pattern produced a
GREEN guard over an empty probe. The guard about checks that pass over nothing
passed over nothing.
"""
import json
import pathlib

import check_repo

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _register(tmp_path, gates):
    (tmp_path / "evals").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evals" / "gates.json").write_text(
        json.dumps({"schema": 1, "gates": gates}), encoding="utf-8")


def test_the_shipped_tree_is_clean():
    assert check_repo.check_vacuous_gates() == []


def test_no_measurable_fixture_is_a_finding_not_a_pass(tmp_path, monkeypatch):
    """The green-over-nothing path, which is this guard's own subject.

    A tree with no design fixture cannot check a single gating row. Returning
    `[]` there reads identically to a clean run, and `check_repo`'s summary
    counts it among the passing checks.
    """
    (tmp_path / "fixtures").mkdir()
    _register(tmp_path, {})
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_vacuous_gates()
    assert errors, "a tree with no fixture reported the guard green"
    assert "reported green over nothing" in errors[0]


def test_an_unreadable_register_is_a_finding(tmp_path, monkeypatch):
    (tmp_path / "evals").mkdir(parents=True)
    (tmp_path / "evals" / "gates.json").write_text("{ not json", encoding="utf-8")
    (tmp_path / "fixtures").mkdir()
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_vacuous_gates()
    assert errors and "gate register" in errors[0]


def test_every_gating_row_in_the_shipped_register_declares_a_subject():
    """Completeness is the property; the probe only ever confirms.

    Absence has two shapes and one of them leaves no observable trace at all —
    `D33_icon_provenance` prints its violation count, so a document with no
    icon renders exactly like a document whose icons are all fine. No probe can
    find that. The declaration is what makes the count trustworthy, so the
    declaration has to be total.
    """
    import check_design
    import gate_registry
    import gating
    r = check_design.measure(ROOT / "fixtures" / "deck-pass.en.html")
    verdicts = {n: v for n, _, _, v in check_design.grade(r)}
    gates = gating.gating_metrics(verdicts, ROOT)
    declared = gate_registry.load(ROOT)
    missing = sorted(n for n in gates
                     if not (declared.get(n) or {}).get("subject"))
    assert not missing, f"gating rows with no declared subject: {missing}"


def test_a_subject_may_be_a_key_a_field_or_always():
    """The three legal forms, and nothing else silently passing for one."""
    import check_design
    import gate_registry
    r = check_design.measure(ROOT / "fixtures" / "deck-pass.en.html")
    for name, entry in gate_registry.load(ROOT).items():
        subject = entry.get("subject")
        if not subject or subject == "always":
            continue
        key, _, field = subject.partition(".")
        assert key in r, f"{name}: {subject}"
        if field:
            assert isinstance(r[key], dict) or r[key] is None, f"{name}: {subject}"
            if isinstance(r[key], dict):
                assert field in r[key], f"{name}: {subject}"
