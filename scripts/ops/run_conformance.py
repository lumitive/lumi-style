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

    python3 scripts/ops/run_conformance.py validate     # tasks + registry parse (CI-safe)
    python3 scripts/ops/run_conformance.py detect       # which agent CLIs exist here
    python3 scripts/ops/run_conformance.py run --drive  # invoke every detected agent CLI
    python3 scripts/ops/run_conformance.py run          # write the prompts, drive by hand
    python3 scripts/ops/run_conformance.py score --run DIR
    python3 scripts/ops/run_conformance.py report --run DIR [--run DIR ...]

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

# The scripts are peers in one directory; the genre vocabulary lives in
# check_prose.py and is imported, never copied (see GENRES there).
# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import re
import shutil
import subprocess
import sys
import sys as _bs_sys  # noqa: E402
import tempfile
import time
from typing import Any

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import checker_report  # noqa: E402
import fingerprint  # noqa: E402
from check_prose import GENRES  # noqa: E402
from deliverable_registry import kinds  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
REGISTRY = ROOT / "adapters" / "platforms.json"
TASKS = ROOT / "conformance" / "tasks"
RESULTS = ROOT / "conformance" / "results"
CAP_RANK = {"prompt": 0, "files": 1, "full": 2}

# How long one task may take before the driver gives up. T1 is a twelve-page
# deck and this package's own measurement of a thirty-page one is 27 minutes, so
# the ceiling is generous; what it buys is that an agent which hangs produces a
# recorded `timeout` rather than a session that never ends. Before this existed
# the only timeout in the file was the 20 seconds on the `--version` probe.
DRIVE_TIMEOUT = 1800


# What a consumer of this skill must be able to READ. Not a guess about the
# platform's sandbox: the rules cite these directories by name, so an agent that
# cannot open them is being asked to follow instructions it cannot see.
SKILL_SURFACE = ("SKILL.md", "tokens/lumi-theme.css", "references/design-rules.md",
                 "scripts/ops/new_deck.py", "assets/brand")


def environment_check(agent):
    """Can this agent reach the skill? Returns [] when it can.

    **What this proves, exactly: the skill exists at the registry's install path
    on THIS machine, and the platform declares a way to be handed it.** It does
    not prove the agent can read it — the reads happen in the agent's sandbox
    and this runs in the driver's process. In the 2026-08-13 incident the files
    existed the whole time; `.exists()` would have said yes and the run would
    have proceeded. `drive()`'s transcript check is the half that can see the
    sandbox, after the fact.

    Both halves exist because of one incident on 2026-08-13. An agent driven in
    a temporary directory produced **two** decks with invented palettes (a
    third, driven after the fix, carries all 36 shipped colour tokens), and its
    transcript said *"the skill's references/, tokens/, scripts/ and assets/
    live outside this session's allowed directory and are blocked from
    reading"*. The palette was not a judgement it made. Two attributions were
    published before anyone read that line — first to the agent, then to the
    rules — and both were wrong.

    The counts matter and were themselves overstated at first ("three decks,
    three agent failures on the board"; the board carries two `fail` rows, one
    per agent, and the other agent's was `M2_number_sourcing`). The evidence
    lives under `conformance/results/`, which is untracked, so a later reader
    cannot check it — which is the reason to state it exactly.
    """
    paths = agent.get("skill_paths") or []
    if not paths:
        return [f"{agent['id']} declares no skill_paths; there is nothing to "
                f"prove reachable"]
    # EVERY declared path, not the first. The registry lists several per
    # platform and the live one is not always first: opencode's own list ends
    # with the shared ~/.claude/skills path, and openclaw's carries a literal
    # <workspace> placeholder that expanduser will never resolve. Probing
    # paths[0] alone would skip a working install permanently, and a permanent
    # skip that looks like a finding is the harder kind of wrong to notice.
    roots = [pathlib.Path(p).expanduser() for p in paths if "<" not in p]
    live = [r for r in roots
            if all((r / rel).exists() for rel in SKILL_SURFACE)]
    if not live:
        return [f"{agent['id']} cannot reach the skill from any of its "
                f"{len(roots)} declared path(s): "
                + ", ".join(str(r) for r in roots[:3])]
    if not agent.get("drive_skill_flag"):
        return [f"{agent['id']} declares no drive_skill_flag, so the driver "
                f"cannot hand {live[0]} to it — an agent driven in a temporary "
                f"directory reads SKILL.md and nothing beside it"]
    return []


