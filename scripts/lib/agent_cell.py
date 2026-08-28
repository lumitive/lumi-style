#!/usr/bin/env python3
"""What was ASKED FOR, as a type: the cell, and the ruler beside it.

WHY THIS MODULE EXISTS. `conformance/agent-evals.json` declares the unit of
measurement — `"cell": ["agent", "model", "effort"]`, with the note that an
agent id alone is not a configuration — and no code read that declaration. The
unit was instead computed four times, in three shapes, with no shared
constructor: a 5-tuple in `agent_evals.cells()`, the declared 3-tuple in
`agent_evals`'s `plan`, and a 2-tuple with the agent dropped in
`agent_runs.matrix()`. That is the defect `evals/single-source.json` refuses one
layer down — it catches a duplicated IMPLEMENTATION, and nothing caught a
duplicated CONCEPT.

INTENT ONLY, and the boundary is the point. `agent_capability.py`'s docstring
records that merging capability (what a CLI offers), intent (what we asked for)
and observation (what it said it ran) is the defect 0.1.614, 0.1.623 and 0.1.625
each paid for. A `Cell` is the ask. `model_ran` and `offered()` never enter it,
and `cell_of_config` reads `model_asked` rather than `model` for that reason.

THE RULER IS BESIDE THE CELL, NEVER INSIDE IT. `Measured` pairs them, and the
distinction is what the two shapes above were disagreeing about: one folded the
ruler in, the other dropped half the cell. **Anything computing a median groups
on `Measured`; nothing groups on `Cell`.** A cell is what you ask for; a
measured cell is what you may pool.
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

import dataclasses  # noqa: E402

# The axes, held to `conformance/agent-evals.json`'s declaration by check_repo's
# `cell axes` guard, which reads the register — this module does not. It ships
# to the consumer projection and `conformance/` does not, so a path to it here
# would be a reference that resolves in one tree and dangles in the other.
AXES = ("agent", "model", "effort")

# WHAT MEASURED IT, not what was measured. 0.1.626 added these two because
# pooling releases misattributed a headline number by 12.8%: cursor at
# `cursor-grok-4.6-high` read 6,290 tokens per page pooled across
# 0.1.542-0.1.623 and 7,093 under 0.1.623 alone. Before that release the number
# was one median over both rulers, and the difference read as the model's.
RULER_AXES = ("skill_version", "cli_version")

# The display sentences the pipeline writes when nothing was pinned. They are
# prose for a person and must never reach a key: `(the CLI's default)` as a
# model would make two unpinned runs of different models one cell. The driver
# handles them by hand at three sites; the constructor below refuses them once.
SENTINEL_PREFIX = "("


class CellError(ValueError):
    """A cell that cannot be built. Raised, never `sys.exit` — the CLI decides
    what to print, and a library that exits cannot be unit-tested."""


def _clean(value: object, field: str) -> str | None:
    """-> a normalized axis value, or None for an absence.

    Empty and whitespace-only collapse to None, because `close --cli-version ""`
    stores `""` and `render` prints `""` and `None` identically — one
    configuration rendered as two rows with two medians until 0.1.626 stripped
    it at one call site. Stripping it in the constructor is that fix, everywhere.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith(SENTINEL_PREFIX):
        raise CellError(
            f"{field}={text!r} is a display sentence, not a value. "
            f"`(not pinned)` and `(the CLI's default)` say a person should read "
            f"'nothing was pinned'; as a key they would pool every unpinned run "
            f"into one cell")
    return text


@dataclasses.dataclass(frozen=True, slots=True)
class Cell:
    """One configuration: what a run was ASKED to be."""

    agent: str
    model: str | None = None
    effort: str | None = None

    def key(self) -> tuple[str, str | None, str | None]:
        """-> the declared 3-tuple. `agent_evals`'s `plan` counts these."""
        return (self.agent, self.model, self.effort)

    def drop_agent(self) -> tuple[str, str]:
        """-> `(model, effort)` with absences as `?`, for the model x effort
        matrix.

        A NAMED PROJECTION, and the name is the point: `agent_runs.matrix()`
        drops the agent because its grid asks "what does this model at this
        level cost", a question whose answer does not depend on which CLI
        carried it. That reason was written nowhere; it is written here, and the
        `?` is the matrix's own spelling for an axis a run did not record.
        """
        return (self.model or "?", self.effort or "?")


