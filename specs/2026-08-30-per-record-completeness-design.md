# A closed trace must carry what its source owes

Date: 2026-08-30 · Status: design under owner review; not yet implemented.
The release that implements it will cite this file. Roadmap item R5 (GAP-046).

## What was found (verified in the store and the code)

`check_trace_schema` validates a stored trace's TYPES and enums only; `null` and
empty-dict are legal by design (absent is not measured). So a trace that closed
but recorded no config/cost is fully valid and CI is green over it. "The record
exists" and "the record has the content its kind owes" have no machine check
between them. This is the per-RECORD axis, orthogonal to 0.1.650's
`check_trace_field_writers` (a declared field empty on EVERY trace).

**The defect is real and measured.** Of 71 closed non-partial traces:
- **source=conformance (59):** 15 carry **no `model`**, 13 no `effort` — yet
  14 of the 15 have real `input/output_tokens` and all 15 have `gates`. They are
  **orphan cost**: real spend the board cannot attribute to a configuration
  (`agent_evals.cells()` joins on model×effort, so a model-less row places
  nowhere). The 15 span all three agents (hermes 4, claude-code 5, cursor 6),
  and each agent reports `model` in its OTHER runs — so this is captured-nothing,
  not a platform that cannot report.
- **source=build (12):** 0 have `effort`, 0 have tokens, only 2 have
  `phase_seconds` — and that is CORRECT. A real build cannot inline model/effort
  or usage (GAP-048, verified structurally). A build's nulls are honest absence.

So the same null (`model`/`effort`/`tokens` absent) is a **defect on a
conformance trace and honest on a build** — which is exactly why a flat
"a closed trace must be full" check is wrong, and the policy has to be
source-keyed.

## The nuance that makes this a design, not a flat gate

`_conformance_trace` (`run_conformance.py:1626-1628`) adds `--model`/`--effort`
to the close **only** when the driver's record carries them and they do not start
with `"("` — a `"(...)"` placeholder ("no model reported") is deliberately NOT
recorded, because a fake model name is worse than a null. So a conformance trace
legitimately lacks `model` when the run was driven WITHOUT a pin
(`run --drive`, all detected agents) AND the agent did not self-report. A
`--cell agent@effort` pin, by contrast, KNOWS the effort (and usually the model)
before the run starts.

So "conformance owes model/effort" is true for a **pinned** run and not
guaranteed for an **unpinned** one. The trace does not currently record whether
it was pinned. That gap in the trace is the first thing the design must settle.

## The design — three questions this spec puts to review, with a recommendation

### (A) What is owed, by source
- **conformance, pinned:** owes `model` AND `effort` (the pin knew them; a
  measurement that drops them is orphan cost).
- **conformance, unpinned (`--drive`):** owes what the platform reports; a null
  is honest when the agent did not self-report. This case needs a signal in the
  trace (see B).
- **build:** owes nothing beyond gates/pages (GAP-048). Its model/effort/token
  nulls are honest absence.
- **partial (R8):** exempt entirely — a fast-loop record owes nothing.
- **fixture:** exempt (synthetic).

### (B) Where the gate lives — RECOMMEND: enforce at close, not (only) a store scan
The repo's pattern is to enforce at the ACTION (release.py, check_evidence
execute-don't-trust), not a later scan. Recommend: **`_conformance_trace` records
whether the run was pinned**, and **`cmd_close` refuses to close a pinned
conformance trace without model+effort** — the forcing function that stops NEW
orphan-cost traces at the source. A store-scan guard (`check_repo`) is the
weaker complement: it can only flag what already exists, and the 15 existing
traces have lost provenance (the drive-time model/effort are gone and cannot be
recovered).
- **Open question:** is close-time enforcement enough, or does GAP-046's framing
  ("a per-record store guard complementing check_trace_field_writers") require a
  `check_repo` scan too? A scan reddens the 15 existing traces unless they are
  grandfathered.

### (C) The 15 existing orphan-cost traces — RECOMMEND: grandfather by version
They cannot be fixed (provenance lost) and should not be deleted (they carry real
gate/cost data the board already excludes them from via the model×effort join).
Recommend the gate bind only traces **opened at/after the rule's version**
(`skill_version` is recorded at open), so the 15 stay as historical records and
new incompleteness is caught. This mirrors `evals/gates.json`'s `since` and the
`ADDED_LATER` philosophy: a rule written after a record was made does not
retroactively redden it.
- **Open question:** grandfather-by-version, or a small explicit waiver list of
  the 15 ids with a reason? Version-binding scales; a waiver list is auditable
  but grows.

## What this is NOT
- It does not require a build to record model/effort/tokens — that is GAP-048,
  and those fields are structurally not inlinable for a real build.
- It does not touch `partial` traces (R8) — they are exempt.
- It does not invent a cost for a run that did not report one; it requires that a
  run which KNEW its config (a pin) records it.

## What likely ships (pending the review's answers to A/B/C)
- `scripts/lib/trace_schema.py`: possibly a `pinned` (or `driven_by`) signal so a
  trace records whether its config was pinned — the field (B) turns on. RUN
  partition, `ADDED_LATER`.
- `scripts/ops/run_conformance.py`: `_conformance_trace` records the pin.
- `scripts/ops/trace.py`: `cmd_close` refuses to close a pinned conformance trace
  without model+effort.
- possibly `scripts/check/check_repo.py`: a per-record completeness guard over
  the store, version-bound, exempting partial/build/fixture and the honest-null
  cases.
- `KNOWN_GAPS.md`: GAP-046 → fixed (or narrowed if the store-scan half defers).
- tests + a deliberate-red: a pinned conformance close with no model fails; a
  build close with the same nulls passes; a partial is exempt; FM-24 three
  answers if a store guard ships.

## Open questions for review (the load-bearing ones)
1. **A — the policy:** is "pinned conformance owes model+effort, everything else
   is source-honest" the right cut? Is there a case where an unpinned `--drive`
   run SHOULD still be required to record model (e.g. the platform always reports
   it, so a null is always a capture bug)?
2. **B — enforce point:** close-time refusal (recommended), store-scan guard, or
   both? Does a close-time-only fix satisfy GAP-046's "per-record" framing?
3. **C — the 15 existing:** grandfather by opened-version, or waive by id?
4. Does adding a `pinned` signal to the trace touch the DOCUMENT/PRODUCER/RUN
   partition, the fill-rate guard, or any consumer, the way `partial` did (R8)?
5. Is there a simpler design that needs NO new field — e.g. keying the gate on
   whether `effort` is present (a pin always sets effort) without recording
   pinned-ness explicitly?

## Verification (once the design settles)
- Deliberate red planted first: a pinned conformance trace closing without
  model/effort fails; a build with the same nulls passes; a partial is exempt.
- If a store guard ships: FM-24 three answers (complete / incomplete-finding /
  can't-look), and it must not redden the grandfathered 15.
- preflight green; `claim_sweep` clean; one release, one commit.
