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

This is the second beat of the discussion entry path, and the questions
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

---

**These rules are restated in the entry points**, which is what entry points
are for. `references/` is where they are true; `SKILL.md` and `AGENTS.md` are
where an agent reads them. When the two disagree, this file wins.
