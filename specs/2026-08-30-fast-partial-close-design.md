# A --fast build must leave a non-abandoned, partial-marked record

Date: 2026-08-30 · Status: revised after a two-reviewer red-team (trace-consumer
impact + adversarial design). Ready to implement. The release that implements it
will cite this file. Roadmap item R8 (GAP-050, **part 1 only** — part 2 splits
out, see below).

## What was found (verified in code)

`check_deliverable.py:642` guards the whole close block with
`if trace_id and not a.fast:`. Under `--fast` the build clock the scaffold
started is never stopped (65 orphaned phase clocks measured), and no close runs.
So a build that ends on a `--fast` round leaves its trace open forever, and
`ledger.py:199` reports it **abandoned** (`abandoned = [t for t in traces if not
t.get("closed_at")]`). The author's inner loop can produce a "tested" deck whose
record is indistinguishable from a genuinely abandoned build.

The `--fast` skip is **deliberate**, and a naive close breaks the loop:
- one trace spans N rounds (0.1.602); `trace.py close` ACCUMULATES `phase_seconds`
  (`trace.py:356`), and the author iterates with `--fast` then does one final
  non-`--fast` run that closes;
- `trace.py close` RE-RUNS the checkers — `_checker_json` →
  `checker_report.run_checker` re-runs `check_prose`/`check_design` to transcribe
  verdicts (verdicts are transcribed, never supplied). Closing every fast round
  re-runs both checkers every round, the exact cost `--fast` exists to avoid.

## The design — Option B: a `partial` MARK, not a partial close

The first draft finalized a `--fast` round with a partial *close* (write
`closed_at` + the cheap render shape). **The red-team killed that (Option A):**
overloading `closed_at` to mean "closed OR partially-closed" forces every one of
the ~6 `closed_at` readers to re-check `partial`, and writing shape on a fast
round leaks a non-delivered document's `visual_share_median` into `ledger_shape`
(`ledger.py:204`, the human-read threshold distribution), drifts the cost axis,
and mislabels the trace in the generated index. The correct, smaller design:

**Under `--fast`, mark the trace `partial` and stop the build clock — but do NOT
write `closed_at`, shape, or verdicts.** Concretely:
- Move the **build-clock stop** out of the `not a.fast` guard so a `--fast` round
  stops it (banking the build seconds, ending the orphaned clock).
- Set a new boolean field **`partial = True`** on the trace (a cheap flag write;
  the geometry cross-check — one `body_attr` read — stays, it is cheap).
- Do **not** call the full `close`: no `closed_at`, no shape sweep, no checker
  re-run. A fast round measured one geometry and reviewed no storyline; its
  record says so by carrying `partial` and nothing it did not earn.
- Change the abandoned filter to **`not t.get("closed_at") and not
  t.get("partial")`** (`ledger.py:199`). A partial trace is now "a known
  fast-loop record," neither abandoned nor a delivery.

`closed_at` keeps meaning exactly "a full delivery record exists." The final
non-`--fast` run closes as today (sets `closed_at`, transcribes verdicts,
accumulates the checks phase, and — since a full close is not partial — sets
`partial = False`). Re-close is sound (verified, Q3): `closed_at` overwrites, the
checks phase accumulates by design, and a second `phase stop build` on an
already-stopped clock exits non-zero and is caught as a `note` — the build
seconds are banked exactly once.

Why Option B is strictly better here: a partial trace carries **no shape, no
gates, no `content_pages`, no `closed_at`**, so it is invisible to every
aggregate without a single new filter — `agent_runs.board()` already drops it
(`if not gates`/`if not pages`), `ledger_shape` never sees a shape it did not
write, and the generated index counts `closed` only where `closed_at` is set. The
whole change is the flag plus one ledger line.

### The `partial` field
A nullable boolean in `trace_schema.FIELDS`, **RUN** partition (a property of the
run). Empty on all 96 existing traces, so it goes in `ADDED_LATER` — which is
doubly necessary: `cmd_open`'s `dict.fromkeys(FIELDS)` leaves it `None`, and
`validate` tolerates `None` only for `ADDED_LATER` fields, so without it every
open would fail validation. Adding to `FIELDS` REQUIRES updating the
DOCUMENT/PRODUCER/RUN partition sets — `check_trace_schema` asserts they are
disjoint and exhaust `FIELDS` (`tests/test_trace_field_partition.py` pins the
union), so `partial` goes in the RUN set or both guards redden.

