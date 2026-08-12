"""The evidence gate's failure shapes on synthetic trees.

Each test builds a throwaway git repo shaped like the real one (CHANGELOG,
KNOWN_GAPS, a release-convention base commit) and calls check_file directly,
so every error path the gate promises is pinned by an assertion rather than
by prose.
"""
import json
import subprocess

import check_evidence

V = "0.1.500"

CHANGELOG = """# Changelog

## 0.1.500 — head

## 0.1.499 — base
"""

GAP_OPEN = """# Known gaps

## GAP-001 · something broke

- status: open
- opened: 0.1.400
- surface: scripts/x.py
- symptom: it is broken
- check: python3 scripts/x.py
"""


def _git(cwd, *args):
    p = subprocess.run(["git", *args], cwd=cwd, check=True,
                       capture_output=True, text=True)
    return p.stdout.strip()


def _tree(tmp_path, monkeypatch, changelog=CHANGELOG):
    """A git repo with the release scaffolding; returns the base commit sha."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "CHANGELOG.md").write_text(changelog)
    (tmp_path / "KNOWN_GAPS.md").write_text(GAP_OPEN)
    (tmp_path / "SKILL.md").write_text("line1\nline2\nline3\n")
    (tmp_path / "conformance").mkdir()
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "0.1.499 — base")
    monkeypatch.setattr(check_evidence, "ROOT", tmp_path)
    # The map self-check validates TOUCH_MAP/OBLIGATIONS against ROOT; the
    # synthetic tree carries none of the real scripts, so tests that are not
    # about the maps run with empty ones (test_validate_maps covers them).
    monkeypatch.setattr(check_evidence, "TOUCH_MAP", ())
    monkeypatch.setattr(check_evidence, "OBLIGATIONS", {})
    monkeypatch.setattr(check_evidence, "EVIDENCE_DIR",
                        tmp_path / "releases" / "evidence")
    return _git(tmp_path, "rev-parse", "HEAD")


def _evidence(tmp_path, base, **overrides):
    doc = {"version": V, "diff_base": base, "spec": "",
           "obligations": [], "checks": [], "waivers": []}
    doc.update(overrides)
    d = tmp_path / "releases" / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{V}.json").write_text(json.dumps(doc, indent=2))


def _check(cid="layout-fixtures", code=0, sha="a" * 64, **extra):
    entry = {"id": cid, "command": "python3 x", "exit_code": code,
             "stdout_sha256": sha, "date": "2026-08-12"}
    entry.update(extra)
    return entry


def _row(agent):
    return {"skill_version": V, "agent": agent, "date": "2026-08-12",
            "tasks": {"T1-deck": "fail", "T2-deaify": "pass",
                      "T3-recall": "pass"}}


def test_missing_evidence_file_points_at_init(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    errors = check_evidence.check_file(V, warn=False)
    assert len(errors) == 1
    assert "--init" in errors[0]


def test_unanswered_obligation_fails(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, obligations=["layout-fixtures"])
    errors = check_evidence.check_file(V, warn=False)
    assert any("neither a recorded execution nor a reasoned waiver" in e
               for e in errors)


def test_reasoned_waiver_discharges_an_obligation(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, obligations=["layout-fixtures"],
              waivers=[{"id": "layout-fixtures",
                        "reason": "no browser on this runner"}])
    assert check_evidence.check_file(V, warn=False) == []


def test_shared_stdout_digest_reads_as_copied_evidence(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base,
              checks=[_check(cid="layout-fixtures"), _check(cid="globe-js")])
    errors = check_evidence.check_file(V, warn=False)
    assert any("copied, not executed" in e for e in errors)


def test_failure_without_gap_citation_fails(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, checks=[_check(code=1)])
    errors = check_evidence.check_file(V, warn=False)
    assert any("KNOWN_GAPS" in e for e in errors)


def test_failure_citing_an_open_gap_passes(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, checks=[_check(code=1, gap="GAP-001")])
    assert check_evidence.check_file(V, warn=False) == []


def test_waiver_without_reason_is_not_a_waiver(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, waivers=[{"id": "layout-fixtures"}])
    errors = check_evidence.check_file(V, warn=False)
    assert any("not a waiver" in e for e in errors)


def test_blank_diff_base_fails(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, diff_base="")
    errors = check_evidence.check_file(V, warn=False)
    assert len(errors) == 1
    assert "diff_base" in errors[0]


def test_bogus_diff_base_re_resolves_by_subject(tmp_path, monkeypatch):
    """The rebase lesson (main run 31553098031): a dangling SHA whose
    previous release still exists BY SUBJECT re-resolves and passes —
    subjects survive a rebase, hashes do not."""
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, diff_base="0" * 40)
    errors = check_evidence.check_file(V, warn=False)
    assert errors == []


def test_bogus_diff_base_with_no_subject_match_fails(tmp_path, monkeypatch, capsys):
    base = _tree(tmp_path, monkeypatch)
    _evidence(tmp_path, base, diff_base="0" * 40)
    # break the subject fallback: rewrite the base commit's subject so no
    # commit matches the previous release
    subprocess.run(["git", "commit", "--amend", "-q", "-m", "not a release"],
                   cwd=tmp_path, check=True)
    errors = check_evidence.check_file(V, warn=False)
    assert any("does not resolve" in e and "no commit subject" in e
               for e in errors)


def test_overclaim_with_a_waiver_quotes_the_phrase(tmp_path, monkeypatch):
    changelog = CHANGELOG.replace("— head", "— head, all gates green")
    base = _tree(tmp_path, monkeypatch, changelog=changelog)
    _evidence(tmp_path, base,
              waivers=[{"id": "globe-js", "reason": "no browser"}])
    errors = check_evidence.check_file(V, warn=False)
    assert any("all gates green" in e for e in errors)


def test_stale_board_without_waiver_fails(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    (tmp_path / "conformance/history.json").write_text(
        json.dumps([_row("claude-code")]))  # one agent: stale
    _evidence(tmp_path, base, obligations=["conformance-freshness"])
    errors = check_evidence.check_file(V, warn=False)
    assert any("stale" in e for e in errors)


def test_fresh_board_discharges_the_obligation(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    (tmp_path / "conformance/history.json").write_text(
        json.dumps([_row("claude-code"), _row("cursor")]))
    _evidence(tmp_path, base, obligations=["conformance-freshness"])
    assert check_evidence.check_file(V, warn=False) == []


# --- effective_touches: the stamp filter and the untracked blind spot ---

def test_stamp_sized_change_to_a_stamped_file_is_filtered(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    # one edited line = 1 added + 1 deleted = 2, inside SKILL.md's budget of 2
    (tmp_path / "SKILL.md").write_text("line1 restamped\nline2\nline3\n")
    touched = check_evidence.effective_touches(base)
    assert touched is not None
    assert "SKILL.md" not in touched


def test_substantive_change_to_a_stamped_file_counts(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    (tmp_path / "SKILL.md").write_text(
        "line1\nline2\nline3\n" + "a new rule line\n" * 5)
    touched = check_evidence.effective_touches(base)
    assert touched is not None
    assert "SKILL.md" in touched


def test_untracked_new_file_is_a_touch(tmp_path, monkeypatch):
    base = _tree(tmp_path, monkeypatch)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/new_check.py").write_text("x = 1\n")
    touched = check_evidence.effective_touches(base)
    assert touched is not None
    assert "scripts/new_check.py" in touched


def test_validate_maps_clean_on_the_live_repo():
    assert check_evidence.validate_maps() == []


def test_validate_maps_catches_a_dangling_touch_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(check_evidence, "ROOT", tmp_path)
    monkeypatch.setattr(check_evidence, "TOUCH_MAP",
                        (("scripts/gone.py", ("layout-fixtures",)),))
    monkeypatch.setattr(check_evidence, "OBLIGATIONS", {})
    errors = check_evidence.validate_maps()
    assert len(errors) == 1 and "can never fire" in errors[0]


def test_validate_maps_catches_a_dangling_obligation_command(tmp_path, monkeypatch):
    monkeypatch.setattr(check_evidence, "ROOT", tmp_path)
    monkeypatch.setattr(check_evidence, "TOUCH_MAP", ())
    monkeypatch.setattr(check_evidence, "OBLIGATIONS",
                        {"x": ("python3 scripts/gone.py --check", "why")})
    errors = check_evidence.validate_maps()
    assert len(errors) == 1 and "recording it would fail" in errors[0]
