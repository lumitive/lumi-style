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
in the same way `check_evidence.py`'s schema has no field for one. The token
counts are verdicts about the bill and follow the same rule: `--usage` reads
the API's own usage dump, and there is no flag for typing a number.

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
  trace.py phase start build --id T       # the clock is the tool's, never typed
  trace.py phase stop  build --id T
  trace.py close --id T --deliverable out.html [--usage usage.json]
  trace.py validate                       # every stored record against the schema
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import sys
import uuid

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())

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
import checker_report  # noqa: E402
import fingerprint  # noqa: E402
import markup  # noqa: E402
import state_dir  # noqa: E402
import versioning  # noqa: E402
from deliverable_registry import STAGE_OF  # noqa: E402
from trace_schema import ENUMS, FIELDS, PHASES, validate  # noqa: E402
from trace_store import traces_dir  # noqa: E402 — one store resolver

# LUMI_TRACES redirects the store (tests, dry runs); the default is the
# tracked directory, because a trace that is not kept is not a record.
# Bound at IMPORT, like every other module constant here. A test that sets
# LUMI_TRACES afterwards must re-import (tests/test_trace_store.py does);
# `traces_dir()` is the callable form for anyone who needs it resolved live.
TRACES = traces_dir(ROOT)


def _now():
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def _path(trace_id):
    return TRACES / f"{trace_id}.json"


def _load(trace_id):
    p = _path(trace_id)
    if not p.exists():
        sys.exit(f"no such trace: {trace_id}")
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path, doc):
    """The same tmp + `os.replace` as `_save`, for the file beside the trace.

    The phase CLOCK was written in place while the trace beside it was written
    atomically, so a crash between the two banked the seconds and left the
    clock running — and the next `phase stop` added the whole span again,
    because `phase_seconds` accumulates. A truncated clock also made every later
    phase command die in an uncaught `JSONDecodeError` naming neither traces
    nor phases.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _save(rec):
    """Write a trace, whole, or not at all.

    TMP + `os.replace`, the idiom this repository already carries at
    `debug_log.py`'s `_save` and for the same reason. A bare `write_text`
    truncates on a crash mid-write, and `trace_store.load()` swallows the
    resulting `JSONDecodeError` and skips the file — so a damaged record reads
    as a record that was never made. That is FM-24's shape in the data layer:
    the loss and the absence print the same thing, which is nothing.

    Every mutation here is load → change → validate → REWRITE THE WHOLE FILE,
    so this is not a rare path; it runs on every phase stop and every close.
    """
    path = _path(rec["trace_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def _checker_json(script, deliverable, extra=()):
    """-> (parsed, spoke). `spoke` is False when the checker could not be
    transcribed at all — the distinction ledger 2 depends on. The running and
    the parsing live in checker_report now, one implementation for the four
    scripts that need them; what stays HERE is only the mapping from this
    tool's script names to the registry's kinds.
    """
    kind = {"check_prose.py": "prose", "check_design.py": "design"}[script]
    genre = extra[1] if len(extra) >= 2 and extra[0] == "--genre" else None
    run = checker_report.run_checker(kind, deliverable, genre=genre)
    if not run["spoke"]:
        return None, False
    return run["reports"], True

def _fresh_id() -> str:
    """-> a trace id no file in the store already carries.

    Twelve hex characters is 48 bits, and `_save` overwrites whatever is at the
    path it builds — so a collision would destroy a record silently and leave
    two runs believing they own one id. The store is small enough that the
    probability is remote and the check is one `exists()`, which is the wrong
    trade to skip: the cost of the guard is nothing and the cost of the event is
    a record that cannot be recovered.
    """
    for _ in range(8):
        candidate = "t-" + uuid.uuid4().hex[:12]
        if not _path(candidate).exists():
            return candidate
    sys.exit("eight generated trace ids were all already in the store. That is "
             "not chance at this size — check that the store is what you think "
             "it is before opening anything else.")


def cmd_open(a):
    rec: dict[str, object] = dict.fromkeys(FIELDS)
    rec.update(trace_id=_fresh_id(), opened_at=_now(), closed_at=None,
               source=a.source, skill_version=versioning.skill_version(ROOT), genre=a.genre,
               storyline=a.storyline, entry_path=a.entry_path,
               outline_reviewed=False, titles_changed_after_approval=0,
               geometry=a.geometry, pages=0, content_pages=0, phase_seconds={},
               gates={}, graded={}, thresholds={}, shape={},
               principle_yields=[], refused_to_emit=None,
               recipe_hash=None, recipe_version=None)
    # WHAT DROVE THIS BUILD, taken at open when the build was handed one.
    # Taking it at open is still the better moment — it fingerprints what the
    # build was actually given rather than whatever the recipe had become,
    # which is the mistake `asked_fingerprint` exists to avoid one domain over.
    # But a fill script does not EXIST at scaffold time, so `annotate --recipe`
    # (0.1.592) records it afterwards; that is a later reading of the same
    # fact, not a second opinion about it, and it overwrites whatever was taken
    # here. Prefer this one when the recipe is in hand.
    if getattr(a, "recipe", None) is not None:
        if not a.recipe.is_file():
            sys.exit(f"--recipe {a.recipe} is not a file. A recipe nobody can "
                     f"read is not a recipe this trace can vouch for.")
        rec["recipe_hash"], rec["recipe_version"] = fingerprint.recipe_fingerprint(
            a.recipe, genre=a.genre, storyline=a.storyline)
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


def _read_usage(path):
    """-> (input_tokens, output_tokens), read from a machine-emitted usage dump.

    A typed token count is a typed verdict about the bill, so there is no flag
    for one: the numbers come from the API's own usage JSON, unedited. Extra
    keys are tolerated and ignored — a real usage dump carries more than these
    two — but both token counts must be present and integral, and every
    refusal names exactly what is wrong: "could not read" must never look
    like "read, and there were no tokens".
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        sys.exit(f"--usage: could not read {path} ({e.strerror or e}). A usage "
                 f"file nobody can read is not a token count this trace can "
                 f"vouch for.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"--usage: {path} is not JSON (line {e.lineno}: {e.msg}). "
                 f"Point it at the API's own usage dump, unedited.")
    if not isinstance(data, dict):
        sys.exit(f"--usage: {path} holds a JSON {type(data).__name__}, not the "
                 f"usage object an API emits.")
    counts = []
    for key in ("input_tokens", "output_tokens"):
        if key not in data:
            sys.exit(f"--usage: {path} has no {key!r}. Both token counts are "
                     f"required; a trace that records half the bill reads as a "
                     f"cheaper build than the one that happened.")
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, int):
            sys.exit(f"--usage: {key!r} in {path} is {value!r} "
                     f"({type(value).__name__}); an integer is required.")
        counts.append(value)
    return counts[0], counts[1]


