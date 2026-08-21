#!/usr/bin/env python3
"""Stamp, regenerate, gather evidence, verify, and commit — in that order.

Why this exists, stated plainly: the release flow was a checklist of six to
eight commands executed by hand, and chaining them in a shell put a commit
behind a pipe:

    python3 scripts/preflight.py 2>&1 | tail -2 && git commit ...

`&&` reads the exit status of the LAST stage of a pipeline, and `tail` always
succeeds. So preflight failed, the `&&` proceeded, and a red release was
committed. Twice, in one session, after the lesson had already been written
down once in a previous one.

A rule that has been recorded and then broken is not a rule that needs
recording more firmly. It needs a tool that holds it, which is the same
reasoning that produced `check_evidence.py`: that script executes the command
and writes the result itself because a human typing "pass" is not evidence.

So: **this refuses to commit when preflight fails**, and there is no flag to
make it. It also never pipes anything — every step's exit code is read from the
process that produced it.

Usage
  release.py --version 0.1.474 --spec specs/....md
  release.py --version 0.1.474 --spec specs/....md --dry-run
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())

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

import shipping  # noqa: E402 — after the bootstrap
from check_repo import ENTRY_STAMP, TOKEN_STAMPS  # noqa: E402 — after the bootstrap


# WHERE THE STAMPS ARE IS NOT DECLARED HERE. It is read out of check_repo's
# ENTRY_STAMP and TOKEN_STAMPS, which are the guards' own authority on the same
# fact. The first version of this file carried its own eight-row table, and the
# review that found it put the point exactly: fixing a drift problem by adding a
# third copy of the thing that drifts is the defect arriving through the door
# marked "release tooling". A test asserts this file declares no stamp table.
#
# The replacement is a literal swap of the old version string for the new one,
# first occurrence only — the patterns in ENTRY_STAMP are regexes and cannot be
# inverted into a replacement. The header stamp is the first occurrence in every
# stamped file; historical notes inside tokens/ name OLDER versions and are not
# touched. check_versions and check_version_citations verify the result, which
# is what they exist for, so a miss fails the release rather than shipping.
def stamped_files() -> list[str]:
    return sorted(set(ENTRY_STAMP) | {name for name, _pattern in TOKEN_STAMPS})


GENERATORS = [
    ["python3", "scripts/build/build_entrypoints.py"],
    ["python3", "scripts/build/build_fixtures.py"],
    ["python3", "scripts/build/build_eval_inventory.py"],
    ["python3", "scripts/build/recolor_shapes.py"],
]


def run(cmd, *, capture=True):
    """-> CompletedProcess. Never through a shell, never through a pipe: the
    exit code has to come from the process that produced it."""
    return subprocess.run(cmd, cwd=ROOT, capture_output=capture, text=True)


def current_version() -> str:
    m = re.search(r'version: "([\d.]+)"',
                  (ROOT / "SKILL.md").read_text(encoding="utf-8"))
    if not m:
        sys.exit("SKILL.md carries no version stamp")
    return m.group(1)


def newest_changelog_heading() -> tuple[str, str]:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## (\d+\.\d+\.\d+) — (.+)$", text, re.M)
    if not m:
        sys.exit("CHANGELOG.md has no versioned heading")
    return m.group(1), m.group(2)


def stamp(old: str, new: str, dry: bool) -> list[str]:
    touched = []
    for name in stamped_files():
        path = ROOT / name
        if not path.exists():
            sys.exit(f"{name} is declared as a stamp position and does not exist")
        text = path.read_text(encoding="utf-8")
        if old not in text:
            sys.exit(f"{name}: no occurrence of {old!r}. Either it was already "
                     f"bumped or the stamp moved; the version guards say which, "
                     f"and this refuses to guess.")
        if not dry:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
        touched.append(name)
    return touched


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", required=True, help="the version being released")
    ap.add_argument("--spec", help="specs/*.md this release implements")
    ap.add_argument("--dry-run", action="store_true",
                    help="do everything except write, and stop before committing")
    a = ap.parse_args()

    old, new = current_version(), a.version
    heading_version, heading_summary = newest_changelog_heading()
    if heading_version != new:
        sys.exit(f"CHANGELOG's newest heading is {heading_version}, not {new}. "
                 f"Write the entry first: the commit subject is taken FROM it, "
                 f"so that the two cannot disagree.")

    print(f"release {old} -> {new}")
    print(f"  subject will be: {new} — {heading_summary[:60]}...")

    print("\n1. stamps")
    for name in stamp(old, new, a.dry_run):
        print(f"   {'would stamp' if a.dry_run else 'stamped'} {name}")

    print("\n2. generated artefacts")
    for cmd in GENERATORS:
        if a.dry_run:
            print(f"   would run {' '.join(cmd)}")
            continue
        proc = run(cmd)
        if proc.returncode != 0:
            sys.exit(f"   {' '.join(cmd)} failed:\n{proc.stdout}{proc.stderr}")
        print(f"   ran {' '.join(cmd)}")

    print("\n3. evidence")
    if not a.dry_run:
        # --init rewrites the file from the diff, which DESTROYS any waiver
        # written by hand since the last run. Found by running this twice: the
        # first pass could not record an obligation, a waiver was written for
        # it, and the second pass silently removed it and failed on the same
        # obligation again. A waiver names something unconfirmed; losing it
        # loses the only record that anyone looked.
        path = ROOT / "releases" / "evidence" / f"{new}.json"
        kept_waivers = []
        # The SPEC LINE is hand-written the same way and was not carried, which
        # is this comment's own lesson one field to the left: a release that
        # waived the spec requirement by hand had the waiver silently removed
        # by the next --init and failed on the same rule again. Both fields are
        # somebody's sentence about why; neither survives a rewrite unless it
        # is carried.
        kept_spec = ""
        if path.exists():
            prior = json.loads(path.read_text(encoding="utf-8"))
            kept_waivers = prior.get("waivers", [])
            kept_spec = prior.get("spec", "")
        proc = run(["python3", "scripts/check/check_evidence.py", "--init"])
        if proc.returncode != 0:
            sys.exit(f"   --init failed:\n{proc.stdout}{proc.stderr}")
        doc = json.loads(path.read_text(encoding="utf-8"))
        if a.spec:
            doc["spec"] = a.spec
        elif kept_spec and not doc.get("spec"):
            doc["spec"] = kept_spec
            print("   carried the spec line across --init")
        if kept_waivers and not doc.get("waivers"):
            doc["waivers"] = kept_waivers
            print(f"   carried {len(kept_waivers)} waiver(s) across --init")
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        for obligation in doc.get("obligations", []):
            done = {c.get("id") for c in doc.get("checks", [])}
            waived = {w.get("id") for w in doc.get("waivers", [])}
            if obligation in done or obligation in waived:
                continue
            proc = run(["python3", "scripts/check/check_evidence.py",
                        "record", "--id", obligation])
            print(f"   {'recorded' if proc.returncode == 0 else 'COULD NOT RECORD'} "
                  f"{obligation}")
            if proc.returncode != 0:
                print(f"     {proc.stdout.strip()[:200]}")
                print("     Record it by hand or write a waiver naming what is "
                      "unconfirmed. This will not commit until it is closed.")

    print("\n4. preflight — exactly what CI runs")
    proc = run(["python3", "scripts/preflight.py"])
    tail = "\n".join((proc.stdout or "").strip().splitlines()[-3:])
    print("   " + tail.replace("\n", "\n   "))
    if proc.returncode != 0:
        print("\nNOT COMMITTING. preflight failed, and there is no flag here to "
              "override that:\nthe reason this script exists is that a hand-run "
              "pipeline swallowed a red preflight\nand committed anyway. Fix the "
              "failures and run this again.")
        sys.exit(1)

    # Convention 12 says to sweep restated claims before committing, and for a
    # long time the only thing holding that was the sentence saying so. It is
    # the defect class this repository has fixed twenty-six times, and a rule
    # written down and then not followed does not need writing more firmly — it
    # needs a tool that holds it. REPORTED, never gating: the sweep's own
    # contract is that it reports and never fails, and turning it into a gate
    # here would quietly overrule that.
    print("\n5. restated claims — the ones in the files this release touches")
    # `--changed HEAD`: the staged release diff, not the whole tree. The full
    # sweep printed 280 lines and its last two were what a reader saw.
    sweep = run(["python3", "scripts/check/claim_sweep.py", "--counts", "--changed", "HEAD"])
    body = (sweep.stdout or "").strip().splitlines()
    print("   " + "\n   ".join(body[:40]) + ("\n   …" if len(body) > 40 else ""))

    if a.dry_run:
        print("\n--dry-run: stopping before the commit.")
        return

    print("\n6. commit")
    run(["git", "add", "-A"], capture=False)
    subject = f"{new} — {heading_summary}"
    proc = run(["git", "commit", "-m", subject, "-m",
                "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"])
    if proc.returncode != 0:
        sys.exit(f"   git commit failed:\n{proc.stdout}{proc.stderr}")
    print(f"   committed: {subject[:80]}")

    # The last thing a release says is how much finished work has still not
    # left this machine. Forty releases once accumulated on an unpushed branch
    # while every local check stayed green, and nothing asked.
    print()
    shipping.report()


if __name__ == "__main__":
    main()