def drive(agent, task, prompt_dir, model=None, timeout=DRIVE_TIMEOUT, effort=None):
    """Invoke one agent on one task, and return what happened.

    Until 0.1.454 nothing in this repository invoked an agent. `run` wrote a
    PROMPT.txt and printed "invoke each agent against its PROMPT.txt", and every
    row this board has ever carried was earned by an operator typing the command
    themselves. The `cli` column reports the `--version` probe, which is how a
    newly installed binary once turned a hand-driven run into a sentence
    claiming the tasks had run non-interactively (corrected at 0.1.452).

    **The working directory is outside this repository, and that is not a
    detail.** An agent started inside the tree reads this repo's maintenance
    CLAUDE.md and behaves like a maintainer of the skill instead of a consumer
    of it — it has the rules, the checkers and the changelog in front of it, and
    the task stops measuring what the task is for. It gets a bare temporary
    directory and whatever the platform installed at its own skill path.
    """
    argv = list(agent.get("drive") or [])
    if not argv:
        return {"verdict": "no driver",
                "detail": f"{agent['id']} declares no `drive` argv in the "
                          f"registry; drive it by hand and score the artifact"}
    # THE SKILL HAS TO BE READABLE, and running outside the repository is what
    # made it not. A CLI driven with `-p` in a temporary directory confines its
    # file access to that directory, so an agent could read SKILL.md — the
    # platform surfaces it — and NOT the `tokens/`, `references/`, `scripts/`
    # and `assets/` beside it. One said so in its own transcript: "blocked from
    # reading … I'll rebuild the palette inside the file", which is precisely
    # what three runs of it did, and the harness recorded three invented
    # palettes as the agent's doing.
    #
    # The flag is declared per platform rather than assumed, and the path is the
    # registry's own install location — the same one a reader would use, so the
    # run reproduces what a user has rather than something only this harness
    # arranges.
    # INSERTED AFTER THE BINARY, never appended. `claude --help` declares
    # `--add-dir <directories...>` variadic, so a flag placed last swallows the
    # prompt that follows it as another directory and the CLI exits in a second
    # with "Input must be provided". Put it first and the platform's own flags
    # terminate it.
    flag = agent.get("drive_skill_flag")
    paths = agent.get("skill_paths") or []
    if flag and paths:
        argv[1:1] = [flag, str(pathlib.Path(paths[0]).expanduser())]
    if model:
        argv += ["--model", model]
    # Effort is passed only through a flag the registry names for this agent;
    # a CLI that has no such flag is not handed one it would reject, and the
    # run records that the level was NOT pinned rather than pretending.
    effort_flag = agent.get("drive_effort_flag")
    effort_pinned = bool(effort and effort_flag)
    if effort_pinned:
        argv += [effort_flag, effort]
    # A CLI that can return its own usage is asked to, through the flag the
    # registry names; the counts are then the API's, which is the only kind
    # trace.py accepts (`--usage` reads a dump, there is no flag to type one).
    usage_flag = agent.get("drive_usage_flag")
    if usage_flag:
        argv += list(usage_flag)
    workdir = pathlib.Path(tempfile.mkdtemp(prefix=f"lumi-conf-{agent['id']}-"))
    try:
        for name in ("PROMPT.txt", "input.md"):
            if (prompt_dir / name).exists():
                shutil.copy2(prompt_dir / name, workdir / name)
        started = time.monotonic()
        try:
            proc = subprocess.run(argv + [task["prompt"]], cwd=workdir,
                                  capture_output=True, timeout=timeout)
            code, out = proc.returncode, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired as expired:
            code, out = None, (expired.stdout or b"") + (expired.stderr or b"")
        except OSError as exc:
            return {"verdict": "could not start", "detail": str(exc)}
        seconds = round(time.monotonic() - started, 1)

        # Bring back whatever the task asked for, plus the transcript. Anything
        # else the agent wrote stays in the temporary directory: the run record
        # is the deliverable and the log, not the agent's scratch.
        produced = [p for p in sorted(workdir.glob(task["deliverable"]))
                    if p.name not in ("PROMPT.txt", "input.md")]
        for p in produced:
            shutil.copy2(p, prompt_dir / p.name)
        (prompt_dir / "transcript.txt").write_bytes(out)
        # THE EXIT CODE IS READ. It was recorded and never looked at, so a CLI
        # that rejected its own arguments — a renamed flag, expired auth, a
        # rate limit — completed in a second having written nothing and was
        # recorded as "driven". `score` then found no deliverable and put an
        # agent-shaped failure on the board for an invocation that never
        # reached the agent.
        #
        # And the agent's own words decide too: the 2026-08-13 incident was
        # visible only in the transcript, where an agent said it could not read
        # the skill. environment_check cannot see the sandbox; this can.
        text = out.decode("utf-8", "replace")
        usage = _usage_from_transcript(text) if usage_flag else None
        blocked = re.search(r"blocked from reading|outside .{0,40}allowed "
                            r"director|cannot (?:read|access) .{0,40}"
                            r"(?:tokens|references)/", text, re.I)
        verdict = ("timeout" if code is None
                   else "environment" if blocked
                   else "driven" if code == 0
                   else "driver failed")
        return {"verdict": verdict,
                "detail": (blocked and "the agent's own transcript says it could "
                           "not read the skill; this run attributes nothing")
                          or (code not in (0, None) and
                              f"the CLI exited {code} after {seconds}s: "
                              f"{text.strip()[-200:]}") or None,
                "exit_code": code, "seconds": seconds,
                "produced": [p.name for p in produced],
                "digest": hashlib.sha256(out).hexdigest(),
                "model": model or "(the CLI's default)",
                # The matrix axis. Recorded as what was PINNED: an effort the
                # CLI could not be told is "(not pinned)", never the requested
                # value, because a board cell is a claim about what ran.
                "effort": effort if effort_pinned else "(not pinned)",
                # The API's own counts, when the CLI returned them; None
                # means "not returned", never zero.
                "usage": usage}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

