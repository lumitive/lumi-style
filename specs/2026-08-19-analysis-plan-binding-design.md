# The plan becomes an input — design record

*Written before the work, 2026-08-19, for 0.1.522. Implemented; kept as
history. A spec is never cited as authority — rules live in `references/`,
values in `tokens/`, rationale in `CHANGELOG.md`.*

## The complaint

The owner's retrospective: the analysis and insight capability does not take
effect by itself, the intelligence has serious inertia, information is
forgotten or omitted between rounds, and absorbed bodies of knowledge
(McKinsey, YC) have not made the work better. Every gain costs another round
of her asking.

## What the audit measured, rather than guessed

1. **The analysis beat ran and its output was discarded.** A shipped deck's
   outline declares a move, a written finding and a written implication for
   14 of 14 content sections. **0 of those findings still described a page.**
   Nothing carried `finding:` into `<h2 class="t">` or `implication:` into
   `<p class="take">`, and nothing noticed.
2. **A rebuild silently dropped eleven facts** — four brand names, five of the
   seven markets whose count the deck still claimed, two delivery figures —
   with every gate green.
3. **Typographic knowledge landed automatically; analytical knowledge did
   not.** Row labels ×56 and stat blocks 11/11, against 0 benchmark lines and
   1 scope flag over 14 pages. What a stylesheet can carry gets applied.
4. **The architecture has one structural generator and no content
   generators**, ~44 deliverable gates, and `assets/frameworks.json` validated
   by a guard and read by no runtime.

## The cause

0.1.516's spec already named it: *the form/content line, right about GATING,
was over-applied to GUIDANCE.* "Never gate on quality" — earned by the
withdrawn 82% fill floor — was being executed as "do not act on quality at
build time". Absorbed knowledge therefore went to `references/` prose, which
is inert by construction.

## The decision

Not more rules, and not quality gates. Make the plan an **input** to the build,
and check the artifact against its own declared plan. Both are consistency
checks of the class D27 already applies to the agenda; neither asks whether
anything is good.

- `new_deck.py --outline` pre-fills each page from the beat and names the
  framework the declared move implies, quoting its `misuse` line.
- `check_outline.py --against` gates on findings reaching titles, reports on
  implications reaching takes.
- `check_facts.py` gates on quantities absent from the contract, reports facts
  the build dropped.

## Rejected

- **Gating on the implication rung.** It is a judgement about prose. A take
  rewritten better than its outline is a legitimate outcome, and the check
  cannot tell that from a take that lost the point.
- **Archiving the source material as the mechanism.** The audit's own finding
  is that `references/exemplars/` is where knowledge goes to be inert;
  EX-4 is provenance, and the conventions in `CLAUDE.md` are the mechanism.

## Acceptance test

Run both checks against the rebuild that lost the eleven facts. They must fail
before the code is trusted, and pass after correction — the claim being that a
script catches what five rounds of the owner's review caught by eye.
