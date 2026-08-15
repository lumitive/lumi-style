# What lumi-style is — product definition

Date: 2026-08-16 · Status: current · This is P2.1 of
`2026-08-15-principles-and-evals-refactor-design.md`.

Unlike the other files in `specs/`, this one is **not** a record of a past
decision. It states what the product is, and it is expected to be read before
any of the design records. It says nothing about how the rules work — that is
`references/` — and nothing about how the repository is maintained — that is
`CLAUDE.md`.

## One sentence

**lumi-style turns a request and its evidence into a business document a
consultant would put their name on, in the LUMI design language, with every
claim traceable and every check run.**

## Who it is for

Not "a designer" and not "an engineer". The user is whoever has to produce a
document that will be read by someone whose decision depends on it: a founder
writing to a board, an analyst writing to a client, a team lead writing a
status report that has to survive being forwarded.

What they have in common is that the document is not the work — the decision
is — and the time spent on the document is time taken from the decision. That
is the constraint the whole product is shaped around.

## What it does, in the order the user meets it

1. **It asks before it writes.** On the discussion path the user states the
   situation first and is not interrupted; the agent then leads with questions
   that may probe structure and evidence but never decide the conclusion; then
   it proposes; then the storyline — titles, order, the logic joining them —
   is agreed before anything is built.
2. **It builds in one design language.** Palette, type, layout and figure
   vocabulary come from `tokens/` and `references/`, not from the model's taste
   on the day.
3. **It checks what can be checked.** Prose metrics, design diagnostics,
   rendered layout, privacy — machine-written verdicts, never a self-report.
4. **It says what it could not check.** An agent that cannot run the checks
   lists what it owes rather than calling anything verified.

## What it refuses to do

- **Invent.** A number without a source does not ship, and an illustrative
  value ships labelled as one.
- **Sign.** The byline is a person's, and money and safety conclusions are made
  by a person.
- **Pass off structure as quality.** Completeness is reported, and a gap may be
  declared; it is never gated, because structural compliance does not predict
  whether a document is any good.
- **Improvise the brand.** A deliverable is recognisably from one house.

## How to tell whether it is working

Five criteria, all stated as outcomes rather than as work done:

| | Criterion |
|---|---|
| **K1** | The model matrix runs — two model tiers × three effort levels — and produces a quality column and a cost column together, with differences inside a tier explainable |
| **K2** | The evidence ledger is healthy: every real build leaves an anonymous trace, the three ledgers are kept, every shipped change went through draft → ratification → record, and the share of releases fixing drift falls measurably. **Self-falsifying clause**: if documents from the discussion path do not score better than documents from the template path, the four-beat design itself goes back for review |
| **K3** | Consultant standard: each of the three rule tiers has an accepted reference; the agreement study has joinable data and has produced a disagreement list; C-scores do not regress across two consecutive releases |
| **K4** | **Measurable** — per-phase timing lands, budget is counted per content page, and the efficiency board admits only runs that passed the quality line. **Not "cheaper"**: that claim is not available until a baseline exists, and it has a falsification condition attached |
| **K5** | The early proof point is not worse than the level the product had reached before the refactor. If it is, the plan stops rather than continues |

## What it is not

**Not a slide generator.** The output is an argument that happens to be
paginated. A deck whose pages are pretty and whose titles do not read as a
continuous argument has failed the thing this product is for.

**Not a writing assistant.** It does not improve prose it was handed. It builds
a document from evidence, and its prose rules exist to keep that document out
of the register that makes a reader stop believing it.

**Not a template library.** Templates are a checklist applied at the end, not a
starting point — a professional's principled deviation from a template is
exactly what a template-first pipeline would penalise.
