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
    python3 scripts/run_conformance.py report --run DIR
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "adapters" / "platforms.json"
TASKS = ROOT / "conformance" / "tasks"
RESULTS = ROOT / "conformance" / "results"
CAP_RANK = {"prompt": 0, "files": 1, "full": 2}


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


def score_checks(kind: str, path: pathlib.Path) -> dict:
    script = {"prose": "check_prose.py", "design": "check_design.py"}[kind]
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / script),
                           str(path), "--json"], capture_output=True, text=True)
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
             f"Run `{record['run_id']}` · {record['host']} · "
             f"{record['detected']} of {record['agents']} agents detected · n={record['repeat']} per agent",
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
              "`not installed` were not exercised and are listed rather than omitted."]
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["validate", "detect", "run", "score", "report"])
    ap.add_argument("--run", default=None)
    args = ap.parse_args(argv)

    try:
        tasks, agents = load_tasks(), load_agents()
    except (OSError, ValueError, KeyError) as exc:          # noqa: BLE001
        print(f"FAIL  conformance suite does not parse: {exc}")
        return 1

    if args.command == "validate":
        print(f"ok    {len(tasks)} tasks, {len(agents)} agents in the registry")
        return 0

    probed = {a["id"]: detect(a) for a in agents}
    if args.command == "detect":
        for a in agents:
            ok, note = probed[a["id"]]
            print(f"  {a['id']:16} {'available' if ok else 'not exercised':14} {note}")
        print(f"\n{sum(1 for v in probed.values() if v[0])} of {len(agents)} available here")
        return 0

    if args.command == "run":
        run_dir = pathlib.Path(args.run) if args.run else RESULTS / "latest"
        # Created up front. The mkdir moved inside the per-agent loop when run and
        # score split, so on the case the scoreboard itself documents — few or no
        # agents detected — `run` announced a directory it had not made and
        # `score` then reported it missing.
        run_dir.mkdir(parents=True, exist_ok=True)
        for a in agents:
            if not probed[a["id"]][0]:
                continue
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
        if not args.run:
            print("FAIL  score needs --run DIR")
            return 1
        run_dir = pathlib.Path(args.run)
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
                    scores[key] = {"verdict": "no deliverable", "detail":
                                   f"nothing matching {task['deliverable']}"}
                    unscored += 1
                    continue
                target = produced[0]
                # The run directory is wherever the operator put it, which is
                # usually outside this repository; relative_to() raises there.
                try:
                    shown = str(target.relative_to(ROOT))
                except ValueError:
                    shown = str(target)
                entry, failed = {"artifact": shown}, []
                seen = {}
                for kind in task["score"]:
                    if kind == "recall":
                        entry["recall"] = score_recall(
                            task, target.read_text(encoding="utf-8", errors="replace"))
                        if entry["recall"]["missed"]:
                            failed.append(f"recall {entry['recall']['score']}"
                                          f"/{entry['recall']['of']}")
                    else:
                        entry[kind] = score_checks(kind, target)
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
                        seen.update(entry[kind]["verdicts"])
                # `require` is checked ONCE, against the union of every checker's
                # verdicts. Per-kind it needed `got is not None` to skip the other
                # checker's metrics, and that clause also swallowed the case this
                # harness most needs to catch: a required metric that reported
                # nothing at all. check_design returns UNMEASURABLE for a document
                # using none of LUMI's tokens, so an agent emitting exactly that
                # scored green on the scoreboard.
                for metric, want in (task.get("require") or {}).items():
                    got = seen.get(metric)
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
    rows = []
    for a in agents:
        ok, note = probed[a["id"]]
        rows.append({"name": a["name"], "capability": a["capability"],
                     "cli": note if ok else "—",
                     "tasks": {t["id"]: ("—" if not ok else "not run") for t in tasks},
                     "verdict": "not installed" if not ok else "not run"})
    record = {"version": version, "run_id": args.run or "detect-only",
              "host": f"{sys.platform}", "agents": len(agents),
              "detected": sum(1 for v in probed.values() if v[0]),
              "repeat": 1, "task_ids": [t["id"] for t in tasks], "rows": rows}
    print(render(record))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
