# A guard for two declared-but-never-recorded trace fields

*(One slice of the declaration–record gap the baseline found, not the whole of
it — see "What this does not do." The four sibling instances get ledger ids and
stay open.)*

Date: 2026-08-30 · Status: IMPLEMENTED at 0.1.650 (`check_trace_field_writers`
+ `WRITER_WAIVERS`, which cite this file); 0.1.651 registered the sibling
instances as ledger ids. This file stays as the design record.

## What was asked

A four-dimension baseline audit (trace reliability, Evals–trace consistency,
external dependencies, delivery-pipeline attack surface) found one recurring
disease: the **declaration layer and the record layer are systematically
disconnected**. Evals declare what data they consume — bars, sort keys, the
constitutional-yield record — and the trace layer largely does not record it,
while **no check holds "what was declared is actually written."** The guards
hold schema legality only.

`principle_yields` and `refused_to_emit` are the sharpest instance: 0-of-96
after 187 releases. They have a validator (`trace_schema.validate`) and a writer
subcommand (`trace.py yield` / `refuse`), but no pipeline ever constructs the
argv that calls those subcommands, so the columns are empty on every trace while
looking like coverage. This is FM-24's exact shape, one field over from the
guard that already exists for the read side (`check_trace_field_readers`).

The owner ruled two things:
1. On whether to fix by **wiring** the empty fields or **deleting** them:
   "make the most correct choice." Investigation (below) showed **neither** is
   right, and named a third path.
2. Add a **declaration–existence parity guard** so "declared but never recorded"
   cannot recur silently.
3. Guard severity: **allow a reasoned deferral** — a field may stand without a
   writer only with a registered reason naming what would activate it; no
   reason, no writer → red. The ADDED_LATER philosophy applied to writers.

## Why neither wiring nor deleting is correct (both verified)

**Cannot force-wire.** A real build's `build.py` has no `--model`/`--effort`;
recording them would mean a session agent self-reporting values that cannot be
machine-verified (violating "a verdict is transcribed, never typed"). Token
usage is not obtainable inline — it lives only in the whole-session transcript,
unfinished when the build closes, and is a different source from conformance's
single `--usage` dump. Wiring these would inject unverifiable or unavailable
values. (Verified: `build.py` argparse has only `--platform`;
`check_deliverable.py` close passes only the three shape readings;
`session_cost.py` reads usage post-hoc at session scope.)

**Cannot force-delete.** The four dead `shape` keys
(`visual_share_median` and three others) are not dead — they are **dormant**,
deliberately kept as "reported, not gating." `evals/thresholds.json:226` records
that these bars were **refused as gates in writing** (a red-team pass cleared
all four with two mechanical rewrites adding no fact), and that "the agreement
study — these numbers against the owner's H1–H6 scores — is what would earn
[promotion], and it has not been run." Deleting them removes the data interface
of a deferred study. `principle_yields`/`refused_to_emit` are red line 9's only
data-layer home; deleting them removes the ability to count a constitutional
yield at all.

## The third path: make the gap visible and held, without touching data

Do not change data (no wiring, no deletion). Add a guard that makes "declared
but not recorded" **itself** visible and enforceable — and a registry that turns
each such hole from invisible into a tracked debt with a named trigger. This is
how the repository already handles a known gap: not pretend it is absent, make
it an entry with an id.

## The guard: `check_trace_field_writers`

The mirror of `check_trace_field_readers` (check_repo.py:5004), one field over.
That guard catches a field nobody READS; this catches a field nobody WRITES.

### The criterion — a red-team review killed the first method; this is the second

**A first design used static analysis** of `scripts/ops/trace.py` — which
subcommand writes which field, and whether that subcommand's name appears as an
argv literal in a pipeline entry point. A three-way review destroyed it, and the
verdict is recorded here so the replacement is a decision, not another guess:

- The static criterion measured **"the subcommand name is mentioned in a
  pipeline file,"** not **"the pipeline actually records the field."** It flagged
  `principle_yields`/`refused_to_emit` (their writers `yield`/`refuse` appear in
  no pipeline file) but **passed `corpus_id`, `review_ref`, `outline_reviewed`,
  `titles_changed_after_approval`** — which have the *same* structural disease
  (a writer subcommand exists, no pipeline passes the flag that fills them) and
  are just as sparse (2–4/96). They escaped only because their writer subcommand
  (`annotate`/`close`) rides into the pipeline for an *unrelated* flag
  (`build.py` passes `annotate --recipe`). "Flags exactly two" was
  **under-catching by accident, not precision** (verified: no pipeline file
  passes `--corpus-id`, `--review-ref`, `--outline-reviewed`, or
  `--titles-changed`).
