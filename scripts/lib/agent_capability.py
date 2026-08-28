#!/usr/bin/env python3
"""What an agent can be RUN AS — one module, three questions, three facts.

WHY THIS EXISTS, AND WHY IT IS NOT ONE FUNCTION. The owner asked why the model
vocabulary, the pinned model and the model that ran are fetched by three
separate paths, and asked for one. They are three DIFFERENT facts and merging
them is the defect three releases already paid for:

* **capability** — what does this CLI OFFER? Answered by asking the CLI
  (`probe_models`) and remembered in `conformance/vocabularies.json`.
* **intent** — what did we ASK for? Recorded in the trace as the pin.
* **observation** — what did the CLI SAY it used? Recorded as `model_ran`.

0.1.614 fixed a board that recorded the model asked for and never the one that
ran; 0.1.623 fixed a join that assumed those two strings agree; 0.1.625 fixed a
cell that pooled runs pinned to different models. Collapsing the three would
re-open all of it. **What was genuinely duplicated is the vocabulary KNOWLEDGE
around them** — how effort reaches a CLI, whether a level exists, whether two
names are the same model, and where the recorded vocabulary lives — and that is
what this module owns.

**The registry's prose already knew what the code did not.** `adapters/hermes.md`
records that `--reasoning` takes eight levels and `adapters/cursor.md` that Grok
4.6 tops out at `xhigh` with no `max` — both written down, in sentences no code
read, while `trace_schema.ENUMS["effort"]`'s five levels (Claude Code's, and
correct for Claude Code) were applied to every platform. Nothing validated a pin
before spending a run's budget on it: `--effort max` against Cursor composed an
id the CLI does not have, and the CLI was what found out.
"""
from __future__ import annotations

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

import json  # noqa: E402
import os  # noqa: E402
import pathlib  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

import repo_files  # noqa: E402 — one repository root

VOCAB_RELATIVE = "conformance/vocabularies.json"

FLAG, IN_MODEL, NONE = "flag", "in_model", "none"


_root = repo_files.repo_root


# --- capability: what does this CLI offer? -----------------------------------

def probe_models(agent: dict) -> tuple[str, str]:
    """-> (state, detail) for what this agent can be pointed at.

    FOUR STATES, and the fourth is the one a review had to add. `asked` carries
    the ids the CLI returned; `waived` carries the registry's REASON — a fact
    about the platform; `absent` is a declared probe whose binary is not on this
    machine — a fact about the machine, which one install changes; `failed` is a
    declared, present probe that did not answer, which is an accident. The first
    version filed `absent` under `waived` while the docstring said a waiver is a
    reason and these are not.

    Read-only by construction: the only argv in the registry is
    `cursor-agent --list-models`, and the manifest guard requires a list of
    strings, so nothing here can compose a command out of operator input.
    """
    argv = agent.get("models")
    if not argv:
        return "waived", agent.get("models_waiver", "no models probe declared")
    if not shutil.which(argv[0]):
        return "absent", (f"{argv[0]} is not installed here; the registry "
                          f"declares a probe, so this is one install away")
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except Exception as exc:                                    # noqa: BLE001
        return "failed", f"{' '.join(argv)}: {exc.__class__.__name__}"
    if out.returncode != 0:
        return "failed", (f"{' '.join(argv)} exited {out.returncode}: "
                          f"{(out.stderr or out.stdout).strip()[:80]}")
    # An id is the first whitespace-delimited token of a line that carries one.
    # Cursor prints `id - Display Name`; a line with no ` - ` is a heading or a
    # blank, and is skipped rather than being recorded as an id called
    # "Available".
    ids = [line.split(" - ", 1)[0].strip() for line in out.stdout.splitlines()
           if " - " in line and not line.startswith(" ")]
    if not ids:
        return "failed", (f"{' '.join(argv)} answered, and nothing in its output "
                          f"parses as an id — an empty vocabulary from a working "
                          f"probe is a parse failure, not an empty CLI")
    return "asked", ", ".join(ids)


def vocab_path(root: pathlib.Path | None = None) -> pathlib.Path:
    return _root(root) / VOCAB_RELATIVE


