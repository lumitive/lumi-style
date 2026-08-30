# A real build's cost: session is easy, build-slice is the hard part

Date: 2026-08-30 · Status: **Path B chosen by the owner** (build-scoped, precise).
Recut after a two-reviewer red-team (one empirical on this session's real
transcript). The mechanism below is reviewed and corrected (window is build-phase
cost mirroring the time axis; phase_windows in PRODUCER; dominant-model, no dead
share field); ready to implement. Roadmap item R7 (GAP-048).

## Path B mechanism — persist the phase intervals the clock already computes

The build-only window is buildable because the timestamps already exist at the
moment they are needed. `trace.py cmd_phase` on `stop` reads the phase's start
(`clocks[name]`, an ISO timestamp it wrote at `start`) and takes `now` — it holds
**both ends of the interval** and today keeps only their difference
(`phase_seconds[name] += seconds`). Path B persists the interval too:

1. **Schema — `phase_windows`.** A new field: `{phase: [[start_iso, stop_iso], …]}`,
   accumulated across rounds beside `phase_seconds`, in the **PRODUCER**
   partition (it is the same measurement as `phase_seconds` — its start/stop pairs
   ARE those durations; splitting the two spellings of one fact across partitions
   is the drift `trace_schema.py:255` exists to stop). `ADDED_LATER` (empty on the
   existing traces — re-verify the count at build). One list per phase because a
   build spans N rounds (0.1.602).
2. **`cmd_phase` stop** appends `[started_iso, now_iso]` to `phase_windows[name]`
   as it accumulates the seconds — both ends already in hand (`trace.py:309-311`),
   a genuine 2-line change. It rides the same trace-first write as
   `phase_seconds`, and is *more* crash-robust: a re-stop appends a superset
   interval, unioning is idempotent, and the reader's `message.id` dedup counts
   each call once — so GAP-043's double-count fear does not reach tokens.
3. **The window is the clocked build cost, labelled as such — NOT total
   authoring.** Only `build` is clocked in a real loop (`new_deck.py:616` is the
   sole `phase start`; `check_deliverable.py:648` stops it). `discussion` and
   `outline` are **deliberately never counted** — `operating-rules.md:192`:
   charging for the thinking the user was asked to do pushes every build back
   toward the template path, "the opposite of what the measurement is for." So the
   window is the union of the **build** intervals, and the token number this
   records is **build-phase cost**, excluding discussion/outline token spend by
   the *same rule* the cost board already applies on the time axis
   (`agent_runs.py:97` charges `build`+`checks` only; pinned by
   `tests/test_agent_runs.py:49`). Consistency across the two axes is what makes
   the number defensible — it is the repo's own definition of build cost, applied
   to tokens. Not the trace lifespan: turns outside the build intervals fall in no
   window and are excluded, bounding the cache-read that otherwise dominates.
4. **A consumer-side reader** (new; the existing mappers are dev-side, H1) reads
   the transcript once, keeps each assistant record whose top-level ISO
   `timestamp` falls in a build interval, and returns: the four usage fields
   summed (deduped by `message.id`, mapped to `_read_usage`'s names, **preserving
   `None` for an absent cache field** — `session_cost`'s `… or 0` must not turn
   absence into a `0` claim), the **dominant model** (from per-message
   `message.model` — NOT `_model_from_transcript`, which returns `None` on this
   format, C2) recorded as a string when its share of billable (output) tokens
   clears a threshold else `null`, and `effort` from the record's top-level field.
5. **check_deliverable full close** gathers the build window from the trace, runs
   the reader, passes `--usage`/`--model`/`--effort`. OR-8c: no session id / no
   file / no build window → record nothing and say so.

### The four integrity yardsticks, and how the design meets them
This is the point, per the owner: the number must **stand up and be checkable**.
1. **Reproducible.** `phase_windows` is recorded ON the trace, so anyone can
   re-run the reader over the same window + transcript and get the same number.
   The cost is evidence-backed, not asserted — and this is the backbone that also
   settles yardstick 4.
2. **Not collapsed.** The four token kinds (input / output / cache-read /
   cache-write) stay four fields, priced differently; output is the billable
   signal the board grades, cache-read is context. Never one lump.
3. **Scope stated.** It is **build-phase cost**, the repo's established boundary
   (time axis already excludes discussion/outline), labelled — not "total
   authoring" dressed as precise.
4. **Multi-model honest — settled by yardstick 1.** Record the dominant model or
   `null`; do NOT persist a token-share field (it has no reader — an unconsumed
   column is the FM-24 fake-coverage defect). The full per-model split is
   *re-derivable* from the recorded window, so recording the dominant is honest,
   auditable, and needs no dead field.

### Deliberate-red is load-bearing here
`ADDED_LATER` permanently withdraws `phase_windows` from the fill-rate guard (no
dead-waiver reverse check), so nothing automatic catches `cmd_phase stop`
regressing to never-append — the mechanism that PRODUCES the evidence. The
deliberate-red (conventions 11/15 + FM-24) must therefore prove: `cmd_phase stop`
appends an interval; `validate` rejects a malformed `phase_windows` (not a list of
`[iso, iso]` pairs, or a phase outside `PHASES`); the reader excludes
out-of-window turns and handles an absent window (old traces, un-clocked builds).
`phase_windows` gets its own validation and its own test, in the style of
`test_phase_seconds_*`.

## The premise held; my "already built" claims did not

