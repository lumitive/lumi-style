"""A proposed bar is replayed against the documents an owner has judged.

0.1.592 drafted a ceiling on layout top share from five documents found one at
a time, and withdrew it when a sixth — A1, this package's own accepted anchor —
measured worse than both documents the owner had faulted. The reasoning was
sound; the corpus was whatever somebody had remembered to reopen. This tool
asks the question the same way every time.
"""
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import bar_replay  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _nothing_written():
    """Snapshot `evals/` BEFORE any test in this module runs the tool.

    The first version of this check snapshotted one file, ran the tool once and
    compared — as the LAST test in the file. Three earlier tests had already
    invoked it, so a mutant that writes to `thresholds.json` had already
    written by the time the snapshot was taken, and `before == after` held
    while the tracked file sat modified on disk. Measured: run alone the check
    failed the mutant, run in the file it passed.
    """
    def digest():
        return {p.relative_to(ROOT): p.read_bytes()
                for p in sorted((ROOT / "evals").rglob("*"))
                if p.is_file() and p.suffix in (".json",)}
    before = digest()
    yield
    after = digest()
    changed = [str(k) for k in set(before) | set(after)
               if before.get(k) != after.get(k)]
    assert not changed, (
        "bar_replay wrote to the corpus it was asked to read: " + ", ".join(changed))


def _run(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/bar_replay.py"), *args],
        capture_output=True, text=True, cwd=ROOT)


def test_the_withdrawn_layout_bar_is_still_refuted():
    """The tool's own deliberate red: it must reproduce, mechanically, the
    answer that took a release and a hand measurement to reach."""
    r = _run("layout_top_share", "50")
    assert r.returncode != 0, r.stdout
    assert "CONTRADICTS THE RECORD" in r.stdout
    assert "A1" in r.stdout and "accepted and the bar FAILS it" in r.stdout


def test_the_two_directions_are_reported_apart():
    """A bar that FAILS an accepted document is wrong outright. A bar that
    PASSES a rejected one is weaker evidence — a document is rejected for a
    reason, and R1's was its figures, not its layout. Collapsing the two makes
    every metric unpassable as rejected documents accumulate."""
    out = bar_replay.replay("layout_top_share", 50, "ceiling")
    assert any("accepted and the bar FAILS it" in d for d in out["contradictions"])
    assert any("rejected and the bar PASSES it" in d for d in out["permissive"])
    assert out["separates"] is False


def test_a_bar_that_matches_the_record_is_reported_as_agreeing():
    """The product claim runs both ways, and only one way was pinned.

    Both existing tests assert on documents that genuinely disagree at bar 50,
    so a tool that flagged EVERY document — never consulting the owner's
    verdict at all — produced identical output and passed. Nothing asserted an
    exit of 0 either. This case is the same two documents under a bar that
    agrees with the record.
    """
    r = _run("layout_top_share", "50", "--direction", "floor")
    assert r.returncode == 0, r.stdout
    assert "CONTRADICTS" not in r.stdout and "PERMISSIVE" not in r.stdout
    out = bar_replay.replay("layout_top_share", 50, "floor")
    assert out["disagreements"] == [] and out["separates"] is True


def test_a_metric_nobody_has_measured_is_not_a_pass():
    """Silence is the failure this package hunts: a bar checked against an
    empty corpus must not read as a bar that survived."""
    r = _run("no_such_metric", "1")
    assert r.returncode != 0
    assert "no judged document carries a reading" in r.stdout


def test_every_judged_document_carries_the_readings_it_claims():
    """The corpus block is the tool's whole input. A reading that is a string,
    or a verdict outside the vocabulary, would quietly change the answer."""
    rows = bar_replay.judged()
    # NOT VACUOUS. Deleting every `readings` block left this test green, because
    # the loop below simply never ran: it asserted the readings are numbers IF
    # ANY EXIST, and never that any do.
    assert sum(1 for r in rows if r["readings"]) >= 2, (
        "fewer than two judged documents carry any reading; a bar cannot be "
        "replayed against a corpus that has not been measured")
    for row in rows:
        assert row["id"], f"a judged entry has no corpus id: {row}"
        assert row["verdict"] in bar_replay.GOOD + bar_replay.BAD, row
        for key, value in row["readings"].items():
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                f"{row['id']}.{key} is {value!r}, not a number")


def test_the_tool_sets_nothing():
    """It reports and a person decides. A tool that could write the threshold
    it just validated would be the invented-number machine with a step.

    The real assertion is the module-scoped fixture above; this keeps the
    behaviour named where a reader looks for it."""
    _run("layout_top_share", "50")


def _corpus(tmp_path, monkeypatch, judged):
    fake = tmp_path / "thresholds.json"
    fake.write_text(json.dumps({"corpus": {"judged": judged}}))
    monkeypatch.setattr(bar_replay, "THRESHOLDS", fake)
    return fake


def test_a_bar_with_nothing_to_separate_is_not_reported_as_separating(
        tmp_path, monkeypatch):
    """One accepted document and a generous bar produced `separates: True` — a
    bar that survived a test nobody ran. It needs one document on each side of
    the record before agreement means anything."""
    _corpus(tmp_path, monkeypatch, [
        {"id": "G1", "verdict": "accepted", "readings": {"m": 10}}])
    out = bar_replay.replay("m", 999, "ceiling")
    assert out["contradictions"] == [] and out["permissive"] == []
    assert out["separates"] is False, "a one-sided corpus separated nothing"
    assert out["judged_good"] == 1 and out["judged_bad"] == 0


def test_a_bar_that_agrees_with_both_sides_separates(tmp_path, monkeypatch):
    _corpus(tmp_path, monkeypatch, [
        {"id": "G1", "verdict": "accepted", "readings": {"m": 10}},
        {"id": "B1", "verdict": "rejected", "readings": {"m": 90}}])
    out = bar_replay.replay("m", 50, "ceiling")
    assert out["separates"] is True and not out["disagreements"]


def test_a_verdict_outside_the_vocabulary_is_refused(tmp_path, monkeypatch):
    """Silently ignored, such a row printed with the `!!` mark, counted as no
    disagreement and exited 0 — a document the record has an opinion about,
    quietly dropped from the question being asked of the record."""
    _corpus(tmp_path, monkeypatch, [
        {"id": "X1", "verdict": "maybe", "readings": {"m": 10}}])
    with pytest.raises(SystemExit) as exc:
        bar_replay.judged()
    assert "X1" in str(exc.value)
