# LUMI Operating Rules

*Serves: **P-2**.* · id `OR-1`

Every other file in `references/` says what a deliverable must be. This one says
how the work is done, and it is here for a specific reason: five rule families
had their only home in an entry point. An entry point is a hand-written
restatement by design, so a rule that exists **only** there has no source — the
restatements have nothing to be checked against, and the rule quietly means
whatever the last edit of that file left behind.

They belong under P-2 rather than the product goal because each answers the same
question: **what makes the result of this work trustworthy rather than merely
finished.** A log that is written by the machine, a merge that refuses a
leftover, a figure that is generated from data rather than drawn — each is the
difference between an artifact that carries evidence and one that carries a
claim.

## 1 · Debug mode is a log the machine writes

On request only. When the user asks for debug mode, an execution log is written
beside the deliverable — `<stem>.debug.json` — through `scripts/ops/debug_log.py`
and **never by hand**. The subcommands are the schema, so every platform
produces the same log:

- `init` at the start, naming the platform from the registry — and
  `init --resume` at the start of every round after the first, because a
  build is N rounds and the record belongs to the deck rather than to the
  round. Until 0.1.601 each round restarted the log and carried nothing
  but the self-score, so a build's earlier evidence survived only if an
  operator moved the file aside by hand;
- `run` for **every check or build command** — it executes the command and
  machine-writes the exit code, output digest and timing;
- `attach` for each checker's JSON output.

**The point is the same one `check_evidence.py` makes about releases**: a log a
person could type is a claim, and a log the machine wrote while running the
command is evidence. There is no subcommand for stating a result.

The debug log stays in the delivery directory and never enters a trace — the
trace is its anonymous projection, and red line 9 is held by the trace schema
rather than by care.

## 2 · Parallel building, and the merge gate that makes it safe

Pages are independent once the storyline is fixed, so parts may be written in
parallel where the platform allows it. The protocol exists because parallelism
without one produces a document assembled out of inconsistent halves.

- **The orchestrator owns the frame.** It fixes the storyline and page order,
  generates the scaffold with `new_deck.py`, and splits content pages into
  contiguous parts. Shared things stay OUT of the parts as placeholders, so no
  part needs to know the page total or carry a copy of an asset.
- **Part authors write page markup only** — no head, no fonts, no runtime, no
  page numbers. Each works against the same tokens and rules.
- **The assembler stitches, and then refuses.** Preamble, parts in order,
  placeholder substitution — and a scan for any unreplaced placeholder that
  **fails the build** rather than shipping it. A placeholder reaching the reader
  is D14's territory; this catches it one stage earlier, where it is cheap.
- **The runtime is BUILT, never harvested.** The assembler calls the embed
  scripts; it does not copy a runtime out of an earlier deliverable, because a
  copied runtime is a copy of whatever version that deliverable happened to
  carry.

## 2b · A build gets its own session, and one command per stage

The bill for an agent build is `API calls x context per call`, and both halves
are the build's to control. Measured on one 2026-08 ten-page deck: **460 calls,
105 million cached input tokens, 389 terminal commands** — `inspect_layout` 64
times, the fill script 46, `embed_shapes` 38, and the one command that runs the
whole check stack, 6.

- **One command per stage.** `scripts/ops/build.py` runs scaffold, fill, embed
  and the full gate stack in one process, and writes the debug log as a side
  effect rather than one wrapped command per turn. `check_deliverable.py`
  already contained every instrument; running the stack and then the instruments
  is the same work twice, and the expensive half is a browser.
- **Use the loop flags.** `--fast` on the driver, `--iterate --no-sheet` on
  `inspect_layout` directly: about 4 seconds against 22 on a twelve-page deck,
  with every gate still running. The delivery round runs without them.
- **A build gets its own session.** Unrelated conversation in the same session
  is re-sent on every call for the rest of the build. On the build above, a
  cost-verification discussion held in the same session cost about as much as
  the build it was measuring.

## 3 · Questioning is segmented, and the segments are the user's

Study everything the user supplied first, and work from the reader's side: the
first-principles question is what this reader does differently after reading.

Let the user state everything freely, without interruption; then follow up
**segment by segment, grouped by the topics the user themselves raised** —
the segments are theirs, never the agent's categories. The experimental
record is one-directional: segmented follow-up recovers roughly twice the
core detail of a single batched round, and follow-up questions carry a
load-bearing share of what tacit knowledge surfaces at all. (This section
said "batch every question into one round" for six releases — a practice the
2026-08 research had already falsified as an evidence-free invention before
it shipped; the research finding was adopted into the refactor plan and lost
in transit, and nothing compared the shipped text against the research until
an owner review forced the audit.)

