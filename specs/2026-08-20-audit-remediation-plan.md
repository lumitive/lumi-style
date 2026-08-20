# Audit remediation · plan

Date 2026-08-20 · Design: `2026-08-20-audit-remediation-design.md` · Status: **proposed**

Branch `audit-remediation` off `main` at `cf940fb`. One PR. Every step below is
one release commit cut by `scripts/ops/release.py` (preflight must be green; no
override exists). Versions are assigned at landing by `release.py`; this file names steps,
never version numbers, so it cannot drift against the CHANGELOG. New ledger
entries are named by their title here and get their ids when opened.
Each step lists: **change · red run · tests · ledger**.

## Step 0 · the held batch (one release) (needs D0)

- change: commit the working tree as it stands (CJK mirror matcher in
  `check_outline.py`, CJK normaliser in `check_design.py`, `check_facts.py`
  false-positive fixes, `.lede` reserve 2+2 → 1+2 with the 24px gap term,
  regenerated fixtures, the six new tests) **plus** `git add` of the 33 koboyo
  icons and the model SVGs the manifests already describe; koboyo
  `SOURCES.md` count corrected to the number `ls` returns.
- the three owner-supplied PNGs follow **D1**: with provenance they ship here;
  without, they leave the manifest and the tree in this same commit.
- red run: already recorded in `tests/test_fact_and_outline_defects.py` §7–§10.
- ledger: none new. Note in CHANGELOG that IDEA-14 (zh assertion in `is_label`)
  is **not** closed by this batch.

## Step 1 · instruments that fail

- change:
  - `scripts/ops/trace.py`: `--phase` keeps `nargs=2` but the second value is
    parsed with `float` and rejected if ≤0; `trace_schema.validate()` types
    every `phase_seconds` value as a number.
  - `scripts/check/inspect_layout.py:2832`: `aspect_report(path, dark,
    STAGE_OF[declared_geometry])`; the matrix loop variable is renamed so the
    leftover cannot be reused by accident.
  - `scripts/check/check_design.py` `d26_declared_scope`: `missing` is
    computed from `TYPICAL_SECTIONS` against `data-section` ids and
    `data-omitted` declarations; the row reports `missing` as a **reported**
    finding so `check_deliverable.py` prints it; pass condition unchanged.
- red run: a trace closed with `--phase build 12` that `ledger.py` sums; a
  correct 16:9 fixture reporting 0/N off-shape and a 4:3 fixture reporting
  N/N; `fixtures/deck-pass` (pitch-deck) surfacing its undeclared sections.
- tests: `tests/test_trace.py` CLI path; `tests/test_inspect_layout_aspect.py`
  (new); `tests/test_declared_scope.py` extended.
- ledger: none.

## Step 2 · one credential table, one markup helper

- change: `scripts/lib/secret_patterns.py` holds the union of both tables
  (`github_pat_` and `AKIA|ASIA` and Slack/Google/JWT/URL-creds and the
  assignment shapes); `check_repo.py` and `check_privacy.py` import it; new
  guard `secret patterns parity`; `scripts/lib/markup.py` gains
  `visible_text()` and `join_cjk()`; `check_facts.py`, `check_outline.py`,
  `judge_findings.py`, `check_privacy.py`, `check_design._norm_line` call
  them; new guard `no shadow markup`.
- red run: a private `re.compile(r"ghp_…")` planted in `check_privacy.py`;
  a private `re.sub(r"<[^>]+>"` planted in `check_facts.py`.
- tests: `tests/test_check_repo_guards.py` gains both guards with failing
  synthetic trees; `tests/test_markup.py` covers the two helpers.
- ledger: none.

## Step 3 · privacy boundary

- change: `references/operating-rules.md` names `~/.lumi/terms/<engagement>.terms.txt`
  as the canonical location and restates the three constraints; `SKILL.md`
  and `AGENTS.md` point at it; `.gitignore` nets `*.terms.txt` and
  `terms-oob*` with a written reason; `check_privacy.py` strips `data:` URIs
  and `@font-face` base64 before term matching; the `secrets` guard in
  `check_repo.py` also runs every list under `~/.lumi/terms/` over tracked
  text files when the directory exists, and reports `not attempted` when it
  does not (CI).
- red run: `Ray` in a terms file against a fixture with an embedded font
  (must **not** fire); a real term planted in a tracked file (must fire).
- tests: `tests/test_check_privacy.py` base64 case; guard test.
- ledger: **closes IDEA-15**.

## Step 4 · prose drift, with a guard

