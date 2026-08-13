# Stopping the prose-vs-code drift — design record

Date: 2026-08-13 · Status: settled, implementing at 0.1.452 · Owner ask: after
0.1.451 shipped a fix that turned out to cover two of ten sites, the owner asked
for a complete scheme rather than another round of tidying.

## The measurement

Twenty-six of 124 released versions carry an explicit fix for a prose copy that
disagreed with the code. Twelve of those fixed a stale *count* specifically.
**Five of the last ten releases carry such a fix** — the recent rate is double
the lifetime rate, so the problem is getting worse while being written about.
Where a CHANGELOG entry says how long the drift stood, it is four to eleven
releases. Two releases (0.1.360, 0.1.429) exist for nothing else.

The registry already names the class twice — FM-03 prose-copy drift, FM-05
enumeration rot — and both entries end their `prevention` line by handing the
job to a person: *"the semantic half stays a review duty"*. That is why it keeps
happening. Nothing here is a new discovery; the discovery is that recording a
failure mode does not prevent it.

The immediate case: `check_design.py` gained a fourth gating metric at 0.1.443.
Nine sentences said three. 0.1.451 fixed two of them and said so in its entry.
One of the seven it missed is in `AGENTS.md`, eighty-six lines below a line that
same edit corrected, immediately above that file's own confession about carrying
a wrong gating claim for eight releases.

## Decisions

**D1 — Delete the number before guarding it.**
The winning move is already in the repository and applied inconsistently:
`preflight.py`'s docstring refuses to state the CI step count ("how many is
whatever the workflow says today, never a number written here"); 0.1.429 deleted
that count rather than correcting it; `check_js.py` discovers probes by naming
convention; `deliverable_verdicts` names itself the authority instead of
counting. Every finding in this release is a place where someone wrote the
number down instead. So the first move on each is deletion — six of the range
claims became "the design metrics" or "the M / D / H rubric" and cannot rot
again — and a guard is what remains for the counts that carry meaning.

**D2 — One guard that discovers its sites, one that declares them.**

`check_metric_id_ranges` needs no registry. A range written from `D1`/`M1` claims
a whole family, so its endpoint is checkable against the highest id the checker
defines, and a claim written next week is covered without anyone registering it.
Ranges that do not start at 1 are subsets and are left alone; that single rule
removes the false-positive class without a waiver list.

`check_gating_claims` cannot discover its sites, because knowing that a sentence
is making a claim *about gating* means reading English. So the sites are declared
with the pattern that captures their ids, in the `ENTRY_STAMP` shape — and a
pattern that stops matching is an **error**, not a skip. Without that, rewording
a sentence would silently retire the check on it, and the guard would protect
only sentences nobody edits.

*Answering AG-1.* 0.1.422 declined a guard that decides from prose whether a
sentence is making a claim, as brittle by construction and FM-01 in the making.
Neither guard does that. The first matches an identifier pattern (`D1-D17`),
which is lexical; the second matches ids inside a declared span. What AG-1
refused is the thing `claim_sweep.py` does — and it does not gate.

**D3 — The advisory sweep, sized to be read.**
`claim_sweep.py` reports counted claims and `file:line` self-citations whose
lines have moved. It always exits 0. Sizing was the whole design problem: the
first cut reported 1115 sentences, which is the package, and a report that size
trains the reader to skip it — the same failure the release is about. Three
narrowings brought it to 197: require the count adjacent (16 characters, not 40)
to a name this repository owns; drop quantifiers, because "every guard" survives
a new guard and "three guards" does not; skip generated entry points, whose
claims are copies held byte-identical to their source by another gate.

Declined: making it fail. A reporting tool that can fail a run is a gate nobody
argued for, and this one was argued against.

Declined: putting it in CI. It would be a 200-line always-green step, which is
noise of exactly the kind the narrowing above exists to prevent. It goes in the
release flow and in `CLAUDE.md`'s Checks block instead. This is a narrower call
than AG-5's ("a gate must run under preflight, not only in CI") and does not
contradict it: AG-5 is about gates.

**D4 — Conventions that name a command.**
Three added, per the owner's condition that a prose rule must point at something
executable: sweep the restatements of a fact you change (`claim_sweep.py`),
prefer deleting a number to maintaining it (the guards are where a surviving
count lives), and do not write a claim about behaviour you have not read in the
code. The third is a rule about the CHANGELOG, and it exists because this
session's author broke it: 0.1.450's entry described a harness driving an agent
that the harness has never driven.

## Out of scope

The two releases this one clears the ground for: the blind figure metrics, and
the conformance driver. The order is deliberate — both will write new prose, and
it lands on a tree where the guards already run.
