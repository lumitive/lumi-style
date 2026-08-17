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

- `init` at the start, naming the platform from the registry;
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

## 3 · Questions come once, or not at all

Study everything the user supplied first, and work from the reader's side: the
first-principles question is what this reader does differently after reading.

When a required input is missing, or two requirements conflict, **batch every
question into one round before generating**. Otherwise state the assumption in
the deliverable and carry on. A second round of questions costs the user more
than a stated assumption they can correct, and an agent that asks continuously
has moved its own uncertainty onto them.

This is the second beat of the discussion entry path (§6), and the questions
themselves are bounded by the form/content line: they may ask about structure
and evidence, and may not decide the conclusion.

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

**Timing starts when the storyline is agreed.** Discussion and outline are not
counted against it. Charging a user for the thinking they were asked to do
would push every build back toward path B, which is the opposite of what the
measurement is for.

---

**These rules are restated in the entry points**, which is what entry points
are for. `references/` is where they are true; `SKILL.md` and `AGENTS.md` are
where an agent reads them. When the two disagree, this file wins.
