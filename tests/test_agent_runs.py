"""What a configuration costs — the agent half, moved out of the document half.

These thirteen tests were in `tests/test_ledger.py`, calling `ledger.matrix`,
`ledger.render_matrix` and `ledger.board`, because the model x effort cost
matrix lived in the tool that answers three questions about DOCUMENTS. The code
moved to `scripts/lib/agent_runs.py` and the tests moved with it.

**The reason is that the file would have split in half, silently.** `ledger`
re-exports `board`, `render_matrix` and `load_prices` — the three its own
report needs — and NOT `matrix` or `cell_cost`. So seven of these would have
gone on passing against the old address and six would have raised
`AttributeError`, which is a worse outcome than either whole answer. (An earlier
version of this paragraph said all thirteen would have passed, which is the
same class of unread claim a review has now caught twice on this branch.)

The load-bearing one is `test_a_run_with_a_failing_gate_is_not_on_the_board`:
the DOCUMENT's verdict is the admission ticket to the AGENT's board. Lose it and
the cheapest way to the top of the board is to write thinner decks.
"""
import agent_runs
import pytest


def _trace(tid="t-000000000001", **kw):
    base = {"trace_id": tid, "closed_at": "2026-08-16T00:00:00+00:00",
            # A PASSING GATE, not an empty dict. Every fixture in this file
            # carried `{}` and every one of them reached the board through
            # `any({}.values())` being False — the suite was proving the
            # admission ticket worked while holding no ticket. A test that
            # means "nobody measured this run" now says `gates={}` out loud.
            "gates": {"D12_commercial_footer": "ok"},
            "graded": {}, "thresholds": {},
            "principle_yields": [], "refused_to_emit": None,
            "content_pages": 10, "output_tokens": 30000,
            "phase_seconds": {"build": 300}}
    base.update(kw)
    return base


def test_a_run_with_a_failing_gate_is_not_on_the_board():
    """A thin deck is cheap and worthless; rewarding it would invert the point."""
    good = _trace("t-000000000001")
    bad = _trace("t-000000000002", gates={"D14_placeholders": "FAIL"},
                 output_tokens=100)
    ids = [r["trace_id"] for r in agent_runs.board([good, bad])]
    assert ids == ["t-000000000001"]


def test_discussion_and_outline_are_not_charged():
    t = _trace(phase_seconds={"discussion": 900, "outline": 600,
                              "build": 300, "checks": 60})
    assert agent_runs.board([t])[0]["charged_seconds"] == 360


def test_an_unclosed_trace_is_not_on_the_board():
    """Half of a test that used to assert across the seam.

    It checked both that an unclosed trace counts as an abandoned build (a
    DOCUMENT-side fact, `ledger_signals`) and that it is off the cost board (an
    AGENT-side fact). One assertion per side now, each in its own file — the
    original could not have been moved without dragging the document tool into
    this one, which is the mixing the move exists to end.
    """
    assert agent_runs.board([_trace(closed_at=None)]) == []


# The model × effort matrix (K1): quality and cost columns produced together.
# The board's quality line is the matrix's quality line — one implementation —
# and cost exists only at render time, computed from a local dated price
# table, because `cost_usd` was deleted from the schema for going stale the
# day the price does.


def test_matrix_groups_by_model_and_effort():
    traces = [_trace("t-000000000001", model="opus-5", effort="high"),
              _trace("t-000000000002", model="opus-5", effort="low"),
              _trace("t-000000000003", model="sonnet-5", effort="high")]
    _models, _efforts, cells = agent_runs.matrix(traces)
    assert set(cells) == {("opus-5", "high"), ("opus-5", "low"),
                          ("sonnet-5", "high")}


def test_matrix_effort_columns_are_the_schema_s_own_plus_unknown():
    """Read from trace_schema.ENUMS, never retyped — a retyped effort list is
    the sixth-literal-copy defect the genre vocabulary already had."""
    from trace_schema import ENUMS
    _models, efforts, _cells = agent_runs.matrix([_trace(model="m", effort="low")])
    assert efforts == (*ENUMS["effort"], "?")


def test_matrix_cell_is_the_median_of_tokens_per_page():
    traces = [
        _trace("t-000000000001", model="m", effort="low",
               content_pages=10, output_tokens=100),   # 10.0 t/p
        _trace("t-000000000002", model="m", effort="low",
               content_pages=10, output_tokens=200),   # 20.0 t/p
        _trace("t-000000000003", model="m", effort="low",
               content_pages=10, output_tokens=400),   # 40.0 t/p
    ]
    _m, _e, cells = agent_runs.matrix(traces)
    rows = cells[("m", "low")]
    assert len(rows) == 3
    import statistics
    assert statistics.median(r["tokens_per_page"] for r in rows) == 20.0


