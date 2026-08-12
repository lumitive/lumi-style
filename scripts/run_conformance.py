#!/usr/bin/env python3
"""Run the same tasks through every agent CLI on this machine, and score them alike.

The point of this package is that a deliverable is held to one bar whichever model
wrote it. That is a claim, and this is the only thing in the repository that can
produce evidence for it: fixed prompts, whatever agents the operator has
installed, and the same three check scripts scoring every output.

**What it cannot do**, stated plainly because the temptation to overclaim here is
the whole risk:

* It cannot show a model writes *well*. The checks measure mechanical conformance.
  A green row means the artifact is well-formed and free of the defects we can
  express as arithmetic — not that the deck is good. `CLAUDE.md` §8 governs, and
  adding platforms does not change it.
* It cannot show reproducibility. Agent CLIs are non-deterministic and their
  versions drift weekly. A recorded pass is one run, of one CLI version, on one
  machine, on one date. The report prints n=1 because nothing here repeats
  a run; a --repeat flag existed briefly and only printed the number the
  operator typed, which in an evidence document is the worst possible field.
* It cannot say anything about a platform the operator has not installed. That
  state is `not installed — not exercised`, and it is printed rather than omitted.
* **It does not run in CI.** No API keys, no network, no vendor SDKs. CI proves
  the package is well-formed and the gates fire; this proves neither.

    python3 scripts/run_conformance.py validate     # tasks + registry parse (CI-safe)
    python3 scripts/run_conformance.py detect       # which agent CLIs exist here
    python3 scripts/run_conformance.py run          # invoke every detected agent
    python3 scripts/run_conformance.py score --run DIR
    python3 scripts/run_conformance.py report --run DIR [--run DIR ...]

`report` takes as many run directories as the operator has, and merges them.
Building the board from one directory blanks every agent that directory does not
contain, which turned a recorded `fail` into `not installed` the first time a
second agent was run — a measured result becoming an absence, in the document
whose closing paragraph says absences are listed rather than omitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

# The scripts are peers in one directory; the genre vocabulary lives in
# check_prose.py and is imported, never copied (see GENRES there).
from check_prose import GENRES  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "adapters" / "platforms.json"
TASKS = ROOT / "conformance" / "tasks"
RESULTS = ROOT / "conformance" / "results"
CAP_RANK = {"prompt": 0, "files": 1, "full": 2}

# What a task's `score` list may name, and the script behind each.
#
# `layout` joins in 0.1.368, and its absence was the hole under this whole
# harness: `inspect_layout.py` is the only instrument here that renders the
# document, and the scoreboard has never run it. A deliverable with overlapping
# text, no part openers and a clamped title scored `pass` on prose and design and
# was recorded as conformant, because the two checkers that ran cannot see a
# rendered page and the one that can was never asked.
SCRIPTS = {"prose": "check_prose.py", "design": "check_design.py",
           "layout": "inspect_layout.py"}
SCORE_KINDS = set(SCRIPTS) | {"recall"}


def load_tasks() -> list[dict]:
    tasks = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(TASKS.glob("*.json"))]
    for t in tasks:
        for field in ("id", "prompt", "min_capability", "score"):
            if field not in t:
                raise ValueError(f"{t.get('id', '?')}: missing {field}")
        if t["min_capability"] not in CAP_RANK:
            raise ValueError(f"{t['id']}: unknown min_capability {t['min_capability']!r}")
        # Everything `score` will dereference, checked here rather than as a
        # traceback halfway through a scoreboard that then discards every row
        # already scored.
        if not t["score"]:
            raise ValueError(f"{t['id']}: empty `score` list would pass anything")
        # A kind nothing knows how to run used to reach `score_checks` and raise
        # KeyError halfway through a scoreboard, discarding every row already
        # graded. Caught here, where the answer is "fix the task file".
        for kind in t["score"]:
            if kind not in SCORE_KINDS:
                raise ValueError(f"{t['id']}: `score` names {kind!r}, which is not "
                                 f"one of {', '.join(sorted(SCORE_KINDS))}")
        # Imported, not hand-copied: the hand-copy that used to sit here
        # rejected `training` for two releases after 0.1.376 added it to
        # check_prose.py, and nothing could notice until a task used it.
        if t.get("genre") not in (None, *GENRES):
            raise ValueError(f"{t['id']}: genre {t['genre']!r} is not one "
                             f"check_prose.py accepts")
        if not t.get("deliverable"):
            raise ValueError(f"{t['id']}: no `deliverable` glob")
        if "recall" in t["score"]:
            for q, keys in (t.get("answers") or {}).items():
                for k in keys:
                    try:
                        re.compile(k)
                    except re.error as exc:
                        raise ValueError(f"{t['id']}: answer pattern {k!r} for {q!r} "
                                         f"does not compile: {exc}") from exc
            if not t.get("answers"):
                raise ValueError(f"{t['id']}: scores recall with no `answers` key")
    return tasks


def task_fingerprint(task: dict) -> str:
    """What a result is a result *of*.

    A recorded verdict is only meaningful against the task that produced it, and
    a task is edited far more often than anyone re-runs an agent: T1 went from
    six pages to twelve, which moved M11 from ungraded to graded, and the
    scoreboard went on showing the six-page `pass` with nothing to indicate it
    was answering a prompt that no longer exists.

    Only the fields that can change a verdict are hashed. `title` and `note` are
    documentation; rewording them must not invalidate a run.
    """
    material = {k: task.get(k) for k in
                ("prompt", "deliverable", "score", "require", "answers", "input",
                 "genre")}
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:12]


def asked_fingerprint(task_dir: pathlib.Path, task: dict) -> str:
    """The fingerprint of the question the agent was actually shown.

    Taken from the PROMPT.txt in the run directory, not from the task at scoring
    time. Scoring re-reads the artifact from disk, so hashing the current task
    would stamp a fresh fingerprint onto an old answer and call it current —
    which is exactly the failure being closed: a six-page deck reported as
    passing a twelve-page task. If the prompt the agent saw is gone, say so
    rather than assuming it matched.
    """
    f = task_dir / "PROMPT.txt"
    if not f.exists():
        return "no-prompt"
    material = dict({k: task.get(k) for k in
                     ("deliverable", "score", "require", "answers", "input",
                      "genre")},
                    prompt=f.read_text(encoding="utf-8"))
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:12]


def load_agents() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["platforms"]


def detect(agent: dict) -> tuple[bool, str]:
    """Is this agent runnable here? Never a guess: a platform with no probe is
    recorded as unprobeable with the reason its registry entry gives."""
    probe = agent.get("probe")
    if not probe:
        return False, agent.get("probe_waiver", "no probe declared")
    if not shutil.which(probe[0]):
        return False, "not installed"
    try:
        out = subprocess.run(probe, capture_output=True, text=True, timeout=20)
        return True, (out.stdout or out.stderr).strip().splitlines()[0][:40]
    except Exception as exc:                                # noqa: BLE001
        return False, f"probe failed: {exc.__class__.__name__}"


def score_checks(kind: str, path: pathlib.Path, genre: str | None = None) -> dict:
    """Run one checker, honouring the task's declared genre.

    `check_prose.py` has taken `--genre` since it was written, and this harness
    never passed it — so every deliverable was graded as sales material whatever
    it was. T1 has called itself an internal analysis deck since the day it was
    added, and the dash ban that failed it explicitly does not bind internal
    analysis. The task said what it was and nothing carried the word to the
    checker.
    """
    script = SCRIPTS[kind]
    argv = [sys.executable, str(ROOT / "scripts" / script), str(path), "--json"]
    if kind == "prose" and genre:
        argv += ["--genre", genre]
    if kind == "layout":
        # `--deliverable` is the point: without it `inspect_layout.py` gates on
        # nothing and every artifact scores the same. `--no-sheet` because the
        # contact sheet is for a person to look at and nobody is watching a
        # harness run; the numbers are what this reads.
        argv += ["--deliverable", "--no-sheet"]
    proc = subprocess.run(argv, capture_output=True, text=True)
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"exit": proc.returncode, "verdicts": {}, "unparseable": True}
    # An empty list is valid JSON and survived the `isinstance(report, list) and
    # report` guard as `[]`, which then hit `[].get` and crashed the run. A
    # checker that graded nothing has not scored the artifact; say so rather
    # than raising into the operator's face halfway through a scoreboard.
    if isinstance(report, list):
        if not report:
            return {"exit": proc.returncode, "verdicts": {}, "unparseable": True}
        report = report[0]
    if not isinstance(report, dict):
        return {"exit": proc.returncode, "verdicts": {}, "unparseable": True}
    verdicts = report.get("verdicts", {})
    if not verdicts:
        # A checker that emitted a report and graded nothing has not scored the
        # artifact. A `deliverable` glob matching a directory produced exactly
        # this and read as a pass.
        return {"exit": proc.returncode, "verdicts": {}, "unparseable": True}
    return {"exit": proc.returncode, "verdicts": verdicts}


def score_recall(task: dict, text: str) -> dict:
    # Per numbered answer line, which is what T3's `scoring` field says and what
    # the whole-document version did not do: `\bone\b` for question 5 was
    # satisfied by question 3's own "no one", so a one-line reply answering
    # nothing scored 5 of 5. Answer i is matched against line i alone.
    # Keyed on the literal number, and on the LAST run of them. Matching by
    # ordinal position marked a correct sheet 0/5 when the agent echoed the
    # prompt's own five numbered questions above its answers — failing a recall
    # task for a formatting reason unrelated to recall.
    numbered = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)[.)]", line)
        if m:
            numbered[int(m.group(1))] = line.strip().lower()
    hits = {}
    for i, (q, keys) in enumerate(task["answers"].items(), start=1):
        line = numbered.get(i, "")
        hits[q] = any(re.search(k, line) for k in keys)
    return {"score": sum(hits.values()), "of": len(hits),
            "missed": [q for q, ok in hits.items() if not ok]}


def render(record: dict) -> str:
    lines = [f"# LUMI style conformance · skill {record['version']}", "",
             f"Runs {record['run_id']} · {record['host']} · "
             f"{record['detected']} of {record['agents']} agents detected · "
             f"up to n={record['repeat']} per agent · "
             f"{record['structural']} of {record['agents']} can never answer a CLI probe",
             "",
             "| agent | capability | cli | " +
             " | ".join(t for t in record["task_ids"]) + " | verdict |",
             "|---|---|---|" + "---|" * (len(record["task_ids"]) + 1)]
    for row in record["rows"]:
        cells = [row["name"], row["capability"], row["cli"]]
        cells += [row["tasks"].get(t, "—") for t in record["task_ids"]]
        cells.append(f"**{row['verdict']}**")
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## What this table is not", "",
              "It is not a claim that any model produces good output: the checks "
              "measure mechanical conformance, and a page is done when a human reads "
              "it as intentional. Each row is one run of one CLI version on one "
              "machine on one date, not a property of the agent. Rows marked "
              "`not installed` were not exercised and are listed rather than omitted. "
              "A cell reading `stale: task changed` means the recorded verdict answers "
              "a version of that task the repository no longer contains — it is not a "
              "pass and not a failure, it is a result that has to be re-earned.",
              "",
              "**Absence has two kinds and they are marked differently.** A row "
              "reading `not installed` is a machine away: the agent ships a CLI, "
              "nobody has run it here, and one install would produce a row "
              "tomorrow. A row reading `cannot be probed` never will — an IDE with "
              "no command line, and chat models reached through an API — so its "
              "artifacts have to be produced by hand and scored with `--agent`. "
              "Printing the two identically made the board read as ten pieces of "
              "pending work when only six are.",
              "",
              "**Where a cell names more than one run, it names the spread too.** "
              "`3 runs, all pass` is a different claim from `3 runs UNSTABLE: "
              "fail×1, pass×2`, and until 0.1.390 the harness could not tell them "
              "apart: a repeat of an agent OVERWROTE its earlier row, so every "
              "verdict was one sample and a flaky checker could not be "
              "distinguished from a flaky agent. Repeating costs tokens and "
              "produces an uncomfortable number, which is the value.",
              "",
              "**A verdict can change without the artifact changing.** The checks are "
              "the moving part: a row re-scored after a release that taught the "
              "checkers something new is a statement about this package's instruments "
              "on that date, not about the model that wrote the file. A `pass` that "
              "later reads `fail` most often means the earlier run measured less."]
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["validate", "detect", "run", "score", "report"])
    # Repeatable, and only `report` may take more than one. A scoreboard built
    # from a single directory erases every agent that directory does not
    # contain: recording the Claude Code run turned Cursor's row from a
    # measured `fail` into `not installed`, which is the false absence this
    # file's own closing paragraph says it exists to avoid. Later --run wins on
    # a collision, so re-running one agent replaces its own row and nobody
    # else's.
    ap.add_argument("--run", action="append", default=None)
    ap.add_argument("--agent", default=None,
                    help="prepare (or report) this agent even if no CLI answers its "
                         "probe — IDEs and API models are driven by hand")
    ap.add_argument("--record", action="store_true",
                    help="with report: append one row per scored agent per run "
                         "to conformance/history.json — the tracked memory the "
                         "evidence gate's freshness obligation reads")
    args = ap.parse_args(argv)

    try:
        tasks, agents = load_tasks(), load_agents()
    except (OSError, ValueError, KeyError) as exc:          # noqa: BLE001
        print(f"FAIL  conformance suite does not parse: {exc}")
        return 1

    if args.command == "validate":
        hist = ROOT / "conformance" / "history.json"
        if hist.exists():
            try:
                rows = json.loads(hist.read_text(encoding="utf-8"))
                if not isinstance(rows, list):
                    raise ValueError("history must be a JSON list")
                for i, r in enumerate(rows):
                    for key in ("skill_version", "agent", "date", "run_dir",
                                "tasks", "scores_sha256"):
                        if key not in r:
                            raise ValueError(f"history[{i}] missing {key!r}")
                    if not isinstance(r["tasks"], dict):
                        raise ValueError(f"history[{i}].tasks is not a dict")
            except (json.JSONDecodeError, ValueError) as exc:
                print(f"FAIL  conformance/history.json does not parse: {exc}")
                return 1
            print(f"ok    {len(tasks)} tasks, {len(agents)} agents in the "
                  f"registry, {len(rows)} history rows")
            return 0
        print(f"ok    {len(tasks)} tasks, {len(agents)} agents in the registry")
        return 0

    # `run` and `score` act on exactly one directory. Saying so beats quietly
    # taking the first: an operator who passes two to `score` means to score
    # two, and scoring one of them without a word is the kind of silent
    # narrowing this harness is otherwise careful about.
    runs = args.run or []
    if args.command in ("run", "score") and len(runs) > 1:
        print(f"FAIL  {args.command} acts on one --run directory; {len(runs)} given. "
              f"Only `report` merges runs.")
        return 1

    probed = {a["id"]: detect(a) for a in agents}
    if args.command == "detect":
        for a in agents:
            ok, note = probed[a["id"]]
            print(f"  {a['id']:16} {'available' if ok else 'not exercised':14} {note}")
        print(f"\n{sum(1 for v in probed.values() if v[0])} of {len(agents)} available here")
        return 0

    if args.command == "run":
        run_dir = pathlib.Path(runs[0]) if runs else RESULTS / "latest"
        # Created up front. The mkdir moved inside the per-agent loop when run and
        # score split, so on the case the scoreboard itself documents — few or no
        # agents detected — `run` announced a directory it had not made and
        # `score` then reported it missing.
        run_dir.mkdir(parents=True, exist_ok=True)
        wanted = [a for a in agents
                  if (a["id"] == args.agent if args.agent else probed[a["id"]][0])]
        if args.agent and not wanted:
            print(f"FAIL  no platform with id {args.agent!r} in the registry")
            return 1
        if not wanted:
            print("no agent detected and no --agent given; nothing to prepare. An IDE "
                  "or an API model has no CLI to probe — name it with --agent and drive "
                  "it by hand.")
            return 1
        for a in wanted:
            for t in tasks:
                if CAP_RANK[a["capability"]] < CAP_RANK[t["min_capability"]]:
                    continue
                wd = run_dir / a["id"] / t["id"]
                wd.mkdir(parents=True, exist_ok=True)
                (wd / "PROMPT.txt").write_text(t["prompt"], encoding="utf-8")
                if "input" in t:
                    (wd / "input.md").write_text(t["input"], encoding="utf-8")
        print(f"prepared {run_dir}; invoke each agent against its PROMPT.txt, then "
              f"`score --run {run_dir}`")
        return 0

    if args.command == "score":
        if not runs:
            print("FAIL  score needs --run DIR")
            return 1
        run_dir = pathlib.Path(runs[0])
        if not run_dir.exists():
            print(f"FAIL  {run_dir} does not exist; run `run` first")
            return 1
        by_id = {t["id"]: t for t in tasks}
        scores, unscored = {}, 0
        for agent_dir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
            for task_dir in sorted(p for p in agent_dir.iterdir() if p.is_dir()):
                task = by_id.get(task_dir.name)
                if task is None:
                    scores[f"{agent_dir.name}/{task_dir.name}"] = {
                        "verdict": "unknown task",
                        "detail": "no task of this id; a renamed task silently "
                                  "erased every prior result for it"}
                    unscored += 1
                    continue
                # sorted: glob yields in filesystem order, so an agent that also
                # left notes.md made the scored artifact depend on directory
                # ordering — non-reproducible for a reason unrelated to model
                # non-determinism, which this harness is careful to bound.
                produced = sorted(f for f in task_dir.glob(task["deliverable"])
                                  if f.name not in ("input.md",))
                key = f"{agent_dir.name}/{task_dir.name}"
                if not produced:
                    # No artifact is NOT a pass. It is the most common real
                    # outcome — an agent that answered in chat instead of
                    # writing a file — and it has to read as a failure to
                    # produce, never as an absent finding.
                    scores[key] = {"verdict": "no deliverable",
                                   "task_hash": asked_fingerprint(task_dir, task),
                                   "detail": f"nothing matching {task['deliverable']}"}
                    unscored += 1
                    continue
                target = produced[0]
                # The run directory is wherever the operator put it, which is
                # usually outside this repository; relative_to() raises there.
                try:
                    shown = str(target.relative_to(ROOT))
                except ValueError:
                    shown = str(target)
                entry: dict[str, Any] = {"artifact": shown,
                                         "task_hash": asked_fingerprint(task_dir, task)}
                failed: list[str] = []
                verdict_union: dict[str, Any] = {}
                for kind in task["score"]:
                    if kind == "recall":
                        entry["recall"] = score_recall(
                            task, target.read_text(encoding="utf-8", errors="replace"))
                        if entry["recall"]["missed"]:
                            failed.append(f"recall {entry['recall']['score']}"
                                          f"/{entry['recall']['of']}")
                    else:
                        entry[kind] = score_checks(kind, target, task.get("genre"))
                        # A checker that could not be read has not scored this
                        # artifact. The flag was written into the record and
                        # never looked at, so a crashed checker scored `pass`.
                        if entry[kind].get("unparseable"):
                            failed.append(f"{kind} emitted no parseable report")
                        elif entry[kind]["exit"] != 0:
                            # Written into the record four times and read none.
                            # `require` names two metrics of eighteen, so an
                            # artifact failing sixteen others scored `pass` —
                            # the same defect as the unread `unparseable` flag,
                            # in the release that fixed that one.
                            failed.append(f"{kind} exited {entry[kind]['exit']}")
                        verdict_union.update(entry[kind]["verdicts"])
                # `require` is checked ONCE, against the union of every checker's
                # verdicts. Per-kind it needed `got is not None` to skip the other
                # checker's metrics, and that clause also swallowed the case this
                # harness most needs to catch: a required metric that reported
                # nothing at all. check_design returns UNMEASURABLE for a document
                # using none of LUMI's tokens, so an agent emitting exactly that
                # scored green on the scoreboard.
                for metric, want in (task.get("require") or {}).items():
                    got = verdict_union.get(metric)
                    if got is None:
                        failed.append(f"{metric} never reported")
                    elif got != want:
                        failed.append(f"{metric}={got}")
                entry["verdict"] = "pass" if not failed else "fail"
                entry["failed"] = failed
                scores[key] = entry
        (run_dir / "scores.json").write_text(
            json.dumps(scores, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for key, s in sorted(scores.items()):
            extra = f" ({', '.join(s.get('failed', []))})" if s.get("failed") else ""
            print(f"  {key:38} {s['verdict']}{extra}")
        if not scores:
            print(f"  NOT MEASURED: nothing under {run_dir} matched a known agent and "
                  f"task; `run` writes that layout, and a scoreboard of zero rows is "
                  f"not a scoreboard of passes")
            return 1
        print(f"\n{len(scores) - unscored} scored, {unscored} produced no deliverable "
              f"-> {run_dir / 'scores.json'}")
        return 1 if any(s["verdict"] != "pass" for s in scores.values()) else 0

    # report
    version = (ROOT / "SKILL.md").read_text(encoding="utf-8").split('version: "')[1].split('"')[0]
    # Merged across every --run given, in the order given, so a second agent's
    # results ADD a row instead of blanking every row the new directory does not
    # contain. Later wins on a collision: re-running one agent replaces its own
    # cells and nobody else's.
    # ACCUMULATED, not overwritten. `scored.update()` made a second run of the
    # same agent REPLACE the first, so the board printed "n=1 per agent" as a
    # property of the harness when it was a property of this line: a repeat was
    # silently discarded, and the one thing a repeat is for — telling a flaky
    # checker from a flaky agent — was the one thing that could not happen.
    scored: dict[str, list[Any]] = {}
    for name in runs:
        f = pathlib.Path(name) / "scores.json"
        if not f.exists():
            print(f"FAIL  {f} does not exist; run `score --run {name}` first")
            return 1
        # Guarded here, at the first read, so a corrupt file is a verdict and
        # not a traceback. The --record block below re-reads with its own
        # guard, but this loop runs first, so an unguarded loads here made
        # that guard unreachable — found by test_record_producer.py.
        try:
            scored_doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"FAIL  {f} does not parse ({exc}); nothing reported")
            return 1
        for key, value in scored_doc.items():
            scored.setdefault(key, []).append(value)
    rows = []
    for a in agents:
        ok, note = probed[a["id"]]
        # A recorded score outranks a probe: an agent driven by hand has no CLI
        # to answer, and reporting it as "not installed" when its artifacts were
        # just graded is the kind of false absence this scoreboard exists to
        # avoid.
        mine = {k.split("/", 1)[1]: v for k, v in scored.items()
                if k.split("/", 1)[0] == a["id"]}
        cells, verdicts = {}, []
        runs_here = 0
        for t in tasks:
            got = mine.get(t["id"]) or []
            runs_here = max(runs_here, len(got))
            if not got:
                cells[t["id"]] = "—" if not ok else "not run"
                continue
            fresh = [s for s in got if s.get("task_hash") == task_fingerprint(t)]
            if not fresh:
                # The verdict stands, but not for this task. Showing it would be
                # reporting an answer to a question no longer asked.
                cells[t["id"]] = "stale: task changed"
                verdicts.append("stale")
                continue
            seen = [s["verdict"] for s in fresh]
            worst = "fail" if "fail" in seen else seen[0]
            detail = ", ".join(sorted({f for s in fresh for f in s.get("failed", [])}))
            cell = worst if worst == "pass" else (f"{worst}: {detail}" if detail else worst)
            # THE SPREAD, beside the verdict. A mean with no spread is the thing
            # this board is told not to report: with n>1 the cell says how many
            # runs agreed, and disagreement is named rather than averaged away.
            if len(fresh) > 1:
                agree = seen.count(worst)
                cell += (f" · {len(fresh)} runs, all {worst}" if agree == len(fresh)
                         else f" · {len(fresh)} runs UNSTABLE: "
                              + ", ".join(f"{v}×{seen.count(v)}" for v in sorted(set(seen))))
            cells[t["id"]] = cell
            verdicts.append(worst)
        if verdicts:
            verdict = ("pass" if all(v == "pass" for v in verdicts)
                       else "stale" if any(v == "stale" for v in verdicts)
                       and not any(v == "fail" for v in verdicts) else "fail")
            cli = note if ok else "driven by hand"
        else:
            # Six of the ten "not installed" rows are a machine away; four can
            # never answer a CLI probe at all — an IDE with no command line and
            # two chat models behind an API. Printing them identically made the
            # board look like ten pieces of pending work when only six are.
            structural = not a.get("probe")
            verdict = ("cannot be probed" if structural
                       else "not installed" if not ok else "not run")
            cli = note if ok else "—"
        rows.append({"name": a["name"], "capability": a["capability"],
                     "cli": cli, "tasks": cells, "verdict": verdict,
                     "runs": runs_here})
    record = {"version": version,
              "run_id": ", ".join(f"`{r}`" for r in runs) or "detect-only",
              "host": f"{sys.platform}", "agents": len(agents),
              "detected": sum(1 for v in probed.values() if v[0]),
              "repeat": max((r["runs"] for r in rows), default=0),
              "structural": sum(1 for r in rows if r["verdict"] == "cannot be probed"),
              "task_ids": [t["id"] for t in tasks], "rows": rows}
    print(render(record))

    if args.record:
        # One row per scored agent per run directory, pinned to the artifact
        # by digest: the scores.json stays untracked (results/ is gitignored
        # on purpose), so the digest is what makes a history row evidence
        # rather than an assertion. Idempotent: an identical row is not
        # appended twice.
        import datetime
        import hashlib
        hist_path = ROOT / "conformance" / "history.json"
        history = (json.loads(hist_path.read_text(encoding="utf-8"))
                   if hist_path.exists() else [])
        added = 0
        for name in runs:
            f = pathlib.Path(name) / "scores.json"
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            per_agent: dict[str, dict[str, str]] = {}
            try:
                scored_doc = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"FAIL  {f} does not parse ({exc}); nothing recorded "
                      f"from this run")
                return 1
            for key, value in scored_doc.items():
                agent_id, _, task_id = key.partition("/")
                per_agent.setdefault(agent_id, {})[task_id] = value.get(
                    "verdict", "unscored")
            for agent_id, task_verdicts in sorted(per_agent.items()):
                row = {"skill_version": version, "agent": agent_id,
                       "date": datetime.date.today().isoformat(),
                       "run_dir": str(name), "tasks": task_verdicts,
                       "scores_sha256": digest}
                if not any(r.get("agent") == agent_id
                           and r.get("run_dir") == str(name)
                           and r.get("scores_sha256") == digest
                           for r in history):
                    history.append(row)
                    added += 1
        hist_path.write_text(json.dumps(history, indent=2) + "\n",
                             encoding="utf-8")
        print(f"\nrecorded {added} new history row(s) -> "
              f"{hist_path.relative_to(ROOT)} ({len(history)} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
