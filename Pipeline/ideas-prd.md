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
CHANGELOG can cite. Verified against the tree at restoration time:

- **IDEA-3 shipped** — 0.1.390's fixture coverage work is exactly this item
  (34/34 graded verdicts have a failing fixture today).
- **IDEA-4 shipped** — `reviews/scores.json` + `scripts/review_scores.py`
  exist and gate in CI.
- **IDEA-7 in progress** — the conformance-history work of the
  engineering-quality migration (`specs/2026-08-12-engineering-quality-plan.md`
  R11) is this item's acceptance in different words.
- IDEA-1, IDEA-2, IDEA-5, IDEA-6 remain open.

## IDEA-1 · Implement M1, M2 and M6

**Problem.** Six of the twelve M-metrics have no code behind them. Three of the
six carry rules the package itself calls non-negotiable.

**Evidence.**

- `scripts/check_prose.py` computes M4, M8 (two halves), M9, M10, M11 and M12.
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
- M2 and M6 fail (non-zero exit) like M4. M1 reports rather than gates until it
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

- `scripts/check_prose.py` states in its own docstring that it handles English
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

- `scripts/check_fixtures.py` runs `check_prose.py` and `check_design.py` only.
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

- `scripts/inspect_layout.py` defines a `laptop` geometry at 1000×550 and a
  `16x9-hd` at 1920×1080, and its default geometry list contains neither.
- `../references/design-rules.md` §7 requires the short-laptop check by name and
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
