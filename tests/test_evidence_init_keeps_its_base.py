"""`--init` reuses a base an earlier pass already established.

A release whose predecessor has no commit of its own — because a branch carried
two releases and they were folded into one commit, which is a decision the
owner makes at merge time — cannot have its diff base computed from the
CHANGELOG. `--init` said so and returned 1, and `release.py` aborted the whole
flow on it, so the release could not be committed by the tool that exists to
refuse committing on a red preflight.

The file already carried a valid `diff_base`, written when the release was set
up. Recomputing it is what fails; keeping it costs nothing and is the same
reasoning that already makes release.py carry hand-written waivers across an
`--init` — do not destroy what an earlier pass established.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts" / "check"))

import check_evidence  # noqa: E402


def test_init_keeps_an_existing_base_when_it_cannot_compute_one(monkeypatch):
    """The predecessor has no commit; the file already names a base."""
    monkeypatch.setattr(check_evidence, "find_release_commit", lambda _v: None)
    monkeypatch.setattr(check_evidence, "releases_in_changelog",
                        lambda: ["9.9.9", "9.9.8"])
    monkeypatch.setattr(check_evidence, "effective_touches", lambda _b: ["tokens/x.css"])
    monkeypatch.setattr(check_evidence, "spec_lines_changed", lambda _b: 0)

    saved: dict = {}
    monkeypatch.setattr(check_evidence, "save",
                        lambda v, d: saved.update({"v": v, "doc": d}))
    monkeypatch.setattr(check_evidence, "load",
                        lambda _v: {"version": "9.9.9", "diff_base": "deadbeef",
                                    "spec": "", "obligations": [], "checks": [],
                                    "waivers": []})

    rc = check_evidence.cmd_init("9.9.9")
    assert rc == 0, "init refused to run against a base it had already been given"
    assert saved["doc"]["diff_base"] == "deadbeef"


def test_init_still_fails_when_there_is_no_base_at_all(monkeypatch):
    """The fix must not turn a genuinely uncomputable release green."""
    monkeypatch.setattr(check_evidence, "find_release_commit", lambda _v: None)
    monkeypatch.setattr(check_evidence, "releases_in_changelog",
                        lambda: ["9.9.9", "9.9.8"])
    monkeypatch.setattr(check_evidence, "load", lambda _v: {})
    assert check_evidence.cmd_init("9.9.9") == 1
