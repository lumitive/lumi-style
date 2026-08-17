#!/usr/bin/env python3
"""Read the traces and keep three ledgers. Draft candidates. Ratify nothing.

This is the analysis half of the evidence ledger. `trace.py` writes what
happened; this reads the accumulated record and answers three questions:

  **Which metric keeps failing** — the same bar missed across runs is either a
  real weakness or a threshold set wrong, and which one it is needs a person.
  **Which instrument may be broken** — a metric that is `not_measured` more
  often than it is measured, or one that never fails on any document, is a
  suspect ruler. Of the last five findings in this repository's history, three
  turned out to be instrument defects, so instruments are checked before
  thresholds and rank above them in the queue.
  **What to change next** — a candidate, drafted with its evidence attached.

**It ratifies nothing.** Every candidate is a draft with trace ids and counts;
the trigger for shipping any of it is a person. That is not a courtesy — the
whole input to this loop comes from the agent being measured, and an automated
path from "the numbers moved" to "the rules changed" would let a bad instrument
rewrite the rules it is failing.

**It does not do statistics.** The real volume is tens of documents a year.
Counting is honest at that scale; inference is not, and the evidence-grade
discipline (`calibrated` / `provisional`) is not suspended because a count got
large enough to look like a sample.

**Queue rules**, because a queue without them fakes health:
  *trigger* — a candidate is drafted per N accumulated pieces of the same
  evidence, never on a schedule. On a schedule it either overflows or sits
  empty, and both look like normal operation.
  *order* — instrument suspicions before threshold changes, then by evidence
  count. A wrong ruler contaminates every measurement taken after it.
  *eviction* — nothing is dropped. Over capacity, a candidate is marked
  deferred and the backlog is printed. A queue that silently empties is
  reporting health it does not have.

Usage
  ledger.py                     # the three ledgers and the queue
  ledger.py --board             # cost per content page, quality-gated
  ledger.py --json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
TRACES = ROOT / "evals" / "traces"

TRIGGER_N = 3          # pieces of the same evidence before a candidate is drafted
QUEUE_CAPACITY = 5     # per cycle; the rest are deferred, never dropped


def load():
    if not TRACES.exists():
        return []
    out = []
    for path in sorted(TRACES.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def ledger_failing(traces):
    """Which metric keeps failing. Counts, with the trace ids attached."""
    hits: dict[str, list[str]] = collections.defaultdict(list)
    for t in traces:
        for bucket in ("gates", "graded"):
            for mid, verdict in (t.get(bucket) or {}).items():
                if str(verdict).upper() == "FAIL":
                    hits[mid].append(t["trace_id"])
    return sorted(hits.items(), key=lambda kv: -len(kv[1]))


def ledger_instruments(traces):
    """Which ruler is suspect. Two shapes, and both need a person to resolve."""
    measured: dict[str, int] = collections.Counter()
    unmeasured: dict[str, int] = collections.Counter()
    ever_failed: set[str] = set()
    for t in traces:
        for mid, value in (t.get("thresholds") or {}).items():
            if value == "n/a":
                continue          # does not apply here; not evidence either way
            if value == "not_measured":
                unmeasured[mid] += 1
            else:
                measured[mid] += 1
        for bucket in ("gates", "graded"):
            for mid, verdict in (t.get(bucket) or {}).items():
                if str(verdict).upper() == "FAIL":
                    ever_failed.add(mid)
    suspects = []
    for mid in sorted(set(measured) | set(unmeasured)):
        runs = measured[mid] + unmeasured[mid]
        if unmeasured[mid] > measured[mid]:
            suspects.append((mid, "more often not measured than measured",
                             f"{unmeasured[mid]}/{runs}"))
        elif runs >= TRIGGER_N and mid not in ever_failed:
            suspects.append((mid, "never fails on any document",
                             f"{runs} run(s)"))
    return suspects


def ledger_beats(traces):
    """-> what the storyline review beat actually did, counted.

    The four-beat design says beat 4 is the ONLY defence completeness has, and
    that the trace records `outline_reviewed` so that skipping it is a
    countable fact rather than an invisible choice. It was recorded and never
    counted: both this field and `titles_changed_after_approval` were written
    faithfully by `trace.py` and read by nothing, for the whole life of the
    design they exist to falsify.

    `titles_changed_after_approval` is the sharper of the two. A review that is
    agreed and then quietly departed from is not a review, and the number says
    how far the built document walked from the storyline somebody approved.
    """
    reviewed = [t for t in traces if t.get("outline_reviewed")]
    drifted = [t for t in traces
               if (t.get("titles_changed_after_approval") or 0) > 0]
    linked = [t for t in traces if t.get("review_ref")]
    by_path = collections.Counter(t.get("entry_path") or "?" for t in traces)
    return {"total": len(traces), "reviewed": len(reviewed),
            "drifted": len(drifted), "review_linked": len(linked),
            "titles_moved": sum(t.get("titles_changed_after_approval") or 0
                                for t in traces),
            "by_entry_path": dict(by_path)}


def ledger_signals(traces):
    """Signals the constitution put here on purpose: refusals, and who yields."""
    refusals = [(t["trace_id"], t["refused_to_emit"]) for t in traces
                if t.get("refused_to_emit")]
    yields: dict[str, int] = collections.Counter()
    for t in traces:
        for y in t.get("principle_yields") or []:
            yields[y["yielded"]] += 1
    abandoned = [t["trace_id"] for t in traces if not t.get("closed_at")]
    return refusals, yields, abandoned



def ledger_recipes(traces):
    """-> rows saying whether each build's recipe was current, old, or unknown.

    A trace's `skill_version` is read from SKILL.md when the trace opens, so it
    always equals HEAD and can never be stale. That is why a replay of a frozen
    recipe used to produce a record indistinguishable from a build made to the
    current constitution: measured, not supposed. `recipe_version` is the
    recipe's OWN stamp, and the three states it produces are different answers,
    not one answer with shades:

      · `current`  — the recipe names the version that graded it;
      · `stale`    — it names an older one, so the build reproduced rules that
                     have since moved, and the entry-path B ruling applies;
      · `unknown`  — it names none. **This is not `current`.** A recipe that
                     never said which rules it was written against has not told
                     us it followed them, and the first real recipe measured
                     here was exactly this case.
      · `none`     — no recipe was given, which is what path A looks like.
    """
    rows = []
    for t in traces:
        rv, sv = t.get("recipe_version"), t.get("skill_version")
        if not t.get("recipe_hash"):
            state = "none"
        elif rv is None:
            state = "unknown"
        elif rv == sv:
            state = "current"
        else:
            state = "stale"
        rows.append({"trace_id": t["trace_id"], "entry_path": t.get("entry_path"),
                     "state": state, "recipe_version": rv, "skill_version": sv})
    return rows

def candidates(traces):
    """Drafts, ordered instrument-first. Each carries the evidence it rests on."""
    drafts = []
    for mid, why, count in ledger_instruments(traces):
        drafts.append({"kind": "instrument", "about": mid,
                       "claim": f"{mid}: {why} ({count})",
                       "evidence_count": TRIGGER_N,
                       "why_first": "a wrong ruler contaminates every "
                                    "measurement taken after it"})
    for mid, ids in ledger_failing(traces):
        if len(ids) >= TRIGGER_N:
            drafts.append({"kind": "threshold", "about": mid,
                           "claim": f"{mid} failed on {len(ids)} run(s) — a real "
                                    f"weakness, or a bar set wrong",
                           "evidence_count": len(ids), "trace_ids": ids[:8]})
    refusals, _yields, _ab = ledger_signals(traces)
    for tid, r in refusals:
        drafts.append({"kind": "clause-collision", "about": "+".join(r["clauses"]),
                       "claim": f"{' and '.join(r['clauses'])} could not both be "
                                f"satisfied at {r['stage']} — the clauses need "
                                f"specifying, not adjudicating",
                       "evidence_count": 1, "trace_ids": [tid]})
    order = {"instrument": 0, "clause-collision": 1, "threshold": 2}
    drafts.sort(key=lambda d: (order[d["kind"]], -d["evidence_count"]))
    for i, d in enumerate(drafts):
        d["state"] = "queued" if i < QUEUE_CAPACITY else "deferred"
    return drafts


def board(traces):
    """Cost per content page — and only for runs that passed the quality line.

    A thin deck is cheap and worthless. An efficiency board that admitted one
    would reward exactly the behaviour every other check here exists to catch,
    so a run with a failing gate is not on the board at all.
    """
    rows = []
    for t in traces:
        if not t.get("closed_at"):
            continue
        if any(str(v).upper() == "FAIL" for v in (t.get("gates") or {}).values()):
            continue
        pages = t.get("content_pages") or 0
        out = t.get("output_tokens")
        if not pages or out is None:
            continue
        # Input tokens are most of the bill on a long context and were recorded
        # and read by nothing. Reported beside output rather than folded into
        # it: the two move for different reasons, and a single total hides
        # which one a change moved.
        inp = t.get("input_tokens")
        phases = t.get("phase_seconds") or {}
        # discussion and outline are not charged: the thinking a user was asked
        # to do is not the pipeline's cost, and counting it would push everyone
        # back toward the template path.
        charged = sum(v for k, v in phases.items() if k in ("build", "checks"))
        rows.append({"trace_id": t["trace_id"], "model": t.get("model"),
                     "effort": t.get("effort"), "content_pages": pages,
                     "tokens_per_page": round(out / pages, 1),
                     "input_tokens": inp,
                     "opened_at": t.get("opened_at"),
                     "charged_seconds": charged})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", action="store_true",
                    help="cost per content page, quality-gated")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    traces = load()
    if a.json:
        print(json.dumps({"traces": len(traces), "failing": ledger_failing(traces),
                          "instruments": ledger_instruments(traces),
                          "recipes": ledger_recipes(traces),
                          "beats": ledger_beats(traces),
                          "candidates": candidates(traces),
                          "board": board(traces)}, indent=1, ensure_ascii=False))
        return

    if not traces:
        print("no traces yet. `scripts/ops/trace.py open` starts one when a "
              "storyline is agreed; this ledger has nothing to read until real "
              "builds have run.\n\nThat is a true state, not a clean bill of "
              "health — an empty ledger and a healthy one look identical from "
              "here, which is why the queue rules exist.")
        return

    if a.board:
        rows = board(traces)
        print(f"efficiency board — {len(rows)} of {len(traces)} run(s) qualify "
              f"(a run with a failing gate is not on the board: a thin deck is "
              f"cheap and worthless)\n")
        for r in sorted(rows, key=lambda r: r["tokens_per_page"]):
            print(f"  {r['tokens_per_page']:>9.1f} tokens/page  "
                  f"{r['charged_seconds']:>5}s charged  "
                  f"{r['content_pages']:>3} pages  "
                  f"{r.get('model') or '?'}/{r.get('effort') or '?'}  "
                  f"in={r.get('input_tokens') if r.get('input_tokens') is not None else '?'}"
                  f"  opened {(r.get('opened_at') or '?')[:10]}")
        if rows:
            med = statistics.median(r["tokens_per_page"] for r in rows)
            print(f"\n  median {med:.1f} tokens per content page. Discussion and "
                  f"outline are not charged.")
        return

    print(f"{len(traces)} trace(s)\n")
    print("LEDGER 1 · which metric keeps failing")
    rows = ledger_failing(traces)
    for mid, ids in rows[:10]:
        print(f"  {len(ids):>3}x  {mid}")
    print("  (none)" if not rows else "")

    print("LEDGER 2 · which instrument is suspect  — checked BEFORE thresholds")
    for mid, why, count in ledger_instruments(traces):
        print(f"       {mid}: {why} ({count})")
    print("  (none)" if not ledger_instruments(traces) else "")

    print("LEDGER 2b · was the recipe written against these rules?")
    recipes = ledger_recipes(traces)
    order = ("stale", "unknown", "current", "none")
    tally = {s: [r for r in recipes if r["state"] == s] for s in order}
    for state in order:
        rows_s = tally[state]
        if not rows_s:
            continue
        if state == "stale":
            print(f"       {len(rows_s)} build(s) STALE — the recipe names an "
                  f"older version than the rules that graded it")
            for r in rows_s[:5]:
                print(f"         {r['trace_id']}  path {r['entry_path']}  "
                      f"recipe {r['recipe_version']} vs rules {r['skill_version']}")
        elif state == "unknown":
            print(f"       {len(rows_s)} build(s) UNKNOWN — the recipe carries "
                  f"no version stamp, so it never said which rules it followed. "
                  f"That is not the same as current.")
        elif state == "current":
            print(f"       {len(rows_s)} build(s) current")
        else:
            print(f"       {len(rows_s)} build(s) had no recipe (path A looks "
                  f"like this)")

    beats = ledger_beats(traces)
    print("LEDGER 2c · did the storyline review happen, and did it hold?")
    print(f"       {beats['reviewed']} of {beats['total']} build(s) record a "
          f"reviewed outline — beat 4 is the only defence completeness has, so "
          f"the rest had none")
    print(f"       {beats['drifted']} build(s) changed titles after approval "
          f"({beats['titles_moved']} title(s) in total) — a review agreed and "
          f"then departed from is not a review")
    print(f"       {beats['review_linked']} build(s) carry a reader review "
          f"reference; entry paths: "
          f"{', '.join(f'{k}={v}' for k, v in sorted(beats['by_entry_path'].items()))}")

    refusals, yields, abandoned = ledger_signals(traces)
    print("LEDGER 3 · what the constitution recorded")
    print(f"       {len(refusals)} refusal(s) to emit — each names a pair of "
          f"clauses that needs specifying")
    if yields:
        for clause, n in yields.most_common():
            print(f"       {clause} yielded {n}x")
        print("       (a severity-led rule starves high-frequency low-severity "
              "harms; this count is how that prediction gets tested)")
    print(f"       {len(abandoned)} abandoned build(s) — an unclosed trace is "
          f"the record of one")

    drafts = candidates(traces)
    print(f"\nCANDIDATE QUEUE — {sum(d['state'] == 'queued' for d in drafts)} "
          f"queued, {sum(d['state'] == 'deferred' for d in drafts)} deferred "
          f"(nothing is dropped)")
    for d in drafts:
        mark = "→" if d["state"] == "queued" else "·"
        print(f"  {mark} [{d['kind']}] {d['claim']}")
    print("\nNothing here ships. Every candidate is a draft with its evidence "
          "attached, and\nthe trigger is a person: the whole input to this loop "
          "comes from the agent being\nmeasured, and an automated path from "
          "\"the numbers moved\" to \"the rules changed\"\nwould let a bad "
          "instrument rewrite the rules it is failing.")


if __name__ == "__main__":
    main()
    sys.exit(0)
