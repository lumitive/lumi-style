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

2. **Self-citations** — a script or document cited with the line it is on.
   The line
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
    python3 scripts/check/claim_sweep.py --changed  # counted claims in the files you touched
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
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

import repo_files  # noqa: E402 — the one way to ask git

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

# A tracked file cited with its line, in prose or in a comment. The examples
# this comment would otherwise carry are left out on purpose: written down,
# they are citations, and this tool would report its own illustrations.
CITE_RE = re.compile(r"\b([\w./-]+\.(?:py|md|json|css|js|sh|ya?ml)):(\d+)(?:-(\d+))?\b")


def tracked() -> list[str]:
    listed, problem = repo_files.tracked_files(root=ROOT, what="claim sweep")
    if problem:
        print(f"{problem}; nothing swept", file=sys.stderr)
        return []
    # Prose and code only. A claim about this repository is made in a sentence
    # or a comment; a topology file has numbers and says nothing.
    return [p for p in listed
            if p and p.endswith((".md", ".py"))
            and not any(p.startswith(f) for f in FROZEN + GENERATED)]


def changed_since(ref: str) -> set[str] | None:
    """-> the files touched since `ref` (committed, staged and unstaged) plus
    untracked files, or None when git cannot answer.

    Convention 12 says "read the claims touching what you changed", and the
    whole sweep prints two hundred and eighty lines; a reader who has to
    find their own twenty in it reads none. `--changed` is the filter that
    convention named and nobody had built — the P1 item the refactor design
    listed as "claim_sweep extension" and the audit found untouched.
    """
    out: set[str] = set()
    for argv in (["git", "diff", "--name-only", ref],
                 ["git", "diff", "--name-only", "--cached"],
                 ["git", "ls-files", "--others", "--exclude-standard"]):
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        if p.returncode != 0:
            return None
        out.update(line for line in p.stdout.splitlines() if line)
    return out


def read(relpath: str) -> str | None:
    try:
        return (ROOT / relpath).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def sweep_counts(only: set[str] | None = None) -> list[tuple[str, int, str]]:
    out = []
    for relpath in tracked():
        if only is not None and relpath not in only:
            continue
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
    ap.add_argument("--changed", nargs="?", const="HEAD", metavar="REF",
                    help="only the counted claims in files changed since REF "
                         "(default HEAD; staged and untracked files count). "
                         "Convention 12's 'the ones touching what you changed', "
                         "as a flag.")
    args = ap.parse_args(argv)
    both = not (args.counts or args.refs)

    if args.counts or both:
        only = None
        if args.changed is not None:
            only = changed_since(args.changed)
            if only is None:
                print("note  --changed: git could not list the changed files; "
                      "sweeping everything instead")
        counts = sweep_counts(only)
        scope = (f" in the {len(only)} file(s) changed since {args.changed}"
                 if only is not None else "")
        print(f"note  {len(counts)} counted claim(s){scope} — a count next to a name "
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
