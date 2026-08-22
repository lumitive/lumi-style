"""What a conformance deliverable is held to: every gate, plus the Evals.

T1's `require` was a hand-written list of six metrics — D12, D14, D15, M4,
collision, content_hidden — while ten design metrics gate and fifteen layout
verdicts do, and no conformance run had ever applied the Evals thresholds at
all. A deck could fail D19, D1, D3, D4 and eleven layout checks and be recorded
`pass`. One was: the owner opened a 51KB deck with zero content pages on
2026-08-21 and found it green on the board.

The set is read from the checkers' own row tables, so a gate added tomorrow
binds the task the same day and no list here can rot.
"""
import gating


def test_the_gating_set_is_read_from_the_checkers():
    ids, gate = gating.metric_ids("D")
    assert "D12" in gate and "D19" in gate and "D22" in gate
    # Reported-not-gating metrics must stay out: requiring them would invent a
    # bar this package does not hold a deliverable to.
    assert "D1" in ids and "D1" not in gate
    assert gate < ids


def test_prose_has_a_gating_set_too():
    ids, gate = gating.metric_ids("M")
    assert gate, "check_prose gates on at least one metric"
    assert gate <= ids


def test_only_verdicts_that_were_reported_are_demanded():
    # A metric that did not run is not demanded of a document that never had it.
    got = gating.gating_metrics({"D12_commercial_footer": "ok",
                                 "D1_contrast": "FAIL"})
    assert got == {"D12_commercial_footer"}


def test_an_unreported_gate_is_not_conjured():
    assert gating.gating_metrics({}) == set()


def test_layout_names_are_not_matched_by_the_prefix_rule():
    # Layout verdicts are words, not prefixed ids, and every one of them gates
    # by construction — which is why the driver adds them from the report
    # rather than through this function.
    assert gating.gating_metrics({"collision": "ok", "band_escape": "FAIL"}) == set()


def test_the_task_declares_the_full_standard():
    import json
    import pathlib
    t = json.loads(pathlib.Path("conformance/tasks/T1-deck.json").read_text("utf-8"))
    assert t["require"] == "all-gating", "the six-metric list must not come back"
    assert t["evals"] is True, "the Evals thresholds are half the standard"


def test_every_full_tier_driver_can_actually_run_a_command():
    """A tier that claims the agent runs the checkers must be driven able to.

    T1 asks the agent to run check_design, check_prose and inspect_layout and
    fix what they report. Claude Code was driven with `--permission-mode
    acceptEdits`, which permits writing files and not running commands: it
    stopped after 141 seconds having written nothing, asking for `python3` to
    be allowlisted. The tier claim was impossible to meet because of the
    driver's own flags, and no run had ever noticed — because until 0.1.543 no
    task asked.
    """
    import json
    import pathlib
    reg = json.loads(pathlib.Path("adapters/platforms.json").read_text("utf-8"))
    cannot_execute = {"acceptEdits", "plan", "manual", "ask"}
    for agent in reg["platforms"]:
        argv = agent.get("drive")
        if not argv or agent.get("capability") != "full":
            continue
        flat = " ".join(argv)
        # Either the mode permits commands, or an explicit allowlist does. What
        # is NOT acceptable is a mode that forbids them with nothing to reopen
        # the door — the agent then cannot meet the tier's own claim.
        allows = ("--allowedTools" in argv or "--allowed-tools" in argv
                  or not (set(argv) & cannot_execute))
        assert allows, (
            f"{agent['id']} is driven in a mode that cannot execute a command "
            f"and carries no allowlist, while the full tier claims it runs the "
            f"checkers itself: {argv}")
        # And never by handing over the whole shell. This registry ships; the
        # flag would grant arbitrary execution on every machine that drives it.
        assert "bypassPermissions" not in flat, (
            f"{agent['id']} grants arbitrary shell. Allowlist the commands the "
            f"task needs instead: {argv}")


def test_a_document_the_evals_cannot_read_is_a_finding_not_a_crash(tmp_path, monkeypatch):
    """The measurement returns what it managed. A file it could not parse —
    a partial write, an artifact caught mid-flight — arrives without
    `content_pages`, and `eval_corpus.score` raises KeyError on it. One
    unmeasurable document must not cost the whole run its scores."""
    import run_conformance as rc
    monkeypatch.setattr(rc.eval_corpus, "measure",
                        lambda path, with_render, **kw: {"genre": "internal"})
    out = rc._eval_misses(tmp_path / "x.html", "internal")
    assert out and "could not read" in out[0]


def test_a_measurable_document_still_reports_its_misses(tmp_path, monkeypatch):
    import run_conformance as rc
    monkeypatch.setattr(rc.eval_corpus, "measure",
                        lambda path, with_render, **kw: {"genre": "internal",
                                                   "content_pages": 3})
    out = rc._eval_misses(tmp_path / "x.html", "internal")
    assert any("content_pages=3" in x for x in out)
