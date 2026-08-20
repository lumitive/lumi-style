#!/usr/bin/env python3
"""Print the human dimensions (C1–C8) over time, and validate the store.

`references/eval-rubric.md` defines C1–C8 (H1–H6 until 0.1.463) and a
protocol where a divergence of two forces a retrospective. The machine half of this package reports the current
state of one artifact; the human half had no memory at all. Every score in the
record was a sentence inside a release note, so nobody could answer "is H3
improving" without re-reading the changelog.

    python3 scripts/ops/review_scores.py            # the series, per dimension
    python3 scripts/ops/review_scores.py --check    # validate only (runs in CI)

This is a schema and a printer, not a system. It stores no prose: see the
$comment in reviews/scores.json for why a notes column is the one field this
file may never have.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
STORE = ROOT / "reviews" / "scores.json"
CHANGELOG = ROOT / "CHANGELOG.md"

# The genres references/storyline-templates.md defines. Imported rather than
# retyped would be better, but check_prose's tuple is about CLI flags and this
# is about what kind of document was reviewed; they are allowed to differ, and
# a hand-copy of four words that check_repo.py does not verify is exactly the
# drift this repository keeps paying for — so the guard below checks it.
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
# --- end bootstrap ---
from deliverable_registry import GENRES  # noqa: E402

# Fields, and NOTHING else. An unknown key is an error rather than ignored
# data: the whole engagement-fact defence is that there is nowhere to put one.
RECORD_KEYS = {"release", "genre", "self", "reader", "outcome"}
# OPTIONAL, and it must be a corpus ID rather than a name or a path. The
# agreement study needs to know which document a score is about; a filename here
# would put an engagement fact in a tracked file, which is exactly what the
# closed key set above exists to prevent. So the field is admitted and the
# validator refuses anything that is not the id shape — the ids resolve through
# the gitignored evals/corpus.local.json.
OPTIONAL_KEYS = {"document", "corpus_id", "storyline"}
DOCUMENT_ID = re.compile(r"^[A-Z]\d{1,3}$")


def validate(store) -> list[str]:
    errors = []
    dims = store.get("dimensions")
    outcomes = set(store.get("outcomes") or [])
    if dims != ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]:
        return [f"reviews/scores.json declares dimensions {dims!r}; the rubric "
                f"defines C1-C8 and the store may not disagree with it"]
    releases = set(re.findall(r"^##\s+(\d+\.\d+\.\d+)", CHANGELOG.read_text(
        encoding="utf-8"), re.M))

    LEGACY_DIMS = ["H1", "H2", "H3", "H4", "H5", "H6"]
    for i, rec in enumerate(store.get("reviews", [])):
        where = f"reviews[{i}]"
        # A schema-1 record is history: it was scored against H1-H6 before
        # C1-C8 replaced them, and it is kept verbatim rather than back-filled.
        # Inventing a corpus id for a document nobody can re-measure would put a
        # fabricated join key into the evidence, which is worse than a gap.
        legacy = rec.get("schema") == 1
        expected = LEGACY_DIMS if legacy else dims
        extra = set(rec) - RECORD_KEYS - OPTIONAL_KEYS - ({"schema"} if legacy else set())
        if extra:
            errors.append(
                f"{where} carries {sorted(extra)!r}, which the schema does not "
                f"define. This file has no free-text field on purpose — a score "
                f"store is the shape that breaks red line 9, and a new key is "
                f"how a client name arrives")
        for missing in sorted(RECORD_KEYS - set(rec)):
            errors.append(f"{where} is missing {missing!r}")
        if not legacy and not rec.get("corpus_id"):
            errors.append(
                f"{where}: corpus_id is required. The agreement study joins a "
                f"machine reading to a human score on it, and the two records "
                f"that predate this rule have none — which is the whole reason "
                f"that study has never had a single joinable row")
        doc = rec.get("document")
        if doc is not None and not DOCUMENT_ID.fullmatch(str(doc)):
            errors.append(
                f"{where}.document is {doc!r}; it must be a corpus id like 'A1'. "
                f"A filename here is an engagement fact in a tracked file, which "
                f"is what the closed key set prevents")
        if rec.get("release") not in releases:
            errors.append(f"{where}: release {rec.get('release')!r} names no "
                          f"CHANGELOG heading")
        if rec.get("genre") not in GENRES:
            errors.append(f"{where}: genre {rec.get('genre')!r} is not one of "
                          f"{list(GENRES)}")
        if rec.get("outcome") not in outcomes:
            errors.append(f"{where}: outcome {rec.get('outcome')!r} is not one "
                          f"of {sorted(outcomes)} — the protocol's step 4 gives "
                          f"three, and a no-change is written down like the others")
        for side in ("self", "reader"):
            scores = rec.get(side)
            if not isinstance(scores, dict) or set(scores) != set(expected):
                errors.append(f"{where}.{side} must carry exactly "
                              f"{'H1-H6 (schema 1, history)' if legacy else 'C1-C8'}")
                continue
            for dim, val in scores.items():
                if val is None:
                    continue
                if not isinstance(val, int) or not 1 <= val <= 5:
                    errors.append(f"{where}.{side}.{dim} is {val!r}; anchors run "
                                  f"1-5, and 'not scored' is null rather than 0")
        # The protocol rule, in the tooling rather than only in the prose.
        # A number series invites optimising the number; for reader scores that
        # is the point, and for self-scores it is drift. This is the one rule
        # that stops a self-score running ahead of a reader.
        s, r = rec.get("self") or {}, rec.get("reader") or {}
        for dim in dims:
            if s.get(dim) == 5 and r.get(dim) is None:
                errors.append(
                    f"{where}: self-scored 5 on {dim} with no reader score. "
                    f"eval-rubric.md step 1: never self-score 5 before a reader "
                    f"has scored it")
    return errors


def series(store) -> None:
    dims = store["dimensions"]
    rows = store["reviews"]
    if not rows:
        print("no reviews recorded")
        return
    width = max(len(r["release"]) for r in rows) + 2
    print(f"{'release':<{width}}{'genre':<12}" +
          "".join(f"{d:>8}" for d in dims) + "   outcome")
    for r in rows:
        cells = []
        for d in dims:
            s, rd = r["self"].get(d), r["reader"].get(d)
            # self/reader, and the gap between them is what the protocol acts on.
            cell = "-" if s is None and rd is None else (
                f"{'-' if s is None else s}/{'-' if rd is None else rd}")
            cells.append(f"{cell:>8}")
        print(f"{r['release']:<{width}}{r['genre']:<12}" + "".join(cells)
              + f"   {r['outcome']}")

    print("\nself/reader per dimension. A gap of 2 or more forces a retrospective "
          "(eval-rubric.md step 3).")
    for d in dims:
        seen = [(r["release"], r["self"].get(d), r["reader"].get(d))
                for r in rows
                if r["self"].get(d) is not None or r["reader"].get(d) is not None]
        if not seen:
            print(f"  {d}: never scored")
            continue
        trail = " → ".join(f"{rel}:{'-' if rd is None else rd}" for rel, _s, rd in seen)
        diverged = [rel for rel, s, rd in seen
                    if s is not None and rd is not None and abs(s - rd) >= 2]
        note = f"   divergence ≥2 at {', '.join(diverged)}" if diverged else ""
        print(f"  {d} reader: {trail}{note}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="validate only")
    args = ap.parse_args(argv)
    try:
        store = json.loads(STORE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL  reviews/scores.json is unreadable: {exc}")
        return 1
    errors = validate(store)
    for err in errors:
        print(f"FAIL  {err}")
    if errors:
        return 1
    if args.check:
        print(f"ok    {len(store['reviews'])} review(s) recorded, schema valid")
        return 0
    series(store)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
