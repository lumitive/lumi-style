# Ideas PRD — where lumi-style gets stronger next

> Status: a backlog, not a commitment. Nothing here is scheduled, and nothing
> here is a rule. Each item states a problem, the evidence for it, what "done"
> would look like, and what could go wrong on the way — enough for someone to
> pick one up and argue with it before writing code.
>
> Source: a survey of the package at 0.1.385, prompted by the owner's question
> after the output-directory and portrait-figure work. (Repository language:
> English only — red line.)

## How to read this

Every item is written the same way, because the failure mode this package has
recorded most often is a fix that became its own defect. `CLAUDE.md` maintenance
rule 4 exists because three regressions came from a number whose direction was
never stated; the page-fill floor was withdrawn in 0.1.340 because it could be
satisfied without improving a page. So each item carries a **risks** section that
names how it could go the same way, and an **acceptance** section written as
something a machine or a reader can check rather than as an intention.

Two items — the genre-validation fix and the `--deliverable` help text — were
small enough to land with the release that produced this survey, and are recorded
at the end rather than proposed here.

## The list, ranked

| id | Item | Why it ranks here | Effort |
|---|---|---|---|
| IDEA-1 | Implement M1, M2 and M6 | Three unmeasured metrics stand behind a *fact* red line, which the rules say outranks every style rule | Medium |
| IDEA-2 | Make Chinese a supported output path | Every English rule has machine backing; no Chinese rule does, for a team that writes Chinese | Large |
| IDEA-3 | Assert the rendered gates on the fixtures | Nine gates and thirteen design metrics have no failing case in CI | Medium |
| IDEA-4 | Store the reader scores | The iteration engine keeps no data; the human half is anecdote | Small |
| IDEA-5 | Run the two unused viewports by default | §7 requires two checks that never run unless asked for by hand | Small |
| IDEA-6 | Fill or retire the `files` capability tier | A tier defined, restated in three places, and used by nothing | Small |
| IDEA-7 | Make the conformance board mean something | One agent of twelve, n=1, and an unscored run on disk | Medium |

Items IDEA-1 and IDEA-2 are the structural gaps. Items 3 to 7 are hygiene, and 3 is the one
that protects everything else.

---

## Status at 0.1.422 (the restoration)

This file was deleted in `e861df0` leaving only the rendered HTML deck; it is
restored here as the queryable backlog, with stable ids the ledgers and the
CHANGELOG can cite. The first restoration carried the 0.1.385 survey's
open/closed state without re-verifying, and item-by-item verification then
found most of the survey absorbed by later releases — the corrected record:

- **IDEA-1 shipped** (0.1.390, commit `0145bfb`) — M1, M2 and M6 are computed
  and graded in `scripts/check/check_prose.py`; the conformance runs record their
  verdicts.
- **IDEA-2 OPEN** — the only survivor. Chinese as a supported output path;
  Large; the render fixture was blocked on a font licence at the 0.1.390
  deferral.
- **IDEA-3 shipped** — 0.1.390's fixture coverage work is exactly this item
  (34/34 graded verdicts have a failing fixture today).
- **IDEA-4 shipped** — `reviews/scores.json` + `scripts/ops/review_scores.py`
  exist and gate in CI.
- **IDEA-5 shipped** (0.1.390, same commit) — all five geometries are in
  `DEFAULT_GEOMETRIES` and the report prints which ran and which were
  skipped, the item's acceptance verbatim.
- **IDEA-6 resolved** — the registry's `files` tier carries a
  `population_note` that IS this item's written-waiver acceptance branch: the
  tier describes a real class (an agent that reads files and cannot execute),
  no platform is claimed onto it without an exercised run, and the note
  records why it is empty (capability claims were unverified until
  `capability_verified` arrived; only claude-code is confirmed `full`).
- **IDEA-8 shipped** (0.1.435) — score entries and history rows carry
  `instrument_version` and the colophon `built_version`; `cell_spread`
  renders build-aligned conflicts as the skill changing, latest build
  governing.
- **IDEA-7 shipped** (0.1.427) — `conformance/history.json`, `report
  --record`, and the evidence gate's freshness obligation are this item's
  acceptance in different words.
- **IDEA-23 resolved** (0.1.657) — the 13 uncontrolled dependencies were ruled
  (`specs/2026-08-30-dependency-rulings-design.md`): 11 are *material* (absent →
  degrade to in-repo or fail loud), 1 is already in-repo (the vendored asset
  source), and 1 (the out-of-bounds list) cannot be controlled — client names
  cannot ship — so it is made loud instead. None needs bringing in-repo. The
  rule the census earned is `OR-8c`: an uncontrolled dependency degrades or fails
  loudly, never silently. The single place not yet met is the operator trace
  store diverging unseen, which stays open as GAP-049.

## IDEA-1 · Implement M1, M2 and M6

**Problem.** Six of the twelve M-metrics have no code behind them. Three of the
six carry rules the package itself calls non-negotiable.

**Evidence.**

- `scripts/check/check_prose.py` computes M4, M8 (two halves), M9, M10, M11 and M12.
  M1, M2, M3, M5, M6 and M7 appear in the rubric table and nowhere else.