# Open phase clocks live beside the traces, outside version control (the
# directory is gitignored): a started-at timestamp is machine state for one
# build on one machine, and the trace itself carries only the seconds.
def _clock_path(trace_id):
    return TRACES / ".phases" / f"{trace_id}.json"


def cmd_phase(a):
    """Start or stop a phase clock. The seconds are computed here from two
    timestamps this tool wrote; `--phase NAME SECONDS` on close is for a
    machine dump and stays the only way to TYPE a duration, which is why the
    audit found every stored trace with `phase_seconds = {}`: nothing in the
    loop had a clock, so nobody typed one either."""
    rec = _load(a.id)
    if a.name not in PHASES:
        sys.exit(f"phase {a.name!r} is not one of {PHASES}")
    path = _clock_path(a.id)
    try:
        clocks = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError) as exc:
        sys.exit(f"the phase clock {path} could not be read ({exc}). Delete it "
                 f"to start the phase again; the trace itself is untouched.")
    if not isinstance(clocks, dict):
        sys.exit(f"the phase clock {path} is not a map of phase to start time")
    now = _dt.datetime.now(_dt.UTC)
    if a.action == "start":
        if a.name in clocks:
            sys.exit(f"phase {a.name!r} is already running since {clocks[a.name]}")
        clocks[a.name] = now.isoformat(timespec="seconds")
        _write_json(path, clocks)
        print(f"{a.name} started")
        return
    if a.name not in clocks:
        sys.exit(f"phase {a.name!r} was never started on {a.id}")
    started = _dt.datetime.fromisoformat(clocks.pop(a.name))
    seconds = max(1, round((now - started).total_seconds()))
    rec["phase_seconds"][a.name] = rec["phase_seconds"].get(a.name, 0) + seconds
    errors = validate(rec)
    if errors:
        sys.exit("refusing to write an invalid trace:\n  " + "\n  ".join(errors))
    # TWO ORDERED WRITES CANNOT BE ATOMIC, and the order chooses which failure
    # a crash produces. 0.1.640 put the clock first to stop a replay
    # double-counting; a review showed that trades a checkable wrong number for
    # a LOST span — the trace keeps its old total, the clock is gone, and the
    # replay tells the operator the phase "was never started", which is a false
    # statement about a phase that was. The trace goes first again: a doubled
    # figure can be caught against a wall clock, and `charged_seconds` feeding
    # the cost board must not silently shrink. GAP-043 holds the single-write
    # design (the open clock inside the record) that removes the window.
    _save(rec)
    if clocks:
        _write_json(path, clocks)
    else:
        path.unlink(missing_ok=True)
    print(f"{a.name} +{seconds}s (total {rec['phase_seconds'][a.name]}s)")


