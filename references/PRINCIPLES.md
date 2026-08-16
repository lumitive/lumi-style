# LUMI principles

> **lumi-style 0.1.495.** Six clauses, stable numbering, owner-only. Expected to
> change less than once a year; a change needs a spec and the owner's explicit
> approval, not a retrospective.

**What this file constrains: how rules are made and where they belong.**
It does not govern the writing of any individual document — the rules in
`references/` and the gates in `scripts/check/` do that. Every rule family
declares which clause it serves, so "why does this rule exist" is a question
with an answer. The one place a clause reaches a live document is §3's exit.

**What this file is not.** It is not a summary of the rules, and nothing here
restates one. This repository's dominant defect is the same sentence written by
hand in several places; a constitution that repeated the rules would be the
worst instance of it.

## 1 · The clauses

Numbering is identity order: read top to bottom and you have read what this
product is. Brand consistency is first because it is the only thing unique to
this skill; being grounded and being safe are the entry ticket for any
professional tool and do not describe an identity.

**P-1 · Brand consistency.** The brand pack is the single source of visual and
verbal identity; a deliverable does not improvise. *MUST.*

**P-2 · Grounded.** Every assertion carries evidence, and the kind of evidence
follows the kind of assertion — facts trace to a source the user supplied;
judgements and recommendations trace to facts and reasoning already shown in the
document; claims about the document's own quality trace to an actual
measurement. Never invent. Illustrative values are labelled illustrative. An
agent that cannot run the checks lists what it owes and may not call anything
verified. *MUST.*

**P-3 · Plain language.** Plain, calm, concrete. No AI register. A term is
explained where it appears. *MUST; a rule under this clause may state its own
exception.*

**P-4 · Figures over prose.** What a figure can express precisely is not piled
into words. A figure carries the argument: **one that carries no argument is
decoration, and violates this clause rather than satisfying it.**
*MUST; a rule under this clause may state its own exception.*

**P-5 · Safety and compliance.** Sensitive information does not leave the
document boundary. Every page states how it may be handled, because pages travel
alone. *MUST.*

**P-6 · Accountability.** AI does not take the byline. Money and safety
conclusions are always made by a person. *Absolute — a boundary, not a goal that
trades against the others.*

## 2 · Strength, and why there is no ranking

Each clause carries its own obligation strength. **There is no order between
clauses**, and adding one would be a mistake with evidence against it:
no major professional code ranks its own principle set, and every one that
expresses an asymmetry does it with a single paramount clause and leaves the
rest unranked — which is the shape of P-6 and is not the shape of a six-level
chain. A strict order is also only lossless where each criterion outweighs the
sum of all those below it, which is not true here; and where scores are
continuous, ties never occur and the lower clauses are never reached at all.

Irreversibility of harm is why a clause gets the strength it has — it is why
P-6 is absolute — and it is not a ranking between clauses.

**"MUST" is what makes a clause non-optional.** No clause yields as a matter of
course.

## 3 · When two clauses collide

**First, write the rule more precisely so the collision does not arise.** Most
apparent conflicts are artefacts of a clause stated too coarsely. A rule under
P-1 that reads "the brand pack is the only source" appears to forbid a chart
that needs three series; a rule that says P-1 governs identity rather than
suppressing comprehension, and that multi-series colour comes from the `chart`
tokens, has no conflict to resolve. Prefer redrafting to adjudicating: an
adjudication decides one case, a redraft removes the case.

**When two MUST clauses still cannot both be satisfied after that:**

> **Record the conflict and the reasoning · refuse to emit · hand it to a person.**

This is the one clause-level rule that acts on a live document, and it is
deliberately rare. It is not a licence to stop work when a rule is inconvenient:
it applies where satisfying one MUST necessarily breaks another, and the
document names both. A refusal is evidence that a rule needs redrafting, which
is why it is recorded rather than merely acted on.

## 4 · Declaring a parent

Every rule family in `references/` declares the clause it serves, or `GOAL`.

`GOAL` means the family serves the product's purpose — a document that serves
the reader's decision, at the standard of a competent consultant — rather than a
constitutional clause. **That is a legitimate parent, not an orphan.** Layout,
the output-language default and the storyline templates all sit there, and
forcing them under a clause would produce strained parentage and a traceability
chain worth nothing.

`check_repo.py`'s `principle trace` guard checks that the declaration exists and
that the clause is real. **It cannot check that the right parent was chosen** —
that stays a human judgement, and the guard's own documentation says so. It
stops orphans, not misclassification.

**A clause number is frozen once cited.** Rewording a clause is allowed;
changing what a number means is not.