Two bounds hold regardless of shape: an agent that asks continuously has
moved its own uncertainty onto the user — when nothing needs asking, state
the assumption in the deliverable and carry on; and the questions are
bounded by the form/content line — they may ask about structure and
evidence, and may not decide the conclusion.

This is the second beat of the discussion entry path (§6).

## 4 · Scaffold with the tool; never hand-copy a fixture

`python3 scripts/ops/new_deck.py` emits a document that already renders, in the
standard order. **A fixture is not a starting point.** A shipped review once
carried `REPLACE ME` as its title and the fixture's `www.example.org` in every
footer, which is why D14 now refuses both strings — but the refusal is the
backstop, and using the scaffold is the rule.

## 5 · A world figure that states data is generated, not drawn

Use the shipped assets rather than improvising: `embed_font.py` for the display
face, `embed_icons.py` for the icon library, `embed_shapes.py` for the shape
library, `assets/vectors/` for the globe and trade map.

**For a world figure that states data, generate it**: `regionmap_svg.py` emits
the flat trade-region map with its labels already placed, and `globe_svg.py`
the rotating globe. A hand-drawn coastline is a coastline nobody checked, and
a figure that states data must be the data — which is what D21's contract asks
of any figure that declares what it draws.

## 6 · One pipeline, two entry paths

*Serves: **GOAL**.* · id `OR-2`

A document reaches the pipeline one of two ways, and the trace records which.

**Entry path A — discussion.** Four beats, and the order cannot be reversed:

1. **Free statement.** The user speaks first and the agent does not interrupt.
   Asking first anchors them: it turns their problem into our question.
2. **Segmented questioning.** The agent leads, and every question passes the
   form/content line — it may ask about structure and evidence, and may not
   decide the conclusion. §3 is where that beat is written in full.
3. **Advice.** The agent proposes: the argument, the shape, what earns a page.
4. **Storyline review.** Titles, order, and the logic joining them, agreed
   before anything is built. `check_outline.py` is the machine half of this
   beat; the argument itself stays a person's.

**Beat 4 is the only defence completeness has, and that has to be said plainly.**
C5 reports and never gates, on evidence — a completeness gate is worth
defeating, and structural compliance does not predict quality. So a section
nobody noticed was missing is caught at beat 4 or it is not caught at all. Skip
the beat and completeness has zero defence. The trace records
`outline_reviewed` so that skipping it is a countable fact rather than an
invisible choice.

**Entry path B — template.** A document built from a recipe rather than from a
conversation: a scaffold, a previous build's source, an agreed structure carried
forward. It is legitimate, it is faster, and it is what most real builds use.

**Both paths are held to the current constitution, rules and evals. A recipe is
not a licence to reproduce the document it was written for.** Re-running a
source script demonstrates that nothing broke; it demonstrates nothing about
the capability added since it was written. Path B therefore owes the same
things path A owes — the current rule set, the current gates, a storyline
somebody stands behind — and a build that cannot say which version of the rules
its recipe was written against has not established that it followed them.
*Owner ruling; the case is a rebuild whose argument was two research rounds
behind its own evidence base while every gate reported green, and a second
rebuild that differed from its predecessor by two lines.*

**So a path-B build names its recipe, and the trace fingerprints it.**
`trace.py open --recipe <path>` records the bytes the build was actually driven
by and the version stamp that recipe carries. This exists because a trace's
`skill_version` is read from `SKILL.md` when the trace opens — it always equals
the current version and *cannot* be stale — so without the recipe's own vintage
a replay of a frozen script produces a record indistinguishable from a build
made to today's rules. The ledger reads three different answers where there
used to be one: **current**, **stale** (the recipe names an older version than
the rules that graded it), and **unknown** — a recipe carrying no stamp at all.
**Unknown is not current.** A recipe that never said which rules it was written
against has not told anyone it followed them, and the first real recipe
measured was exactly that case.

**One build, the whole instrument read, one fix pass.** The pre-delivery
stack answers as a single block (`check_deliverable.py`), and the block is read
whole before anything is edited: a ten-round build was autopsied and at least
three rounds were failures met in installments — present in the first report,
discovered in the third — because the reports were grepped instead of read.
Output that has been filtered has not been read.