- change:
  - `references/eval-rubric.md:385` and `:362` cite D23 and D27; `:19` "ten
    of the twelve" deleted in favour of "the table is the list".
  - `references/design-rules.md:622`: DR-6 split into `DR-6` (figure form,
    P-4), `DR-6a` (accent colour, P-1), `DR-6b` (source line, P-2); the three
    ids are added to `FROZEN_RULE_IDS`.
  - `KNOWN_GAPS.md` GAP-005 reworded to the tier model (three tiers, two
    without an accepted reference; `product-intro` is a storyline and has a
    template).
  - `scripts/ops/review_scores.py` docstring.
  - `adapters/platforms.json` Cursor waiver text updated to what
    `run --drive` does today.
  - new guard `rubric self-consistency` (design §3 row 3).
- red run: "there is no D23 check" planted beside the D23 row.
- tests: guard test with a failing synthetic rubric.
- ledger: none new.

## Step 5 · conformance board honesty

- change: `run_conformance.py report` writes the run date into the generated
  header and **generates** the per-agent narrative from `scores.json`
  (the hand-written block under the table is deleted; anything worth keeping
  moves above the generated marker as history); `run --drive` clears the
  agent's task directory before driving and writes a per-run directory
  (`results/<version>-<date>/`) that `history.json` names, so a run id never
  points at an older tree; stale `results/latest/claude-code/T1-deck/deck.en.html`
  removed.
- red run: a `scores.json` saying `pass` under a prose line saying `fail` —
  impossible after the change; the test asserts the generator is the only
  writer.
- tests: `tests/test_run_conformance.py` extended.
- ledger: none.

## Step 6 · the ledger catches up

- change: open seven GAP entries — T1 zero readings (closed in Step 8 of
  this branch); privacy layer 3 is not the designed T3; `check_outline`
  covers 3 of 13 outline items; recolour tool outside the repo (closed in
  Step 9); AGENTS.md grew against D1 (closed in Step 13); D2 conformance
  cleanup never done (closed in Step 5); `feedback` trace field dropped
  without a decision — and two IDEA entries: `marketing` genre has no
  behaviour; M13 reads differently on a zh twin. Each entry names its close
  condition; ids are assigned when opened.
- red run: the ledger guard on a deliberately dangling cite.
- ledger: this step **is** the ledger.

## Step 7 · prompt tier parity

- change: the capability-tier sentence (obligation **and** prohibition)
  moves to `references/operating-rules.md` as `OR-8`; `platforms.json` and
  `eval-rubric.md:422` cite it; `prompts/lumi-style-core.md` gains the
  number-first rule (the `design-rules.md` §7 sentence, verbatim), all eight
  storyline names with one-line skeletons for the six missing, the eighteen
  missing banned phrases, and the unconditional owed-checks sentence; new
  guard `prompt parity` (design §3 row 8) with a `NOT_IN_PROMPT` waiver table.
- red run: delete one storyline name from the prompt.
- tests: guard test.
- ledger: none.

## Step 8 · T1 gets readings

- change: `trace.py phase start <name>` / `phase stop <name>` stamp the
  clock themselves and write the difference; `--phase` stays for the API
  dump path only; `new_deck.py --outline` opens the trace (or takes
  `--trace`) and stamps `outline`; `check_deliverable.py` takes `--trace`,
  stamps `checks`, and prints `unmeasured  trace: none` in the verdict block
  when absent; `run_conformance.py run --drive` passes `--model` and
  `--effort` to the driver and records both in the trace it opens;
  `ledger.py --board` already qualifies runs, so no change there.
- red run: a `check_deliverable` run without `--trace` shows `unmeasured`; a
  drive with `--effort low` lands `effort: low`.
- tests: `tests/test_check_deliverable.py`, `tests/test_trace.py`.
- ledger: **closes GAP «T1 zero readings»**. The six matrix cells themselves are an operator
  step (D4) recorded through `check_evidence.py record`.

## Step 9 · the recolour tool comes home

- change: `scripts/build/recolor_shapes.py` ported from
  `_refactor/tools/recolor_lumi.py`, reading the token values from
  `tokens/design-tokens.json` through `css_tokens.py` (no private colour
  maths — the `no shadow math` guard holds it); the un-recoloured originals
  vendored under `assets/shapes/source/` with `SOURCE.md`; `--check` in
  `ci.yml` asserts byte-identical regeneration.
- red run: one edited byte in `assets/shapes/p009-arrow-3d-01.svg`.
- tests: `tests/test_recolor_shapes.py`.
- ledger: **closes GAP «recolour tool outside the repo»**.

