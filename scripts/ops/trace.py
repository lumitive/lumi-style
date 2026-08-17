#!/usr/bin/env python3
"""Open, annotate and close a build trace.

Why a trace exists: every claim this repository makes about its own quality has
until now come from whichever agent was being measured. 0.1.415 reported "all
gates pass" having run eight of seventeen, and `check_evidence.py` was built so
a release's verdicts are executed and machine-written rather than typed. A trace
is the same discipline applied to a build.

Three rules the shape of this tool enforces:

**The verdict fields are machine-written.** `--close` RUNS the checkers with
`--json` and transcribes their output. There is no flag for supplying a verdict,
in the same way `check_evidence.py`'s schema has no field for one.

**A trace opens when the storyline is agreed, not when the deliverable is
finished.** A trace written only at the end never records an abandoned build,
and the bias runs one way: toward success. An open record with no `closed_at` is
itself the evidence that a build was abandoned.

**No free text, ever.** Every field is closed-vocabulary or a number. A trace
is the anonymous projection of a build; the reasoning belongs in the debug log,
which stays in the delivery directory. This is red line 9 held by a schema
rather than by good intentions.

Usage
  trace.py open  --genre sales --storyline market-analysis --entry-path A
  trace.py yield --id T --clause P-1 --to P-2 --stage build
  trace.py refuse --id T --clauses P-1,P-5 --stage checks
  trace.py close --id T --deliverable out.html [--input-tokens N --output-tokens N]
  trace.py validate                       # every stored record against the schema
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import subprocess
import sys
import uuid

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
TRACES = ROOT / "evals" / "traces"

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
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
from deliverable_registry import STAGE_OF  # noqa: E402
from trace_schema import ENUMS, FIELDS, PHASES, validate  # noqa: E402


def _now():
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def _skill_version():
    m = re.search(r'version: "([\d.]+)"', (ROOT / "SKILL.md").read_text(encoding="utf-8"))
    return m.group(1) if m else "unknown"


def _path(trace_id):
    return TRACES / f"{trace_id}.json"


def _load(trace_id):
    p = _path(trace_id)
    if not p.exists():
        sys.exit(f"no such trace: {trace_id}")
    return json.loads(p.read_text(encoding="utf-8"))


def _save(rec):
    TRACES.mkdir(parents=True, exist_ok=True)
    _path(rec["trace_id"]).write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n",
                                      encoding="utf-8")


def _checker_json(script, deliverable, extra=()):
    """-> (parsed, spoke). `spoke` is False when the checker could not be
    transcribed at all.

    The two states must not be one value. An HONEST empty report — a checker
    that ran and had nothing to say — is `([], True)`. A checker that crashed,
    timed out, or printed something that is not JSON is `(None, False)`, and
    the caller has to record that rather than skip it.

    This is not hypothetical. `check_design.py` prints its blind-gate warning
    with a bare `print()` that `--json` does not suppress, so a deck built with
    `div.page` instead of `section.page` — the exact case that warning exists
    for — emits prose in front of its JSON. The checker does its job (exit 1,
    UNMEASURABLE); the old version of this function returned None and `close`
    read that as "nothing to say", so every design gate vanished from the trace
    without a word. `ledger.py`'s second ledger looks for `not_measured` to
    suspect an instrument, and absence is not `not_measured`, so the one
    mechanism built to catch a broken checker could not see it.
    """
    cmd = ["python3", str(ROOT / "scripts" / "check" / script),
           str(deliverable), "--json", *extra]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return None, False
    try:
        return json.loads(proc.stdout), True
    except json.JSONDecodeError:
        # A nonzero exit with unparseable stdout is a checker that failed to
        # speak. Exit code alone is not the test: check_design exits 1 on a
        # legitimate FAIL and its JSON is perfectly good.
        return None, False


def cmd_open(a):
    rec: dict[str, object] = dict.fromkeys(FIELDS)
    rec.update(trace_id="t-" + uuid.uuid4().hex[:12], opened_at=_now(), closed_at=None,
               source=a.source, skill_version=_skill_version(), genre=a.genre,
               storyline=a.storyline, entry_path=a.entry_path,
               outline_reviewed=False, titles_changed_after_approval=0,
               geometry=a.geometry, pages=0, content_pages=0, phase_seconds={},
               gates={}, graded={}, thresholds={},
               principle_yields=[], refused_to_emit=None)
    errors = validate(rec)
    if errors:
        sys.exit("refusing to open an invalid trace:\n  " + "\n  ".join(errors))
    _save(rec)
    print(rec["trace_id"])


def cmd_yield(a):
    rec = _load(a.id)
    rec["principle_yields"].append({"yielded": a.clause, "for": a.to, "stage": a.stage})
    _fail_if_invalid(rec)
    _save(rec)
    print(f"{a.id}: {a.clause} yielded to {a.to} at {a.stage}")


def cmd_refuse(a):
    rec = _load(a.id)
    rec["refused_to_emit"] = {"clauses": a.clauses.split(","), "stage": a.stage}
    _fail_if_invalid(rec)
    _save(rec)
    print(f"{a.id}: refused to emit — {a.clauses} collided at {a.stage}. "
          f"Record the reasoning in the debug log, not here.")


def cmd_close(a):
    rec = _load(a.id)
    rec["closed_at"] = _now()
    rec["outline_reviewed"] = bool(a.outline_reviewed)
    rec["titles_changed_after_approval"] = a.titles_changed_after_approval
    for phase, seconds in (a.phase or []):
        rec["phase_seconds"][phase] = seconds
    for k in ("model", "effort", "agent", "corpus_id"):
        if getattr(a, k, None) is not None:
            rec[k] = getattr(a, k)
    for k in ("input_tokens", "output_tokens"):
        if getattr(a, k) is not None:
            rec[k] = getattr(a, k)

    # THE TRACE MUST NOT CONTRADICT THE DOCUMENT. A trace recording `a4`
    # beside a body declaring `landscape` describes two different documents,
    # and until 0.1.499 nothing could see it: the word `geometry` named three
    # unrelated vocabularies and no code connected any pair. The map is
    # declared once in the registry; this reads it.
    try:
        raw = pathlib.Path(a.deliverable).read_text(encoding="utf-8")
    except OSError:
        raw = ""
    m = re.search(r'data-geometry="([a-z0-9-]+)"', raw)
    if m and rec.get("geometry"):
        expected = STAGE_OF.get(m.group(1))
        if expected and expected != rec["geometry"]:
            sys.exit(f"the document declares data-geometry={m.group(1)!r}, whose "
                     f"stage is {expected!r}, and this trace was opened as "
                     f"{rec['geometry']!r}. One of the two is wrong, and a trace "
                     f"that disagrees with its own deliverable is worse than no "
                     f"trace.")

    # Verdicts are transcribed from the checkers, never supplied.
    prose, prose_spoke = _checker_json(
        "check_prose.py", a.deliverable,
        ["--genre", rec["genre"]] if rec["genre"] else [])
    design, design_spoke = _checker_json("check_design.py", a.deliverable)
    # Both checkers emit a LIST of one dict per file, carrying `verdicts`
    # (id -> ok/fail/n-a) and `targets` (id -> the target string, in which
    # "(gates)" is what marks a gate). The numeric readings are top-level keys
    # under the same id. Nothing here interprets a result; it transcribes.
    for name, report, spoke in (("prose", prose, prose_spoke),
                                ("design", design, design_spoke)):
        if not spoke:
            # A checker that could not speak is recorded PER CHECKER. The old
            # code marked `_checkers` only when BOTH failed, so one broken
            # checker left a trace that looked complete: nine design gates
            # simply absent, and absence reads as "nothing to say" to every
            # consumer. ledger.py's second ledger hunts `not_measured` to
            # suspect an instrument, so this line is what lets it work at all.
            rec["thresholds"][f"_checker_{name}"] = "not_measured"
            continue
        if not report:
            continue
        row = report[0] if isinstance(report, list) else report
        targets = row.get("targets", {})
        for mid, verdict in row.get("verdicts", {}).items():
            bucket = "gates" if "(gates)" in targets.get(mid, "") else "graded"
            rec[bucket][mid] = verdict
            value = row.get(mid)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rec["thresholds"][mid] = value
            elif value is None and mid in row:
                # Three states, not two. "n/a" means the metric does not apply
                # to this document — a Chinese ban list on an English deck.
                # "not_measured" means it applies and could not be run. The
                # ledger suspects an instrument on the second and must not on
                # the first, and collapsing them made three healthy metrics
                # look broken the first time the ledger was run.
                rec["thresholds"][mid] = (
                    "n/a" if str(verdict).lower() in ("n/a", "na")
                    else "not_measured")
        v = row.get("D16_visual_presence") or {}
        if isinstance(v.get("content_pages"), int):
            rec["content_pages"] = v["content_pages"]
        d = row.get("D12_commercial_footer") or {}
        if isinstance(d.get("pages"), int):
            rec["pages"] = d["pages"]
    if not rec["gates"] and not rec["graded"]:
        # not measured is not zero, and it is not a pass either. This now fires
        # on the shape the old condition missed too: both checkers ran, both
        # returned an honest empty report, and the trace records a build that
        # was never graded.
        rec["thresholds"]["_checkers"] = "not_measured"
    _fail_if_invalid(rec)
    _save(rec)
    print(f"closed {a.id}: {len(rec['gates'])} gate(s), {len(rec['graded'])} graded, "
          f"{len(rec['thresholds'])} threshold reading(s)")


def _fail_if_invalid(rec):
    errors = validate(rec)
    if errors:
        sys.exit("refusing to write an invalid trace:\n  " + "\n  ".join(errors))


def cmd_validate(_a):
    if not TRACES.exists():
        print("no traces yet")
        return
    bad = 0
    for p in sorted(TRACES.glob("*.json")):
        errors = validate(json.loads(p.read_text(encoding="utf-8")))
        if errors:
            bad += 1
            print(f"FAIL {p.name}")
            for e in errors:
                print("       " + e)
    total = len(list(TRACES.glob("*.json")))
    print(f"{total - bad}/{total} traces valid")
    if bad:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("open", help="open a trace when the storyline is agreed")
    o.add_argument("--genre", choices=ENUMS["genre"], required=True)
    o.add_argument("--storyline", required=True)
    o.add_argument("--entry-path", dest="entry_path", choices=ENUMS["entry_path"],
                   required=True)
    o.add_argument("--source", choices=ENUMS["source"], default="build")
    o.add_argument("--geometry", choices=ENUMS["geometry"])
    o.set_defaults(func=cmd_open)

    y = sub.add_parser("yield", help="record that one clause gave way to another")
    y.add_argument("--id", required=True)
    y.add_argument("--clause", required=True)
    y.add_argument("--to", required=True)
    y.add_argument("--stage", choices=PHASES, required=True)
    y.set_defaults(func=cmd_yield)

    r = sub.add_parser("refuse", help="record a refusal to emit (PRINCIPLES.md §3)")
    r.add_argument("--id", required=True)
    r.add_argument("--clauses", required=True, help="comma-separated, e.g. P-1,P-5")
    r.add_argument("--stage", choices=PHASES, required=True)
    r.set_defaults(func=cmd_refuse)

    c = sub.add_parser("close", help="close a trace; verdicts come from the checkers")
    c.add_argument("--id", required=True)
    c.add_argument("--deliverable", required=True)
    c.add_argument("--outline-reviewed", action="store_true", dest="outline_reviewed")
    c.add_argument("--titles-changed-after-approval", type=int, default=0,
                   dest="titles_changed_after_approval")
    c.add_argument("--phase", nargs=2, action="append", metavar=("PHASE", "SECONDS"),
                   type=str)
    c.add_argument("--model")
    c.add_argument("--effort")
    c.add_argument("--agent")
    c.add_argument("--corpus-id", dest="corpus_id")
    c.add_argument("--input-tokens", type=int, dest="input_tokens")
    c.add_argument("--output-tokens", type=int, dest="output_tokens")
    c.set_defaults(func=cmd_close)

    v = sub.add_parser("validate", help="check every stored trace against the schema")
    v.set_defaults(func=cmd_validate)

    a = ap.parse_args()
    if a.cmd == "close" and a.phase:
        a.phase = [(p, int(s)) for p, s in a.phase]
    a.func(a)


if __name__ == "__main__":
    main()
