# LUMI style conformance · skill 0.1.439

Runs `conformance/results/cursor-20260813`, `conformance/results/claude-code-20260813` · darwin · 1 of 12 agents detected · up to n=1 per agent · 4 of 12 can never answer a CLI probe

| agent | capability | cli | T1-deck | T2-deaify | T3-recall | verdict |
|---|---|---|---|---|---|---|
| Claude Code | full | 2.1.228 (Claude Code) | pass | pass | pass | **pass** |
| Gemini CLI | full | — | — | — | — | **not installed** |
| OpenAI Codex | full | — | — | — | — | **not installed** |
| Cursor | full | driven by hand | pass | — | — | **pass** |
| Google Antigravity | full | — | — | — | — | **cannot be probed** |
| GitHub Copilot | full | — | — | — | — | **not installed** |
| OpenCode | full | — | — | — | — | **not installed** |
| Pi | full | — | — | — | — | **not installed** |
| OpenClaw | full | — | — | — | — | **not installed** |
| Hermes | full | — | — | — | — | **cannot be probed** |
| Kimi | prompt | — | — | — | — | **cannot be probed** |
| DeepSeek | prompt | — | — | — | — | **cannot be probed** |

## What this table is not

It is not a claim that any model produces good output: the checks measure mechanical conformance, and a page is done when a human reads it as intentional. Each row is one run of one CLI version on one machine on one date, not a property of the agent. Rows marked `not installed` were not exercised and are listed rather than omitted. A cell reading `stale: task changed` means the recorded verdict answers a version of that task the repository no longer contains — it is not a pass and not a failure, it is a result that has to be re-earned.

**Absence has two kinds and they are marked differently.** A row reading `not installed` is a machine away: the agent ships a CLI, nobody has run it here, and one install would produce a row tomorrow. A row reading `cannot be probed` never will — an IDE with no command line, and chat models reached through an API — so its artifacts have to be produced by hand and scored with `--agent`. Printing the two identically made the board read as ten pieces of pending work when only six are.

**Where a cell names more than one run, it names the spread too.** `3 runs, all pass` is a different claim from `3 runs UNSTABLE: fail×1, pass×2`, and until 0.1.390 the harness could not tell them apart: a repeat of an agent OVERWROTE its earlier row, so every verdict was one sample and a flaky checker could not be distinguished from a flaky agent. Repeating costs tokens and produces an uncomfortable number, which is the value.

**A verdict can change without the artifact changing.** The checks are the moving part: a row re-scored after a release that taught the checkers something new is a statement about this package's instruments on that date, not about the model that wrote the file. A `pass` that later reads `fail` most often means the earlier run measured less.

**Superseded runs.** The 2026-08-08/09 runs (both agents failing T1-deck)
measured a skill that shipped a colliding media block in its own tokens until
0.1.380, scored with instruments added after the decks were built — the
GAP-001 diagnosis, 0.1.433; closed by re-run at 0.1.434. Their rows are
preserved in `conformance/history.json`. Since 0.1.435 (IDEA-8) every score
pins its instrument version and the artifact's colophon build version, and a
verdict conflict that aligns with different builds renders as "skill changed
between builds" with the latest build governing — never as agent
instability.

## What this table is not

It is not a claim that any model produces good output: the checks measure mechanical conformance, and a page is done when a human reads it as intentional. Each row is one run of one CLI version on one machine on one date, not a property of the agent. Rows marked `not installed` were not exercised and are listed rather than omitted. A cell reading `stale: task changed` means the recorded verdict answers a version of that task the repository no longer contains — it is not a pass and not a failure, it is a result that has to be re-earned.

**Absence has two kinds and they are marked differently.** A row reading `not installed` is a machine away: the agent ships a CLI, nobody has run it here, and one install would produce a row tomorrow. A row reading `cannot be probed` never will — an IDE with no command line, and chat models reached through an API — so its artifacts have to be produced by hand and scored with `--agent`. Printing the two identically made the board read as ten pieces of pending work when only six are.

**Where a cell names more than one run, it names the spread too.** `3 runs, all pass` is a different claim from `3 runs UNSTABLE: fail×1, pass×2`, and until 0.1.390 the harness could not tell them apart: a repeat of an agent OVERWROTE its earlier row, so every verdict was one sample and a flaky checker could not be distinguished from a flaky agent. Repeating costs tokens and produces an uncomfortable number, which is the value.

**A verdict can change without the artifact changing.** The checks are the moving part: a row re-scored after a release that taught the checkers something new is a statement about this package's instruments on that date, not about the model that wrote the file. A `pass` that later reads `fail` most often means the earlier run measured less.

**Superseded runs.** The 2026-08-08/09 runs (both agents failing T1-deck)
measured a skill that shipped a colliding media block in its own tokens until
0.1.380, scored with instruments added after the decks were built — the
GAP-001 diagnosis, 0.1.433. Their rows are preserved in
`conformance/history.json` (which pins each row's skill version); this table
answers "does the CURRENT skill conform", so it renders the runs made against
it. IDEA-8 in the backlog is the structural fix: a score row should pin its
instruments.

## What this table is not

It is not a claim that any model produces good output: the checks measure mechanical conformance, and a page is done when a human reads it as intentional. Each row is one run of one CLI version on one machine on one date, not a property of the agent. Rows marked `not installed` were not exercised and are listed rather than omitted. A cell reading `stale: task changed` means the recorded verdict answers a version of that task the repository no longer contains — it is not a pass and not a failure, it is a result that has to be re-earned.

**Absence has two kinds and they are marked differently.** A row reading `not installed` is a machine away: the agent ships a CLI, nobody has run it here, and one install would produce a row tomorrow. A row reading `cannot be probed` never will — an IDE with no command line, and chat models reached through an API — so its artifacts have to be produced by hand and scored with `--agent`. Printing the two identically made the board read as ten pieces of pending work when only six are.

**Where a cell names more than one run, it names the spread too.** `3 runs, all pass` is a different claim from `3 runs UNSTABLE: fail×1, pass×2`, and until 0.1.390 the harness could not tell them apart: a repeat of an agent OVERWROTE its earlier row, so every verdict was one sample and a flaky checker could not be distinguished from a flaky agent. Repeating costs tokens and produces an uncomfortable number, which is the value.

**A verdict can change without the artifact changing.** The checks are the moving part: a row re-scored after a release that taught the checkers something new is a statement about this package's instruments on that date, not about the model that wrote the file. A `pass` that later reads `fail` most often means the earlier run measured less.

