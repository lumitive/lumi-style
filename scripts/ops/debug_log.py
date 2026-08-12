#!/usr/bin/env python3
"""The debug-mode log: one JSON file beside the deliverable, machine-written.

    python3 scripts/ops/debug_log.py init <deliverable> --platform <id>
    python3 scripts/ops/debug_log.py run <log> [--label <text>] -- <command...>
    python3 scripts/ops/debug_log.py step <log> --label <text> --seconds <s>
    python3 scripts/ops/debug_log.py attach <log> --kind design|prose|layout --json-file <f>
    python3 scripts/ops/debug_log.py assess <log> --dim H1..H6 --score 1-4 --reason <text>
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
and machine-writes exit code, stdout digest and date, so there is no verdict
field for a human to type; quality is the checkers' own `--json` attached
verbatim plus H1-H6 self-scores, under review_scores' standing rule that 5 is
never self-scored before a reader has scored it (this file refuses to write
one).

THE KEY SET IS CLOSED, and `validate` fails an unknown key — the same
engagement-fact defence as reviews/scores.json: there is nowhere to put a
client name or figure. English only; `validate` enforces that too. The log is
a working artifact of the engagement folder and is never committed to this
repository.

Standard library only.
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
import time

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent

TOP_KEYS = {"debug_log", "skill_version", "platform", "machine", "created",
            "deliverable", "steps", "commands", "checks", "quality", "errors",
            "notes"}
CHECK_KINDS = ("design", "prose", "layout")
DIMS = tuple(f"H{i}" for i in range(1, 7))
CJK = re.compile(r"[㐀-鿿　-〿！-～]")


def _now():
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _skill_version():
    m = re.search(r'^\s*version:\s*"(\d+\.\d+\.\d+)"',
                  (ROOT / "SKILL.md").read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit("FAIL  SKILL.md carries no metadata.version")
    return m.group(1)


def _platform_ids():
    reg = json.loads((ROOT / "adapters" / "platforms.json").read_text(encoding="utf-8"))
    return {p["id"] for p in reg["platforms"]}


def _load(path):
    log = json.loads(path.read_text(encoding="utf-8"))
    if log.get("debug_log") != "1":
        raise SystemExit(f"FAIL  {path} is not a debug log (no debug_log: \"1\")")
    return log


def _save(path, log):
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def cmd_init(args):
    deliverable = pathlib.Path(args.deliverable)
    ids = _platform_ids()
    if args.platform not in ids:
        raise SystemExit(f"FAIL  platform {args.platform!r} is not in "
                         f"adapters/platforms.json ({', '.join(sorted(ids))})")
    # The stem before the first dot: `guide.en.html` and `guide.en.pdf` share
    # one log, which is the point — the log describes the build, not one export.
    out = deliverable.parent / (deliverable.name.split(".")[0] + ".debug.json")
    log = {"debug_log": "1", "skill_version": _skill_version(),
           "platform": args.platform, "machine": sys.platform,
           "created": _now(), "deliverable": deliverable.name,
           "steps": [], "commands": [], "checks": {},
           "quality": {}, "errors": [], "notes": []}
    _save(out, log)
    print(f"ok    {out}")
    return 0


def cmd_run(args):
    path = pathlib.Path(args.log)
    log = _load(path)
    if not args.command:
        raise SystemExit("FAIL  nothing to run — pass the command after `--`")
    start = time.monotonic()
    proc = subprocess.run(args.command, capture_output=True)  # noqa: S603 — the
    # command is the caller's own check invocation, recorded because it ran;
    # quoting it through a shell would change what was executed.
    secs = round(time.monotonic() - start, 2)
    entry = {"command": " ".join(args.command), "exit_code": proc.returncode,
             "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
             "seconds": secs, "date": _now()}
    log["commands"].append(entry)
    log["steps"].append({"label": args.label or args.command[0], "seconds": secs})
    _save(path, log)
    sys.stdout.buffer.write(proc.stdout)
    sys.stderr.buffer.write(proc.stderr)
    print(f"note  recorded: exit {proc.returncode} in {secs}s", file=sys.stderr)
    return proc.returncode


def cmd_step(args):
    path = pathlib.Path(args.log)
    log = _load(path)
    log["steps"].append({"label": args.label, "seconds": round(args.seconds, 2)})
    _save(path, log)
    return 0


def cmd_attach(args):
    path = pathlib.Path(args.log)
    log = _load(path)
    doc = json.loads(pathlib.Path(args.json_file).read_text(encoding="utf-8"))
    log["checks"][args.kind] = doc
    _save(path, log)
    print(f"ok    attached {args.kind}")
    return 0


def cmd_assess(args):
    path = pathlib.Path(args.log)
    log = _load(path)
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
    log["quality"][args.dim] = {"score": args.score, "reason": args.reason}
    _save(path, log)
    return 0


def cmd_error(args):
    path = pathlib.Path(args.log)
    log = _load(path)
    log["errors"].append({"stage": args.stage, "message": args.message,
                          "date": _now()})
    _save(path, log)
    return 0


def cmd_note(args):
    path = pathlib.Path(args.log)
    log = _load(path)
    log["notes"].append(args.text)
    _save(path, log)
    return 0


def validate(log) -> list[str]:
    """-> human-readable problems; empty means the log holds its contract."""
    out = []
    for key in log:
        if key not in TOP_KEYS:
            out.append(f"unknown key {key!r} — the key set is closed so there "
                       f"is nowhere to put an engagement fact")
    for key in TOP_KEYS - set(log):
        out.append(f"missing key {key!r}")
    if CJK.search(json.dumps(log, ensure_ascii=False)):
        out.append("CJK content — the log is English-only by owner requirement")
    for i, c in enumerate(log.get("commands", [])):
        for field in ("command", "exit_code", "stdout_sha256", "date"):
            if field not in c:
                out.append(f"commands[{i}] lacks {field!r} — a command entry is "
                           f"machine-written or it is not evidence")
    for i, s in enumerate(log.get("steps", [])):
        if not isinstance(s.get("seconds"), (int, float)):
            out.append(f"steps[{i}] lacks a numeric 'seconds'")
    for kind in log.get("checks", {}):
        if kind not in CHECK_KINDS:
            out.append(f"checks.{kind} is not one of {CHECK_KINDS}")
    for dim, q in log.get("quality", {}).items():
        if dim not in DIMS:
            out.append(f"quality.{dim} is not an H1-H6 dimension")
        elif not isinstance(q, dict) or q.get("score") == 5:
            out.append(f"quality.{dim}: a self-scored 5 — never before a reader")
        elif not str(q.get("reason", "")).strip():
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

    p = sub.add_parser("assess", help="record an H1-H6 self-score with its reason")
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
