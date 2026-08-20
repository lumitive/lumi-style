#!/usr/bin/env python3
"""Score a corpus of deliverables against the Evals thresholds.

The checkers answer "is this document well formed". This answers a different
question: **is this document as good as the one whose acceptance is on record.**
The two are not the same, and the gap between them is measured — a deck that
passed every design verdict turned out to carry five figures where the
accepted document carries twenty-two, and half its content pages carried nothing
visual at all.

So the thresholds here sit on quantities the gates do not touch, and every one of
them names the evidence that set it (`evals/thresholds.json`) — how many hold
each level is in that file and deliberately not repeated here, because a count
in prose is the thing this package keeps finding one release behind. Only the
two genres with a document on record can read `calibrated` at all. This package
has withdrawn an invented threshold before, and the withdrawal is the reason the
`evidence` field exists.

**Nothing here gates.** A bar that is missed is printed, and the exit code says
only whether the measurement could be taken — 1 when a document could not be
scored or a threshold could not be measured, 0 when every number was obtained,
whatever the numbers were. Two reasons, both in `evals/thresholds.json`'s
`status_note`: a red-team pass cleared all four bars on the rejected document
with two mechanical rewrites that added no content, and two of the four numbers
were refused as gates IN WRITING by the checkers they come from, on exactly that
reasoning. Promotion needs the agreement study, not a decision.

It is an evaluation of DOCUMENTS, not of this repository, so it never runs in CI.

    python3 scripts/ops/eval_corpus.py <file> [<file> ...]
    python3 scripts/ops/eval_corpus.py --corpus            # the recorded corpus
    python3 scripts/ops/eval_corpus.py <file> --json
"""
from __future__ import annotations

import argparse
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import re
import statistics
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
import corpus  # noqa: E402
from deliverable_registry import GENRES, checker_path  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
THRESHOLDS = ROOT / "evals" / "thresholds.json"


def genre_of(raw: str) -> str | None:
    """The genre the document declares. Never guessed: a document graded under
    a genre it did not declare is measured against the wrong targets, and the
    checker that used to default to `sales` graded a training handbook at the
    sales visual share and printed a confident green line about it."""
    m = re.search(r'<body[^>]*\bdata-genre="([^"]+)"', raw)
    return m.group(1) if m and m.group(1) in GENRES else None


