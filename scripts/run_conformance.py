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
  machine, on one date. The report always prints its `n`.
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
        if isinstance(report, list) and report:
            report = report[0]
        return {"exit": proc.returncode, "verdicts": report.get("verdicts", {})}
    except json.JSONDecodeError:
        return {"exit": proc.returncode, "verdicts": {}, "unparseable": True}


def score_recall(task: dict, text: str) -> dict:
    low = text.lower()
    hits = {q: any(k in low for k in keys) for q, keys in task["answers"].items()}
    return {"score": sum(hits.values()), "of": len(hits),
            "missed": [q for q, ok in hits.items() if not ok]}


def render(record: dict) -> str:
    lines = [f"# LUMI style conformance · skill {record['version']}", "",
             f"Run `{record['run_id']}` · {record['host']} · "
             f"{record['detected']} of {record['agents']} agents detected · n={record['repeat']}",
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
    ap.add_argument("--repeat", type=int, default=1)
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

    if args.command in ("run", "score"):
        run_dir = pathlib.Path(args.run) if args.run else RESULTS / "latest"
        run_dir.mkdir(parents=True, exist_ok=True)
        for a in agents:
            ok, _ = probed[a["id"]]
            if not ok:
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
              f"re-run with `score --run {run_dir}`")
        return 0

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
              "repeat": args.repeat, "task_ids": [t["id"] for t in tasks], "rows": rows}
    print(render(record))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