## Step 10 · knowledge reaches the build

- change: `new_deck.py --outline` maps `analysis: <move>` →
  `frameworks.json` → shape family and emits a `<use href="#shape-…">` slot
  on that figure page (the scaffold already carries the contract card; the
  slot joins it); `check_design.py` gains **D31 shape-library use**
  (reported); `SKILL.md` step "analysis beat" and `AGENTS.md` load
  `references/exemplars/mckinsey-design-notes.md` and `yc-pitch-notes.md`
  there; `.field` follows **D5** (default: the scaffold offers it on the
  thesis page).
- red run: an outline with five `compare` moves yields five slots; D26/D19
  already red when a slot points at nothing.
- tests: `tests/test_new_deck_outline.py` extended; `tests/test_check_design.py` D31.
- ledger: none.

## Step 11 · evidence is not deleted

- change: `review_scores.py --check` requires every scored `corpus_id` to
  resolve (file exists) or to carry `archived: {sha256, pages, removed_at}`;
  D15/D16/D17 get archive records built from `_layout/` sheet metadata
  **marked as such** (no measurement is invented); `operating-rules.md` gains
  "a scored document is never deleted; superseded builds may be"; the
  Chengdu BP registered as **D18** with a generated scoring sheet (D2);
  `evals/thresholds.json` A1 entry gains `accepted_under` and
  `shippable_under_current_gates: false` with GAP «A1 fails D27» recording D3.
- red run: a record citing an id with neither file nor archive.
- tests: `tests/test_review_scores.py`.
- ledger: opens GAP «A1 fails D27» (A1 vs D27) carrying the owner's D3 ruling.

## Step 12 · red-line edge and manifests

- change: neutral wording replaces the city name in `tokens/lumi-layouts.css:585`
  (fixtures regenerate), `tests/test_check_prose_units.py:159`,
  `backlog/ideas-prd.md:587,602`, and the 2026-08-19 spec's filename cite;
  `releases/evidence/0.1.519.json` is left (evidence is history) with a
  CHANGELOG note; `assets tracked` guard fails on a `SOURCES.md` row whose
  file is not in `git ls-files`.
- red run: a manifest row for an absent file.
- tests: guard test.
- ledger: none.

## Step 13 · AGENTS.md and claim_sweep

- change: AGENTS.md returns to load order + six red lines + version +
  capability tier, citing `references/` for everything it currently restates
  (target: at or below its 0.1.456 length, measured by the guard below, not
  by a number in prose); `claim_sweep.py` extended to scan `AGENTS.md` and
  `prompts/lumi-style-core.md` for counted claims and to report, never fail
  (its contract). New guard `entry restatement ceiling`: AGENTS.md may not
  exceed the line count recorded in `check_repo.py` beside the guard.
- red run: add twenty lines to AGENTS.md.
- ledger: **closes GAP «AGENTS.md grew against D1»**.

## Step 14 · process, then the PR

- change: CLAUDE.md convention 19 (a release reaches `main` only through a
  PR; merge, never squash); `check_evidence.py --init` obliges a
  `branch-protection` record whose command is `gh api
  repos/:owner/:repo/branches/main/protection` and whose digest must show
  `required_pull_request_reviews` present — an operator step.
- then: `gh pr create`, `bash scripts/ops/ci_wait.sh <PR>`, merge with
  `--merge --subject "<newest version> — …"` read against the CHANGELOG first.

## Operator steps (hers, recorded through the evidence gate, never typed)

| step | what | unblocks |
|---|---|---|
| D1 answer | logo provenance or removal | Step 0 |
| D3 answer | A1 ruling | Step 11 |
| six matrix runs | `run_conformance.py run --drive --model … --effort …` ×6 | K1, `ledger.py --board` |
| branch protection | "require a pull request" on `main` | Step 14 evidence |
| score D18 | the Chengdu BP sheet | agreement study row 4 |

## Order and dependencies

0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14.
Steps 1–5 are independent of each other and could be reordered; 6 cites ids
that 8, 9, 13 close, so it lands before them; 10 depends on 9 (the scaffold
embeds recoloured shapes only); 14 is last by definition.

## Verification at each step

`python3 scripts/ops/release.py --version X --spec specs/2026-08-20-audit-remediation-design.md`
— preflight runs the whole of `ci.yml`; the new guard's red run is recorded in
that step's CHANGELOG entry before the green commit; `python3
scripts/check/claim_sweep.py` is read for every count touched. After Step 8,
`python3 scripts/ops/ledger.py` must show at least one trace with a
tool-written `phase_seconds`.