- [`../references/eval-rubric.md`](../references/eval-rubric.md) heads that table
  "scriptable; spot-check manually when no script". The parenthesis is carrying
  the whole gap.
- **M1** (assertive-title rate, target ≥70%) is the only measurement behind the
  title contract's demand that every title carry a verifiable fact. The rubric
  says in the same file that M1 "is never skipped", and the changelog records a
  release whose deck titles collapsed to bare antitheses precisely because
  nothing measured them.
- **M2** (number-sourcing rate, ≥90%) and **M6** (unsourced range figures, =0)
  stand behind `writing-rules.md` §7, which the file itself says outranks every
  style rule: every number carries its source, and a range figure without one may
  not appear. A deliverable can break both today and pass every check.
- M6 is closest to free: `NUMERIC_RANGE` already exists in `check_prose.py` and is
  used only to *exempt* ranges from the dash rule.

**Proposal.** Implement the three that back the fact red line, in this order:
M6, M2, M1. Leave M3, M5 and M7 out of scope here — M3 and M7 are terminology
consistency and belong with item 2, and M5 is Chinese punctuation, which is item
2 outright.

- **M6** — a range-shaped number with no source marker within its block. The
  predicate is nearly written already.
- **M2** — the share of percentage and currency figures with a source marker
  nearby. Report the share and the unsourced list; a number the author can see is
  worth more than a verdict.
- **M1** — the share of titles that name a subject and carry a verifiable fact.
  This is the hard one and the reason it is third. "Verifiable fact" is not
  decidable in general; a workable proxy is *a title containing a numeral, a
  named entity, or a dated term*, reported with the failing titles listed so a
  reader can overrule it.

**Acceptance.**

- Each metric appears in `check_prose.py`'s grade table with a target, and in
  `fixtures/expected.json` for both fixtures.
- Each has a **failing case planted in `deck-broken`**. A metric asserted `ok` on
  both fixtures cannot tell a working checker from one rewritten to return `ok`.
- M6 fails (non-zero exit) like M4; M2 has never gated. M1 reports rather than gates until it
  has been read against real documents for two releases, because a title
  heuristic that fires on good titles is a line reviewers learn to skip.

**Risks.**

- **M1 is a judgment dressed as a number.** If it gates, authors will write
  titles that satisfy the regex. That is the same shape as the withdrawn page-fill
  floor. Ship it reported, with the failing titles printed, and promote it only if
  a review shows it caught something a person missed.
- **M2 depends on what "nearby" means.** Too wide and every number passes; too
  narrow and a figure sourced in the preceding sentence fails. Define the window
  in the same block, state it in the rubric, and print the misses.
- Adding a metric adds a copy of a rule. `check_ban_list_parity` exists because
  §2 and the checker drifted; whatever M2 counts as a source marker has to be
  stated in `writing-rules.md` §4 and held to it.

**Effort.** M6 small, M2 medium, M1 medium. Each is independently shippable.

---

## IDEA-2 · Make Chinese a supported output path

**Problem.** The rules cover Chinese output thoroughly. The machinery does not
cover it at all. Chinese exists in this package as something to detect and
exclude, not as something to produce well.

**Evidence.**

- `scripts/check/check_prose.py` states in its own docstring that it handles English
  deliverables only, and that Chinese is governed by the de-translationese pass in
  the rules.
- [`../references/writing-rules.md`](../references/writing-rules.md) ships a
  Chinese banned-phrase list, a Chinese punctuation section, a coined-term red
  line and a de-translationese pass. **None of them has a machine counterpart**,
  and `check_ban_list_parity` covers the English list only — so the Chinese list
  can drift without anything noticing.
- There is no Chinese fixture. Both tracked fixtures are English.
- **No CJK face ships.** `tokens/lumi-theme.css` falls back to system Chinese
  fonts, which no integrity guard covers, while the rules require the display
  face to be embedded rather than linked. This is the pattern `CLAUDE.md`
  maintenance rule 5 names: a rule may not mandate an asset the package does not
  ship.
- The only Chinese string CI touches is the negative case that makes M12 fail.

**Proposal.** Three phases, each shippable alone.

1. **Parity first.** Extend the ban-list guard to the Chinese list, with the same
   `NOT_MECHANIZED` discipline: every phrase the rules ban is either a pattern or
   a documented exemption. This closes the drift channel before any new code
   exists to drift.
2. **A Chinese checker path.** M5 (punctuation) and M3/M7 (term consistency) are
   the mechanizable ones; the de-translationese pass is not, and should be
   recorded as not mechanized rather than half-implemented. Segmentation for
   sentence rhythm does not transfer from English and should be scoped out until
   there is a reason.
3. **A Chinese fixture pair**, built the same way the English pair is, so the
   Chinese metrics have a failing case.

Font: either vendor a CJK face with a license that permits embedding, or state
plainly in the rules that Chinese deliverables fall back to system faces and what
that costs. Both are honest; silence is not.

**Acceptance.**

- The Chinese ban list and its checker are held together by a guard that fails on
  divergence.
- A Chinese fixture exists, and every Chinese metric has a verdict on both
  fixtures with at least one that flips.
