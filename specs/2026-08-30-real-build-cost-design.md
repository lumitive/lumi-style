# A real build's cost: session is easy, build-slice is the hard part

Date: 2026-08-30 · Status: **Path B chosen by the owner** (build-scoped, precise).
Recut after a two-reviewer red-team (one empirical on this session's real
transcript). The mechanism is below; a focused review of it comes before
implementation. Roadmap item R7 (GAP-048).

## Path B mechanism — persist the phase intervals the clock already computes

The build-only window is buildable because the timestamps already exist at the
moment they are needed. `trace.py cmd_phase` on `stop` reads the phase's start
(`clocks[name]`, an ISO timestamp it wrote at `start`) and takes `now` — it holds
**both ends of the interval** and today keeps only their difference
(`phase_seconds[name] += seconds`). Path B persists the interval too:

1. **Schema — `phase_windows`.** A new field: `{phase: [[start_iso, stop_iso], …]}`,
   accumulated across rounds beside `phase_seconds`. RUN partition, `ADDED_LATER`
   (empty on the 96 existing traces). One list per phase because a build spans N
   rounds (0.1.602), so each round contributes an interval.
2. **`cmd_phase` stop** appends `[started_iso, now_iso]` to `phase_windows[name]`
   as it accumulates the seconds — the interval it already has in hand.
3. **The authoring window** is the union of the intervals for the token-spending
   phases — `discussion`, `outline`, `build` — and NOT `checks` (checks is the
   tooling's own run, no model tokens). A build-only window, not the trace
   lifespan: the turns between authoring phases (email, other work) fall in no
   interval and are excluded. This is what makes the number build cost, not
   session cost, and bounds the cache-read that otherwise dominates.
4. **A consumer-side reader** (new; the existing readers are dev-side, H1) reads
   the session transcript once, keeps each assistant record whose top-level ISO
   `timestamp` falls in any authoring interval, and returns: the four usage
   fields summed (deduped by `message.id`, mapped to `_read_usage`'s names,
   **preserving `None` for an absent cache field**), and the model(s) seen —
   from per-message `message.model`, not the CLI-stream reader that returns
   `None` here (C2). Effort comes from the record's top-level `effort`.
5. **check_deliverable full close** gathers the authoring window from the trace,
   runs the reader, and passes `--usage`, `--model`, `--effort`. OR-8c: no
   session id / no file / no authoring intervals → record nothing and say so.

### The two sub-decisions the mechanism review must settle
- **Are the authoring phases actually clocked in a real build?** If only `build`
  is clocked (the scaffold starts it, check_deliverable stops it) and
  `discussion`/`outline` are not, the window is build-phase-only and misses the
  earlier authoring turns. The review must check what a real loop clocks; the
  window is only as complete as the phases that are timed.
- **Multi-model within the authoring window.** Even build turns can span models
  (a compaction runs `fable`). The reader must decide: record the token-dominant
  model, split per model, or null when no model holds a clear majority. The cost
  board keys on one `(model, effort)`, so a rule is needed — recommend
  dominant-model with the token share recorded, null below a threshold.

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
