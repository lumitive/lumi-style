"""The ledger counts, drafts and ratifies nothing.

The tests that matter here are the ones about what it must NOT do: promote a
metric that is merely inapplicable into a broken instrument, put a thin deck on
the efficiency board, or drop a candidate to keep the queue looking clean.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import ledger  # noqa: E402 — after the path insert, deliberately


def _trace(tid="t-000000000001", **kw):
    base = {"trace_id": tid, "closed_at": "2026-08-16T00:00:00+00:00",
            "gates": {}, "graded": {}, "thresholds": {},
            "principle_yields": [], "refused_to_emit": None,
            "content_pages": 10, "output_tokens": 30000,
            "phase_seconds": {"build": 300}}
    base.update(kw)
    return base


def test_an_inapplicable_metric_is_not_a_broken_instrument():
    """A Chinese ban list on an English deck is n/a, not unmeasurable. The
    first version collapsed the two and reported three healthy metrics broken."""
    traces = [_trace(f"t-00000000000{i}", thresholds={"M4zh": "n/a"})
              for i in range(1, 5)]
    assert ledger.ledger_instruments(traces) == []


def test_a_metric_that_could_not_run_is_suspect():
    traces = [_trace(f"t-00000000000{i}", thresholds={"M8": "not_measured"})
              for i in range(1, 5)]
    assert any("not measured" in why for _mid, why, _c
               in ledger.ledger_instruments(traces))


def test_a_metric_that_never_fails_is_suspect():
    """A ruler nothing ever trips is either perfect or not a ruler."""
    traces = [_trace(f"t-00000000000{i}", thresholds={"M8": 1.0},
                     graded={"M8": "ok"}) for i in range(1, 5)]
    assert any("never fails" in why for _mid, why, _c
               in ledger.ledger_instruments(traces))


def test_instrument_candidates_outrank_threshold_candidates():
    """A wrong ruler contaminates every measurement taken after it."""
    traces = [_trace(f"t-00000000000{i}", thresholds={"M8": "not_measured"},
                     graded={"M2": "FAIL"}) for i in range(1, 5)]
    kinds = [d["kind"] for d in ledger.candidates(traces)]
    assert kinds.index("instrument") < kinds.index("threshold")


def test_nothing_is_dropped_from_the_queue():
    """Over capacity a candidate is deferred and printed, never evicted: a
    queue that silently empties reports health it does not have."""
    traces = [_trace(f"t-0000000000{i:02d}",
                     thresholds={f"M{i}": "not_measured" for i in range(1, 12)})
              for i in range(1, 5)]
    drafts = ledger.candidates(traces)
    assert len(drafts) > ledger.QUEUE_CAPACITY
    assert all(d["state"] in ("queued", "deferred") for d in drafts)
    assert any(d["state"] == "deferred" for d in drafts)


def test_a_run_with_a_failing_gate_is_not_on_the_board():
    """A thin deck is cheap and worthless; rewarding it would invert the point."""
    good = _trace("t-000000000001")
    bad = _trace("t-000000000002", gates={"D14_placeholders": "FAIL"},
                 output_tokens=100)
    ids = [r["trace_id"] for r in ledger.board([good, bad])]
    assert ids == ["t-000000000001"]


def test_discussion_and_outline_are_not_charged():
    t = _trace(phase_seconds={"discussion": 900, "outline": 600,
                              "build": 300, "checks": 60})
    assert ledger.board([t])[0]["charged_seconds"] == 360


def test_an_unclosed_trace_is_an_abandoned_build_and_not_on_the_board():
    t = _trace(closed_at=None)
    _r, _y, abandoned = ledger.ledger_signals([t])
    assert abandoned == [t["trace_id"]]
    assert ledger.board([t]) == []


# The four-beat design's own falsification data was recorded and never read.
# `outline_reviewed` exists so that skipping beat 4 — the only defence
# completeness has — is a countable fact rather than an invisible choice, and
# nothing counted it. `titles_changed_after_approval` is the sharper of the
# two: a review agreed and then departed from is not a review.

def _t(**kw):
    base = {"trace_id": "t-000000000001", "entry_path": "B",
            "outline_reviewed": False, "titles_changed_after_approval": 0,
            "review_ref": None}
    base.update(kw)
    return base


def test_beats_counts_the_reviews_that_happened():
    rows = ledger.ledger_beats([_t(outline_reviewed=True), _t(), _t()])
    assert rows["total"] == 3 and rows["reviewed"] == 1


def test_beats_counts_titles_that_moved_after_approval():
    rows = ledger.ledger_beats([
        _t(outline_reviewed=True, titles_changed_after_approval=4),
        _t(outline_reviewed=True)])
    assert rows["drifted"] == 1 and rows["titles_moved"] == 4


def test_beats_splits_by_entry_path():
    rows = ledger.ledger_beats([_t(entry_path="A"), _t(entry_path="B"),
                                _t(entry_path="B")])
    assert rows["by_entry_path"] == {"A": 1, "B": 2}


def test_beats_on_no_traces_reports_zero_rather_than_failing():
    assert ledger.ledger_beats([])["total"] == 0
