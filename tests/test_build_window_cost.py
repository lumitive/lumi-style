"""R7's build-window reader: a real build's cost, over exactly the build turns.

The number must be re-derivable from (transcript, window) by anyone — these tests
use a SYNTHETIC transcript so they are deterministic on any machine (the real
one is read only at build time; a test that read it would be the GAP-050
operator-state fragility class).
"""
import json
import pathlib

import session_cost


def _transcript(tmp_path: pathlib.Path, records: list) -> pathlib.Path:
    p = tmp_path / "session.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return p


def _rec(ts, mid, model, out, *, cache=True, effort="high"):
    usage = {"input_tokens": 10, "output_tokens": out}
    if cache:
        usage["cache_read_input_tokens"] = 1000
        usage["cache_creation_input_tokens"] = 100
    return {"type": "assistant", "timestamp": ts, "effort": effort,
            "message": {"id": mid, "role": "assistant", "model": model, "usage": usage}}


def test_the_window_carves_the_build_slice(tmp_path):
    """A record outside the window does not count."""
    t = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "m1", "claude-opus-5", 500),   # in
        _rec("2026-08-30T09:00:00.000Z", "m2", "claude-opus-5", 999),   # out
    ])
    r = session_cost.build_window_cost(
        t, [["2026-08-30T00:30:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["usage"]["output_tokens"] == 500, "the out-of-window record leaked in"
    assert r["model"] == "claude-opus-5" and r["effort"] == "high"


def test_dedup_by_message_id(tmp_path):
    """Every record of one response repeats its usage; it counts once."""
    t = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "same", "claude-opus-5", 500),
        _rec("2026-08-30T01:00:01.000Z", "same", "claude-opus-5", 500),
    ])
    r = session_cost.build_window_cost(
        t, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["usage"]["output_tokens"] == 500, "a repeated message.id was double-counted"


def test_absent_cache_stays_none_not_zero(tmp_path):
    """None is 'the CLI did not say'; 0 would be a claim of no cache."""
    t = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "m1", "claude-opus-5", 500, cache=False)])
    r = session_cost.build_window_cost(
        t, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["usage"]["cache_read_tokens"] is None
    assert r["usage"]["cache_write_tokens"] is None
    assert r["usage"]["output_tokens"] == 500


def test_dominant_model_recorded_split_is_null(tmp_path):
    """One model with >=80% of output is the build's model; a real split is null
    (the board's '?' bucket), and the full split stays re-derivable."""
    dominant = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "a", "claude-opus-5", 900),
        _rec("2026-08-30T01:00:02.000Z", "b", "claude-fable-5", 100)])  # 90% opus
    r = session_cost.build_window_cost(
        dominant, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["model"] == "claude-opus-5"

    split = tmp_path / "split.jsonl"
    split.write_text("\n".join(json.dumps(x) for x in [
        _rec("2026-08-30T01:00:00.000Z", "a", "claude-opus-5", 500),
        _rec("2026-08-30T01:00:02.000Z", "b", "claude-fable-5", 500)]) + "\n",
        encoding="utf-8")
    r2 = session_cost.build_window_cost(
        split, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r2["model"] is None, "a 50/50 split must not claim one model"


def test_subagent_transcripts_are_counted_too(tmp_path):
    """A session's cost is NOT in one file: Claude Code writes subagent turns to
    a sibling directory. Reading only the main transcript dropped a measured
    median 9% of a build's tokens (59% on the worst session) and reported the
    rest as the whole bill — the review's CRITICAL finding."""
    main = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "m1", "claude-opus-5", 500)])
    sub = tmp_path / "sub.jsonl"
    sub.write_text(json.dumps(
        _rec("2026-08-30T01:00:30.000Z", "s1", "claude-opus-5", 300)) + "\n",
        encoding="utf-8")
    window = [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]]
    assert session_cost.build_window_cost([main], window)["usage"]["output_tokens"] == 500
    both = session_cost.build_window_cost([main, sub], window)
    assert both["usage"]["output_tokens"] == 800, "the subagent's tokens were dropped"
    assert both["transcripts"] == 2, "the transcript count is the layout's own evidence"