**Timing starts when the storyline is agreed.** Discussion and outline are not
counted against it. Charging a user for the thinking they were asked to do
would push every build back toward path B, which is the opposite of what the
measurement is for.

---

**These rules are restated in the entry points**, which is what entry points
are for. `references/` is where they are true; `SKILL.md` and `AGENTS.md` are
where an agent reads them. When the two disagree, this file wins.

## 7 · Source material is a fact source, never a sentence source

*Serves: **P-2**.* · id `OR-7`

A prior document supplied for a rebuild, whether it is an earlier draft, a
competitor's deck or a colleague's outline, contributes **facts and
constraints**. It does not contribute sentences, titles, or the order of the
argument, unless the user says in so many words that it should.

The rule exists because the failure is invisible to every prose metric this
package ships. A rebuild can copy no sentence at all and still inherit the
whole argument: at the 2026-08 roadshow build, sentence-level copying measured
zero while nine of fifteen page titles carried a fragment of the source deck
and ten of fifteen signature phrases survived. The document passed the ban
list, the punctuation pass and the rhythm floor, and the owner read it as a
copy on sight, because it was one.

**In practice.** Extract the facts into a list with their sources, and give
the part authors that list. Do not give them the prior document. Re-derive the
page titles by applying the analytical moves (AR-1) to the facts: a move that
lands on the title the source already used is evidence that no move was
applied, not that the title was inevitable. Where the user wants a phrase
carried over because it is theirs and it works, that is their decision and it
is recorded as one.

**The related trap in the same family**: writing the analysis declarations
after the pages exist. A declaration produced to describe a finished page
documents nothing; AR-3's line runs move → finding → page, and the outline
beat is where that order is visible.

## 8 · The out-of-bounds list lives in one place, outside every repository

*Serves: **P-5**.* · id `OR-8`

The terms a deliverable must not carry — prior clients' names, other
projects' code names, internal system names — are kept as **one file per
engagement** under **`~/.lumi/terms/`**, named `<engagement>.terms.txt`, one
term per line, `#` for a comment. `check_privacy.py` reads every list there
when it is given no `--terms`, and `check_repo.py`'s secrets guard runs the
same lists over this repository's tracked files on any machine that has them.
Nothing else reads them and nothing writes them anywhere.

The list accumulates across engagements (owner ruling, 2026-08-15): it gets
safer with use, and it is therefore the most sensitive single file in the
workflow. Three constraints follow, and they are not advice:

- **strings only** — a name, never a context ("X Bank, 2025 project" is a
  second leak);
- **never in a repository, a trace, a report or a debug log** — it is the
  thing checked, not a thing recorded; `.gitignore` nets `*.terms.txt` as
  the second layer, and the checker never echoes a term in a finding;
- **file-system permissions first** — encryption is a later decision, and a
  gate does not wait for a later decision to go live.

A pure-Latin term matches on word boundaries; a term carrying a CJK
character matches as a substring, because that script does not put spaces
where a boundary would be. Embedded fonts and images are blanked before the
term scan, since base64 spells every short Latin word eventually (IDEA-15).

## 8b · An operator's stores live outside the package

*Serves: **GOAL**.* · id `OR-8b`

Four things this package writes belong to the person running it, not to the
package: the build traces, the local corpus registry, the price table, and the
review scores. They resolve through one answer — `LUMI_STATE` if it is set,
else `$XDG_STATE_HOME/lumi`, else `~/.lumi` — with `LUMI_TRACES` still winning
for the trace store alone.

**A checkout that already holds one of them keeps it.** The resolver prefers the
in-repo directory when it exists, so no release ever moves an operator's file;
an installed skill, which has no such directory, gets the state directory
instead. Nothing is created by asking where a store is — a directory appears on
an explicit write and never on an import or a read. This is `OR-8`'s rule for
the out-of-bounds list, generalised to everything else with the same shape.

## 8c · An uncontrolled dependency degrades or fails loudly, never silently

*Serves: **GOAL**.* · id `OR-8c`

