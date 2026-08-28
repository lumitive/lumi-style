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
import os
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
import signal
import subprocess
import sys
import sys as _bs_sys  # noqa: E402
import tempfile
import threading
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
import agent_capability  # noqa: E402
import checker_report  # noqa: E402
import eval_corpus  # noqa: E402
import fingerprint  # noqa: E402
import gating  # noqa: E402
import history  # noqa: E402
import output_dir  # noqa: E402
import platform_registry  # noqa: E402
import trace_schema  # noqa: E402
import versioning  # noqa: E402
from check_prose import GENRES  # noqa: E402
from deliverable_registry import kinds  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
TASKS = ROOT / "conformance" / "tasks"
IN_REPO_RESULTS = ROOT / "conformance" / "results"


def _results_root() -> pathlib.Path:
    """Where a run's directories go: the operator's deliverable folder.

    Multi-agent verification produces documents a person reads — decks,
    rewrites, transcripts — and they belong beside the other deliverables
    rather than inside a checkout, which is where they sat until 0.1.542
    (owner directive). `output_dir.py` resolves that folder portably and is
    the only thing in this package allowed to name it, so this asks rather
    than restating the path.

    **It never CREATES the deliverable folder.** Making a directory in
    someone's home without being asked is the 2026-08-09 directive
    `output_dir.py --create` exists for, so a machine that has not run
    `--create` keeps its runs inside the checkout and the run says which of
    the two it chose. `LUMI_CONFORMANCE_RESULTS` overrides both, for a test
    or an operator who wants them elsewhere.
    """
    override = os.environ.get("LUMI_CONFORMANCE_RESULTS")
    if override:
        return pathlib.Path(override).expanduser()
    try:
        deliverables = output_dir.output_dir()
    except output_dir.Unresolvable:
        return IN_REPO_RESULTS
    return deliverables / "_conformance" if deliverables.is_dir() else IN_REPO_RESULTS


RESULTS = _results_root()
CAP_RANK = {"prompt": 0, "files": 1, "full": 2}

# --- the budget -------------------------------------------------------------
#
# **A fixed wall clock is the wrong instrument, and this repository has the
# measurement.** `DRIVE_TIMEOUT = 1800` killed Hermes on 2026-08-21 while it was
# still working: its deck's mtime is six seconds before the driver record's, and
# that deck still fails `title_two_lines` today — it was inside the repair loop
# for the third gate when the SIGKILL landed. Nothing about thirty minutes was a
# statement about that run; it was a number somebody wrote.
#
# What replaces it is not a bigger number. A run gets a BASE budget outright,
# and past that it continues only while it keeps showing it is alive, up to a
# HARD CAP that renewal can never pass. Three consequences, all of them the
# point: a run that finishes early is unaffected, a run that is still working at
# the base budget gets more, and a run that has genuinely stopped is collected
# without waiting for a clock nobody set for it.
#
# `base` is deliberately unshortenable. A stall is only ever grounds for ending
# a run that has ALREADY spent its base budget, because silence inside it is
# normal — an agent composing one long message emits nothing for minutes, and a
# stall detector that fired there would kill the healthy case to catch the sick
# one.
DRIVE_BASE_BUDGET = 1800
# No sign of life for this long, after the base budget is spent, is a stall.
# Five minutes is generous against the finest-grained signal a CLI offers
# (token deltas, below) and coarse against the crudest (the artifact's mtime).
DRIVE_IDLE_GRACE = 300
# The backstop. Renewal cannot pass it, so an agent that loops forever while
# emitting events still ends.
DRIVE_HARD_CAP = 3600
# SIGTERM, then this long to flush, then SIGKILL. The old code sent SIGKILL
# outright, so the CLI never wrote its result object and its own child browser
# was orphaned.
DRIVE_TERM_GRACE = 15


def _is_delta(line: bytes) -> bool:
    """Is this NDJSON line a token-level chunk rather than a record?

    Both shapes here were read off a real invocation rather than reasoned about
    (convention 15): Claude Code spells a partial `{"type":"stream_event", ...}`
    and Cursor spells it `{"type":"thinking","subtype":"delta", ...}`.

    They are dropped from the stored transcript and counted as liveness. Nothing
    is lost by dropping them — both CLIs also emit the COMPLETED message as its
    own event, so the text a reader wants is in the transcript either way, and
    keeping the deltas would put roughly one JSON line per output token into a
    file whose job is to be read by a person.
    """
    if not line.startswith(b"{") or len(line) > 65536:
        return False
    try:
        doc = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    return isinstance(doc, dict) and (doc.get("type") == "stream_event"
                                      or doc.get("subtype") == "delta")


def _newest_mtime(globs) -> float:
    """-> the newest mtime among files matching `globs`, or 0.0.

    The progress signal for a CLI with no event stream. Coarse on purpose: it
    ticks when the agent writes the thing it was asked for, which is the one
    piece of evidence available from outside a process that reports nothing.
    """
    newest = 0.0
    for root, pattern in globs:
        try:
            for f in root.glob(pattern):
                if f.is_file():
                    newest = max(newest, f.stat().st_mtime)
        except OSError:
            continue
    return newest


def _run_with_budget(argv, cwd, base, hard_cap, idle_grace, watch=(),
                     signal_kind="none", poll=1.0):
    """Run `argv`, renewing its budget while it shows signs of life.

    -> (exit code or None if it was collected, transcript bytes, a record of
    how the budget went).

    The signs, in the order of how much they can tell you:

    * **the event stream** — every line the CLI writes, deltas included. A CLI
      told `--output-format stream-json` reports each tool call and each token
      chunk, so silence here really is silence.
    * **the artifact** — the mtime of anything matching `watch`. All that is
      left for a CLI that streams nothing; it ticks per file write.
    * **neither** — the base budget, and nothing renews it.

    Two reader threads rather than `select`: the child's stdout and stderr are
    both pipes, and a single-threaded reader that drains one while the other
    fills deadlocks on the full pipe. `capture_output=True` had no such problem
    because it never looked until the process was over, which is exactly the
    property being given up here.
    """
    proc = subprocess.Popen(argv, cwd=str(cwd), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                            # ITS OWN PROCESS GROUP, so the whole tree can be
                            # signalled. These CLIs start browsers and language
                            # servers; killing the parent alone left them.
                            start_new_session=True)
    started = time.monotonic()
    kept: list[bytes] = []
    # None until something happens, NOT the start time. Seeding it with the
    # start would make the run's floor `idle_grace` rather than `base` — with a
    # base shorter than the grace, a process that emitted nothing at all would
    # still be waited on for the whole grace, which is the opposite of the rule.
    live: list[float | None] = [None]
    events = [0]
    lock = threading.Lock()

    def reader(stream):
        for line in iter(stream.readline, b""):
            with lock:
                live[0] = time.monotonic()
                events[0] += 1
                if not _is_delta(line.rstrip(b"\n")):
                    kept.append(line)
        stream.close()

    threads = [threading.Thread(target=reader, args=(s,), daemon=True)
               for s in (proc.stdout, proc.stderr)]
    for t in threads:
        t.start()

    artifact = _newest_mtime(watch) if watch else 0.0
    ended = "exit"
    while True:
        code = proc.poll()
        if code is not None:
            break
        now = time.monotonic()
        if watch:
            seen = _newest_mtime(watch)
            if seen > artifact:
                artifact = seen
                with lock:
                    live[0] = now
                    events[0] += 1
        with lock:
            last = live[0]
        # RENEWAL, AND IT ONLY EVER EXTENDS. The base is the floor — a quiet
        # first minute cannot pull the limit backwards — and the hard cap is
        # the ceiling, which nothing can push past.
        limit = started + base
        if last is not None:
            limit = max(limit, last + idle_grace)
        limit = min(limit, started + hard_cap)
        if now >= limit:
            ended = "hard cap" if now >= started + hard_cap else "stall"
            _collect(proc)
            code = None
            break
        time.sleep(poll)

    for t in threads:
        t.join(timeout=DRIVE_TERM_GRACE)
    if code is None:
        proc.poll()
    with lock:
        record = {"base": base, "hard_cap": hard_cap, "idle_grace": idle_grace,
                  "events": events[0], "ended": ended,
                  "signal": signal_kind,
                  "spent": round(time.monotonic() - started, 1)}
    return code, b"".join(kept), record


def _collect(proc) -> None:
    """End a process and its children: SIGTERM the group, then SIGKILL it.

    The grace matters. A CLI signalled with SIGKILL never writes its result
    object, so a run collected at its budget lost the usage counts, the model it
    actually ran, and whatever it was about to say about why it was slow — the
    whole record of the run this harness exists to keep.
    """
    for sig, wait in ((signal.SIGTERM, DRIVE_TERM_GRACE), (signal.SIGKILL, 5)):
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except (OSError, ProcessLookupError):
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


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


def _per_agent(values, flag: str, known: set[str],
               allowed: tuple[str, ...] | None = None) -> tuple[str | None, dict]:
    """-> (the value for every agent, {agent id: its own value}).

    `x` sets the default; `agent=x` sets one agent's. Both may appear.

    A horse race pins a different model per CLI — `opus`, `cursor-grok-4.6`,
    an Anthropic id through Hermes — and one global flag could not say that, so
    three agents had to be driven in three invocations and the concurrency
    added in 0.1.556 had nothing to do. Every id has to resolve, on the same
    reasoning as `--agent`: a typo that silently pins nobody is the failure
    mode `--effort` already produced once, reported as a level that was never
    applied.
    """
    default: str | None = None
    per: dict[str, str] = {}
    for raw in values or []:
        agent, sep, value = str(raw).partition("=")
        if not sep:
            agent, value = "", raw
        if allowed and value not in allowed:
            # WHAT THIS TUPLE IS, said out loud since 0.1.637. It is what a
            # TRACE can record, not what a CLI accepts: Hermes takes eight
            # levels and this harness can store five, so `--reasoning ultra` is
            # refusable here while being perfectly good on the command line.
            # Whether the CLI accepts a level is `agent_capability`'s question
            # and is asked separately, per agent, before the run starts.
            sys.exit(f"FAIL  {flag} {raw!r}: {value!r} is not one of "
                     + "|".join(allowed)
                     + (" — the levels a trace can record, which is a smaller "
                        "question than what a CLI accepts"
                        if flag == "--effort" else ""))
        if not agent:
            default = value
        elif agent not in known:
            sys.exit(f"FAIL  {flag} {raw!r}: no platform in the registry with "
                     f"id {agent!r}")
        else:
            per[agent] = value
    return default, per


def _artifact_roots(agent: dict) -> list[pathlib.Path]:
    """-> the places outside the working directory where a deliverable turns up.

    One list, two readers, and they must not diverge: `_misplaced` searches
    these AFTER the run to say where the file went, and the budget watches them
    DURING it to say whether the agent is still writing. A driver that renewed
    against one set and reported against another would report a file it had
    never counted as progress.

    Bounded and never recursive, for the reason `_misplaced` gives at length.
    """
    roots: list[pathlib.Path] = [pathlib.Path.home(), ROOT]
    for sp in agent.get("skill_paths") or []:
        if "<" in sp:
            continue
        roots.append(pathlib.Path(sp).expanduser())
    return roots


def _misplaced(agent: dict, task: dict, since: float,
               transcript: str = "") -> list[str]:
    """-> paths of deliverable-shaped files written OUTSIDE the working
    directory during this run — the one the AGENT NAMED first, then the rest
    newest-first.

    THE AGENT'S OWN WORD OUTRANKS THE CLOCK, and the cost of the other order is
    measured. Three agents were driven in parallel on 2026-08-21, all of them
    able to write to HOME and to the checkout; the sweep sorted candidates by
    mtime and took the newest, so Hermes's record cited a deck at the
    repository root that Hermes had not written — its transcript names
    `~/deck.en.html` and nothing else. That file was copied into
    Hermes's run record, scored as Hermes's, reported to the owner as Hermes's,
    and she reviewed another agent's cover page believing it was this one. The
    real artifact passed every gate; the impostor failed two.

    A path the transcript names is evidence of authorship. A path that merely
    appeared during the window is a coincidence with a timestamp, which is all
    this ever had.

    Bounded on purpose. It looks in the three places a confused agent actually
    writes — the user's home, the roots this platform declares as its skill
    install, and this package's own root — and never recursively, because a
    sweep that walks a filesystem would find every file anyone has ever named
    `answers.md` and report the run's own history back to it. Anything it
    misses stays reported as "wrote nothing", which is the honest floor.

    NEVER USED FOR THE BOARD'S VERDICT — and it IS read once, so the flat
    "never used to score" this said was wrong in the one place it mattered.
    `score` globs the task directory and never recurses, so a misplaced file
    sitting in `misplaced/` cannot reach a cell; that is the claim, and
    `drive()`'s comment carries the argument for it. But `_conformance_trace`
    falls back to the misplaced path when nothing else was produced, because a
    trace that records what a run actually built is worth more than a trace
    left open — and a reader who took the old sentence at face value would
    have believed no code path touched this list. Two different questions, and
    the docstring answered only one of them.
    """
    roots = _artifact_roots(agent)
    seen: set[pathlib.Path] = set()
    hits: list[tuple[float, pathlib.Path]] = []
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            candidates = sorted(root.glob(task["deliverable"]))
        except OSError:
            continue
        for f in candidates:
            if f.name in ("PROMPT.txt", "input.md") or not f.is_file():
                continue
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            # A second of slack: the run's own start is recorded before the
            # process is spawned, and filesystem timestamps are coarse.
            if mtime >= since - 1:
                hits.append((mtime, f))
    hits.sort(reverse=True)
    paths = [str(f) for _, f in hits]
    # The agent said where it wrote. If one of the candidates is that path, it
    # goes first and everything else is a bystander.
    named = [p for p in paths if p in transcript]
    return named + [p for p in paths if p not in named]