def test_a_cache_field_only_some_records_carry_is_not_a_zero_claim(tmp_path):
    """One flag for two fields wrote `cache_write_tokens: 0` — a claim of 'no
    cache writes' about a CLI that never said. Per-field presence, so a wholly
    absent field stays None while a present one sums."""
    half = {"type": "assistant", "timestamp": "2026-08-30T01:00:00.000Z",
            "effort": "high",
            "message": {"id": "m1", "role": "assistant", "model": "claude-opus-5",
                        "usage": {"input_tokens": 1, "output_tokens": 2,
                                  "cache_read_input_tokens": 9}}}
    t = _transcript(tmp_path, [half])
    r = session_cost.build_window_cost(
        t, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["usage"]["cache_read_tokens"] == 9
    assert r["usage"]["cache_write_tokens"] is None, (
        "a field no record carried must stay None, never a 0 claim")


def test_a_malformed_window_degrades_instead_of_crashing(tmp_path):
    """OR-8c: a cost read must never fail a delivery whose document is fine.
    `validate` only checks the interval entries are strings, so an unparseable
    one reaches here — it must return None, not raise."""
    t = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "m1", "claude-opus-5", 500)])
    assert session_cost.build_window_cost(t, [["not-a-time", "also-not"]]) is None
    assert session_cost.build_window_cost(t, [["2026-08-30T00:00:00+00:00"]]) is None


def test_a_non_assistant_record_is_not_counted(tmp_path):
    """The same acceptance rule `claude()` uses — two readers of one format with
    different rules is a defect waiting for a new record type that echoes usage."""
    rec = _rec("2026-08-30T01:00:00.000Z", "m1", "claude-opus-5", 500)
    rec["type"] = "summary"
    t = _transcript(tmp_path, [rec])
    assert session_cost.build_window_cost(
        t, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]]) is None