- `references/design-rules.md` states the font position explicitly, whichever way
  it goes.

**Risks.**

- **Scope.** This is the largest item here and the easiest to half-finish. Phase 1
  is worth doing even if 2 and 3 never happen, because it stops the rules and the
  machine from separating further.
- **Font licensing is the blocker, not the code.** The Latin face is embeddable
  under its license; a CJK face of comparable quality may not be, and a Chinese
  font is one to two orders of magnitude larger than the Latin pair, which changes
  the size of every deliverable that embeds it. Decide the license question before
  building anything around it.
- Mechanizing punctuation across a language is where false positives live. Scope
  it to the cases the rules already state as absolute.

**Effort.** Phase 1 small. Phase 2 medium. Phase 3 medium. Font decision:
research, not engineering.

---

## IDEA-3 · Assert the rendered gates on the fixtures

**Problem.** The gates that decide whether a document may be delivered are not
themselves tested. A checker rewritten to return `ok` unconditionally would pass
CI.

**Evidence.**

- `scripts/check/check_fixtures.py` runs `check_prose.py` and `check_design.py` only.
  `inspect_layout.py` is absent, so **all nine `--deliverable` gates have zero
  assertions in CI**.
- Of the seventeen design verdicts, **thirteen are `ok` on both fixtures** — only
  four flip. Of the seven prose verdicts, four are `ok` on both.
- `fixtures/expected.json` says this about itself in its own comment: coverage is
  complete but not equally strong, several metrics pass a literal `True`, and both
  tier-1 callout metrics pass vacuously because neither fixture carries one.

**Proposal.** Two moves, in order.

1. **Plant a failing case for every metric that has none.** The two probes added
   in the release that produced this survey each got one, and the exercise took
   minutes per probe: the broken fixture gains a drawing whose label runs past its
   viewBox, a page with a tier-1 callout, a title set that trips M11, and so on.
2. **Bring `inspect_layout.py` into `check_fixtures.py`** behind an availability
   check, so it asserts the nine gates locally and skips loudly where Chromium is
   absent. It cannot run in CI — that is a stated posture, not an oversight — so
   the assertion belongs in the local suite with a clear "not run here" line.

**Acceptance.**

- Every emitted verdict has at least one fixture on which it fails.
- `check_fixtures.py` reports which gates it asserted and which it could not, and
  the count of unasserted gates is zero when Chromium is present.

**Risks.**

- **A fixture that carries every defect stops being readable as an example.** The
  broken fixture is also teaching material. Keep the defects one per page and
  labelled, or split into a third fixture whose only job is to fail.
- Adding assertions to a suite that currently passes will surface metrics that
  were quietly wrong. That is the point, and it should be expected rather than
  treated as breakage.

**Effort.** Medium, and it decomposes into one metric at a time.

---

## IDEA-4 · Store the reader scores

**Problem.** The H1–H6 loop is described as the package's iteration engine, and
it keeps no data. Every score in the record is prose inside a changelog entry.
Nobody can answer whether figure self-explanation has improved over ten releases.

**Evidence.**

- `../references/eval-rubric.md` defines six human dimensions with anchors and a
  protocol in which a divergence of two or more forces a retrospective.
- The repository contains no scores file, no schema, and no history. The
  conformance board stores mechanical verdicts only.
- The changelog carries individual scores as sentences, which is how the record of
  a reader scoring three dimensions at 1 survives — as an anecdote inside a
  release note.

**Proposal.** One small tracked file — a list of records, each with the release,
the document genre (never its name or client, per `CLAUDE.md` rule 9), the six
self-scores, the six reader scores, and the retrospective outcome. A short script
prints the series per dimension.

**Acceptance.**

- A tracked file with a stated schema, and at least the scores already recorded in
  the changelog backfilled into it.
- A command that prints each dimension over time.
- `check_repo.py` refuses a record that carries a client name or a document title.

**Risks.**

- **This is where engagement facts leak into the repository.** Red line 9 is the
  hardest rule in the package and a scores file is exactly the shape that breaks
  it. The guard is not optional, and the schema should have no free-text field
  that invites a name.
- A number series invites optimizing the number. These are reader scores, so the
  optimization is legitimate — but self-scores in the same file will drift upward
  unless the protocol's rule against self-scoring five before a reader stays
  visible in the tooling.

**Effort.** Small.

---

## IDEA-5 · Run the two unused viewports by default

**Problem.** The verification matrix requires two checks that never happen unless
someone types them.

**Evidence.**

- `scripts/check/inspect_layout.py` defines a `laptop` geometry at 1000×550 and a
  `16x9-hd` at 1920×1080, and its default geometry list contains neither.
- `../references/design-rules.md` §8 requires the short-laptop check by name and
  states what it catches: an overflowing page pushing its footer below the fold
  silently.

**Proposal.** Add both to the default list, or state in §7 that they are opt-in
and why. Prefer the first: the whole reason the off-geometry render exists is that
a defect invisible at the design size shows up at a shape nobody designed for, and
that argument applies to these two exactly as it applies to `wide`.

**Acceptance.** The default run covers every geometry §7 names, and the report
prints which geometries ran.

