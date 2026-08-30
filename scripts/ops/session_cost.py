#!/usr/bin/env python3
"""What one build actually cost, in the same units on either platform.

**Two counting traps, one each, and both of them fooled us.**

*Claude Code* writes its transcript as JSONL with **one record per content
block** — a thinking block, a text block and three tool calls from one API
response become five records, each repeating the *same* `usage` object. A
counter that sums per record therefore multiplies both the call count and every
token figure. Measured on one build: 187 "calls" that were 70, and token totals
inflated 2.5-3.6x. This dedupes by `message.id` before summing.

*Hermes* keeps per-`(model, task)` rows in `~/.hermes/state.db`. The `task`
column separates the main loop from `approval`, `background_review`,
`compression`, `title_generation` and `vision`, and a reading that names only
the main row understates the session — `background_review` alone was 12 calls
and 2M cache_read on one build. This sums the whole table, and prints the split
so nothing is hidden rather than excluded.

**And the two are still not directly comparable**, which is the third trap. An
API call is not a unit of work: Hermes batches 1.4-2.0 tool calls into one call,
Claude Code 1.6. So this reports tool calls beside API calls, and the
distribution of tools per call, because that is the number that says how much
was actually done.

    python3 scripts/ops/session_cost.py --hermes 20260823_232927_e413bd [more…]
    python3 scripts/ops/session_cost.py --claude ~/.claude/projects/…/x.jsonl
    python3 scripts/ops/session_cost.py --claude <file> --since <epoch> --until <epoch>

Several ids or files sum into one reading: a task split across two sessions is
one task, and reporting the cheaper half is how a 130 became a 37.
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import argparse  # noqa: E402
import collections  # noqa: E402
import datetime as _dt  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import pathlib  # noqa: E402
import sqlite3  # noqa: E402
import sys  # noqa: E402

FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens",
          "cache_creation_input_tokens")
# Hermes names two of them differently; one vocabulary out.
HERMES_FIELD = {"input_tokens": "input_tokens",
                "output_tokens": "output_tokens",
                "cache_read_input_tokens": "cache_read_tokens",
                "cache_creation_input_tokens": "cache_write_tokens"}


def _blank() -> dict:
    return {"api_calls": 0, "tool_calls": 0,
            **dict.fromkeys(FIELDS, 0),
            "per_call": collections.Counter(), "by_task": {}}


def hermes(ids: list[str], db: pathlib.Path) -> dict:
    """-> the reading for one or more Hermes sessions, whole table.

    **One pass over `session_model_usage`, and only one.** Until 0.1.592 this
    summed the four token fields and a second reader summed the SAME rows into
    the SAME dict afterwards, so every token came back exactly doubled while
    `api_calls` and `tool_calls` stayed correct. That is the worst shape an
    instrument can fail in: the counts look sane, so the doubling reads as real
    usage rather than as a bug. It survived two releases and was caught in the
    field, by a platform comparison that halved the numbers by hand and put the
    correction in a footnote — which is a reader doing the tool's job.

    The two functions are merged rather than one of them trimmed, because the
    defect was not a stray line: it was two readers of one table sharing one
    accumulator. Trimming leaves that shape in place for the next edit to
    re-grow. `tests/test_session_cost_hermes.py` pins the reading.
    """
    out = _blank()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        for sid in ids:
            for row in con.execute(
                    "select task, api_call_count, input_tokens, output_tokens,"
                    " cache_read_tokens, cache_write_tokens"
                    " from session_model_usage where session_id=?", (sid,)):
                task = row[0] or "(main)"
                # `or 0` on the COUNT as well as the tokens below. The merge
                # that removed the double-count guarded the tokens and left
                # these two unguarded, so one NULL `api_call_count` in a real
                # state store took the whole reading down with a TypeError.
                calls = row[1] or 0
                out["api_calls"] += calls
                out["by_task"][task] = out["by_task"].get(task, 0) + calls
                # row[2:] is (input, output, cache_read, cache_write) — the
                # Hermes column order, which is FIELDS' order under
                # HERMES_FIELD. Summed HERE and nowhere else.
                for f, v in zip(FIELDS, row[2:]):
                    out[f] += v or 0
            # The tool side: one row per tool result, and the assistant rows
            # carry the batched call arrays.
            for (blob,) in con.execute(
                    "select tool_calls from messages where session_id=?"
                    " and tool_calls is not null", (sid,)):
                try:
                    calls = json.loads(blob)
                except (TypeError, ValueError):
                    continue
                out["tool_calls"] += len(calls)
                out["per_call"][len(calls)] += 1
    finally:
        con.close()
    return out


def claude(paths: list[pathlib.Path], since=None, until=None) -> dict:
    """-> the reading for one or more Claude Code transcripts.

    **Deduped by `message.id`.** Every record of one response repeats that
    response's usage; summing per record is the error this exists to prevent.
    """
    out = _blank()
    seen: set[str] = set()
    for p in paths:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message") or {}
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    out["tool_calls"] += 1
            mid = msg.get("id")
            usage = msg.get("usage")
            if not mid or not isinstance(usage, dict) or mid in seen:
                continue
            seen.add(mid)
            out["api_calls"] += 1
            for f in FIELDS:
                out[f] += usage.get(f, 0) or 0
    # Tools per API call, recomputed over the deduped groups.
    for p in paths:
        per: dict = collections.defaultdict(int)
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line.strip() or "{}")
            except ValueError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message") or {}
            mid = msg.get("id")
            if not mid:
                continue
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    per[mid] += 1
        for mid in per:
            out["per_call"][per[mid]] += 1
    return out



DOMINANT_SHARE = 0.8  # a build's model is the one with >=80% of in-window output
                      # tokens; below that, several models really shared the work
                      # and the honest record is null (the board's '?' bucket).


def _parse_iso(s: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def build_window_cost(paths, intervals: list, share=DOMINANT_SHARE):
    """-> {"usage", "model", "effort", "transcripts"} for the turns inside
    `intervals` ([start_iso, stop_iso] pairs) across `paths` — a REAL build's
    cost (R7) — or None when nothing falls in-window.

    **`paths` is a LIST because one session's cost is not in one file.** Claude
    Code writes subagent turns to `<session>/subagents/*.jsonl` beside the main
    transcript; reading only the main file dropped a MEDIAN 9% of a build's
    tokens and 59% on the worst session — measured by the 0.1.658 pre-PR review
    over the 20 sessions of this project that have subagents (442 subagent
    transcripts), deduped by message.id across all four token fields — and
    reported the remainder as the whole bill. That is this module's own docstring warning — "reporting the
    cheaper half is how a 130 became a 37" — one directory over, so `claude()`
    and this take the same shape. Dedup by `message.id` spans all of them.

    The number is EVIDENCE-BACKED: given the same (paths, intervals) anyone
    re-derives it. `usage` uses `trace.py close --usage` field names via
    HERMES_FIELD (one home) and keeps None for a cache field NO in-window record
    carried — per field, never one flag for both, because `... or 0` must not
    write a "0" claim over "the CLI did not say". A field only SOME records
    carried is summed and said so on stderr: a partial total presented as
    complete is neither a silence nor a number. `model` is the output-dominant
    model when its share clears `share`, else None with the split reported.
    """
    try:
        spans = [(_parse_iso(a), _parse_iso(b)) for a, b in intervals]
    except (TypeError, ValueError) as exc:
        print(f"note  build cost: a phase window is unreadable ({exc}) — "
              f"recorded nothing", file=sys.stderr)
        return None
    if not spans:
        return None
    if isinstance(paths, (str, pathlib.Path)):
        paths = [paths]
    totals = dict.fromkeys(FIELDS, 0)
    carried: collections.Counter = collections.Counter()
    by_model_out: collections.Counter = collections.Counter()
    by_effort_out: collections.Counter = collections.Counter()
    seen: set = set()
    for path in paths:
        try:
            handle = path.open(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"note  build cost: {path.name} could not be read ({exc}) — "
                  f"its turns are not counted", file=sys.stderr)
            continue
        with handle:
            for line in handle:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                # The same acceptance rule `claude()` uses, deliberately: two
                # readers of one format with different rules is a defect waiting
                # for the CLI to add a record type that echoes usage.
                if rec.get("type") != "assistant":
                    continue
                ts = rec.get("timestamp")
                if not isinstance(ts, str):
                    continue
                try:
                    when = _parse_iso(ts)
                except ValueError:
                    continue
                if when.tzinfo is None:
                    continue  # a naive stamp cannot be compared to an aware span
                if not any(lo <= when <= hi for lo, hi in spans):
                    continue
                msg = rec.get("message")
                if not isinstance(msg, dict):
                    continue
                usage, mid = msg.get("usage"), msg.get("id")
                if not mid or mid in seen or not isinstance(usage, dict):
                    continue
                seen.add(mid)
                for f in FIELDS:
                    v = usage.get(f)
                    if f in usage:
                        carried[f] += 1
                    # A non-int is the CLI saying something unreadable; count it
                    # as nothing rather than crashing the close on a TypeError.
                    totals[f] += v if isinstance(v, int) and not isinstance(v, bool) else 0
                out = usage.get("output_tokens")
                out_tokens = out if isinstance(out, int) and not isinstance(out, bool) else 0
                model = msg.get("model")
                if model:
                    by_model_out[model] += out_tokens
                if rec.get("effort"):
                    # WEIGHTED, not last-write-wins. Now that subagent
                    # transcripts are read, a 5-token subagent at `low` was
                    # overwriting a 10,000-token main session at `xhigh` —
                    # whichever record happened to be read last won, silently,
                    # while `model` beside it had a dominance rule. Same axis,
                    # same treatment.
                    by_effort_out[rec["effort"]] += out_tokens
    if not seen:
        return None

    def _optional(name: str):
        """A CACHE field: None when no in-window record carried it — `_read_usage`
        reads absence as "the CLI did not say" and a 0 would be a claim. A field
        only SOME records carried is summed and said so: a partial total passed
        off as complete is neither a silence nor a number."""
        if carried[name] == 0:
            return None
        if carried[name] != len(seen):
            print(f"note  build cost: {name} on {carried[name]}/{len(seen)} "
                  f"in-window responses — the total is partial", file=sys.stderr)
        return totals[name]

    # THE TWO MANDATORY FIELDS ARE NEVER None. `_read_usage` requires both and
    # refuses a trace that records half the bill, so routing them through the
    # optional helper only moved the abort: a window whose records lacked
    # `input_tokens` produced an absent key and the close refused it. A zero here
    # is not a claim about a CLI that stayed silent — it is the sum over the
    # window's responses, which is what these two mean.
    usage_out: dict = {
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        HERMES_FIELD["cache_read_input_tokens"]: _optional("cache_read_input_tokens"),
        HERMES_FIELD["cache_creation_input_tokens"]:
            _optional("cache_creation_input_tokens"),
    }
    model = None
    if by_model_out:
        top, top_out = by_model_out.most_common(1)[0]
        total_out = sum(by_model_out.values())
        if total_out and top_out / total_out >= share:
            model = top
        else:
            split = ", ".join(f"{m} {v * 100 // max(1, total_out)}%"
                              for m, v in by_model_out.most_common(3))
            print(f"note  build cost: no dominant model ({split}) — recorded "
                  f"none rather than one label over several", file=sys.stderr)
    effort = None
    if by_effort_out:
        top_e, top_e_out = by_effort_out.most_common(1)[0]
        total_e = sum(by_effort_out.values())
        # No output tokens anywhere (a window of empty responses): fall back to
        # the only level seen, since there is no weight to judge by.
        if total_e == 0:
            effort = top_e if len(by_effort_out) == 1 else None
        elif top_e_out / total_e >= share:
            effort = top_e
    return {"usage": usage_out, "model": model, "effort": effort,
            "transcripts": len(list(paths))}


def report(label: str, r: dict) -> None:
    calls = max(1, r["api_calls"])
    print(f"\n{label}")
    print(f"  API calls        {r['api_calls']:>12,}")
    print(f"  tool calls       {r['tool_calls']:>12,}"
          f"   ({r['tool_calls'] / calls:.2f} per API call)")
    for f in FIELDS:
        print(f"  {f:<16} {r[f]:>12,}")
    if r["by_task"]:
        print("  by task          " + ", ".join(
            f"{k}={v}" for k, v in sorted(r["by_task"].items(),
                                          key=lambda kv: -kv[1])))
    if r["per_call"]:
        print("  tools per call   " + ", ".join(
            f"{k}:{v}" for k, v in sorted(r["per_call"].items())))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hermes", nargs="+", metavar="SESSION_ID",
                    help="one or more Hermes session ids; summed")
    ap.add_argument("--claude", nargs="+", type=pathlib.Path,
                    metavar="TRANSCRIPT.jsonl",
                    help="one or more Claude Code transcripts; summed")
    ap.add_argument("--db", type=pathlib.Path,
                    default=pathlib.Path(os.environ.get("HERMES_STATE_DB")
                                         or pathlib.Path.home()
                                         / ".hermes" / "state.db"),
                    help="Hermes state store")
    a = ap.parse_args(argv)
    if not a.hermes and not a.claude:
        ap.error("give --hermes or --claude (or both, to compare)")

    if a.hermes:
        if not a.db.is_file():
            sys.exit(f"no Hermes state store at {a.db}")
        # A SESSION ID THAT MATCHES NOTHING IS A TYPO, NOT A FREE BUILD. Without
        # this an unknown id printed a whole zero table under a "1 session(s)"
        # header and exited 0 — a reading that says the work cost nothing. The
        # Claude branch below already hard-exits on a transcript it cannot find;
        # this is the same rule on the other platform.
        con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
        try:
            empty = [sid for sid in a.hermes if not con.execute(
                "select 1 from session_model_usage where session_id=? limit 1",
                (sid,)).fetchone()]
        finally:
            con.close()
        if empty:
            sys.exit("no rows for session id(s): " + ", ".join(empty)
                     + "\n  A reading of zero is not the same as no reading. "
                       "Check the id against the store's own sessions table.")
        r = hermes(a.hermes, a.db)
        report(f"hermes · {len(a.hermes)} session(s)", r)
    if a.claude:
        missing = [p for p in a.claude if not p.is_file()]
        if missing:
            sys.exit("no such transcript: " + ", ".join(str(p) for p in missing))
        report(f"claude-code · {len(a.claude)} transcript(s)", claude(a.claude))
    print("\n  An API call is not a unit of work: the two platforms batch "
          "differently.\n  Read `tool calls` beside it, and the distribution "
          "under it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