- The static match was **defeatable by a comment**: a single
  `# principle_yields …` line, or `if False: rec["principle_yields"]=[]`, in a
  pipeline-reachable subcommand body flips the substring test to "has writer."
- It was **already out of step with the code**: `cmd_open` is
  `dict.fromkeys(FIELDS)` then `rec.update(...)`, so ten fields are set to `None`
  by `fromkeys` and never named in the `update` a placeholder-scan reads.

The root cause the review named: a static scan of subcommand bodies cannot
answer a data-flow question ("is an argument actually passed by a pipeline"),
and eight iterations only tuned a heuristic that measures the wrong thing.

**The replacement measures the disease directly: fill rate.** A field is red iff
it is **empty on every stored trace** (`evals/traces/`) AND is not in
`ADDED_LATER` AND has no `WRITER_WAIVERS` entry. This tests what the guard exists
to catch — a declared field that records nothing — rather than a proxy for it,
and it is immune to every fragility above (comments, `fromkeys`, helper depth,
one-flag-many-fields), because it reads the data, not the code that writes it.

The one objection the review raised against fill rate — "a new field with no
data yet is falsely flagged" — is exactly what `ADDED_LATER` already answers: a
newly added field is declared there as an honest absence, and the guard skips
it. Zero is the only non-arbitrary threshold (convention 6: a floor of zero is a
line the data either crosses or does not; any positive threshold would be an
invented bar).

Verified against the 96 stored traces: **empty-on-every-trace, not in
ADDED_LATER, is exactly `principle_yields` and `refused_to_emit`.**
`cache_write_tokens` is also 0/96 but sits in `ADDED_LATER` (skipped);
`corpus_id`(3), `outline_reviewed`(4), `review_ref`(2),
`titles_changed_after_approval`(2), `recipe_version`(5) are sparse but non-zero
— they have real, if thin, records, which is a different state from structural
death and one this guard deliberately does not touch (see the honesty note in
"What this does not do").

### Severity (owner-ruled: reasoned deferral)

An empty-on-every-trace field not in `ADDED_LATER` is red **unless**
`trace_schema.WRITER_WAIVERS` carries a reason for it. The waiver names what
would activate a writer. No waiver → red. Two waivers ship: `principle_yields`
and `refused_to_emit`, each citing red line 9 and the `--assess` /
machine-refusal hook that would wire them.

**And the reverse is held too — a dead waiver fails (convention 19).** A
`WRITER_WAIVERS` entry naming a field that is NOT currently flagged — because a
writer was wired, or the field was removed from `FIELDS` — is itself red. Without
this, a stale waiver sits as approved coverage over a hole that no longer exists,
which is the same "looks like coverage" defect the guard is built against. This
mirrors `check_one_home`'s dead-waiver check (a waiver nothing needed fails).

### FM-24 (three answers, not two)

The guard fails rather than passing vacuously when: `trace_schema.FIELDS` is
absent, `WRITER_WAIVERS` is not a dict, or **the trace store visited no file** —
a fill-rate guard that reads zero traces would find every field empty and, worse
if inverted, would report clean while measuring nothing. The store being empty
is a legal state elsewhere (an installed skill has no `evals/traces/`), so the
guard distinguishes "scanned N traces, these were empty" from "scanned nothing":
the second is a finding, the first is the measurement.

## Registry: `trace_schema.WRITER_WAIVERS`

A dict beside `FIELDS` and `ADDED_LATER` in `scripts/lib/trace_schema.py` — the
authoritative home for field facts, so the guard reads the waiver list from
there and holds no second copy (the `one home` rule; the guard only reconciles).
Shape: `{field_name: reason}`, reason naming the activation trigger.

## What ships

- `scripts/lib/trace_schema.py`: add `WRITER_WAIVERS` with the two entries.
- `scripts/check/check_repo.py`: add `check_trace_field_writers` next to
  `check_trace_field_readers` (:5004); register in `CHECKS` right after
  `("trace field readers", …)`.
- `tests/test_check_repo_guards*.py`: synthetic-tree tests — a passing tree, and
  at least one failing fixture per mode (a declared field empty on all fixture
  traces and not waived → names the field; a waiver naming a still-filled or
  non-existent field → dead-waiver red; waiver registry not a dict; empty trace
  store → "scanned nothing" finding, not a vacuous pass).
- CHANGELOG entry with the deliberate-red run recorded (convention 11): remove
  the `principle_yields` waiver, watch it go red naming the field, restore.

