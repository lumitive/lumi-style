#!/usr/bin/env python3
"""Scaffold, fill, embed and check — one command, one round trip.

**Why this exists, measured rather than felt.** A 2026-08 build of a ten-page
deck spent **460 API calls and 389 terminal commands**: `inspect_layout` 64
times, the fill script 46, `embed_shapes` 38, `check_design` 31, `check_prose`
28 — and the one command that runs the whole check stack, 6. Every one of those
commands is a round trip carrying the whole conversation, so the bill is
`calls x context`, and the calls were the half nobody was counting. There was no
script anywhere in this package that ran scaffold -> fill -> embed -> check, so
each stage cost a turn whether or not anything had changed.

**What it deliberately does NOT do.** It invents no format for page content. The
content is the author's and arrives as an ordinary Python script that rewrites
the deck — the pattern a real build already converged on — and this runs it. A
new page-content schema would be a new API designed without a real instance in
front of it, which is convention 15's exact warning.

    python3 scripts/ops/build.py --deck out/deck.html --script build_deck.py \\
            --outline outline.md --genre internal --storyline market-analysis \\
            --pages 10 --parts A,B,C

    ... --fast          the author's loop: 4s instead of 22 on the browser half
    ... --deliver       the delivery round: full matrix and the contact sheet
    ... --debug-log     write <stem>.debug.json as it goes, one entry per command

The exit code is the check stack's. A stage that fails stops the run, because
running the checks over a deck whose fill script died measures the scaffold.
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
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import debug_log  # noqa: E402
from deliverable_registry import COMPOSITIONS, GENRES, STORYLINES  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())


class Stage:
    """One command, run once, recorded once.

    Recording goes through `debug_log`'s own `run` subcommand rather than a
    second writer here, because a parallel implementation of the log schema is
    this repository's most-fixed defect class. What changes is only WHERE the
    loop lives: `debug_log.py run -- <cmd>` from a shell is one API round trip
    per command, so debug mode taxed the builds most likely to need it — 16
    extra turns on the build this script was written from. Here the loop is in
    one process and the log is a side effect of running.
    """

    def __init__(self, log_path: pathlib.Path | None):
        self.log_path = log_path

    def run(self, label: str, argv: list[str]) -> int:
        print(f"\u2500\u2500 {label}", flush=True)
        t0 = time.monotonic()
        if self.log_path is not None:
            rc = debug_log.main(["run", str(self.log_path),
                                 "--label", label, "--", *argv])
        else:
            rc = subprocess.run(argv).returncode
        print(f"   {label}: exit {rc} in {round(time.monotonic() - t0, 2)}s",
              flush=True)
        return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--deck", type=pathlib.Path, required=True,
                    help="the deliverable this build writes")
    ap.add_argument("--script", type=pathlib.Path,
                    help="the author's fill script. Run as `python3 <script> "
                         "<deck>`; a script that ignores the argument and "
                         "carries its own paths works unchanged")
    ap.add_argument("--outline", type=pathlib.Path,
                    help="the analysis beat's outline. Seeds the scaffold, and "
                         "the built deck is held to it afterwards "
                         "(check_outline --against, which gates)")
    ap.add_argument("--genre", choices=list(GENRES), default="internal")
    ap.add_argument("--geometry", choices=list(COMPOSITIONS), default="landscape")
    ap.add_argument("--storyline", choices=list(STORYLINES))
    ap.add_argument("--entry-path", dest="entry_path", choices=("A", "B"),
                    help="how this document reached the workflow: A is the "
                         "four-beat discussion, B starts from a recipe. The "
                         "scaffold opens no trace without it, because the "
                         "value used to be guessed from whether an --outline "
                         "was present and an outline is used on both paths.")
    ap.add_argument("--pages", type=int)
    ap.add_argument("--parts")
    ap.add_argument("--lang", default="en",
                    help="the deliverable's output language, BCP-47. Default: "
                         "en. Pass another code when the USER asked for it; "
                         "the deck is authored in that language directly")
    ap.add_argument("--lang-asked", metavar="QUOTE",
                    help="the user's own words asking for --lang, verbatim. "
                         "Required for any language but English")
    ap.add_argument("--terms", help="the engagement's out-of-bounds list, "
                                    "passed to the privacy half")
    ap.add_argument("--fast", action="store_true",
                    help="the author's loop: the declared stage only, no "
                         "off-shape sweep, no contact sheet. Every gate still "
                         "runs. NOT a delivery reading")
    ap.add_argument("--deliver", action="store_true",
                    help="the delivery round: full matrix and the contact "
                         "sheet, whose path is printed for you to look at")
    ap.add_argument("--keep-scaffold", action="store_true",
                    help="the deck already exists and is being re-filled; do "
                         "not scaffold over it")
    ap.add_argument("--debug-log", action="store_true",
                    help="write <stem>.debug.json beside the deck, one entry "
                         "per command, machine-written")
    ap.add_argument("--assess", action="append", metavar="Cn=score:reason",
                    default=[],
                    help="a C1-C8 self-score, repeatable: "
                         "--assess C1=4:\"storyline declared and mirrored\". "
                         "Folded into this run instead of eight separate "
                         "`debug_log assess` calls. 5 is refused — never "
                         "self-score 5 before a reader")
    ap.add_argument("--keep-log", action="store_true",
                    help="do not restart the debug log. One run of this driver "
                         "is one build's record, so it restarts by default; "
                         "pass this to keep an earlier run's log and let init "
                         "refuse")
    ap.add_argument("--facts", type=pathlib.Path, metavar="CONTRACT.md",
                    help="the fact contract this build was made from. Asks the "
                         "question no other check asks — whether the rebuild "
                         "still carries the facts it was built from. A measured "
                         "rebuild silently lost eleven")
    ap.add_argument("--platform", default="claude-code",
                    help="registry id for the debug log")
    a = ap.parse_args(argv)

    if a.fast and a.deliver:
        sys.exit("--fast and --deliver are the loop and the delivery round; "
                 "pick one")
    # The language refusal lives in `new_deck.py`, which is the command that
    # writes the declaration; repeating it here would be a second copy of a
    # rule with one owner.

    a.deck.parent.mkdir(parents=True, exist_ok=True)
    log_path = None
    if a.debug_log:
        # The same rule as `debug_log init`, asked of it rather than retyped:
        # the two computed the path independently and would diverge the moment
        # only one was fixed.
        log_path = a.deck.parent / (debug_log.log_stem(a.deck) + ".debug.json")
        # RESTART BY DEFAULT. `debug_log init` refuses an existing log so one
        # build's record is not silently overwritten — and **one run of this
        # driver IS one build**, which is the invariant that guard protects.
        # Without the passthrough, every iteration after the first died here
        # before a single stage ran, and the author moved the log aside by
        # hand: nine times on one measured build.
        argv_init = ["init", str(a.deck), "--platform", a.platform]
        if not a.keep_log:
            argv_init.append("--restart")
        debug_log.main(argv_init)
        if not log_path.is_file():
            sys.exit(f"debug_log init wrote no log at {log_path}")
    stage = Stage(log_path)

    # A9 · THE BEAT'S OWN HALF, before anything is built. `check_outline`
    # without `--against` decides the cheap half — topic-label titles, group
    # size, an undeclared section — and prints the titles to be read as one
    # paragraph. SKILL.md asks for it before building; only the after half was
    # ever in this driver, so the before half cost a separate command.
    if a.outline:
        stage.run("outline", [sys.executable,
                              str(ROOT / "scripts/check/check_outline.py"),
                              str(a.outline)])

    if not a.keep_scaffold:
        argv_nd = [sys.executable, str(ROOT / "scripts/ops/new_deck.py"),
                   "--genre", a.genre, "--geometry", a.geometry,
                   "--lang", a.lang]
        if a.lang_asked:
            argv_nd += ["--lang-asked", a.lang_asked]
        if a.storyline:
            argv_nd += ["--storyline", a.storyline]
        if a.entry_path:
            argv_nd += ["--entry-path", a.entry_path]
        if a.outline:
            argv_nd += ["--outline", str(a.outline)]
        if a.pages:
            argv_nd += ["--pages", str(a.pages)]
        if a.parts:
            argv_nd += ["--parts", a.parts]
        argv_nd += ["--out", str(a.deck)]
        if stage.run("scaffold", argv_nd):
            return 1

    if a.script:
        if stage.run("fill", [sys.executable, str(a.script), str(a.deck)]):
            print("   the fill script failed, so the checks below would be "
                  "measuring the scaffold. Stopping.", file=sys.stderr)
            return 1

    # Always, and cheap: a shape referenced and not embedded is a D19 failure,
    # and the sprite goes stale the moment the fill script swaps a shape in.
    stage.run("embed shapes",
              [sys.executable, str(ROOT / "scripts/build/embed_shapes.py"),
               str(a.deck)])

    argv_cd = [sys.executable, str(ROOT / "scripts/ops/check_deliverable.py"),
               str(a.deck)]
    if a.terms:
        argv_cd += ["--terms", a.terms]
    if a.fast:
        argv_cd.append("--fast")
    if a.deliver:
        argv_cd.append("--sheet")
    # THE PREVIOUS ROUND'S READING, kept and passed back in. A build that is
    # already green has no signal telling it so, and one measured session ran
    # SIX more rounds after its last failure — with the debug log recording
    # nothing on a green round, so neither the author nor a reader could say
    # whether those rounds improved anything. `--against` answers that: a round
    # that moved no measured number says so in one line.
    prev = a.deck.parent / f".{a.deck.stem}.layout.json"

    # ALWAYS, not only in debug mode: the next round's comparison needs this
    # round's reading, and a driver that only kept it when someone asked for a
    # log would make the comparison a debug-mode feature.
    reports_dir = a.deck.parent / f".{a.deck.stem}.reports"
    argv_cd += ["--reports-dir", str(reports_dir)]
    if prev.is_file():
        argv_cd += ["--against", str(prev)]
    rc = stage.run("check", argv_cd)

    # Keep this round's layout reading as the next round's baseline, so the
    # comparison needs no ceremony from the caller.
    src = (reports_dir or (a.deck.parent / f".{a.deck.stem}.reports")) / "layout.json"
    if src.is_file():
        prev.write_bytes(src.read_bytes())

    if a.facts:
        # Also outside check_deliverable, and the only check that compares the
        # document to what it was built FROM.
        rc = stage.run("facts", [sys.executable,
                                 str(ROOT / "scripts/check/check_facts.py"),
                                 str(a.facts), str(a.deck)]) or rc

    if a.deliver:
        # THE DELIVERY ROUND'S OWN COMMANDS, folded in. `export_pdf` had no
        # caller anywhere in the package, and the scoring sheet is generated
        # from the rubric — both were separate round trips at the end of every
        # build, after the driver had already returned.
        stage.run("export pdf", [sys.executable,
                                 str(ROOT / "scripts/ops/export_pdf.py"),
                                 str(a.deck)])
        sheet = a.deck.parent / f"{a.deck.stem}.scoring-sheet.md"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/ops/scoring_sheet.py"),
             str(a.deck)], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            sheet.write_text(proc.stdout, encoding="utf-8")
            print(f"   scoring sheet: {sheet}")

    if a.outline:
        # The question no other check asks: is this still the deck that was
        # planned? It is NOT inside check_deliverable, so it is a real stage
        # rather than a duplicate.
        rc = stage.run("outline mirror",
                       [sys.executable, str(ROOT / "scripts/check/check_outline.py"),
                        str(a.outline), "--against", str(a.deck)]) or rc

    if log_path is not None:
        # THE CONTRACT'S OTHER HALF, honoured from the reports the check step
        # already produced. `attach` asked for documents this pipeline used to
        # throw away, so keeping the contract cost six commands and a second
        # browser render.
        for kind in ("design", "prose", "layout"):
            f = reports_dir / f"{kind}.json"
            if f.is_file():
                try:
                    debug_log.attach_doc(log_path, kind,
                                         json.loads(f.read_text(encoding="utf-8")))
                except (OSError, ValueError) as exc:
                    print(f"   could not attach {kind}: {exc}", file=sys.stderr)
    shutil.rmtree(reports_dir, ignore_errors=True)

    if log_path is not None and a.assess:
        for spec in a.assess:
            dim, _, rest = spec.partition("=")
            score, _, reason = rest.partition(":")
            rc_a = debug_log.main(["assess", str(log_path), "--dim", dim.strip(),
                                   "--score", score.strip(),
                                   "--reason", reason.strip() or "(no reason given)"])
            if rc_a:
                rc = rc or rc_a

    if log_path is not None:
        print(f"\n   debug log: {log_path}")
        problems = debug_log.validate(debug_log._load(log_path))
        for p in problems:
            print(f"   log FAIL  {p}")
        rc = rc or (1 if problems else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
