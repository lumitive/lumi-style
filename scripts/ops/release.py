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
import base64
import binascii
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

import preflight  # noqa: E402
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


# Commands that leave the tree in the state CI expects, run before verification.
# Two kinds, and only one of them can be listed here honestly.
#
# THE GENERATORS ARE DERIVED FROM ci.yml, never listed. This was a hand-written
# list of four while CI checked every generator in `scripts/build/`:
# `build_page_contracts.py` was missing, so a release that changed
# `evals/rule-coverage.json` regenerated three artefacts, left that one stale,
# and failed its own preflight. That happened three times
# before anybody read the list against the workflow — which is the same shape as
# every other hand-written subset this package has fixed, in the script whose
# whole purpose is that local green and CI green are the same claim.
# `--check` MEANS TWO THINGS in `scripts/build/`, and only one of them has a
# regeneration. Most of these scripts write a tracked artefact and `--check`
# asks whether it is current — dropping the flag makes it so. `embed_icons.py
# --check` asks whether the VENDORED LIBRARY is intact ("2007 icons, LICENSE
# present, 18 reserved bindings all resolve"); it produces no tracked artefact,
# the sprite is embedded per document by the consumer, and run bare it wants
# icon names. Listing it as an exception would be a name to maintain; the
# difference is real, so the code asks for it.
VALIDATORS_NOT_GENERATORS = frozenset({"scripts/build/embed_icons.py"})


def generators():
    """-> every `--check`ed generator, as the command that REGENERATES it.

    A workflow step names a build script with `--check`; dropping the flag is
    the command that makes it true. (Spelled without an example path: the
    `script paths` guard reads every `scripts/…` string in tracked text and
    requires it to resolve, and a placeholder that looks like a path is a
    dangling mention — it caught this line.) Read from `preflight.ci_commands`,
    the same parser that gives preflight its step list, so a generator added to
    CI tomorrow is regenerated by the next release without anyone editing this.

    This was a hand-written list of four while CI checked fourteen. The other
    ten passed only because their inputs rarely change, and the first one whose
    input started moving failed three releases in a row.
    """
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    out = []
    for cmd in preflight.ci_commands(text):
        parts = cmd.split()
        if (len(parts) >= 3 and parts[0] == "python3"
                and parts[1].startswith("scripts/build/")
                and "--check" in parts
                and parts[1] not in VALIDATORS_NOT_GENERATORS):
            out.append([p for p in parts if p != "--check"])
    return out


# Line numbers in the rule register are POINTERS, not assertions: editing a
# paragraph above a rule moves fifty of them without changing one rule.
# `--relocate` follows a quote to where it now is, and only ever when the quote
# appears exactly once — an ambiguous or vanished quote stays a finding for a
# person. Run here because the alternative is a human doing it, and the human
# did it three times in one afternoon.
REALIGNERS = [
    ["python3", "scripts/check/check_rule_coverage.py", "--relocate"],
]


# The published package advances only when `publish.sh --push` runs, and the
# development repository advances on every merge. Nothing joins them, so the
# projection falls behind silently — it did, between 0.1.580 and 0.1.581,
# and a person noticing was the only thing that caught it.
#
# REPORTED, never a gate. Being behind is a normal state: a maintainer may
# deliberately hold several releases before publishing. What is not normal is
# not knowing. This is `shipping.report()`'s argument, one repository over.
# THE API, not raw.githubusercontent. The raw host is a CDN and caches for
# minutes: measured immediately after publishing 0.1.582, the API returned
# 0.1.582 and raw still returned 0.1.581. A note that says "1 release behind"
# to someone who has just published is a note that trains its reader to ignore
# it. `gh` is already a hard dependency of this workflow (emergency_merge.sh),
# and `--jq` keeps the parsing on gh's side.
PUBLISHED_REPO = "lumitive/lumi-style-skill"