**Risks.** Two more renders per run is real time on a thirty-page document. If
that matters, make them default for `--deliverable` and optional otherwise, rather
than dropping them.

**Effort.** Small.

---

## IDEA-6 · Fill or retire the `files` capability tier

**Problem.** The package defines three capability tiers and uses two. The unused
one is `files` — reads the bundled rules, cannot execute — which is the shape of
most IDE integrations.

**Evidence.**

- `adapters/platforms.json` holds ten `full` records and two `prompt` records. No
  platform is on the `files` tier.
- The tier is defined in the registry and restated in `CLAUDE.md` and in the
  entry points, including the rule that an agent which cannot run the checks may
  not call a deliverable verified.

**Proposal.** Decide which it is. Either a real platform belongs on that tier —
in which case add the record, the loading note, and the verification wording it
implies — or the tier is aspirational and should say so. A third possibility
worth testing first: some of the ten `full` platforms may not actually execute
scripts in every mode, in which case the registry is optimistic rather than the
tier unused.

**Acceptance.** Either at least one registry record on the tier, or a written
waiver in the registry saying the tier is defined for a class of platform this
package does not yet claim.

**Risks.** Adding a platform without confirming its behavior is the failure the
platform-manifest guard already exists to prevent. One record already carries
three waivers because its discovery path could not be confirmed; do not add a
fourth by guessing.

**Effort.** Small, mostly verification rather than code.

---

## IDEA-8 · A score row pins its instruments

**Problem.** `task_hash` pins the question; nothing pins the ruler. The
GAP-001 diagnosis found all three archived decks were built against one
skill version and scored against a stricter later one (the deliverable gate
itself, `figure_clipped`, and the laptop matrix point all postdate the
builds), and rescoring them today accretes still-newer failures (D19).

**Proposal.** `run_conformance.py score` records the checker commit/skill
version at score time and the deck's colophon build version; the scoreboard
marks rows where build < instrument as answers to an older question.

**Acceptance.** A history row carries both versions, and CONFORMANCE.md
renders the mismatch visibly.

**Risks.** None structural; one more field in scores.json and history rows.

**Effort.** Small.

---

## IDEA-7 · Make the conformance board mean something

**Problem.** The cross-agent scoreboard reports one agent of twelve, one run each,
and has an unscored run sitting on disk that no table references.

**Evidence.**

- `conformance/CONFORMANCE.md` records one agent detected of twelve, n=1 per
  agent, two rows with results and ten reading "not installed".
- `conformance/results/` holds three run directories; one of them has no scores
  file and does not appear in the published table.
- Four platforms carry waivers stating the harness can never exercise them: an
  IDE with no CLI, and two API chat models.
- The harness docstring already states its own limits, including that it cannot
  show reproducibility because nothing repeats a run.

**Proposal.** Three parts, and the first is the cheapest honest improvement:

1. **Prune or score the orphan run.** A results directory that no table cites is
   a claim nobody made.
2. **Separate "not installed" from "cannot be exercised."** Ten rows read the
   same today, but four of them are structural and six are contingent on a
   machine. The table should distinguish them, because only six are ever
   actionable.
3. **Repeat a run.** The board's own note says a verdict can change without the
   artifact changing. Until a run repeats, every row is a single sample and the
   board cannot tell a flaky checker from a flaky agent.

**Acceptance.** No unreferenced results directory; a column or symbol separating
structural from contingent gaps; at least one agent with more than one run and the
variance recorded.

**Risks.** Repeating runs costs tokens and time and produces a number that will
be uncomfortable. That is the value. Do not report a mean without the spread.

---

## IDEA-10 · Four storylines have a name and no skeleton

**Problem.** `references/storyline-templates.md`'s roster names seven
storylines; only `training-curriculum` (Template 4) and `proposal` (Template 5)
carry a full narrative skeleton. The remaining four — `market-analysis`, `gtm`,
`status-report`, `due-diligence` — carry one line each saying
what shape of argument they are. That is enough to choose with, and it is not
enough to build from.

**Evidence.** 0.1.491 found that none of the six original storyline names
appeared anywhere in `references/` at all: the axis was a closed tuple in
`scripts/lib/deliverable_registry.py` with no prose behind it. The roster fixed
the readability half. The skeletons are the other half, and writing five at once
without a document to write each against is exactly the speculative rule-making
convention 2 forbids.

**Closed at 0.1.516 — all four, as Templates 7–10, by owner decision.** The
close condition above said one at a time from real documents, written to
prevent speculative invention; the analysis-engine retrospective found the
four structures were never speculative — the 2026-08 consulting-standards
research had already documented each one section by section (market analysis
7 sections with the TAM/SAM/SOM double-count; GTM's 6 decisions; the status
report's 8 elements with an ask per risk; due diligence with the red-flag
matrix), and the skeletons then sat in this backlog for four releases while
their research was already paid for. C5 reports and never gates, so a
section name the industry uses and a given document does not need costs a
reported line and a declared omission, not a gate. (`product-intro` closed
the one-at-a-time way at 0.1.513: Template 6, from the deck whose blind
review scored 1 on completeness precisely because the skeleton did not
exist.)

## IDEA-9 · The fixture's reserved domain doubles as a deliverable placeholder

