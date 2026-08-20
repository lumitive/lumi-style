# Audit remediation · design

Date 2026-08-20 · Status: **proposed, awaiting the owner's go** · Companion: `2026-08-20-audit-remediation-plan.md`

## The complaint

The post-merge audit of the 0.1.456 → 0.1.522 refactor (owner's copy lives
outside the repo, under the review directory, dated 2026-08-20) found the
structure track over-delivered and the product promise under-delivered, with
a specific defect list. The owner's instruction is to fix **all** of it. This
record decides how, and what "fixed" means for each class, before any code
moves.

## What the audit established (not re-argued here)

Eleven findings classes, each verified by re-running the command on 2026-08-20:

1. Instruments that will fail or mislead: `trace.py --phase` stores strings
   that `ledger.py` sums; `inspect_layout.py`'s aspect probe reads a loop
   leftover and reports every landscape deck off-shape; `D26` decides
   "missing" by substring and never surfaces it.
2. Two credential pattern tables, neither a superset, no parity.
3. Prose drift inside files the refactor created: `eval-rubric.md` lists D23
   and D27 as shipped and describes them as unbuilt; `design-rules.md:622`
   promises a split that P0.5 already shipped; `GAP-005` describes a state
   three releases stale; `CONFORMANCE.md`'s hand-written half narrates
   0.1.454 under a 0.1.522 table; `review_scores.py` still says H1–H6.
4. Nine shortfalls against the design with no ledger entry, in a design that
   said "every shortfall goes to KNOWN_GAPS".
5. The cost instrument (T1) has zero readings; the model×effort matrix has
   zero cells; no trace was opened for the last fourteen builds.
6. Evidence loss: eight of fifteen corpus entries point at deleted files,
   including both documents that carry human scores; the accepted anchor A1
   fails a current gate.
7. Knowledge that does not reach the build: 208 vendored shapes used 0 times
   in five deliverables; the exemplar notes are loaded by no entry point.
8. The prompt tier is a subset with no parity guard: number-first rule,
   six of eight storylines, eighteen banned phrases, and the unconditional
   "may not call a deliverable verified" are absent.
9. Boundary gaps: the `--terms` list has no canonical location and no
   `.gitignore` net; "Chengdu" reached eight tracked files through a CSS
   comment; three owner-supplied logos entered `SOURCES.md` with no licence,
   and the manifests describe 37 files that are not in git.
10. Four private copies of strip-tags/unescape where `scripts/lib/markup.py`
    exists; two copies of the CJK-space rule in the uncommitted batch.
11. Process: 66 releases pushed linearly to `main` with no PR; one release
    without its own commit; a held, uncommitted post-0.1.522 batch.

## The decision

**One branch, one PR, many release commits, merged (never squashed).** Each
release is one coherent change with its own CHANGELOG entry, deliberate-red
run, and tests, exactly as CLAUDE.md conventions 3 and 11 require — the audit's
own finding 11 is that the refactor skipped the branch-and-PR half of that
rule, so the remediation does not.

Three principles decide the shape of each fix:

**a. Fix the mechanism, not the instance, wherever a second instance is
plausible.** The credential tables get one shared module and a parity guard,
not a hand-sync. The rubric contradiction gets a `rubric self-consistency`
guard, not an edit. The four markup copies get one function and a `no shadow
markup` guard. The prompt tier gets a `prompt parity` guard. A drift fixed by
editing prose is the drift class this repository has fixed twenty-six times.

**b. What cannot be built in this pass is ledgered, and the ledger entry says
what would close it.** Nine shortfalls were silent; after this pass none is.
Where the honest answer is "the design's item was re-decided", the ledger
entry records the re-decision and the reason, so it is a decision and not a
quarterly re-debate (convention 10).

**c. Evidence that was lost is not fabricated.** D15/D16 cannot be
re-measured. The fix is a rule and a guard that stop it happening again (a
scored corpus id's file must exist, or be recorded as archived with its
digest), plus a new scored document — not a back-filled measurement.

## Per-class resolution