def test_a_run_with_a_failing_gate_is_not_in_the_matrix():
    """The board's line holds here too: a thin deck must not set the median."""
    good = _trace("t-000000000001", model="m", effort="low")
    bad = _trace("t-000000000002", model="m", effort="low",
                 gates={"D14_placeholders": "FAIL"}, output_tokens=100)
    _m, _e, cells = agent_runs.matrix([good, bad])
    assert [r["trace_id"] for r in cells[("m", "low")]] == ["t-000000000001"]


def test_a_run_with_no_model_or_effort_groups_under_question_mark():
    _m, _e, cells = agent_runs.matrix([_trace()])
    assert set(cells) == {("?", "?")}


def test_rendering_prints_an_em_dash_for_an_empty_cell():
    lines = agent_runs.render_matrix([_trace(model="opus-5", effort="low")],
                                 prices=None)
    row = next(ln for ln in lines if ln.strip().startswith("opus-5"))
    assert "—" in row, "an empty cell is drawn, not skipped"


def test_rendering_states_price_absence_rather_than_implying_it():
    lines = agent_runs.render_matrix([_trace(model="opus-5", effort="low")],
                                 prices=None)
    assert any("prices.local.json" in ln and "not computed" in ln
               for ln in lines)


def test_rendering_computes_cost_at_report_time_from_a_dated_price_table():
    t = _trace(model="opus-5", effort="low", content_pages=10,
               output_tokens=100_000, input_tokens=1_000_000)
    prices = {"opus-5": {"input_per_mtok": 15.0, "output_per_mtok": 75.0,
                         "date": "2026-08-15"}}
    lines = agent_runs.render_matrix([t], prices=prices)
    joined = "\n".join(lines)
    # (1.0 mtok × $15) + (0.1 mtok × $75) = $22.50, over 10 content pages
    assert "2.25" in joined
    assert "2026-08-15" in joined, "the cost is labelled with the price date"


def test_a_model_with_no_price_row_is_stated_not_skipped():
    t = _trace(model="mystery-model", effort="low")
    prices = {"opus-5": {"input_per_mtok": 15.0, "output_per_mtok": 75.0,
                         "date": "2026-08-15"}}
    lines = agent_runs.render_matrix([t], prices=prices)
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
    _m, _e, cells = agent_runs.matrix([with_in, without])
    rows = cells[("m", "low")]
    assert len(rows) == 2
    price = {"input_per_mtok": 15.0, "output_per_mtok": 75.0,
             "date": "2026-08-15"}
    med, n = agent_runs.cell_cost(rows, price)
    assert n == 1
    assert med == 2.25


# The four-beat design's own falsification data was recorded and never read.
# `outline_reviewed` exists so that skipping beat 4 — the only defence
# completeness has — is a countable fact rather than an invisible choice, and
# nothing counted it. `titles_changed_after_approval` is the sharper of the
# two: a review agreed and then departed from is not a review.


# `load_prices` had no test of its own, and its two failure states are the
# whole reason it is a function rather than a `json.loads`. Both are pinned by
# repointing `PRICES` — the module reads it at call time, so a monkeypatch of
# the module attribute is the real path and not a stand-in.

def test_no_price_table_is_none_rather_than_an_empty_table(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_runs, "PRICES", tmp_path / "absent.json")
    assert agent_runs.load_prices() is None, (
        "an empty dict here would make 'no table' and 'a table pricing nothing' "
        "the same value, and render_matrix says different words for each")


def test_an_unparseable_price_table_exits_rather_than_pricing_nothing(
        tmp_path, monkeypatch):
    bad = tmp_path / "prices.local.json"
    bad.write_text('{"opus-5": {"in": 5.0,\n', encoding="utf-8")
    monkeypatch.setattr(agent_runs, "PRICES", bad)
    with pytest.raises(SystemExit) as caught:
        agent_runs.load_prices()
    message = str(caught.value)
    assert "not JSON" in message and "prices.local.json" in message, (
        f"the exit must name the file and the fault; it said {message!r}")


def test_a_run_that_recorded_no_gates_at_all_is_not_on_the_board():
    """The admission ticket's own hole. `any()` over an empty dict is False, so
    until 0.1.620 a run that recorded NO verdicts cleared the quality line
    vacuously — and a run nobody measured is the cheapest thin deck there is.
    Measured 2026-08-27: 0 of the 31 admitted rows on disk, so this closes a
    branch rather than changing a number. It would have opened the first time a
    driver timed out before the checks ran."""
    assert agent_runs.board([_trace(gates={})]) == []
    assert len(agent_runs.board([_trace(gates={"D12_commercial_footer": "ok"})])) == 1