**Problem.** `fixtures/deck-pass.en.html` carries `www.example.org` as its
footer site — deliberately, because fixtures ship no real fact — and a 34-page
deliverable shipped that same string to a reader, because its footers were
copied from the fixture and D12 accepts any domain-shaped token.

**Evidence.** The 0.1.442 owner review: every one of a 34-page deliverable's
footers read `www.example.org`. D14's scaffold-slot patterns (added in the same
retrospective) deliberately exclude it, because refusing the reserved domain
in deliverables while requiring it in fixtures needs a fixture-vocabulary
decision, not a regex.

**Proposal.** Either give the fixtures a marked synthetic site that D14 can
refuse in deliverables without a carve-out (e.g. move the "this is fixture
furniture" signal out of the string and into markup the fixture alone uses),
or decide the site slot stays with the reviewer and record it in
`check_design.py`'s NOT_MECHANIZED with this reasoning.

**Acceptance.** A deliverable carrying the fixture's site string fails a gate,
or the decision not to mechanize is recorded where ban-list parity looks.

---

## Not doing, and why

- **A third geometry.** Two fixed stages are already two compositions per subject.
  A third multiplies the authoring cost of every deliverable and no reader has
  asked for one.
- **A page-fill floor, in any form.** Withdrawn in 0.1.340 after it was satisfied
  by stretching table rows rather than by improving pages. Cell fill and empty
  band stay reported. This is the package's clearest precedent and it should stay
  a precedent.
- **An LLM judge in the conformance harness.** The recall task is scored by
  keyword regex on purpose. A model grading a model produces a number with no
  appeal.
- **Mechanizing the de-translationese pass.** It is judgment about register.
  Record it as not mechanized rather than approximating it.

## Sequencing

Item 3 protects every other item on this list, because a metric with no failing
case can be broken by the change that adds the next one. Item 1's first piece is
small and independent. Item 2's first phase is a guard, not a feature, and can
land beside anything.

A defensible order: **3.1 (plant the missing failing cases) → 1 (M6, then M2,
then M1) → 2.1 (Chinese ban-list parity) → 4 → 5 → 6 → 7**, with items 2.2 and
2.3 scheduled only after the font-license question has an answer.

## Landed with the survey

Two findings were small enough to fix in place rather than propose:

- **An unknown `data-genre` was graded as sales in silence.** The share probe
  accepted any word and validated it against nothing, so a misspelled genre scored
  a training handbook against the wrong target and printed a confident line about
  it. It now reports as not measured and names the vocabulary. The `internal`
  genre gained the share entry it had been falling through.
- **The `--deliverable` help text listed eight findings after a ninth shipped.**
  Fixed in the same release, and it is the reason item 3 ranks where it does: the
  help text is documentation, and nothing compares documentation to behavior.

## IDEA-11 · A promise conditional on a state, not on a version

`check_stale_promises` catches a note that names a release which has already
shipped. It cannot catch one that names a **condition**, and the rubric carried
two rows reading *"temporarily human → machine once the shape vocabulary
lands"* for twenty-four releases after the shape vocabulary landed. The
citation guard is structurally blind to this: there is no version to compare.

Two ways to close it, and the cheap one is not a guard:

1. **Require the conditional form to name a version.** A row saying
   "temporarily human → machine at 0.1.5xx" is checkable by the guard that
   already exists. This is a prose rule for `eval-rubric.md`'s conditional-item
   convention, costs nothing, and converts an invisible promise into a visible
   one by construction.
2. A phrase-trigger guard over "once … lands" and its cousins. Brittle by the
   same reasoning that declined AG-1: deciding what prose constitutes a promise
   is FM-01 in the making.

Recorded rather than built, because option 1 is a convention change and belongs
in a retrospective with a second instance behind it. The first instance is
fixed in 0.1.503, which stated the reason instead of the condition.

## IDEA-12 · Noun-pile enumeration as an AI tell

**Problem.** The first blind review flagged two agenda rows as machine-written
— "the tell every model ships, the one rule set behind three entry points, the
asset library, and the gates" — and the shape they share is a pile of noun
phrases joined by commas, no verb, no claim. M4's ban list cannot see it
(no phrase is banned; the STRUCTURE is the tell) and M10 counts triads, not
piles.

**Evidence.** One document, one reviewer, two instances on one page. The
two-document promotion rule says this is not yet a rule; the C1/C2 anchor
notes carry the examples so a second occurrence is recognized.

**What would close it.** A second document flagged for the same shape promotes
it: either a prose rule in writing-rules §5 (a list of nouns is a list, not a
sentence — give the row a verb) or, if a mechanical form emerges, an M-series
reported metric for verbless comma-runs above a length floor.

## IDEA-13 · `EXTERNAL_GENRES` is a third copy of the genre split, unguarded

**Problem.** `scripts/check/check_design.py` declares
`EXTERNAL_GENRES = ("sales", "marketing", "consulting")` as its own literal —
the gate on D28's `.take` coverage and the code-side reading of AR-5's "the
external genres". Its comment argues the non-import is deliberate (it answers
a different question than `DASH_BANNED`), but the absence of a *guard* is not
argued anywhere: `check_genre_vocabulary` reads seven files and this tuple is
in none of them. A future external genre added to the registry would silently
fall out of the takeaway discipline and the reader-outcome rule — the exact
silent-divergence class the genre-vocabulary guard was built for.

