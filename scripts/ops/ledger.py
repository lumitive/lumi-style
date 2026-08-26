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
  ledger.py --board             # per-run cost, then the model × effort matrix
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
# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

# The effort vocabulary and the price store went with the cost matrix — they
# were only ever read by it. `agent_runs` imports them from the same one place
# this file did, so nothing was retyped on the way out.
from trace_store import traces_dir  # noqa: E402 — the SAME store trace.py writes

TRACES = traces_dir(ROOT)
# THE COST MATRIX MOVED, and the import is the whole of what is left of it here.
# `board`, `matrix`, `cell_cost`, `load_prices` and `render_matrix` are an AGENT
# evaluation — what a configuration costs to produce a page that cleared the bar
# — and this file answers three questions about DOCUMENTS. They lived here only
# because the traces they read were already open here. `scripts/lib/agent_runs.py`
# is their home now, and it is what `--board` below renders through — the flag
# stays for the moment, and the tool that owns it is the next thing built.
from agent_runs import board, load_prices, render_matrix  # noqa: E402

TRIGGER_N = 3          # pieces of the same evidence before a candidate is drafted
QUEUE_CAPACITY = 5     # per cycle; the rest are deferred, never dropped


# The day the suite stopped writing into the tracked store. Nothing pytest
# wrote can be dated after it, so the population `suite_artifact` describes is
# CLOSED and finite — which is what makes a shape heuristic tolerable at all.
SUITE_LEAK_STOPPED = "2026-08-26"


def suite_artifact(t) -> bool:
    """A trace the test suite wrote, not a build anybody made.

    Until the suite got its own store, `tests/test_fewer_round_trips.py` drove
    `build.py` with no environment, so every run of pytest opened a trace of a
    throwaway two-page scaffold in the TRACKED store. `preflight.py` runs the
    suite and `release.py` stages with `git add -A`, so they were committed.

    **WHAT THIS CANNOT DISTINGUISH, said plainly because the first version of
    this docstring claimed the opposite.** It said four conditions together
    protect a real build. They do not: `trace.py cmd_open` sets `pages=0`,
    `closed_at=None` and `recipe_hash=None` on EVERY trace it opens, and
    `entry_path == "B"` is what most real builds use — so three of the four are
    just the initial state of any trace, and a real path-B build abandoned
    before `annotate --recipe` ran matches exactly. What actually separates the
    two populations is the date, and it only works because the leak has a stop:
    after `SUITE_LEAK_STOPPED` the suite writes elsewhere, so nothing written
    from that day on can be one of these however it is shaped.

    Measured when this was written: 182 of 199 build records matched, across
    sixteen distinct `skill_version`s (not sixteen releases — the span is
    0.1.532 and then most of 0.1.586-0.1.605).

    They are NOT deleted — a trace store is a record, and the honest fix for a
    bad denominator is to name what is in it, not to delete until the number
    reads better. `--with-suite-artifacts` puts them back everywhere, including
    in `--json` and `--board`.
    """
    if not isinstance(t, dict):
        return False
    return (t.get("source") == "build"
            and t.get("entry_path") == "B"
            and not (t.get("pages") or 0)
            and not t.get("recipe_hash")
            and not t.get("closed_at")
            and (t.get("opened_at") or "") < SUITE_LEAK_STOPPED)


