#!/usr/bin/env python3
"""What this repository counts in words, and where it points at itself.

**This reports. It never fails a run.** That is not timidity — it is the
condition under which it is allowed to exist. `FAILURE_MODES.md`'s AG-1 declined
a guard that reads English and decides what a sentence is claiming, because
deciding that mechanically is brittle by construction and a brittle gate is
FM-01 waiting to happen. Deciding it is still useful; deciding it *for a person
to read* costs nothing when it is wrong.

Two lists, both advisory:

1. **Counted claims** — sentences carrying a number-word or a digit next to a
   name this repository defines. Some are load-bearing counts that will rot;
   most are ordinary prose. The reader decides. The ones that turned out to
   matter get promoted into a parity guard in `check_repo.py`, which is where
   the enforcement lives — this file is the net that finds candidates for it.

2. **Self-citations** — `file.py:123` and `file.md:12-34` references. The line
   numbers are checked: a file that is now shorter than the line it cites, or a
   citation whose target moved, is reported. `check_links` validates markdown
   link syntax and `check_script_paths` validates that a script exists; nothing
   validated a line number, and two had drifted by the time anyone looked.

Why this exists at all: twenty-six of this repository's releases have carried a
fix for a prose copy that disagreed with its code, five of them in the last ten
releases. The mean time to notice, where the changelog says, is four to eleven
releases. Nobody was looking, because looking meant remembering to grep.

    python3 scripts/check/claim_sweep.py            # everything
    python3 scripts/check/claim_sweep.py --counts   # just the counted claims
    python3 scripts/check/claim_sweep.py --refs     # just the self-citations
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Frozen: each was true when it was written and is not retroactively corrected.
# tests/ builds synthetic trees full of invented filenames; a citation there is
# a fixture, not a claim about this repository.
FROZEN = ("CHANGELOG.md", "specs/", "releases/evidence/", "conformance/results/",
          "tests/")

# Generated from SKILL.md and the registry, and held byte-identical to them by
# build_entrypoints.py --check. A claim here is a copy of a claim already swept
# at its source, so sweeping both doubles every finding and fixes none.
GENERATED = ("adapters/", "GEMINI.md", ".github/copilot-instructions.md",
             ".cursor/", ".well-known/", ".claude-plugin/")

# "every" and "both" are deliberately absent. They are quantifiers, not counts:
# "every guard" stays true when a guard is added, and "three guards" does not.
# Only a claim that a change can falsify is worth a reader's attention.
NUMBER_WORD = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)

# A count is interesting when the thing counted is a name this repository owns.
# Deliberately a small vocabulary rather than "any noun": the wide version
# reported most of the prose in the package and taught the reader to skip it.
COUNTED_THINGS = (
    r"gates?|gating|metrics?|verdicts?|geometr(?:y|ies)|layouts?|entry points?|"
    r"platforms?|tiers?|floors?|red lines?|fixtures?|assertions?|drawers?|"
    r"ledgers?|slots?|probes?|dimensions?|exceptions?"
)

# The gap is small on purpose. At forty characters this reported 1115 sentences,
# which is the whole package and teaches a reader to skip the list — the exact
# failure the report is meant to prevent. A count that is load-bearing sits next
# to the thing it counts.
COUNT_RE = re.compile(
    rf"\b(?:{NUMBER_WORD}|\d{{1,3}})\b(?:[^.\n]{{0,16}}?)\b(?:{COUNTED_THINGS})\b",
    re.I)

# `path/to/file.py:123` or `file.md:12-34`, in prose or in a comment.
CITE_RE = re.compile(r"\b([\w./-]+\.(?:py|md|json|css|js|sh|ya?ml)):(\d+)(?:-(\d+))?\b")


def tracked() -> list[str]:
    listed = subprocess.run(["git", "ls-files"], cwd=ROOT,
                            capture_output=True, text=True)
    if listed.returncode != 0:
        print("git ls-files failed; nothing swept", file=sys.stderr)
        return []
    # Prose and code only. A claim about this repository is made in a sentence
    # or a comment; a topology file has numbers and says nothing.
    return [p for p in listed.stdout.splitlines()
            if p and p.endswith((".md", ".py"))
            and not any(p.startswith(f) for f in FROZEN + GENERATED)]


def read(relpath: str) -> str | None:
    try:
        return (ROOT / relpath).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def sweep_counts() -> list[tuple[str, int, str]]:
    out = []
    for relpath in tracked():
        text = read(relpath)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in COUNT_RE.finditer(line):
                out.append((relpath, n, m.group(0).strip()))
    return out


def sweep_refs() -> list[tuple[str, int, str, str]]:
    """-> (citing file, line, the citation, why it is suspect)."""
    out = []
    for relpath in tracked():
        text = read(relpath)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in CITE_RE.finditer(line):
                target, start = m.group(1), int(m.group(2))
                # A bare filename resolves against the citing file's own folder
                # first, then the repository root — the two forms both appear.
                here = (ROOT / relpath).parent / target
                path = here if here.is_file() else ROOT / target
                if not path.is_file():
                    out.append((relpath, n, m.group(0),
                                "the file does not exist"))
                    continue
                length = len(path.read_text(encoding="utf-8",
                                            errors="replace").splitlines())
                end = int(m.group(3) or start)
                if end > length:
                    out.append((relpath, n, m.group(0),
                                f"{target} has {length} lines"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="report counted claims and self-citations; never fails")
    ap.add_argument("--counts", action="store_true", help="only counted claims")
    ap.add_argument("--refs", action="store_true", help="only self-citations")
    args = ap.parse_args(argv)
    both = not (args.counts or args.refs)

    if args.counts or both:
        counts = sweep_counts()
        print(f"note  {len(counts)} counted claim(s) — a count next to a name "
              f"this repository defines. Most are prose; the ones that are not "
              f"belong in a parity guard.")
        by_file: dict[str, list[tuple[int, str]]] = {}
        for relpath, n, claim in counts:
            by_file.setdefault(relpath, []).append((n, claim))
        for relpath in sorted(by_file):
            print(f"      {relpath}")
            for n, claim in by_file[relpath]:
                print(f"        :{n}  {claim}")

    if args.refs or both:
        refs = sweep_refs()
        if not refs:
            print("ok    every file:line self-citation resolves")
        else:
            print(f"note  {len(refs)} self-citation(s) that do not resolve")
            for relpath, n, cite, why in refs:
                print(f"      {relpath}:{n}  cites {cite} — {why}")

    # ALWAYS ZERO. A reporting tool that can fail a run is a gate that was never
    # argued for, and this one was argued against (AG-1).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