*Naming note (LOW):* "partial" is already a verdict word on the agent-evals board
(`"partial: N of 3 earned"`). Different namespace (a trace field vs. a board
string), but the CHANGELOG/comments should be explicit which is meant.

### Reader parity — make the exclusion legible, not merely emergent
The cost board's safety currently rests on a partial having empty gates/pages.
That is emergent; make it legible: where a reader means "full delivery records
only," it should test `closed_at`/`partial` explicitly. Minimal in this release:
the abandoned-filter change (required), and the generated index gains a `partial`
column so a partial-open is distinguishable from a truly-abandoned open.

## What ships
- `scripts/lib/trace_schema.py`: `partial` field (RUN partition, `ADDED_LATER`),
  in `validate` and the partition sets.
- `scripts/ops/trace.py`: a cheap `partial` mark (a `close --partial` that sets
  `partial=True` and stops nothing else, or a small `mark-partial` subcommand —
  impl detail; it must NOT set `closed_at`, write shape, or re-run checkers). A
  full `close` sets `partial=False`.
- `scripts/ops/check_deliverable.py`: `--fast` stops the build clock and marks
  the trace partial instead of skipping the whole block.
- `scripts/ops/ledger.py`: abandoned = `not closed_at and not partial`; the
  partial count reported as its own line, not folded into delivered builds.
- `scripts/build/build_trace_dictionary.py` + regenerated `evals/traces/README.md`
  and `evals/traces/index.jsonl` (**CI-gated by `--check`** — adding a FIELD makes
  them stale; `release.py` regenerates them, but they are named here so a
  non-`release.py` path does not fail CI on the generator, the 0.1.415 lesson).
  Add `partial` to `INDEX_FIELDS`.
- tests: a `--fast` run leaves a partial-marked, non-abandoned, clock-stopped
  trace (deliberate-red: before the fix it is abandoned/orphaned); a full close
  sets `partial=False` and accumulates; the partial mark runs NO checker
  subprocess (the cost property); `ledger.py` counts a partial separately from
  abandoned and from delivered.
- `KNOWN_GAPS.md`: GAP-050 narrowed to part 1, then closed by this release; part
  2 closed by its own earlier release (below).
- `CHANGELOG.md`: the deliberate-red run and the FM-24 note for `partial`.

## Part 2 splits out and ships FIRST (its own release)
`test_the_top_efforts_are_expressible` (`tests/test_conformance_driver.py:782`)
calls `rc.main(["run", ...])`, which creates the results dir under the real
`~/Documents/LUMI-Style/_conformance/` before failing on the unknown agent — so
it depends on operator machine state and already broke on a dangling `latest`
symlink (`mkdir(exist_ok=True)` → `FileExistsError`). This shares **zero surface**
with the schema work and is urgent (it writes into the owner's real Documents).
Ship it first as a tiny standalone release: monkeypatch the conformance results
root to `tmp_path`. GAP-050 narrows to part 1 for this spec.

## Open questions — resolved by review
- **bool `partial`**, not a `state` enum: the layer already infers state from
  field presence (`closed_at`, `recipe_hash`); a bool composes, an enum forces
  rewriting ~6 readers and a 96-trace migration.
- **Option B** (mark, not close): keeps `closed_at` honest, needs one ledger
  line, and no per-consumer filters — chosen over Option A.
- **Re-close is sound**: overwrite `closed_at`, accumulate checks (intended),
  stop the build clock once. No double-count.
- **No downstream requires verdicts on a closed trace**: `validate` accepts empty
  `gates`/`graded`; the board's `if not gates: continue` is what keeps a partial
  OFF the cost board — skipping transcription is the protection, not a risk.

## What this does NOT do
- It does not build R5's per-record completeness gate; it ships the `partial`
  signal R5 (GAP-046) will consume to exempt fast-loop records from owing
  verdicts.

## Verification
- Deliberate red planted first: a `--fast` build leaves an abandoned/orphaned
  trace today; after the fix it leaves a partial-marked, clock-stopped,
  non-abandoned record. FM-24 for `partial` (the writers guard's three answers
  hold with it added to `ADDED_LATER`).
- The partial mark asserted to run NO checker subprocess (the cost property).
- preflight green; `claim_sweep` clean; one release, one commit (part 1);
  part 2 is its own earlier one-commit release.