def measure(path: pathlib.Path, with_render: bool) -> dict:
    """Every quantity the thresholds name, for one document."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    genre = genre_of(raw)
    out: dict = {"file": str(path), "genre": genre}
    if genre is None:
        out["unmeasurable"] = ("no data-genre on <body>, or one this package "
                               "does not know — nothing to compare against")
        return out

    design = subprocess.run(
        [sys.executable, str(checker_path("design")), str(path), "--json"],
        capture_output=True, text=True)
    try:
        d = json.loads(design.stdout)[0]
    except (ValueError, IndexError):
        out["unmeasurable"] = "check_design produced no parseable report"
        return out

    if design.returncode:
        out["gates"] = (f"check_design exits {design.returncode} on this "
                        f"document — a threshold score is not a gate verdict")
    vis = d.get("D16_visual_presence") or {}
    drawn = d.get("D5_drawn_share") or {}
    parity = d.get("D5_figure_parity") or {}
    pages = vis.get("content_pages") or 0
    # THE DRAWN SUBSET, not every `.fig` block. d5_drawn_share exists precisely
    # to separate them — its own docstring names the deck "whose figures were
    # all HTML blocks, measured clean on every gate and read as flat" — and
    # reading `figures` here meant a document with zero drawings anywhere
    # cleared a floor whose unit string says "drawn figures".
    figures = drawn.get("drawn") or 0
    if not pages:
        out["unmeasurable"] = "no content pages"
        return out

    out["content_pages"] = pages
    out["prose_only_share"] = round(len(vis.get("prose_only") or []) / pages, 3)
    out["figures_per_content_page"] = round(figures / pages, 3)
    # COUNTED ON CONTENT PAGES ONLY, to match the denominator. Counting the
    # whole file while dividing by content pages punishes the correct move: an
    # ops guide with a boundaries list on a declared apparatus page read 1.042
    # against an honest 0.708, because the list stayed in the numerator while
    # its page left the denominator.
    body = re.sub(r'<section[^>]*\bdata-role="apparatus".*?</section>', " ",
                  raw, flags=re.S)
    for cls in ("cover", "closing", "opener"):
        body = re.sub(rf'<section[^>]*class="[^"]*\b{cls}\b.*?</section>', " ",
                      body, flags=re.S)
    out["list_items_per_content_page"] = round(
        len(re.findall(r"<li\b", body)) / pages, 3)
    out["reported"] = {
        "fig_blocks": drawn.get("figures") or 0,
        "drawn": figures,
        "laid_out": drawn.get("laid_out"),
        "rect_only_share": round((parity.get("rect_only_figures") or 0)
                                 / max(figures, 1), 3),
        "shape_kinds_min": parity.get("shape_kinds_min"),
        "arrowed_figure_share": round((parity.get("figures_with_arrows") or 0)
                                      / max(figures, 1), 3),
        "tables": len(re.findall(r"<table\b", raw)),
    }

    # The rendered half costs a browser and about thirty seconds a document, so
    # a sweep may skip it — and says so rather than reporting a partial score as
    # a whole one.
    out["visual_share_median"] = None
    if not with_render:
        out["render_state"] = "skipped by --no-render"
        return out

    layout = subprocess.run(
        [sys.executable, str(checker_path("layout")), str(path),
         "--deliverable", "--json", "--no-sheet"], capture_output=True, text=True)
    try:
        doc = json.loads(layout.stdout)
    except ValueError:
        # A CRASHED BROWSER IS NOT A SKIPPED ONE. Both used to produce the same
        # row and the same words — "the rendered half was not run" — so a
        # missing Chromium, an argparse drift or a page that would not load all
        # read as a deliberate choice. The exit code was never even looked at.
        out["render_state"] = (
            f"inspect_layout exited {layout.returncode} and emitted no parseable "
            f"report: {(layout.stdout + layout.stderr).strip()[:200]}")
        return out
    geometry = next((r for r in doc.get("results", []) if "pages" in r), None)
    if geometry is None or not geometry["pages"]:
        # `results` is a heterogeneous list — per-geometry entries plus a
        # per-file aspect entry with no `pages` key — so index 0 was a guess.
        out["render_state"] = ("inspect_layout matched no page; that is a report "
                               "about zero pages, not a clean document")
        return out
    shares = [p["visualPct"] for p in geometry["pages"]
              if p.get("visualPct") is not None
              and not (p.get("isOpener") or p.get("isCover")
                       or p.get("isClosing") or p.get("isApparatus"))]
    if not shares:
        out["render_state"] = (f"{len(geometry['pages'])} pages rendered and none "
                               f"is a gradable content page")
        return out
    out["visual_share_median"] = round(statistics.median(shares), 1)
    return out


def score(measured: dict, table: dict) -> list[dict]:
    """-> one row per threshold: its bar, the document's value, and the verdict."""
    rows = []
    small = measured["content_pages"] < table.get("min_content_pages", 0)
    for name, spec in table["metrics"].items():
        bar = (spec["genres"].get(measured["genre"]) or {})
        if bar.get("value") is None:
            rows.append({"metric": name, "verdict": "no bar",
                         "detail": bar.get("why") or bar.get("evidence")
                         or f"no bar for genre {measured['genre']!r}"})
            continue
        if small and spec.get("needs_corpus_size", True):
            # A ratio over four pages is one page's opinion. check_prose draws
            # the same line for number-sourcing.
            rows.append({"metric": name, "verdict": "too few pages",
                         "bar": bar["value"], "evidence": bar["evidence"],
                         "detail": f"{measured['content_pages']} content pages, "
                                   f"under the {table['min_content_pages']} a "
                                   f"per-page ratio needs to mean anything"})
            continue
        value = measured.get(name)
        if value is None:
            # NOT a pass. A quantity that was not measured has not cleared its
            # bar; reporting it as ok is the reassuring line this package keeps
            # finding in its own output.
            rows.append({"metric": name, "verdict": "not measured",
                         "bar": bar["value"], "evidence": bar["evidence"],
                         "detail": measured.get("render_state")
                                   or "the rendered half produced no value"})
            continue
        ok = (value <= bar["value"] if spec["direction"] == "ceiling"
              else value >= bar["value"])
        rows.append({"metric": name, "verdict": "ok" if ok else "MISS",
                     "value": value, "bar": bar["value"],
                     "direction": spec["direction"], "evidence": bar["evidence"],
                     "unit": spec["unit"]})
    return rows


