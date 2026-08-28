# Where the agent evaluation ends and the document evaluation begins

This package measures two different things and, until 0.1.616–0.1.621, measured
them with one set of tools. The owner asked for them to be separated. This file
says where the line runs, so the next reader does not have to reconstruct it
from five commits.

## The two questions

**Is this DOCUMENT good?** Answered by the checkers, the gate register
(`evals/gates.json`), the thresholds (`evals/thresholds.json`) and
`scripts/ops/ledger.py`. A document's verdict may never depend on which model
wrote it — that is the sentence with teeth, and it is why the two questions have
to stay apart at all.

**Is this CONFIGURATION worth running?** Answered by
`conformance/agent-evals.json` (the axes), `scripts/ops/agent_evals.py` (the
tool) and `conformance/CONFIGURATIONS.md` (the board). A configuration is
`agent × model × effort`, never an agent id: measured at 0.1.614, two runs of
one id on one task, pinned differently, produced different outcomes.

## What moved, what did not, and why

| | where it lives | why |
|---|---|---|
| the cost matrix | `scripts/lib/agent_runs.py` | it was inside `ledger.py`, the DOCUMENT tool, only because the traces it reads were already open there |
| which records the store holds | `scripts/lib/trace_store.py` | neither a document question nor an agent one; both tools need the same filter, and a second copy is this repository's most-repaired defect |
| the axes and the ordering | `conformance/agent-evals.json` | a register, so the tool cannot quietly change what it scores on |
| **driving an agent** | `scripts/ops/run_conformance.py`, **unmoved** | four of its five couplings are to things that are not about agent evaluation at all — a `check_repo` guard imports it by name, `release.py` shells `restamp`, `ci.yml` shells `validate`, `stamps.py` owns the board's stamp. Moving it would have spent the budget on a rename |

The owner's decision, in her words: the analysis separates, the driver stays
where it is.

## The one bar, borrowed rather than invented

`conformance/agent-evals.json` declares the axes and **no numbers** — how many is whatever that file holds today, and 0.1.633 added the seventh. The bar a
run is held to is already the gate line in `evals/gates.json`, which
`agent_runs.board()` applies as an admission ticket: a run with a failing gate
is not on the cost board, and since 0.1.620 a run that recorded no gates at all
is not either, because a run nobody measured is the cheapest thin deck there is.

This matters more than it looks. **A cost board without a quality line rewards
writing less.** Tokens per page falls fastest for the agent that writes the
thinnest deck, which is the exact behaviour every other check in this package
exists to catch. The admission ticket is the whole defence, and the argument for
it travels in `board()`'s docstring so a future move cannot drop it.

Adding a second bar here would need a documented case under CLAUDE.md convention
2, and there is none.

## What crosses the line, and what does not

A trace is one flat record holding three populations — the document's, the
producer's, and the run's own — declared as a partition in
`scripts/lib/trace_schema.py` and held disjoint and exhaustive by
`check_trace_schema`. Three uses cross the line legitimately:

* **QUALIFY** — the board reads `gates`, a document field, to admit a run.
* **NORMALIZE** — the board divides by `content_pages`, a document field,
  because a rate needs a denominator.
* **REPORT** — `ledger.ledger_signals()` prints producer fields under its own
  heading; it neither groups nor grades.

What no reader may do is **GRADE** across the line: a document's verdict may not
depend on which model wrote it, and an agent's standing may not be read off one
document's quality. None of this is mechanical, and a tighter check would be
FM-01 pretending to judge intent. What IS mechanical is that every field has a
side.

## What this separation does not give the user

**It cannot set your model.** Nine of the twelve registered platforms load this
package as a skill file, Codex reads `AGENTS.md`, and the two `prompt`-tier
platforms have `prompts/lumi-style-core.md` pasted into a chat. On every route
the agent is already running, with its model and effort already fixed, when it
reads anything this package ships. There is no code path by which any register
here changes a session. README's generated block tells a person what to
configure once, and calling that automation would be a promise no code here can
keep.

**It cannot maintain a vocabulary it cannot read.** One of the twelve can
enumerate its models read-only (`run_conformance.py detect --ask-models` prints
which, and the registry's `models_waiver` says why each of the other eleven
cannot). For the other eleven, the model names on the board are a record of what
an operator happened to pin.

**n is structural.** Nothing repeats a run by design, so an ordering over n=1
cells cannot separate a flaky agent from a flaky checker. Every row prints its
`n` rather than smoothing it, and `suggest` says out loud when a one-run cell
beat a five-run one. A minimum-n bar would be the invented threshold convention
2 forbids.

**CI verifies the derivation, never the measurement.** `agent_evals.py board
--check` and `build_readme_configs.py --check` prove that the written files are
what the recorded data derives. Whether the data is right is what driving a
round answers — the same limit `run_conformance.py validate` has, said here in
the same words on purpose.
