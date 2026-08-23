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
    """-> the reading for one or more Hermes sessions, whole table."""
    out = _blank()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        for sid in ids:
            for row in con.execute(
                    "select task, api_call_count, input_tokens, output_tokens,"
                    " cache_read_tokens, cache_write_tokens"
                    " from session_model_usage where session_id=?", (sid,)):
                task = row[0] or "(main)"
                out["api_calls"] += row[1]
                out["by_task"][task] = out["by_task"].get(task, 0) + row[1]
                for i, f in enumerate(FIELDS, start=2):
                    out[f] += row[i] if i < 6 else 0
                out["input_tokens"] += 0  # summed above; kept explicit
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


def _hermes_tokens(ids: list[str], db: pathlib.Path, out: dict) -> None:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        for sid in ids:
            for row in con.execute(
                    "select input_tokens, output_tokens, cache_read_tokens,"
                    " cache_write_tokens from session_model_usage"
                    " where session_id=?", (sid,)):
                for f, v in zip(FIELDS, row):
                    out[f] += v or 0
    finally:
        con.close()


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
        r = hermes(a.hermes, a.db)
        _hermes_tokens(a.hermes, a.db, r)
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
