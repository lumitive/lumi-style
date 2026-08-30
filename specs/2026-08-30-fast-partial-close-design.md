# A --fast build must leave a closeable, partial-marked record

Date: 2026-08-30 · Status: design under owner review; not yet implemented.
The release that implements it will cite this file. Roadmap item R8 (GAP-050).

## What was found (verified in code)

Two coupled record-robustness holes the baseline audit found.

**Part 1 — `--fast` skips the entire trace close.** `check_deliverable.py:642`
guards the close block with `if trace_id and not a.fast:`. Under `--fast` the
build clock the scaffold started is never stopped (65 orphaned phase clocks
measured), `closed_at` is never written, and verdict/shape/tokens are never
recorded. A dangling `trace_id` (the document names a record that does not
exist) is waved through rather than closed. So the author's inner loop can end
on a `--fast` round and leave a "tested" deck whose trace is open forever —
`ledger.py:199` then reports it as **abandoned** (`abandoned = [t for t in
traces if not t.get("closed_at")]`).

**Part 2 — a test writes into the real `~/Documents`.**
`test_the_top_efforts_are_expressible` (`tests/test_conformance_driver.py:782`)
calls `rc.main(["run", ...])`, whose `run` creates the results directory under
the real `~/Documents/LUMI-Style/_conformance/` as a side effect before failing
on the unknown agent. On 2026-08-30 it broke against a dangling `latest`
symlink a hand-deleted results dir left behind (`mkdir(exist_ok=True)` raises
`FileExistsError` on a dangling symlink). The test depends on operator machine
state — the GAP-050-part-2 / GAP-050 fragility class.

## Why part 1 is NOT "just close it" — the multi-round tension

The `--fast` skip is **deliberate**, and a naive close breaks two things:

1. **One trace spans N rounds (0.1.602).** A build is many rounds and the trace
   spans all of them (`trace.py:352`: the checks phase ACCUMULATES across
   rounds). The author iterates with `--fast`, then does ONE final non-`--fast`
   run before delivery (the `--fast` banner says exactly this) which closes the
   trace. If a `--fast` round did a full close, a later round could still add to
   it (close overwrites `closed_at` and accumulates phases, verified) — so that
   part is survivable — but:
2. **`trace.py close` RE-RUNS the checkers.** `_checker_json` →
   `checker_report.run_checker(kind, deliverable)` re-runs `check_prose` and
   `check_design` on the deliverable to transcribe verdicts (verdicts are
   transcribed, never supplied). Doing that on every `--fast` round re-runs the
   checkers every round — which is exactly the cost `--fast` exists to avoid.

So the fix must make a `--fast` round leave a **closeable, non-abandoned,
honestly-partial** record *cheaply* — without the verdict transcription — and a
later full close must still complete it.

## The design — a `partial` trace state + a cheap partial close

### The `partial` field
Add a nullable boolean `partial` to `trace_schema.FIELDS`, in the **RUN**
partition (it is a property of the run, not the document or the producer).
`True` = this trace was finalized by a `--fast` round and carries only the
declared-stage reading, not a full delivery sweep. `False`/absent = a full
close. Because it is empty on all 96 existing traces, it goes in `ADDED_LATER`
(an honest late arrival — the field the 0.1.653 comment says can later move out
once reliably filled), so `check_trace_field_writers` does not redden it.
`validate` and the DOCUMENT/PRODUCER/RUN disjoint-and-exhaust check must include
it.

### `trace.py close --partial`
A `--partial` flag on `cmd_close` that:
- sets `rec["partial"] = True` (a full close sets it `False`);
- stops the build clock and writes `closed_at` and the phases it has — the
  cheap half of close;
- **skips the verdict transcription** (the `_checker_json` re-runs) and the
  shape sweep, because a `--fast` round measured one geometry, not the delivery
  set. A partial close records what the fast round cheaply holds and marks the
  rest honestly absent.
The geometry cross-check (trace must not contradict the document) is cheap
(one `body_attr` read) and stays.

