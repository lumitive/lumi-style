# GAP-046 recut: the defect is dropped attribution, not missing completeness

Date: 2026-08-30 · Status: recut after a two-reviewer red-team that killed the
completeness-gate design. Ready to implement as a much smaller change. The
release that implements it will cite this file. Roadmap item R5 (GAP-046).

## What the review established (verified in store + code)

The first draft proposed a per-record completeness GATE: a closed conformance
trace owes model+effort, enforced at close or scanned in the store. **Two
independent red-teams killed it**, and the store data agrees:

- **A completeness gate reddens legitimate nulls.** A conformance trace lacks
  `model` for good reasons, not only bad ones. An **effort-only pin**
  (`--cell claude-code@high`) leaves the model to the CLI default, and
  `run_conformance.py:940` records `"(the CLI's default)"` which the close at
  `:1625` deliberately drops to null — the code choosing null over a fake model
  name, on purpose. 4 of the model-less traces are exactly this (effort=`high`,
  model null). A **model-only pin** (`--cell cursor-grok-4.6-high`) leaves
  effort null (2 traces). An unpinned Hermes/Gemini run reports no model at all
  (`run_conformance.py:1390`). Requiring both axes false-fails all of these.
- **The gate would exempt the actual defect.** The real orphan cost is the
  ~11 fully-unpinned claude-code/cursor runs — and a "pinned owes model" policy
  exempts unpinned runs, so it catches essentially none of them.
- **Close-time refusal is destructive.** If `cmd_close` refuses, `_conformance_trace`
  returns on the nonzero exit (`run_conformance.py:1629`) and leaves the trace
  OPEN → `ledger.py:459` counts it an **abandoned build**, conflating
  "couldn't attribute" with "drive didn't finish." Worse, `cmd_close` is where
  the checkers run and usage is read, so a refused close **discards the gates and
  tokens** — it destroys the cost record the fix exists to preserve.
- **A `pinned` field is unreliable and unnecessary.** `effort present ⟺ pinned`
  fails both ways (model-only pins have effort null; effort-only pins have model
  null), and `model`/`effort` are PRODUCER fields, not RUN — the first draft even
  mis-placed the field. The question a `pinned` field would answer is already
  answered by `model_ran`.
- **Correction to the first draft's rationale:** builds are NOT structurally
  unable to record `model` — 7 of 12 build traces carry one (`claude-opus-5`
  etc.). A build is exempt because it OWES nothing (GAP-048 is about
  usage/tokens, which a build genuinely cannot inline), not because model is
  unobtainable. The symmetry argument was built on a false structural claim.

**So GAP-046 as framed — "add a per-record completeness gate" — is the wrong
tool.** "Closed with empty content" resolves, on inspection, to legitimate
unpinned / single-axis / no-effort-CLI records. There is no completeness gate
that separates the honest nulls from the defective ones, because the trace does
not carry the pin, and adding the pin does not help (an unpinned run has no pin
to record).

## The real defect, and the one change that fixes it

The measured symptom — orphan cost — has a specific mechanism: the driver
computes `model_ran` (the model the CLI's own transcript says it used,
`run_conformance.py:952`), and the board already PREFERS it (`_model_cell`,
`run_conformance.py:1376`), but **`_conformance_trace` throws it away at close**
— it passes `record["model"]` (the pin) and never `record["model_ran"]`. So an
unpinned claude-code/cursor run that DID report which model ran closes with
`model=null` and pools into a junk `(agent, None, None)` cost cell
(`agent_evals.py:350`).

**The fix is one change: thread `model_ran` into the trace at close.** At
`run_conformance.py:1625-1628`, prefer the pinned model, fall back to
`model_ran` when the pin is absent:

```
chosen = record["model"] if (record.get("model") and not str(record["model"]).startswith("("))
         else record.get("model_ran")
if chosen and not str(chosen).startswith("("):
    argv += ["--model", chosen]
```

This attributes every unpinned run whose platform reports a model (claude-code,
cursor), directly shrinking the orphan-cost population the spec measured. It
leaves Hermes/Gemini as honest nulls (they report no model — the spec's own
intent). It needs **no new field, no policy cut, no close refusal, no schema
change** — `model` already exists and already types `str|None`.

## The historical traces — grandfather, do not touch
The 35 model-less conformance traces (20 legacy `agent=None`) span 0.1.539–0.1.623.
They predate the traces↔scores join (0.1.618, `agent_evals.py:145`) and are
referenced by none of the 53 `scores.json` files, so they were never
board-attributable regardless. Their drive-time `model_ran` is gone (driver.json
survives for 0 of 15). Leave them: `model_ran`-at-close binds new runs only, the
way a data-capture fix naturally does.

## What ships
- `scripts/ops/run_conformance.py`: `_conformance_trace` prefers the pin, falls
  back to `model_ran`, at close.
- tests: a driven record with no pin but a `model_ran` closes its trace WITH that
  model (deliberate-red: before the change it closes model-null and pools into
  the junk cell); a pinned record still records the pin; a Hermes/Gemini record
  with neither stays honest-null.
- `KNOWN_GAPS.md`: GAP-046 recharacterized and closed — the "completeness gate"
  is declined (with the reason: it reddens legitimate nulls), and the real
  attribution defect is fixed by `model_ran`-at-close. FAILURE_MODES' *Abandoned
  gates* records the declined completeness gate so it is a decision, not a
  re-debate.
- optional (NOT a gate): a REPORTS-never-fails line in `ledger.py` surfacing
  null-model conformance cost cells to the operator, since honest-null is
  pin-dependent and a gate cannot decide it.

## What this is NOT
- Not a completeness gate (declined — it cannot separate honest nulls from
  defects).
- Not a `pinned` field (unreliable and unnecessary).
- Not a close-time refusal (it abandons the trace and discards its cost).
- Not a change to builds (they owe nothing; GAP-048 stands for usage/tokens).

## Owner decision this surfaces
GAP-046 as written asked for a completeness gate; the investigation shows that is
the wrong tool and the genuine defect is narrower (dropped `model_ran`). Two
honest options: (1) implement the `model_ran`-at-close capture (recommended — it
fixes the measured orphan cost, small and safe), or (2) recharacterize GAP-046 as
"largely a non-defect; the completeness gate is declined" and stop there. This
is a change of target from what the roadmap listed, so it is put to the owner.

## Verification (if implemented)
- Deliberate red planted first: an unpinned claude-code record with a
  `model_ran` closes model-null before the change and model-attributed after.
- A pinned run still records the pin; a no-model platform stays null.
- preflight green; `claim_sweep` clean; one release, one commit.