def recorded_vocabularies(
        root: pathlib.Path | None = None) -> tuple[dict, str | None]:
    """-> ({agent id: {ids, asked_on, ...}}, problem). Absent is not a problem.

    `history.read_rows`'s shape, for the same reason and on the same kind of
    file: `conformance/vocabularies.json` is tracked and every probe round
    appends to it, which is the shape most likely to arrive from a merge
    unparseable. Until 0.1.640 this was a bare `json.loads` — a damaged store
    raised `JSONDecodeError` out of `validate_pin` mid-drive, and a store
    holding `null` or a list raised `AttributeError` from the `.get` below.
    """
    path = vocab_path(root)
    if not path.exists():
        return {}, None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {}, f"{path} could not be read ({exc})"
    if not isinstance(doc, dict):
        return {}, (f"{path} holds a {type(doc).__name__}, not a map of agent "
                    f"id to vocabulary")
    # THE ENTRIES TOO, not only the document. Validating the outer mapping and
    # returning the inner values raw left `record_vocabularies`'s
    # `(prior.get(aid) or {}).get("ids")` to raise on `{"cursor": "oops"}` —
    # in the WRITE path, after the probes had been paid for, which is the
    # sentence three lines above it.
    bad = sorted(k for k, v in doc.items() if not isinstance(v, dict))
    if bad:
        return {}, (f"{path} records {bad} as something other than a "
                    f"vocabulary — an entry, not the document, is damaged")
    return doc, None


def offered(agent_id: str,
            root: pathlib.Path | None = None) -> tuple[list[str] | None, str | None]:
    """-> (the ids this CLI last offered, a problem). None ids = never asked.

    None and `[]` are different answers and the caller must be able to tell
    them apart: a waived or failed probe records NOTHING, because writing an
    empty set would make "this CLI offers nothing" and "we could not ask" the
    same row.

    THREE ABSENCES, not two, since 0.1.640. Never asked is `(None, None)`; a
    store that cannot be read is `(None, problem)`; and an entry whose `ids` is
    not a list is `(None, problem)` too — it used to join the honest absence
    silently, which turned a corrupted record into an unarmed pin check.
    """
    doc, problem = recorded_vocabularies(root)
    if problem:
        return None, problem
    entry = doc.get(agent_id)
    if not entry:
        return None, None
    ids = entry.get("ids") if isinstance(entry, dict) else None
    if not isinstance(ids, list):
        return None, (f"{vocab_path(root)} records {agent_id} with no list of "
                      f"ids — a damaged entry, not an agent nobody asked")
    return list(ids), None


def record_vocabularies(answered: dict,
                        root: pathlib.Path | None = None) -> list[str]:
    """Store what the probes answered; -> one line per vocabulary that MOVED.

    Only agents that ANSWERED belong in `answered`; see `offered` for why.
    """
    path = vocab_path(root)
    prior, problem = recorded_vocabularies(root)
    if problem:
        # BEFORE THE WRITE, because the probes have already been paid for and
        # `prior.update()` on a damaged store threw them away.
        raise SystemExit(f"FAIL  {problem}; nothing recorded")
    lines = []
    for aid, asked in sorted(answered.items()):
        was = (prior.get(aid) or {}).get("ids")
        now = list(asked["ids"])
        if isinstance(was, list) and was != now:
            gone = sorted(set(was) - set(now))
            arrived = sorted(set(now) - set(was))
            lines.append(f"  CHANGED {aid}: "
                         + (f"gone {gone} " if gone else "")
                         + (f"new {arrived}" if arrived else ""))
    prior.update(answered)
    # TMP + REPLACE, the idiom `trace.py` carries for the same reason: a bare
    # write truncates on a crash, and this release taught the READER to report
    # a damaged store while leaving the writer able to produce one.
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(prior, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)
    return lines


# --- how effort reaches this CLI, and whether a level exists -----------------

def effort_style(agent: dict) -> str:
    """-> FLAG, IN_MODEL or NONE.

    Three shapes, and the registry already declared which: a flag
    (`--effort`, `--reasoning`), a template that spells the level inside the
    model id (`{model}-{effort}`), or no effort concept at all.
    """
    if agent.get("drive_effort_in_model"):
        return IN_MODEL
    if agent.get("drive_effort_flag"):
        return FLAG
    return NONE


def declared_efforts(agent: dict) -> tuple[list[str] | None, str | None]:
    """-> (the levels this CLI accepts, why there is no list). One or the other.

    The `models` / `models_waiver` pattern, for the second axis. The values
    come from each CLI's own help — Hermes accepts eight, Claude Code five,
    Gemini has no such concept — and stop being Claude Code's five generalised
    to everyone.
    """
    levels = agent.get("efforts")
    if levels:
        return list(levels), None
    return None, agent.get("efforts_waiver")