### `check_deliverable.py` under `--fast`
Replace the `and not a.fast` skip with: on `--fast`, still stop the build clock
and call `trace.py close --partial` (passing the cheap shape readings it already
has from the render, no checker re-run). On a full (non-`--fast`) run, close as
today (full, `partial=False`). Either way the trace ends **closeable**: a
fast-only sequence leaves a partial-marked record `ledger.py` will not call
abandoned; a completed build's final full close overwrites `closed_at`, flips
`partial` to `False`, transcribes verdicts, and accumulates the phases.

### `ledger.py`
`abandoned` already keys on `not closed_at`, so a partial-closed trace is
correctly not abandoned with no change. Optionally, report partial traces as a
distinct line ("N partial — a fast-loop record, not a delivery") so a partial is
not silently counted as a full build; this is a reporting nicety, not required
for the fix.

### Relationship to R5 (GAP-046)
The future per-record completeness gate (R5) must EXEMPT `partial` traces from
owing verdicts/full-shape — a partial trace legitimately lacks them. `partial`
is the signal that gate keys on. R8 ships the state; R5 consumes it.

## Part 2 — point the effort test at a tmp results dir

`test_the_top_efforts_are_expressible` must monkeypatch the conformance results
root (the `RESULTS`/output-dir constant `run` writes under) to `tmp_path`, so it
never touches `~/Documents` and passes regardless of operator machine state.
The other `run`-invoking tests in the file already take `tmp_path`; this one was
missed. (The workaround applied on 2026-08-30 — deleting the dangling symlink —
is not a fix; the test must not read that path at all.)

## What ships
- `scripts/lib/trace_schema.py`: `partial` field (RUN partition, `ADDED_LATER`),
  in `validate` and the partition sets.
- `scripts/ops/trace.py`: `close --partial` (cheap close, no verdict transcription).
- `scripts/ops/check_deliverable.py`: `--fast` closes partial instead of skipping.
- `scripts/ops/ledger.py`: (optional) a partial-count line.
- `tests/test_conformance_driver.py`: the effort test uses a tmp results dir.
- tests: a `--fast` run leaves a closeable partial-marked trace (deliberate-red:
  before the fix it is abandoned/open); a full close flips `partial` to False and
  accumulates; `close --partial` does NOT re-run the checkers (assert no checker
  subprocess); the effort test is environment-independent.
- `KNOWN_GAPS.md`: GAP-050 → fixed (both parts), or narrowed if part 2 is split.
- `CHANGELOG.md`: the deliberate-red run and the FM-24 note for the new field.

## Open questions for review
1. **`partial` as bool vs. a `state` enum** (`open|partial|closed`). A bool is
   the smallest change and composes with `closed_at`; an enum is more explicit
   but touches more readers. Which does the trace layer want?
2. **Should a `--fast` round close on EVERY round, or only stop-clock + mark and
   leave `closed_at` for the final?** Closing every round is cheap (no checker
   re-run) and keeps the record always-closeable, but writes `closed_at` on a
   trace the author may keep iterating. Is a partial-closed-then-reopened trace
   the right model, or should `--fast` set `partial=True` + stop the clock while
   leaving `closed_at` null and have `ledger.py` treat partial-open as
   not-abandoned? (The first needs no ledger change; the second keeps `closed_at`
   meaning "delivered".)
3. **Does re-close correctly flip `partial` False and accumulate phases** without
   double-counting the build clock? Verify the stop-clock idempotence across a
   partial then full close.
4. Any reader that assumes `closed_at` implies a full delivery record (and would
   now see a partial)?

## Verification
- Deliberate red planted first: a `--fast` build leaves an abandoned/open trace
  today; after the fix it leaves a closeable `partial=True` record. FM-24 for the
  new field (the writers guard's three answers hold with `partial` added).
- `close --partial` asserted to run NO checker subprocess (the cost property).
- preflight green; `claim_sweep` clean; one release, one commit.
