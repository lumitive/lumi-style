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

The exit code is the strictest aggregation: zero only when every instrument
exited zero. A check that could not run is a nonzero exit somewhere, and a
check nobody ran is not a check that found nothing.
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
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import checker_report  # noqa: E402
import eval_corpus  # noqa: E402
import fingerprint  # noqa: E402
import gate_registry  # noqa: E402
import markup  # noqa: E402
from deliverable_registry import GENRES, kinds  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())


def gather(path: pathlib.Path, genre: str | None, terms: str | None,
           skip_layout: bool = False, iterate: bool = False) -> dict:
    """Run every instrument; -> {kind: run dict}. Layout goes first and runs
    concurrently — it renders in a browser while the text checks execute."""
    runs: dict[str, dict] = {}
    layout_proc = None
    t0 = time.monotonic()
    if not skip_layout:
        layout_proc = subprocess.Popen(
            checker_report.checker_argv("layout", path, iterate=iterate),
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
            continue
        for report in run["reports"] or []:
            if report.get("unmeasurable"):
                silent.append(f"{kind}: unmeasurable — {report['unmeasurable']}")
            if report.get("unmeasured"):
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
                silent.append(f"{kind}: gating metric {m} could not be "
                              f"measured (this is not a pass)")
            gates = _gating_ids(report)
            for metric, verdict in (report.get("verdicts") or {}).items():
                if verdict in ("ok", "n/a"):
                    continue
                line = f"{kind}: {metric} {verdict}"
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
    ap.add_argument("--skip-layout", action="store_true",
                    help="no browser available; recorded as a silent "
                         "instrument and the exit stays nonzero")
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
                  iterate=a.fast)
    checks_seconds = max(1, round(time.monotonic() - started))
    # THE VERSION THE DOCUMENT DECLARES. `fingerprint.version_in` reads the
    # colophon every LUMI deliverable carries; it existed and nothing that
    # decided anything read it.
    built = fingerprint.version_in(raw)
    gating, graded, silent, not_held, worst = verdict_block(runs, built)
    if gating:
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
        print("\n── the verdict — every instrument, one block ──────────────")
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
    if trace_id and worst == 0 and not a.fast:
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
        proc = subprocess.run(close, capture_output=True, text=True)
        print(proc.stdout.strip() or proc.stderr.strip())
        worst = max(worst, proc.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
