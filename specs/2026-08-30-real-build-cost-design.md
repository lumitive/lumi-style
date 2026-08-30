# A real build records its own cost, read from its session

Date: 2026-08-30 · Status: design under owner review; not yet implemented.
The release that implements it will cite this file. Roadmap item R7 (GAP-048).

## The premise correction that started this

GAP-048 was recorded as "accept-and-track: a real build's cost is structurally
unobtainable inline." **That was wrong, and the owner caught it.** Every turn of
a real build writes its token usage to the session transcript; the cost is
readable during the build, and the build's own slice of it is complete the moment
the build closes. What is not final until the session ends is the *whole
session's* total — but that is not what a build trace needs. So the gap is not
"cannot measure"; it is "the tool never reads what is already written."

## What is already built (verified)

- **The counter exists and is correct.** `scripts/ops/session_cost.py` reads a
  Claude Code transcript and sums `input_tokens`, `output_tokens`,
  `cache_read_input_tokens`, `cache_creation_input_tokens`, **deduping by
  `message.id`** (the trap that inflated one build's tokens 2.5–3.6×) and
  bounding by `--since`/`--until`.
- **The build can identify its own session.** `CLAUDE_CODE_SESSION_ID` is in the
  environment of a build running under Claude Code; the transcript is the file
  named `<id>.jsonl` under `~/.claude/projects/` (verified: it exists for the
  current session). No guessing "the latest file" — the id is exact.
- **The close already accepts a usage dump.** `trace.py close --usage <file>`
  reads `input_tokens`/`output_tokens` (required) and `cache_read_tokens`/
  `cache_write_tokens` (optional) and records them. The `--usage` path is how
  conformance already fills these; a real build just never uses it.
- **The numbers are the platform's own, not self-reported.** They come from the
  transcript's API usage records, so recording them satisfies "a measurement is
  transcribed, never typed" — the exact rule that made "a session agent would
  have to self-report, which is unverifiable" a real objection for model/effort
  but NOT for the usage the API itself wrote down.

## The design — read the build's session slice at close, hand it to `--usage`

In `check_deliverable.py`'s **full-close path** (the non-`--fast` branch; a
`--fast` round marks the trace partial and does not close — R8), after the run
that closes the trace:

1. **Identify the session.** If `CLAUDE_CODE_SESSION_ID` is set, find
   `<id>.jsonl` under `~/.claude/projects/`. Absent, or no file, or a platform
   with no readable per-turn usage → **record nothing, and say so on stderr**
   (OR-8c: a material dependency degrades or fails loudly, never silently — the
   session transcript is exactly such a dependency).
2. **Bound it to the build.** Convert the trace's `opened_at`→`closed_at` to
   epoch and pass them as `--since`/`--until`, so the reading is the build's
   slice of the session, not the whole session.
3. **Map the field names** (the one translation): `cache_read_input_tokens` →
   `cache_read_tokens`, `cache_creation_input_tokens` → `cache_write_tokens`;
   `input_tokens`/`output_tokens` pass through. Write the four as a `usage.json`
   and pass `--usage usage.json` to the close.
4. **Record the model too.** The transcript names the model that ran; read it the
   way conformance reads `model_ran` (reuse `run_conformance._model_from_transcript`
   — one home) and pass `--model`. Effort is a session setting the transcript
   does not carry, so it stays null (honest).

The result: a `source=build` trace gains real `input/output/cache tokens` and a
real `model`, all from the platform's own record. The cost board, blank for real
delivery today, gets its first real rows.

## The open questions for review (the load-bearing ones)

1. **Time-window attribution.** `opened_at`→`closed_at` spans every build round
   (one trace spans N rounds, 0.1.602) but may also include session turns that
   were NOT this build (the author answered an email mid-session). Is the whole
   trace lifespan the right slice, or should the build phases be timestamped so
   the window is build-only? The trace records phase *durations*, not absolute
   phase timestamps — so a tighter window needs a new capture. Is the lifespan
   window good enough (a focused build session ≈ the build), with the over-count
   named as a known imprecision?
2. **Reading the author's transcript.** The file is on the operator's own machine
   and only token *numbers* + the model name are extracted (never content). But
   it is a read outside the repo — confirm it is OR-8c-compliant (degrade/loud,
   which the design does) and that extracting nothing but counts raises no
   privacy concern.
3. **Cost per close.** `session_cost` reads the whole JSONL; a long session makes
   that a non-trivial read on every full close. Acceptable on the full-close
   path (not the fast loop)? Or bound the read (it already streams)?
4. **Platform scope.** Claude Code is confirmed (env var + transcript). Hermes has
   a session id but a real build is driven by the author's own tool, not Hermes's
   driver; Cursor exposes only an end-of-session total (no per-turn window). So
   Claude Code is the realistic first target — is shipping it Claude-Code-only
   (others record null, honestly) the right scope, or wait for all three?
5. **Automatic vs opt-in.** Automatic when `CLAUDE_CODE_SESSION_ID` is present is
   cleanest, but reading the transcript on every full close is a new default. A
   flag (`--record-cost`) is more explicit but easy to forget. Which?

## What ships (pending review's answers)
- `scripts/ops/check_deliverable.py`: at full close, identify the session,
  compute the build-window cost, map fields, pass `--usage` and `--model`.
- possibly a small helper (in `session_cost.py` or `check_deliverable.py`) that
  turns a `CLAUDE_CODE_SESSION_ID` into a transcript path and a bounded reading.
- reuse `run_conformance._model_from_transcript` for the model (one home; if it
  is not importable across the boundary, that move is part of the work).
- tests: a synthetic transcript + a session id yields a `--usage` with the four
  mapped counts and a `--model`; an absent env var records nothing and says so
  (OR-8c deliberate-red); the field rename is asserted.
- `KNOWN_GAPS.md`: GAP-048 → fixed for the readable platforms; any residual
  (effort, non-Claude platforms) named.

## What this is NOT
- Not self-reported: the numbers are the transcript's own.
- Not the whole-session total: it is the build's slice, bounded by the trace's
  lifespan.
- Not effort: the transcript does not carry it; it stays honestly null.
- Not a `--fast` concern: fast rounds mark partial and never close (R8).

## Verification (once the design settles)
- Deliberate red planted first: a build close with a resolvable session records
  non-null tokens+model; with no session id it records nothing AND prints the
  skip (OR-8c three-answers — recorded / honest-null-and-said-so).
- The field rename is asserted against `trace._read_usage`'s expected names.
- preflight green; one release, one commit.
