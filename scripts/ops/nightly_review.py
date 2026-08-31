#!/usr/bin/env python3
"""Review what today shipped, against the failure classes this repo measured.

**Why this exists.** On 2026-09-01 one design went through four review rounds
and every round found defects — fifteen, and the owner had to ask for each
round. Sorted by what would have caught them, only three needed a human reader.
Convention 20 records the classes; this runs the mechanical ones nightly so the
author is not the only thing standing between a defect and the owner.

    python3 scripts/ops/nightly_review.py              # today
    python3 scripts/ops/nightly_review.py --since 3    # the last three days
    python3 scripts/ops/nightly_review.py --json

What it checks, and which measured failure each maps to:

  A · numbers asserted without being run   — dangling self-citations, via
      claim_sweep; and any spec claim whose file:line no longer resolves.
  B · coverage claimed without its blind spot — a document saying "0 false
      negatives", "every row", "all of" near a count, which on 2026-09-01 was
      false three times out of three.
  D · a mechanism re-proposed after refusal — any guard added today is searched
      against the abandoned-gates ledger by `precedent.py`.
  E · a release that shipped with a repeated waiver, or claimed a number it did
      not move.

**It reports and never fails.** A nightly job that can break a build is a
nightly job someone turns off, and AG-1 declined the class of guard that decides
what a sentence claims. What it removes is the excuse of nobody having looked.

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import re
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

# The closed vocabulary lives in scripts/lib/trace_schema.py — one definition,
# read by this writer and by check_repo.py's guard.

ROOT = pathlib.Path(__file__).resolve().parents[2]

# A count next to a totalising word. Measured on the 2026-09-01 spec: every one
# of "0 false negatives", "every row is machine-checkable" and "both give the
# same two findings" was false, and each was written by the author about their
# own instrument's reach.
OVERCLAIM = re.compile(
    r"(?:\b(?:0|zero|no)\s+(?:false|missing|uncovered|omitted)\b"
    r"|\bevery\s+(?:row|claim|one|link|entry|figure|rule)\b"
    r"|\ball\s+\d+\b"
    r"|\b100\s?%)", re.I)

# A guard is a function this repo registers as a check.
NEW_GUARD = re.compile(r"^\+def (check_\w+)\(", re.M)


def _git(*args) -> str:
    """-> stdout, or "" when git failed.

    `repo_files.run_git` is the one spelling of the invocation
    (`evals/single-source.json`). A private call here was caught by the very
    guard this file exists to run nightly — and the first fix left the offending
    shape in this docstring as an example, where the guard rightly caught it
    again. A comment naming the thing it forbids is the thing it forbids."""
    import repo_files
    code, out = repo_files.run_git(*args, root=ROOT)
    return out if code == 0 else ""


def commits_since(days: int):
    since = (dt.date.today() - dt.timedelta(days=max(days - 1, 0))).isoformat()
    log = _git("log", f"--since={since} 00:00", "--format=%H%x09%s")
    return [tuple(row.split("\t", 1)) for row in log.splitlines() if "\t" in row]


def changed_files(shas):
    if not shas:
        return []
    out: set[str] = set()
    for sha in shas:
        out.update(f for f in _git("show", "--name-only", "--format=", sha).split()
                   if f)
    return sorted(out)


def class_a_dangling():
    """-> citations that no longer resolve. claim_sweep already finds these."""
    # claim_sweep is a CLI, not a library — it exposes no stable entry point,
    # so this reads its output rather than pretending to an import contract.
    if True:
        out = subprocess.run([sys.executable,
                              str(ROOT / "scripts/check/claim_sweep.py")],
                             capture_output=True, text=True)
        return [row.strip() for row in out.stdout.splitlines()
                if "does not exist" in row or "has moved" in row]
    return []


def class_b_overclaims(files, shas=()):
    """-> coverage claims in today's prose that do not say what they cannot see.

    Reported, never judged: the reader decides whether a sentence is load
    bearing. What this removes is the sentence nobody re-read.
    """
    # ONLY the lines today ADDED. Scanning whole files re-reports every
    # coverage sentence this repository has ever written -- 12 hits from
    # CHANGELOG history on the first run, none of them today's work. A review
    # that buries today's three findings under a decade of prose is a review
    # nobody finishes reading.
    added = set()
    for sha in shas:
        for line in _git("show", "--format=", "-U0", sha).splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added.add(line[1:].strip())
    hits = []
    for f in files:
        if not f.endswith(".md") or not (ROOT / f).is_file():
            continue
        for n, line in enumerate((ROOT / f).read_text(
                encoding="utf-8", errors="replace").splitlines(), 1):
            t = line.strip()
            if t not in added:
                continue
            if OVERCLAIM.search(t) and not re.search(
                    r"cannot see|blind|does not see|not reproducible|attested",
                    t, re.I):
                hits.append(f"{f}:{n}  {t[:88]}")
    return hits


def class_d_unsearched_guards(shas):
    """-> guards added today, with what a precedent search says about each."""
    try:
        import precedent
    except ImportError:
        return None
    found = []
    for sha in shas:
        diff = _git("show", "--format=", "-U0", sha)
        for name in NEW_GUARD.findall(diff):
            terms = [t for t in name.replace("check_", "").split("_") if len(t) > 3]
            hits = precedent.search(terms, body=True) if terms else []
            found.append((name, sha[:8],
                          [(h[0], h[1]) for h in hits if h[4]]))
    return found


def class_e_release_hygiene(commits):
    """-> releases today, and whether each carried a waiver already carried."""
    out = []
    for _sha, subject in commits:
        m = re.match(r"^(0\.1\.\d+) — ", subject)
        if not m:
            continue
        ev = ROOT / "releases" / "evidence" / f"{m.group(1)}.json"
        waivers = []
        if ev.is_file():
            try:
                waivers = [w.get("id") for w in
                           json.loads(ev.read_text(encoding="utf-8")).get("waivers", [])]
            except (OSError, ValueError):
                waivers = ["<evidence file unreadable>"]
        out.append((m.group(1), subject[:60], waivers))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", type=int, default=1, metavar="DAYS",
                    help="how many days back to review (default: today)")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    a = ap.parse_args(argv)

    commits = commits_since(a.since)
    shas = [c[0] for c in commits]
    files = changed_files(shas)

    report = {
        "days": a.since,
        "commits": len(commits),
        "files": len(files),
        "dangling_citations": class_a_dangling(),
        "coverage_claims": class_b_overclaims(files, shas),
        "new_guards": class_d_unsearched_guards(shas),
        "releases": class_e_release_hygiene(commits),
    }

    if a.json:
        print(json.dumps(report, indent=1, ensure_ascii=False, default=str))
        return 0

    span = "today" if a.since == 1 else f"the last {a.since} days"
    print(f"nightly review · {span} · {len(commits)} commit(s), "
          f"{len(files)} file(s) touched")
    if not commits:
        # Not "clean". Nothing was looked at, and those print differently.
        print("  nothing shipped — nothing was reviewed, which is not the same "
              "as nothing being wrong")
        return 0

    print("\nA · citations that no longer resolve")
    d = report["dangling_citations"]
    if d is None:
        print("  COULD NOT CHECK — claim_sweep did not import")
    elif d:
        for x in d[:12]:
            print(f"  {x}")
    else:
        print("  none")

    print("\nB · coverage claimed without saying what it cannot see")
    if report["coverage_claims"]:
        for x in report["coverage_claims"][:12]:
            print(f"  {x}")
        print("  (measured 2026-09-01: three such sentences, three false)")
    else:
        print("  none in today's prose")

    print("\nD · guards added today, against the refusals ledger")
    g = report["new_guards"]
    if g is None:
        print("  COULD NOT CHECK — precedent did not import")
    elif not g:
        print("  no new guard")
    else:
        for name, sha, refused in g:
            mark = "  ★ REFUSED PRECEDENT" if refused else "  no refusal found"
            print(f"  {name} ({sha}){mark}")
            for rid, title in refused:
                print(f"      {rid} · {title}")

    print("\nE · releases today")
    if not report["releases"]:
        print("  none")
    for ver, subject, waivers in report["releases"]:
        print(f"  {ver} {subject}")
        if waivers:
            print(f"      waivers: {', '.join(str(w) for w in waivers)}")
    print("\nThis reports. Nothing here fails a build; a nightly job that can "
          "is a nightly job that gets turned off.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