def main(argv=None) -> int:
    def note(*parts):
        """Prose that must never land in stdout when --json is on.

        A `--json` mode whose stdout does not parse is the defect that bit the
        debug log this same week: the caller reads the stream, not the
        intention.
        """
        print(*parts, file=sys.stderr if _json_mode[0] else sys.stdout)

    _json_mode = [False]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", type=pathlib.Path)
    ap.add_argument("--corpus", action="store_true",
                    help="score the corpus: ids from evals/thresholds.json, "
                         "paths from the gitignored evals/corpus.local.json")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-render", action="store_true",
                    help="skip the browser half; visual share reads 'not "
                         "measured' rather than passing")
    args = ap.parse_args(argv)
    _json_mode[0] = args.json

    table = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    files = list(args.files)
    unresolved = []
    if args.corpus:
        # The ids are the package's; the paths are this machine's. A corpus
        # entry naming a real deliverable in a tracked file is an engagement
        # fact (red line 9), so the mapping is local and its absence is said
        # out loud rather than read as an empty corpus.
        local_path = corpus.LOCAL_CORPUS
        local = {k: str(p) for k, p in corpus.paths().items()}
        if corpus.load() is None:
            note(f"note  {local_path.relative_to(ROOT)} is absent, so no "
                  f"corpus document could be located. evals/README.md gives "
                  f"its shape.")
        for group in ("accepted", "rejected"):
            for entry in table["corpus"][group]:
                where = local.get(entry["id"])
                if where:
                    files.append(pathlib.Path(where).expanduser())
                else:
                    unresolved.append(entry["id"])
        if unresolved:
            note(f"note  {len(unresolved)} corpus id(s) have no local path: "
                  + ", ".join(unresolved))
    if not files and not unresolved:
        ap.error("name at least one file, or --corpus")

    # Three counters, because they are three different answers. A document that
    # is missing or unmeasurable did not miss a threshold — it took none — and
    # folding it into the miss count reports a broken corpus as a quality
    # finding. That mattered the moment the paths moved out of the tracked file.
    reports, missed, untaken, unscored = [], 0, 0, len(unresolved)
    for path in files:
        if not path.exists():
            note(f"FAIL  {path} does not exist")
            unscored += 1
            continue
        measured = measure(path, with_render=not args.no_render)
        if "unmeasurable" in measured:
            note(f"\nUNMEASURABLE  {path.name}: {measured['unmeasurable']}")
            unscored += 1
            continue
        rows = score(measured, table)
        measured["scores"] = rows
        reports.append(measured)
        missed += sum(1 for r in rows if r["verdict"] == "MISS")
        # A THRESHOLD THAT WAS NEVER TAKEN IS NOT A THRESHOLD THAT PASSED, and
        # the summary has to say so or it contradicts the row above it. With
        # --no-render the visual-share row reads `not measured` and this line
        # used to print "0 threshold miss(es)" over it and exit 0 — the exact
        # reassuring line the row's own comment refuses. `too few pages` and
        # `no bar` are different: those are decisions, made and recorded here.
        untaken += sum(1 for r in rows if r["verdict"] == "not measured")
        if args.json:
            continue
        print(f"\n{path.name}  (genre={measured['genre']}, "
              f"{measured['content_pages']} content pages)")
        for r in rows:
            if r["verdict"] in ("no bar", "not measured", "too few pages"):
                print(f"  {r['verdict']:<12} {r['metric']:<28} {r.get('detail','')}")
                continue
            arrow = "<=" if r["direction"] == "ceiling" else ">="
            print(f"  {r['verdict']:<12} {r['metric']:<28} "
                  f"{r['value']:<8} {arrow} {r['bar']}   [{r['evidence']}]")
        if measured.get("gates"):
            print(f"  gates        {measured['gates']}")
        rep = measured["reported"]
        print(f"  reported     {rep['drawn']} drawn of {rep['fig_blocks']} "
              f"fig blocks ({rep['laid_out']} laid out), "
              f"rect-only {rep['rect_only_share']}, "
              f"shape kinds {rep['shape_kinds_min']}, "
              f"arrowed {rep['arrowed_figure_share']}, "
              f"tables {rep['tables']}")

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        parts = [f"{len(reports)} document(s)", f"{missed} threshold miss(es)"]
        if untaken:
            parts.append(f"{untaken} never taken")
        if unscored:
            parts.append(f"{unscored} not scored at all")
        print("\n" + ", ".join(parts)
              + ". A miss is a question for a person, not a verdict on the writer.")
        if untaken:
            print("      a threshold that was not measured has not been cleared; "
                  "run without --no-render for the whole score")
        if unscored:
            print("      a document that could not be scored is not a document "
                  "that passed")
    # A MISS DOES NOT FAIL THE RUN. `untaken` and `unscored` do, because those
    # are the measurement failing rather than the document — a threshold nobody
    # took has not been cleared, and a document nobody could score has not
    # passed. The bars themselves report (see thresholds.json's status_note).
    return 1 if (untaken or unscored) else 0


if __name__ == "__main__":
    raise SystemExit(main())