@dataclasses.dataclass(frozen=True, slots=True)
class Ruler:
    """What measured a run: the rule set, and the CLI build that ran it."""

    skill_version: str | None = None
    cli_version: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class Measured:
    """A cell together with the ruler that measured it. The poolable unit."""

    cell: Cell
    ruler: Ruler

    def pooled_key(self) -> tuple:
        """-> the grouping key for a median.

        Byte-identical to the 5-tuple `agent_evals.cells()` built by hand, in
        the same order, so the boards it produces do not move.
        """
        return (self.cell.agent, self.cell.model, self.cell.effort,
                self.ruler.skill_version, self.ruler.cli_version)


def cell(agent: object, model: object = None, effort: object = None) -> Cell:
    """-> a Cell, normalized. The one constructor.

    Raises `CellError` on an absent agent — a cell without one is not a
    configuration, which is the sentence `agent-evals.json`'s `cell_note` opens
    with — and on a display sentence in any axis.
    """
    name = _clean(agent, "agent")
    if name is None:
        raise CellError("a cell needs an agent; an agent id alone is not a "
                        "configuration, and neither is a configuration without "
                        "one")
    return Cell(name, _clean(model, "model"), _clean(effort, "effort"))


def cell_of_trace(trace: dict) -> Cell:
    """-> the cell a trace records. `model` on a trace IS the pin."""
    return cell(trace.get("agent"), trace.get("model"), trace.get("effort"))


def cell_of_config(agent_id: str, config: dict | None) -> Cell | None:
    """-> the cell a history row's per-task config records, or None.

    `model_asked`, NEVER `model`. A score entry's `model` is `_model_cell()`'s
    display sentence — `cursor-grok-4.6-high (asked cursor-grok-4.6-xhigh)` —
    and joining on those is the defect 0.1.623 fixed. None when the pins are not
    both recorded: a task with nothing pinned matches nothing, rather than
    matching every other unpinned task.
    """
    conf = config or {}
    asked, level = conf.get("model_asked"), conf.get("effort")
    if not asked or not level:
        return None
    try:
        return cell(agent_id, asked, level)
    except CellError:
        return None


def ruler_of_trace(trace: dict) -> Ruler:
    return Ruler(_clean(trace.get("skill_version"), "skill_version"),
                 _clean(trace.get("cli_version"), "cli_version"))


def measured_of_trace(trace: dict) -> Measured:
    """-> the cell and the ruler a trace records, as one value."""
    return Measured(cell_of_trace(trace), ruler_of_trace(trace))

def parse_pin(text: str, known_agents: frozenset | set,
              allowed_efforts: tuple = ()) -> tuple[str | None, str | None, str | None]:
    """-> (agent | None, model | None, effort | None) from `[AGENT=]MODEL[@EFFORT]`.

    THE ONE SPELLING OF A CELL ON A COMMAND LINE. It replaces two flags whose
    values had to agree by convention: `--model cursor=X --effort cursor=high`
    said one thing in two places, and `--effort cursor=low --effort cursor=high`
    silently kept the last, so one agent could never be asked for two levels.

    `agent=` is optional and sets one agent's pin; without it the pin is the
    default for every agent, which is what a horse race between three CLIs with
    three different model ids needs.

    `@` separates the level and is safe: no model id in any recorded vocabulary
    contains one. The LAST `@` splits, so a model id that somehow carried one
    keeps it. `@high` alone pins the level and leaves the model to each CLI;
    `agent=model` leaves the level to it.

    `allowed_efforts` is the caller's, not this module's, and the distinction is
    the one `run_conformance` states at the flag: the tuple a caller passes is
    what a TRACE can record, which is a smaller question than what a CLI
    accepts. Empty means "do not check here".
    """
    raw = str(text or "").strip()
    if not raw:
        raise CellError("an empty --cell pins nothing")
    agent, sep, rest = raw.partition("=")
    if not sep:
        agent, rest = "", raw
    agent = agent.strip()
    if agent and agent not in known_agents:
        raise CellError(f"--cell {text!r}: no platform in the registry with id "
                        f"{agent!r}")
    model, at, effort = rest.rpartition("@")
    if not at:
        model, effort = rest, ""
    model, effort = model.strip(), effort.strip()
    if not model and not effort:
        raise CellError(f"--cell {text!r} names neither a model nor a level")
    if effort and allowed_efforts and effort not in allowed_efforts:
        raise CellError(
            f"--cell {text!r}: {effort!r} is not one of "
            + "|".join(allowed_efforts)
            + " — the levels a trace can record, which is a smaller question "
              "than what a CLI accepts")
    # A LEVEL WHERE A MODEL SHOULD BE is what an operator types on the first
    # try; say the fix rather than pinning a model called `high`.
    if model and not effort and allowed_efforts and model in allowed_efforts:
        raise CellError(f"--cell {text!r} pins a model named {model!r}; did you "
                        f"mean `@{model}`?")
    return (agent or None, model or None, effort or None)
