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


# The model × effort matrix (K1): quality and cost columns produced together.
# The board's quality line is the matrix's quality line — one implementation —
# and cost exists only at render time, computed from a local dated price
# table, because `cost_usd` was deleted from the schema for going stale the
# day the price does.

def test_matrix_groups_by_model_and_effort():
    traces = [_trace("t-000000000001", model="opus-5", effort="high"),
              _trace("t-000000000002", model="opus-5", effort="low"),
              _trace("t-000000000003", model="sonnet-5", effort="high")]
    _models, _efforts, cells = ledger.matrix(traces)
    assert set(cells) == {("opus-5", "high"), ("opus-5", "low"),
                          ("sonnet-5", "high")}


def test_matrix_effort_columns_are_the_schema_s_own_plus_unknown():
    """Read from trace_schema.ENUMS, never retyped — a retyped effort list is
    the sixth-literal-copy defect the genre vocabulary already had."""
    sys.path.insert(0, str(ROOT / "scripts" / "lib"))
    import trace_schema
    _models, efforts, _cells = ledger.matrix([_trace(model="m", effort="low")])
    assert efforts == (*trace_schema.ENUMS["effort"], "?")


def test_matrix_cell_is_the_median_of_tokens_per_page():
    traces = [
        _trace("t-000000000001", model="m", effort="low",
               content_pages=10, output_tokens=100),   # 10.0 t/p
        _trace("t-000000000002", model="m", effort="low",
               content_pages=10, output_tokens=200),   # 20.0 t/p
        _trace("t-000000000003", model="m", effort="low",
               content_pages=10, output_tokens=400),   # 40.0 t/p
    ]
    _m, _e, cells = ledger.matrix(traces)
    rows = cells[("m", "low")]
    assert len(rows) == 3
    import statistics
    assert statistics.median(r["tokens_per_page"] for r in rows) == 20.0


def test_a_run_with_a_failing_gate_is_not_in_the_matrix():
    """The board's line holds here too: a thin deck must not set the median."""
    good = _trace("t-000000000001", model="m", effort="low")
    bad = _trace("t-000000000002", model="m", effort="low",
                 gates={"D14_placeholders": "FAIL"}, output_tokens=100)
    _m, _e, cells = ledger.matrix([good, bad])
    assert [r["trace_id"] for r in cells[("m", "low")]] == ["t-000000000001"]


def test_a_run_with_no_model_or_effort_groups_under_question_mark():
    _m, _e, cells = ledger.matrix([_trace()])
    assert set(cells) == {("?", "?")}


def test_rendering_prints_an_em_dash_for_an_empty_cell():
    lines = ledger.render_matrix([_trace(model="opus-5", effort="low")],
                                 prices=None)
    row = next(ln for ln in lines if ln.strip().startswith("opus-5"))
    assert "—" in row, "an empty cell is drawn, not skipped"


def test_rendering_states_price_absence_rather_than_implying_it():
    lines = ledger.render_matrix([_trace(model="opus-5", effort="low")],
                                 prices=None)
    assert any("prices.local.json" in ln and "not computed" in ln
               for ln in lines)


def test_rendering_computes_cost_at_report_time_from_a_dated_price_table():
    t = _trace(model="opus-5", effort="low", content_pages=10,
               output_tokens=100_000, input_tokens=1_000_000)
    prices = {"opus-5": {"input_per_mtok": 15.0, "output_per_mtok": 75.0,
                         "date": "2026-08-15"}}
    lines = ledger.render_matrix([t], prices=prices)
    joined = "\n".join(lines)
    # (1.0 mtok × $15) + (0.1 mtok × $75) = $22.50, over 10 content pages
    assert "2.25" in joined
    assert "2026-08-15" in joined, "the cost is labelled with the price date"


def test_a_model_with_no_price_row_is_stated_not_skipped():
    t = _trace(model="mystery-model", effort="low")
    prices = {"opus-5": {"input_per_mtok": 15.0, "output_per_mtok": 75.0,
                         "date": "2026-08-15"}}
    lines = ledger.render_matrix([t], prices=prices)
    assert any("mystery-model" in ln and "no price" in ln for ln in lines)


def test_a_run_without_input_tokens_counts_for_tokens_but_not_for_cost():
    """Input tokens are most of the bill; a cost computed without them would
    understate silently. Such a run stays in the token median and is excluded
    from the cost one, with its own n saying so."""
    with_in = _trace("t-000000000001", model="m", effort="low",
                     content_pages=10, output_tokens=100_000,
                     input_tokens=1_000_000)
    without = _trace("t-000000000002", model="m", effort="low",
                     content_pages=10, output_tokens=100_000)
    _m, _e, cells = ledger.matrix([with_in, without])
    rows = cells[("m", "low")]
    assert len(rows) == 2
    price = {"input_per_mtok": 15.0, "output_per_mtok": 75.0,
             "date": "2026-08-15"}
    med, n = ledger.cell_cost(rows, price)
    assert n == 1
    assert med == 2.25


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
