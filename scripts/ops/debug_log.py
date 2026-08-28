#!/usr/bin/env python3
"""The debug-mode log: one JSON file beside the deliverable, machine-written.

    python3 scripts/ops/debug_log.py init <deliverable> --platform <id>
    python3 scripts/ops/debug_log.py run <log> [--label <text>] -- <command...>
    python3 scripts/ops/debug_log.py step <log> --label <text> --seconds <s>
    python3 scripts/ops/debug_log.py attach <log> --kind design|prose|layout --json-file <f>
    python3 scripts/ops/debug_log.py assess <log> --dim C1..C8 --score 1-4 --reason <text>
    python3 scripts/ops/debug_log.py error <log> --stage <text> --message <text>
    python3 scripts/ops/debug_log.py note <log> --text <text>
    python3 scripts/ops/debug_log.py validate <log>

WHY A HELPER AND NOT A FORMAT DOC. Debug mode serves every platform the
registry claims, and a format that each agent writes by hand is a format with
as many dialects as agents. The subcommands are the schema; an agent that can
run scripts produces the same log on every platform, and an agent that cannot
run anything (the prompt tier) writes what it can into the delivery note and
names what it owes — the same degradation contract the checkers use.

THE SHAPES ARE BORROWED FROM THE ONES THIS REPO ALREADY TRUSTS
(specs/2026-08-12-debug-mode-design.md): steps are the perf-baseline shape
(label + seconds; AG-3's local, warn-only stance — the log records, nothing
gates on speed); `run` is the evidence-gate shape — it EXECUTES the command
and machine-writes exit code, output digest and date, so there is no verdict
field for a human to type; quality is the checkers' own `--json` attached
verbatim plus C1-C8 self-scores, under review_scores' standing rule that 5 is
never self-scored before a reader has scored it (this file refuses to write
one).

WHAT THE CLOSED KEY SET DOES AND DOES NOT DO. No field invites a client name
or an engagement figure, which is `reviews/scores.json`'s defence borrowed —
but only half of it: that file ships NO free-text field at all, and this one
has four (`notes`, `errors[].message`, `quality[].reason`, and whatever
`attach` embeds). Red line 9 binds the author in those four; the schema
cannot. What `validate` does enforce mechanically is the shape of every
machine-written field and the absence of CJK, Kana and Hangul — the
owner-language risk, not a proof of English.

The log is a working artifact of the engagement folder and is never committed
to this repository.

Standard library only.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent

TOP_KEYS = {"debug_log", "skill_version", "platform", "machine", "created",
            "deliverable", "steps", "commands", "checks", "quality", "errors",
            "notes"}
# ABSENT AND ONE SAY THE SAME THING. `rounds` arrives with 0.1.601 and a log
# written before it has no such key — validating it as missing would turn every
# in-flight build into a red on a field its author never had. The trace schema
# makes the same distinction for the same reason.
OPTIONAL_KEYS = {"rounds"}
CHECK_KINDS = ("design", "prose", "layout")

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

import checker_report  # noqa: E402 — after the bootstrap
import versioning  # noqa: E402

# C1-C8, matching the store review_scores.py validates. This said C1-C8 for
# forty-odd releases after C replaced H — the exact defect the scoring-sheet
# parity guard was built for, alive in the one file that guard does not read.
DIMS = tuple(f"C{i}" for i in range(1, 9))
# CJK, Kana and Hangul. The narrow original covered Chinese only and the
# docstring called it "English-only", which it is not and cannot be: a Latin
# alphabet is not a language. This is the owner-language risk, stated as what
# it is.
CJK = re.compile(r"[　-〿぀-ヿ㐀-鿿가-힯"
                 r"！-｠]")
DIGEST = re.compile(r"[0-9a-f]{64}")
ERROR_TAIL_LINES = 20
STEP_SOURCES = ("run", "self-reported")


def failing_verdicts(output: bytes):
    """The checkers' own verdict names, out of a `--json` run. None if not JSON.

    A tail of twenty lines is the right record of a crash and the wrong record
    of a checker: every check script prints its thresholds LAST, so the tail of
    a `--json` failure is the schema footer. The first third-party debug log
    this package collected carried five errors, and three of them were that
    footer — the log knew something had failed and could not say what, which is
    the one thing it exists to say.

    The two report shapes and the non-ok extraction live in checker_report now
    — one reader for the four scripts that need it, because four private
    copies of a contract is how a sheet described C1-C8 for two releases after
    C1-C8 replaced them.
    """
    reports, spoke = checker_report.parse_report(output)
    if not spoke:
        return None
    return checker_report.findings(reports)

def _now():
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _is_iso(value):
    try:
        datetime.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return False
    return True


def _platform_ids():
    reg = json.loads((ROOT / "adapters" / "platforms.json").read_text(encoding="utf-8"))
    return {p["id"] for p in reg["platforms"]}


def _read_json(path, what):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"FAIL  {path} does not exist ({what})") from None
    except json.JSONDecodeError as exc:
        # A raw traceback names the json module; the actionable fact is which
        # file is damaged and that something wrote it badly.
        raise SystemExit(f"FAIL  {path} is not parseable JSON ({exc}) — "
                         f"{what}") from None


def _load(path):
    log = _read_json(path, "run `init` first, and check nothing interrupted a write")
    if log.get("debug_log") != "1":
        raise SystemExit(f"FAIL  {path} is not a debug log (no debug_log: \"1\")")
    return log


def _save(path, log):
    # Write-then-rename. `write_text` truncates in place, so a reader could see
    # a half-written log and two writers could interleave into a file that was
    # not JSON at all — measured, under the parallel build protocol this same
    # package ships (SKILL.md step 1).
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


@contextlib.contextmanager
def _locked(path, tries=600, wait=0.05):
    """Hold an exclusive lock on one log across a read-modify-write.

    THE PARALLEL BUILD PROTOCOL MAKES THIS MANDATORY. SKILL.md step 1 puts one
    agent per body part in flight at once, each running its checks through
    `run`; every one of them read the log, appended an entry and wrote the
    whole file back. Measured with eight concurrent writers: one entry
    survived and the file came back unparseable. A log that silently drops
    evidence under the protocol it was written for is worse than no log,
    because the gaps look like nothing happened.

    `O_CREAT|O_EXCL` rather than fcntl or msvcrt: one implementation that
    holds on macOS, Linux and Windows, which is the platform requirement. A
    lock left by a killed writer blocks until the bound and then fails loudly
    naming the file to remove — breaking a lock on a timer would silently
    resume the corruption this exists to prevent.
    """
    lock = path.with_name(path.name + ".lock")
    for _ in range(tries):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            time.sleep(wait)
            continue
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                lock.unlink()
        return
    raise SystemExit(f"FAIL  {lock} has been held for {tries * wait:.0f}s. A "
                     f"writer died holding it; delete that file and retry.")


def _mutate(path, fn):
    """Every write goes through here: lock, load, change, save, unlock."""
    with _locked(path):
        log = _load(path)
        fn(log)
        _save(path, log)


def log_stem(deliverable: pathlib.Path) -> str:
    """-> the log's stem: everything but the final extension.

    `guide.en.html` and `guide.en.pdf` share one log, which is the point — the
    log describes the build, not one export. **The version and the language
    stay**, because this package's own convention puts both in the filename:
    `x.0.1.588.zh-Hans.html`. Splitting on the FIRST dot collapsed that to
    `x.debug.json`, so the zh and en versions of one deck wrote to the same
    file — and since `init` refuses to start when the log already exists, the
    second one hard-failed, or with `--restart` destroyed the first one's
    evidence.
    """
    return deliverable.name.rsplit(".", 1)[0] if "." in deliverable.name \
        else deliverable.name


def cmd_init(args):
    deliverable = pathlib.Path(args.deliverable)
    ids = _platform_ids()
    if args.platform not in ids:
        raise SystemExit(f"FAIL  platform {args.platform!r} is not in "
                         f"adapters/platforms.json ({', '.join(sorted(ids))})")
    out = deliverable.parent / (log_stem(deliverable) + ".debug.json")
    # A LOG IS ONE BUILD'S RECORD. Starting over on top of an existing one
    # silently destroys a build's evidence, and carrying one across builds is
    # how the first real sample came to name one version in `deliverable` while
    # its last commands checked another — a log that cannot say which file it
    # describes cannot be evaluated from alone, which is the whole purpose.
    # A BUILD IS N ROUNDS, AND THE RECORD BELONGS TO THE ARTIFACT. The sentence
    # above — one run of a driver is one build — was the premise, and it is
    # false: a real build fixes and re-runs. `--restart` therefore destroyed
    # rounds 1..N-1 of machine-written evidence every time round N began, and
    # the driver carried only the C1-C8 self-score across. The tell was
    # operators archiving the log by hand between rounds: this package's own
    # author did it nine times on one measured build, and both agents of the
    # 2026-08-25 validation round independently did the same.
    #
    # `--resume` keeps everything and counts the round. Nothing else in the
    # schema had to move: `checks.<kind>` has always been a list because a
    # checker runs more than once per build, and `validate`'s rule that a
    # failed command must have been run again and passed could only ever apply
    # WITHIN one round while the restart stood.
    if out.exists() and args.resume:
        log = _load(out)
        was = log.get("skill_version")
        # THE ORIGINAL LESSON, MADE MECHANICAL. A log carried across builds once
        # named one version in `deliverable` while its last commands checked
        # another. Resuming into a different version is that same log.
        if was != versioning.skill_version(ROOT):
            raise SystemExit(
                f"FAIL  {out} was written by lumi-style {was} and this is "
                f"{versioning.skill_version(ROOT)}. A log that spans two versions cannot say "
                f"which rules its commands ran under: pass --restart to begin "
                f"a new record, or move this one aside to keep it.")
        log["rounds"] = int(log.get("rounds", 1)) + 1
        _save(out, log)
        print(f"ok    {out} (round {log['rounds']})")
        return 0
    if out.exists() and not args.restart:
        raise SystemExit(f"FAIL  {out} already exists. A log is one build's "
                         f"record: pass --restart to replace it, --resume to "
                         f"continue it as a further round, or move it aside to "
                         f"keep it.")
    log = {"debug_log": "1", "skill_version": versioning.skill_version(ROOT),
           "platform": args.platform, "machine": sys.platform,
           "created": _now(), "deliverable": deliverable.name,
           "rounds": 1,
           "steps": [], "commands": [], "checks": {},
           "quality": {}, "errors": [], "notes": []}
    _save(out, log)
    print(f"ok    {out}")
    return 0


def cmd_run(args):
    path = pathlib.Path(args.log)
    _load(path)                       # fail before running, not after
    if not args.command:
        raise SystemExit("FAIL  nothing to run — pass the command after `--`")
    label = args.label or args.command[0]
    start = time.monotonic()
    # The command runs OUTSIDE the lock: parallel part-builds must be able to
    # run their checks at the same time, and only the recording is serialised.
    try:
        proc = subprocess.run(args.command, capture_output=True)  # noqa: S603 — the
        # command is the caller's own check invocation, recorded because it ran;
        # quoting it through a shell would change what was executed.
    except OSError as exc:
        # A COMMAND THAT COULD NOT START IS THE MOST IMPORTANT ONE TO RECORD,
        # and it was the only case that reached no record at all: a typo'd path
        # or a moved script raised out of this function before the append, so
        # the log held no trace of the attempt and `validate` called it clean.
        secs = round(time.monotonic() - start, 2)
        message = f"could not execute {args.command[0]!r}: {exc}"
        stamp = _now()

        def note_failure(log):
            log["commands"].append({"command": " ".join(args.command),
                                    "exit_code": None, "stdout_sha256": None,
                                    "seconds": secs, "date": stamp,
                                    "round": int(log.get("rounds", 1))})
            log["errors"].append({"stage": label, "message": message,
                                  "date": stamp})

        _mutate(path, note_failure)
        raise SystemExit(f"FAIL  {message}") from exc
    secs = round(time.monotonic() - start, 2)
    # stdout AND stderr, the way check_evidence.py digests. stdout alone gave
    # every crashed command the same empty-output digest — two different
    # failures colliding, with the whole story on the stream not read.
    entry = {"command": " ".join(args.command), "exit_code": proc.returncode,
             "stdout_sha256": hashlib.sha256(proc.stdout + proc.stderr).hexdigest(),
             "seconds": secs, "date": _now()}
    # A FAILURE WRITES ITS OWN RECORD. The first real log this tool produced
    # held thirteen commands, one of them a nonzero exit — and an empty
    # `errors` list, because the schema left the most important entry to human
    # discipline. An evaluator could see that something failed and nothing
    # about what.
    err = None
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip()
        tail = "\n".join(tail.splitlines()[-ERROR_TAIL_LINES:])
        entry["tail"] = tail
        # A CHECKER SAYS WHICH CHECK FAILED, and the tail does not. Fall back
        # to the tail whenever the output is not the JSON we can read: a crash,
        # a run without --json, a tool that is not one of ours.
        verdicts = failing_verdicts(proc.stdout)
        if verdicts is None:
            message = tail
        elif verdicts:
            entry["failing"] = verdicts
            message = "; ".join(verdicts)
        else:
            message = (f"exit {proc.returncode} and no failing verdict in the "
                       f"output — read the run itself")
        err = {"stage": label, "message": message, "date": entry["date"]}

    def append(log):
        # WHICH ROUND RECORDED THIS. A build is N rounds and the log now spans
        # them, so an entry that cannot say which round it belongs to turns a
        # cleared failure and a fresh one into the same two lines.
        entry["round"] = int(log.get("rounds", 1))
        log["commands"].append(entry)
        # `source`, because a hand-typed `step --seconds` lands in this same
        # array in this same shape: "no verdict field for a human to type" is
        # not true of an array that cannot say who measured the number.
        log["steps"].append({"label": label, "seconds": secs, "source": "run",
                             "round": int(log.get("rounds", 1))})
        if err:
            log["errors"].append(err)

    _mutate(path, append)
    sys.stdout.buffer.write(proc.stdout)
    sys.stderr.buffer.write(proc.stderr)
    print(f"note  recorded: exit {proc.returncode} in {secs}s", file=sys.stderr)
    return proc.returncode


def cmd_step(args):
    _mutate(pathlib.Path(args.log), lambda log: log["steps"].append(
        {"label": args.label, "seconds": round(args.seconds, 2),
         "source": "self-reported", "round": int(log.get("rounds", 1))}))
    return 0


def attach_doc(log_path, kind: str, doc) -> None:
    """Attach an already-parsed checker report. The in-process half of
    `cmd_attach`.

    It exists because the contract asked for something the driver destroyed:
    `check_deliverable` gathers all three reports into memory and never writes
    them, so honouring `attach` meant **re-running all three checkers with
    `--json` redirected to files** — six commands, one of them a second browser
    render. The reports were in hand the whole time.
    """
    def add(log):
        log["checks"].setdefault(kind, []).append(
            {"after": len(log["commands"]), "doc": doc})

    _mutate(pathlib.Path(log_path), add)


def cmd_attach(args):
    doc = _read_json(pathlib.Path(args.json_file),
                     "a checker that crashed writes no parseable --json")

    # A LIST, NOT A SLOT. Keyed by kind and overwritten, a checker's second run
    # replaced its first — so a build that failed a check and then passed it
    # kept only the passing document, which is the one an evaluator does not
    # need. `after` ties each document to the command entry it followed.
    attach_doc(args.log, args.kind, doc)
    print(f"ok    attached {args.kind}")
    return 0


def cmd_assess(args):
    if args.score == 5:
        # eval-rubric step 1 / review_scores.py: never self-score 5 before a
        # reader has scored it. A reader's 5 goes in reviews/scores.json where
        # the anti-gaming rule can see it; this file has no field for one.
        raise SystemExit("FAIL  never self-score 5 before a reader has scored "
                         "it (eval-rubric.md step 1)")
    if not (1 <= args.score <= 4):
        raise SystemExit("FAIL  a self-score is 1-4")
    if not args.reason.strip():
        raise SystemExit("FAIL  a score without its reason is a number, not an "
                         "assessment")
    _mutate(pathlib.Path(args.log), lambda log: log["quality"].__setitem__(
        args.dim, {"score": args.score, "reason": args.reason}))
    return 0


def cmd_error(args):
    _mutate(pathlib.Path(args.log), lambda log: log["errors"].append(
        {"stage": args.stage, "message": args.message, "date": _now()}))
    return 0


def cmd_note(args):
    _mutate(pathlib.Path(args.log), lambda log: log["notes"].append(args.text))
    return 0


def _short(cmd: str, width: int = 70) -> str:
    cmd = " ".join(str(cmd).split())
    return cmd if len(cmd) <= width else cmd[:width - 1] + "\u2026"


def _by_command(commands) -> dict:
    """-> {command string: its entries, in the order they were recorded}.

    Keyed on the command itself rather than on a label, because `run` records
    no label into `commands` - the two lists have never been joined.
    """
    by: dict = {}
    for c in commands:
        by.setdefault(" ".join(str(c.get("command", "")).split()), []).append(c)
    return by


def _cites_open_gap(log) -> bool:
    """Does any error message name an OPEN KNOWN_GAPS entry?

    An id nobody defines is not a citation, and a closed one is not a reason to
    ship red. Where KNOWN_GAPS cannot be read - the log is written in an
    engagement folder and the package may not be beside it - a well-formed id is
    accepted rather than the whole check being dropped: refusing to validate a
    log because the repository is elsewhere would fail the platforms this
    contract exists to make comparable.
    """
    cited = set()
    for e in log.get("errors") or []:
        cited |= set(re.findall(r"GAP-\d+", str(e.get("message", ""))))
    if not cited:
        return False
    try:
        gaps = (ROOT / "KNOWN_GAPS.md").read_text(encoding="utf-8")
    except OSError:
        return True
    open_ids = set(re.findall(
        r"^## (GAP-\d+)[^\n]*\n(?:(?!^## ).)*?- status: open",
        gaps, re.M | re.S))
    return bool(cited & open_ids)


def validate(log) -> list[str]:
    """-> human-readable problems; empty means the log holds its contract.

    THE VALIDATOR HAS TO REACH AS FAR AS THE WRITERS DO. It checked that four
    keys were PRESENT, so a hand-written log met it while breaking every
    promise the writers enforce: a score of 9, a self-scored 5 admitted as the
    string "5", a `stdout_sha256` reading "not-a-digest". Worse, it could not
    tell an empty log from a clean run — an agent that crashed before running
    anything produced a file this function blessed, and SKILL.md tells the
    author to point the reader at it.

    What it still cannot do is prove a digest is the digest of the output that
    command actually produced. Nothing short of re-running it can, and this
    file says so rather than implying otherwise.
    """
    out = []
    for key in log:
        if key not in TOP_KEYS | OPTIONAL_KEYS:
            out.append(f"unknown key {key!r} — the key set is closed so no "
                       f"field invites an engagement fact")
    for key in TOP_KEYS - set(log):
        out.append(f"missing key {key!r}")
    if CJK.search(json.dumps(log, ensure_ascii=False)):
        out.append("CJK, Kana or Hangul content — the log is English by owner "
                   "requirement")
    if log.get("platform") not in _platform_ids():
        out.append(f"platform {log.get('platform')!r} is not in "
                   f"adapters/platforms.json")

    commands = log.get("commands") or []
    if not commands:
        out.append("no command was ever recorded — an empty log is not a clean "
                   "run, it is a run that did not happen")
    for i, c in enumerate(commands):
        for field in ("command", "exit_code", "stdout_sha256", "date"):
            if field not in c:
                out.append(f"commands[{i}] lacks {field!r} — a command entry is "
                           f"machine-written or it is not evidence")
        if not str(c.get("command", "")).strip():
            out.append(f"commands[{i}] records no command")
        code, digest = c.get("exit_code"), c.get("stdout_sha256")
        if code is None:
            # `run` writes this pair when the command could not start.
            if digest is not None:
                out.append(f"commands[{i}] never ran but carries a digest")
        else:
            if not isinstance(code, int) or isinstance(code, bool):
                out.append(f"commands[{i}] has a non-integer exit_code")
            if not DIGEST.fullmatch(str(digest)):
                out.append(f"commands[{i}] carries {digest!r}, which is not a "
                           f"sha256 — the digest is the evidence")
        if not _is_iso(c.get("date")):
            out.append(f"commands[{i}] has a date that is not ISO-8601")
    unexplained = [c for c in commands if c.get("exit_code") not in (0, None)]
    if unexplained and not log.get("errors"):
        out.append(f"{len(unexplained)} command(s) exited non-zero and the log "
                   f"explains none of them — `run` records a failure itself, so "
                   f"an empty `errors` beside a failure means the log was "
                   f"assembled by hand")
    # A LOGGED FAILURE IS NOT A RESOLVED ONE. The check above passes the moment
    # `errors` is non-empty, and `run` fills `errors` automatically — so a build
    # whose last layout check printed NOT SHIPPABLE and whose last full-stack
    # check exited 1 produced a log this function blessed, and the delivery note
    # beside it reported both as green. Measured on a 2026-08 build; the debug
    # JSON says `"exit_code": 1` twice and the report says "0 FAIL".
    #
    # So: a command that failed must have been RUN AGAIN and passed, or the log
    # must say which open gap it ships under. This is check_evidence.py's rule,
    # which exists for exactly this and had no counterpart on the deliverable
    # side.
    for cmd, entries in _by_command(commands).items():
        if entries[-1].get("exit_code") in (0, None):
            continue
        if _cites_open_gap(log):
            continue
        out.append(f"the last run of `{_short(cmd)}` exited "
                   f"{entries[-1]['exit_code']} and nothing ran it clean "
                   f"afterwards — a build whose final reading is red is a red "
                   f"build. Fix it and run it again, or name the open "
                   f"KNOWN_GAPS entry it ships under in an `error` message")

    for i, s in enumerate(log.get("steps") or []):
        secs = s.get("seconds")
        if isinstance(secs, bool) or not isinstance(secs, (int, float)) or secs < 0:
            out.append(f"steps[{i}] lacks a non-negative numeric 'seconds'")
        if s.get("source") not in STEP_SOURCES:
            out.append(f"steps[{i}] does not say who measured it "
                       f"(source: {' | '.join(STEP_SOURCES)})")
    for kind, docs in (log.get("checks") or {}).items():
        if kind not in CHECK_KINDS:
            out.append(f"checks.{kind} is not one of {CHECK_KINDS}")
        if not isinstance(docs, list):
            out.append(f"checks.{kind} is not a list — a checker runs more than "
                       f"once per build and every run is kept")
    # AN EMPTY SELF-ASSESSMENT IS NOT A CLEAN ONE. The loop below grades each
    # entry, so a block with no entries was graded zero times and produced no
    # finding: a log recording seven commands and not one self-score printed
    # `ok  the log holds its contract`. That is precisely the shape
    # `verify_gates.py` exists to refuse — a validator saying yes to work that
    # was never done. Found in the field at 0.1.591, where one build's
    # `--assess` values were cleared by a later round and the log stayed green.
    #
    # Keyed on `commands` because an initialised log is not a finished build:
    # nagging before there is anything to assess would make every `init` read
    # red, and a gate that is red by default is a gate people learn to ignore.
    if log.get("commands") and not (log.get("quality") or {}):
        out.append("quality is empty — this log records a finished build and "
                   "not one self-score. `debug_log.py assess` writes them, or "
                   "`build.py --assess Cn=score:reason`; the rubric's "
                   "dimensions are in references/eval-rubric.md")
    for dim, q in (log.get("quality") or {}).items():
        if dim not in DIMS:
            out.append(f"quality.{dim} is not one of {', '.join(DIMS)}")
            continue
        if not isinstance(q, dict):
            out.append(f"quality.{dim} is {type(q).__name__}, not a "
                       f"{{score, reason}} object")
            continue
        score = q.get("score")
        if score == 5 or str(score) == "5":
            out.append(f"quality.{dim}: a self-scored 5 — never before a reader")
        elif isinstance(score, bool) or not isinstance(score, int) \
                or not 1 <= score <= 4:
            out.append(f"quality.{dim}: a self-score is an integer 1-4, "
                       f"got {score!r}")
        if not str(q.get("reason", "")).strip():
            out.append(f"quality.{dim} has no reason")
    return out


def cmd_validate(args):
    problems = validate(_load(pathlib.Path(args.log)))
    for p in problems:
        print(f"FAIL  {p}")
    if not problems:
        print("ok    the log holds its contract")
    return 1 if problems else 0


def main(argv):
    # The recorded command is split off BEFORE argparse sees it: REMAINDER
    # swallows optionals that follow a positional (a stdlib sharp edge), and
    # the first version of this file shipped exactly that bug — `--label`
    # became the executable. The `--` is the contract, not a convention.
    command = None
    if argv and argv[0] == "run" and "--" in argv:
        cut = argv.index("--")
        command, argv = list(argv[cut + 1:]), list(argv[:cut])
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create <stem>.debug.json beside the deliverable")
    p.add_argument("deliverable")
    p.add_argument("--platform", required=True,
                   help="a platform id from adapters/platforms.json")
    p.add_argument("--restart", action="store_true",
                   help="replace an existing log for this deliverable")
    p.add_argument("--resume", action="store_true",
                   help="continue the existing log as a further round of the "
                        "same build: everything already recorded is kept and "
                        "`rounds` goes up by one. A build is N rounds and this "
                        "is what makes the record the artifact's rather than "
                        "the round's")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("run", help="execute a command and record it as evidence; "
                                   "the command comes after `--`")
    p.add_argument("log")
    p.add_argument("--label")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("step", help="record a timed step the agent measured itself")
    p.add_argument("log")
    p.add_argument("--label", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.set_defaults(fn=cmd_step)

    p = sub.add_parser("attach", help="embed a checker's --json document")
    p.add_argument("log")
    p.add_argument("--kind", choices=CHECK_KINDS, required=True)
    p.add_argument("--json-file", required=True)
    p.set_defaults(fn=cmd_attach)

    p = sub.add_parser("assess", help="record an C1-C8 self-score with its reason")
    p.add_argument("log")
    p.add_argument("--dim", choices=DIMS, required=True)
    p.add_argument("--score", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(fn=cmd_assess)

    p = sub.add_parser("error", help="record a failure as it happens")
    p.add_argument("log")
    p.add_argument("--stage", required=True)
    p.add_argument("--message", required=True)
    p.set_defaults(fn=cmd_error)

    p = sub.add_parser("note", help="one free-text line (English, no facts)")
    p.add_argument("log")
    p.add_argument("--text", required=True)
    p.set_defaults(fn=cmd_note)

    p = sub.add_parser("validate", help="exit 1 unless the log holds its contract")
    p.add_argument("log")
    p.set_defaults(fn=cmd_validate)

    args = ap.parse_args(argv)
    if args.cmd == "run":
        args.command = command or []
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
