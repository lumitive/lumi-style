#!/usr/bin/env python3
"""Do the Evals thresholds agree with the person whose judgement they stand in for?

This is the study `evals/thresholds.json` names as the thing that would let its
bars gate. Until it has been run, those bars are reasoned numbers that separate
two documents, and a red-team pass has already cleared all four of them with
rewrites that added no content — so "it separates the corpus" is not evidence
that it measures quality.

**The output is a disagreement list, not a coefficient.** With ten documents a
correlation is a number with no power behind it, and the useful question is not
"how correlated" but "which documents does the machine read differently from the
reader, and what is on those pages". A metric that agrees on eight and is wrong
about two has told you exactly where to look; its rho has told you nothing.

**The reader scores blind.** `--sheet` prints a scoring form carrying no
mechanical number, because a reader who has seen the machine's answer is no
longer an independent measurement. The form itself comes from
`scripts/ops/scoring_sheet.py`'s source (`scripts/lib/rubric_items.py`, which
reads the dimension set out of the rubric) — a second dimension list lived here
once and outlived the rubric, offering C1-C7 after C8 shipped, so a reader who
filled it produced a record `review_scores.py` rejects. Scores go into
`reviews/scores.json` through the schema that already exists, and this reads
them back.

**The join key is a corpus id, never a filename.** The measurement cache is
keyed by filename; a reader record carries `corpus_id` (the id shape
`review_scores.py` validates), because a filename in that tracked file would be
an engagement fact. The gitignored `evals/corpus.local.json` maps the ids to
paths, and this script resolves filenames to ids through it — when that map is
absent the study says it could not join, rather than printing an empty success.

    python3 scripts/ops/eval_agreement.py --sheet            # blind form, for a person
    python3 scripts/ops/eval_agreement.py --measure          # the machine half, cached
    python3 scripts/ops/eval_agreement.py                    # the study, once both exist

Each metric declares which human dimension it claims to predict. That claim is
itself under test: a metric that predicts nothing is not thereby excused, it is
disconfirmed.
"""
from __future__ import annotations

import argparse
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import subprocess
import sys
import sys as _bs_sys  # noqa: E402
from collections import Counter

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import corpus  # noqa: E402
import jsonio  # noqa: E402

# --- end bootstrap ---
import scoring_sheet  # noqa: E402
from review_scores import DOCUMENT_ID  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
CACHE = ROOT / "evals" / "measured.local.json"
SCORES = ROOT / "reviews" / "scores.json"
LOCAL_CORPUS = corpus.LOCAL_CORPUS  # the one reader is scripts/lib/corpus.py

# WHICH HUMAN DIMENSION EACH METRIC CLAIMS TO PREDICT. Stated up front so the
# study can disconfirm it. H2 is structural expression ("each page's layout best
# expresses its topic"); H3 is chart self-explanation ("every figure's message is
# clear without the body text"). A metric about drawing that turns out to track
# H5 business readability instead is not a success with a footnote — it is a
# metric measuring something other than what it was introduced for.
# A machine reading -> the human dimension it is a proxy for. These are
# HYPOTHESES, not findings: the study exists to test them, and a mapping that
# never disagrees with its dimension is either right or measuring the same
# thing twice. They moved from H to C at 0.1.468 and the mapping was re-derived
# rather than transliterated — C2 is the storyline read through the titles,
# C3 is the argument on one page, C4 is sourcing.
PREDICTS = {
    "prose_only_share": "C3",
    "figures_per_content_page": "C3",
    "list_items_per_content_page": "C2",
    "visual_share_median": "C3",
    "M1_assertive_titles": "C2",
    "M2_number_sourcing": "C4",
}

# A reader's 1-5 against a threshold's pass/miss. 3 is the anchor's midpoint —
# "most pages carry value, some merely state" — so 3 and above is the half of
# the scale a document is not failing on.
ACCEPTABLE_FROM = 3


def measure_all(paths: list[pathlib.Path]) -> dict:
    """Run eval_corpus over the corpus and cache it. Rendering is the slow half."""
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/eval_corpus.py"), "--json",
         *[str(p) for p in paths]], capture_output=True, text=True)
    try:
        reports = json.loads(out.stdout)
    except ValueError:
        print(f"FAIL  eval_corpus emitted no parseable report "
              f"(exit {out.returncode}): {out.stdout[-300:]}")
        return {}
    return {pathlib.Path(r["file"]).name: r for r in reports}


