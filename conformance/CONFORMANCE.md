# LUMI style conformance · skill 0.1.381

Runs `conformance/results/cursor-20260808`, `conformance/results/claude-code-20260808` · darwin · 1 of 12 agents detected · n=1 per agent

| agent | capability | cli | T1-deck | T2-deaify | T3-recall | verdict |
|---|---|---|---|---|---|---|
| Claude Code | full | 2.1.226 (Claude Code) | pass | pass | pass | **pass** |
| Gemini CLI | full | — | — | — | — | **not installed** |
| OpenAI Codex | full | — | — | — | — | **not installed** |
| Cursor | full | driven by hand | fail: design exited 1, layout exited 1, D14_placeholders=FAIL, collision=FAIL | pass | pass | **fail** |
| Google Antigravity | full | — | — | — | — | **not installed** |
| GitHub Copilot | full | — | — | — | — | **not installed** |
| OpenCode | full | — | — | — | — | **not installed** |
| Pi | full | — | — | — | — | **not installed** |
| OpenClaw | full | — | — | — | — | **not installed** |
| Hermes | full | — | — | — | — | **not installed** |
| Kimi | prompt | — | — | — | — | **not installed** |
| DeepSeek | prompt | — | — | — | — | **not installed** |

## What this table is not

It is not a claim that any model produces good output: the checks measure mechanical conformance, and a page is done when a human reads it as intentional. Each row is one run of one CLI version on one machine on one date, not a property of the agent. Rows marked `not installed` were not exercised and are listed rather than omitted. A cell reading `stale: task changed` means the recorded verdict answers a version of that task the repository no longer contains — it is not a pass and not a failure, it is a result that has to be re-earned.

**A verdict can change without the artifact changing.** The checks are the moving part: a row re-scored after a release that taught the checkers something new is a statement about this package's instruments on that date, not about the model that wrote the file. A `pass` that later reads `fail` most often means the earlier run measured less.

