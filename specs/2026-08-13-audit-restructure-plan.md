# The audit — the plan

Date: 2026-08-13 · Decomposes `2026-08-13-audit-restructure-design.md`.
Releases R0-R5, versions assigned at ship time; each carries CHANGELOG, the
stamp set, an evidence file, preflight green, and a deliberate-red run for
every new or changed gate. Moves use `git mv`.

## R0 — cleanup + backlog rename (shipped as 0.1.436)

Delete the `1` typo file and the superseded 298KB backlog render (ignore
hole closed with `backlog/*.html`); untrack the four contradicted contact
sheets; `Pipeline/` → `backlog/` with the full live-reference sweep;
document `new_deck.py` in the Checks block; write the evidence-retention
line; disk-only cache cleanup + remote-ref prune.

## R1 — hardening (all silent points made loud, before anything moves)

1. `check_script_paths` guard: every `scripts/[\w./-]+.(py|sh)` string in
   live tracked text (all *.md except CHANGELOG and specs/, all *.py/*.sh,
   ci.yml, platforms.json, design-tokens.json, pyproject, NOTICE, tokens
   CSS, assets JS) must resolve to a file; `SCRIPT_PATH_WAIVERS` starts
   empty.
2. `check_bootstrap` guard: a script with a sibling import must carry the
   canonical bootstrap block.
3. rglob (with `__pycache__` filtered) in check_no_shadow_math,
   check_ledgers, tests/test_cli_contracts.
4. check_evidence: TOUCH_MAP file-entries and OBLIGATIONS script paths must
   exist on disk, else the gate fails.
5. The canonical bootstrap block lands in every sibling-importing script
   (replacing the ad-hoc inserts); conftest inserts all drawers; mypy gains
   `mypy_path`; the strict override's bare names stay valid.
6. emergency_merge.sh copies the trusted closure (check_repo + lib three)
   and PYTHONSAFEPATH runs green — fixing the live defect; a permanent
   regression test locks it.
7. `deliverable_registry.py`: the one copy of the checker map;
   check_fixtures and run_conformance both consume it (FM-07 closed).

## R2 — move lib/ render/ build/ (19 files, one lock ceremony)

ci.yml build/embed steps; LOCKED.json keys hand-renamed BEFORE
`lock.py --update`; locked JS comment citations updated and re-embedded;
TOUCH_MAP geo/globe entries; builder banner literals + full regeneration;
layout-fixtures and globe-js obligations recorded; guard-enforced docs
sweep.

## R3 — move check/ (8 files)

ci.yml check steps; check_repo's seven AST literal paths; the registry's
one `"check"` line; OBLIGATIONS commands + inspect_layout/check_globe
TOUCH_MAP entries; emergency/ci_wait check_repo paths; builder body
literals + regeneration; obligation-appearance is a stop-ship check.

## R4 — move ops/ (7 files) + finalization

ci.yml conformance + bash -n lines; OUTPUT_DEFAULT_SITES literal and its
name-comparison special case (both); review_scores subprocess path;
conformance-freshness command; export_pdf path; the two shell scripts'
`$SCRIPT_DIR`-relative rework (`../check/`, `../lib/`); perf baseline
re-recorded; hand-written `scripts/README.md`; final grep audit outside the
frozen zones.

## R5 — public-repo normalization

README badges + honest license section (MIT + NOTICE third-party) + true
entry-point list + tree; CONTRIBUTING.md; SECURITY.md (private disclosure
via GitHub Security Advisories); SKILL.md `compatibility` + the specs/
pointer redirected to references/; `assets/icons/lucide/LICENSE` (ISC text
travels with the vendored set); plugin.json `repository`/`keywords` via the
builder; TOCs for the long references files.
