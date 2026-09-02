# Design · Making the lessons compound

*Written 2026-09-02, after the owner asked whether each iteration is actually
getting better. A record of what was decided and why. Rule prose stays in
`references/`, values in `tokens/`, rationale in `CHANGELOG.md`.*

## The question, and the measurement

The owner asked whether the problems every review turns up accumulate into the
scaffold and the foundation, so that the next round is better — and then, more
sharply, that what she cares about is not this document improving but each
iteration improving.

The honest answer was mostly no, and the evidence is this repository's own
record. Every one of the seven defect classes the 0.1.677 pre-merge review
found was **already written down**:

| the class | how long on record |
|---|---|
| a gate that prints clean when it cannot look | FM-24, ten mentions |
| a test that reads the constant it pins | recorded, saying it had happened twice |
| a held-fixed axis is an unchecked axis | recorded |
| a gate a correct answer cannot satisfy | AG-10, four mentions |
| a coverage claim that does not say what it cannot see | convention 20 |
| a claim about behaviour nobody read | convention 14 |
| a fact changed without sweeping its restatements | convention 12 |

All seven were committed again anyway. The self-inflicted rate across the last
forty releases does not converge either: 4/10, 1/10, 3/10, 5/10.

## The dividing line

Sorted by what happened to each class, the pattern is not subtle.

**Became something that RUNS → went to zero.** Markup guessing, 12 wrong
guesses to 0, because the content interface removed the possibility rather
than asking for care. Hand-written substitutions, 19 to 0. Every gate holds
its class for good once it is a row in a checker.

**Became only a paragraph → came back.** FM-24 ten times. AG-10 in the same
release that fixed it for a neighbouring move. The constant-pinning pattern
four more times in one branch.

Convention 16 already states the principle — *a rule written down and then
broken does not need writing more firmly; it needs a tool that holds it* — and
this repository had been applying it to the release pipeline and not to its own
failure modes.

## The three mechanisms

Chosen because each converts a class with a long paper trail into something
that runs, and each is decidable without judgement.

1. **`self-referential tests`**, a `check_repo` guard. Purely syntactic. It
   follows the constant through local names, because both real instances
   unpacked it a line earlier and a guard reading the `assert` line alone
   catches neither. It refuses numbers and containers, where the VALUE is the
   contract, and allows plain string sentinels, where the identity is.

2. **The third answer as a coverage rule**, in `check_fixtures`. It tracked
   whether a fixture could make a gate FAIL — FM-01's question standing in for
   FM-24's, so a gate seen only failing counted as covered. Gates declared at
   or after 0.1.667 must now declare what an n/a from them means AND have been
   seen saying it, or declare why they can never be n/a.

3. **`mutation_probe.py` in the release flow**, bounded to the files the
   release changed and the tests that reach them. A survivor fails the release;
   the answers are a test or a recorded reason.

## Decisions inside the design

- **Discovered, never listed.** FM-20: a hand-written inventory is short the
  day it is written. The guard's subject set is every module a test imports;
  the probe's test selection is every test importing the changed module; the
  gate rule reads `evals/gates.json`.
- **Grandfathered rather than backfilled.** Fifty-five gating verdicts predate
  the third-answer rule. A guard that fails on all of them the day it ships is
  a guard someone switches off; the cut is set where the two newest gates
  already comply, so it has teeth immediately and no backlog.
- **Bounded rather than thorough.** A full-suite mutation run is seven minutes
  per mutation. The probe finishes in seconds because it mutates only what
  changed. An unbounded step is a step that gets skipped.
- **A waiver is a debt with an address**, keyed on the source line's text and
  not its number — a line-numbered waiver stops matching when anything above it
  moves, which is the citation-drift class fixed the same week.

## What this does not answer

**Four of the seven classes are still only paragraphs**: a claim written
without reading the code, a fact changed without sweeping its restatements, a
gate a correct answer cannot satisfy, and an instrument's reach described as
the requirement's. Each needs the same treatment and none has it. That is the
next round's work, and naming it here is the point — the failure this whole
design is about is a lesson recorded and then not converted.
