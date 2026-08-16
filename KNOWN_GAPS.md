# Known gaps

The queryable ledger of known defects and unclosed verification gaps in this
package. One entry per gap, machine-checked by `check_repo.py`'s ledger guard:
ids unique, statuses legal (`open | fixed | declined`), `fixed` entries name
the closing release (whose CHANGELOG entry must cite the id), `declined`
entries carry a reason. Deferred work goes to `backlog/ideas-prd.md`
(IDEA-ids); recurring failure *shapes* go to `FAILURE_MODES.md` (FM-ids);
this file holds concrete, current gaps.

Tracked bugs live here, not in code comments — a `TODO` in a script citing a
GAP id fails CI. (The lumi project's KNOWN_GAPS rule, adopted 0.1.422.)

## GAP-001 · T1-deck fails on both scored conformance agents

- status: fixed
- opened: 0.1.422
- closed: 0.1.434
- surface: conformance/CONFORMANCE.md, references/storyline-templates.md,
  scripts/check/check_prose.py, tokens/lumi-layouts.css (historical)
- symptom: both agents ever scored (Claude Code, Cursor) fail the T1-deck
  task. DIAGNOSED at 0.1.433 by reproducing every verdict: the dominant
  failure (collision, both agents) was the skill's own window-keyed media
  block in tokens/lumi-layouts.css — both decks copied it verbatim — removed
  at 0.1.380, AFTER the decks were built; the instruments that see it
  (0.1.368/0.1.385/0.1.390) also postdate the builds. Two live skill defects
  found and fixed at 0.1.433: the [TO FILL] template-vs-D14 contradiction
  and M6 counting enumeration labels as ranges. The five remaining findings
  are agent-capability (unfit title reserves, inline role overrides, an
  overfull closing page shipped against the agent's own screenshot, a
  1-unit descender clip, one unsourced page).
- check: EXECUTED 2026-08-13 — T1 re-run on both agents against the 0.1.433
  rules: Cursor hand-driven by the operator (pass), Claude Code driven clean
  with the skill (pass; T2/T3 also pass). Scored with run_conformance.py,
  recorded via report --record (history rows pin skill 0.1.433); the
  scoreboard renders the current-skill runs and names the superseded ones.

## GAP-006 · Rules whose only home is outside references/, and a subset claim that is false

- status: open
- opened: 0.1.456
- surface: SKILL.md, AGENTS.md, prompts/lumi-style-core.md, tokens/lumi-layouts.css,
  tokens/region-palette.css, assets/brand/README.md, CLAUDE.md
- symptom: a full sweep found whole rule families stated nowhere in
  references/ — the entire debug-mode contract (references/ contains no
  occurrence of "debug"), the parallel-build protocol including the merge gate,
  the questions-come-once rule, the colophon-placement rule, the
  scaffold-never-fixture rule, the world-figure generation rule, the
  capability-tier rule that an agent unable to run the checks may not call a
  deliverable verified, and the whole globe/map figure grammar living as
  comments in region-palette.css. CLAUDE.md's architecture section calls
  prompts/lumi-style-core.md "a strict subset of references/", and with
  core-only rules on record (never name a region by its colour in prose;
  the prompt-tier debug degradation format) that claim is false today.
- check: each family either moves into a reference file with the entry points
  restating it, or the architecture statement is amended to name entry-point
  rules as a legitimate second home. Either is a decision; the current state is
  neither. The generated references/eval-inventory.md covers the NUMERIC half
  of this gap already — the remaining half is prose rules.

## GAP-009 · The shape library's relation classification is a third unclassified

- status: open
- opened: 0.1.473
- surface: assets/shapes/tags.json
- symptom: the library is complete — all 206 units ship — but **70 of them carry
  `relation_from: unclassified`**: the extraction tagged 68, the template's own
  page names named another 68, and the rest is neither. They are usable and a
  person can look at the preview; what they lack is the machine-readable
  relation that makes "choose by the relation the content has" checkable.
- history, because it is the point: this entry was closed at 0.1.475 with a
  curated 68 of 206, on the rule that a shape enters only if its relation serves
  the chart rules. **That curation was wrong twice over.** The relation tags are
  sparse rather than authoritative, so it dropped the `flow-2`…`flow-6` and
  `cycle-2`…`cycle-8` families — one relation at several arities, which is the
  most useful thing a shape library holds. And the exclusions were made from
  page names: of the two checked against the rendered preview, **both were
  wrong** — `box` is a 2×2 grid with a four-arrow cycle and `surround` is a
  large directional arrow, neither a text box. Reopened, and the library is now
  complete: an absent shape cannot be chosen, an unclassified one merely carries
  no recommendation.
- check: classify the remaining 70 by looking at their previews, which is the
  step whose absence produced both wrong curations. Convention 15 named it
  before this happened; the previews were rendered and never opened.

## GAP-008 · P-1 is stated wider than anything checks it

- status: open
- opened: 0.1.460
- surface: references/design-rules.md §1-§2, scripts/check/check_design.py
- symptom: P-1 says the brand pack is the single source of visual and verbal
  identity and a deliverable does not improvise. What is actually held: the
  palette (D20 gate, D4, D13, D1, token parity) and the region hues. Typography
  and layout are only partly covered — **an agent inventing a seventeenth page
  layout is caught by nothing**, and `check_design.py` has no font-count check
  at all (verified in code, not assumed). The clause is not wrong; the wording
  of a principle should be wider than the checks of the day. It is recorded so
  the gap is not read as coverage.
- check: a layout-vocabulary check that grades a page's structure against the
  layouts `tokens/` defines rather than against class names invented by whatever
  document a probe was written against, plus the font-count check C7-④ names.
  Neither is built. Until they are, P-1's landing table entry in the refactor
  spec is the honest statement of what holds.

## GAP-007 · The reference files read as accretion, not as documents

- status: open
- opened: 0.1.456
- surface: references/design-rules.md, references/storyline-templates.md,
  references/eval-rubric.md
- symptom: the owner read the rule set end to end and said a person cannot
  form a correct judgement from it, and the skeletons agree with her:
  design-rules' section order is 1, 1c, 1d, 2, 3, 4, 4b, 5, 7, 6 — section 6
  is physically after section 7 — and its §4 numbers rules 1-5, 6, 7, 7b, 7c,
  7d, 7e, 8, 8b; storyline-templates wedges its shared apparatus between
  Template 1 and Template 2; eval-rubric describes three gating surfaces in
  three places with three vocabularies. The cause is structural: convention 2
  admits rules only from per-defect retrospectives, so every rule lands as a
  patch at the site of its wound, and no structural release has ever run.
- check: a structural release that reorders without rewording — content-frozen,
  diffable as pure moves, with the parity guards as the safety net — and a
  re-flow of every §-citation that the reordering breaks (SKILL.md and the
  checkers cite sections by number). Not begun; recorded so the next reader of
  these files knows the disorder is known, measured, and scheduled rather than
  invisible.

## GAP-004 · The Evals thresholds are gameable and calibrated on two documents

- status: open
- opened: 0.1.455
- surface: evals/thresholds.json, scripts/ops/eval_corpus.py
- symptom: a red-team pass cleared all four bars on the rejected corpus
  document with two mechanical rewrites that add no content — every `<li>`
  re-tagged as `.vows` markup, and one decorative rect-only SVG per prose page.
  The two metrics that saw it (`rect_only_share` 0.667, `shape_kinds_min` 1)
  had been demoted to reported for not separating a two-document corpus.
  Separately: the sales column is calibrated from a REJECTED document only —
  there is no accepted sales document — so those cells say where a bar could
  sit, not where it should. The bars therefore report and do not gate.
- check: the agreement study. Score the deliverables already on the operator's
  machine against the owner's recorded H1-H6 review scores and publish the
  correlation per threshold. A bar that does not track her judgement across ten
  documents is not measuring what she measures, however cleanly it separates
  two. `references/eval-rubric.md`'s own promotion rule asks for the same
  thing: two releases of real documents read against a metric before it gates.

## GAP-005 · Three of the owner's four deliverable categories have no accepted reference

- status: open
- opened: 0.1.455
- surface: evals/thresholds.json, references/storyline-templates.md
- symptom: only `training` has a document on record as meeting the product
  requirement. `sales` has a rejected one; `consulting` has none outside
  synthetic conformance decks; **product introduction has no genre at all** —
  the phrase appears nowhere in SKILL.md, references/ or scripts/, and the
  nearest fit (`marketing`) has no skeleton and cannot be scaffolded. Nine of
  twenty threshold cells therefore read `provisional`, and `internal`'s figure
  floor is `declined` outright because the only real internal document argues
  in prose and clears every gate.
- check: an accepted document per category, or a recorded decision that a
  category maps onto an existing genre. Until then the provisional cells are
  reasoned, not measured, and the file says so per cell.

## GAP-003 · The conformance history's producer path has no automated test

- status: fixed
- opened: 0.1.431
- closed: 0.1.433
- surface: scripts/ops/run_conformance.py (report --record)
- symptom: conformance_fresh() is tested against hand-written rows, but
  nothing tests that `report --record` produces rows of that shape — the
  agent/task key split, the digest pinning, the idempotency claim. A
  one-sided producer/consumer contract is FM-07's shape. Mitigations that
  keep this a 5-not-an-8: `validate` schema-checks the history in CI, and a
  malformed or under-grouped row reads as stale (fail-closed).
- check: python3 -m pytest tests/test_record_producer.py — drives the real
  main() against a synthetic ROOT (stubbed registry, task, run dir); closing
  it found one defect: a corrupt scores.json crashed the report merge loop
  with a traceback before the --record block's own does-not-parse guard could
  fire, so that guard was unreachable (fixed with the test)

## GAP-002 · Five checks CI cannot run are verified by prose

- status: fixed
- opened: 0.1.422
- closed: 0.1.425
- surface: scripts/check/inspect_layout.py, scripts/check/check_prose.py,
  scripts/check/check_design.py, scripts/check/check_globe.py, scripts/ops/run_conformance.py
- symptom: the layout gates, full-deliverable prose/design modes, the globe's
  JS half and conformance runs need a browser or an operator; their results
  were recorded as sentences in release notes — claims, not evidence. 0.1.415
  reported "all gates green" on eight of seventeen.
- check: python3 scripts/check/check_evidence.py --check (red in CI since 0.1.425:
  an operator check is a recorded execution with a digest, or the release
  does not ship)