# What a task's `score` list may name, and the script behind each.
#
# `layout` joins in 0.1.368, and its absence was the hole under this whole
# harness: `inspect_layout.py` is the only instrument here that renders the
# document, and the scoreboard has never run it. A deliverable with overlapping
# text, no part openers and a clamped title scored `pass` on prose and design and
# was recorded as conformant, because the two checkers that ran cannot see a
# rendered page and the one that can was never asked.
# The kind->checker map lives in deliverable_registry (one copy; its
# docstring carries the FM-07 story).
SCORE_KINDS = set(kinds()) | {"recall"}


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


def skill_version() -> str:
    """The version of the skill (and so of its checkers) as installed here."""
    return (ROOT / "SKILL.md").read_text(
        encoding="utf-8").split('version: "')[1].split('"')[0]


def _ver_key(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def cell_spread(fresh: list[dict]) -> tuple[str, str]:
    """-> (cell text, governing verdict) for one task's fresh results.

    IDEA-8's render half. With n>1 the cell names the spread; and when the
    DISAGREEMENT ALIGNS WITH DIFFERENT BUILD VERSIONS — every build has one
    verdict, more than one build, all builds known — the cell says "skill
    changed between builds" and the LATEST build's verdict governs, because
    "the skill improved" and "the agent is flaky" are opposite conclusions
    that a bare UNSTABLE cannot tell apart (the GAP-001 misread: fail rows
    built pre-0.1.380 merged with a pass built at 0.1.433 rendered as agent
    instability). Any conflict NOT explained by builds — same build
    disagreeing, or a build unknown — stays UNSTABLE, which errs toward the
    uncomfortable reading.
    """
    seen = [s["verdict"] for s in fresh]
    worst = "fail" if "fail" in seen else seen[0]
    detail = ", ".join(sorted({f for s in fresh for f in s.get("failed", [])}))
    if len(fresh) > 1 and len(set(seen)) > 1:
        by_build: dict[str | None, set[str]] = {}
        for s in fresh:
            by_build.setdefault(s.get("built_version"), set()).add(s["verdict"])
        aligned = (None not in by_build and len(by_build) > 1
                   and all(len(v) == 1 for v in by_build.values()))
        if aligned:
            builds = sorted((b for b in by_build if b is not None), key=_ver_key)
            latest = builds[-1]
            worst = next(iter(by_build[latest]))
            latest_detail = ", ".join(sorted(
                {f for s in fresh if s.get("built_version") == latest
                 for f in s.get("failed", [])}))
            base = (worst if worst == "pass" or not latest_detail
                    else f"{worst}: {latest_detail}")
            return (base + " · skill changed between builds: "
                    + ", ".join(f"{next(iter(by_build[b]))}@{b}" for b in builds),
                    worst)
        cell = worst if worst == "pass" else (f"{worst}: {detail}" if detail else worst)
        return (cell + f" · {len(fresh)} runs UNSTABLE: "
                + ", ".join(f"{v}×{seen.count(v)}" for v in sorted(set(seen))),
                worst)
    cell = worst if worst == "pass" else (f"{worst}: {detail}" if detail else worst)
    if len(fresh) > 1:
        cell += f" · {len(fresh)} runs, all {worst}"
    return cell, worst


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
    # One implementation, shared with trace.py. Two sha256-of-sorted-json is
    # the `no shadow math` guard's territory, and a fingerprint that differs
    # between callers is worse than none — both sides would report matches.
    return fingerprint.material_hash(material)


def _usage_from_transcript(text: str) -> dict | None:
    """-> {input_tokens, output_tokens} from a JSON transcript, else None.

    Claude Code's `-p --output-format json` ends in one JSON object carrying
    `usage`; the last JSON object in the transcript is read and the two counts
    taken only when both are integers. Anything else is None — a count this
    function cannot read is a count that was not returned."""
    last = text.strip().rfind("\n{")
    candidates = [text.strip()] + ([text.strip()[last + 1:]] if last >= 0 else [])
    for chunk in candidates:
        try:
            doc = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        usage = doc.get("usage") if isinstance(doc, dict) else None
        if not isinstance(usage, dict):
            continue
        i, o = usage.get("input_tokens"), usage.get("output_tokens")
        if all(isinstance(v, int) and not isinstance(v, bool) for v in (i, o)):
            return {"input_tokens": i, "output_tokens": o}
    return None


def _conformance_trace(agent: dict, task: dict, wd: pathlib.Path, record: dict) -> str:
    """Open and close a `source: conformance` trace for one driven task, so
    the matrix board reads real rows. The build phase is the driver's own
    wall clock; model and effort are what the driver recorded; the
    deliverable's verdicts are transcribed by `trace.py close` exactly as for
    a real build. A task with no `storyline` field opens no trace (the schema
    requires one and this harness does not guess), and a drive that produced
    nothing closes none — an unclosed conformance trace is the record of a
    drive that did not finish, which is what the ledger counts."""
    storyline = task.get("storyline")
    if not storyline:
        return "no trace: the task declares no storyline"
    tool = ROOT / "scripts" / "ops" / "trace.py"
    geometry = {"landscape": "16x9", "portrait": "a4"}.get(task.get("geometry", "landscape"), "16x9")
    opened = subprocess.run(
        [sys.executable, str(tool), "open", "--genre", task.get("genre", "internal"),
         "--storyline", storyline, "--entry-path", "B", "--source", "conformance",
         "--geometry", geometry], capture_output=True, text=True, cwd=ROOT)
    if opened.returncode != 0:
        return f"no trace: {opened.stderr.strip()[:120]}"
    tid = opened.stdout.strip()
    produced = [wd / n for n in record.get("produced") or []]
    if record.get("verdict") != "driven" or not produced:
        return f"trace {tid} opened and left open: the drive did not finish"
    argv = [sys.executable, str(tool), "close", "--id", tid,
            "--deliverable", str(produced[0]), "--agent", agent["id"],
            "--phase", "build", str(max(1, int(record.get("seconds") or 1)))]
    if record.get("model") and not str(record["model"]).startswith("("):
        argv += ["--model", record["model"]]
    if record.get("effort") and not str(record["effort"]).startswith("("):
        argv += ["--effort", record["effort"]]
    if isinstance(record.get("usage"), dict):
        usage_path = wd / "usage.json"
        usage_path.write_text(json.dumps(record["usage"]) + "\n", encoding="utf-8")
        argv += ["--usage", str(usage_path)]
    closed = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    if closed.returncode != 0:
        return f"trace {tid} could not close: {closed.stderr.strip()[:120]}"
    return f"trace {tid} closed (source: conformance)"


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
    # Invocation and parsing live in checker_report — one implementation for
    # the four scripts that need them. The POLICY stays here: a checker that
    # graded nothing has not scored the artifact (a `deliverable` glob matching
    # a directory produced exactly that and read as a pass), so an empty or
    # silent report is `unparseable` to this scoreboard.
    run = checker_report.run_checker(kind, path, genre=genre)
    verdicts = checker_report.first_verdicts(run["reports"])
    if not run["spoke"] or not verdicts:
        return {"exit": run["exit"], "verdicts": {}, "unparseable": True}
    return {"exit": run["exit"], "verdicts": verdicts}


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


# The board's generated region. `report --record` replaces what lies between
# these, and nothing else in the file: the narrative paragraphs are written by a
# person and have to survive a refresh. Before this existed the operator pasted
# the rendered output in by hand, which is how "What this table is not" came to
# appear in that file THREE times — the section was re-appended at every refresh
# and nobody diffed a document they had just generated.
BOARD_OPEN = "<!-- generated by run_conformance.py report --record -->"
BOARD_CLOSE = "<!-- end generated -->"


def render_board(record: dict) -> str:
    """The header and the table — the part a person must never retype."""
    return "\n".join(render(record).split("\n## What this table is not")[0].rstrip().split("\n"))


def write_board(record: dict) -> str:
    """Replace the generated region of conformance/CONFORMANCE.md in place."""
    path = ROOT / "conformance" / "CONFORMANCE.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        # Report, never raise. --record's job is the history row; the board is
        # the second half of it, and a missing board must not take the first
        # half down with it (the synthetic trees the record tests build have
        # no board at all).
        return f"note  the board was not written: {exc}"
    if BOARD_OPEN not in text or BOARD_CLOSE not in text:
        return (f"FAIL  {path.name} carries no generated region; add "
                f"{BOARD_OPEN} and {BOARD_CLOSE} around its header and table")
    head, rest = text.split(BOARD_OPEN, 1)
    _, tail = rest.split(BOARD_CLOSE, 1)
    path.write_text(head + BOARD_OPEN + "\n" + render_board(record) + "\n"
                    + BOARD_CLOSE + tail, encoding="utf-8")
    return f"wrote the board table into {path.relative_to(ROOT)}"



def _board_run_version(record: dict) -> str | None:
    """-> the skill version the rendered runs were produced at: from the run
    id when it carries one, else from the newest `instrument_version` in the
    scores. The fallback exists because `results/latest` carries no version
    in its name, and a board rendered from it read "skill 0.1.527" over a run
    scored at 0.1.522 — the exact claim the comment above render() says this
    field exists to stop."""
    m = re.search(r"(\d+\.\d+\.\d+)", str(record.get("run_id") or ""))
    if m:
        return m.group(1)
    found: list[str] = []
    for r in re.findall(r"`([^`]+)`", str(record.get("run_id") or "")):
        f = pathlib.Path(r) / "scores.json"
        if f.exists():
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            found += [str(v["instrument_version"]) for v in doc.values()
                      if isinstance(v, dict) and v.get("instrument_version")]
    return sorted(found, key=_ver_key)[-1] if found else None


def _releases_between(older: str | None, newer: str | None) -> int | None:
    """-> how many CHANGELOG headings separate two versions, or None.

    Counted from the CHANGELOG rather than from arithmetic on the patch number,
    because the distance that matters is how many rule revisions have landed
    since — not how far apart two integers are.
    """
    if not older or not newer:
        return None
    try:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        return None
    versions = re.findall(r"^##\s+(\d+\.\d+\.\d+)", text, re.M)
    if older not in versions or newer not in versions:
        return None
    return abs(versions.index(older) - versions.index(newer))

def _scores_date(runs) -> str | None:
    """-> ISO date of the newest scores.json among the run dirs, or None."""
    import datetime
    stamps = []
    for r in runs:
        f = pathlib.Path(r) / "scores.json"
        if f.exists():
            stamps.append(f.stat().st_mtime)
    if not stamps:
        return None
    return datetime.date.fromtimestamp(max(stamps)).isoformat()


def _findings(runs) -> list[str]:
    """-> one generated line per agent/task that did not pass, naming the
    failed metrics from scores.json. This replaces the hand-written
    narrative that used to sit under the table: at 0.1.522 that prose still
    said "Both agents fail T1-deck" and "Cursor: M2 at 86.0%" under a table
    in which Cursor passed all three, because the table was regenerated and
    the paragraph was not. A sentence derived from the file cannot disagree
    with the table derived from the same file."""
    out = []
    for r in runs:
        f = pathlib.Path(r) / "scores.json"
        if not f.exists():
            continue
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            out.append(f"`{f}` does not parse — nothing below it is a verdict")
            continue
        for key, value in sorted(doc.items()):
            verdict = value.get("verdict", "unscored")
            if verdict == "pass":
                continue
            failed = value.get("failed") or []
            detail = value.get("detail")
            tail = (", ".join(str(x) for x in failed) if failed else
                    (detail or "no metric named"))
            out.append(f"`{key}` · **{verdict}** · {tail}")
    return out


def render(record: dict) -> str:
    # THE HEADER CARRIES BOTH VERSIONS AND THE DISTANCE BETWEEN THEM. It used
    # to name the instrument alone, so a board rendering runs from 0.1.454 sat
    # under the words "skill 0.1.502" — a version it had never measured
    # anything at. That is the same claim `built_version` exists to stop a cell
    # from making, made by the page the cells sit on.
    ran_at = _board_run_version(record)
    behind = _releases_between(ran_at, record["version"])
    # `skill <version>` STAYS, and stays first: it is this file's version stamp
    # and check_version_citations matches `skill {v}` on it. Dropping the word
    # for a better-reading "instrument" would have reddened CI the first time
    # anyone regenerated the board — a trap laid by a cosmetic edit.
    stamp = (f"skill {record['version']}" if behind is None or behind == 0 else
             f"skill {record['version']} · newest run {ran_at} · "
             f"{behind} release{'' if behind == 1 else 's'} behind")
    dated = f" · run {record['run_date']}" if record.get("run_date") else ""
    lines = [f"# LUMI style conformance · {stamp}", "",
             f"Runs {record['run_id']}{dated} · {record['host']} · "
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
    findings = record.get("findings") or []
    lines += ["", "**What did not pass, from the scores file** (generated; a "
              "`pass` row has no line here):", ""]
    if not record.get("run_date"):
        lines += ["* no run named — nothing was scored, so nothing passed either"]
    else:
        lines += [f"* {x}" for x in findings] or ["* nothing — every scored task passed"]
    lines += ["", "*Everything below the generated marker is history of earlier "
              "runs, dated in its own text. The table and the list above are "
              "the only statements about the run named in the header.*"]
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
    ap.add_argument("--task", default=None,
                    help="with run: only this task id. The suite is three tasks "
                         "and one of them is a twelve-page deck, so proving the "
                         "driver works should not cost a deck")
    ap.add_argument("--drive", action="store_true",
                    help="with run: actually invoke each agent, in a temporary "
                         "directory OUTSIDE this repository, instead of writing "
                         "a prompt for a person to invoke by hand")
    ap.add_argument("--model", default=None,
                    help="with run --drive: pin the model and record which one. "
                         "Left off, each CLI picks its own default and the run "
                         "records that it did — a comparison needs the pin, a "
                         "check of what a user actually gets does not")
    ap.add_argument("--effort", choices=("low", "medium", "high"), default=None,
                    help="with run --drive: pin the reasoning effort through the "
                         "agent's `drive_effort_flag` and record it. This is the "
                         "second axis of the model×effort matrix (K1); an agent "
                         "whose registry record names no effort flag records "
                         "the level as not pinned")
    ap.add_argument("--timeout", type=int, default=DRIVE_TIMEOUT,
                    help=f"with run --drive: seconds before one task is "
                         f"abandoned (default {DRIVE_TIMEOUT})")
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
        # A DRIVEN run gets its own dated directory by default, and `latest`
        # becomes a symlink to it. Under the old default every drive wrote
        # into `results/latest`, so a new driver.json (timeout, nothing
        # produced) could sit beside a deck from a previous run in the same
        # directory, and history.json's run_dir pointed at a tree last written
        # on another day. A run id now names one run.
        if runs:
            run_dir = pathlib.Path(runs[0])
        elif args.drive:
            import datetime
            run_dir = RESULTS / f"{skill_version()}-{datetime.date.today().isoformat()}"
        else:
            run_dir = RESULTS / "latest"
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
        driven = skipped = 0
        for a in wanted:
            for t in tasks:
                if CAP_RANK[a["capability"]] < CAP_RANK[t["min_capability"]]:
                    continue
                if args.task and t["id"] != args.task:
                    continue
                wd = run_dir / a["id"] / t["id"]
                if args.drive and wd.exists():
                    # Cleared before driving: whatever is in here afterwards
                    # was produced by THIS drive or by nothing.
                    shutil.rmtree(wd)
                wd.mkdir(parents=True, exist_ok=True)
                (wd / "PROMPT.txt").write_text(t["prompt"], encoding="utf-8")
                if "input" in t:
                    (wd / "input.md").write_text(t["input"], encoding="utf-8")
                if not args.drive:
                    continue
                # PROVEN BEFORE DRIVEN. A run whose agent cannot read the
                # rules produces artifacts that look like the agent's judgement
                # and are not; two such runs were attributed to the agent
                # before anyone read the transcript that said so.
                blocked = environment_check(a)
                if blocked:
                    skipped += 1
                    print(f"  SKIPPED {a['id']} on {t['id']}: {blocked[0]}")
                    (wd / "driver.json").write_text(
                        json.dumps({"verdict": "environment",
                                    "detail": blocked[0]}, indent=2) + "\n",
                        encoding="utf-8")
                    continue
                print(f"  driving {a['id']} on {t['id']} …", flush=True)
                record = drive(a, t, wd, model=args.model, timeout=args.timeout,
                               effort=args.effort)
                (wd / "driver.json").write_text(
                    json.dumps(record, indent=2) + "\n", encoding="utf-8")
                note = _conformance_trace(a, t, wd, record)
                if note:
                    print(f"    {note}")
                driven += record["verdict"] == "driven"
                print(f"    {record['verdict']}"
                      + (f" in {record['seconds']}s, wrote "
                         f"{', '.join(record['produced']) or 'nothing'}"
                         if "seconds" in record else f" — {record.get('detail', '')}"))
        if not args.drive:
            print(f"prepared {run_dir}; invoke each agent against its PROMPT.txt, then "
                  f"`score --run {run_dir}`. `--drive` runs them here instead.")
            return 0
        latest = RESULTS / "latest"
        if run_dir != latest:
            if latest.is_symlink() or latest.exists() and not latest.is_dir():
                latest.unlink()
            if not latest.exists():
                latest.symlink_to(run_dir.name)
        print(f"drove {driven} task(s) into {run_dir}; now `score --run {run_dir}`")
        if not driven and skipped:
            # Agent RESULTS are non-deterministic and must not gate a release.
            # The harness being unable to invoke anything is neither: it is
            # deterministic, operator-fixable, and the condition this release
            # added a function to detect.
            print(f"NOTHING RAN: all {skipped} task(s) were blocked before "
                  f"driving. That is an environment finding, not a result — fix "
                  f"the install path or the drive flag and run again.")
            return 1
        # DRIVING IS NOT SCORING, and this exit code says only that the driver
        # ran. Whether the artifacts pass is `score`'s answer, and it is
        # deliberately not folded in here: agent output is non-deterministic by
        # this file's own opening paragraph, so a release that blocked on it
        # would block on something that is not the release.
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

                # AN INTERRUPTED RUN DOES NOT EARN A VERDICT. The board already
                # says so — 0.1.450 withdrew a recorded `fail` by hand because
                # the agent had been killed mid-run and what was scored was a
                # draft — and until now the rule lived only in a person's
                # judgement. `run --drive` can now produce that situation
                # automatically: a task that hits its timeout is killed while
                # writing, and the half-file it leaves scores exactly like a
                # finished one. The same agent had produced a complete deck for
                # this task in 699s and hit a 1500s ceiling on the next run, so
                # this is not a rare shape.
                #
                # The driver's own record decides, because it is the only thing
                # that knows. A hand-driven task has no driver.json and is
                # scored as it always was.
                driver = task_dir / "driver.json"
                if driver.exists():
                    try:
                        record = json.loads(driver.read_text(encoding="utf-8"))
                    except ValueError as exc:
                        # A process killed while writing can leave a half
                        # driver.json as easily as a half deliverable, and
                        # `record = {}` turned that into the outcome this block
                        # exists to prevent: a draft scored as a result.
                        scores[key] = {
                            "verdict": "not earned",
                            "task_hash": asked_fingerprint(task_dir, task),
                            "detail": f"driver.json does not parse ({exc}); the "
                                      f"driver was very likely killed mid-write"}
                        unscored += 1
                        continue
                    if record.get("verdict") in ("timeout", "could not start",
                                                 "no driver", "environment",
                                                 "driver failed"):
                        scores[key] = {
                            "verdict": "not earned",
                            # The fingerprint goes in like every other entry, or
                            # the freshness check reads a missing hash as a
                            # changed task and the cell prints "stale" — a
                            # timeout reported as a question nobody asked.
                            "task_hash": asked_fingerprint(task_dir, task),
                            "detail": f"the driver reports "
                                      f"{record['verdict']!r}"
                                      + (f" after {record['seconds']}s"
                                         if record.get("seconds") else "")
                                      + " — whatever it left behind is a draft, "
                                        "and a draft is not a result"}
                        unscored += 1
                        continue
                if not produced:
                    # No artifact is NOT a pass. It is the most common real
                    # outcome — an agent that answered in chat instead of
                    # writing a file — and it has to read as a failure to
                    # produce, never as an absent finding.
                    #
                    # UNLESS NOTHING WAS EVER DRIVEN HERE. A hand-driven agent
                    # is one an operator invokes task by task, and the two they
                    # did not reach are not two failures: 0.1.450's board
                    # marked Cursor **fail** on a day it produced a passing
                    # deck, because two prompts it was never given scored as
                    # missing deliverables. The board's own prose already draws
                    # this line for absent AGENTS ("printing the two
                    # identically made the board read as ten pieces of pending
                    # work when only six are") and the roll-up did not draw it
                    # for absent RUNS. An untouched directory — the prompt this
                    # harness wrote and nothing else — is the evidence.
                    left = {f.name for f in task_dir.iterdir()}
                    untouched = not (left - {"PROMPT.txt", "input.md"})
                    scores[key] = {
                        "verdict": "not attempted" if untouched
                        else "no deliverable",
                        "task_hash": asked_fingerprint(task_dir, task),
                        "detail": ("the prompt was never driven here"
                                   if untouched
                                   else f"nothing matching {task['deliverable']}")}
                    unscored += 1
                    continue
                target = produced[0]
                # The run directory is wherever the operator put it, which is
                # usually outside this repository; relative_to() raises there.
                try:
                    shown = str(target.relative_to(ROOT))
                except ValueError:
                    shown = str(target)
                # IDEA-8's record half: task_hash pins the question;
                # these two pin the ruler and the artifact's own vintage. The
                # colophon regex reads the "built with lumi-style X.Y.Z" line
                # a LUMI deliverable carries; absent (markdown answers), the
                # build vintage is honestly unknown.
                built_v = fingerprint.version_in(
                    target.read_text(encoding="utf-8", errors="replace"))
                entry: dict[str, Any] = {"artifact": shown,
                                         "task_hash": asked_fingerprint(task_dir, task),
                                         "instrument_version": skill_version(),
                                         "built_version": built_v}
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
        print(f"\n{len(scores) - unscored} scored, {unscored} not scored "
              f"-> {run_dir / 'scores.json'}")
        return 1 if any(s["verdict"] != "pass" for s in scores.values()) else 0

    # report
    version = skill_version()
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
            # THE SPREAD, beside the verdict — and since IDEA-8, a
            # conflict that aligns with different build versions is named as
            # the skill changing rather than the agent wobbling (cell_spread's
            # docstring carries the argument).
            cell, worst = cell_spread(fresh)
            cells[t["id"]] = cell
            verdicts.append(worst)
        if verdicts:
            # A task nobody drove is not a task the agent failed. It drops out
            # of the roll-up entirely, and an agent that passed everything it
            # was actually given reads `partial` — the pass is real, the
            # coverage is not complete, and both facts survive.
            # "not earned" joins "not attempted" here. Both mean the same
            # thing to a roll-up — no verdict was produced — and folding either
            # into `fail` is how a board reports a timeout as a model's defect.
            judged = [v for v in verdicts
                      if v not in ("not attempted", "not earned")]
            if not judged:
                verdict = "not run"
            elif all(v == "pass" for v in judged):
                verdict = "pass" if len(judged) == len(verdicts) else \
                    f"partial: {len(judged)} of {len(verdicts)} driven, all pass"
            elif any(v == "stale" for v in judged) and \
                    not any(v == "fail" for v in judged):
                verdict = "stale"
            else:
                verdict = "fail"
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
              # The date the scores were written, read from the file, never
              # typed: a board without a date under a table of verdicts is a
              # board whose prose can narrate a different run than its table
              # (it did, for six days, at 0.1.522).
              "run_date": _scores_date(runs),
              "findings": _findings(runs),
              "host": f"{sys.platform}", "agents": len(agents),
              "detected": sum(1 for v in probed.values() if v[0]),
              "repeat": max((r["runs"] for r in rows), default=0),
              "structural": sum(1 for r in rows if r["verdict"] == "cannot be probed"),
              "task_ids": [t["id"] for t in tasks], "rows": rows}
    print(render(record))

    if args.record:
        print(write_board(record))
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
            per_built: dict[str, dict[str, str]] = {}
            instruments: set[str] = set()
            for key, value in scored_doc.items():
                agent_id, _, task_id = key.partition("/")
                per_agent.setdefault(agent_id, {})[task_id] = value.get(
                    "verdict", "unscored")
                if value.get("built_version"):
                    per_built.setdefault(agent_id, {})[task_id] = value["built_version"]
                if value.get("instrument_version"):
                    instruments.add(value["instrument_version"])
            for agent_id, task_verdicts in sorted(per_agent.items()):
                row = {"skill_version": version, "agent": agent_id,
                       "date": datetime.date.today().isoformat(),
                       "run_dir": str(name), "tasks": task_verdicts,
                       "scores_sha256": digest}
                # IDEA-8: the ruler and the artifact vintages, when the
                # scores carry them (older scores.json rows predate the
                # fields and stay honestly silent).
                if instruments:
                    row["instrument_version"] = sorted(instruments, key=_ver_key)[-1]
                if per_built.get(agent_id):
                    row["built"] = per_built[agent_id]
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
