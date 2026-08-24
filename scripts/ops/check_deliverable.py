#!/usr/bin/env python3
"""Every pre-delivery instrument, one command, one verdict block.

    python3 scripts/ops/check_deliverable.py <file> [--terms <list>]
    python3 scripts/ops/check_deliverable.py <file> --trace-id t-... [--json]

Why this exists, measured rather than felt: a 15-page deck took **ten**
build-check-fix rounds, and the autopsy attributed at least three of them to
nothing but partial reading — the author assembled the gate stack by hand,
filtered each tool's output to protect their own context, and so met failures
in installments that had all been present in the first report. A second class
came from running the slow rendered check only after the text checks were
clean, serially. The historical lineages are worse: one proposal carried
twenty-three run numbers under the same workflow.

So: this launches the RENDERED check first (it is the slow one — the browser
renders while the text checks run), executes every instrument, and ends in ONE
block that lists every gating failure, every graded failure, and every
check that could not be measured. There is nothing to grep and nothing to
scroll past; the last block is the whole verdict. Genre is read from the
document's own declaration unless overridden — the document says what it is.

The exit code is THIS BLOCK's, not the instruments'. Zero only when nothing
gates and nothing went unmeasured: a gate the document is too old to be held to
no longer fails the run, and a check that could not run still does — a check
nobody ran is not a check that found nothing.
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
import statistics  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import checker_report  # noqa: E402
import eval_corpus  # noqa: E402
import fingerprint  # noqa: E402
import gate_registry  # noqa: E402
import inspect_layout  # noqa: E402
import markup  # noqa: E402
import trace_store  # noqa: E402
from deliverable_registry import GENRES, kinds  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())


def gather(path: pathlib.Path, genre: str | None, terms: str | None,
           skip_layout: bool = False, iterate: bool = False,
           sheet: bool = False, against=None) -> dict:
    """Run every instrument; -> {kind: run dict}. Layout goes first and runs
    concurrently — it renders in a browser while the text checks execute."""
    runs: dict[str, dict] = {}
    layout_proc = None
    t0 = time.monotonic()
    if not skip_layout:
        layout_proc = subprocess.Popen(
            checker_report.checker_argv("layout", path, iterate=iterate,
                                        sheet=sheet, against=against),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for kind in kinds():
        if kind == "layout":
            continue
        runs[kind] = checker_report.run_checker(kind, path, genre=genre)

    # Privacy is not in the registry because its report shape differs (one
    # `verdict` per file, layers instead of metrics). It is still part of the
    # stack: P-5's term half reports NOT ATTEMPTED without a list, and that is
    # a nonzero exit here, never a quiet skip.
    argv = [sys.executable, str(ROOT / "scripts/check/check_privacy.py"),
            str(path), "--json"]
    if terms:
        argv += ["--terms", terms]
    proc = subprocess.run(argv, capture_output=True, text=True)
    reports, spoke = checker_report.parse_report(proc.stdout)
    runs["privacy"] = {"kind": "privacy", "exit": proc.returncode,
                       "spoke": spoke, "reports": reports}

    if layout_proc is not None:
        out, _err = layout_proc.communicate(timeout=900)
        reports, spoke = checker_report.parse_report(out)
        runs["layout"] = {"kind": "layout", "exit": layout_proc.returncode,
                          "spoke": spoke, "reports": reports,
                          "seconds": round(time.monotonic() - t0, 1)}
    else:
        # Skipped is a loud state, not a silent one: the run records an
        # instrument that did not speak, and the exit stays nonzero.
        runs["layout"] = {"kind": "layout", "exit": None, "spoke": False,
                          "reports": None, "skipped": True}
    return runs


def eval_notes(path: pathlib.Path, runs: dict) -> list[str]:
    """-> the Evals, as graded notes, from the reports this run already holds.

    **The Evals were not in this block at all**, so the one command that exists
    so nobody meets failures in installments left out the measure of whether the
    document is the right KIND of document — prose-only share, figures per
    content page, list density, visual share. An author ran `eval_corpus.py`
    separately or did not run it, and running it separately cost a second full
    render of the same file: 17 seconds to recompute numbers this process had
    already measured.

    They stay GRADED and never gating, which is what `eval_corpus` has always
    been (CLAUDE.md: "REPORTS, never gates"). A threshold miss is a question for
    a person.
    """
    try:
        measured = eval_corpus.measure(path, with_render=True,
                                       design=runs.get("design"),
                                       layout=runs.get("layout"))
        table = eval_corpus.thresholds()
    except Exception as exc:                                    # noqa: BLE001
        return [f"evals: not measured ({exc.__class__.__name__}: {exc})"]
    if measured.get("unmeasurable"):
        return [f"evals: unmeasurable — {measured['unmeasurable']}"]
    out = []
    for row in eval_corpus.score(measured, table):
        if row["verdict"] == "MISS":
            out.append(f"evals: {row['metric']}={row.get('value')} "
                       f"({row['direction']} {row.get('bar')})")
        elif row["verdict"] == "not measured":
            out.append(f"evals: {row['metric']} not measured")
    return out


def _gating_ids(report: dict) -> set[str]:
    targets = report.get("targets") or {}
    return {m for m, t in targets.items() if "(gates)" in (t or "")}


def _family_of(line: str) -> str:
    """-> the concept a finding belongs to, from `evals/gates.json`.

    The line is `"<kind>: <metric> <verdict>"` and the metric is the second
    word; a finding whose metric is not a declared verdict (the privacy line,
    the trace line, an Evals row) keeps its own kind as its heading, which
    reads correctly rather than forcing everything into a taxonomy built for
    gates.
    """
    parts = line.split(None, 2)
    metric = parts[1] if len(parts) > 1 else ""
    try:
        row = gate_registry.load().get(metric)
    except (OSError, ValueError, KeyError):
        row = None
    if row:
        return row["family"]
    return (parts[0].rstrip(":") if parts else "other") or "other"


def _grouped(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Findings by concept, largest group first.

    **Why the report groups at all.** Forty-six lines came out in the order the
    checkers happened to emit them, so five agenda defects sat in four separate
    places and a reader met the same page four times without being told it was
    the same page. The owner's word for the cost was that every use of the skill
    gets more expensive as the gate set grows; this is where that is felt, and
    grouping costs no assertion.
    """
    out: dict[str, list[str]] = {}
    for line in lines:
        out.setdefault(_family_of(line), []).append(line)
    return sorted(out.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def _emit(label: str, lines: list[str]) -> None:
    for family, group in _grouped(lines):
        print(f"  ── {family}")
        for line in group:
            print(f"  {label}  {line}")


def _since(metric: str) -> str:
    """-> the release a gate arrived in, for the line a reader sees."""
    try:
        return gate_registry.load().get(metric, {}).get("since", "?")
    except (OSError, ValueError, KeyError):
        return "?"


def verdict_block(runs: dict, built: str | None = None
                  ) -> tuple[list[str], list[str], list[str], list[str], int]:
    """-> (gating, graded, silent, not_held, exit_code). The one block at the end.

    `built` is the version the document declares — `built with lumi-style
    X.Y.Z`, read by `fingerprint.version_in`. A gate introduced AFTER that
    version has nothing to say about this document: its finding goes to
    `not_held`, which is neither a pass nor a failure and does not touch the
    exit code.

    **Why this exists** (owner directive, 2026-08-22): historical deliverables
    were never meant to be upgraded to satisfy rules written after them. Before
    this, the gate set applied was always HEAD's — `built_version` was captured
    by `run_conformance` and read by nothing that decided anything — so a deck
    accepted at 0.1.449 was failed by a gate written at 0.1.560 and the failure
    read exactly like a defect. A NEW deliverable is still held to everything.

    A document with NO stamp is held to everything, deliberately: an absent
    stamp must never become an exemption, or the cheapest way to escape every
    gate is to delete the line saying which rules you were written against.
    """
    gating: list[str] = []
    graded: list[str] = []
    silent: list[str] = []
    not_held: list[str] = []
    # SILENT RAISES THE EXIT, everywhere. 0.1.574 stopped inheriting the
    # instruments' exits so `since` could move a finding out of the gating
    # bucket — and five branches append to `silent`, of which only one still
    # touched `worst`. The block printed "this is not a pass" beside three
    # different findings and returned 0. The summary line has always asserted
    # "N unmeasured/silent" alongside a nonzero exit; nothing held it.
    #
    # The exit is computed from THIS block's own buckets, not inherited from
    # the instruments'. `check_design` and `check_prose` grade a document
    # against HEAD's rules by construction and know nothing about `since`, so
    # inheriting their exit made the version scope cosmetic: a gate the block
    # had just filed under `not held` still failed the run, and the summary
    # then read "exit 1 · 0 gating findings", which is a summary contradicting
    # the block above it. An instrument that exits nonzero and produces NO
    # verdicts is a different thing — that is a crash, and it still fails.
    worst = 0
    for kind, run in runs.items():
        if not run["spoke"]:
            why = "skipped" if run.get("skipped") else "no parseable report"
            silent.append(f"{kind}: the instrument did not speak ({why})")
            worst = max(worst, 1)
            continue
        if not run["reports"] and run["exit"] not in (0, None):
            # check_design drops an UNMEASURABLE file from its JSON entirely,
            # so "nonzero with an empty report" is a real answer — and without
            # this line it was an invisible one: the tri-failing red run showed
            # prose, privacy and layout and said nothing at all about design.
            silent.append(f"{kind}: exited {run['exit']} with an empty report "
                          f"— the document could not be measured at all")
            # AND IT FAILS THE RUN. 0.1.574 stopped inheriting the instruments'
            # exits so that `since` could move a finding out of the gating
            # bucket, and this branch lost its exit with them: the block
            # printed "could not be measured at all" and returned 0. A
            # document nothing could measure is not a document that passed.
            worst = max(worst, 1)
            continue
        for report in run["reports"] or []:
            if report.get("unmeasurable"):
                silent.append(f"{kind}: unmeasurable — {report['unmeasurable']}")
                worst = max(worst, 1)
            if report.get("unmeasured"):
                worst = max(worst, 1)
                silent.append(f"{kind}: {report['unmeasured']} rendered "
                              f"check(s) could not be measured")
            # Reported layout findings that used to live only in the report
            # prose — the reviewer called wrapped captions this author's
            # chronic defect, and the instrument's line never reached the one
            # block anyone reads. The page rows live one level down, inside
            # each per-geometry result — the first version read a top-level
            # `pages` that does not exist, and its own planted red caught it:
            # the r10 deck's two wrapped captions never surfaced.
            geo_rows = report.get("results") or [report]
            seen_wrap: dict[str, bool] = {}
            for geo in geo_rows:
                for pg in geo.get("pages") or []:
                    if pg.get("capWrapped"):
                        seen_wrap[pg.get("id", "?")] = True
            if seen_wrap:
                graded.append(f"{kind}: {len(seen_wrap)} figure caption(s) "
                              f"wrap to a second line "
                              f"({', '.join(sorted(seen_wrap))}) — shorten "
                              f"the name, never the type")
            for m in report.get("blind_gates") or []:
                worst = max(worst, 1)
                silent.append(f"{kind}: gating metric {m} could not be "
                              f"measured (this is not a pass)")
            gates = _gating_ids(report)
            for metric, verdict in (report.get("verdicts") or {}).items():
                if verdict in ("ok", "n/a"):
                    continue
                line = f"{kind}: {metric} {verdict}"
                # WHICH PAGE. The instrument computes it and used to drop it,
                # so an author who read this block still had to re-run the
                # renderer to find out where to go. The `capWrapped` block
                # above is the same need, solved by hand for one finding.
                where = (report.get("details") or {}).get(metric)
                if where:
                    line += f" — {where}"
                # Layout's deliverable verdicts all gate; prose/design gate
                # only where the target says so.
                if kind == "layout" or metric in gates:
                    since = _since(metric)
                    if not gate_registry.held(metric, built):
                        not_held.append(f"{line} — this gate arrived at "
                                        f"{since}; the document declares "
                                        f"{built}")
                    else:
                        gating.append(line)
                else:
                    graded.append(line)
            if kind == "privacy":
                v = report.get("verdict")
                if v and v != "ok":
                    line = (f"privacy: declared terms {v}"
                            if v in ("not_attempted", "missing")
                            else f"privacy: {v}")
                    (gating if gate_registry.held("privacy_terms", built)
                     else not_held).append(line)
    return gating, graded, silent, not_held, worst


def _text_share(signature: str) -> int:
    """-> the percent of a figure-shape signature that is `text`.

    A signature is `tag:pct` parts joined by commas, percentages rounded to the
    nearest ten (`inspect_layout`'s figShapes). `text:90` and `line:10,text:90`
    are the same drawing as far as structure goes.
    """
    for part in signature.split(","):
        tag, _, pct = part.partition(":")
        if tag == "text":
            try:
                return int(pct)
            except ValueError:
                return 0
    return 0


def _rendered_shape(runs) -> dict:
    """-> the shape readings only a render can produce, from THIS run's reports.

    `visual_share_median` is `eval_corpus`'s own computation over the rendered
    pages; `repeated_skeleton_pages` counts the pages drawing a skeleton that
    `inspect_layout.FIGURE_SHAPE_REPEAT` or more pages draw — the checker's own
    bar, imported, because two thresholds under one metric name is exactly what
    the corpus must not hold. Both are descriptive: they say what the document
    looked like, never whether that was good enough.
    """
    out: dict[str, object] = {}
    reports = (runs.get("layout") or {}).get("reports") or []
    doc = reports[0] if reports else None
    if not isinstance(doc, dict):
        return out
    # THE SAME SELECTOR `eval_corpus` USES (`"pages" in r`, not truthiness).
    # `inspect_layout` emits one entry per geometry — five by default — so
    # "several entries carry pages" is the normal case, and the two selectors
    # disagreed whenever the first one was empty: one returned None, the other
    # a median from a different geometry. Two computations under one metric
    # name is what the `no shadow math` guard is about, and a corpus holding
    # both would compare numbers that are not the same number.
    geometry = next((r for r in doc.get("results", []) if "pages" in r), None)
    if geometry is None or not geometry.get("pages"):
        return out
    # RECORD WHICH GEOMETRY IT CAME FROM. A median with no geometry beside it
    # is not comparable across documents, and `bar_replay` compares them.
    if geometry.get("geometry"):
        out["geometry"] = geometry["geometry"]
    shares = [p["visualPct"] for p in geometry["pages"]
              if isinstance(p.get("visualPct"), (int, float))
              and not (p.get("isOpener") or p.get("isCover")
                       or p.get("isClosing") or p.get("isApparatus"))]
    if shares:
        out["visual_share_median"] = round(statistics.median(shares), 1)
    seen: dict[str, set] = {}
    for page in geometry["pages"]:
        for sig in set(page.get("figShapes") or []):
            seen.setdefault(sig, set()).add(page.get("id"))
    # `inspect_layout.FIGURE_SHAPE_REPEAT` is the checker's own bar for calling
    # a skeleton repeated, and it is 3 — not 2. Counting at 2 here and calling
    # the result by the checker's name would put two different definitions of
    # one metric into the corpus. The threshold is imported, not retyped.
    repeated = {pid for ids in seen.values()
                if len(ids) >= inspect_layout.FIGURE_SHAPE_REPEAT for pid in ids}
    if seen:
        out["repeated_skeleton_pages"] = len(repeated)

    # PAGES THAT DECLARE DIFFERENT ANALYTICAL MOVES AND DRAW THE SAME SKELETON.
    # GAP-025 asks whether a deck's figures repeat, and wanted a share to gate
    # on. This is the contradiction form of the same question and needs no
    # threshold — a page saying it compares and a page saying it positions
    # should not arrive as the same drawing.
    #
    # MEASURED, NOT GATED, and the calibration is why. The two judged
    # documents on record — one accepted, one rejected — carry no
    # `data-analysis` at all; both predate the convention — so they cannot exercise it, and a gate no accepted document
    # can exercise is FM-01 waiting to happen. On the two decks that do declare
    # moves it fires only on the degenerate signature below, which is excluded.
    # So it has no failing case anywhere yet: it accumulates in the corpus until
    # there is material, which is what `bar_replay.py` will then read.
    by_sig: dict[str, set] = {}
    excluded = 0
    for page in geometry["pages"]:
        move = (page.get("declaredMove") or "").strip()
        if not move:
            continue
        for sig in set(page.get("figShapes") or []):
            # A DRAWING THAT IS ALL TEXT carries no structure to share, so two
            # pages "agreeing" on it says nothing about either. Keyed on the
            # TEXT SHARE, not on the absence of a comma: signature parts are
            # percentages rounded to ten, so one stray element makes
            # `line:0,text:100` — every bit as structureless, and the comma
            # rule let it through. Measured on a real deck, three of its four
            # signatures were text-only and only one was excluded.
            if _text_share(sig) >= 90:
                excluded += 1
                continue
            by_sig.setdefault(sig, set()).add(move)
    # A MEASURED ZERO IS A READING. Keyed on whether any page DECLARED a move,
    # not on whether any skeleton survived the exclusion: `if by_sig` omitted
    # the key for a document where the honest answer is 0, the schema says an
    # absent key means "not measured", and the corpus would then hold only the
    # documents that happened to clash — a distribution biased toward the
    # defect, which is the 0.1.592 failure this release exists to prevent.
    if any((page.get("declaredMove") or "").strip() for page in geometry["pages"]):
        out["move_skeleton_clashes"] = sum(
            1 for v in by_sig.values() if len(v) > 1)
        # A zero over nothing but text blobs is not the same statement as a
        # zero over real drawings, and the number alone cannot tell them apart.
        if excluded:
            out["text_only_figures"] = excluded
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--genre", choices=GENRES,
                    help="override the document's own data-genre declaration")
    ap.add_argument("--terms", help="the engagement's out-of-bounds list, "
                                    "for check_privacy's gating half")
    ap.add_argument("--trace-id", help="close this build trace afterwards "
                                       "(trace.py close, verdicts transcribed); "
                                       "default: the document's own data-trace")
    ap.add_argument("--fast", action="store_true",
                    help="the author's loop: the rendered check runs at the "
                         "declared stage only, with no off-shape sweep. Every "
                         "gate still runs — 3s instead of 16s on a twelve-page "
                         "deck. NOT a delivery reading; run it without --fast "
                         "before you hand the document over")
    ap.add_argument("--sheet", action="store_true",
                    help="also build the contact sheet, and print where it "
                         "landed. Off by default because a harness run has "
                         "nobody watching — but the sheet IS the last gate "
                         "(`SKILL.md`: 'look at the sheet'), and suppressing it "
                         "unconditionally is why authors ran inspect_layout a "
                         "second time. Pass it on the delivery round")
    ap.add_argument("--skip-layout", action="store_true",
                    help="no browser available; recorded as a silent "
                         "instrument and the exit stays nonzero")
    ap.add_argument("--against", type=pathlib.Path, metavar="BEFORE.json",
                    help="the previous round's layout --json. Passed to the "
                         "renderer, which prints what moved between then and "
                         "now — the reading that says whether a repair landed")
    ap.add_argument("--reports-dir", type=pathlib.Path, metavar="DIR",
                    help="write each instrument's raw --json here, one file "
                         "per kind. The debug-log contract asks the author to "
                         "`attach` those documents, and this process gathered "
                         "them in memory and threw them away — so honouring "
                         "the contract meant re-running all three checkers, "
                         "one of them a second browser render")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not a.file.is_file():
        sys.exit(f"no such deliverable: {a.file}")

    raw = a.file.read_text(encoding="utf-8", errors="replace")
    genre = a.genre or markup.body_attr(raw, "data-genre")
    # The trace id rides in the document (`<body data-trace="t-…">`, written
    # by new_deck.py at scaffold time) so the build that opened the record is
    # the build that closes it, with nothing retyped in between.
    trace_id = a.trace_id or markup.body_attr(raw, "data-trace")

    started = time.monotonic()
    runs = gather(a.file, genre, a.terms, skip_layout=a.skip_layout,
                  iterate=a.fast, sheet=a.sheet, against=a.against)
    if a.reports_dir:
        a.reports_dir.mkdir(parents=True, exist_ok=True)
        for kind, run in runs.items():
            reports = run.get("reports")
            if reports is None:
                continue
            doc = reports[0] if len(reports) == 1 else reports
            (a.reports_dir / f"{kind}.json").write_text(
                json.dumps(doc, indent=2), encoding="utf-8")
    checks_seconds = max(1, round(time.monotonic() - started))
    # THE VERSION THE DOCUMENT DECLARES. `fingerprint.version_in` reads the
    # colophon every LUMI deliverable carries; it existed and nothing that
    # decided anything read it.
    built = fingerprint.version_in(raw)
    gating, graded, silent, not_held, worst = verdict_block(runs, built)
    if gating or silent:
        # The invariant the summary line asserts: a finding in either bucket is
        # a nonzero exit. Held here as well as at each append, because a later
        # branch that forgets is exactly how this broke.
        worst = max(worst, 1)
    graded.extend(eval_notes(a.file, runs))
    if not trace_id:
        # Unmeasured, not silent: a build with no trace leaves no record of
        # its phases, its driver or its verdicts, and until 0.1.531 that
        # absence printed nothing — fourteen consecutive builds of one deck
        # left zero traces while the ledger reported "0 abandoned builds".
        silent.append("trace: none — this build leaves no record (new_deck.py "
                      "opens one; or trace.py open, then --trace-id)")
        worst = max(worst, 1)
    elif not (trace_store.traces_dir() / f"{trace_id}.json").is_file():
        # THE ID IS A PROMISE THAT A RECORD EXISTS, and `--fast` never asked.
        #
        # Be precise about what was already there: the close step below fails
        # on an id it cannot find, prints `no such trace: t-…` and carries a
        # nonzero exit back, so a DELIVERY round has always caught this. But
        # that step is skipped under `--fast` — the author's inner loop, the
        # one run many times per build — so a deck naming a trace stored
        # nowhere ran the whole loop clean, exit 0, with the word `trace`
        # appearing nowhere in the output. Measured on three real decks from
        # one validation round, and on a synthetic one in tests/test_trace.py.
        #
        # A DANGLING ID IS WORSE THAN AN ABSENT ONE. Absent prints
        # `trace: none` and a reader knows where they stand; dangling said
        # nothing, so the deck read as measured while naming a record no one
        # can open. An open trace is NOT this case — `trace.py open` writes
        # the record before it prints the id, so a build still in flight
        # resolves here and closes below.
        silent.append(
            f"trace: {trace_id} names no record — the document declares a "
            f"trace that is not in {trace_store.traces_dir()}. The id was "
            f"kept and the record was not; a build whose record cannot be "
            f"opened is not a measured build")
        worst = max(worst, 1)

    if a.json:
        print(json.dumps({"file": str(a.file), "genre": genre,
                          "built": built,
                          "gating": gating, "graded": graded, "silent": silent,
                          "not_held": not_held,
                          "exits": {k: r["exit"] for k, r in runs.items()},
                          "exit": worst}, indent=1))
    else:
        secs = runs["layout"].get("seconds")
        print(f"{a.file.name}  (genre={genre or 'undeclared'}"
              + (f", layout rendered concurrently in {secs}s" if secs else "")
              + (", --fast: the declared stage only" if a.fast else "")
              + ")")
        # WHAT MOVED SINCE THE LAST ROUND. The renderer computes it under
        # --json and it would otherwise sit unread in the report: this is the
        # only line in the package that can say a repair did not land, and one
        # measured session ran six rounds after its last failure without it.
        for rep in (runs.get("layout") or {}).get("reports") or []:
            rows = rep.get("against") or []
            if not rows:
                continue
            print(f"\n  what moved since the last round ({len(rows)}):")
            mark = {"ok": "ok  ", "FAIL": "FAIL", "note": "note",
                    "not_measured": "n/m "}
            for row in rows[:12]:
                print(f"    {mark.get(row.get('verdict'), '?')}  "
                      f"{row.get('subject', ''):26} {row.get('detail', '')}")
            if len(rows) > 12:
                print(f"    … {len(rows) - 12} more in the --json")
            break

        # WHAT LANGUAGE IS THIS. Zero hits for `lang` in this file before
        # 0.1.588, so the one block that exists to spare an author from meeting
        # failures in installments never said which language it had graded —
        # while three validation rounds shipped a language nobody asked for.
        for rep in (runs.get("prose") or {}).get("reports") or []:
            lang = rep.get("language") or "undeclared"
            if rep.get("M16_language_asked"):
                print(f"  language: {lang} \u2014 NOT ASKED FOR (M16). English "
                      f"is the default and needs no record; another language "
                      f"is derived with scripts/ops/localize.py from an "
                      f"English deck that passed.")
            elif lang == "en":
                print("  language: en (the default)")
            elif lang != "undeclared":
                print(f"  language: {lang} (derived from "
                      f"{rep.get('localized_from')}; asked: "
                      f"\"{rep.get('ask_quote')}\")")
            break
        print("\n\u2500\u2500 the verdict \u2014 every instrument, one block "
              "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
        _emit("GATE", gating)
        _emit("MUTE", silent)
        _emit("note", graded)
        # NEITHER A PASS NOR A FAILURE, and printed as its own word. A gate
        # written after this document has nothing to say about it; reporting
        # that as `note` would put it in the same bucket as a real graded
        # finding, and as `GATE` would be the behaviour this exists to end.
        for line in not_held:
            print(f"  past  {line}")
        if not (gating or silent or graded or not_held):
            print("  every instrument spoke, and nothing failed. The last "
                  "gate is a person: look at the contact sheet.")
        # WHERE the sheet is, when one was built. "Look at the contact sheet"
        # is the last gate and it was an instruction with no address.
        for rep in (runs.get("layout") or {}).get("reports") or []:
            sheets = [row.get("sheet") for row in (rep.get("results") or [])
                      if row.get("sheet")]
            if sheets:
                png = pathlib.Path(sheets[0]).with_suffix(".png")
                if png.is_file():
                    print(f"\n  contact sheet: {png}")
                    print("  One image, every page. Look at it — that is the "
                          "last gate; the numbers only say where to look.")
                    break
                print(f"\n  contact sheet: {sheets[0]}")
                print("  Look at it. That is the last gate; the numbers only "
                      "say where to look.")
                break
        print(f"\nexit {worst}: {len(gating)} gating · {len(silent)} unmeasured"
              f"/silent · {len(graded)} graded findings"
              + (f" · {len(not_held)} not held (this document declares "
                 f"{built or 'no version'})" if not_held else ""))

    if a.fast:
        # A LOOP READING IS NOT A DELIVERY READING, and the difference has to
        # survive being read by somebody in a hurry. Printed after the verdict
        # block rather than before it, because the last line is what gets read
        # — and on STDERR, because `--json`'s stdout is a document a parser
        # reads and a note appended to it is a note that breaks the parse. The
        # first version of this line did exactly that and its own test caught
        # it.
        print("\n  --fast: one geometry, no off-shape sweep. Run this again "
              "without --fast before delivery.", file=sys.stderr)
    # A RED BUILD IS STILL A MEASURED BUILD. Closing only on a green,
    # non-`--fast` run meant every loop round left an open trace, and
    # `ledger.py` then reported them as abandoned — one manual `trace.py close`
    # each. The trace records what happened; refusing to close it on a failure
    # loses exactly the rounds worth studying.
    if trace_id and not a.fast:
        # Stop the build clock the scaffold started (if it is running), then
        # close with THIS run's own duration as the checks phase. Both numbers
        # are the tooling's; neither is typed.
        stop = [sys.executable, str(ROOT / "scripts/ops/trace.py"), "phase",
                "stop", "build", "--id", trace_id]
        stopped = subprocess.run(stop, capture_output=True, text=True)
        if stopped.returncode == 0:
            print(stopped.stdout.strip())
        close = [sys.executable, str(ROOT / "scripts/ops/trace.py"), "close",
                 "--id", trace_id, "--deliverable", str(a.file),
                 "--phase", "checks", str(checks_seconds)]
        # HAND OVER THE TWO READINGS THAT NEEDED A BROWSER. This run rendered
        # the document; `trace.py close` does not and should not. Passing them
        # is what lets the corpus keep a shape for every build instead of
        # re-measuring old files by hand — which is why GAP-024's bar was
        # drafted from five documents found one at a time and refuted by a
        # sixth nobody had thought to check.
        shape = _rendered_shape(runs)
        for flag, key in (("--visual-share-median", "visual_share_median"),
                          ("--repeated-skeleton-pages", "repeated_skeleton_pages"),
                          ("--move-skeleton-clashes", "move_skeleton_clashes")):
            if shape.get(key) is not None:
                close += [flag, str(shape[key])]
        proc = subprocess.run(close, capture_output=True, text=True)
        print(proc.stdout.strip() or proc.stderr.strip())
        worst = max(worst, proc.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
