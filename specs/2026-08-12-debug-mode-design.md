# Debug mode — design record

Date: 2026-08-12 · Status: settled, implementing at 0.1.445 · Owner ask:
recorded in the 0.1.442 review retrospective
(`specs/2026-08-12-owner-review-retrospective-design.md` D9).

## The ask

When the user requests debug mode, the skill writes an execution log beside
the deliverable — errors, performance, and an assessment of the output's
quality — so a later session can run a detailed eval from the log alone.
Requirements: macOS and Windows; every agent platform the registry claims
(Claude Code, Codex, Cursor, Gemini, Pi, OpenClaw, Hermes, …); English only.

## Decisions

**D1 — One schema, one helper, no per-platform forks.**
`scripts/ops/debug_log.py` (standard library only, like every deliverable-path
script) owns the file format; agents call its subcommands rather than writing
JSON by hand, so Codex and Pi produce the same log Claude Code does. Platform
coverage costs nothing new: `full`-tier platforms run the script; `prompt`-tier
platforms cannot run anything, so the core prompt tells them to write what
they can into the delivery note and NAME what they owe — the same degradation
contract the checkers already use ("an agent that cannot run the checks names
the checks it owes"). `adapters/` does not change: a per-platform note about
debug mode would be a restated rule, which the registry's own header forbids.

**D2 — Reuse the shapes this repo already trusts.**
- *Performance*: step entries carry `label` + `seconds` — the
  `releases/perf-baseline.json` shape, with the machine recorded once at the
  top (AG-3: local, warn-only timing is the sanctioned form; the log records,
  nothing gates on speed).
- *Commands*: `debug_log.py run -- <cmd>` EXECUTES the command and
  machine-writes `command`, `exit_code`, `stdout_sha256`, `seconds`, `date` —
  the evidence-gate shape, and its principle: there is no verdict field for a
  human to type, so an unexecuted claim has nowhere to live.
- *Quality*: the three checkers' `--json` documents attach verbatim under
  `checks.{design,prose,layout}` (their `verdicts` maps already speak
  `ok|FAIL|n/a`), and the agent's H1–H6 self-scores go under `quality` with a
  mandatory reason per score — bound by the standing rule that 5 is never
  self-scored before a reader has scored it (`review_scores.py`'s rule; the
  helper refuses to write one).
- *Errors*: `{stage, message}` entries, appended as they happen.

**D3 — The key set is closed.** Unknown top-level keys fail `validate`, for
the same reason `reviews/scores.json` closes its record keys: the
engagement-fact defence is that there is nowhere to put one. The log carries
metrics, commands, paths, scores and reasons — never client names or figures
(red line; `validate` also enforces English-only content).

**D4 — Where it lands and what it is called.** Beside the deliverable —
`<deliverable stem>.debug.json` — in the same directory `output_dir.py`
resolves, which is what makes macOS/Windows/Linux one code path. The log is a
working artifact of the engagement folder and is never committed to this
repository.

**D5 — Trigger.** The user says "debug mode" (any casing) in the request; the
skill then: `init` at start, `run` for every check/build command it executes,
`attach` for checker JSON, `assess` after the self-score step it already
performs, `error` on any failure, and points the user at the file in the
delivery note. Without the words "debug mode", nothing is written — the log
is a request, not a default.

## Acceptance

`debug_log.py` ships with pytest coverage proving each subcommand writes what
it claims, that `assess --score 5` is refused, and that `validate` goes red on
an unknown key and on CJK content (deliberate-red recorded in the CHANGELOG
entry). The first real log is written during the owner's acceptance rebuild.