Deliberately NOT in this release: wiring any writer, deleting any field,
touching the shape keys or reader_score. Each of those deferred decisions gets a
ledger id before the release so the CHANGELOG can cite it (convention 10) — the
baseline audit is not a ledger, and leaving them as prose would turn "the gap is
still open" back into something the next session cannot see. The declaration–
record gap itself, and the four sibling instances the guard does not cover (see
below), are registered as KNOWN_GAPS/IDEA entries; this release uses on those
four the same philosophy it uses on the two it flags — a tracked debt, not a
silence.

## What this does not do (scope honesty)

The baseline found the declaration–record disconnect in five instances. This
guard makes exactly ONE of them enforceable, and even there it records nothing —
it makes "empty" a *declared* state, not a filled one. Stated plainly so no
reader, and no CHANGELOG line, mistakes a slice for the whole:

- **(a) `principle_yields`/`refused_to_emit` 0/96** — covered: the guard flags
  them, the waivers declare them as debt with a trigger. They stay 0/96; the
  guard makes the emptiness visible and held, not filled. This is "the
  unreliable place now has a record," not "the trace is now reliable."
- **(b) shape dead sub-keys** (`visual_share_median` etc.) — NOT covered: they
  are sub-keys of the `shape` field, which the guard sees as written. → its own
  ledger id.
- **(c) reader_score dead axis / corpus_id sparse** — NOT covered: these are
  Evals-side declarations, not `FIELDS` entries; the guard never reconciles "what
  an Eval declares it consumes" against "what a trace records." → its own id.
- **(d) real builds record no model/effort/usage** — NOT covered, and this is a
  structural blind spot: those fields ARE written by the conformance pipeline, so
  a fill-rate or writer check both pass them; the disease is that ONE path
  (`build.py`) leaves them null, which neither a per-field guard sees. → its own
  id.
- **(e) no integrity guard; an empty closed trace is CI-green** — NOT covered:
  this guard is a static repo check over the schema and stored fill rates, not a
  per-record completeness check. → its own id.

The honest one-line summary for the CHANGELOG: *makes one declared-but-unrecorded
field pair enforceable; the four sibling gaps get ledger ids and stay open.*

## Verification

- New guard planted red FIRST (waiver removed → red → restored → green), and the
  unmeasurable branches asserted literally (each prints something a clean tree
  does not).
- Synthetic-tree tests with a failing fixture per mode.
- `python3 scripts/preflight.py` green; `claim_sweep.py` no new dangling.
- One release, one commit, `X.Y.Z — summary` subject matching the CHANGELOG head.

## What the adversarial review found (three reviewers, 2026-08-30)

Ran before any code, on this spec. Every finding was verified against the code
before it changed the design; the criterion review's central finding forced the
method change above, and it was right.

- **Criterion review — killed the static method.** It proved the static criterion
  measured "subcommand mentioned in a pipeline file," not "pipeline records the
  field," and therefore under-caught: `corpus_id`/`review_ref`/`outline_reviewed`
  have the same structural disease and were passed. Verified (no pipeline passes
  their flags). It also showed the substring match was comment-defeatable and
  already out of step with `cmd_open`'s `fromkeys`. → criterion replaced with
  fill-rate, which measures the disease directly and is immune to all three.
  (One half-correct point, kept honest: the review called `corpus_id` the *same*
  disease as `principle_yields`; fill rate shows it is *sparse-but-alive* (3/96)
  vs *structurally dead* (0/96) — a real distinction the new criterion draws and
  the old one could not.)
- **Convention review — three gaps, all folded in.** Missing dead-waiver check
  (convention 19) → added. Deferrals with no ledger id (convention 10) → each
  sibling instance now gets a KNOWN_GAPS/IDEA id before the release. A path bug
  in the old criterion (`check_deliverable.py` is under `scripts/ops/`) →
  dissolved by the method change, since fill rate reads traces, not pipeline
  source. Convention 14 (no unverified claim): strongly compliant — every number
  spot-checked and confirmed.
- **Scope-honesty review — forced the honesty section and the narrowed title.**
  It confirmed the guard covers only (a) and leaves (b)–(e) structurally
  untouched, and warned that the guard turns an *embarrassing* 0/96 into an
  *approved* 0/96, removing the pressure to wire a real writer. → the title, the
  "What this does not do" section, and the one-line CHANGELOG summary all exist
  because of this review.

The remaining obligation: the release's CHANGELOG must carry the one-line honesty
summary and cite the sibling ledger ids, or it recreates the over-claim this
whole review chain existed to prevent.
