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
longer an independent measurement. Scores go into `reviews/scores.json` through
the schema that already exists, and this reads them back.

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

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
CACHE = ROOT / "evals" / "measured.local.json"
SCORES = ROOT / "reviews" / "scores.json"
LOCAL_CORPUS = ROOT / "evals" / "corpus.local.json"

# WHICH HUMAN DIMENSION EACH METRIC CLAIMS TO PREDICT. Stated up front so the
# study can disconfirm it. H2 is structural expression ("each page's layout best
# expresses its topic"); H3 is chart self-explanation ("every figure's message is
# clear without the body text"). A metric about drawing that turns out to track
# H5 business readability instead is not a success with a footnote — it is a
# metric measuring something other than what it was introduced for.
PREDICTS = {
    "prose_only_share": "H3",
    "figures_per_content_page": "H3",
    "list_items_per_content_page": "H2",
    "visual_share_median": "H2",
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


def read_scores() -> dict:
    """-> {document key: {H1..H6}} from the reader side of reviews/scores.json.

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
        key = record.get("document")
        if key and record.get("reader"):
            out[key] = record["reader"]
    return out


def study(measured: dict, scored: dict) -> list[dict]:
    """One row per (metric, document) where a bar and a reader both spoke."""
    table = json.loads((ROOT / "evals" / "thresholds.json").read_text(encoding="utf-8"))
    rows = []
    for name, report in sorted(measured.items()):
        reader = scored.get(name)
        if not reader:
            continue
        for entry in report.get("scores", []):
            metric = entry["metric"]
            dim = PREDICTS.get(metric)
            human = reader.get(dim) if dim else None
            if entry["verdict"] not in ("ok", "MISS") or human is None:
                continue
            spec = table["metrics"][metric]
            rows.append({
                "document": name, "metric": metric, "dimension": dim,
                "machine": entry["verdict"], "value": entry["value"],
                "bar": entry["bar"], "direction": spec["direction"],
                "human": human,
                "agree": (entry["verdict"] == "ok") == (human >= ACCEPTABLE_FROM),
            })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sheet", action="store_true",
                    help="print a blind scoring form — no mechanical numbers")
    ap.add_argument("--measure", action="store_true",
                    help="run the machine half and cache it")
    ap.add_argument("files", nargs="*", type=pathlib.Path)
    args = ap.parse_args(argv)

    paths = list(args.files)
    if not paths and LOCAL_CORPUS.exists():
        local = json.loads(LOCAL_CORPUS.read_text(encoding="utf-8"))
        paths = [pathlib.Path(v).expanduser() for v in local.values()]

    if args.measure:
        if not paths:
            ap.error("name the documents, or record them in evals/corpus.local.json")
        measured = measure_all([p for p in paths if p.exists()])
        CACHE.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
        print(f"measured {len(measured)} document(s) -> "
              f"{CACHE.relative_to(ROOT)} (gitignored)")
        return 0

    if args.sheet:
        names = sorted(json.loads(CACHE.read_text(encoding="utf-8"))
                       ) if CACHE.exists() else [p.name for p in paths]
        print("# Blind scoring sheet\n")
        print("Score each document 1-5 on each dimension, against the anchors in")
        print("references/eval-rubric.md. **No mechanical number appears here on")
        print("purpose** — a reader who has seen the machine's answer is no longer")
        print("an independent measurement, and this study is worth nothing without")
        print("that independence.\n")
        print("Put the results in reviews/scores.json (reader side), one record per")
        print("document, and then run this script with no flags.\n")
        for name in names:
            print(f"## {name}\n")
            for dim, anchor in (("H1", "reader value"), ("H2", "structural expression"),
                                ("H3", "chart self-explanation"),
                                ("H4", "honest-boundary disclosure"),
                                ("H5", "business readability"),
                                ("H6", "narrative persuasion")):
                print(f"- {dim} {anchor:28} ___   because:")
            print()
        return 0

    if not CACHE.exists():
        print("FAIL  no cached measurement. Run with --measure first.")
        return 1
    measured = json.loads(CACHE.read_text(encoding="utf-8"))
    scored = read_scores()
    if not scored:
        print(f"note  no reader scores name a document, so nothing can be "
              f"compared. {len(measured)} document(s) are measured and waiting; "
              f"`--sheet` prints the form.")
        return 1

    rows = study(measured, scored)
    if not rows:
        print("note  measured documents and scored documents do not overlap")
        return 1

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
            print(f"   DISAGREES  {r['document']}: machine {said} "
                  f"({r['value']} {'<=' if r['direction'] == 'ceiling' else '>='} "
                  f"{r['bar']}), reader scored {r['dimension']}={r['human']}")
        print()

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
