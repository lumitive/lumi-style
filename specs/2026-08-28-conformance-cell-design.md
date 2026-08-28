# The cell, and the tool that could not name it

Date: 2026-08-28 · Status: in progress; the releases that implement it cite
this file.

## What was asked

The owner read the parameter surface of `scripts/ops/run_conformance.py` and
said its parameters are accreted rather than designed — that the accretion is
why each iteration and each test costs more than the last, and why quality is
hard to hold. She named five specifics and asked for a redesign:

1. `--model` and `--effort` should not be two parameters. A model always runs at
   some effort, and one model may be given different ones.
2. `--models` and `--model` differ by one letter and mean unrelated things.
3. `--budget` and `--hard-cap` look redundant; she proposed one `maxbudget`.
4. Across the parameter set there is no visible design logic.
5. The subcommand-to-parameter relationship is not clear.

And the sixth, which is the one the other five are symptoms of: **the function
has no domain abstraction.**

## The diagnosis

**The domain unit is wrong at one end of the pipeline.** The board's unit is a
CELL — `agent × model × effort` — and `conformance/agent-evals.json:5` declares
exactly that. The driver's unit is the AGENT: its loop is `agent × task`, and
model and effort are two scalars hung on an agent.

**The cell is implemented four times and shared zero times.**

| where | shape |
|---|---|
| `conformance/agent-evals.json:5` | declared as `[agent, model, effort]` — **read by no code** |
| `scripts/ops/agent_evals.py:337` | a 5-tuple, adding `skill_version` and `cli_version` |
| `scripts/ops/agent_evals.py:709` | projected back to the 3-tuple |
| `scripts/lib/agent_runs.py:117` | a 2-tuple, with the agent dropped |

There is no shared constructor and no shared type. This is the defect
`evals/single-source.json` was built to refuse, one layer up: that register
catches a duplicated IMPLEMENTATION, and nothing catches a duplicated CONCEPT.

**The consequence is reconstruction.** Because the driver never writes the cell
down as a key, three readers rebuild it: `score` lifts the fields into a score
entry (`run_conformance.py:2716-2741`), `report --record` whitelists them into a
`config` map (`:3020-3036`), and `agent_evals._sibling_trace` (`:177-221`) has
to infer "these two tasks were the same configuration" from `(model_asked,
effort)` — forty-five lines deducing a fact the writer knew.

**And the release gate does not know what a configuration is.**
`scripts/check/check_evidence.py:228` keys conformance freshness on the agent
alone.

## The evidence that settles the shape

Thirty run directories under the owner's conformance folder. **Sixteen encode a
cell in the run id by hand** — `r18-low`, `r18-medium`, `r18-high`, `r18-xhigh`,
`r19-{low,medium,high,xhigh}-{2,3}`, `0.1.613-grok46high`, `0.1.614-grok46-2020`
— and `matrix-2026-08-21/` is the missing directory level, built by hand a month
ago:

```
matrix-2026-08-21/{low,medium,high,high-loop}/<agent>/T1-deck/
```

The layout is not a proposal. It is the promotion of an operator workaround that
has been in daily use since 2026-08-21, and it exists because
`<run>/<agent>/<task>` cannot hold two cells of one agent — the driver `rmtree`s
the directory before driving (`:2229-2232`), so the second cell destroys the
first in silence.

**Open, and deliberately not decided here**: her hand-built tree puts the cell
ABOVE the agent; the plan puts it below. Agent-first matches the code's grain
(one worker per agent, `report` iterates the registry); cell-first matches how
she reads a matrix. Cheap to choose before the layout release, expensive after.

## The decisions

Three from the owner:

1. **A general "drive agents over a task matrix" tool**, with conformance as one
   suite of it. Tasks and scoring become replaceable inputs.
2. **A hard cutover** — no compatibility layer, no deprecation window; every
   call site moves in the same commit as the change.
3. **The output directory carries the cell.**

Three corrections the design made to what was asked, each with its reason:

**`--budget` and `--hard-cap` are not redundant.** `_run_with_budget`
(`:202-293`) grants the base outright and renews on signs of life up to the hard
cap. The comment at `:126-158` records the measurement that produced this shape:
`DRIVE_TIMEOUT = 1800` killed Hermes on 2026-08-21 while it was still working —
its deck's mtime is six seconds before the driver record's, and it was inside
the repair loop for its third gate. One number deletes the floor, and a quiet
first minute then kills a healthy run. The answer to the real complaint — two
peer integers with no stated relationship read as two names for one thing — is
**one parameter carrying one policy**: `--budget FLOOR[:CEILING]`, default
`1800:3600`, the relationship visible in the colon. `--budget 3600:3600` is
expressible and means no renewal; the help text says so, so it is a choice
rather than an accident. Recorded in `FAILURE_MODES.md` as a declined mechanism.