def cmd_close(a):
    rec = _load(a.id)
    # NOT `setdefault`: the schema blesses `null` as "not recorded" (absent and
    # null say the same thing), so a record carrying one still reached
    # `rec["shape"][key] = ...` and died with TypeError. Two stored traces in
    # this repository carry exactly that. A migration must handle every state
    # its own schema declares legal.
    if not isinstance(rec.get("shape"), dict):
        rec["shape"] = {}
    rec["closed_at"] = _now()
    rec["outline_reviewed"] = bool(a.outline_reviewed)
    rec["titles_changed_after_approval"] = a.titles_changed_after_approval
    for phase, seconds in (a.phase or []):
        try:
            value = float(seconds)
        except ValueError:
            sys.exit(f"--phase {phase}: {seconds!r} is not a number of seconds")
        if value <= 0:
            sys.exit(f"--phase {phase}: {seconds!r} must be a positive number")
        # ACCUMULATE, like `phase stop` two hundred lines up. A build is N
        # rounds and one trace now spans them (0.1.602), so the checks phase is
        # the sum of the rounds' check runs; assigning reported the last round
        # and called it the build. A fresh trace is unaffected — adding to zero
        # is setting.
        total = rec["phase_seconds"].get(phase, 0) + value
        rec["phase_seconds"][phase] = int(total) if float(total).is_integer() else total
    for k in ("model", "effort", "agent", "cli_version", "corpus_id"):
        if getattr(a, k, None) is not None:
            rec[k] = getattr(a, k)
    if a.usage is not None:
        rec["input_tokens"], rec["output_tokens"] = _read_usage(a.usage)
    # The two readings that need a browser arrive from the tool that ran one.
    # Supplied like `--usage` and for the same reason: re-rendering here to
    # re-derive a number `check_deliverable` already holds would double the
    # cost of every close. They are READINGS, not verdicts — the rule that
    # verdicts are never supplied is untouched.
    for flag, key in (("visual_share_median", "visual_share_median"),
                      ("repeated_skeleton_pages", "repeated_skeleton_pages"),
                      ("move_skeleton_clashes", "move_skeleton_clashes")):
        got = getattr(a, flag, None)
        if got is not None:
            rec["shape"][key] = got

    # THE TRACE MUST NOT CONTRADICT THE DOCUMENT. A trace recording `a4`
    # beside a body declaring `landscape` describes two different documents,
    # and until 0.1.499 nothing could see it: the word `geometry` named three
    # unrelated vocabularies and no code connected any pair. The map is
    # declared once in the registry; this reads it.
    try:
        raw = pathlib.Path(a.deliverable).read_text(encoding="utf-8")
    except OSError:
        raw = ""
    # THE REAL <body>, via the shared helper. This line originally used the
    # first regex match and was caught, in its first run against a real
    # portrait document, reading `landscape` out of the stylesheet's own
    # comment — the FIFTH defect from that one sentence, written before
    # markup.py existed to hold the lesson. The cross-check refused a correct
    # trace, which is the exact inversion of what it is for.
    declared = markup.body_attr(raw, "data-geometry") if raw else None
    if declared and rec.get("geometry"):
        expected = STAGE_OF.get(declared)
        if expected and expected != rec["geometry"]:
            sys.exit(f"the document declares data-geometry={declared!r}, whose "
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
            # checker left a trace that looked complete: every design gate
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
        # THE SHAPE, from the report this function already ran. Free: no extra
        # render, no second measurement, and the numbers are the checker's own.
        if name == "design":
            spread = row.get("D9_layout_variety") or {}
            if isinstance(spread.get("top_share"), (int, float)):
                rec["shape"]["layout_top_share"] = spread["top_share"]
            if isinstance(spread.get("distinct"), int):
                rec["shape"]["layout_kinds"] = spread["distinct"]
            drawn = row.get("D5_drawn_share") or {}
            if isinstance(drawn.get("drawn"), int):
                rec["shape"]["figures"] = drawn["drawn"]
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



# THE OPERATOR'S OWN FILE, BESIDE THE STORE AND NOT IN IT. A trace is a closed
# machine record with nowhere to put prose, which is the stated reason
# `check_repo`'s english-only guard exempts `evals/traces/` at all — so putting
# a human note INSIDE a trace would have quietly falsified that reason. The
# owner declined the field for exactly that. A sidecar keyed by trace id keeps
# the record closed and the exemption honest, and costs one join.
#
# Optional in every direction: the file need not exist, a trace need not appear
# in it, and no run's behaviour depends on it.
# RESOLVED, NOT HARD-CODED, for the same reason the store itself is: `evals/`
# is development-side and this file ships. A hard-coded path would point, in an
# installed skill, at a directory the projection does not carry — which the
# `cross-boundary paths` guard caught on the first attempt. `state_dir.store`
# keeps a maintainer's checkout writing where its data already is and gives an
# installed skill its own place.
NOTES = state_dir.store("trace-notes.json",
                        in_repo=("evals", "trace-notes.json"))


def _notes() -> dict:
    if not NOTES.exists():
        return {}
    try:
        return json.loads(NOTES.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"{NOTES} does not parse ({exc}). It is hand-edited on "
                 f"purpose; fix the JSON rather than letting a reader guess.")


def cmd_note(a):
    """Attach a note or labels to a trace, in the sidecar.

    Not a verdict, and it is in a different file from the verdicts for the same
    reason `trace.py` has no `--pass` flag: the two kinds of writing should not
    look alike. What a person is the AUTHORITY on is why a run was made and
    what to remember about it; everything a trace holds is a measurement.
    """
    if not _path(a.id).exists():
        sys.exit(f"no such trace: {a.id}. A note about a run nobody recorded "
                 f"is a note about nothing.")
    notes = _notes()
    entry = dict(notes.get(a.id) or {})
    if a.note is not None:
        entry["note"] = a.note
    if a.tag:
        # ADDED, not replaced, and de-duplicated in the order met. A second run
        # that silently dropped the first is how a label set becomes whatever
        # the last operator happened to type.
        seen = list(entry.get("tags") or [])
        for t in a.tag:
            if t not in seen:
                seen.append(t)
        entry["tags"] = seen
    if not entry:
        sys.exit("nothing to write: pass --note or --tag.")
    notes[a.id] = entry
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    tmp = NOTES.with_name(f"{NOTES.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(notes, indent=1, sort_keys=True,
                              ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, NOTES)
    print(f"{a.id}: tags={','.join(entry.get('tags') or []) or '—'} "
          f"note={'yes' if entry.get('note') else '—'} -> "
          f"{NOTES.name}")
    return 0


def cmd_annotate(a):
    """Link fields only. `corpus_id` and `review_ref` join a build to the
    measurement corpus and to the review that scored it — they are addresses,
    not verdicts, which is why this subcommand may write them after close and
    the verdict fields still have no flag anywhere.

    `--recipe` belongs here for the same reason and no other: the file that
    drives a build does not exist when the trace opens. `new_deck.py` opens the
    trace to time the scaffold, and the build script is written afterwards — so
    until 0.1.592 the only thing available to fingerprint at open was the
    OUTLINE, and that is what got recorded. An outline carries no version
    stamp, so such a build sits in the ledger as `unknown` vintage for ever
    while the script that actually produced the pages is fingerprinted by
    nothing. (Eleven stored traces carry a hash and no version; the record does
    not say which file each hashed, so this is one known cause among them
    rather than the cause of all eleven — `fingerprint.py` names the other.)

    It is still a fact and not a verdict: the hash and the version are COMPUTED
    from the file, never typed, on the same reasoning that makes
    `check_evidence.py` run its own commands instead of accepting a person's
    word for the result.
    """
    # A RECORD OPENED BEFORE `shape` EXISTED IS STILL A RECORD. `trace_schema`
    # migrated the READ side — absent and null both mean "not recorded" — and
    # this side was left assuming `cmd_open` had written the key. Any build open
    # across the 0.1.595 boundary therefore died here with KeyError and lost its
    # trace entirely. A migration is not done until both sides of it are.
    rec = _load(a.id)
    if a.corpus_id:
        rec["corpus_id"] = a.corpus_id
    if a.review_ref:
        rec["review_ref"] = a.review_ref
    if a.recipe is not None:
        if not a.recipe.is_file():
            sys.exit(f"--recipe {a.recipe} is not a file. A recipe nobody can "
                     f"read is not a recipe this trace can vouch for.")
        rec["recipe_hash"], rec["recipe_version"] = fingerprint.recipe_fingerprint(
            a.recipe, genre=rec.get("genre"), storyline=rec.get("storyline"))
        if rec["recipe_version"] is None:
            print(f"  note: {a.recipe.name} carries no version stamp, so this "
                  f"build reads as UNKNOWN vintage in the ledger — which is "
                  f"not the same as current.", file=sys.stderr)
    _fail_if_invalid(rec)
    _save(rec)
    print(f"{a.id}: corpus_id={rec['corpus_id']} review_ref={rec['review_ref']} "
          f"recipe={rec['recipe_version'] or 'unstamped'}")

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
    o.add_argument("--recipe", type=pathlib.Path,
                   help="the assemble script or template this build is "
                        "driven by — NOT its outline, which is a plan rather "
                        "than a driver and carries no version stamp. Its bytes "
                        "are fingerprinted and its own "
                        "version stamp is read, so a replay of a frozen recipe "
                        "is distinguishable from a build made to the current "
                        "rules. Omit it only when there is no recipe — a "
                        "document composed from a conversation.")
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

    ph = sub.add_parser("phase", help="start or stop a phase clock (the tool keeps time)")
    ph.add_argument("action", choices=("start", "stop"))
    ph.add_argument("name", choices=PHASES)
    ph.add_argument("--id", required=True)
    ph.set_defaults(func=cmd_phase)

    c = sub.add_parser("close", help="close a trace; verdicts come from the checkers")
    c.add_argument("--id", required=True)
    c.add_argument("--deliverable", required=True)
    c.add_argument("--outline-reviewed", action="store_true", dest="outline_reviewed")
    c.add_argument("--visual-share-median", dest="visual_share_median", type=float,
                   help="the rendered reading, from the tool that rendered it")
    c.add_argument("--repeated-skeleton-pages", dest="repeated_skeleton_pages",
                   type=int, help="pages drawing a skeleton another page draws")
    c.add_argument("--move-skeleton-clashes", dest="move_skeleton_clashes",
                   type=int, help="skeletons drawn for two different declared "
                                  "analytical moves")
    c.add_argument("--titles-changed-after-approval", type=int, default=0,
                   dest="titles_changed_after_approval")
    # The seconds value is parsed in cmd_close, with a message. Until 0.1.524
    # main() did `int(s)` on the pair: `3.5` and `twelve` both died in a
    # traceback, and the schema typed the phase NAME and never the value, so
    # a hand-edited string would have validated and broken ledger.py's sum.
    c.add_argument("--phase", nargs=2, action="append", metavar=("PHASE", "SECONDS"),
                   type=str)
    c.add_argument("--model")
    c.add_argument("--effort", choices=ENUMS["effort"])
    c.add_argument("--agent")
    c.add_argument("--cli-version", dest="cli_version",
                   help="which build of the agent's CLI did the work. Supplied "
                        "rather than probed here: this process is not the one "
                        "that ran the agent, and asking a CLI its version after "
                        "the fact answers about today rather than about the "
                        "run.")
    c.add_argument("--corpus-id", dest="corpus_id")
    c.add_argument("--usage", type=pathlib.Path,
                   help="a machine-emitted usage JSON (the API's own dump); "
                        "input_tokens and output_tokens are read from it. "
                        "There is no flag for typing a token count, for the "
                        "same reason there is none for typing a verdict.")
    c.set_defaults(func=cmd_close)

    nt = sub.add_parser("note", help="attach a note or labels to a trace, in "
                        "evals/trace-notes.json — never in the trace")
    nt.add_argument("--id", required=True)
    nt.add_argument("--note",
                    help="a sentence about this run, from the person who made "
                         "it. Any language: the sidecar is development-side and "
                         "an operator's note is neither rule prose nor rule "
                         "data.")
    nt.add_argument("--tag", action="append", default=[],
                    help="a label. Repeatable, added to what the trace already "
                         "carries rather than replacing it.")
    nt.set_defaults(func=cmd_note)

    an = sub.add_parser("annotate", help="link a closed trace to its corpus "
                        "id and review — addresses, never verdicts")
    an.add_argument("--id", required=True)
    an.add_argument("--corpus-id", dest="corpus_id")
    an.add_argument("--review-ref", dest="review_ref")
    # The builder, fingerprinted once it exists. See cmd_annotate's docstring
    # for why this cannot be done at open.
    an.add_argument("--recipe", type=pathlib.Path,
                    help="the file that actually drove this build — hashed and "
                         "read for a version stamp, never typed")
    an.set_defaults(func=cmd_annotate)

    v = sub.add_parser("validate", help="check every stored trace against the schema")
    v.set_defaults(func=cmd_validate)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
