# The expressive register — plan

Date: 2026-08-11 · Decomposes `2026-08-11-expressive-register-design.md`.
Branch off `main` (0.1.405). Intermediate commits carry no version stamp; the
final commit is the release. Every commit leaves
`python3 scripts/check_repo.py` green.

1. **Record the design.** This file and the design doc. *(specs are history,
   not authority — the rules land in commit 5.)*
2. **The water.** `scripts/build_seigaiha.py` (ground `<defs>` +
   band `<defs>`, fixed jitter tables, `--check` against tracked output in
   `assets/vectors/`); band and illustration tokens in both `tokens/` files
   (parity guard); `build_fixtures.py` adopts the generated ground.
3. **The icons.** `assets/icons/lumi/` first batch (~24 targets);
   `embed_icons.py`: second library, `--register expressive` lumi-first
   resolution, `--check` extended over both directories.
4. **The illustrations.** `assets/illustrations/` first batch (~12 targets) +
   `manifest.json`; `scripts/embed_illustrations.py` (embed / `--list` /
   `--search` / `--check`).
5. **The rules.** `references/brand.md` (registers, band, illustration
   honesty, §4 scoping), `references/design-rules.md` (§5 + illustration
   section + verification matrix), `references/storyline-templates.md`
   (training scenario, cover note); `tokens/lumi-layouts.css` base renderings
   for `.illo` and `.band`.
6. **The checks.** `check_design.py` (register gate + diagnostics),
   `inspect_layout.py` (band-placement finding, illustration ink),
   `build_fixtures.py` expressive fixture, `check_fixtures.py` verdicts.
7. **The release.** Entry points by hand (`SKILL.md`, `AGENTS.md`,
   `prompts/lumi-style-core.md`, `README.md`); `build_entrypoints.py`;
   `.github/workflows/ci.yml`; `CHANGELOG.md`; version bump across the
   hand-stamped tier. Rendered verification per design §4 before the bump.