def corpus_ids_by_name() -> dict[str, str] | None:
    """-> {filename: corpus id} from evals/corpus.local.json, or None if absent.

    The map is gitignored on purpose — a path to a real deliverable is an
    engagement fact — so its absence is a normal state on any machine but the
    operator's, and the caller must SAY the join was impossible rather than
    let it read as an empty result.
    """
    if corpus.load() is None:
        return None
    # An archived entry (scored, then deleted) names no file to join on and
    # is simply not in this map; corpus.paths() reads both shapes.
    return {p.name: k for k, p in corpus.paths().items()}


def read_scores() -> dict:
    """-> {corpus id: {C1..C8}} from the reader side of reviews/scores.json.

    Keyed by `corpus_id` — the field review_scores.py requires on a schema-3
    record for exactly this join — with `document` accepted as a fallback when
    it carries the same id shape. A record with neither (the legacy schema-1
    history) names no document and cannot enter the study.

    The SELF side is deliberately ignored. An agent scoring its own output is
    not a measurement of quality, and debug mode's self-scores are written to an
    uncommitted log for that reason.
    """
    try:
        store = json.loads(SCORES.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:                            # noqa: BLE001
        print(f"note  {SCORES.name} could not be read: {exc}")
        return {}
    out = {}
    for record in store.get("reviews", []):
        key = record.get("corpus_id") or record.get("document")
        if key and DOCUMENT_ID.fullmatch(str(key)) and record.get("reader"):
            out[str(key)] = record["reader"]
    return out


def study(measured: dict, scored: dict, ids_by_name: dict) -> dict:
    """-> {"rows": ..., "unjoinable": ..., "left_out": ...}.

    `rows` is one per (metric, document) where a bar and a reader both spoke.
    The join runs filename -> corpus id (through `ids_by_name`, from the local
    corpus map) -> reader record; comparing the filename to the id directly is
    the disjoint-by-schema join this function shipped with, under which no
    input the schema permits could ever produce a row.

    `unjoinable` names the measured filenames the map gives no id, and
    `left_out` counts the verdicts with no pass/miss to compare ("no bar",
    "too few pages", "not measured") per metric. Both are reported rather than
    dropped, because a study that silently thins its own input reads exactly
    like a clean one.
    """
    table = json.loads((ROOT / "evals" / "thresholds.json").read_text(encoding="utf-8"))
    rows = []
    unjoinable = []
    left_out: dict[str, Counter] = {}
    for name, report in sorted(measured.items()):
        cid = ids_by_name.get(name)
        if cid is None:
            unjoinable.append(name)
            continue
        reader = scored.get(cid)
        if not reader:
            continue
        for entry in report.get("scores", []):
            metric = entry["metric"]
            dim = PREDICTS.get(metric)
            if dim is None:
                continue                      # claims no dimension: not under test
            if entry["verdict"] not in ("ok", "MISS"):
                left_out.setdefault(metric, Counter())[entry["verdict"]] += 1
                continue
            human = reader.get(dim)
            if human is None:
                continue
            spec = table["metrics"][metric]
            rows.append({
                "document": name, "corpus_id": cid, "metric": metric,
                "dimension": dim,
                "machine": entry["verdict"], "value": entry["value"],
                "bar": entry["bar"], "direction": spec["direction"],
                "human": human,
                "agree": (entry["verdict"] == "ok") == (human >= ACCEPTABLE_FROM),
            })
    return {"rows": rows, "unjoinable": unjoinable, "left_out": left_out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sheet", action="store_true",
                    help="print a blind scoring form — no mechanical numbers")
    ap.add_argument("--measure", action="store_true",
                    help="run the machine half and cache it")
    ap.add_argument("--report", action="store_true",
                    help="print the standing state and exit 0. This is the mode "
                         "CI runs: the measurement cache and the corpus map are "
                         "gitignored operator files, so on a runner the honest "
                         "output is what is missing, never a failure. Without "
                         "--report, no joinable row is an error, because a "
                         "study nobody can run should be loud when someone "
                         "runs it.")
    ap.add_argument("files", nargs="*", type=pathlib.Path)
    args = ap.parse_args(argv)

    paths = list(args.files)
    if not paths and corpus.load() is not None:
        paths = list(corpus.paths().values())

    if args.measure:
        if not paths:
            ap.error("name the documents, or record them in evals/corpus.local.json")
        found = [p for p in paths if p.exists()]
        for p in paths:
            if not p.exists():
                print(f"note  named but not found, so not measured: {p}")
        if not found:
            print(f"FAIL  none of the {len(paths)} named document(s) exist on "
                  f"this machine. Nothing was measured, and a check nobody ran "
                  f"must not read like a check that found nothing; the cache "
                  f"was left as it was.")
            return 1
        measured = measure_all(found)
        if not measured:
            print("FAIL  eval_corpus returned no report, so there is nothing "
                  "to cache; the cache was left as it was.")
            return 1
        jsonio.dump_json(CACHE, measured)
        print(f"measured {len(measured)} of {len(paths)} named document(s) -> "
              f"{CACHE.relative_to(ROOT)} (gitignored)")
        return 0

    if args.sheet:
        # No dimension list lives here. The sheet is rendered by
        # scoring_sheet.py from scripts/lib/rubric_items.py, which reads the
        # dimension set out of the rubric — the hardcoded list this branch
        # used to carry stopped at C7 after C8 shipped, and a reader who
        # filled it produced a record review_scores.py rejects.
        if not paths:
            print("FAIL  --sheet needs the documents: name them as arguments, "
                  "or record them in evals/corpus.local.json. The form itself "
                  "is scripts/ops/scoring_sheet.py's, generated from the "
                  "rubric.")
            return 1
        known_ids = corpus_ids_by_name() or {}
        ids = [known_ids.get(p.name, f"A{i}")
               for i, p in enumerate(paths, start=1)]
        print(scoring_sheet.sheet([str(p) for p in paths], ids))
        return 0

    if not CACHE.exists():
        if args.report:
            print("note  agreement study: no cached measurement on this machine. "
                  "The study is a local operator step; `--measure` builds the "
                  "cache, and the gitignored evals/corpus.local.json supplies "
                  "the filename-to-corpus-id join.")
            return 0
        print("FAIL  no cached measurement. Run with --measure first.")
        return 1
    measured = json.loads(CACHE.read_text(encoding="utf-8"))
    scored = read_scores()
    if not scored:
        print(f"note  no reader record carries a corpus id, so nothing can be "
              f"compared. {len(measured)} document(s) are measured and waiting; "
              f"`--sheet` prints the form.")
        return 0 if args.report else 1

    ids_by_name = corpus_ids_by_name()
    if ids_by_name is None:
        # Not an empty result: the join itself was impossible, and saying so
        # is the difference between "the study found nothing" and "nobody
        # could run the study".
        print(f"{'note' if args.report else 'FAIL'}  the study could not join: "
              f"evals/corpus.local.json is absent on this machine, so no "
              f"measured filename resolves to a corpus id. No comparison was "
              f"made.")
        return 0 if args.report else 1

    result = study(measured, scored, ids_by_name)
    rows = result["rows"]
    for name in result["unjoinable"]:
        print(f"note  measured, but {LOCAL_CORPUS.name} gives it no corpus id, "
              f"so it cannot join a reader score: {name}")
    if not rows:
        print("note  measured documents and scored documents do not overlap; "
              "no (metric, document) pair had both a bar and a reader")
        return 0 if args.report else 1

    print(f"# Agreement: {len(rows)} (metric, document) pair(s) where a bar and "
          f"a reader both spoke\n")
    for metric in sorted({r["metric"] for r in rows}):
        mine = [r for r in rows if r["metric"] == metric]
        agree = sum(1 for r in mine if r["agree"])
        print(f"## {metric}  — claims to predict {PREDICTS[metric]}")
        print(f"   agrees on {agree} of {len(mine)}")
        for r in mine:
            if r["agree"]:
                continue
            said = "cleared the bar" if r["machine"] == "ok" else "missed the bar"
            print(f"   DISAGREES  {r['corpus_id']} ({r['document']}): machine {said} "
                  f"({r['value']} {'<=' if r['direction'] == 'ceiling' else '>='} "
                  f"{r['bar']}), reader scored {r['dimension']}={r['human']}")
        print()

    for metric in sorted(result["left_out"]):
        drops = result["left_out"][metric]
        detail = ", ".join(f"{n} x {v!r}" for v, n in sorted(drops.items()))
        print(f"note  {metric}: left out of the study with no pass/miss to "
              f"compare — {detail}. Reported so a thin study cannot read like "
              f"a clean one; this does not gate.")

    total = sum(1 for r in rows if r["agree"])
    print(f"{total} of {len(rows)} agree. **This is a disagreement list, not a "
          f"verdict.** Read the pages named above: each is either a metric "
          f"measuring the wrong thing or a document the reader judged on "
          f"something no metric sees, and only the pages say which.")
    if len(rows) < 20:
        print(f"      {len(rows)} pairs is a small study. It can disconfirm a "
              f"metric; it cannot confirm one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