def drive(agent, task, prompt_dir, model=None, base=DRIVE_BASE_BUDGET,
          effort=None, hard_cap=DRIVE_HARD_CAP):
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
    # SOME CLIS HAVE NO EFFORT FLAG BECAUSE THE EFFORT IS THE MODEL. Cursor
    # ships Grok 4.6 as `cursor-grok-4.6-low`, `-medium`, `-high`: one model id
    # per level, so a separate flag would have nothing to set. Declaring the
    # template lets such a platform pin BOTH axes and record both, instead of
    # recording three different models at "(not pinned)" effort and putting a
    # deliberate comparison into the matrix's unknown column.
    effort_template = agent.get("drive_effort_in_model")
    effort_flag = agent.get("drive_effort_flag")
    # ASKED BEFORE THE BUDGET IS SPENT, not by the CLI afterwards. Until 0.1.637
    # nothing compared a pin to what the platform actually offers: `--effort max`
    # against Cursor composed `cursor-grok-4.6-max`, an id that does not exist,
    # and the run failed after the working directory had been built. THAT case
    # is caught by `validate_pin` below, against the recorded vocabulary — this
    # line catches the narrower one, a level the CLI's own declared list
    # excludes, and a review found both this comment and the module's docstring
    # crediting it with the catch it does not make.
    refusal = effort and agent_capability.effort_refusal(agent, effort)
    if refusal:
        return {"verdict": "driver refused", "detail": refusal}
    # AN EFFORT THAT CANNOT BE APPLIED IS AN ERROR, NOT A FOOTNOTE. An agent
    # that spells effort inside its model id needs BOTH halves; given only
    # `--effort`, the old code composed nothing, pinned nothing, and recorded
    # "(not pinned)" — honest in the record and invisible on the console. A
    # whole comparison round was reported as "Cursor at high effort" when Cursor
    # had run on the server's default model at the server's default level, and
    # the matrix row it was meant to fill was silently dropped.
    if effort and effort_template and not model:
        # RETURNED, NOT `sys.exit`. This is called from a driver THREAD, and
        # `threading.excepthook` ignores SystemExit by design — so the refusal
        # written to stop "a whole comparison round reported as Cursor at high
        # effort" printed nothing at all, incremented neither `driven` nor
        # `skipped`, and the run reported `drove 0 task(s)` and exited 0.
        return {"verdict": "driver refused",
                "detail": (f"--effort {effort} was given, but {agent['id']} "
                           f"composes effort into its model id "
                           f"({effort_template!r}) and no --model was given, so "
                           f"neither axis can be pinned. Pass --model as well, "
                           f"or drop --effort and accept the CLI's defaults.")}
    model, effort_pinned = agent_capability.compose_model(agent, model, effort)
    # THE LEVEL THE ID ALREADY CARRIES IS THE LEVEL THAT RAN. A model pinned as
    # `cursor-grok-4.6-high` with no `--effort` recorded "(not pinned)" and left
    # the trace's effort null — so two traces sat in a cell of their own beside
    # ten identical ones that had been given both halves. The id says `high`;
    # recording `high` is reading it, not guessing.
    if not effort_pinned:
        carried = agent_capability.effort_in_model(agent, model)
        if carried:
            effort, effort_pinned = carried, True
    # THE PIN ITSELF, against the vocabulary the CLI last answered with. Three
    # states: only a recorded vocabulary can refuse, and an agent nobody has
    # probed is UNVALIDATED — said out loud, because "checked and fine" and
    # "never checked" printed the same nothing until 0.1.640.
    pin_state, why = agent_capability.validate_pin(agent, model, ROOT)
    if pin_state == agent_capability.REFUSED:
        return {"verdict": "driver refused", "detail": why}
    if pin_state == agent_capability.UNVALIDATED:
        print(f"  note  {why}", flush=True)
    if model:
        argv += ["--model", model]
    # Effort is otherwise passed only through a flag the registry names for this
    # agent; a CLI that has no such flag is not handed one it would reject, and
    # the run records that the level was NOT pinned rather than pretending.
    if effort_pinned and effort_flag and not effort_template:
        argv += [effort_flag, effort]
    # A CLI that can return its own usage is asked to, through the flag the
    # registry names; the counts are then the API's, which is the only kind
    # trace.py accepts (`--usage` reads a dump, there is no flag to type one).
    #
    # STREAMING IS THE SAME FLAG ASKED FOR MORE. `--output-format stream-json`
    # ends in the identical result object `json` returns, so a streaming CLI
    # reports its usage exactly as before AND reports progress while it works,
    # which is what the budget above needs to renew against. The two are
    # mutually exclusive on the command line — a CLI cannot be told both output
    # formats — so the registry declares whichever it supports and the stream
    # wins when both are present.
    stream_flag = agent.get("drive_stream_flag")
    usage_flag = agent.get("drive_usage_flag")
    if stream_flag:
        argv += list(stream_flag)
    elif usage_flag:
        argv += list(usage_flag)
    # SOME CLIS REPORT USAGE TO A FILE, NOT TO THE TRANSCRIPT. Hermes writes
    # `--usage-file <path>` and prints nothing about tokens, so the transcript
    # reader found none and its cells carried quality without cost — a clean
    # eight-page deck with no row on the efficiency board. The flag is declared
    # per platform like every other, and the file is written inside the working
    # directory so it dies with it.
    usage_file_flag = agent.get("drive_usage_file_flag")
    usage_path = None
    # The prompt is appended LAST, so a CLI that takes it as the VALUE of a flag
    # needs that flag put here rather than in the registry's `drive` argv — every
    # optional flag above would otherwise land between them and be eaten as the
    # prompt. Gemini is the case: `-p <prompt>` is its only non-interactive mode,
    # and `gemini … -p --model gemini-2.5-flash <prompt>` sends the model NAME as
    # the prompt and leaves the real one as an interactive-mode positional. An
    # agent whose prompt is a positional (Claude Code, Cursor) declares nothing
    # and is unaffected. Same lesson as `drive_skill_flag`'s placement note
    # above: where a flag sits is part of the flag.
    # The working directory is made HERE, before the prompt flag, because the
    # usage-file flag needs a path inside it and every flag has to be placed
    # before the prompt that trails the argv. Appending it after cost Hermes a
    # whole matrix cell: it received `-z --usage-file <path>` and read the flag
    # name as its prompt, exiting in 0.4s. That is precisely the failure
    # `drive_prompt_flag` exists to prevent, made by the code that implements
    # it — where a flag sits is part of the flag, and the rule binds the driver
    # as much as the registry.
    workdir = pathlib.Path(tempfile.mkdtemp(prefix=f"lumi-conf-{agent['id']}-"))
    if usage_file_flag:
        usage_path = workdir / "cli-usage.json"
        argv += [usage_file_flag, str(usage_path)]
    prompt_flag = agent.get("drive_prompt_flag")
    if prompt_flag:
        argv.append(prompt_flag)
    try:
        for name in ("PROMPT.txt", "input.md"):
            if (prompt_dir / name).exists():
                shutil.copy2(prompt_dir / name, workdir / name)
        started = time.monotonic()
        # Wall clock too: the misplaced-write sweep compares mtimes, and a
        # monotonic clock has no relationship to a file's timestamp.
        started_wall = time.time()
        # WHAT THIS RUN CAN SEE OF ITS OWN PROGRESS, decided here rather than
        # assumed. A streaming CLI is watched through its events. One that
        # streams nothing is watched through the artifact — the same places
        # `_misplaced` looks, because an agent that writes its deck to HOME is
        # still visibly working, and Hermes is precisely that agent. A CLI with
        # neither gets the base budget and the record says so, which is better
        # than a renewal rule quietly doing nothing.
        watch: list[tuple[pathlib.Path, str]] = [(workdir, task["deliverable"]),
                                                 (prompt_dir, task["deliverable"])]
        if not stream_flag:
            for root in _artifact_roots(agent):
                watch.append((root, task["deliverable"]))
        signal_kind = "stream" if stream_flag else "artifact"
        try:
            # stdin from /dev/null: without it Claude Code waits three seconds
            # for input that is never coming and then warns about it, and the
            # warning lands in the transcript after the JSON result. Its own
            # message names this fix.
            code, out, budget = _run_with_budget(
                argv + [task["prompt"]], workdir, base, hard_cap,
                DRIVE_IDLE_GRACE, watch=tuple(watch), signal_kind=signal_kind)
        except OSError as exc:
            return {"verdict": "could not start", "detail": str(exc)}
        seconds = round(time.monotonic() - started, 1)

        # Bring back whatever the task asked for, plus the transcript. Anything
        # else the agent wrote stays in the temporary directory: the run record
        # is the deliverable and the log, not the agent's scratch.
        text = out.decode("utf-8", "replace")
        produced = [p for p in sorted(workdir.glob(task["deliverable"]))
                    if p.name not in ("PROMPT.txt", "input.md")]
        # THE RUN'S OWN FOLDER COUNTS TOO, and one agent found it by reasoning
        # rather than by accident: told to write "in the working directory" and
        # unable to see the driver's cwd, Hermes looked for where `input.md`
        # lives and wrote beside it — which is this folder, because the driver
        # leaves a copy of the input here as well as in the working directory.
        # Its transcript says exactly that, and it is a better reading of the
        # instruction than the driver's own assumption deserves.
        #
        # It is also where the driver is about to COPY the artifact, so an
        # agent that writes here directly has met the same requirement by a
        # shorter route. Scoring it is not a favour: `score` globs this
        # directory, so before this the file was scored `pass` while the
        # driver record beside it said `produced: []` — two files in one
        # directory telling a reader different stories.
        relocated = []
        if not produced:
            relocated = [p for p in sorted(prompt_dir.glob(task["deliverable"]))
                         if p.name not in ("PROMPT.txt", "input.md",
                                           "transcript.txt", "driver.json")]
            produced = relocated
        # WHERE ELSE IT MIGHT HAVE LANDED. "Wrote nothing" and "wrote it
        # somewhere this harness does not look" are different findings, and
        # until 0.1.542 the second was recorded as the first. Two agents have
        # now produced the second: one wrote its deck into the installed skill
        # directory believing it was the working directory, and Hermes writes
        # every file to the user's HOME whatever cwd the driver starts it in —
        # `--in` and `--no-restore-cwd` do not move it, and a prompt naming an
        # absolute path does. The cost of calling that "no deliverable" is
        # measured: Hermes's misplaced T1 deck passes check_design,
        # check_prose AND inspect_layout --deliverable with no failure at all,
        # and the board recorded it as an agent that wrote nothing.
        #
        # The file is NAMED and never copied in and scored. Scoring it would
        # launder a run that did not meet the task's own instruction ("write
        # the file to <name> in the working directory") into a pass, and
        # whether missing that instruction is the agent's defect or this
        # harness's assumption is not something a scoreboard should decide
        # silently. See GAP-022.
        misplaced = (_misplaced(agent, task, started_wall, text)
                     if not produced else [])
        # THE RECORD KEEPS IT EVEN THOUGH THE SCORE DOES NOT. Not copying it in
        # at all left a run directory holding a transcript, a driver record and
        # no deliverable, so the person reviewing the run could not find the
        # thing the run produced — the owner looked for one and reported the
        # absence as a bug, correctly. `misplaced/` is a SUBdirectory: the
        # scorer globs `<task dir>/<deliverable>` without recursing, so the file
        # is one `ls` away from a reviewer and still invisible to the score.
        # Both halves matter — scoring it would launder a run that missed the
        # task's own instruction, and hiding it wastes the artifact.
        for src in misplaced[:1]:
            keep = prompt_dir / "misplaced"
            try:
                keep.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, keep / pathlib.Path(src).name)
            except OSError as exc:
                print(f"    could not keep the misplaced artifact: {exc}")
        for p in produced:
            if p.parent != prompt_dir:
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
        usage = (_usage_from_transcript(text)
                 if (usage_flag or stream_flag) else None)
        if usage is None and usage_path is not None:
            usage = _usage_from_file(usage_path)
        blocked = re.search(r"blocked from reading|outside .{0,40}allowed "
                            r"director|cannot (?:read|access) .{0,40}"
                            r"(?:tokens|references)/", text, re.I)
        # A COLLECTED RUN IS NOT A HUNG ONE ANY MORE, so it stops being called
        # one word. `stall` is a run that showed no sign of life after its base
        # budget; `over budget` is one that was still moving when the hard cap
        # arrived. The board treats both as failures — they are — but a reader
        # asking "was it stuck or was it slow" now has the answer in the
        # verdict rather than having to reason from a duration.
        verdict = ("stall" if code is None and budget["ended"] == "stall"
                   else "over budget" if code is None
                   else "environment" if blocked
                   else "driver failed" if code != 0
                   # A run that finished and put the artifact somewhere else is
                   # not a run that produced nothing, and it is not a pass
                   # either. It gets its own word so the board can stop calling
                   # it either of them.
                   else "misplaced" if misplaced
                   else "driven")
        return {"verdict": verdict,
                # THE DETAIL FOLLOWS THE VERDICT'S OWN ORDER. It did not:
                # `timeout` was decided first and described last, so a run
                # collected at its budget that had also written its file
                # somewhere odd was recorded `verdict: timeout` with a detail
                # explaining a misplaced artifact. That is what Hermes's
                # 2026-08-21 record says, and reading it tells you neither
                # thing.
                "detail": (code is None and
                           f"collected after {seconds}s: {budget['ended']} "
                           f"(base {budget['base']}s, hard cap "
                           f"{budget['hard_cap']}s, {budget['events']} sign(s) "
                           f"of life via {budget['signal']}); the CLI was sent "
                           f"SIGTERM first, so whatever it flushed is above")
                          or (blocked and "the agent's own transcript says it could "
                              "not read the skill; this run attributes nothing")
                          or (code not in (0, None) and
                              f"the CLI exited {code} after {seconds}s: "
                              f"{text.strip()[-200:]}")
                          or (misplaced and
                              f"the run wrote no {task['deliverable']} in its "
                              f"working directory, and a file matching it "
                              f"appeared at {misplaced[0]} while it ran; "
                              f"nothing here is scored from that file")
                          or (relocated and
                              f"written into the run's own folder rather than "
                              f"the working directory, which is where the "
                              f"driver copies it to anyway: "
                              f"{', '.join(p.name for p in relocated)}")
                          or None,
                "exit_code": code, "seconds": seconds, "budget": budget,
                "produced": [p.name for p in produced],
                "misplaced": misplaced,
                "digest": hashlib.sha256(out).hexdigest(),
                # WHAT WAS PINNED. `--model x` is a request, and this is it.
                "model": model or "(the CLI's default)",
                # WHETHER THE REQUEST WAS CHECKED AGAINST A VOCABULARY. The
                # third state went to the console and nowhere else, so one
                # scroll later a pin validated against a recorded vocabulary
                # and one never checkable read the same on the board.
                "pin_state": pin_state,
                # WHAT ACTUALLY RAN, read out of the CLI's own stream. The two
                # are different facts and only the first was kept, so a board
                # cell said "(the CLI's default)" over a run whose model nobody
                # could name afterwards — on a board whose argument is that a
                # cell states what produced it. None when the CLI does not say.
                "model_ran": _model_from_transcript(text),
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


def _history_rows() -> tuple[list, str | None]:
    """-> (rows, why they could not be read). Never both empty-and-fine.

    The reading moved to `scripts/lib/history.py` at 0.1.636, because this
    function's discipline was the careful one and every other reader of that
    file had its own — including two more in THIS file, the `validate` command
    and the `record` path, and `record` WRITES. The seam stays because it is
    this file's name for the operation, not because anything patches it: a
    review checked, and nothing does.
    """
    return history.read_rows(ROOT)


def _rows_for(rows: list, run_dir: pathlib.Path) -> list[dict]:
    """-> the history rows describing this run directory, spelling aside.

    RESOLVED, not string-compared. `_portable` collapses `$HOME` to `~` and
    nothing else, so the same directory recorded absolutely and given
    relatively read as two — and `history.json` holds thirteen different
    spellings across its rows, some `~`-prefixed and some relative. Passing
    this function the path in the exact form the file records was the case that
    found nothing.

    A RELATIVE row is relative to ROOT, not to the process's directory: the
    recorded ones (`conformance/results/latest`) were written from the
    repository root and `score` may be run from anywhere.
    """
    def resolved(text: str) -> pathlib.Path | None:
        try:
            path = pathlib.Path(text).expanduser()
            if not path.is_absolute():
                path = ROOT / path
            return path.resolve()
        except (OSError, RuntimeError, ValueError):
            # expanduser() raises RuntimeError on `~nosuchuser`, resolve()
            # raises ValueError on an embedded NUL, and the fallback that was
            # written for "a path this machine cannot resolve" caught neither.
            return None

    here = resolved(str(run_dir))
    out = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("run_dir"):
            continue
        there = resolved(str(row["run_dir"]))
        if here is not None and there == here:
            out.append(row)
        elif here is None and _portable(str(row["run_dir"])) == _portable(str(run_dir)):
            out.append(row)
    return out


def _pin_guard(run_dir: pathlib.Path) -> list[str]:
    """Read BEFORE `scores.json` is rewritten; keep the bytes; say what happens.

    `report --record` writes `scores_sha256` into every history row, and the
    code that does it says why: the run directory lives outside this repository
    and is gitignored, so **the digest is the whole of what makes a row
    evidence rather than an assertion**. Re-scoring rewrites the file and every
    pinned digest silently stops resolving.

    Found by doing it — refreshing the board's held counts broke all four rows
    of the 2026-08-26 run in one command that reported nothing but success, and
    the verdicts happened to be identical, which is exactly when such a break
    goes unnoticed.

    THREE THINGS THE FIRST VERSION GOT WRONG, all the same mistake in different
    clothes — a check that could not look printing what a clean check prints:

    * It ran AFTER the write, so its advice ("keep the previous file") named a
      remedy the command had already made impossible. It now runs before, and
      copies the file rather than recommending that someone should have.
    * It ran after the `if not scores` early return, so the one case where the
      pin is destroyed COMPLETELY — `scores.json` replaced by `{}` — was the
      one case it never reported. That is reachable by pointing `--run` one
      directory too high.
    * It compared the current file against the recorded digests, so it claimed
      "a re-score replaced the bytes" on every later invocation too, including
      ones that changed nothing. Reading before the write is what lets it tell
      "this command broke them" from "they were already unresolved".

    Reported, never a gate: re-scoring with newer instruments is a legitimate
    thing to do, and refusing it would be worse than naming what it costs.
    """
    scores = run_dir / "scores.json"
    rows, unreadable = _history_rows()
    if unreadable:
        return [f"note  {unreadable}; this re-score's effect on the pinned "
                f"digests is UNKNOWN, not clean."]
    mine = _rows_for(rows, run_dir)
    if not mine:
        return []
    try:
        before = hashlib.sha256(scores.read_bytes()).hexdigest()
    except OSError:
        # No scores.json to replace, and rows that pin one: they were already
        # unresolvable before this command touched anything.
        pinned = [r for r in mine if r.get("scores_sha256")]
        return ([f"note  {len(pinned)} history row(s) pin a scores.json this "
                 f"run directory no longer has."] if pinned else [])

    breaking = [r for r in mine if r.get("scores_sha256") == before]
    already = [r for r in mine
               if r.get("scores_sha256") not in (None, before)]
    out = []
    if breaking:
        keep = run_dir / f"scores.{_kept_suffix(mine)}.json"
        note = ""
        if not keep.exists():
            try:
                shutil.copy2(scores, keep)
                note = f" The bytes they name are kept at {keep.name}."
            except OSError as exc:
                note = f" They could not be kept beside it ({exc})."
        else:
            note = f" The bytes they name were already kept at {keep.name}."
        out.append(
            f"note  {len(breaking)} history row(s) pin the scores.json this "
            f"command is about to replace, and will stop resolving to it.{note}")
        out.append(
            "      `report --record` is not the remedy: it would stamp fresh "
            "rows with TODAY's skill version over agents that read an older one.")
    if already:
        out.append(
            f"note  {len(already)} history row(s) already pinned a different "
            f"scores.json before this command ran.")
    return out


def _kept_suffix(rows: list[dict]) -> str:
    """-> a name for the preserved file, from what the rows say measured it."""
    versions = sorted({str(r.get("instrument_version") or r.get("skill_version"))
                       for r in rows if r.get("instrument_version")
                       or r.get("skill_version")})
    return f"{versions[-1]}-instruments" if versions else "superseded"


def _held_note(fresh: list[dict]) -> str:
    """-> " (N held)", " (N-M held)", or "" when no result recorded it.

    Empty rather than zero, because "not recorded" and "nothing was graded" are
    the very distinction this number exists to draw — a scores file written
    before the field existed prints no parenthesis, and a genuine zero prints
    `(0 held)`.

    THE RANGE, NOT THE MAXIMUM. This returned `max(counts)` while the cell's
    verdict is the WORST of the runs, so two runs that graded 15 and 10 gates
    rendered as `2 runs, all pass (15 held)` — the most flattering count beside
    the least flattering verdict, in the function whose whole documented
    purpose is that a spread is a different claim from an agreement. Two runs
    that held different amounts produced different artifacts, which is the very
    thing this number was added to expose.
    """
    counts = sorted({s["design"]["gates_held"] for s in fresh
                     if isinstance(s.get("design"), dict)
                     and s["design"].get("gates_held") is not None})
    if not counts:
        return ""
    return (f" ({counts[0]} held)" if len(counts) == 1
            else f" ({counts[0]}-{counts[-1]} held)")


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
            builds = sorted((b for b in by_build if b is not None), key=versioning.sort_key)
            latest = builds[-1]
            worst = next(iter(by_build[latest]))
            latest_detail = ", ".join(sorted(
                {f for s in fresh if s.get("built_version") == latest
                 for f in s.get("failed", [])}))
            base = (worst if worst == "pass" or not latest_detail
                    else f"{worst}: {latest_detail}")
            return (base + " · skill changed between builds: "
                    + ", ".join(f"{next(iter(by_build[b]))}@{b}" for b in builds)
                    + _held_note(fresh),
                    worst)
        cell = worst if worst == "pass" else (f"{worst}: {detail}" if detail else worst)
        # THE COUNT ON THIS PATH TOO. It was computed only at the final return,
        # so the two multi-run cells — the ones that most need to say how much
        # each run held — lost it entirely.
        return (cell + f" · {len(fresh)} runs UNSTABLE: "
                + ", ".join(f"{v}×{seen.count(v)}" for v in sorted(set(seen)))
                + _held_note(fresh),
                worst)
    cell = worst if worst == "pass" else (f"{worst}: {detail}" if detail else worst)
    if len(fresh) > 1:
        cell += f" · {len(fresh)} runs, all {worst}"
    # HOW MANY GATES HAD A SUBJECT, in the cell that claims them. A clean sheet
    # over eighteen gates and a clean sheet over thirteen print the same word,
    # and the 2026-08-26 round published that pair side by side: one deck
    # carried an agenda, part openers and pages declaring an analysis move; the
    # other had none of them, so five of its clean rows graded nothing at all.
    # The rows are right to pass — a measured absence passes, deliberately —
    # and the roll-up was where the number went missing.
    return cell + _held_note(fresh), worst


# Driver verdicts that earn nothing. Split by whether the agent's CLI was ever
# invoked: `environment` is decided by `environment_check` before `drive()` is
# called at all, `no driver` means the registry declares no argv, and
# `could not start` is the OSError from exec — in none of the three did the
# agent do anything. The rest are the agent's own run going wrong.
NEVER_RAN = ("could not start", "no driver", "environment")
DRIVER_FAILURES = ("stall", "over budget", "timeout", "driver failed",
                   "misplaced") + NEVER_RAN

def scored_file(produced: list[pathlib.Path],
                task: dict) -> tuple[pathlib.Path | None, str]:
    """-> (the one file to score, why) out of everything the glob matched.

    THE TASK'S OWN WORD OUTRANKS THE ALPHABET, which is `_misplaced`'s rule one
    directory over. Both call sites took `produced[0]` off a sorted glob, so
    when an agent left working files beside its deliverable the scored artifact
    was whichever name sorted first. A deliverable pattern is `*.html` on
    purpose — the prompt names the file and the harness accepts what arrives —
    so several matches is the ordinary case for any agent that shows its work.

    Never fired, and came four minutes from firing: Claude Code hit the hour
    cap on T1-deck in the 0.1.605 round having written `deck.en.html` plus four
    working files, and `_s2.html` sorts first — a shape sprite. The timeout is
    what saved the cell, which is not a defence.

    The prompt is searched for each candidate's literal filename; that is exact
    rather than a guess about shape. When it settles nothing, the caller is
    told so and refuses rather than picking — an ambiguous run recorded as
    ambiguous is a finding, and a wrong file scored silently is not.
    """
    if not produced:
        return None, "nothing matched the deliverable pattern"
    if len(produced) == 1:
        return produced[0], "the only match"
    prompt = str(task.get("prompt") or "")
    if not prompt.strip():
        return None, ("this task declares no prompt, so nothing can say which "
                      f"of the {len(produced)} matching files is the "
                      "deliverable")
    # BOUNDED, not a substring test. `p.name in prompt` also matched a
    # candidate whose name is a tail of the named one, so a run that produced
    # `deck.en.html` alongside a stray `en.html` was refused — the FM-13
    # direction, inside the repair for one.
    def _named(p):
        return re.search(rf"(?<![\w.-]){re.escape(p.name)}(?![\w.-])", prompt)
    named = [p for p in produced if p.name and _named(p)]
    if len(named) == 1:
        return named[0], f"the file the prompt names ({named[0].name})"
    if len(named) > 1:
        return None, ("the prompt names more than one of the files that were "
                      "written: " + ", ".join(sorted(p.name for p in named)))
    return None, ("the prompt names none of the "
                  f"{len(produced)} files matching {task['deliverable']!r}: "
                  + ", ".join(sorted(p.name for p in produced)))


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
    # the `one home` guard's territory, and a fingerprint that differs
    # between callers is worse than none — both sides would report matches.
    return fingerprint.material_hash(material)


def _two_counts(usage: object) -> dict | None:
    """-> {input_tokens, output_tokens} from a vendor's usage object, else None.

    TWO SPELLINGS, because vendors do not agree and a reader that knows one of
    them reports "no usage" for the other in silence. Claude Code and Hermes
    write `input_tokens`; Cursor writes `inputTokens` in the same field of the
    same shape, and its runs carried a clean eight-page deck and no cost row
    until this looked for both.

    Two integers or nothing, either way. A count that cannot be read is a count
    that was not returned, and `None` says so — never zero, which would put a
    free run on the cost board.
    """
    if not isinstance(usage, dict):
        return None
    for keys in (("input_tokens", "output_tokens"), ("inputTokens", "outputTokens")):
        i, o = usage.get(keys[0]), usage.get(keys[1])
        if all(isinstance(v, int) and not isinstance(v, bool) for v in (i, o)):
            return {"input_tokens": i, "output_tokens": o}
    return None


def _model_cell(rec: dict) -> str | None:
    """-> what the board's model column should say for one driven task.

    WHAT RAN OUTRANKS WHAT WAS ASKED. `model` is the request and reads
    `(the CLI's default)` when nothing was pinned; `model_ran` is what the CLI
    said it used. A board cell states what produced it, so the answer wins over
    the ask — and the ask is kept beside it when the two differ, because `Auto`
    routes and a run pinned to nothing is not the same claim as a run pinned to
    whatever Auto happened to choose.

    A function rather than four lines inline so the rule can be tested for what
    it decides instead of for how it is spelled.
    """
    ran, asked = rec.get("model_ran"), rec.get("model")
    pinned = bool(asked) and not str(asked).startswith("(")
    if ran:
        # CONFIRMED. The ask rides along when it was pinned and worded
        # differently — `Auto` routing to a model is not the same claim as
        # pinning it, and neither is a pin the CLI answered under another name.
        # `same_model`, not `!=`: the tokeniser is what knows that
        # `cursor-grok-4.6-high` and `Cursor Grok 4.6 High` are one
        # model, and a private comparison here printed them as two.
        differs = pinned and agent_capability.same_model(asked, ran) is not True
        return f"{ran} (asked {asked})" if differs else ran
    # NOTHING CONFIRMED IT, and BOTH unconfirmed shapes say so. A pinned model
    # with no answer printed exactly what a confirmed one prints; the first fix
    # repaired that and left the unpinned case returning `(the CLI's default)`
    # — the very string this release exists to abolish, byte-identical to what
    # the pre-fix board printed, and the ordinary case for two of the four
    # agents on it, since Gemini and Hermes announce no model at all. A review
    # caught the second half, and a test of mine had asserted it as correct.
    return f"asked {asked}, unconfirmed" if pinned else "unconfirmed"


def _model_from_transcript(text: str) -> str | None:
    """-> the model the CLI says it ran, out of its own output, else None.

    **WHAT WAS PINNED AND WHAT RAN ARE DIFFERENT FACTS, and the record kept
    only the first.** `--model` is a request; with no request the field read
    `(the CLI's default)`, which is a description of the ASK rather than an
    answer. Cursor's stream says `"model":"Auto"` on its `system`/`init` line,
    and Auto routes — so the board's model column said "default" over runs
    whose model nobody can now name, on a board whose whole argument is that a
    cell states what produced it.

    Found when the owner asked which model a verification run had used and the
    answer was in the transcript, in a field the driver had never read.

    Both stream shapes: NDJSON, one object per line (Cursor's `stream-json`),
    and a single object (Claude Code's `json`). The first `model` a `system`
    or `init` record carries wins, because that is the session's own
    announcement; a later per-message `model` would be one turn's.
    """
    body = text.strip()
    if not body:
        return None
    # WHICH SILENCE. `None` covered six states — no transcript, unparseable
    # text, an init record with no `model`, a blank one, a non-string one, and
    # a CLI that genuinely announces nothing. The first two mean nothing ran to
    # be asked; the last is Gemini and Hermes every time. They are not the same
    # fact and the caller could not tell them apart.
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            doc = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(doc, dict):
            continue
        if doc.get("type") in ("system", "init") or doc.get("subtype") == "init":
            model = doc.get("model")
            if isinstance(model, str) and model.strip():
                return model.strip()
    # A single-object transcript, read from the front the way the usage
    # reader does — the object may be followed by a CLI warning line.
    head = body.find("{")
    if head >= 0:
        try:
            doc, _ = json.JSONDecoder().raw_decode(body[head:])
        except ValueError:
            return None
        if isinstance(doc, dict) and isinstance(doc.get("model"), str):
            return doc["model"].strip() or None
    return None


def _usage_from_transcript(text: str) -> dict | None:
    """-> {input_tokens, output_tokens} from a JSON transcript, else None.

    Claude Code's `-p --output-format json` ends in one JSON object carrying
    `usage`; the last JSON object in the transcript is read and the two counts
    taken only when both are integers. Anything else is None — a count this
    function cannot read is a count that was not returned."""
    body = text.strip()
    last = body.rfind("\n{")
    candidates = [body] + ([body[last + 1:]] if last >= 0 else [])
    # AND THE OBJECT MAY COME FIRST. Both readings above assume the JSON is the
    # last thing in the transcript, and the transcript is stdout AND stderr:
    # Claude Code prints its result object, then the CLI warns "no stdin data
    # received in 3s", and the extra line makes the whole text unparseable while
    # leaving no `\n{` for the fallback to find. Every twelve-page run recorded
    # `usage: null` for that reason, which is a missing row on the cost board —
    # `ledger.py --board` needs output tokens before it computes anything, so
    # the model x effort matrix could not be filled by the runs filling it.
    # raw_decode reads one object from the front and ignores whatever follows.
    head = body.find("{")
    if head >= 0:
        try:
            obj, _ = json.JSONDecoder().raw_decode(body[head:])
        except ValueError:
            pass
        else:
            candidates.append(json.dumps(obj))
    for chunk in candidates:
        try:
            doc = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        counts = _two_counts(doc.get("usage") if isinstance(doc, dict) else None)
        if counts:
            return counts
    return None


def _eval_misses(path: pathlib.Path, genre: str | None,
                 design: dict | None = None,
                 layout: dict | None = None) -> list[str]:
    """-> the Evals findings that should fail a conformance deliverable.

    The Evals are what this package means by a document being good enough:
    enough content pages for a ratio to mean anything, and then prose-only
    share, figures per content page, list density and visual share against the
    genre's bars. No conformance run had ever applied them — T1 scored three
    checkers and none of these — so a deck could satisfy the markup gates while
    being a different kind of document entirely. The owner opened one and said
    so.

    `eval_corpus`'s own measure and score are used rather than re-derived: a
    second reading of a threshold table is the shape `gating.py` and
    `checker_report.py` were both extracted to end.

    A missing bar for the genre is not a failure — the table says so in
    `evidence`, and inventing one here would be the 0.1.339 mistake. A metric
    the run could not MEASURE is: "not measured" has never been a pass in this
    package.
    """
    try:
        measured = eval_corpus.measure(path, with_render=True,
                                       design=design, layout=layout)
    except Exception as exc:                                        # noqa: BLE001
        return [f"evals could not measure the deliverable: {exc}"]
    if genre:
        measured["genre"] = genre
    # A DOCUMENT THE EVALS COULD NOT READ is a finding, not a traceback. The
    # measurement returns whatever it managed, so a file it could not parse —
    # a partial write, a misplaced artifact caught mid-flight — arrives without
    # `content_pages` and `eval_corpus.score` raises KeyError on it. Crashing
    # the scorer turns one unmeasurable document into no scores for the whole
    # run, which is the 0.1.350 lesson: a tool that cannot measure says so.
    if "content_pages" not in measured:
        return [f"evals could not read the deliverable: "
                f"{measured.get('render_state') or 'no content pages measured'}"]
    table = eval_corpus.thresholds()
    out = []
    floor = table.get("min_content_pages", 0)
    if measured.get("content_pages", 0) < floor:
        out.append(f"evals content_pages={measured.get('content_pages')} "
                   f"(floor {floor})")
    for row in eval_corpus.score(measured, table):
        if row["verdict"] == "MISS":
            out.append(f"evals {row['metric']}={row.get('value')} "
                       f"({row['direction']} {row.get('bar')})")
        elif row["verdict"] == "not measured":
            out.append(f"evals {row['metric']} not measured")
    return out


def _usage_from_file(path: pathlib.Path) -> dict | None:
    """-> {input_tokens, output_tokens} from a CLI's own usage report, else None.

    Same contract as the transcript reader and the same refusal: two integers or
    nothing. A CLI that writes a report and fails to fill it in has reported no
    usage, and `null` is what that means — never zero, which would put a free
    run on the cost board.
    """
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict):
        return None
    # The report may be the counts themselves or wrap them in `usage`.
    return _two_counts(doc) or _two_counts(doc.get("usage"))


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
    # THE ID GOES INTO THE RECORD, not only into the sentence this returns.
    # The trace holds what a run COST; `history.json` holds what it EARNED, and
    # joining them meant matching on (agent, date) — a heuristic that is wrong
    # the first time two agents run on one day. The id is the key, and this is
    # the only place that knows it. Written before anything can fail below, so
    # a run that opens a trace and then dies still says which one it opened.
    record["trace_id"] = tid
    produced = [wd / n for n in record.get("produced") or []]
    # A MISPLACED ARTIFACT STILL ANSWERS THE COST QUESTION. The two boards ask
    # different things and only one of them cares where the file went: the
    # conformance verdict asks whether the agent did the task as stated, and
    # the task states the working directory, so a misplaced run is `not earned`
    # there and stays that way. This trace asks how many output tokens a
    # model at an effort spent per content page, and a file's location has no
    # bearing on that. Nothing here is laundered into a pass: a trace records
    # agent, model, effort, gates, pages and tokens, and not one field is about
    # location — while `ledger.py --board` drops any run with a failing gate
    # before it computes anything.
    #
    # Measured before this existed: of the first four matrix cells driven on
    # 2026-08-21, two were misplaced and therefore contributed no trace at all,
    # so the matrix the runs were FOR could not be filled by the runs that
    # filled it. A timeout is still refused — its file is a draft.
    if not produced and record.get("verdict") == "misplaced" and record.get("misplaced"):
        produced = [pathlib.Path(record["misplaced"][0])]
    if (record.get("verdict") not in ("driven", "misplaced")) or not produced:
        return f"trace {tid} opened and left open: the drive did not finish"
    one, why = scored_file(produced, task)
    if one is None:
        # WRITTEN DOWN, not only printed. The note below reaches `drive_one`'s
        # console and nothing else, so an operator reading the run directory
        # afterwards found an open trace and `ledger.py` calling it an
        # abandoned build — which is a claim about the agent, for a refusal
        # that is the harness's.
        record["trace_note"] = why
        try:
            (wd / "driver.json").write_text(
                json.dumps(record, indent=2), encoding="utf-8")
        except OSError:
            pass
        return f"trace {tid} opened and left open: {why}"
    argv = [sys.executable, str(tool), "close", "--id", tid,
            "--deliverable", str(one), "--agent", agent["id"],
            "--phase", "build", str(max(1, int(record.get("seconds") or 1)))]
    if record.get("model") and not str(record["model"]).startswith("("):
        argv += ["--model", record["model"]]
    if record.get("effort") and not str(record["effort"]).startswith("("):
        argv += ["--effort", record["effort"]]
    if record.get("cli_version"):
        argv += ["--cli-version", str(record["cli_version"])]
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
    return platform_registry.platforms(ROOT)


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
        # THE WHOLE FIRST LINE. It was sliced to 40 characters here, which is a
        # BOARD COLUMN's width applied at the source — and since 0.1.626 this
        # string is also what `cli_version` records. Hermes' banner is 89
        # characters and the slice removed exactly the discriminating half:
        # `Hermes Agent v0.20.5 (2026.8.19) · upstr` drops `upstream 8d30c204 ·
        # local 057dcdf2`, so two different builds carrying one version tag
        # would land in one cell — the fold the field exists to prevent. The
        # truncation moved to the two places that DISPLAY it.
        return True, (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception as exc:                                # noqa: BLE001
        return False, f"probe failed: {exc.__class__.__name__}"


def _short(note: str, width: int = 40) -> str:
    """-> the probe banner at a board column's width.

    Truncation belongs where a thing is DISPLAYED, not where it is read: the
    same string is recorded as `cli_version`, and a build id cut off at 40
    characters is a build id that cannot tell two builds apart.
    """
    return note if len(note) <= width else note[:width - 1] + "…"


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
    # THE RUN ITSELF RIDES ALONG UNDER A PRIVATE KEY, and the caller pops it
    # before the entry is written to scores.json. The Evals need the same two
    # checkers this just ran, and re-running them re-rendered the whole
    # document in a second browser — 17 seconds per artifact to recompute
    # numbers that were already in memory. The key is popped rather than
    # serialized because a full report per kind would multiply the scoreboard's
    # size for data nobody reads out of it.
    if not run["spoke"] or not verdicts:
        return {"exit": run["exit"], "verdicts": {}, "unparseable": True,
                "_run": run}
    return {"exit": run["exit"], "verdicts": verdicts, "_run": run}


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
# NAMES THE COMMAND, NOT ONE OF ITS FLAGS. This read `report --record`, so a
# board written by `report --redraw` was stamped as having been recorded — and
# this is the release where the difference is load-bearing, since redraw's whole
# argument is that it deliberately does not touch history. A reader auditing
# whether history rows should exist for a board was told, by the board, that
# they were.
BOARD_OPEN = "<!-- generated by run_conformance.py report -->"
# The form written before that, still accepted when splitting an existing file
# so a board on disk does not have to be regenerated to be readable.
BOARD_OPEN_LEGACY = "<!-- generated by run_conformance.py report --record -->"
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
    opener = next((m for m in (BOARD_OPEN, BOARD_OPEN_LEGACY) if m in text), None)
    if opener is None or BOARD_CLOSE not in text:
        return (f"FAIL  {path.name} carries no generated region; add "
                f"{BOARD_OPEN} and {BOARD_CLOSE} around its header and table")
    head, rest = text.split(opener, 1)
    _, tail = rest.split(BOARD_CLOSE, 1)
    path.write_text(head + BOARD_OPEN + "\n" + render_board(record) + "\n"
                    + BOARD_CLOSE + tail, encoding="utf-8")
    return f"wrote the board table into {path.relative_to(ROOT)}"



def _board_run_version(record: dict, read_scores: bool = True) -> str | None:
    """-> the skill version the rendered runs were produced at: from the run
    id when it carries one, else from the newest `instrument_version` in the
    scores. The fallback exists because `results/latest` carries no version
    in its name, and a board rendered from it read "skill 0.1.527" over a run
    scored at 0.1.522 — the exact claim the comment above render() says this
    field exists to stop.

    **`read_scores=False` is for the CHECKER, and the split is a local/CI
    divergence rather than a preference.** The fallback opens a file in the run
    directory, which lives outside this repository: it resolves on the machine
    that drove the run and never in CI. So a board naming a run id with no
    version in it PASSED `check_board_staleness_clause` locally and FAILED it on
    the runner — with preflight, whose whole premise is that local green and CI
    green are one claim, reporting green. It happened: eight `report --record`
    calls left the board describing `r19-xhigh-3`, and the divergence was found
    by CI rather than by the thirty-four steps that exist to prevent that.

    The leniency also runs the wrong way. The local run is the one meant to
    catch things early, and it was the lenient one.
    """
    m = re.search(r"(\d+\.\d+\.\d+)", str(record.get("run_id") or ""))
    if m:
        return m.group(1)
    if not read_scores:
        return None

    found: list[str] = []
    for r in re.findall(r"`([^`]+)`", str(record.get("run_id") or "")):
        f = pathlib.Path(r).expanduser() / "scores.json"
        if f.exists():
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            found += [str(v["instrument_version"]) for v in doc.values()
                      if isinstance(v, dict) and v.get("instrument_version")]
    return sorted(found, key=versioning.sort_key)[-1] if found else None


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


def _portable(text: str) -> str:
    """Collapse this machine's home directory to `~` in anything RECORDED.

    The board and `history.json` are tracked files, and a run directory is
    named by an absolute path — so every recorded run carried the operator's
    username into git, and would have carried it into a public repository. `~`
    keeps the path meaningful and expandable on the machine that wrote it,
    which is the only machine that can resolve it anyway.

    Paired with `expanduser()` wherever a recorded path is read BACK: a run id
    is not only displayed, it is opened to recover the version of a run whose
    directory name carries none.
    """
    home = str(pathlib.Path.home())
    return text.replace(home, "~") if home not in ("", "/") else text


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


def board_header(version: str, ran_at: str | None,
                 root: pathlib.Path | None = None) -> str:
    """-> the board's `# ` line, for the one version and the one run.

    THE ONE PLACE THE HEADER'S SHAPE IS WRITTEN. It was three: `render` built
    it, `cmd_restamp` rebuilt it to rewrite it, and `check_repo`'s guard
    rebuilt it again to compare — three transcriptions of one format, inside
    the fix for a drift defect. A review named it before it could cost
    anything: change `render`'s title and `cmd_restamp` would have silently
    rewritten it back on the next release.

    `skill <version>` STAYS, and stays first: it is this file's version stamp
    and `check_version_citations` matches `skill {v}` on it.
    """
    distance = versioning.releases_between(ran_at, version, root)
    # ABS, because `restamp --version` may name a version OLDER than the
    # board's run, and the clause says how far apart they are either way.
    behind = abs(distance) if distance is not None else None
    stamp = (f"skill {version}" if not behind else
             f"skill {version} · newest run {ran_at} · "
             f"{behind} release{'' if behind == 1 else 's'} behind")
    return f"# LUMI style conformance · {stamp}"


def board_run_id_line(text: str) -> str | None:
    """-> the board's `Runs ` line, from the generated block."""
    return next((ln for ln in text.splitlines()[:8]
                 if ln.startswith("Runs ")), None)


def cmd_restamp(version: str) -> int:
    """Recompute the board's header line for a new skill version.

    NOT a re-render of the board: the table, the failure list and the history
    are the run's and stay exactly as recorded. Only the header changes, and
    only because it is the one line that is about the DISTANCE between the run
    and the current release — a quantity that goes stale every time anybody
    ships anything.

    This exists because the alternative had been running for two dozen
    releases. `stamps.py` requires `skill {v}` in this file, the pattern is a
    substring match, and the cheapest edit that satisfies it moves the version
    and leaves `newest run 0.1.578 · 3 releases behind` frozen underneath —
    which is what 0.1.581 through 0.1.604 each shipped, twenty-four releases of
    one unchanged sentence. It was true when written at 0.1.581 and wrong for
    the twenty-three after it, understating a distance that reached 26.

    Called from `release.py`'s realigners, so no release can bump the stamp
    without recomputing the clause it invalidates. The ORDER is load-bearing
    and not for the reason first written here: `stamp()` aborts the release
    when the OLD version string is absent from a stamped file, so a restamp
    running first would rewrite `skill <old>` and the stamp step would exit
    saying it could not find it.
    """
    path = ROOT / "conformance" / "CONFORMANCE.md"
    if not path.exists():
        print(f"FAIL  {path} does not exist")
        return 1
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    hi = next((i for i, ln in enumerate(lines[:6]) if ln.startswith("# ")), None)
    runs = board_run_id_line(text)
    if hi is None or runs is None:
        print("FAIL  conformance/CONFORMANCE.md has no `# ` header or no "
              "`Runs ` line; it is not in the shape report --record writes")
        return 1
    # THROUGH `_board_run_version`, NOT A SECOND REGEX. The generator's own
    # answer has a `scores.json` fallback for a run id that carries no version
    # — `results/latest` is the documented case — and a second, lossier reader
    # here would have failed the repo on a board `report --record` wrote
    # correctly, with a message accusing the file of the wrong shape. That
    # makes every release impossible and invites a hand-edit of a good file.
    ran_at = _board_run_version({"run_id": runs})
    if not ran_at:
        print(f"FAIL  the board's run names no version and no scores.json "
              f"reachable from it does either, so its distance from {version} "
              f"cannot be computed: {runs.strip()!r}")
        return 1
    # WHICH SIDE IS MISSING IS THE WHOLE DIAGNOSIS. `releases_between` returns
    # None when EITHER argument is absent from the CHANGELOG, and the first
    # version of this blamed the board unconditionally — so `restamp --version
    # 0.1.608` on a repo at 0.1.607 reported that the board's run predated the
    # CHANGELOG, sending a reader to look at run directories.
    released = versioning.releases(ROOT)
    if version not in released:
        print(f"FAIL  {version} is not a CHANGELOG heading, so there is no "
              f"release to measure the board against. Write the entry first.")
        return 1
    if ran_at not in released:
        # A board older than this CHANGELOG carries. Leaving the header alone
        # is the honest answer and inventing a distance would not be — but it
        # is NOT silence: `check_repo`'s guard fails on the same state, so the
        # release stops here rather than shipping an unchecked clause.
        print(f"note  the board's run ({ran_at}) is not a release this "
              f"CHANGELOG carries, so no distance is computable; header left "
              f"as written. The board staleness guard fails on this state.")
        return 0
    new = board_header(version, ran_at, ROOT) + "\n"
    if lines[hi] == new:
        print(f"ok    board header already reads {new.strip()!r}")
        return 0
    was = lines[hi].strip()
    lines[hi] = new
    path.write_text("".join(lines), encoding="utf-8")
    print(f"restamped the board header: {was!r} -> {new.strip()!r}")
    return 0


def render(record: dict) -> str:
    # THE HEADER CARRIES BOTH VERSIONS AND THE DISTANCE BETWEEN THEM. It used
    # to name the instrument alone, so a board rendering runs from 0.1.454 sat
    # under the words "skill 0.1.502" — a version it had never measured
    # anything at. That is the same claim `built_version` exists to stop a cell
    # from making, made by the page the cells sit on.
    ran_at = _board_run_version(record)
    header = board_header(record["version"], ran_at)
    dated = f" · run {record['run_date']}" if record.get("run_date") else ""
    # THE RESOLVED VERSION, WRITTEN INTO THE LINE when the run id does not
    # carry one. `results/latest` is a run id `report --record` legitimately
    # writes, and the only other place its version can be read is a scores.json
    # in the run DIRECTORY — outside this repository, present on the machine
    # that drove the run and absent on the runner. So the checker was lenient
    # here and strict there, and preflight's claim that local green and CI green
    # are one thing did not hold: a board describing `r19-xhigh-3` passed all
    # thirty-four steps and reddened the merge.
    #
    # Putting it in the line moves the fact INTO the committed file, so both
    # machines read the same thing and neither has to open a directory.
    ran_at = _board_run_version(record)
    stamped = (f" · scored at {ran_at}"
               if ran_at and ran_at not in str(record["run_id"]) else "")
    lines = [header, "",
             f"Runs {record['run_id']}{dated}{stamped} · {record['host']} · "
             f"{record['detected']} of {record['agents']} agents detected · "
             f"up to n={record['repeat']} per agent · "
             f"{record['structural']} of {record['agents']} can never answer a CLI probe",
             "",
             "| agent | capability | cli | model | " +
             " | ".join(t for t in record["task_ids"]) + " | verdict |",
             "|---|---|---|---|" + "---|" * (len(record["task_ids"]) + 1)]
    for row in record["rows"]:
        cells = [row["name"], row["capability"], row["cli"],
                 row.get("model") or "—"]
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
    ap.add_argument("command", choices=["validate", "detect", "run", "score",
                                        "report", "restamp"])
    ap.add_argument("--models", action="store_true",
                    help="with `detect`: also ask each agent what it can be RUN "
                         "AS. Opt-in because it shells out a second time per "
                         "agent and `detect` is the cheap answer to 'is it "
                         "there'. Eleven of the twelve answer from the registry "
                         "waiver without running anything.")
    # Repeatable, and only `report` may take more than one. A scoreboard built
    # from a single directory erases every agent that directory does not
    # contain: recording the Claude Code run turned Cursor's row from a
    # measured `fail` into `not installed`, which is the false absence this
    # file's own closing paragraph says it exists to avoid. Later --run wins on
    # a collision, so re-running one agent replaces its own row and nobody
    # else's.
    ap.add_argument("--run", action="append", default=None)
    ap.add_argument("--version", default=None,
                    help="restamp: the skill version the header should name "
                         "(default: the newest CHANGELOG heading)")
    ap.add_argument("--agent", action="append", default=None,
                    help="prepare (or report) this agent even if no CLI answers "
                         "its probe — IDEs and API models are driven by hand. "
                         "Repeatable: `--agent a --agent b` runs both. It took "
                         "one value until 0.1.550, so three of them silently "
                         "kept the last and a three-agent round drove one agent")
    ap.add_argument("--task", default=None,
                    help="with run: only this task id. The suite is three tasks "
                         "and one of them is a twelve-page deck, so proving the "
                         "driver works should not cost a deck")
    ap.add_argument("--drive", action="store_true",
                    help="with run: actually invoke each agent, in a temporary "
                         "directory OUTSIDE this repository, instead of writing "
                         "a prompt for a person to invoke by hand")
    ap.add_argument("--model", action="append", default=None, metavar="[AGENT=]ID",
                    help="with run --drive: pin the model and record which one. "
                         "Repeatable, and `<agent>=<id>` pins one agent — a "
                         "horse race between three CLIs has three different "
                         "model ids and one global flag could not express it, "
                         "which meant the agents had to be driven one at a time. "
                         "Left off, each CLI picks its own default and the run "
                         "records that it did — a comparison needs the pin, a "
                         "check of what a user actually gets does not")
    # `xhigh` and `max` are real levels: `claude --effort` documents
    # low|medium|high|xhigh|max and `hermes --reasoning` adds none|minimal|ultra.
    # Cursor spells its top level `xhigh` inside the model id and has no `max`
    # for Grok 4.6 at all. Refusing them here meant the highest effort a
    # comparison could ask for was `high`, on every agent.
    # Not `choices`: the value may be `<agent>=<level>` now, and argparse would
    # reject that before anything could split it. `_per_agent` validates.
    ap.add_argument("--effort", action="append", default=None,
                    metavar="[AGENT=]LEVEL",
                    help="with run --drive: pin the reasoning effort through the "
                         "agent's `drive_effort_flag` and record it. This is the "
                         "second axis of the model×effort matrix (K1); an agent "
                         "whose registry record names no effort flag records "
                         "the level as not pinned. Repeatable as "
                         "`<agent>=<level>`, and one of "
                         "low|medium|high|xhigh|max")
    ap.add_argument("--budget", "--timeout", dest="budget", type=int,
                    default=DRIVE_BASE_BUDGET,
                    help=f"with run --drive: seconds one task gets outright "
                         f"(default {DRIVE_BASE_BUDGET}). Past it the run "
                         f"continues while it shows signs of life, never past "
                         f"--hard-cap")
    ap.add_argument("--hard-cap", type=int, default=DRIVE_HARD_CAP,
                    help=f"with run --drive: seconds no amount of progress can "
                         f"extend a task past (default {DRIVE_HARD_CAP})")
    ap.add_argument("--redraw", action="store_true",
                    help="rewrite the board's generated block from the named "
                         "run WITHOUT touching conformance/history.json — for "
                         "when the wording changed and the measurement did "
                         "not. `--record` would stamp the run's history rows "
                         "with today's version.")
    ap.add_argument("--record", action="store_true",
                    help="write this run's result into the tracked record. "
                         "With `report`: one history row per scored agent per "
                         "run, which is what the evidence gate's freshness "
                         "obligation reads. With `detect --models`: the "
                         "answered vocabularies, so a later probe can say what "
                         "CHANGED — without a stored set the "
                         "`vocabulary-changed` trigger in agent-evals.json "
                         "describes a comparison nothing can make.")
    args = ap.parse_args(argv)

    try:
        tasks, agents = load_tasks(), load_agents()
    except (OSError, ValueError, KeyError) as exc:          # noqa: BLE001
        print(f"FAIL  conformance suite does not parse: {exc}")
        return 1

    if args.command == "restamp":
        version = args.version
        if not version:
            found = versioning.releases(ROOT)
            if not found:
                print("FAIL  no '## X.Y.Z' heading in CHANGELOG.md and no "
                      "--version given")
                return 1
            version = found[0]
        return cmd_restamp(version)

    if args.command == "validate":
        hist = history.path(ROOT)
        if hist.exists():
            rows, problem = history.read_rows(ROOT)
            if problem:
                print(f"FAIL  {problem}")
                return 1
            try:
                for i, r in enumerate(rows):
                    for key in ("skill_version", "agent", "date", "run_dir",
                                "tasks", "scores_sha256"):
                        if key not in r:
                            raise ValueError(f"history[{i}] missing {key!r}")
                    if not isinstance(r["tasks"], dict):
                        raise ValueError(f"history[{i}].tasks is not a dict")
                    # The optional per-task maps are keyed by task id, like
                    # `tasks` and `built`. A row that names a task in `config`
                    # which `tasks` does not hold is describing a run that was
                    # never scored, and that is the shape a hand edit takes.
                    for key in ("config", "traces"):
                        if key not in r:
                            continue
                        if not isinstance(r[key], dict):
                            raise ValueError(
                                f"history[{i}].{key} is not a dict")
                        stray = sorted(set(r[key]) - set(r["tasks"]))
                        if stray:
                            raise ValueError(
                                f"history[{i}].{key} names {stray} which "
                                f"history[{i}].tasks does not")
                    for task_id, conf in (r.get("config") or {}).items():
                        if not isinstance(conf, dict):
                            raise ValueError(
                                f"history[{i}].config[{task_id!r}] is not a dict")
                        # The effort tuple is IMPORTED for the reason stated at
                        # its other use in this file: a second copy of it drifted
                        # once and cost a real run.
                        eff = conf.get("effort")
                        if eff is not None and eff not in trace_schema.ENUMS["effort"]:
                            raise ValueError(
                                f"history[{i}].config[{task_id!r}].effort is "
                                f"{eff!r}, not one of "
                                f"{sorted(trace_schema.ENUMS['effort'])}")
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

    known_ids = {a["id"] for a in agents}
    model_all, model_per = _per_agent(args.model, "--model", known_ids)
    # THE TUPLE IS IMPORTED, NOT RETYPED. It was retyped, and the copies drifted
    # in one release: 0.1.554 widened this one and left `trace_schema`'s at
    # three, so a run pinned to `xhigh` could be driven and could not be
    # recorded.
    effort_all, effort_per = _per_agent(
        args.effort, "--effort", known_ids, trace_schema.ENUMS["effort"])
    probed = {a["id"]: detect(a) for a in agents}
    if args.command == "detect":
        import datetime
        answered: dict[str, dict] = {}
        for a in agents:
            ok, note = probed[a["id"]]
            print(f"  {a['id']:16} {'available' if ok else 'not exercised':14} {note}")
            if args.models:
                state, detail = agent_capability.probe_models(a)
                print(f"  {'':16} models {state:8} {detail}")
                if state == "asked":
                    answered[a["id"]] = {
                        "ids": [i.strip() for i in detail.split(",")],
                        "cli_version": note if ok else None,
                        "asked_on": datetime.date.today().isoformat(),
                    }
        if args.record:
            # RECORDED SO A CHANGE CAN BE SEEN. `agent-evals.json` declared a
            # `vocabulary-changed` trigger and nothing stored a vocabulary to
            # compare against — the live list was printed and dropped, so the
            # trigger described a comparison no code could make (GAP-042). Only
            # the agents that ANSWERED are written: a waiver and a failed probe
            # are not vocabularies, and recording them as empty sets would make
            # "this CLI offers nothing" and "we could not ask" the same row.
            if not args.models:
                print("FAIL  --record needs --models: there is nothing to "
                      "record until the probes have been asked.")
                return 1
            for line in agent_capability.record_vocabularies(answered, ROOT):
                print(line)
            print(f"\nrecorded {len(answered)} vocabular"
                  f"{'y' if len(answered) == 1 else 'ies'} -> "
                  f"conformance/vocabularies.json")
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
            # A BARE NAME IS A RUN ID, NOT A PATH. `--run r13` used to be taken
            # literally, so it resolved against the working directory: invoked
            # from the checkout it wrote the whole run — transcripts, driver
            # records, an agent's deck — into the repository, which is the one
            # place the 2026-08-21 directive says conformance results may not
            # go. The print below claims to say "which root, said out loud" and
            # it did: it said `r13-phase3`, a bare relative name, which is
            # exactly the artifacts-nobody-can-find case it exists to prevent.
            # A value that names a path (absolute, or carrying a separator) is
            # still honoured as one — that is what an operator pointing at a
            # scratch directory means.
            given = pathlib.Path(runs[0]).expanduser()
            run_dir = (given if given.is_absolute() or len(given.parts) > 1
                       else RESULTS / given)
        elif args.drive:
            import datetime
            run_dir = RESULTS / f"{versioning.skill_version(ROOT)}-{datetime.date.today().isoformat()}"
        else:
            run_dir = RESULTS / "latest"
        # Created up front. The mkdir moved inside the per-agent loop when run and
        # score split, so on the case the scoreboard itself documents — few or no
        # agents detected — `run` announced a directory it had not made and
        # `score` then reported it missing.
        run_dir.mkdir(parents=True, exist_ok=True)
        # WHICH ROOT, said out loud. A run that quietly changed where it writes
        # is a run whose artifacts a person cannot find, and the two roots are
        # far apart: one is inside the checkout, the other is the folder the
        # operator reads deliverables in.
        print(f"  writing into {run_dir}"
              + ("" if RESULTS != IN_REPO_RESULTS else
                 " (the deliverable folder does not exist yet — "
                 "`output_dir.py --create` moves runs there)"))
        named = set(args.agent or ())
        wanted = [a for a in agents
                  if (a["id"] in named if named else probed[a["id"]][0])]
        # EVERY NAME HAS TO RESOLVE, not just one of them. A set difference
        # rather than `if not wanted`: naming three agents and matching one
        # would otherwise run that one and say nothing about the two typos.
        missing = sorted(named - {a["id"] for a in agents})
        if missing:
            print("FAIL  no platform in the registry with id "
                  + ", ".join(repr(m) for m in missing))
            return 1
        if not wanted:
            print("no agent detected and no --agent given; nothing to prepare. An IDE "
                  "or an API model has no CLI to probe — name it with --agent and drive "
                  "it by hand.")
            return 1
        # PREPARED FIRST, SEQUENTIALLY. Making the directories and writing the
        # prompts is milliseconds and it is the part that must be deterministic:
        # a reader looking at the tree afterwards should find it laid out the
        # same way every time, whatever order the agents finished in.
        plan: list[tuple[dict, dict, pathlib.Path]] = []
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
                plan.append((a, t, wd))

        driven = skipped = 0
        # ONE WORKER PER AGENT, and the agents run at once. Three agents on one
        # task ran back to back for 74 minutes on 2026-08-21 and share nothing:
        # separate CLIs, separate temporary directories, separate accounts.
        # Serial was never a requirement, it was the shape of a `for` loop.
        #
        # Tasks WITHIN an agent stay sequential. One CLI driven twice at once
        # shares an installation, a rate limit and in some cases a session
        # store, and a horse race whose entrants interfere with themselves
        # measures the interference.
        out_lock = threading.Lock()
        counts_lock = threading.Lock()
        crashed: list[str] = []

        def say(lines: list[str]) -> None:
            """One agent's lines, printed together. Interleaving them line by
            line across three concurrent agents produces a transcript nobody
            can attribute, which is the console equivalent of the misplaced
            artifact this harness spent a release learning to name."""
            with out_lock:
                for line in lines:
                    print(line, flush=True)

        def drive_one(a: dict, t: dict, wd: pathlib.Path) -> None:
            nonlocal driven, skipped
            # PROVEN BEFORE DRIVEN. A run whose agent cannot read the
            # rules produces artifacts that look like the agent's judgement
            # and are not; two such runs were attributed to the agent
            # before anyone read the transcript that said so.
            blocked = environment_check(a)
            if blocked:
                with counts_lock:
                    skipped += 1
                say([f"  SKIPPED {a['id']} on {t['id']}: {blocked[0]}"])
                (wd / "driver.json").write_text(
                    json.dumps({"verdict": "environment",
                                "detail": blocked[0]}, indent=2) + "\n",
                    encoding="utf-8")
                return
            record = drive(a, t, wd,
                           model=model_per.get(a["id"], model_all),
                           base=args.budget,
                           effort=effort_per.get(a["id"], effort_all),
                           hard_cap=args.hard_cap)
            # WHICH BUILD OF THE CLI DID IT, taken from the probe this run
            # already made BEFORE driving — not re-probed here, which would
            # answer about now rather than about the run. `agent` names a
            # platform and `model` names what it was pointed at; neither says
            # which binary. Two rounds of one configuration a week apart were
            # driven by `2026.08.11-e8db854` and `2026.08.25-3e8eec8`, so a
            # difference between them had a third possible cause that nothing
            # recorded.
            probe_ok, probe_note = probed.get(a["id"], (False, ""))
            if probe_ok and probe_note.strip():
                record["cli_version"] = probe_note.strip()
            else:
                # SAID, NOT DROPPED. `--agent x` drives whether or not the
                # probe answered — the selection above consults `probed` only
                # when no agent was named — so a 20-second probe timeout used
                # to leave this key absent in silence, and the run joined the
                # "nobody recorded which binary" cell beside runs that predate
                # the field. Those are different facts and the console now says
                # which this is.
                record["cli_version_note"] = (
                    f"not recorded: the {a['id']} probe did not answer "
                    f"({probe_note or 'no output'})")
                print(f"  note  {a['id']}: the CLI build was not recorded — "
                      f"{probe_note or 'the probe gave no output'}")
            # WRITTEN TWICE, ON PURPOSE, AND THE FIRST WRITE IS NOT THE ONE
            # THAT MATTERS. `_conformance_trace` mutates `record` — it puts the
            # trace id in — and this file was serialized BEFORE that, so the id
            # 0.1.617 added reached memory and never reached disk. `score`
            # reads the file, so the join key was absent from every score cell
            # of the first round driven after it shipped. The first write stays
            # because a crash inside the trace helper must still leave a driver
            # record; the second is what carries the id.
            (wd / "driver.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")
            note = _conformance_trace(a, t, wd, record)
            (wd / "driver.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")
            with counts_lock:
                driven += record["verdict"] == "driven"
                # A REFUSAL IS A TASK THAT DID NOT RUN, and the `NOTHING RAN`
                # guard below keys on `skipped`. 0.1.640 made the refusal
                # VISIBLE and left it counting as nothing, so a run where every
                # task was refused still printed `drove 0 task(s)` and exited 0
                # — which is the half of that finding the fix did not close.
                skipped += record["verdict"] == "driver refused"
            # WHICH MODEL AND WHICH LEVEL, SAID OUT LOUD. The record has
            # carried both since the driver was written and the console has
            # never printed either, so a round could be reported as "at high
            # effort" when neither axis was pinned and nothing on screen
            # disagreed. It is printed on FINISHING rather than on starting,
            # now that several are in flight at once: a line that announces an
            # intention is not a line that reports what happened.
            lines = [f"  {a['id']} on {t['id']} "
                     f"(model {record.get('model', '?')}, "
                     f"effort {record.get('effort', '?')})"]
            if note:
                lines.append(f"    {note}")
            lines.append(f"    {record['verdict']}"
                         + (f" in {record['seconds']}s, wrote "
                            f"{', '.join(record['produced']) or 'nothing'}"
                            if "seconds" in record
                            else f" — {record.get('detail', '')}"))
            say(lines)

        def drive_agent(a: dict) -> None:
            # BaseException ON PURPOSE. A thread that dies takes its message
            # with it — `threading.excepthook` ignores SystemExit entirely and
            # prints a traceback for the rest into concurrently interleaved
            # output — and neither counter moved, so a run where every task
            # died printed `drove 0 task(s)` and exited 0. An escaped exception
            # is now a counted crash and a non-zero exit.
            for one_a, t, wd in plan:
                if one_a is a:
                    try:
                        drive_one(a, t, wd)
                    except BaseException as exc:            # noqa: BLE001
                        with counts_lock:
                            crashed.append(f"{a['id']}/{t['id']}: "
                                           f"{exc.__class__.__name__}: {exc}")
                        say([f"  CRASHED {a['id']} on {t['id']}: "
                             f"{exc.__class__.__name__}: {exc}"])

        if args.drive and plan:
            by_agent = list(dict.fromkeys(a["id"] for a, _t, _wd in plan))
            print(f"  driving {len(by_agent)} agent(s) concurrently: "
                  f"{', '.join(by_agent)} — output appears as each finishes",
                  flush=True)
            threads = [threading.Thread(target=drive_agent, args=(a,))
                       for a in wanted if any(x is a for x, _t, _w in plan)]
            for th in threads:
                th.start()
            for th in threads:
                th.join()
        if not args.drive:
            print(f"prepared {run_dir}; invoke each agent against its PROMPT.txt, then "
                  f"`score --run {run_dir}`. `--drive` runs them here instead.")
            return 0
        # `latest` points at the newest dated run — only when the run lives
        # under results/ (a `--run` elsewhere is the caller's directory, and a
        # relative link to it would dangle), and never fatally: ten CI runs
        # went red at 0.1.528 because this tried to link inside a directory
        # CI does not have, and a symlink is a convenience, not a result.
        latest = RESULTS / "latest"
        if run_dir.parent == RESULTS and run_dir != latest:
            try:
                if latest.is_symlink() or (latest.exists() and not latest.is_dir()):
                    latest.unlink()
                if not latest.exists():
                    latest.symlink_to(run_dir.name)
            except OSError as exc:
                print(f"note  results/latest was not repointed ({exc}); the run "
                      f"is at {run_dir}")
        print(f"drove {driven} task(s) into {run_dir}; now `score --run {run_dir}`")
        if crashed:
            print(f"CRASHED: {len(crashed)} task(s) died inside the driver — "
                  f"{'; '.join(crashed[:3])}"
                  + ("…" if len(crashed) > 3 else ""))
            return 1
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
        # ANNOTATED because the cells gained a non-string member at
        # 0.1.623: `effort_pinned` / `model_pinned` are explicit booleans,
        # and a dict inferred as `dict[str, str]` rejects them.
        scores: dict[str, dict[str, Any]] = {}
        unscored = 0
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
                    if record.get("verdict") in DRIVER_FAILURES:
                        scores[key] = {
                            "verdict": "not earned",
                            # WHICH KIND OF NOT-EARNED, kept so the roll-up can
                            # tell an agent that ran badly from one this host
                            # never invoked. Without it `environment` — the CLI
                            # is not installed, checked BEFORE anything is
                            # launched — read as three attempts that earned
                            # nothing, on the artifact this package publishes
                            # about other people's models.
                            "attempted": ("no" if record.get("verdict")
                                          in NEVER_RAN else "yes"),
                            # The fingerprint goes in like every other entry, or
                            # the freshness check reads a missing hash as a
                            # changed task and the cell prints "stale" — a
                            # timeout reported as a question nobody asked.
                            "task_hash": asked_fingerprint(task_dir, task),
                            "detail": (
                                f"the driver reports 'misplaced': the artifact "
                                f"was written to {record['misplaced'][0]}, "
                                f"outside the working directory, and is not "
                                f"scored from there"
                                if record.get("verdict") == "misplaced"
                                and record.get("misplaced")
                                else f"the driver reports "
                                     f"{record['verdict']!r}"
                                     + (f" after {record['seconds']}s"
                                        if record.get("seconds") else "")
                                     + " — whatever it left behind is a draft, "
                                       "and a draft is not a result")}
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
                target, why = scored_file(produced, task)
                if target is None:
                    # AMBIGUOUS IS A RESULT, not a coin toss. Scoring the
                    # alphabetically-first file would have graded a shape
                    # sprite as a deck; recording what could not be decided
                    # leaves the run reviewable.
                    scores[key] = {
                        "verdict": "not earned",
                        "task_hash": asked_fingerprint(task_dir, task),
                        "detail": f"which file to score is undecidable: {why}"}
                    unscored += 1
                    continue
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
                                         "instrument_version": versioning.skill_version(ROOT),
                                         "built_version": built_v}
                failed: list[str] = []
                verdict_union: dict[str, Any] = {}
                # The parsed reports, kept out of the score entry: the
                # Evals below read the same two checkers this loop runs.
                raw_runs: dict[str, dict] = {}
                layout_verdicts: dict = {}
                for kind in task["score"]:
                    if kind == "recall":
                        entry["recall"] = score_recall(
                            task, target.read_text(encoding="utf-8", errors="replace"))
                        if entry["recall"]["missed"]:
                            failed.append(f"recall {entry['recall']['score']}"
                                          f"/{entry['recall']['of']}")
                    else:
                        one = score_checks(kind, target, task.get("genre"))
                        raw_runs[kind] = one.pop("_run")
                        entry[kind] = one
                        # HOW MANY GATES HAD A SUBJECT. "Zero gating failures"
                        # does not say how much was held, and the 2026-08-26
                        # round published it over a deck holding eighteen gates
                        # and one holding thirteen — the second had no agenda
                        # page and no page declaring an analysis move, so five
                        # of its clean rows graded nothing. Not a defect in
                        # those rows (a measured absence passes, deliberately);
                        # a number the roll-up was throwing away.
                        report = ((raw_runs[kind].get("reports") or [{}])[0]
                                  or {})
                        if report.get("gates_held") is not None:
                            entry[kind]["gates_held"] = len(report["gates_held"])
                            entry[kind]["gates_not_graded"] = len(
                                report.get("gates_with_nothing_to_grade") or [])
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
                        # Kept apart as well as merged: every key the layout
                        # report returns under `--deliverable` is a gating
                        # verdict by construction, and their names are words
                        # rather than prefixed ids, so the prefix rule that
                        # finds D-and-M gates cannot recognise them.
                        if kind == "layout":
                            layout_verdicts = dict(entry[kind]["verdicts"])
                # `require` is checked ONCE, against the union of every checker's
                # verdicts. Per-kind it needed `got is not None` to skip the other
                # checker's metrics, and that clause also swallowed the case this
                # harness most needs to catch: a required metric that reported
                # nothing at all. check_design returns UNMEASURABLE for a document
                # using none of LUMI's tokens, so an agent emitting exactly that
                # scored green on the scoreboard.
                require = task.get("require") or {}
                if require == "all-gating":
                    # EVERY GATE THIS PACKAGE HOLDS A DELIVERABLE TO, read from
                    # the checkers rather than listed here. The hand-written
                    # list this replaced named six metrics; ten design metrics
                    # gate and fifteen layout verdicts do, so a deck could fail
                    # D19, D1, D3, D4 and eleven layout checks and still score
                    # `pass`. The owner found one by opening it.
                    # `gating` raises on an unreadable register rather than
                    # answering the empty set, which used to mean "nothing is
                    # required". Turned into a finding here: a scoring pass
                    # that cannot read the gate set must say so, not discard a
                    # run that has already driven every agent.
                    try:
                        require = dict.fromkeys(
                            gating.gating_metrics(verdict_union), "ok")
                    except (OSError, ValueError, KeyError) as exc:
                        failed.append(f"the gate register could not be read "
                                      f"({exc}); nothing could be required")
                        require = {}
                    require.update(dict.fromkeys(layout_verdicts, "ok"))
                for metric, want in require.items():
                    got = verdict_union.get(metric)
                    if got is None:
                        failed.append(f"{metric} never reported")
                    elif got not in (want, "n/a"):
                        failed.append(f"{metric}={got}")
                # THE EVALS THRESHOLDS, which no conformance run had ever
                # applied. They are what this package means by a deliverable
                # being good enough — page count, prose-only share, figures per
                # content page, list density, visual share — and a task that
                # scores three checkers and none of these is scoring the
                # markup, not the document.
                if task.get("evals"):
                    failed += _eval_misses(target, task.get("genre"),
                                           design=raw_runs.get("design"),
                                           layout=raw_runs.get("layout"))
                entry["verdict"] = "pass" if not failed else "fail"
                entry["failed"] = failed
                scores[key] = entry
        # WHICH MODEL PRODUCED THE CELL, carried out of the driver record into
        # the score so the board can say it. Attached in one pass rather than
        # in each of the four places a score entry is born, because a cell
        # whose model is missing because one branch forgot it is worse than no
        # column at all. A hand-driven task has no driver.json and honestly
        # records nothing.
        #
        # This became material the day it was written: one run drove three
        # agents, and one of them was pinned to a small model because the
        # account's free-tier quota for the larger ones was spent. Three rows
        # on one table, two of them the CLI's default and one a lite tier, with
        # nothing on the board to tell them apart — which is the reading this
        # file's own driver test already warns about: a cell that says nothing
        # about the model reads as a claim about the agent rather than about
        # one of its configurations.
        for key, cell_entry in scores.items():
            agent_id, _, task_id = key.partition("/")
            driver = run_dir / agent_id / task_id / "driver.json"
            if not driver.exists():
                continue
            try:
                rec = json.loads(driver.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, ValueError) as exc:
                # SAID, NOT SWALLOWED. This `continue`d in silence, so the
                # cell rendered `—` — which is what a HAND-DRIVEN task prints,
                # the case the comment above calls "honestly records nothing".
                # A run killed at its hard cap leaves a truncated driver.json,
                # and that is FM-24's `history.json` instance one file over, in
                # a release that touched this very line. `OSError` and a decode
                # error join `ValueError`: unreadable is unreadable, and only
                # one of the three used to stop the whole scoring run.
                print(f"note  {driver} does not parse ({exc}); this cell "
                      f"records no model")
                cell_entry["model"] = "driver record unreadable"
                continue
            cell = _model_cell(rec)
            if cell is not None:
                cell_entry["model"] = cell
            # THE REST OF THE CONFIGURATION, in the same pass and for the same
            # reason its comment gives: a cell whose model is present because
            # one branch remembered and whose effort is missing because another
            # forgot is worse than a column that is not there. `effort` reached
            # `driver.json` and the trace and nothing else, so the board could
            # show which model ran and never at what reasoning tier.
            # `model_ran` rides along BESIDE the display cell. `cell_entry["model"]`
            # is `_model_cell()`'s sentence — built for a board column, and
            # correct there — so a reader comparing a pin against it compares a
            # pin against prose. A review found `agent_evals` doing exactly
            # that; the raw id is what a comparison needs and only this pass
            # has it.
            for key, source in (("effort", "effort"),
                                ("model_asked", "model"),
                                ("model_ran", "model_ran"),
                                ("trace_id", "trace_id")):
                value = rec.get(source)
                if value is None:
                    continue
                # THE SENTINELS DO NOT TRAVEL AS VALUES. `score` writes
                # `(not pinned)` and `(the CLI's default)` where nothing was
                # pinned, and they are answers rather than absences — but they
                # are answers in a DISPLAY field, and `history.json`'s `config`
                # is a record of what a run was configured as, held to the
                # schema's own effort tuple by `validate`. Carrying the
                # sentinel through put `(not pinned)` into that field and the
                # next unpinned round would have turned CI red on a row the
                # harness itself wrote. It is recorded as an explicit `false`
                # instead, so "nobody pinned this" and "this predates the
                # field" stay different facts — which is what 0.1.617's entry
                # asked for and what the parenthesis was doing the wrong way.
                if str(value).startswith("("):
                    if key == "effort":
                        cell_entry["effort_pinned"] = False
                    elif key == "model_asked":
                        cell_entry["model_pinned"] = False
                    continue
                cell_entry[key] = value
        # BEFORE THE BYTES GO. The pin note has to read the file it is about
        # to lose, and it has to print on the empty-scores exit too — that is
        # the case where the pin is destroyed completely rather than partially,
        # and it was the one case the first version could not reach.
        pin_notes = _pin_guard(run_dir)
        (run_dir / "scores.json").write_text(
            json.dumps(scores, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for key, s in sorted(scores.items()):
            extra = f" ({', '.join(s.get('failed', []))})" if s.get("failed") else ""
            print(f"  {key:38} {s['verdict']}{extra}")
        if not scores:
            print(f"  NOT MEASURED: nothing under {run_dir} matched a known agent and "
                  f"task; `run` writes that layout, and a scoreboard of zero rows is "
                  f"not a scoreboard of passes")
            for line in pin_notes:
                print(line)
            return 1
        print(f"\n{len(scores) - unscored} scored, {unscored} not scored "
              f"-> {run_dir / 'scores.json'}")
        for line in pin_notes:
            print(line)
        return 1 if any(s["verdict"] != "pass" for s in scores.values()) else 0

    # report
    version = versioning.skill_version(ROOT)
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
        scored_here: list[dict] = []
        runs_here = 0
        for t in tasks:
            got = mine.get(t["id"]) or []
            runs_here = max(runs_here, len(got))
            if not got:
                cells[t["id"]] = "—" if not ok else "not run"
                # AND IT JOINS THE DENOMINATOR. `verdicts` was appended to only
                # for tasks that had a score entry, so `len(judged) ==
                # len(verdicts)` compared against "tasks that were scored" and
                # an agent measured on one task of three published a bare
                # `pass` — reachable through `run --drive --task T1-deck`. The
                # comment below has claimed the opposite since it was written.
                # Guarded on `mine`, not on the probe: an agent with no scored
                # task at all must keep falling through to the `not installed`
                # / `cannot be probed` branch below, which is about the agent
                # rather than about a run.
                if mine:
                    verdicts.append("not attempted")
                continue
            scored_here += [s for s in got if isinstance(s, dict)]
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
            # DRIVEN AND EARNED ARE DIFFERENT WORDS AND WERE THE SAME ONE.
            # `judged` counts tasks that produced a verdict, and the roll-up
            # called that "driven" — so the 0.1.605 board reported Hermes as
            # `partial: 1 of 3 driven, all pass` about an agent driven three
            # times, two of which wrote their deliverable outside the working
            # directory, and reported Gemini as `not run` about an agent run
            # three times and rate-limited on every one. Both readings hand the
            # agent's failure to the harness's silence.
            # ATTEMPTED IS A FIELD, NOT AN INFERENCE. Reading it off "the
            # verdict is not `not attempted`" counted a host with the CLI
            # uninstalled as three runs that earned nothing; `score` records
            # which kind of not-earned each cell was, and this reads it.
            attempted = [v for v in scored_here
                         if v.get("attempted") in (True, "yes")]
            if not judged:
                verdict = ("not run" if not attempted else
                           f"run, nothing earned: {len(attempted)} of "
                           f"{len(verdicts)} attempted")
            elif all(v == "pass" for v in judged):
                verdict = "pass" if len(judged) == len(verdicts) else \
                    f"partial: {len(judged)} of {len(verdicts)} earned, all pass"
            elif any(v == "stale" for v in judged) and \
                    not any(v == "fail" for v in judged):
                verdict = "stale"
            else:
                verdict = "fail"
            cli = _short(note) if ok else "driven by hand"
        else:
            # Six of the ten "not installed" rows are a machine away; four can
            # never answer a CLI probe at all — an IDE with no command line and
            # two chat models behind an API. Printing them identically made the
            # board look like ten pieces of pending work when only six are.
            structural = not a.get("probe")
            verdict = ("cannot be probed" if structural
                       else "not installed" if not ok else "not run")
            cli = _short(note) if ok else "—"
        # The models behind this row's cells, deduplicated and in the order
        # met. Usually one; more than one means the row mixes configurations
        # and the board says so instead of averaging them into a verdict.
        seen_models: list[str] = []
        for got in mine.values():
            for s in got:
                m = s.get("model")
                if m and m not in seen_models:
                    seen_models.append(m)
        rows.append({"name": a["name"], "capability": a["capability"],
                     "cli": cli, "model": ", ".join(seen_models) or "—",
                     "tasks": cells, "verdict": verdict,
                     "runs": runs_here})
    record = {"version": version,
              "run_id": ", ".join(f"`{_portable(str(r))}`" for r in runs)
              or "detect-only",
              # The date the scores were written, read from the file, never
              # typed: a board without a date under a table of verdicts is a
              # board whose prose can narrate a different run than its table
              # (it did, for six days, at 0.1.522).
              "run_date": _scores_date(runs),
              "findings": [_portable(f) for f in _findings(runs)],
              "host": f"{sys.platform}", "agents": len(agents),
              "detected": sum(1 for v in probed.values() if v[0]),
              "repeat": max((r["runs"] for r in rows), default=0),
              "structural": sum(1 for r in rows if r["verdict"] == "cannot be probed"),
              "task_ids": [t["id"] for t in tasks], "rows": rows}
    print(render(record))

    if args.redraw:
        # THE TABLE WITHOUT THE HISTORY. A board is a photograph of one
        # measurement session, and every history row carries which version of
        # the rules its agents were measured against — so `--record` on an old
        # run stamps those rows with TODAY's version and claims the agents read
        # rules that did not exist when they ran. That is the misattribution
        # 0.1.605 exists to describe, and it is why the shipped board kept
        # wording the generator no longer produces.
        #
        # Redrawing is the narrow answer: the table, the failure list and the
        # header come from the run directory that is still on disk, and
        # `history.json` is not opened at all. Nothing is re-scored — the same
        # `scores.json` renders — so no verdict can change, only how it is
        # written. Same shape as `restamp`, one line up.
        board = ROOT / "conformance" / "CONFORMANCE.md"
        # WHICH RUN THE BOARD IS ALREADY ABOUT. Nothing compared them, so
        # `--redraw --run <any other round>` rewrote the table with a different
        # session's verdicts, left thirty-six history rows describing the old
        # one, and reported success — with "conformance/history.json untouched"
        # as the reassurance. Redrawing is for when the WORDING changed and the
        # measurement did not; a different measurement is `--record`'s job.
        try:
            standing = board_run_id_line(board.read_text(encoding="utf-8")) or ""
        except OSError as exc:
            print(f"FAIL  {board} cannot be read: {exc}")
            return 1
        if standing.strip() and record["run_id"] not in standing:
            print(f"FAIL  the board is a rendering of {standing.strip()!r} and "
                  f"--run names {record['run_id']}. Redraw rewrites how a "
                  f"measurement is worded, never which measurement it is; "
                  f"recording a different run is `--record`.")
            return 1
        if args.record:
            print("FAIL  --redraw and --record together: one rewrites the "
                  "table only, the other appends history rows. Pick one.")
            return 1
        before = board.read_text(encoding="utf-8")
        outcome = write_board(record)
        print(outcome)
        # BRANCHED ON WHAT write_board SAID, not on whether the file moved.
        # It reports rather than raises — a board with no generated region
        # returns a `FAIL ` string — and diffing the file against itself then
        # printed "the board already reads this way" underneath, as the last
        # line, with exit 0. A wrapper reading the tail or the status saw
        # success over a refusal.
        if outcome.startswith(("FAIL", "note")):
            return 1
        if board.read_text(encoding="utf-8") == before:
            print("ok    the board already reads this way; nothing rewritten")
        else:
            print("redrew the board's generated block from "
                  f"{record['run_id']}; conformance/history.json untouched")
        return 0

    if args.record:
        print(write_board(record))
        # One row per scored agent per run directory, pinned to the artifact
        # by digest: the scores.json stays untracked (results/ is gitignored
        # on purpose), so the digest is what makes a history row evidence
        # rather than an assertion. Idempotent: an identical row is not
        # appended twice.
        import datetime
        import hashlib
        hist_path = history.path(ROOT)
        # THE PATH THAT WRITES read the file with no guard at all until 0.1.636:
        # a history damaged by a merge raised out of `record`, after the run had
        # already been paid for, and took its results with it. Refusing before
        # the write is the whole point of asking first.
        rows_now, problem = history.read_rows(ROOT)
        if problem:
            print(f"FAIL  {problem}; nothing recorded from this run")
            return 1
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
            # WHAT THE CELL WAS RUN AS, and the key that joins it to its cost.
            # A verdict without its configuration is a fact about an agent id,
            # and an agent id is not a thing anybody can run — `cursor` at
            # `grok-4.6-high` and `cursor` on Auto are two different runs
            # wearing one name, which is why the 36 rows before this field
            # cannot be read as a comparison of anything.
            per_config: dict[str, dict[str, dict]] = {}
            per_trace: dict[str, dict[str, str]] = {}
            instruments: set[str] = set()
            for key, value in scored_doc.items():
                agent_id, _, task_id = key.partition("/")
                per_agent.setdefault(agent_id, {})[task_id] = value.get(
                    "verdict", "unscored")
                if value.get("built_version"):
                    per_built.setdefault(agent_id, {})[task_id] = value["built_version"]
                if value.get("instrument_version"):
                    instruments.add(value["instrument_version"])
                # ABSENT STAYS ABSENT — a cell scored before 0.1.617 carries
                # none of these, and an invented "(unknown)" would make "nobody
                # recorded it" and "this predates the field" the same string.
                # Named `configured` rather than `cell`: `cell` is a `str |
                # None` earlier in this function, and reusing it here is how
                # mypy caught the shadow on the first run.
                configured: dict = {
                    k: value[k]
                    for k in ("model", "model_ran", "effort", "model_asked")
                    if value.get(k)}
                # An explicit `false` is a value, so `if value.get(k)` would
                # drop it — which is the bug that would turn "nobody pinned
                # this" back into silence one layer down.
                for k in ("effort_pinned", "model_pinned"):
                    if k in value:
                        configured[k] = value[k]
                if configured:
                    per_config.setdefault(agent_id, {})[task_id] = configured
                if value.get("trace_id"):
                    per_trace.setdefault(agent_id, {})[task_id] = value["trace_id"]
            # PORTABLE, like the board's run id. 0.1.568 collapsed the home
            # directory in what `report` RENDERS and missed what it RECORDS, so
            # every history row kept writing the operator's username into a
            # tracked file — `check_local_paths` caught it on the first refresh
            # after that release. The de-duplication below compares against the
            # same form, or a re-record would append a second row for one run.
            where = _portable(str(name))
            for agent_id, task_verdicts in sorted(per_agent.items()):
                row = {"skill_version": version, "agent": agent_id,
                       "date": datetime.date.today().isoformat(),
                       "run_dir": where, "tasks": task_verdicts,
                       "scores_sha256": digest}
                # IDEA-8: the ruler and the artifact vintages, when the
                # scores carry them (older scores.json rows predate the
                # fields and stay honestly silent).
                if instruments:
                    row["instrument_version"] = sorted(instruments, key=versioning.sort_key)[-1]
                if per_built.get(agent_id):
                    row["built"] = per_built[agent_id]
                if per_config.get(agent_id):
                    row["config"] = per_config[agent_id]
                if per_trace.get(agent_id):
                    row["traces"] = per_trace[agent_id]
                if not any(r.get("agent") == agent_id
                           and r.get("run_dir") == where
                           and r.get("scores_sha256") == digest
                           for r in rows_now):
                    rows_now.append(row)
                    added += 1
        hist_path.write_text(json.dumps(rows_now, indent=2) + "\n",
                             encoding="utf-8")
        print(f"\nrecorded {added} new history row(s) -> "
              f"{hist_path.relative_to(ROOT)} ({len(rows_now)} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