The owner's correction to GAP-048 was right and is confirmed on real data: a real
build's token usage IS written to the session transcript, it IS the platform's
own numbers (verifiable, not self-reported), the session is identifiable
(`CLAUDE_CODE_SESSION_ID` → exactly one `~/.claude/projects/<id>.jsonl`), and
reading an 18 MB / 12,200-line live transcript costs **0.26 s** — a non-issue.
`session_cost.py`'s counter works, deduping 3,351 raw usage records to 1,926 real
API calls (a naive sum would inflate ~1.7×).

But the first draft said "reuse existing plumbing," and the red-team proved that
false in three load-bearing places:

- **The time window does not exist.** `session_cost.py`'s `--since`/`--until` are
  advertised in the docstring only; `main()` defines no such flags, `claude()`
  takes the two params but never references them, and no record's timestamp is
  ever read. The window the whole design turns on **must be built**, not reused.
- **The model reader returns `None` on this format.** `_model_from_transcript`
  reads the CLI's captured stdout stream (a `system`/`init` record with a
  top-level `model`); the session `.jsonl` is a different shape — the model lives
  in per-message `message.model`. Run on the real transcript, it returns `None`.
  And it is a **cross-boundary import** anyway (`check_deliverable` is consumer,
  `run_conformance` is dev — `shipped.json` forbids it). A new consumer-side
  reader is needed.
- **One session, three models.** This session's tokens span `claude-opus-5`,
  `claude-fable-5`, `claude-opus-4-8`. A single `--model` over a summed token
  count mislabels it — the cost board's premise is that a cell states what
  produced it.

## The real problem the red-team surfaced: session cost ≠ build cost

The counter reads a SESSION's cost cleanly. Carving out one BUILD's slice is the
hard part, and the naive "trace lifespan window" (`opened_at`→`closed_at`) is
**unsound, not merely imprecise**:

- A trace spans N rounds and can be open for a long time (0.1.602). Its lifespan
  sweeps in every session turn between open and close — other work, other
  projects in the same directory — with no bound on the over-count.
- The dominant number is **cache-read** (916M this session, vs 3.8K fresh input).
  Cache-read grows with session LENGTH, not with build work. A lifespan window
  attributes a session's context-growth to "this build." That is misleading, not
  conservative.

So "record the lifespan window and name the over-count as imprecision" is
rejected. The honest cut is one of two:

### Path A — session-scoped cost, labelled honestly (smaller)
Record what the session cost, as **session cost**, not build cost. Build only:
the `--since`/`--until` window (small), a consumer-side reader that maps the four
usage fields (preserving `None` for absent cache — `_read_usage`'s "None is the
answer, zero would be a claim"), and the wiring. Record the model(s) present, or
leave model null when several ran. The number is real and verifiable but coarse:
it answers "what did this delivery session cost," not "what did this one deck
cost." Honest, and useful for a rough per-delivery figure.

### Path B — build-scoped cost, precise (bigger)
Make a build-only window possible by **timestamping the build phases** — the
trace records phase *durations* today, not absolute start/stop times, so a
build-only window needs a new capture (a schema addition, like R8's `partial`).
Then the window is the build's turns only, cache-read is bounded to them, and the
model read over that window is usually one value. This is the number the cost
board actually wants, and it is a real design of its own weight: window +
phase-timestamp schema + consumer-side reader (usage AND per-message model, with
the multi-model case handled) + wiring, each with OR-8c degrade-loud behaviour.

## Corrections carried from review (either path)
- **Effort IS in the transcript** — top-level `effort: "high"` on every assistant
  record, and `trace close --effort` accepts it. The first draft's "effort stays
  null" was wrong; it can be recorded.
- **Preserve None** — `session_cost` sums with `... or 0`, always emitting an
  integer; the mapper must keep an absent cache field as `None`, not `0`, or it
  contradicts `_read_usage`'s doctrine.
- **The field rename already exists** as `session_cost.HERMES_FIELD` /
  `run_conformance._usage_from_transcript` — reuse, one home; but from a
  consumer-side location (H1).
- **Automatic on `CLAUDE_CODE_SESSION_ID`, degrade loudly when absent** (OR-8c),
  no flag — perf (0.26 s) and privacy (counts only) both clear it.
- **Platform scope:** Claude Code only realistically (Cursor exposes an
  end-of-session total, no window; a real build is not driven by Hermes's store).
  Others record null, honestly; GAP-048 stays partially open with the residual
  naming model/effort/non-Claude, not just "non-Claude."

## The owner decision this surfaces
The choice is Path A (session-scoped, coarse, now — small) or Path B
(build-scoped, precise — a real design with a schema change). My recommendation:
**Path B if real per-deck cost is the goal** (it is the number the board wants and
the reason GAP-048 was opened), accepting it is a proper design pass, not a quick
wiring; **Path A only if a rough per-delivery figure soon is worth more than
precision.** Neither is the "small reuse" the first draft imagined — the red-team
retired that.

## Verification (once a path is chosen)
- Deliberate red planted first: a build close records real, verifiable
  tokens+model (path-appropriate scope); no session id → records nothing and
  says so (OR-8c three-answers).
- The field mapping preserves `None`; the window (Path B) is asserted to exclude
  turns outside it.
- preflight green; one release, one commit.

## What this is NOT
- Not self-reported — the numbers are the transcript's own (holds).
- Not the "reuse existing plumbing" the first draft claimed (retired).
- Not a `--fast` concern — fast rounds mark partial and never close (R8, holds).