def load(include_suite_artifacts: bool = False):
    if not TRACES.exists():
        return []
    out = []
    for path in sorted(TRACES.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    if include_suite_artifacts:
        return out
    return [t for t in out if not suite_artifact(t)]


def set_aside_count() -> int:
    """-> how many records the filter is holding back, for the disclosure."""
    return sum(1 for t in load(True) if suite_artifact(t))


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
    # BUILDS, NOT TRACES. The label has said `build(s)` since this was written
    # and the denominator was `len(traces)`, which includes every conformance
    # record — so `4 of 251 build(s)` counted 52 rows that are not builds at
    # all. Caught by a review checking the sentence against the division.
    #
    # `in (None, "build")` rather than `== "build"`: `source` is required by
    # the schema and every one of the 251 tracked records carries it, so the
    # None arm covers hand-written fixtures alone. Excluding them instead
    # would have been this function's tests deciding its semantics, which is
    # backwards — and the defect being fixed is 52 conformance rows, not an
    # absent field.
    traces = [t for t in traces if t.get("source") in (None, "build")]
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



def ledger_shape(traces):
    """-> {key: sorted readings} over every build that recorded a shape.

    **A distribution, never a bar.** The point is that the corpus keeps its own
    numbers so a proposed threshold can be checked against them instead of
    invented from whichever documents somebody happened to reopen — which is
    how 0.1.592's layout bar came to be drafted from five documents and refuted
    by a sixth. Nothing here decides anything; `bar_replay.py` is what asks a
    number whether it separates, and a person reads the answer.
    """
    out: dict[str, list] = {}
    for t in traces:
        for key, value in (t.get("shape") or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out.setdefault(key, []).append(value)
    return {k: sorted(v) for k, v in sorted(out.items())}


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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", action="store_true",
                    help="cost per content page, quality-gated")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--with-suite-artifacts", action="store_true",
                    help="include the traces pytest wrote into the store "
                         "before it had one of its own (see suite_artifact)")
    a = ap.parse_args()

    traces = load(a.with_suite_artifacts)
    set_aside = 0 if a.with_suite_artifacts else set_aside_count()
    # SAID OUT LOUD ON EVERY EXIT, NOT JUST THE ONE A HUMAN READS. Each of the
    # four paths below carries a denominator, and the first version disclosed
    # the filter on one of them — so `--json` handed a machine `"traces": 69`
    # with nothing to learn 182 from, `--board` printed `28 of 69 run(s)`, and
    # a store holding only set-aside records announced "no traces yet" over
    # hundreds of files. Filtering silently is the defect this filter exists to
    # repair; doing it on three exits out of four is the same defect, quieter.
    aside = (f"       {set_aside} suite artifact(s) set aside and still on "
             f"disk — traces pytest opened before it had a store of its own; "
             f"--with-suite-artifacts counts them") if set_aside else ""
    if a.json:
        print(json.dumps({"traces": len(traces),
                          "suite_artifacts_set_aside": set_aside,
                          "failing": ledger_failing(traces),
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
        if aside:
            print(aside)
        return

    if a.board:
        rows = board(traces)
        print(f"efficiency board — {len(rows)} of {len(traces)} run(s) qualify "
              f"(a run with a failing gate is not on the board: a thin deck is "
              f"cheap and worthless)")
        if aside:
            print(aside)
        print()
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
        for line in render_matrix(traces, load_prices()):
            print(line)
        return

    print(f"{len(traces)} trace(s)")
    # Every denominator below is a claim about how this package is used, and
    # across sixteen `skill_version`s most of it was pytest: `4 of 251` records
    # of a reviewed outline described a store of seventeen real builds.
    if aside:
        print(aside)
    print()
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
            # SPLIT BY ENTRY PATH. This line read "path A looks like this" and
            # every one of the 64 rows it described was path B — false for 100%
            # of its population, while `ledger_recipes` already carried
            # `entry_path` on every row and simply was not read here. Path B
            # with no recipe is the state `--recipe` exists to make impossible,
            # so it is the half worth shouting about.
            no_recipe_b = [r for r in rows_s if r.get("entry_path") == "B"]
            no_recipe_a = [r for r in rows_s if r.get("entry_path") == "A"]
            if no_recipe_a:
                print(f"       {len(no_recipe_a)} build(s) had no recipe on "
                      f"path A — a document composed from a conversation "
                      f"looks like this")
            if no_recipe_b:
                print(f"       {len(no_recipe_b)} build(s) are path B WITH NO "
                      f"RECIPE — path B means 'started from a recipe', so each "
                      f"of these names no driver and cannot say which rules it "
                      f"followed")

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
    shape = ledger_shape(traces)
    print("LEDGER 2d · what the documents LOOKED like")
    if not shape:
        print("       no build has recorded a shape yet — `check_deliverable` "
              "writes one at close from the checkers it already ran")
    for key, values in shape.items():
        mid = statistics.median(values)
        print(f"       {key:24} n={len(values):<4} "
              f"min {values[0]:g}  median {mid:g}  max {values[-1]:g}")
    if shape:
        print("       A distribution, not a bar. `bar_replay.py <metric> <n>` "
              "asks whether a proposed number separates the documents an owner "
              "has actually judged.")

    print("LEDGER 3 · what the constitution recorded")
    print(f"       {len(refusals)} refusal(s) to emit — each names a pair of "
          f"clauses that needs specifying")
    if yields:
        for clause, n in yields.most_common():
            print(f"       {clause} yielded {n}x")
        print("       (a severity-led rule starves high-frequency low-severity "
              "harms; this count is how that prediction gets tested)")
    # THE FILTER'S OVERLAP WITH THIS LINE IS TOTAL, so this is the one number
    # that must name both populations. Every record `suite_artifact` sets aside
    # is unclosed, so filtering them takes them out of `abandoned` and nowhere
    # else — a review measured the result: 21 reported where the store holds
    # 204. Fixing one denominator by breaking the signal the ledger exists to
    # raise is not a fix.
    print(f"       {len(abandoned)} abandoned build(s) — an unclosed trace is "
          f"the record of one")
    if set_aside:
        print(f"       and {set_aside} more unclosed records set aside as "
              f"suite artifacts, which every one of them is: the filter and "
              f"this count select the same field, so it is stated rather than "
              f"subtracted")

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