The deliverable path is standard-library only, so a deck depends on nothing
outside this repository. Everything else — the browser that renders a check, the
platform CLIs a conformance run drives, the operator stores of `OR-8`/`OR-8b`,
the publish remote — is a tool the package READS but must not RELY on. The rule
that keeps "reads" from becoming "relies": **when an uncontrolled dependency is
absent, the tool degrades to a controlled in-repo fallback OR fails loudly — it
never silently changes a verdict.** A silent pass computed over a missing source
is the one outcome forbidden; a borrowed tool is a decision, a silent wrong
answer is a defect.

This is the rule the 2026-08-30 dependency census earned
(`specs/2026-08-30-dependency-rulings-design.md`). Of thirteen uncontrolled
dependencies, eleven are *material* — their absence degrades or refuses out loud
(a browser check is an evidence-gated operator step, not a silent CI pass; a
results directory falls back to `conformance/results/`; the out-of-bounds list
refuses at `check_privacy`/publish and, since 0.1.652, `check_secrets`) — one is
already in-repo, and one (the out-of-bounds list) cannot be controlled at all
because client names cannot ship, so it is made loud instead. The single place
this rule is not yet met is the operator trace store diverging from the in-repo
copy unseen (`KNOWN_GAPS.md` GAP-049), which is why that gap stays open.

## 9 · An agent that cannot run the checks may not call a deliverable verified

*Serves: **P-2**.* · id `OR-9`

Three capability tiers describe what an agent can do with this package:
`full` reads the bundled files and runs `scripts/`; `files` reads but cannot
execute; `prompt` receives one pasted context and no tools. The obligation
and the prohibition go together, and both bind the two lower tiers without
exception: **the agent names the checks it owes, the operator runs them, and
until then the agent may not call the deliverable verified.** "Verified" is a
claim about a measurement (P-2), and an agent that has made none has nothing
to claim it with — a self-score, a read-through or a checklist ticked by the
author are not measurements.

This rule lived only in the platform registry until the audit remediation,
where every entry point says `references/` wins on conflict; a binding rule in
the file that loses is a rule that can be lost. The registry and the review
protocol cite it from here.

## 10 · A scored document is never deleted

*Serves: **P-2**.* · id `OR-10`

A human score is evidence about one document. The agreement study joins a
machine reading to that score by corpus id, the threshold table is calibrated
on the documents it names, and a retrospective reads the pages the score was
given for. Delete the document and every one of those becomes a number with
nothing behind it: the first two documents scored on C1–C8 (and the third
that carried a trace) were deleted within a week of being scored, and the
study's three joinable pairs can never be re-measured.

So: **a document that has been scored, registered as a corpus id, or named
by the threshold table is kept** — in the delivery directory, under its
build name, for as long as the score is in the store `review_scores.py` reads.
Superseded builds that were never scored or registered may go. Where a
scored document was already deleted, its corpus entry records the loss
(`archived: {sha256, pages, removed_before}`) so the id resolves to a fact
rather than to nothing; `review_scores.py --check` fails a scored id that
resolves to neither a file nor an archive.


## 11 · Hand the generator the content; edit the emitted markup only where it has no field

*Serves: **P-2**.* · id `OR-11`

**A build's cost is not in the writing. It is in the guessing.** Measured on
one ten-page deck: a 519-line assembly script, 19 hand-written substitutions
against the scaffold's own markup, and **12 wrong guesses about what that
markup looked like** — a class name, a tag, a sprite id, the agenda's
structure, an icon id, two cells that collapsed into one, an unclosed `</div>`,
a colophon that wrapped across lines and defeated a single-line pattern, and a
set of figure coordinates that ignored `preserveAspectRatio`. Each wrong guess
cost an edit, a rebuild, a render and a look, and none of it was about the
deck.

So: **give `new_deck.py --content <content.json>` the words, and let it render
them.** The shape stays where it is written, once, and a typo stops the build
instead of vanishing.

Where a field genuinely does not exist, surgery is still the answer, and then:

- **One `python3` heredoc carrying a list of `(old, new)` pairs, with
  `assert old in s` on every pair** — never a chain of one-off `sed` calls. A
  substitution that matched nothing is the failure mode, and it is silent: the
  script exits 0, the document is unchanged, and the next thing anyone looks at
  is a render that does not show the fix.
- **Never pipe a verification command, and never chain a commit to one.**
  `preflight.py | tail && git commit` reads `tail`'s exit status. This is
  convention 16 in the maintenance rules; it holds for deliverables too.
- **Re-close the container.** Surgery inside a `.body` that removes or replaces
  a block has twice lost the `</div>` before the footer. Count the div balance
  after any structural edit.