**Evidence.** Found during the 0.1.518 pitch-deck work while mapping every
place the genre vocabulary is keyed. No divergence has happened yet; the
current tuple equals the sales tier exactly.

**What would close it.** Add the tuple to `check_genre_vocabulary`'s read set
with the rule "every EXTERNAL_GENRES member is a GENRES member, and the tuple
equals the set of genres whose TIER is `sales` unless a comment names the
exception" — with the planted-red run convention 15 requires, run first.

## IDEA-14 · `check_outline.py` cannot read assertion in a Chinese title

**Problem.** `is_label` decides "asserts nothing" by an English verb list plus
an Arabic-digit test. A Chinese title asserting plainly (`本轮融资只解决一件事`) reads as a topic label unless it happens to carry an Arabic digit, and
the outline gate FAILs it.

**Evidence.** The 2026-08-19 roadshow outline: two zh titles
misjudged; both were worked around by inserting digits (`只解决 1 件事`),
which is compliance with the instrument, not the rule.

**What would close it.** A zh assertion heuristic (predicate-marker vocabulary
or a full-width-punctuation-aware fact test), designed against a corpus of
real zh outlines rather than invented — convention 15 applies: grep real
titles first, plant the red run first.

## IDEA-15 · Short Latin privacy terms false-positive on embedded base64

**Problem.** `check_privacy.py --terms` substring-matches case-insensitively
across the raw file, so a three-letter Latin term ("Ray") fires on base64
inside the embedded font (`...RayTh2...`), six times on one build.

**Evidence.** The 2026-08-19 roadshow build: all six layer-1 hits were base64;
the term had to be dropped from the out-of-bounds list to keep the check
usable, which weakens the check.

**What would close it.** Word boundaries for pure-Latin terms and a scan that
skips `data:` URIs and base64 runs — with a planted red proving a REAL name in
visible prose still fires.

**Closed at 0.1.526.** `check_privacy.term_text` blanks `data:` URIs and
base64 runs before the term scan (the credential scan keeps the whole file —
a JWT is base64 by construction), `term_pattern` gives a pure-Latin term word
boundaries and leaves a CJK term as a substring. Four tests planted red on
the 0.1.525 code: the font case, the boundary case, the real-name case and
the directory default.

## IDEA-16 · The `marketing` genre has no behaviour of its own

**Problem.** The two-axis split (0.1.465) found that no rule, threshold,
template or scaffold distinguishes `marketing` from `sales`: five genre names
produce four behaviours. `marketing` still owns a threshold column in
`evals/thresholds.json` (three cells, all `provisional`) and a place in every
genre vocabulary, so every genre-keyed table carries a row that can never
differ from its neighbour.

**Evidence.** The refactor design's §6.4 table: `M9_dashes` — `internal`
exempt, the other four identical; `VISUAL_SHARE_TARGET` — `training` 30, the
other four 50; the four threshold lines — identical for `sales` and
`marketing`; the scaffold — only `training` differs.

