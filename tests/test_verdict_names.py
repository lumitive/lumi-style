"""Prose may not name a layout verdict that does not exist.

The guard found two on its first run against the real repository, and the
second was the serious one: `references/design-rules.md` had given the
`figure axes:` REPORT line a verdict-shaped name, and the sentence around it
said the unnamed-axis case reports when `figure_axis_named` gates it — telling
an author a check would not fail them when it would.
"""
import json
import subprocess

import check_repo

REG = {
    "figure_axis_named": {"checker": "layout", "family": "figure-labelling",
                          "severity": "gate", "since": "always"},
    "figure_axis_overlap": {"checker": "layout", "family": "figure-labelling",
                            "severity": "gate", "since": "always"},
    "footer_wrap": {"checker": "layout", "family": "footer",
                    "severity": "gate", "since": "always"},
    "D12_commercial_footer": {"checker": "design", "family": "footer",
                              "severity": "gate", "since": "always"},
}


def _repo(tmp_path, files, reg=None):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "gates.json").write_text(
        json.dumps({"schema": 1, "gates": reg if reg is not None else REG}))
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_a_real_verdict_name_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "references/design-rules.md": "`figure_axis_named` gates.\n"}))
    assert check_repo.check_verdict_names() == []


def test_an_abbreviated_family_name_fails_and_offers_the_verdicts(tmp_path, monkeypatch):
    """The measured defect: prose said `figure_axis`, which is no verdict."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "references/design-rules.md": "intro\n`figure_axis` gates.\n"}))
    errors = check_repo.check_verdict_names()
    assert len(errors) == 1
    assert "references/design-rules.md:2" in errors[0]
    assert "figure_axis_named, figure_axis_overlap" in errors[0]
    assert "footer_wrap" not in errors[0], "the suggestion is the family, not the set"


def test_a_verdict_shaped_name_for_a_report_line_fails(tmp_path, monkeypatch):
    """The other measured defect: `figure_axes` is a printed line, not a
    verdict, and nothing keys on it."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "references/design-rules.md": "`figure_axes` is reported.\n"}))
    errors = check_repo.check_verdict_names()
    assert len(errors) == 1 and "`figure_axes`" in errors[0]


def test_an_unrelated_identifier_is_not_read(tmp_path, monkeypatch):
    """Narrow on purpose. Most snake_case in this repository names a function,
    a probe field or a CSS custom property, and a guard that flagged those
    would edit prose to match itself."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "references/design-rules.md":
            "`build_page_contracts` and `check_design` and `axname_x`.\n"}))
    assert check_repo.check_verdict_names() == []


def test_a_design_verdict_family_is_not_claimed(tmp_path, monkeypatch):
    """`D12_commercial_footer` shares the `footer` FAMILY with a layout verdict
    but not its first word, and the D metrics have their own guard."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "references/design-rules.md": "`D12_commercial` gates.\n"}))
    assert check_repo.check_verdict_names() == []


def test_frozen_history_is_not_rewritten(tmp_path, monkeypatch):
    """A CHANGELOG entry names the verdict that existed when it was written."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "CHANGELOG.md": "## 0.1.1 — `figure_axis` was the name back then\n",
        "specs/2026-01-01-x-design.md": "planned `figure_axis`\n"}))
    assert check_repo.check_verdict_names() == []


def test_a_waiver_silences_with_a_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "references/design-rules.md": "a hypothetical `figure_axis` verdict\n"}))
    monkeypatch.setitem(check_repo.VERDICT_NAME_WAIVERS,
                        ("references/design-rules.md", "figure_axis"),
                        "illustration of a name that does not exist")
    assert check_repo.check_verdict_names() == []
