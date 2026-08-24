#!/usr/bin/env python3
"""Does a proposed bar separate the documents an owner has actually judged?

**This exists because the alternative was doing it by hand, and by hand it was
done wrong.** 0.1.592 drafted a ceiling on layout top share from five documents
found one at a time: three the owner had not faulted at 28.6 / 30.0 / 33.3, two
she had at 64.3 / 70.0, an empty band between them, and a bar of 50 written into
`evals/thresholds.json`. Then A1 — this package's own accepted anchor — was
measured at 78.6, WORSE than both faulted documents, and the bar was withdrawn.
Nothing was wrong with the reasoning. What was wrong is that the corpus was
whatever somebody had remembered to reopen.

So: the judgements AND their readings live in `evals/thresholds.json`'s `corpus`
block — ids and numbers only, never a path, because a tracked file naming a
deliverable is red line 9. `evals/corpus.local.json` is what an operator uses to
resolve an id back to a file when a reading needs re-measuring; this tool never
opens it. It asks one question and prints the answer.

    bar_replay.py layout_top_share 50 --direction ceiling

**It does not set anything.** It reports which judged documents a bar would
have failed, and a person decides. A tool that could write the threshold it
just validated would be the invented-number machine with an extra step.

Standard library only.
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
import json  # noqa: E402
import pathlib  # noqa: E402
import sys  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
THRESHOLDS = ROOT / "evals" / "thresholds.json"

# A verdict is what the OWNER said about a document, in her own record. The two
# that matter are opposite; "not faulted" is deliberately not "accepted",
# because not being criticised is weaker evidence than being accepted and the
# difference is exactly what a bar is being asked to respect.
GOOD = ("accepted", "not faulted")
BAD = ("rejected", "faulted")


def judged() -> list[dict]:
    """-> [{id, verdict, readings}] for every document carrying an owner verdict."""
    table = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    corpus = table.get("corpus") or {}
    rows = []
    for bucket, verdict in (("accepted", "accepted"), ("rejected", "rejected")):
        for entry in corpus.get(bucket) or []:
            rows.append({"id": entry.get("id"), "verdict": verdict,
                         "readings": entry.get("readings") or {},
                         "note": entry.get("note", "")})
    for entry in corpus.get("judged") or []:
        rows.append({"id": entry.get("id"), "verdict": entry.get("verdict"),
                     "readings": entry.get("readings") or {},
                     "note": entry.get("note", "")})
    # A VERDICT OUTSIDE THE VOCABULARY IS NOT A NEUTRAL ROW. Silently ignored,
    # it printed with the `!!` mark, counted as no disagreement, and exited 0 —
    # a document the record has an opinion about, quietly excluded from the
    # question being asked of the record.
    unknown = [r["id"] for r in rows if r["verdict"] not in GOOD + BAD]
    if unknown:
        sys.exit(f"corpus verdict(s) outside {GOOD + BAD}: {', '.join(unknown)}")
    return rows


def replay(metric: str, bar: float, direction: str) -> dict:
    rows = [r for r in judged() if metric in r["readings"]]
    passes: list[tuple] = []
    fails: list[tuple] = []
    unread: list[str] = []
    for r in rows:
        value = r["readings"][metric]
        ok = value <= bar if direction == "ceiling" else value >= bar
        (passes if ok else fails).append((r["id"], value, r["verdict"]))
    for r in judged():
        if metric not in r["readings"]:
            unread.append(r["id"])
    # TWO DIRECTIONS, AND THEY ARE NOT EQUALLY STRONG.
    #
    # A bar that FAILS a document the owner accepted is wrong, full stop — she
    # accepted it, so whatever the bar measures, it is not the thing that made
    # the document acceptable.
    #
    # A bar that PASSES a document she rejected is weaker evidence, because a
    # document is rejected for a REASON and the reason may be another metric
    # entirely: R1 was rejected for its figures, so a layout bar has no
    # obligation to fail it. Treating both as "disagreement" makes every metric
    # unpassable as rejected documents accumulate, and pushes an author toward
    # a number chosen to fail R1 for the wrong reason — the invented-number
    # machine wearing this tool's badge.
    contradicts = [f"{i} ({v}) is {d} and the bar FAILS it" for i, v, d in fails
                   if d in GOOD]
    permissive = [f"{i} ({v}) is {d} and the bar PASSES it" for i, v, d in passes
                  if d in BAD]
    good_rows = [r for r in rows if r["verdict"] in GOOD]
    bad_rows = [r for r in rows if r["verdict"] in BAD]
    # "Separates" needs something to separate. One accepted document and a
    # generous bar produced `separates: True` and exit 0, which reads as a bar
    # that survived a test nobody ran.
    separates = bool(good_rows and bad_rows and not contradicts and not permissive)
    return {"metric": metric, "bar": bar, "direction": direction,
            "passes": passes, "fails": fails, "unread": unread,
            "contradictions": contradicts, "permissive": permissive,
            "disagreements": contradicts + permissive,
            "judged_good": len(good_rows), "judged_bad": len(bad_rows),
            "separates": separates}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("metric")
    ap.add_argument("bar", type=float)
    ap.add_argument("--direction", choices=("ceiling", "floor"),
                    default="ceiling",
                    help="ceiling: a document must be AT OR BELOW the bar")
    a = ap.parse_args(argv)
    r = replay(a.metric, a.bar, a.direction)

    if not r["passes"] and not r["fails"]:
        print(f"no judged document carries a reading for {a.metric!r}.")
        print(f"  {len(r['unread'])} document(s) carry an owner verdict and no "
              f"such reading: {', '.join(x for x in r['unread'] if x) or '—'}")
        print("  A bar cannot be checked against a corpus that has not been "
              "measured. `ledger.py` shows what builds have recorded.")
        return 1

    print(f"{a.metric} {'<=' if a.direction == 'ceiling' else '>='} {a.bar:g}"
          f"  — replayed against {len(r['passes']) + len(r['fails'])} judged "
          f"document(s)")
    for label, rows in (("passes", r["passes"]), ("fails", r["fails"])):
        for doc, value, verdict in sorted(rows, key=lambda x: x[1]):
            mark = "  " if (verdict in GOOD) == (label == "passes") else "!!"
            print(f"  {mark} {doc:6} {value:>7g}  owner: {verdict:12} "
                  f"bar: {label[:-2] if label == 'passes' else 'fail'}")
    if r["unread"]:
        print(f"  -- {len(r['unread'])} judged document(s) carry no reading for "
              f"this metric: {', '.join(x for x in r['unread'] if x)}")
    print()
    if r["contradictions"]:
        print(f"THE BAR CONTRADICTS THE RECORD on "
              f"{len(r['contradictions'])} document(s):")
        for line in r["contradictions"]:
            print(f"  {line}")
        print("\n  A bar that fails a document the owner ACCEPTED is not a "
              "measurement of quality.\n  This is the answer 0.1.592 got by "
              "hand, one document too late.")
    if r["permissive"]:
        print(f"\nThe bar is PERMISSIVE on {len(r['permissive'])} rejected "
              f"document(s):")
        for line in r["permissive"]:
            print(f"  {line}")
        print("\n  Weaker evidence than a contradiction: a document is "
              "rejected for a reason,\n  and the reason may be a different "
              "metric. Read the corpus note before\n  moving the bar to catch "
              "it.")
    if r["contradictions"] or r["permissive"]:
        return 1
    if not r["separates"]:
        print(f"The bar contradicts nothing — and it separates nothing either: "
              f"{r['judged_good']} accepted and {r['judged_bad']} rejected "
              f"document(s) carry this reading.")
        print("  A bar needs one of each before agreement means anything.")
        return 1
    print("The bar agrees with every judged document it could read.")
    print("  That is necessary and not sufficient: it says the bar contradicts "
          "nothing\n  on record, not that it measures what the record measures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