def published_version(timeout: int = 6) -> str | None:
    """-> the version stamp the published package carries, or None.

    Asks GitHub's API for one file, through `gh`. Not `urllib`: a Python.org
    install on macOS ships without a certificate bundle, so `urlopen` fails
    with CERTIFICATE_VERIFY_FAILED against a URL `curl` fetches with a 200.
    Not raw.githubusercontent either — see the constant above. Shelling out is
    this file's habit anyway: every other step reads an exit code from the
    process that produced it.

    ANY failure returns None and the caller says "could not ask". A release
    must not fail because an advisory note could not be written, and a note
    that lies about being current would be worse than none.
    """
    proc = run(["gh", "api", f"repos/{PUBLISHED_REPO}/contents/SKILL.md",
                "--jq", ".content"])
    if proc.returncode != 0:
        return None
    try:
        head = base64.b64decode(proc.stdout).decode("utf-8", "replace")[:4096]
    except (ValueError, binascii.Error):
        return None
    m = re.search(r'version: "([\d.]+)"', head)
    return m.group(1) if m else None


def report_published(now: str) -> None:
    """Say how far the published package is behind, and how to close it."""
    there = published_version()
    if there is None:
        print("note  could not ask the published package which version it "
              "carries (offline, or the remote moved). Publishing state "
              "unknown — `scripts/ops/publish.sh` is a dry run by default.")
        return
    if there == now:
        print(f"ok    the published package carries {there} — nothing to publish.")
        return
    gap = _releases_between(there, now)
    if gap is not None and gap < 0:
        # The published package is NEWER. Not arithmetic to report as a
        # negative: it means this checkout is behind its own remote, or
        # something published from elsewhere, and either is worth saying
        # plainly rather than dressing as a publishing gap.
        print(f"note  the published package carries {there}, which is NEWER "
              f"than this repository's {now}. Pull `main` before publishing — "
              f"something published from another checkout.")
        return
    count = f"{gap} release(s)" if gap is not None else "some releases"
    print(f"note  the published package carries {there}; this repository is now "
          f"at {now} — {count} ahead.\n"
          f"      Publish with `scripts/ops/publish.sh --push` (bare is a dry "
          f"run). It refuses without an out-of-bounds terms list.")


def _releases_between(older: str, newer: str) -> int | None:
    """-> how many release headings sit between two versions, or None.

    Counted from the CHANGELOG rather than from either git history: the
    projection's commits are rewritten, so their hashes cannot be compared to
    this repository's at all.
    """
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    versions = re.findall(r"^## (\d+\.\d+\.\d+) — ", text, re.M)
    if older not in versions or newer not in versions:
        return None
    return versions.index(older) - versions.index(newer)


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


# Files the owner authors and this script may not commit on her behalf. A path
# here is still checked by preflight like any other — it is excluded from the
# COMMIT, not from the verification.
OWNER_OWNED = (
    "specs/2026-08-21-brand-packs-design.md",
    "specs/2026-08-21-brand-packs-plan.md",
)


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
    for cmd in REALIGNERS + generators():
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
    # OWNER-OWNED PATHS ARE NEVER SWEPT INTO A RELEASE. `git add -A` takes
    # everything in the tree, including files the owner is editing and has said
    # not to touch. 0.1.547 committed 413 lines of her brand-packs spec that
    # way — it was untracked, it was hers, and nothing asked. Content unchanged,
    # but a release should not decide when someone else's work-in-progress
    # enters the history.
    #
    # A rule written down and then broken needs a tool that holds it (convention
    # 16, which is why this script exists at all), so the exclusion is code
    # rather than a note to remember at commit time.
    held = [rel for rel in OWNER_OWNED
            if run(["git", "status", "--porcelain", "--", rel]).stdout.strip()]
    run(["git", "add", "-A"], capture=False)
    for owned in held:
        run(["git", "reset", "-q", "HEAD", "--", owned], capture=False)
        print(f"   left alone: {owned} (owner-owned; not this release's to commit)")
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
    print()
    report_published(new)


if __name__ == "__main__":
    main()