def effort_refusal(agent: dict, level: str) -> str | None:
    """-> the sentence saying this level is wrong for this CLI, or None.

    A REFUSAL, not a permission. Three cases and only one of them refuses:

    * the agent declares a list and the level is not in it — refused, naming the
      list. **Not the `--effort max` case**, which this docstring claimed until
      a review checked it: Cursor's list CONTAINS `max`, because `max` ids exist
      for other families, and what refuses `cursor-grok-4.6-max` is
      `validate_pin` against the recorded vocabulary. With today's registry
      every driveable platform declares a superset of the five levels a trace
      can record, so this branch cannot fire from the CLI at all. It is here for
      a platform that declares FEWER — the shape the registry is free to grow
      the day a CLI drops a level — and `tests/test_agent_capability.py` drives
      it with exactly that agent. A check nothing reaches today is worth saying
      out loud rather than leaving to be rediscovered.
    * the agent declares a list and the level is in it — fine.
    * the agent declares no effort vocabulary at all — NOT refused. Gemini has
      no reasoning level, and a horse race that passes one default `--effort`
      across four CLIs must still run the one that has no such concept; the
      driver pins nothing there and records `(not pinned)`, which is the honest
      answer it has given since 0.1.531.

    An agent whose level lives inside the model id cannot answer at this
    altitude either — the levels are a property of the model FAMILY there
    (`cursor-grok-4.6-max` does not exist while `max` ids do exist for other
    families) — so what it declares is the platform's suffix vocabulary and the
    per-family question goes to `validate_pin` on the composed id.
    """
    levels, _waiver = declared_efforts(agent)
    if levels is None or level in levels:
        return None
    return (f"{agent['id']} does not accept effort {level!r}; its registry "
            f"record declares {levels}")


def effort_in_model(agent: dict, model: str | None) -> str | None:
    """-> the level a composed model id already carries, or None.

    Registry-driven rather than guessed: only a platform whose template ENDS in
    `{effort}` can carry one, and the level has to be one the agent's `efforts`
    list declares. `cursor-grok-4.6-high` carries `high`; `cursor-grok-4.6`
    carries nothing, and its `4.6` is not a level — the first implementation
    read it as one.

    THE LAST TWO SEGMENTS, not the last. `adapters/cursor.md` records that
    EVERY Cursor id has a `-fast` twin, and the recorded vocabulary has eight
    of twenty-three: `cursor-grok-4.6-high-fast` ends in `fast`, so reading
    only the final segment found the level on none of them and put every twin
    back in the `(not pinned)` cell this function exists to empty. Two is the
    limit rather than "scan until a level appears", because a model whose NAME
    contains a level word would otherwise be misread from arbitrarily far in.
    """
    template = agent.get("drive_effort_in_model")
    if not template or not model or not template.endswith("{effort}"):
        return None
    levels, _waiver = declared_efforts(agent)
    if not levels:
        return None
    prefix = template[:-len("{effort}")].replace("{model}", "")
    if not prefix:
        return None
    segments = model.split(prefix)
    for segment in reversed(segments[-2:]):
        if segment in levels:
            return segment
    return None


def compose_model(agent: dict, model: str | None,
                  effort: str | None) -> tuple[str | None, bool]:
    """-> (the model id to pass, whether the effort ends up pinned)."""
    template = agent.get("drive_effort_in_model")
    if model and effort and template:
        return template.format(model=model, effort=effort), True
    if effort and agent.get("drive_effort_flag"):
        return model, True
    return model, False


OK, REFUSED, UNVALIDATED = "ok", "refused", "unvalidated"