**`<model>-<effort>` is wrong for a platform that spells the effort inside the
model id.** Cursor's `drive_effort_in_model` composes `cursor-grok-4.6-high`, so
the naive slug is `cursor-grok-4.6-high-high`. When the effort is already in the
id the slug is the id.

**A directory name is intent, never a join key.** The cell directory carries a
`cell.json`; downstream reads that file rather than parsing the path. This is
`agent_capability.py`'s capability / intent / observation separation applied to
the filesystem: a path can only ever record what was ASKED, and `model_ran` is a
different fact. Parsing a rendered string back into a key is the defect
`agent_evals.earned()`'s docstring already describes.

## The domain model

`scripts/lib/agent_cell.py` owns INTENT only. `agent_capability.py`'s docstring
records that merging capability, intent and observation is the defect 0.1.614,
0.1.623 and 0.1.625 each paid for; a cell is what was asked for, and `model_ran`
and `offered()` never enter it.

```
AXES       = ("agent", "model", "effort")
RULER_AXES = ("skill_version", "cli_version")

Cell     = (agent, model, effort)          what was asked for
Ruler    = (skill_version, cli_version)    what measured it
Measured = (cell, ruler)                   one measurement
```

**The ruler is beside the cell, not inside it.** 0.1.626 added the two ruler
axes because pooling releases misattributed a headline number by 12.8% — cursor
at `cursor-grok-4.6-high` read 6,290 tokens per page pooled across
0.1.542–0.1.623 and 7,093 under 0.1.623 alone. That measurement moves into
`Ruler`'s docstring, where it is the type's reason for existing rather than a
comment on one function.

**The invariant**: anything computing a median groups on `Measured`, never on
`Cell`. A cell is what you ask for; a measured cell is what you may pool.

**The register stops being unread.** `check_cell_axes` holds
`agent-evals.json:5` to `AXES`, requires every axis to be a
`trace_schema.PRODUCER_FIELDS` member, refuses `model_ran` as an axis, and —
the second question convention 11 asks — FAILS on a register that declares no
cell at all rather than skipping, because a skip prints what a clean tree
prints.

## The boundary the redesign may not cross

`conformance/README.md:24-31` records why the driver did not move when the
analysis did at 0.1.622: four of its five couplings are not agent evaluation.
Those four are what stays in `run_conformance.py` — `check_repo` imports it by
name, `release.py` shells `restamp`, `ci.yml` shells `validate`, `stamps.py`
owns the board's stamp. The general tool DRIVES, `agent_evals` ANALYSES, and
conformance is a SUITE. Nothing in this design re-merges what that release
separated.

Two consequences worth writing down before the work starts:

- **The `validate` command string is frozen.** `check_evidence.OBLIGATIONS`
  holds the literal, `validate_maps()` asserts its path token is a real file,
  and `releases/perf-baseline.json:105` keys a timing row on its sha256.
  Changing it orphans that row silently — a label miss warns about nothing.
- **`board_header`, `board_run_id_line`, `_board_run_version`, `render` and
  `cmd_restamp` do not move.** `check_repo.py:3923-4019` imports them by name
  and requires the board's header to equal what `board_header` writes, and
  `tests/test_board_staleness_clause.py:281` forbids the header literal from
  appearing anywhere else. This constraint happens to coincide exactly with the
  conformance / general line, which is why the split is possible at all.

## Stages

Each is one release that leaves `python3 scripts/preflight.py` green.

1. **The type.** `agent_cell.py`, `check_cell_axes`, an `evals/single-source.json`
   entry, and only the four existing cell computations repointed. No CLI change.
   Worth shipping alone: the declaration becomes a contract, and the 5-tuple gets
   a name with its measurement attached.
2. **The CLI.** Subparsers; `--cell` replaces `--model` and `--effort`;
   `--budget FLOOR[:CEILING]` replaces `--budget`/`--timeout`/`--hard-cap`;
   `--models` becomes a verb. Ten of twelve flags belong to exactly one command,
   which is complaints 4 and 5 as a fact about the data.
3. **The collision refusal.** Until the layout arrives, a second cell driven into
   an occupied directory is refused before a second of budget is spent, rather
   than destroying the first in silence.
4. **The extraction.** Five inlined command bodies become handlers; `main()`
   falls from 1,123 lines to about sixty. This is the release complaint 6 is
   actually about.
5. **The history key** — `scores.json` keyed by cell, one history row per
   `(agent, cell, run_dir)`, and `_latest_per_round` widened in the same commit.
   Without it the layout pools two configurations into one row or discards one.
6. **The layout** — blocked on the open question above.
7. **`--suite` and a second suite.** The discriminating test is to write
   `suites/smoke/` FIRST and see what it breaks; whatever it forces is the only
   abstraction owed. A `Scorer` protocol with one implementation restates a seam
   the task files already carry in data.

Stages 1–4 are deliverable without the open question. 5 touches recorded data
and 6 depends on a decision, so both wait for the owner.
