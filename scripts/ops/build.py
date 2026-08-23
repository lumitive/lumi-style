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
import pathlib  # noqa: E402
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
    ap.add_argument("--pages", type=int)
    ap.add_argument("--parts")
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
    ap.add_argument("--platform", default="claude-code",
                    help="registry id for the debug log")
    a = ap.parse_args(argv)

    if a.fast and a.deliver:
        sys.exit("--fast and --deliver are the loop and the delivery round; "
                 "pick one")
    # There is no --lang here any more, and that is the point. A flag an agent
    # can type is a flag an agent will type: 0.1.587 had `--lang zh-Hans
    # --lang-asked` and a build ran both itself, signing M16's record on the
    # same command line as the language it was attesting to. Every build is
    # English; another language is `scripts/ops/localize.py`, over a finished
    # English deck.

    a.deck.parent.mkdir(parents=True, exist_ok=True)
    log_path = None
    if a.debug_log:
        log_path = a.deck.parent / (a.deck.name.split(".")[0] + ".debug.json")
        debug_log.main(["init", str(a.deck), "--platform", a.platform])
        if not log_path.is_file():
            sys.exit(f"debug_log init wrote no log at {log_path}")
    stage = Stage(log_path)

    if not a.keep_scaffold:
        argv_nd = [sys.executable, str(ROOT / "scripts/ops/new_deck.py"),
                   "--genre", a.genre, "--geometry", a.geometry]
        if a.storyline:
            argv_nd += ["--storyline", a.storyline]
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
    rc = stage.run("check", argv_cd)

    if a.outline:
        # The question no other check asks: is this still the deck that was
        # planned? It is NOT inside check_deliverable, so it is a real stage
        # rather than a duplicate.
        rc = stage.run("outline mirror",
                       [sys.executable, str(ROOT / "scripts/check/check_outline.py"),
                        str(a.outline), "--against", str(a.deck)]) or rc

    if log_path is not None:
        print(f"\n   debug log: {log_path}")
        problems = debug_log.validate(debug_log._load(log_path))
        for p in problems:
            print(f"   log FAIL  {p}")
        rc = rc or (1 if problems else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