def validate_pin(agent: dict, model: str | None,
                 root: pathlib.Path | None = None) -> tuple[str, str]:
    """-> (OK | REFUSED | UNVALIDATED, the sentence for the last two).

    Answered ONLY from a recorded vocabulary. An agent nobody has probed is
    UNVALIDATED, never OK: this is a check against evidence, and inventing a
    verdict where there is no evidence is the failure mode the four-state probe
    above exists to avoid.

    THREE STATES SINCE 0.1.640, and the third is the one a review found
    missing. A pin validated against a real vocabulary and a pin never checked
    at all both returned `(True, "")` and printed nothing — the same output for
    the check working and the check not running, at the point the module's own
    comment says the check matters most. A damaged store joined them silently,
    which reverted the pin check to unarmed on the run it was written to stop.
    """
    if not model:
        return OK, ""
    ids, problem = offered(agent["id"], root)
    if problem:
        return UNVALIDATED, problem
    if ids is None:
        return UNVALIDATED, (f"{agent['id']} has no recorded vocabulary, so "
                             f"{model!r} was not checked against one — "
                             f"`run_conformance.py detect --models --record`")
    if model in ids:
        return OK, ""
    return REFUSED, (f"{agent['id']} does not offer {model!r}. Its last recorded "
                     f"vocabulary ({len(ids)} ids) has "
                     f"{', '.join(sorted(ids)[:4])}…; re-probe with "
                     f"`run_conformance.py detect --models --record` if the CLI "
                     f"has changed")


# --- observation: are these two names the same model? ------------------------

def model_tokens(name: str | None) -> list[str]:
    """-> a model name as the words a vendor spells it with.

    Tokens rather than a squashed string, because squashing is what made
    `cursor-grok-4.6-high` and `cursor-grok-4.6-high-fast` the same model — and
    `adapters/cursor.md` says in this repository's own words that EVERY id has
    a `-fast` twin. A rule that merges every twin is not a rule.
    """
    raw, run = [], ""
    for ch in str(name or "").lower():
        if ch.isalnum():
            run += ch
        elif run:
            raw.append(run)
            run = ""
    if run:
        raw.append(run)
    # ONE SPELLING OF ONE EFFORT LEVEL, and it is not a model alias. `xhigh` is
    # a member of `trace_schema.ENUMS["effort"]` — a tuple this package owns —
    # and `cursor-agent --list-models` prints it as `Extra High`. Without this
    # the first real xhigh run read **not honoured** on the board: pinned to
    # `cursor-grok-4.6-xhigh`, answered `Cursor Grok 4.6 Extra High`, and
    # called a substitution. Collapsing the pair rather than expanding it keeps
    # the catch that matters — `high` against `Extra High` remains two
    # different token lists and still reads as substituted.
    out: list[str] = []
    skip = False
    for i, tok in enumerate(raw):
        if skip:
            skip = False
            continue
        if tok == "extra" and i + 1 < len(raw) and raw[i + 1] == "high":
            out.append("xhigh")
            skip = True
        else:
            out.append(tok)
    return out


def _run_of(short: list[str], long: list[str]) -> bool:
    """-> is `short` a CONTIGUOUS run of tokens inside `long`?

    Contiguous, not a scattered subsequence. Scattered let
    `cursor-grok-4.6-high` sit inside `Cursor Grok 4.6 Extra High` by stepping
    over `extra` — and that pair is `-high` against `-xhigh`, the one
    substitution this comparison exists to catch.
    """
    return any(long[i:i + len(short)] == short
               for i in range(len(long) - len(short) + 1))


def same_model(asked: str | None, ran: str | None) -> bool | None:
    """-> True honoured, False substituted, **None not established**.

    THREE ANSWERS, because a pin and the name a CLI answers with are two
    vocabularies that are only sometimes comparable:

    * **the same tokens** — honoured. `cursor-grok-4.6-high` and
      `Cursor Grok 4.6 High` are the same words.
    * **one a contiguous run of tokens inside the other** — NOT ESTABLISHED, and this is the
      answer the first version did not have. `opus` is an alias that answers as
      `claude-opus-5`; `cursor-grok-4.6-high` answered as `Cursor Grok 4.6` on
      one task and `Cursor Grok 4.6 High` on two others IN ONE ROUND; and
      `cursor-grok-4.6-high-fast` contains every token of
      `cursor-grok-4.6-high`. The first two are almost certainly honoured, the
      third is certainly not, and nothing available here separates them. So it
      says so. Guessing `True` printed `honoured` over a `-fast` twin, and
      `adapters/cursor.md` records that every id has one.
    * **anything else** — substituted. `high` against `xhigh`, `grok` against
      `composer`.

    `None` is not a soft `False`: `agent_evals._honoured` folds it as no evidence and the
    board prints a dash, which is `na_means`'s discipline one layer down.
    """
    a, r = model_tokens(asked), model_tokens(ran)
    if not a or not r:
        return None
    if a == r:
        return True
    return None if _run_of(a, r) or _run_of(r, a) else False
