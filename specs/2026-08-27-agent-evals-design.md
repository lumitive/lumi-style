# Separating the agent evaluation, and answering the weekly-dictionary question

Date: 2026-08-27 · Status: implemented across the releases whose CHANGELOG
entries cite this file.

**Written after the fact, and that is a defect this record should own.** The
seven releases it describes were built from a plan held in a session rather than
in the repository, and every one of their entries cited
`2026-08-26-board-refresh-design.md` — a spec written for a different piece of
work, which contains the word "stage" zero times. A pre-PR review found the
citation. `specs/` exists precisely so a design is not lost between sessions;
citing a neighbouring file because it was the nearest one is how a record
becomes decoration.

## What was asked

Three things, from the owner:

1. conformance history rows that carry **model and effort**;
2. a **best agent + model + effort recommendation**, so a user does not have to
   configure twice after installing an agent;
3. the multi-agent evaluation **split out** of the package's other evals and
   tools, run on a major upgrade or on demand.

She also proposed a **weekly-updated dictionary** of agents × models × efforts
and asked whether it is feasible.

## Why the dictionary is the wrong shape

Four findings, each verified before it was written down:

1. **`scripts/` is standard library only with no network imports** — a CLAUDE.md
   red line — and `.github/workflows/` holds no schedule. Nothing in this package
   can perform a weekly search. The search would be a human ritual the package
   could not hold or check.
2. **One of the four drivable CLIs can enumerate models read-only.**
   `cursor-agent --list-models` works and returned 23 ids on 2026-08-27.
   `claude` and `gemini` have no listing command; `hermes model`'s own help says
   it selects interactively. So "ask the CLI" covers a quarter of what is
   drivable and an twelfth of what is claimed.
3. **The decisive one: this package cannot set a model.** Every registered
   platform loads it as a skill or a pasted prompt — the agent is already
   running, with its model and effort already fixed, when it reads the entry
   file. There is no code path by which a dictionary entry changes a user's
   session.
4. `trace_schema` already decided `model` stays free text, because model names
   rot and an enum of them is a maintenance tax with no defect behind it.
   Reversing that needs a documented case under convention 2, and the dictionary
   has none. Recorded as FM-25 rather than left open.

**So the recommendation is derived from measurement.** Owner's three decisions:
measured rows only; README's *Install & use* is the delivery surface; the
analysis separates and `run_conformance.py` stays where it is.

## The design

**The analysis separates; the driver does not.** `run_conformance.py` carries
four couplings that are not about agent evaluation at all — a `check_repo` guard
imports it by name, `release.py` shells `restamp`, `ci.yml` shells `validate`,
`stamps.py` owns the board's stamp. Moving it spends the budget on a rename.
What actually mixed agent evaluation into a document tool was the model × effort
cost matrix inside `ledger.py`, and that is what moved.

**The cell is `agent × model × effort`.** An agent id is not a configuration:
0.1.614 measured two runs of one id on one task, pinned differently, producing
different outcomes.

**One bar, borrowed.** `conformance/agent-evals.json` declares axes and an
ordering and no numbers. The bar is `evals/gates.json`, applied by
`agent_runs.board()` as an admission ticket, because a cost board without a
quality line rewards writing thinner decks.

**The join is the trace id.** History says what a run EARNED; a trace says what
it COST. The first implementation joined them on `(agent, model, effort)` and
could never have matched a row — `scores.json` carries a display sentence and a
trace carries the raw pin. See below.

## The stages, as built

1. move the cost matrix to `scripts/lib/agent_runs.py`; declare the trace field
   partition — 0.1.616
2. `effort`, `model_asked` and the trace id reach `scores.json` — 0.1.617
3. history rows carry `config` and `traces`; `validate` grows row checks — 0.1.618
4. a `models` probe and eleven waivers; `detect --models` — 0.1.619
5. `agent_evals.py`, the Score Evals, the configurations board — 0.1.620
6. README's generated block and its generator — 0.1.621
7. `conformance/README.md`, GAP-041, FM-25, FM-26 — 0.1.622
8. what the pre-PR review found — 0.1.623
9. the first measured round — **not done**; it needs the local installs updated,
   which needs the releases published, which needs the owner's say-so. GAP-041
   holds it.

## What the pre-PR review found, and why it is in the record

Four readers over the seven commits. The shape of the findings recurs and is
worth more than the list:

- **A join written against imagined material.** Both sides spell one model
  differently and every test used a clean id — a shape the harness never writes.
  Convention 15, exactly: one `grep` at a real `driver.json` would have found it,
  and the planted red never visited the branch because the fixtures agreed with
  the code.
- **Two commits on one branch contradicting each other.** 0.1.617 recorded
  `(not pinned)` as a deliberate answer; 0.1.618 taught `validate` to reject
  anything outside the effort tuple. Nothing ran both, so the next unpinned round
  would have reddened CI on a row the harness itself wrote.
- **A test disarmed by a sweep.** A mechanical rename removed a redirect in one
  place without replacing it, and the test then asserted a file it had written
  itself.
- **A generated consumer table that re-derived its own answer** and dropped both
  caveats the tool had been built to say.
- **Prose asserting a mechanism that does not exist** — a trigger declared in a
  register that nothing computes, and a design record citing a spec about other
  work.
