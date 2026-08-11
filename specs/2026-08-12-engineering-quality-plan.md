# Engineering quality — the plan

Date: 2026-08-12 · Decomposes `2026-08-12-engineering-quality-design.md` into
releases, R1 through R12 — version numbers are assigned at ship time, one
per release, never promised in advance (the version-citations guard is right
about that); each release carries its own
CHANGELOG entry, the full version-stamp set, and ends with
`python3 scripts/preflight.py` green. Every release that adds a gate performs
and records a deliberate-red run (design D8).

## R1 — CI hygiene + JavaScript syntax checks

- `ci.yml`: replace the hand-maintained 26-file `py_compile` list with
  `python3 -m compileall -q -f scripts/` (covers all 29, cannot rot); add
  `actions/setup-node@v4` (node 22 — a `uses:` step, invisible to
  `preflight.py`'s `- run:` parser by design).
- `preflight.py`: delete the two stale "fifteen commands" hand-counts from
  the docstring — removing the claim, not re-counting it.
- New `scripts/check_js.py` + one `- run:` step: `node --input-type=module
  --check` over every `git ls-files '*.js'` result, then over the three probe
  strings imported from `inspect_layout` (wrapped in parens). The embedded
  probes stay embedded: extraction would change the single-file operator
  story for zero added checking power.

## R2 — toolchain

- `pyproject.toml` (tool sections only; header states the deliverable path
  stays zero-dependency) + `requirements-dev.txt` (exact pins).
- ruff: `E4,E7,E9,F,W,I,B,UP,S,C4`; `S` is the security scan; per-file
  ignores for `preflight.py` (S602) and `tests/` (S101). Burn down existing
  findings (auto-fix I/UP; fix or targeted-noqa the rest).
- mypy: `check_untyped_defs`, `no_implicit_optional`, playwright override;
  strict override reserved for the R4 shared libraries.
- `ci.yml`: `pip install -q -r requirements-dev.txt`, `ruff check .`, `mypy`.
- Split into two releases if the mypy burn-down proves deep.

## R3 — pytest + characterization tests (strictly before R4)

- `tests/` + `tests/conftest.py` (one `sys.path.insert` to `scripts/`).
- `test_color_math.py`, `test_css_tokens.py` written against the CURRENT
  duplicated copies: linearizer boundary channels, both thresholds recorded,
  black-on-white contrast 21.0, the 0.1.415 comment regression, and
  `build_brand._vars`'s live comment bug pinned as xfail.
- `test_sea_route.py`, `test_review_scores.py` (pure cores with no coverage).
- Not tested: geo_projection (the golden grid owns it), Playwright paths,
  the eleven `--check` steps (CI owns them).
- `ci.yml`: `python3 -m pytest -q`.

## R4 — dedup refactor

- `scripts/color_math.py`: `srgb_linear` (one threshold, 0.04045, history
  noted), `srgb_encode`, `luma`, `contrast_ratio`, `hex_to_rgb`, `mix` —
  strict-mypy from birth. The high-precision-coefficient luma in
  `build_region_palette.py` stays: it is deliberately a different formula.
- `scripts/css_tokens.py`: `strip_comments`, `css_block`, `css_vars` (the
  fixed check_repo version is canonical), `rule_vars` (fixing the
  build_brand bug).
- Order: point the R3 tests at the new modules → repoint call sites
  (check_repo, check_design, build_brand, build_region_palette,
  inspect_layout) → delete local copies.
- Gate: every generator `--check` stays byte-identical. If the threshold
  unification shifts one emitted byte, abort and split into its own release.
- New guard `check_no_shadow_math` in `check_repo.py`: no re-duplication of
  the shared functions outside the shared modules.

## R5 — guard tests, wave 1

- `tests/test_check_repo_guards.py`: synthetic repos in `tmp_path` via
  monkeypatched `ROOT`; one passing and one failing fixture per guard —
  the failing fixture is the point. First wave: check_versions,
  check_english_only, check_palette_parity, check_version_citations,
  check_links. Later waves cover the rest.

## R6 — ledgers

- `KNOWN_GAPS.md`: `## GAP-NNN` entries with status/opened/surface/symptom/
  check; `fixed` needs `closed:`, `declined` needs `closed:` + `reason:`.
  Seeds: the T1-deck double failure; the five-checks-verified-by-prose gap
  (closed by R8–R9, giving the ledger a real closure immediately).
- `FAILURE_MODES.md`: the ten recurring failure families extracted from
  CHANGELOG history, each with detection/prevention; an "Abandoned gates"
  section seeded with design §3.
- Restore `Pipeline/ideas-prd.md` from `e861df0^`, add stable `IDEA-NN` ids.
- One guard, `check_ledgers`: id uniqueness, status validity, per-status
  required keys, closed-version cross-check against CHANGELOG, no
  GAP-citing TODO/FIXME in scripts/ or references/, no dangling
  `GAP-`/`FM-`/`IDEA-` references in CHANGELOG or specs/.

## R7 — commit convention guard

- `check_commit_convention`: only commits that touch `CHANGELOG.md` must
  match `^X.Y.Z — ` with the version equal to the newest heading; merge
  commits examine `HEAD^2`; no-`.git` returns clean. Everything else exempt.

## R8 — evidence gate, warn-only

- `scripts/check_evidence.py` + tracked `releases/evidence/<version>.json`.
  Schema (no verdict field): version, diff_base, spec, obligations, checks
  (command/exit_code/stdout_sha256/artifact/artifact_sha256/date), waivers.
- `--init`: previous release found by commit-subject prefix → diff →
  TOUCH_MAP → skeleton. `record --id`: executes the canonical command and
  machine-writes the entry. `--check [--warn]`: missing file, unmet
  obligation, CI-recomputed obligation superset, duplicate digests (D6),
  missing fields (D7), nonzero exit without a `gap: GAP-NNN` citation,
  overclaim phrases in the newest CHANGELOG section while waivers exist.
- Spec discipline folded in: >150 changed lines touching scripts/ or
  references/ or tokens/ requires the `spec` field to name a real specs/
  file cited in the CHANGELOG entry, or a written waiver.
- `ci.yml`: checkout `fetch-depth: 0`; `- run: python3
  scripts/check_evidence.py --check --warn`. This release's own evidence
  file is produced by the gate's `--init` + `record`.

## R9 — the gate goes red

- Drop `--warn`. The three planted violations from R8 now exit non-zero and
  redden preflight; then the honest run is green.

## R10 — globe JS golden grid in CI

- `check_globe.py`: split "obtain JS results" from "compare against golden";
  add a `--node` backend running the 1300-sample grid under bare node
  (projection.js is DOM-free; verified importable). CI step becomes
  `--python-only --node`; a missing/ancient node fails loudly, never skips.

## R11 — conformance as routine practice

- Tracked `conformance/history.json`; `run_conformance.py report --record`
  appends rows (skill_version, agent, date, run_dir, per-task verdicts,
  scores_sha256) and re-renders CONFORMANCE.md; `validate` checks the
  history file's shape. Seed from the three existing run dirs on disk.
- Arm the `conformance-freshness` obligation in check_evidence: rule-surface
  releases with history >15 versions stale require fresh rows for ≥2 agents
  across all three tasks, or a written waiver.

## R12 — secrets guard, CLI smoke, performance floor

- `check_secrets` guard: high-signal patterns only (AKIA, PRIVATE KEY,
  ghp_/github_pat_, sk-, generic key assignments) over `git ls-files` text
  files, with an allowlist; pass/fail tests.
- `tests/test_cli_contracts.py`: `--help` exits 0 for every argparse script;
  a few `--selftest`-class flags CI does not already run.
- `preflight.py --timing --update` writes `releases/perf-baseline.json`
  (keyed by command digest); subsequent runs print WARN for steps exceeding
  max(2× baseline, baseline + 5s). Warn-only, local-only, never a CI step.

## Closing

- Update CLAUDE.md's Checks section and maintenance conventions; re-read the
  three entry points and README for prose drift.
- Run the full (by then ~23-step) preflight and record it as the closing
  evidence file for the final release.