**What would close it.** A pure-rename release (GAP-007's discipline) that
retires `marketing` as a genre name and maps it onto `sales`, touching
`deliverable_registry.GENRES`, the threshold file, the scores history, the
conformance tasks, `new_deck --genre`, `check_prose --genre` and the `genre
vocabulary` guard together. Not before the three real tiers each have an
accepted reference: a rename while the cells are provisional moves numbers
that mean nothing yet.

## IDEA-17 · M13 reads a number conflict in the English twin that the Chinese twin does not

**Problem.** On one deliverable built in two languages from one plan,
`M13_quantity_conflicts` reported one conflict on the English file
(`lumivate part: 20m vs 900m`) and zero on the Chinese file. The two files
state the same quantities; the instrument's reading differs by language.

**Evidence.** 2026-08-20 audit, the r11 en/zh pair of a 23-page pitch deck.
Neither reading has been inspected for which is right: the English hit may
be a true conflict the Chinese scan misses (a CJK quantity phrase the
pattern does not read), or a false one the Chinese scan rightly ignores.

**What would close it.** A fixture pair — one quantity stated twice with
different values, in English and in Chinese with a CJK measure word — that
M13 must flag in both, and a look at the real pair to decide which reading
was wrong. Out of the audit-remediation branch's scope on purpose: it sits
inside the Chinese-output diagnosis the owner froze pending her team.


---

## IDEA-19 · A guard that forgets it could not look is indistinguishable from a clean one

**Problem.** FM-24 records six checks that printed a clean result because they
could not complete a measurement. Two of them are `check_repo` guards, and the
reason both survived is not that the channel is missing — an early draft of this
entry said so and was wrong. `check_repo.main()` turns a raised exception and a
`None` return into findings, with a comment stating why (*"A guard that returns
nothing at all is not a guard that found nothing"*), and twenty-two of the
fifty-seven guards catch their own read or parse failure and return a
`could not …` finding; ten of them say `pass vacuously` in the comment beside it.

The gap is narrower and it is the one that bit. **A guard that simply does not
think about its unmeasurable branch returns `[]`, and `[]` is what a clean guard
returns.** Nothing distinguishes "this guard chose to report blindness" from
"this guard never considered it". And where a guard does report it, blindness
and a genuine failure both print `FAIL` with a sentence, so a reader cannot tell
a broken repository from an unreadable one, and no count exists of how many
guards have thought about it at all.

**Evidence.** 0.1.608's `check_board_staleness_clause` returned `[]` when the
distance could not be computed — the same input on which the realigner it backs
declines, so a reviewer rebuilt the whole original defect through the hole with
both reporting success. 0.1.610's `check_vacuous_gates` returned `[]` on a tree
with no fixture, which is the shape every synthetic-tree test creates: the house
pattern for red-testing a guard was the one input that turned it green. Both are
fixed by hand, one guard at a time, by remembering — and twenty-two of
fifty-seven having remembered is the measurement of how well that works.

**What it would be.** A guard returns findings and, separately, says whether it
ran. `check_repo` prints a third verdict — `blind`, borrowed from `check_prose`
rather than coined, because a second word for one idea is a second idea — and
exits non-zero on it, so an unrunnable guard stops a release instead of joining
the green count. The register would carry, per guard, whether a blind result is
ever legitimate, the way `na_means` does for a gate. The useful by-product is a
count: how many guards have declared what they do when they cannot look.

**Why it is not simply done.** Every guard in `check_repo`'s `CHECKS` tuple
returns a bare list today — how many is whatever that tuple holds, never a
number written here — so the change is to their shared contract rather than to
any one of them. It also needs a decision this entry cannot make alone: several
guards legitimately do not apply to a synthetic tree and are written to skip
one, and they must be able to say so without failing. That is the same
honest-silence distinction `evals/gates.json` needed for `na_means`, which was
added at 0.1.562 and carried a WRONG value for M12 until 0.1.575 — thirteen
releases of a field that looked authoritative and stated a superseded rule. Two
guard instances is a thin basis for a contract that has to get that right;
better designed when a third arrives.

## IDEA-18 · The scaffold hands the author six plausible numbers, and only an optional flag can catch them

**Problem.** A bare scaffold's visible prose carries `41`, `312`, `12`, `190`,
`00` and a caption ordinal — the `.band` sample, the two stat tiles, the card's
"Page 00." and `Figure 10`. Two of those are the checker's problem and were
fixed at 0.1.599 (a caption ordinal and a zero-padded page number are the
document's apparatus). The other four are the author's: `41%` and `312` are
sample VALUES, and a sample value that survives to delivery is exactly what red
line 1 exists to catch.

**Evidence.** Measured on a fresh `new_deck.py --genre sales --storyline
market-analysis` piped straight into `check_facts._visible`: six quantities,
none of them the author's. `D14` cannot see them — they are not `[TO FILL]`,
they are numbers that look finished. The only instrument that can is
`check_facts.py`, which runs only when the author passes `build.py --facts`,
and that flag is optional.

**Why it is not simply fixed.** Exempting them would blind the gate to real
invented figures at exactly the place they are most likely to appear, and
removing them from the scaffold would leave the sample blocks without the
number-first shape they exist to demonstrate. The interesting question is
whether the scaffold's own furniture can be MARKED as furniture — the same
declared-not-inferred move `data-role="apparatus"` and `data-omitted` already
make elsewhere — so that a sample number surviving to delivery is decidable
without a contract.

**What would close it.** Two builds where a scaffold sample number reached a
reader. Until then this is a hazard with one recorded near-miss, not a defect.

## IDEA-22 · Four shape sub-keys and the reader_score axis are declared but the study that would use them has not run

**Problem.** The baseline audit (2026-08-30) found four `shape` sub-keys
(`visual_share_median`, `repeated_skeleton_pages`, `move_skeleton_clashes`,
`text_only_figures`) at 0/96, and the board's first sort key `reader_score`
carrying 0 live cells (it joins reviews by `corpus_id`, filled on 3/96, and
those three have empty output_tokens so they never reach the cost board). It is
tempting to call these dead and delete them. They are not dead — they are
DORMANT. `evals/thresholds.json:227` records that the four bars were **refused
as gates in writing** (a red-team pass cleared them with two mechanical rewrites
adding no fact), and that "the agreement study — these numbers against the
owner's H1–H6 scores — is what would earn [promotion], and it has not been run."
`corpus_id` also carries three incompatible vocabularies (thresholds A1/R1 vs
reviews D15/D16, traces D15-D17), so the join cannot close.

**Why not now — and what the decision is.** Deleting removes the data interface
of a deferred study; keeping without running the study leaves the board's top
sort key inert. The owner's call: run the agreement study (H1-H6 vs these
numbers over documents already measured), OR consolidate corpus_id to one
vocabulary and wire the join, OR formally retire the axis. Each is a decision,
not a mechanical change. `check_trace_field_writers` (0.1.650) deliberately does
NOT flag these — they are sparse-or-sub-key, not structurally dead — so they sit
visible but unheld until the owner picks a direction.

## IDEA-23 · The skill depends on 13 uncontrolled external things; the axiom "depend on nothing outside its own control" needs each given a home

**Problem.** The baseline external-dependency census found 3 controlled deps
(the in-repo tracked files gates actually read) and 13 uncontrolled ones —
`~/.lumi/terms`, `node`, Playwright/Chromium, the publish remote +
git-filter-repo (all on gate paths), plus `~/.lumi/traces`, corpus.local,
prices.local, the `~/Documents` delivery/corpus/results dirs, and the platform
CLIs. The owner tightened the first axiom to "depend on nothing outside its own
control." Today missing `~/.lumi`/`~/Documents` degrades the eval/rebuild
pipeline silently but does not crash (it falls back in-repo); the only hard
blocks are check_privacy's declared-terms half and the publish terms list.

**Why not now — and what the decision is.** Each uncontrolled dependency needs a
per-item ruling: controlled (bring it in-repo or generate it), or explicitly
demoted to *material* (a fact source the skill reads but does not rely on the
continued existence of). That is 13 owner decisions, not a mechanical sweep. The
census is the input; the rulings are the work. GAP-047 (check_secrets) and
GAP-049 (~/.lumi/traces unheld) are two concrete instances already broken out;
this IDEA is the umbrella decision about the class.

## IDEA-21 · The conformance tests reach a command through argv and three patched globals, and now they do not have to

**Problem.** 0.1.646 gave the five conformance commands signatures —
`cmd_validate`, `cmd_detect`, `cmd_run`, `cmd_score`, `cmd_report` — because
until then every one of them was reachable only through `main()`, and only after
a shared preamble. The tests were written against that. Thirty-seven of them
reach into module globals, ninety-four `monkeypatch.setattr` calls between them,
to get at behaviour that has nothing to do with globals: patching `TASKS` and
`load_agents` and `detect` in order to ask what `score` does with a run
directory.

**Why it was not done in the same release.** Mixing a thousand-line mechanical
move with a test rewrite makes both unreviewable, and the move's whole claim was
that nothing changed. It held: no flag, no message, no test expectation moved.
The seam earned its first use one release later, when 0.1.647 needed to prove
that a refused run leaves every other measurement on disk — a fact about the
LOOP, which no test calling the check on one directory could see, and which
`cmd_run(tasks, agents, probed, runs, args)` states in four lines.

**What it is worth.** Not a rewrite for its own sake. The specific cases worth
moving are the ones where a patched global is standing in for a parameter that
now exists — those tests are asserting the wiring rather than the behaviour, and
they go green when the wiring changes underneath them. A test that patches a
global to control an actual global (`ROOT`, `RESULTS`) is right as it is.

**Cost.** Per test, minutes. The reason to do it in batches is that each batch
is a chance to notice a test that was never asserting what its name says.

## IDEA-20 · The figure is where a reasoning tier's quality actually shows, and nothing in this package chooses one on purpose

**Problem.** The owner read all twelve decks from the 0.1.626 four-tier round
and reported: Low is visibly weaker, Medium and High are hard to tell apart,
Extra High is slightly better — and **the whole difference sits in the figures**,
in how each page's drawing is chosen, dimensioned and labelled. Not in the
prose, not in the layout, not in the palette.

That is the part this package leaves most to chance. `assets/frameworks.json`
maps question → framework → shape and the ghost-deck beat names one per section,
but nothing reasons from the CONTENT of a page to the drawing that would make a
reader understand it fastest: which comparison the figure is really making, what
belongs on each axis, whether the numbers or the words carry the point, and
whether two thin figures should have been one.

**Evidence.** Twelve runs, one task, four tiers, every one passing every gating
check. The mechanical difference the checks CAN see is `layout_top_share` — the
share of pages using one layout — and it runs 40–90% with no relation to tier.
One `high` run spent 18,470 output tokens (a third of its tier's dearest run),
passed every gate, and put **80% of its pages on one layout**. The checks read
that deck as equal to the one that cost three times as much; a person does not.

**Why this is worth a design pass rather than a rule.** The obvious move —
another prose rule saying "choose the right figure" — is the shape convention 2
forbids: a direction with no way to tell whether it was followed. What the
owner's read suggests is closer to an analysis beat with its own inputs: read
the page's content, name the comparison, then pick the shape from that, and say
in the figure itself what the reader is meant to take from it.

**What to investigate.**
- Whether the ghost-deck beat can take the page's DATA as an input rather than
  only its analytical move, so the framework is chosen from what is being
  compared.
- Whether the exemplar notes (`references/exemplars/mckinsey-design-notes.md`)
  carry enough about axis choice and figure-internal hierarchy to act at
  composition time, or whether they need a figure-level companion.
- Whether `layout_top_share` and `shape.figures` can become a REPORTED signal a
  human review is anchored to, rather than an observation nobody reads.

**What this is not.** Not a new gate. The thing it would improve is the thing
`SKILL.md` says metrics can never settle — whether a page reads as intentional.

**Filed 2026-08-27** from the owner's read of the four-tier round. Related:
[[IDEA-19]] on guards that forget they could not look, and the standing limit in
`conformance/agent-evals.json` that above the gate line the checks cannot tell
two documents apart.