| # | Class | Resolution | Proof it can go red |
|---|---|---|---|
| 1 | Broken instruments | `--phase` parses a number and the schema types the value; the aspect probe receives the declared stage from `deliverable_registry.STAGE_OF`; D26's `missing` becomes a **reported** row that reaches `check_deliverable`'s block; its matching reads `TYPICAL_SECTIONS` against section ids **and** the `data-omitted` declaration, never titles (C5's own warning) | a trace closed with `--phase build 12` then summed; a correct 16:9 fixture reporting 0/N off-shape; a pitch-deck fixture with five undeclared sections surfacing them |
| 2 | Credential tables | `scripts/lib/secret_patterns.py` is the one table; both checkers import it; `secret patterns parity` guard fails if either file defines a pattern literal of its own | a planted private literal in `check_privacy.py` |
| 3 | Prose drift | edits **plus** a `rubric self-consistency` guard (a metric id listed in the M/D table may not be described elsewhere in the same file as "not built", "checked by nothing", "no … check"); `run_conformance.py report` writes the date into the header and regenerates the prose summary from `scores.json`, so there is no hand-written half to rot | plant "there is no D23 check" beside the D23 row |
| 4 | Unledgered shortfalls | GAP entries for: T1 zero readings (closed by class 5 in the same branch, so it opens and closes with a trail), privacy layer 3 ≠ designed T3, `check_outline` 3/13, recolour tool outside the repo, AGENTS.md growth, D2 cleanup, `feedback` field dropped; `marketing` retirement → IDEA; DR-6 split → fixed directly; GAP-005 reworded | the ledger guard already fails on a dangling cite; each new id is cited from CHANGELOG |
| 5 | T1 / traces / matrix | `trace.py` gains `phase start <name>` / `phase stop <name>` that stamp wall-clock themselves (a typed seconds count is a typed verdict, same reasoning as `--usage`); `new_deck.py --outline` opens the trace and stamps `outline`; `check_deliverable.py` stamps `checks`, and reports `unmeasured` when run without a trace id — so a build without a trace is visible, not silent; `run_conformance.py run --drive` passes `--model/--effort` through and records them, which is how the six matrix cells get real runs | a build with no `--trace` reads `unmeasured` in the verdict block; a drive with `--effort low` lands `effort: low` in its trace |
| 6 | Evidence loss | `review_scores.py --check` requires every scored `corpus_id` to resolve to a file or to an `archived: {sha256, pages}` record; `operating-rules.md` gains the sentence "a scored document is never deleted"; the Chengdu BP becomes corpus D18 with a generated scoring sheet for the owner; A1 is recorded in `thresholds.json` as `accepted_under: 0.1.449, shippable_under_current_gates: false` with a KNOWN_GAPS entry — re-baselining is the owner's call (decision D3 below) | a scores record citing an id with no file and no archive fails `--check` |
| 7 | Inert knowledge | `new_deck.py --outline` maps each section's declared `analysis:` move → `frameworks.json` → shape family and emits the chosen shape's `<use>` on that figure page (the slot is real markup, so D19 holds it); `check_design.py` gains **D31 shape-library use** (reported, never gating: count of library shapes referenced per figure page); `SKILL.md` and `AGENTS.md` load `references/exemplars/` at the analysis beat, which is the one place the ten devices can act; the recolour tool is ported to `scripts/build/recolor_shapes.py` with the un-recoloured originals vendored beside it and `--check` in CI | a scaffold built from an outline with five `compare` moves carries five shape slots; recolour `--check` fails on one edited byte |
| 8 | Prompt tier | a `prompt parity` guard holds `prompts/lumi-style-core.md` to: every `STORYLINES` name, every `check_prose.BANNED` phrase (or a `NOT_IN_PROMPT` waiver with reason), the number-first sentence verbatim, and the unconditional capability-tier sentence; that sentence's home moves to `references/operating-rules.md` and `platforms.json` cites it | delete one storyline name from the prompt |
| 9 | Boundary | canonical location `~/.lumi/terms/` documented in operating-rules, SKILL, AGENTS; `.gitignore` nets `*.terms.txt` and `terms-oob*`; `check_privacy.py` strips `data:` URIs and `@font-face` base64 before matching (closes IDEA-15); "Chengdu" replaced by neutral provenance wording in the CSS comment (fixtures regenerate), the test, the backlog, the spec, and the evidence file is left as history with a note; the secrets guard **also** runs the operator's terms list over tracked files when the list exists locally (absent in CI, reported as not attempted); the three logos either get provenance from the owner (decision D1) or leave the manifest and the deck sets their names in type; the 37 untracked assets are added with the manifest; `assets tracked` guard extended to fail on a manifest row whose file is not in `git ls-files` | manifest row for a file not in the index |
| 10 | Private copies | `markup.visible_text()` and `markup.join_cjk()`; `no shadow markup` guard forbids a private `re.sub(r"<[^>]+>"` outside `markup.py` | plant one |
| 11 | Process | CLAUDE.md convention 19: a release reaches `main` only through a PR; the operator step is GitHub branch protection "require a pull request before merging" (recorded through the evidence gate, not as a sentence); the held post-0.1.522 batch ships as the branch's first release **only if the owner lifts the hold** (decision D0) | — |

## Explicitly out of scope

- **Everything in the 2026-08-20 Chinese-output diagnosis** (A/B/C lists, CJK
  typography tokens, the zh outline language). The owner froze it pending her
  team's verdict; nothing here touches `:lang(zh)`, `--ls-title-cjk`, the
  measure, or the translation chain. The one audit addition — M13 reads
  differently on the zh twin — is ledgered as an IDEA, not fixed.
- Rebuilding any deliverable. The remediation changes instruments and rules;
  the next real build exercises them.
- Retiring `marketing` or `.field`. Both are recorded (IDEA for `marketing`,
  decision D5 for `.field`) because retiring a genre or a brand device is not
  a remediation, it is a product decision.

## Decisions the owner must make before or during the branch

| id | question | default if she says "your call" |
|---|---|---|
| D0 | Lift the hold on the uncommitted post-0.1.522 batch so it ships as the first release? | ship it (it is green and self-contained) |
| D1 | Provenance for `cowork.png`, `hermas.png`, `workbuddy.png`: source URL, date, and usage basis? | remove from manifest and tree; set the names in type |
| D2 | Is the Chengdu BP to be scored (corpus D18) in this cycle? | generate the sheet; scoring is hers, not blocking |
| D3 | A1 fails D27: keep as calibration-only (documented) or re-baseline on a rebuilt, re-accepted document? | calibration-only, ledgered |
| D4 | Run the six matrix cells (Opus/Sonnet × low/medium/high) — needs her machine time and the two CLIs | wire it; runs are an operator step recorded through evidence |
| D5 | `.field` device: keep, scaffold it, or retire? | keep and scaffold it on the thesis page; retirement is hers |

## Rejected

- **Fixing the prose drift by editing alone.** Rejected for the reason the
  audit gave: the refactor's own flagship file drifted within four days of
  being written; an edit without a guard is the next instance.
- **Making D26's `missing` gate.** Rejected; C5 is report-only by a decision
  with five regulatory precedents behind it. Surfacing is the fix.
- **Gating on trace presence.** Rejected; a build without a trace is reported
  `unmeasured`, which is the established "did not run ≠ ok" shape. A gate
  would teach authors to open empty traces.
- **Back-filling D15/D16 from contact sheets.** Rejected; a measurement of a
  screenshot is not a measurement of the document, and the scores file says
  so about schema-1 records already.
- **A blanket "no place names" guard.** Rejected; the deny list is the right
  instrument and it already exists — the fix is to point the repo guard at it.

## Acceptance test

The branch is done when: `scripts/preflight.py` is green on every release
commit; every new guard and check has a recorded deliberate-red run in its
CHANGELOG entry and a failing synthetic test; `ledger.py` shows ≥1 trace with
non-empty `phase_seconds` produced by the tooling rather than typed; the
audit's §10-A list is empty and every §10-B item is either done or carries the
owner's recorded decision; and the PR is merged with a merge commit whose
subject is the newest version.
