# Rebuilding the three deliverables to the 0.1.490 standard

*Design record. Written before the work. Not a source of rules — rule prose
stays in `references/`, values in `tokens/`, shipped rationale in `CHANGELOG.md`.*

## What prompted this

The owner rebuilt a deliverable and reported it was almost identical to its
predecessor. Measured: stripped of version numbers the two differ by **two
lines**, the rebuild references **0 of 206** shapes, and uses **4 of 16**
layouts. The build was honest — a source script was re-run — and that is exactly
the finding. A recipe written before the 0.1.457+ refactor reproduces the
document it was written for. Re-running it demonstrates that nothing broke; it
demonstrates nothing about the capability added since.

The same observation had already been made once, in 0.1.490's own E1 report,
and was not acted on. This record exists so it is acted on.

## The decisions

**D1 — Fix the entry points before rebuilding anything.** `SKILL.md` and
`AGENTS.md` list the vendored assets to embed and omit `embed_shapes.py`. An
agent following an entry point cannot reach the shape library, so zero usage was
guaranteed rather than accidental. Rebuilding first would have produced a
document that again used nothing, and the cause would still be in the file the
next agent reads.

**D2 — Form is rebuilt; page order and facts are preserved; titles may be
rewritten only where they are not assertions.** Owner ruling. Two of the three
documents have already been reviewed and accepted, and re-deriving their
storylines would produce different documents that cannot be diffed against what
was accepted. Every title change ships as a list for the owner to check.

**D3 — One document first.** A2UI (15 pages) before `adopting-lumi-style` (30)
and `signal-radar-ops-guide` (34). 79 pages is enough work that a wrong method
applied three times is the expensive failure. A2UI is also the only one
currently failing a gate, so it is where the method is tested hardest.

**D4 — Entry path B, and the trace says so.** The four-beat discussion path
opens on the user's own free statement; simulating it would write
`entry_path=A` for a conversation that did not happen, which is the falsehood
the trace exists to prevent. Path A is deferred to a later round by the owner.

**D5 — A shape is chosen by the relation in the content, and verified against
its rendered preview before use.** `design-rules.md` §4.1 gives the rule;
`assets/shapes/tags.json` carries the relation for each of the 206 units. There
is no comparison-type-to-shape lookup table and this record does not invent one:
the library was curated wrongly twice by reading names as classifications, so
the preview PNG is opened every time. Convention 15 in one sentence.

**D6 — A table is never replaced by a shape.** `design-rules.md` §4 says
comparisons take tables, and line 539 says a table page still wants its visual
weight from a figure or a band *beside* it. That is what `visual_absent`
enforces and it is why GAP-012 needed no owner decision.

## What "the current standard" adds, concretely

Against a pre-refactor document, a document built now must additionally: carry a
genre **and** a storyline; open a trace at storyline agreement and close it with
machine-transcribed verdicts; pass D21 (data contract), D22 (layout vocabulary)
and D23 (font count); run `check_privacy.py --terms`; reach the shape library
through `embed_shapes.py` rather than pasting geometry; and carry a run number
in its filename.

## How it will be verified

Per document: `inspect_layout.py --deliverable` exits 0 with `visual_absent`
silent; D19, D20, D21, D22 pass; shapes referenced > 0 and every one checked
against its preview; ≥6 distinct layouts with the heaviest under 40%; and a
page-by-page diff against the previous build showing identical order and facts,
with every title difference on the change list.

The instrument discipline does not change: when a check fires, decide first
whether the document or the checker is wrong. 0.1.490 produced one of each, and
correct prose is never edited to make a gate go green.

## Risks recorded before the work

Choosing a wrong shape is worse than choosing none — mitigated by the preview
step and by shipping a page-to-relation-to-shape table with the result. New
checker false positives are likely; 0.1.490 found one. And Phase 0 changes rules
by adding a storyline, which is legitimate under convention 2 only because a
real document could not open a trace — a reported defect, not an improvement.
