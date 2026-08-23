"""The gaps five reviews of 0.1.564–0.1.574 found in this range's own tests.

Each of these covers a behaviour that shipped, broke, or was fixed with nothing
asserting it — which in this repository is the same as not having it.
"""
import json
import pathlib
import re
import subprocess
import sys

import check_repo
import shipped

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))
import check_deliverable as drv  # noqa: E402


def test_an_instrument_that_could_not_measure_at_all_fails_the_run():
    """0.1.574 removed the loop's inherited exit and five `silent` branches
    lost it with them. The block printed "could not be measured at all" and
    the run returned 0 — twice over, since a clean run then closes the trace as
    a completed passing build."""
    for report in ({}, {"unmeasurable": "no token block"},
                   {"unmeasured": 3}, {"blind_gates": ["D12_x"]}):
        runs = {"design": {"kind": "design", "exit": 1, "spoke": True,
                           "reports": [report] if report else []}}
        _, _, silent, _, worst = drv.verdict_block(runs, None)
        assert silent and worst == 1, (report, silent, worst)


def _prose(doc, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_prose.py"), str(doc), *args],
        capture_output=True, text=True)


def _cjk(tmp_path, name, lang):
    raw = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    raw = re.sub(r"(<h2[^>]*>)", r"\1客户在三个月内完成了全部迁移 ", raw, count=1)
    raw = raw.replace('<html lang="en"', "<html" if lang is None else f'<html lang="{lang}"')
    p = tmp_path / name
    p.write_text(raw, encoding="utf-8")
    return p


def test_an_unknown_language_is_not_an_exemption(tmp_path):
    """`declared_language` returns whatever the attribute says. 0.1.574 closed
    "delete the attribute"; `lang="xx"` reopened the same escape one character
    wider, printed as a legitimate exemption."""
    out = _prose(_cjk(tmp_path, "x.html", "xx"))
    assert out.returncode == 1, out.stdout


def test_the_summary_line_agrees_with_the_exit(tmp_path):
    """`blind` was counted into the gating total and not into the failure
    total, so a document whose only defect was a blind M12 printed "all metrics
    pass" and returned 1. An author reads the last line."""
    out = _prose(_cjk(tmp_path, "y.html", None))
    assert out.returncode == 1
    assert "all metrics pass" not in out.stdout, out.stdout


def test_a_blind_gate_reaches_the_one_block_and_the_exit(tmp_path):
    """The motivating defect was that `check_deliverable` printed NOTHING. It
    reaches the gating bucket only because `verdict_block` filters on the pair
    ("ok", "n/a") — a fourth verdict word must not be droppable by a consumer
    that filters on the old pair."""
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/check_deliverable.py"),
         str(_cjk(tmp_path, "z.html", None)), "--fast", "--json"],
        capture_output=True, text=True)
    d = json.loads(out.stdout)
    assert any("M12_visible_cjk blind" in g for g in d["gating"]), d["gating"]
    assert d["exit"] == 1


def test_an_empty_consumer_set_is_a_finding(tmp_path):
    """A SKILL.md rewrite that names its commands in prose rather than as paths
    collapsed the boundary: fourteen scripts flipped to development,
    `new_deck.py` among them, and BOTH guards stayed green."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "SKILL.md").write_text("this entry names no script at all\n")
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "shipped.json").write_text(
        json.dumps({"schema": 1, "consumer_seeds": [], "rules": []}))
    (tmp_path / "scripts" / "ops").mkdir(parents=True)
    (tmp_path / "scripts" / "ops" / "x.py").write_text("a = 1\n")
    try:
        shipped.consumer_scripts(tmp_path)
    except ValueError as exc:
        assert "names no script" in str(exc)
    else:
        raise AssertionError("an empty consumer set was accepted")


def test_a_missing_skill_is_a_finding(tmp_path):
    """`ROOT` is DEFINED by SKILL.md existing, so returning an empty set there
    was a lie in every tree that could reach it."""
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "shipped.json").write_text(
        json.dumps({"schema": 1, "consumer_seeds": [], "rules": []}))
    try:
        shipped.consumer_scripts(tmp_path)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("a tree with no SKILL.md computed a boundary")


def test_the_register_declaring_no_layout_verdict_is_a_finding(tmp_path, monkeypatch):
    """`[]` means "checked and found nothing" in this file."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "gates.json").write_text(json.dumps(
        {"schema": 1, "gates": {"D1_x": {"checker": "design", "family": "c",
                                         "severity": "gate", "since": "always"}}}))
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    errors = check_repo.check_verdict_names()
    assert errors and "no layout verdict" in errors[0]


def test_the_generator_list_covers_every_checked_build_step():
    """Derived from ci.yml, and nothing asserted it was non-empty: a workflow
    reformat that `ci_commands` parsed differently would regenerate nothing and
    commit stale artefacts — silently, where the hand-written list at least
    failed partially."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import release
    got = {" ".join(c) for c in release.generators()}
    assert got, "no generator was derived from ci.yml"
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    import preflight
    want = {c for c in preflight.ci_commands(text)
            if c.split()[1].startswith("scripts/build/") and "--check" in c
            and c.split()[1] not in release.VALIDATORS_NOT_GENERATORS}
    assert got == {c.replace(" --check", "") for c in want}


def test_the_home_collapse_survives_a_root_home():
    """One of the two implementations guarded `home in ("", "/")` and the other
    did not, producing `~Users/name/...`."""
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import run_conformance
    assert run_conformance._portable("/x/y") == "/x/y"
