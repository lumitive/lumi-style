# Contributing

This repository runs on a small set of non-negotiable maintenance
conventions. They exist because each one closed a shipped defect — the
CHANGELOG entry that introduced each rule tells its story.

## Before you open a PR

1. **Rules change only from documented cases.** A rule in `references/` is
   added or changed only off a review retrospective or a reported defect —
   never speculatively. If your PR touches `references/`, its description
   names the case.
2. **One version, moved everywhere at once.** A release bumps the version in
   SKILL.md's frontmatter, the newest CHANGELOG heading, the three `tokens/`
   file headers, `AGENTS.md`, `prompts/lumi-style-core.md` and
   `conformance/CONFORMANCE.md` — CI refuses a partial move
   (`check_versions` holds the first five; `check_version_citations`' 
   ENTRY_STAMP table holds the entry-point stamps). Commit subjects for release commits read
   `X.Y.Z — comma-separated summary` (guard-enforced when CHANGELOG is
   touched).
3. **Run what CI runs, before pushing**: `python3 scripts/preflight.py`
   executes the exact step list from `ci.yml`. "Local green" and "CI green"
   are the same claim here by construction.
4. **Generated files are never edited by hand.** `adapters/*.md`, GEMINI.md,
   the Copilot/Cursor rule files, the plugin manifests and the fixtures are
   written by `scripts/build/build_entrypoints.py` and
   `scripts/build/build_fixtures.py`; edit the source or the registry
   (`adapters/platforms.json`) and regenerate.
5. **Every new gate ships with a deliberate-red run** — plant a violation,
   watch it fail, remove it, and say so in the CHANGELOG entry. Guards get
   synthetic-tree tests with at least one failing fixture.
6. **State lives in the ledgers**: defects in `KNOWN_GAPS.md`, recurring
   failure shapes in `FAILURE_MODES.md`, proposals in `backlog/ideas-prd.md`.
   Cite their ids; a dangling citation fails CI.
7. **No client names, project figures, or engagement facts** — anywhere,
   ever. This binds CHANGELOG entries hardest.

Dev tooling (`pytest`, `ruff`, `mypy`, node for the JS checks) is pinned in
`requirements-dev.txt`; the shipped skill itself runs on the Python standard
library alone.

## What a review will ask

Does the change carry its documented case? Did preflight pass? If a rule
changed, was it re-flowed into the entry points (`SKILL.md`, `AGENTS.md`,
`prompts/lumi-style-core.md`) — the drift the checks cannot see?
