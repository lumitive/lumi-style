#!/usr/bin/env python3
"""The evidence gate: what CI cannot run must be EXECUTED and recorded,
never narrated.

    python3 scripts/check/check_evidence.py --init [<version>]   # write the skeleton
    python3 scripts/check/check_evidence.py record --id <obligation>
    python3 scripts/check/check_evidence.py --check [--warn]     # the CI step

WHY. Five of this package's checks need a browser or an operator; until
0.1.424 their results were sentences in release notes — claims, not evidence
(GAP-002). 0.1.415 reported "all gates green" on eight of seventeen. The lumi
project's SOP names the principle: a requirement is built only when its
declared check has been EXECUTED with linked evidence, and CI green proves
form, never the operator half.

THE SCHEMA HAS NO VERDICT FIELD, deliberately. `record` executes the
canonical command itself and machine-writes the exit code, output digest and
date. A human never types "pass"; an unexecuted claim has no field to live
in. Large artifacts (contact sheets, rasters) stay local and untracked — the
tracked file carries the command, exit code and digests, which is re-runnable
evidence: anyone can execute the same command and compare.

One evidence file per release at releases/evidence/<version>.json, REQUIRED
for every release (an empty-obligations file is still written — uniformity is
what makes absence detectable). Obligations are computed from the release
diff through TOUCH_MAP; version-stamp-only changes to the stamped files do
not count as touches (a stamp bump is not a layout change, and a gate that
nags on every release becomes a gate people waive on reflex).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
EVIDENCE_DIR = ROOT / "releases" / "evidence"

# How many releases the conformance history may trail head before a
# rule-surface release owes fresh multi-agent rows. A ceiling: calibrated to
# observed velocity (~30 releases in 6 days), i.e. roughly a twice-weekly
# run. Single hard threshold, no warn tier — a warn on a manual-cost gate is
# a gate nobody runs.
CONFORMANCE_STALE_AFTER = 15
CONFORMANCE_MIN_AGENTS = 2

# obligation id -> (canonical command, what it proves). Deterministic,
# fixture-targeted, executable by anyone with the named local dependencies.
OBLIGATIONS: dict[str, tuple[str, str]] = {
    "layout-fixtures": (
        "python3 scripts/check/inspect_layout.py --deliverable fixtures/deck-pass.en.html",
        "the ten decidable layout gates on the passing fixture, in a real browser",
    ),
    "globe-js": (
        "python3 scripts/check/check_globe.py",
        "the globe checks INCLUDING the browser half that CI cannot run",
    ),
    "conformance-freshness": (
        "python3 scripts/ops/run_conformance.py validate",
        "rule-surface releases keep the multi-agent scoreboard fresh "
        "(armed once conformance/history.json exists)",
    ),
}

# path prefix -> obligation ids it triggers.
TOUCH_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("tokens/", ("layout-fixtures", "conformance-freshness")),
    ("references/design-rules.md", ("layout-fixtures",)),
    ("scripts/check/inspect_layout.py", ("layout-fixtures",)),
    ("fixtures/", ("layout-fixtures",)),
    ("assets/geo/", ("globe-js",)),
    ("assets/globe/", ("globe-js",)),
    ("scripts/render/globe_svg.py", ("globe-js",)),
    ("scripts/lib/geo_frame.py", ("globe-js",)),
    ("scripts/lib/geo_projection.py", ("globe-js",)),
    ("scripts/build/embed_globe.py", ("globe-js",)),
    ("scripts/check/check_globe.py", ("globe-js",)),
    ("SKILL.md", ("conformance-freshness",)),
    ("references/", ("conformance-freshness",)),
    ("prompts/", ("conformance-freshness",)),
)

# Files whose every-release change is usually just the version stamp (or a
# regeneration of it). A change of <= the named line budget (added+deleted)
# does not count as a touch; anything larger does. The fixtures carry the
# stamp in several generated spots, so their budget is wider — measured at 6
# lines per fixture for a stamp-only regeneration; budget 8 leaves headroom
# for a stamp that gains a character and reflows.
STAMPED_PREFIXES: tuple[tuple[str, int], ...] = (
    ("SKILL.md", 2), ("AGENTS.md", 2), ("prompts/lumi-style-core.md", 2),
    ("tokens/lumi-theme.css", 2), ("tokens/lumi-layouts.css", 2),
    ("tokens/design-tokens.json", 2), ("conformance/CONFORMANCE.md", 2),
    ("fixtures/", 8),
)

# The overclaim phrases, checked ONLY in the newest CHANGELOG section and
# only when this release carries waivers or gap-cited failures. Deliberately
# a short fixed tuple — a general prose parser would be its own drift source.
OVERCLAIM = ("all gates green", "gates green", "all checks pass",
             "every gate", "fully verified")

SPEC_LINE_THRESHOLD = 150  # changed lines above which a spec citation is owed


def validate_maps() -> list[str]:
    """TOUCH_MAP file-entries and OBLIGATIONS commands must point at files
    that exist. A prefix pointing at nothing obliges nothing — silently —
    which is the ENTRY_STAMP lesson (a stamp position pointing at nothing
    checks nothing). Runs at the head of --check so a scripts/ move that
    forgets this file goes red instead of quiet."""
    errors = []
    for prefix, _obs in TOUCH_MAP:
        if prefix.endswith((".py", ".md", ".sh")) and not (ROOT / prefix).is_file():
            errors.append(f"TOUCH_MAP names {prefix!r}, which does not exist "
                          f"— that entry can never fire")
    for ob, (command, _why) in OBLIGATIONS.items():
        for token in command.split():
            if token.startswith("scripts/") and not (ROOT / token).is_file():
                errors.append(f"OBLIGATIONS[{ob!r}] runs {token!r}, which "
                              f"does not exist — recording it would fail")
    return errors


def releases_in_changelog() -> list[str]:
    return re.findall(r"^##\s+(\d+\.\d+\.\d+)",
                      (ROOT / "CHANGELOG.md").read_text("utf-8"), re.M)


def conformance_fresh() -> bool | None:
    """None while unarmed (no history file); else whether the multi-agent
    scoreboard is recent enough. Fresh = at least CONFORMANCE_MIN_AGENTS
    distinct agents have rows within CONFORMANCE_STALE_AFTER releases of
    head, each covering all three tasks. The gate binds on the RECENCY of
    measurement, never on passing — both scored agents currently fail
    T1-deck (GAP-001), and a pass-gate would block every release forever
    while inviting exactly the overclaim this gate exists to kill.
    """
    hist = ROOT / "conformance" / "history.json"
    if not hist.exists():
        return None
    try:
        rows = json.loads(hist.read_text("utf-8"))
    except json.JSONDecodeError:
        # Fail closed and named: a corrupt history reads as stale, which
        # obliges fresh measurement rather than quietly un-arming the gate.
        # (run_conformance.py validate fails CI on the same corruption.)
        print("note  conformance/history.json does not parse; treating the "
              "board as stale")
        return False
    recent = set(releases_in_changelog()[:CONFORMANCE_STALE_AFTER + 1])
    agents = {r.get("agent") for r in rows
              if r.get("skill_version") in recent and len(r.get("tasks", {})) >= 3}
    return len(agents) >= CONFORMANCE_MIN_AGENTS


def newest_section() -> str:
    text = (ROOT / "CHANGELOG.md").read_text("utf-8")
    m = re.search(r"^##\s+\d+\.\d+\.\d+\b.*?(?=^##\s+\d+\.\d+\.\d+\b|\Z)",
                  text, re.M | re.S)
    return m.group(0) if m else ""


def git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def find_release_commit(version: str) -> str | None:
    """The newest commit whose subject starts with `<version> — `. Errors
    beat guesses: None when no commit matches (pre-0.1.423 history has
    stragglers, which is why the commit-convention guard now exists)."""
    rc, out = git("log", "--format=%H %s")
    if rc != 0:
        return None
    for line in out.splitlines():
        sha, _, subject = line.partition(" ")
        if subject.startswith(f"{version} — "):
            return sha
    return None


def effective_touches(base: str) -> list[str] | None:
    """Changed paths since `base` (committed and working tree), with
    stamp-only changes to the stamped files filtered out. None when git
    cannot answer (shallow clone without the base) — the caller degrades
    LOUDLY, never silently."""
    rc, numstat = git("diff", "--numstat", base)
    if rc != 0:
        return None
    touched = []
    presumed_stamps: list[str] = []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        adds, dels, path = parts
        lines = (0 if adds == "-" else int(adds)) + (0 if dels == "-" else int(dels))
        budget = next((n for p, n in STAMPED_PREFIXES if path.startswith(p)), 0)
        if budget and lines <= budget:
            presumed_stamps.append(path)
            continue
        touched.append(path)
    # git diff cannot see a file that was never tracked, and a brand-new
    # script is exactly the kind of change that owes evidence.
    rc, untracked = git("ls-files", "--others", "--exclude-standard")
    if rc == 0:
        touched.extend(p for p in untracked.splitlines() if p)
    if presumed_stamps:
        # The filter is size-blind (a one-line SUBSTANTIVE token edit passes
        # under the same budget as a stamp), so what it presumed is named
        # rather than silent — the operator can disagree.
        print(f"note  {len(presumed_stamps)} stamp-sized change(s) presumed "
              f"version stamps and not counted as touches: "
              f"{', '.join(presumed_stamps[:6])}"
              + ("…" if len(presumed_stamps) > 6 else ""))
    return touched


def obligations_for(paths: list[str]) -> list[str]:
    out: list[str] = []
    for prefix, obliges in TOUCH_MAP:
        if any(p.startswith(prefix) for p in paths):
            for ob in obliges:
                if ob == "conformance-freshness":
                    fresh = conformance_fresh()
                    if fresh is None or fresh:
                        # Unarmed (no history yet) or already fresh: nothing
                        # owed. Only a STALE board on a rule-surface release
                        # creates the obligation.
                        continue
                if ob not in out:
                    out.append(ob)
    return out


def spec_lines_changed(base: str) -> int:
    rc, numstat = git("diff", "--numstat", base, "--",
                      "scripts/", "references/", "tokens/")
    if rc != 0:
        print("note  spec-rule diff failed; counting 0 changed lines — "
              "callers only reach this with a resolvable base, so seeing "
              "this line at all is itself worth investigating")
        return 0
    total = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            total += (0 if parts[0] == "-" else int(parts[0]))
            total += (0 if parts[1] == "-" else int(parts[1]))
    rc, untracked = git("ls-files", "--others", "--exclude-standard", "--",
                        "scripts/", "references/", "tokens/")
    if rc == 0:
        for p in untracked.splitlines():
            if p:
                total += len((ROOT / p).read_text("utf-8").splitlines())
    return total


def evidence_path(version: str) -> pathlib.Path:
    return EVIDENCE_DIR / f"{version}.json"


def load(version: str) -> dict[str, Any]:
    return json.loads(evidence_path(version).read_text("utf-8"))


def save(version: str, doc: dict[str, Any]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path(version).write_text(json.dumps(doc, indent=2) + "\n", "utf-8")


def cmd_init(version: str | None) -> int:
    versions = releases_in_changelog()
    v = version or versions[0]
    if v not in versions:
        print(f"FAIL  {v} is not a CHANGELOG heading")
        return 1
    idx = versions.index(v)
    if idx + 1 >= len(versions):
        print(f"FAIL  {v} has no predecessor in the CHANGELOG")
        return 1
    prev = versions[idx + 1]
    base = find_release_commit(prev)
    if base is None:
        print(f"FAIL  no commit subject starts with '{prev} — '; cannot "
              f"compute the release diff. Name the base explicitly by "
              f"editing the file, or fix the commit history.")
        return 1
    touched = effective_touches(base)
    if touched is None:
        print("FAIL  git cannot diff against the base (shallow clone?)")
        return 1
    obligations = obligations_for(touched)
    spec = ""
    if spec_lines_changed(base) > SPEC_LINE_THRESHOLD:
        spec = "REQUIRED: name a specs/*.md file (or 'waived: <reason>')"
    doc: dict[str, Any] = {
        "version": v,
        "diff_base": base,
        "spec": spec,
        "obligations": obligations,
        "checks": [],
        "waivers": [],
    }
    save(v, doc)
    print(f"wrote {evidence_path(v).relative_to(ROOT)}: "
          f"{len(obligations)} obligation(s) from {len(touched)} effective "
          f"touch(es)")
    for ob in obligations:
        print(f"  - {ob}: {OBLIGATIONS[ob][0]}")
    return 0


def cmd_record(obligation: str) -> int:
    if obligation not in OBLIGATIONS:
        print(f"FAIL  unknown obligation {obligation!r}; known: "
              f"{', '.join(OBLIGATIONS)}")
        return 1
    if obligation == "conformance-freshness":
        # Refused, not recorded: its validate command exits 0 on a STALE
        # board, so a recorded execution would discharge the obligation
        # while proving nothing (found by the PR #87 review). The only two
        # ways to satisfy it are the board becoming fresh
        # (run_conformance.py report --record) or a reasoned waiver.
        print("FAIL  conformance-freshness cannot be satisfied by a recorded "
              "run — refresh the board (run_conformance.py report --record, "
              "≥2 agents, all tasks) or write a reasoned waiver")
        return 1
    v = releases_in_changelog()[0]
    if not evidence_path(v).exists():
        print(f"FAIL  no evidence file for {v}; run --init first")
        return 1
    doc = load(v)
    command = OBLIGATIONS[obligation][0]
    print(f"running: {command}")
    # shell=True for the same reason preflight.py uses it: the recorded
    # string must be exactly what a re-runner would paste into a shell.
    p = subprocess.run(command, shell=True, cwd=ROOT,  # noqa: S602
                       capture_output=True, text=True)
    digest = hashlib.sha256((p.stdout + p.stderr).encode()).hexdigest()
    entry: dict[str, Any] = {
        "id": obligation,
        "command": command,
        "exit_code": p.returncode,
        "stdout_sha256": digest,
        "date": datetime.date.today().isoformat(),
    }
    doc["checks"] = [c for c in doc.get("checks", []) if c.get("id") != obligation]
    doc["checks"].append(entry)
    save(v, doc)
    tail = (p.stdout + p.stderr).strip().splitlines()[-3:]
    for line in tail:
        print(f"  {line}")
    print(f"recorded {obligation}: exit {p.returncode}, sha256 {digest[:16]}…")
    if p.returncode != 0:
        print("  NOTE a nonzero exit must cite an open KNOWN_GAPS entry "
              "(add \"gap\": \"GAP-NNN\" to the entry) or the gate fails.")
    return 0


def check_file(v: str, warn: bool) -> list[str]:
    errors: list[str] = list(validate_maps())
    if not evidence_path(v).exists():
        return [f"releases/evidence/{v}.json does not exist — every release "
                f"writes one (--init), even with zero obligations"]
    try:
        doc = load(v)
    except json.JSONDecodeError as exc:
        return [f"releases/evidence/{v}.json is not valid JSON: {exc}"]

    if doc.get("version") != v:
        errors.append(f"evidence file says version {doc.get('version')!r}, "
                      f"CHANGELOG says {v}")

    checks = doc.get("checks", [])
    waived = {w.get("id") for w in doc.get("waivers", [])
              if isinstance(w, dict) and w.get("reason")}
    for w in doc.get("waivers", []):
        if not isinstance(w, dict) or not w.get("id") or not w.get("reason"):
            errors.append("a waiver without an id and a reason is not a waiver")

    # D7-analog: structural completeness of every recorded check.
    for c in checks:
        for field in ("id", "command", "exit_code", "stdout_sha256", "date"):
            if field not in c:
                errors.append(f"check {c.get('id', '?')}: missing {field!r}")
        if c.get("exit_code", 0) != 0:
            gap = c.get("gap", "")
            gaps_text = (ROOT / "KNOWN_GAPS.md").read_text("utf-8")
            open_ids = re.findall(
                r"^## (GAP-\d+)[^\n]*\n(?:(?!^## ).)*?- status: open",
                gaps_text, re.M | re.S)
            if gap not in open_ids:
                errors.append(
                    f"check {c.get('id')}: exit {c.get('exit_code')} without "
                    f"citing an OPEN KNOWN_GAPS entry — a known failure ships "
                    f"ledgered, an unknown one does not ship")

    # D6-analog: copied evidence.
    digests = [c.get("stdout_sha256") for c in checks if c.get("stdout_sha256")]
    if len(digests) != len(set(digests)):
        errors.append("two checks share a stdout_sha256 — evidence was "
                      "copied, not executed")
    ids = [c.get("id") for c in checks]
    if len(ids) != len(set(ids)):
        errors.append("two checks share an id")

    # Obligations all answered. conformance-freshness has exactly two
    # satisfaction paths — the board BECOMING fresh, or a waiver — and a
    # recorded execution is NOT one of them (cmd_record refuses the id, and
    # this loop never consults `done` for it): its validate command exits 0
    # on a stale board, so a recorded run would prove nothing. Found by the
    # PR #87 review, which recorded exactly such a run and watched the gate
    # go green.
    done = {c.get("id") for c in checks if "exit_code" in c}
    for ob in doc.get("obligations", []):
        if ob == "conformance-freshness":
            if not conformance_fresh() and ob not in waived:
                errors.append(
                    f"obligation {ob!r}: the board is still stale and no "
                    f"waiver is written — satisfy it with fresh rows for "
                    f"≥{CONFORMANCE_MIN_AGENTS} agents via "
                    f"run_conformance.py report --record")
            continue
        if ob not in done and ob not in waived:
            errors.append(f"obligation {ob!r} has neither a recorded "
                          f"execution nor a reasoned waiver")

    # Recompute obligations against the diff — a hand-deleted obligation is
    # caught here. A base the repo SHOULD be able to resolve but cannot is a
    # FAILURE, not a note: the audited file must not be able to switch off
    # its own audit by carrying a blank or bogus diff_base (found by the
    # PR #87 review, which blanked the field and watched the gate exit 0).
    # The one legitimate degradation is a genuinely shallow clone, which is
    # detectable and still gets named.
    base = doc.get("diff_base", "")
    recomputed = None
    if not base:
        errors.append("the evidence file carries no diff_base — --init "
                      "writes one, and without it the obligation recompute "
                      "and the spec rule cannot run")
    else:
        rc, _ = git("cat-file", "-e", base)
        if rc != 0:
            # A recorded SHA is rebase-fragile: the very first rebase-merge
            # to main rewrote every hash and turned each evidence file's
            # diff_base into a dangling pointer, and this check correctly
            # reddened main (run 31553098031). Commit SUBJECTS survive a
            # rebase, and the commit-convention guard makes them reliable —
            # so re-resolve the previous release by subject before calling
            # anything a finding.
            versions = releases_in_changelog()
            idx = versions.index(v) if v in versions else -1
            fallback = (find_release_commit(versions[idx + 1])
                        if 0 <= idx < len(versions) - 1 else None)
            if fallback is not None:
                print(f"note  diff_base {base[:12]}… does not resolve "
                      f"(rebased history); re-resolved the previous release "
                      f"by commit subject as {fallback[:12]}…")
                base = fallback
                rc = 0
        if rc == 0:
            touched = effective_touches(base)
            if touched is not None:
                recomputed = obligations_for(touched)
        if recomputed is None:
            rc_sh, shallow = git("rev-parse", "--is-shallow-repository")
            if rc_sh == 0 and shallow.strip() == "true":
                print("note  shallow clone: cannot resolve the diff base; "
                      "trusting the file's obligation list — this is a "
                      "degraded check, not a passing one")
            else:
                errors.append(
                    f"diff_base {base[:16]}… does not resolve in a "
                    f"full-history checkout, and no commit subject matches "
                    f"the previous release — the recompute that catches a "
                    f"hand-edited obligation list cannot run, and that is a "
                    f"finding, not a note")
    if recomputed is not None:
        for ob in recomputed:
            if ob not in doc.get("obligations", []):
                errors.append(f"the release diff obliges {ob!r} but the "
                              f"evidence file's list omits it")
        # Spec discipline, computed from the same diff.
        if spec_lines_changed(base) > SPEC_LINE_THRESHOLD:
            spec = str(doc.get("spec", ""))
            if spec.startswith("waived:") and len(spec) > len("waived: "):
                pass
            elif spec and (ROOT / spec).exists():
                if spec not in newest_section():
                    errors.append(f"spec {spec!r} exists but the newest "
                                  f"CHANGELOG entry does not cite it")
            else:
                errors.append(
                    f"this release changes >{SPEC_LINE_THRESHOLD} lines of "
                    f"scripts//references//tokens/ — the evidence file's "
                    f"'spec' must name an existing specs/*.md (cited in the "
                    f"CHANGELOG entry) or read 'waived: <reason>'")

    # Overclaim phrases while anything is waived or gap-cited.
    compromised = bool(waived) or any(c.get("exit_code", 0) != 0 for c in checks)
    if compromised:
        section = newest_section().lower()
        for phrase in OVERCLAIM:
            if phrase in section:
                errors.append(
                    f"the CHANGELOG entry says {phrase!r} while this release "
                    f"carries a waiver or a gap-cited failure — the sentence "
                    f"0.1.415 taught this repo not to write")
    return errors


def cmd_check(warn: bool) -> int:
    v = releases_in_changelog()[0]
    errors = check_file(v, warn)
    mode = "WARN" if warn else "FAIL"
    for e in errors:
        print(f"{mode}  {e}")
    if not errors:
        doc = load(v) if evidence_path(v).exists() else {}
        print(f"ok    evidence for {v}: "
              f"{len(doc.get('checks', []))} execution(s), "
              f"{len(doc.get('obligations', []))} obligation(s), "
              f"{len(doc.get('waivers', []))} waiver(s)")
        return 0
    print(f"\n{len(errors)} finding(s)."
          + (" Warn-only for this release; the gate goes red next." if warn
             else " The release does not ship until these close."))
    return 0 if warn else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode")
    ap.add_argument("--init", nargs="?", const="", metavar="VERSION",
                    help="write the skeleton for VERSION (default: newest)")
    ap.add_argument("--check", action="store_true",
                    help="validate the newest release's evidence (CI step)")
    ap.add_argument("--warn", action="store_true",
                    help="with --check: report findings but exit 0")
    rec = sub.add_parser("record", help="execute one obligation and record it")
    rec.add_argument("--id", required=True, dest="obligation")
    args = ap.parse_args(argv)

    if args.mode == "record":
        return cmd_record(args.obligation)
    if args.init is not None:
        return cmd_init(args.init or None)
    if args.check:
        return cmd_check(args.warn)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