def test_a_non_integer_token_count_does_not_crash_the_close(tmp_path):
    """A string where an integer belongs is the CLI saying something unreadable;
    count it as nothing rather than raising into the delivery's close."""
    bad = {"type": "assistant", "timestamp": "2026-08-30T01:00:00.000Z",
           "message": {"id": "m1", "role": "assistant", "model": "claude-opus-5",
                       "usage": {"input_tokens": "lots", "output_tokens": 7}}}
    r = session_cost.build_window_cost(
        _transcript(tmp_path, [bad]),
        [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["usage"]["output_tokens"] == 7 and r["usage"]["input_tokens"] == 0


def test_the_readers_output_is_accepted_by_the_close_that_consumes_it(tmp_path):
    """THE JUNCTION, which nothing tested: the reader spells 'the CLI did not
    say' as None, and `trace.py close --usage` spells it as an ABSENT key and
    REFUSES a present null. Dumping None verbatim aborted the close on a build
    whose document was fine — two well-guarded functions whose guards
    contradicted each other. The writer drops nulls; this pins that contract."""
    import trace_schema  # noqa: F401 — same import surface as the writer
    no_cache = {"type": "assistant", "timestamp": "2026-08-30T01:00:00.000Z",
                "message": {"id": "m1", "role": "assistant",
                            "model": "claude-opus-5",
                            "usage": {"input_tokens": 5, "output_tokens": 50}}}
    cost = session_cost.build_window_cost(
        _transcript(tmp_path, [no_cache]),
        [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert cost["usage"]["cache_read_tokens"] is None
    payload = {k: v for k, v in cost["usage"].items() if v is not None}
    assert "cache_read_tokens" not in payload, (
        "a null must be dropped, not written — close refuses a present null")
    assert payload == {"input_tokens": 5, "output_tokens": 50}


def test_the_two_mandatory_fields_are_never_none(tmp_path):
    """`_read_usage` REQUIRES input_tokens and output_tokens ("a trace that
    records half the bill reads as a cheaper build than the one that happened").
    Routing them through the optional-cache helper only moved the abort: a
    window whose records lacked one produced an absent key and the close refused
    it. They are sums over the window, so 0 is the answer, not a silence."""
    no_input = {"type": "assistant", "timestamp": "2026-08-30T01:00:00.000Z",
                "message": {"id": "m1", "role": "assistant", "model": "m",
                            "usage": {"output_tokens": 5}}}
    cost = session_cost.build_window_cost(
        _transcript(tmp_path, [no_input]),
        [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert cost["usage"]["input_tokens"] == 0
    payload = {k: v for k, v in cost["usage"].items() if v is not None}
    assert "input_tokens" in payload and "output_tokens" in payload, (
        "a mandatory field was dropped by the null-filter — the close refuses that")


def test_one_naive_timestamp_does_not_zero_the_whole_reading(tmp_path):
    """A timestamp with no timezone cannot be compared to an aware window; it
    raises `TypeError` one line past the parse guard, `_build_cost` catches it,
    and the build records NO cost at all. One malformed record silently zeroing
    the reading is the wrong trade — skip the record, keep the build."""
    good = _rec("2026-08-30T01:00:00.000Z", "good", "claude-opus-5", 500)
    naive = _rec("2026-08-30T01:00:05", "naive", "claude-opus-5", 999)  # no Z
    r = session_cost.build_window_cost(
        _transcript(tmp_path, [good, naive]),
        [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r is not None, "one bad record must not zero the whole reading"
    assert r["usage"]["output_tokens"] == 500


def test_effort_is_weighted_not_last_write_wins(tmp_path):
    """`model` had a dominance rule and `effort` beside it took whichever record
    was read LAST — so once subagent transcripts were included, a 5-token
    subagent at `low` overwrote a 10,000-token session at `xhigh`, silently."""
    main = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "a", "claude-opus-5", 10000, effort="xhigh")])
    sub = tmp_path / "sub.jsonl"
    sub.write_text(json.dumps(
        _rec("2026-08-30T01:00:05.000Z", "b", "claude-opus-5", 5, effort="low")) + "\n",
        encoding="utf-8")
    r = session_cost.build_window_cost(
        [main, sub], [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["effort"] == "xhigh", "a tiny subagent must not set the build's effort"


def test_the_dominance_boundary_is_inclusive(tmp_path):
    """Exactly at the share, the model is recorded — pins `>=` against a drift
    to `>`, which the 90/10 and 50/50 cases cannot see."""
    t = _transcript(tmp_path, [
        _rec("2026-08-30T01:00:00.000Z", "a", "claude-opus-5", 800),
        _rec("2026-08-30T01:00:02.000Z", "b", "claude-fable-5", 200)])
    r = session_cost.build_window_cost(
        t, [["2026-08-30T00:00:00+00:00", "2026-08-30T02:00:00+00:00"]])
    assert r["model"] == "claude-opus-5", "exactly 80% must clear the bar"


def test_no_in_window_record_returns_none(tmp_path):
    """OR-8c: nothing to record is None, and the caller says so — never a 0."""
    t = _transcript(tmp_path, [
        _rec("2026-08-30T09:00:00.000Z", "m1", "claude-opus-5", 500)])
    assert session_cost.build_window_cost(
        t, [["2026-08-30T00:00:00+00:00", "2026-08-30T01:00:00+00:00"]]) is None
    assert session_cost.build_window_cost(t, []) is None


# --- the DISCOVERY layer: which transcripts get read at all ---
# The summing layer above is handed a list. `_build_cost` builds that list, and
# it had NO test — which is exactly where the subagent defect survived a round
# of review: the flat `glob` found 621 transcripts and missed 638 nested under
# `subagents/workflows/`. A test that hands paths in by hand cannot see that.

def _fake_session(home, sid, records_by_file):
    proj = home / ".claude" / "projects" / "-p"
    proj.mkdir(parents=True)
    for rel, records in records_by_file.items():
        p = proj / rel if rel else proj / f"{sid}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(json.dumps(r) for r in records) + "\n",
                     encoding="utf-8")
    return proj


def test_build_cost_reads_nested_subagent_transcripts(tmp_path, monkeypatch):
    """The discovery layer. Subagent transcripts nest as
    `<sid>/subagents/workflows/wf_x/agent-y.jsonl`; a flat glob missed more of
    them than it found. Anything but a recursive walk undercounts a real build
    and reports the remainder as the whole bill."""
    import check_deliverable
    sid = "s-1111"
    _fake_session(tmp_path, sid, {
        None: [_rec("2026-08-30T01:00:00.000Z", "m", "claude-opus-5", 500)],
        f"{sid}/subagents/agent-flat.jsonl":
            [_rec("2026-08-30T01:00:01.000Z", "f", "claude-opus-5", 300)],
        f"{sid}/subagents/workflows/wf_a/agent-deep.jsonl":
            [_rec("2026-08-30T01:00:02.000Z", "d", "claude-opus-5", 700)],
    })
    traces = tmp_path / "traces"
    traces.mkdir()
    (traces / "t-abc.json").write_text(json.dumps({
        "trace_id": "t-abc",
        "phase_windows": {"build": [["2026-08-30T00:00:00+00:00",
                                     "2026-08-30T02:00:00+00:00"]]}}),
        encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", sid)
    monkeypatch.setattr(check_deliverable.pathlib.Path, "home",
                        classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(check_deliverable.trace_store, "traces_dir",
                        lambda *a, **k: traces)
    cost = check_deliverable._build_cost("t-abc")
    assert cost is not None
    assert cost["usage"]["output_tokens"] == 1500, (
        "the nested subagent's tokens were dropped — a flat glob undercounts")
    assert cost["transcripts"] == 3


def test_build_cost_degrades_without_a_session(tmp_path, monkeypatch):
    """OR-8c: no session id records nothing and never raises."""
    import check_deliverable
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    assert check_deliverable._build_cost("t-abc") is None
