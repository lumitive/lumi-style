# LUMI Storyline Templates

*Serves: **GOAL*** — narrative skeletons serve the reader's decision rather than a constitutional clause; the cover and closing pages inside it serve **P-1** as brand apparatus. · id `ST-1`

> Four narrative skeletons for four output scenarios, plus the shared
> discipline. (Repository language: English only — red line.)

## The storyline vocabulary

*Serves: **P-2**.* · id `ST-6`

A **storyline** answers "what shape is the argument"; a **genre** answers "which
rules bind". They are separate axes and a document carries one of each — a
proposal can be internal analysis or consulting, and that choice decides the
rules, not the shape.

This roster exists because of what 0.1.491 found while closing GAP-013:
`STORYLINES` had been a closed tuple in `scripts/lib/deliverable_registry.py`
since the split shipped, and **not one of its six names appeared anywhere in
`references/`.** A vocabulary an author cannot read is a vocabulary they cannot
choose from, and a name with no prose behind it means whatever the last person
to type it assumed. The `storyline vocabulary` guard now holds this list and
that tuple to each other.

| storyline | the shape of the argument | full skeleton |
|---|---|---|
| `market-analysis` | the market is this, it is moving that way, and here is what that means for us | — |
| `gtm` | who we sell to, through what motion, and what has to be true for it to work | — |
| `status-report` | what was planned, what happened, what is off track, and what is being done about it | — |
| `due-diligence` | what we examined, what we found, and what would change the answer | — |
| `product-intro` | what it does, who it is for, and what it deliberately does not do | Template 6 |
| `training-curriculum` | what the reader will be able to do, taught one idea at a time | Template 4 |
| `proposal` | here is a decision, here is what I recommend, what it costs, and what blocks it | Template 5 |

**Four of the seven have no full skeleton yet**, and that is recorded rather
than hidden: the templates above are organised by genre, which is the older
axis. Writing the missing five is `backlog/ideas-prd.md` work and not a
prerequisite for using the name — a one-line shape is enough to choose with, and
it is more than the six had before.

## Template 1 · Sales / marketing material: Value & Future

> Lesson provenance: a sales deck built around "honesty boundaries" as its spine
> was rejected in reader review — **"Leading with boundaries is wrong; value and
> future are the sales storyline."**

Page arc — the **default** order, not a lock. Add or remove pages freely; reorder
when the argument genuinely requires it and say why in the delivery note. (It used
to read "never reorder", which meant every LUMI sales deck opened the same way and
two decks side by side read as one document.)

1. **Hook** — negation-first definition ("Not another X. Your Y.") + a stat band;
2. **Shift** — why now: external facts the reader can verify without your product;
3. **Value** (layered, one page each) — what the reader gets daily or weekly, made
   concrete in *their* working day (a mock-UI card beats a mechanism description).
   Find the framing from the client's own routine; "what your morning looks like"
   was a worked example that became a stock phrase appearing in every deck, which
   is how a good device turns into a tell;
4. **Evidence** — one memorable comparison pair (A vs B, same task, same ground
   truth);
5. **Scenarios** — two standard stories: one about speed, one about money; a
   shared closing line;
6. **Capability** — why us: numbers already produced in production, not promises;
7. **Future** — product end-state + roadmap (built vs not-built labeled honestly;
   a roadmap is never sold as a commitment);
8. **Journey** — how to start; a low entry bar is honest (deliberately exclude
   heavyweight inputs from the starter list);
9. **Trust base** — one clean page of "what we don't do", serving the value story,
   never the spine;
10. **Action** — three steps for sales + a usage tier (which pages go straight to
    clients);
11. **Feedback page** — embedded scoring table; readers score right after reading,
    no separate file.

## Template 2 · Consulting / client documents: PwC frame, McKinsey punch

- **Titles**: the shared title contract below, in its fullest form — "Master data
  ledger: codes come only from the client's list — the system never derives its
  own";
- **Opening**: scope, method, and findings summary + the one decision the client
  must make;
- **Per-section scope lines** on key sections (sample size / data version /
  recompute-on-update);
- **Charts**: every figure has a conclusion-style title and a source line;
- **Closing statement**: the document's single build-status declaration section;
  when other passages conflict with it, it wins.

## Template 3 · Internal analysis documents

- Conclusion first; explicit so-what lines are allowed here (see discipline below);
- Three claim classes labeled explicitly: measured (with sample size and source) /
  build-time assertion (re-runnable) / inference (labeled as such);
- "What is not built" is a single consolidated section, never scattered.

## Template 4 · Training materials

For enabling a team to *do* something — sell, operate, adjudicate — rather than
to decide something. (Added at the owner's directive, 2026-08-09, from a
training deck reviewed as the reference.)

- **Arc**: what the learner will be able to do and why it matters → the concept,
  one page per idea → the worked example (a real dialogue, a real screen, a real
  document — concrete beats mechanism) → the practice or self-check → the
  reference pages a learner returns to (glossary as `dl.gloss`, the swap list,
  the graded ladder);
- **The swap is this genre's workhorse**: the sentence a person reaches for
  against the one that survives the room;
- **Sourcing follows the consulting rule**: a claim a trainee will repeat to a
  customer carries its source;
- **Checks run with `--genre training`**; the em-dash rule binds as it does for
  sales, because training material is quoted onward by its readers;
- **Geometry**: A4 portrait is the primary geometry — a training document is
  printed, annotated and bound (`design-rules.md` §7). The 16:9 composition is
  still built and verified as the projection edition.

## Template 5 · Proposal · storyline `proposal`

Added at 0.1.491 because a real document could not be traced: an internal design
proposal recommending an adoption decision matched none of the six storyline
names, and `trace.py open` refused it (GAP-013). The refusal was the schema
working; the gap was that a whole document type had no skeleton. A vocabulary
entry without a template here is a name with nothing behind it, so the template
comes first and the tuple follows it.

**It is a storyline, not a genre.** A proposal can be internal analysis or
consulting; that axis decides which rules bind. This one decides the shape of
the argument, and the shape is: *here is a decision, here is what I recommend,
here is what it costs, and here is the one thing that blocks it.*

- **The recommendation is the first content page**, stated as a decision someone
  can take or refuse — not "options for consideration". Everything after it is
  support, which is the answer-first rule doing its ordinary work;
- **What the proposal deliberately leaves out** is a single consolidated
  section, borrowed from Template 3 for the same reason: an omission scattered
  through the document reads as an oversight, and an omission stated once reads
  as a decision;
- **The strongest objection is named and answered on its own page.** A proposal
  that answers no objection has not been reviewed, it has been written;
- **Sequencing separates the cheap steps from the expensive ones**, so a reader
  can approve part of it;
- **The closing names which decisions block the release and which do not.**
  Where a proposal carries several, exactly one is usually load-bearing and
  saying which is the most useful sentence in the document;
- Claim classes are labelled as in Template 3 when the genre is internal
  analysis: measured / build-time assertion / inference.


## Template 6 · Product introduction · storyline `product-intro`

> Lesson provenance: the first product-intro built from the five-word checklist
> alone passed every machine gate and came back from its blind review scored
> **1 on completeness and 1 on actionability** — the reviewer could not find a
> page saying what to remember, and "completely no action a reader could take."
> The words of the checklist were satisfied; the substance each word stands for
> was not. This skeleton is what the words stand for.

An external product introduction answers **5W+1H** before it argues — What it
is, Why it exists, Who it is for, When and Where it applies, How it is adopted
— and the reader should be able to answer all six from the deck alone.

1. **Overview** — the first-impression page, and the one the reader must
   remember: what this is in one sentence, who it is for, and the one claim to
   carry out of the room. If the reader retains a single page, it is this one.
   Not the agenda: the agenda routes, the overview asserts.
2. **Problem** — the pain in the reader's own terms, with one verifiable fact.
3. **What it is** — the product's shape and parts; what it deliberately does
   not do belongs here, not scattered.
4. **Evidence** — measured, sourced, **and anchored**: every key number stands
   beside what the reader should conclude from it (writing-rules §4 rule 0).
5. **Get started** — four artifacts, and a page missing any of them is a
   missing page, not a thin one: the repository or install link; the install
   step per capability tier; the first command that produces something; and
   the feedback channel. An adoption ask without the how is C6's 1-score.
6. **The ask** — who does what by when. "Pick one document" names nobody and
   no date; "your team runs one build this week and returns the score sheet"
   is an ask.

**Agenda rows state value, not contents.** A row that reads "the ban list, the
rule set, the gates: pages 4 to 7" is a table of contents wearing an agenda's
clothes — the row says what the part *establishes for the reader* and why they
should care; page spans are apparatus and sit in the apparatus position.
(Reader review D15: the contents-style rows read as machine-written, and the
page ranges read as emphasis on the wrong thing.)

## Cover and closing pages (every deck scenario)

A deck opens with a **cover** and ends with a **closing page**; the content arc
sits between them.

- **Cover**: wordmark — the literal string **"LUMI Style"** (typographic, no
  logo file needed; the string was carried only by template markup until an
  owner directive fixed it in prose, 2026-08-12) · document title as the
  page's single statement · one-line subtitle saying who it is for and what it
  answers · a meta strip as the **`.attrs` key/value block** (audience / date /
  version / classification) — the key bold and uppercase, the value **one line**,
  truncating rather than wrapping, so a value that overruns gets shortened
  (this bullet said "spec-band form" while the shipped skeleton emitted
  `.attrs`, and the two drifted until an owner review caught the unstyled
  result; `.spec` remains the in-page strip) · **and exactly one vector mark.**
  The colophon lives on the CLOSING page only — the cover carried one too
  until a reader rejected the duplication, and this list kept it for
  releases after SKILL.md moved it. Body copy and
  photography stay out. **The default mark is the LUMIVATE field globe**
  (`assets/brand/lumivate/globe-field.svg`, locked), embedded live — `data-globe`
  plus the inlined runtime, which the scaffold does for you — so it rotates,
  with reduced-motion respected and the static frame as the fallback (owner
  directive, 0.1.442 review: a shipped cover carried a fresh anonymous render
  where the brand belonged, and it did not turn). It is sized as a field the
  typography sits against, not as a spot illustration.

  **The brand mark is identity; a replacement mark is a claim.** The field
  globe carries LUMIVATE's own field — its blocs, lanes and codes — the way a
  logo carries a company's business, and its `aria-label` says so; it claims
  nothing about the document. A document may instead render its own subject as
  geometry, and THAT mark must say something true about the document: a globe
  on a deck about one supply chain shows that chain's nodes and routes and
  nothing else. Geography implies coverage, so a region drawn is a region
  claimed: mark the built ones in accent, the empty ones as hollow dashed
  rings, and the out-of-scope ones muted. Decoration that implies reach the
  engagement does not have breaks red line 1 as surely as a sentence would.

  *Provenance:* this rule read "No charts, no body copy — the cover is typography"
  through 0.1.337. The ban existed because the skill had no photo library, and it
  was applied to every kind of image rather than to photography, which is what
  the risk actually was. A reader called the resulting covers unprofessional and
  asked for vector geography. Vector geography needs no photo library, so 0.1.338
  ships it instead of banning it.
- **Closing**: one closing statement that echoes the action page. A short
  imperative ("Let the numbers decide.") is one option, not the required form —
  a punchy four-word command is a recognized AI-deck ending, and it is weaker than
  naming the concrete next step and who owns it · a one-sentence recap of the ask · contact
  slots in the same `.attrs` block the cover uses · **and the same single vector mark as the cover**,
  under the same truth test — a cover and a closing are the same kind of page,
  set the same way (`cover-grid` in `tokens/lumi-layouts.css`), and the closing
  restates where the document stood, so its mark repeats the cover's geography
  rather than introducing a new claim. **Contact details: real ones from the user, or none at all.**
  Inventing an email address is inventing a fact. When the user supplies no
  contact details and cannot be asked, OMIT the contact slots entirely and name
  the owning role in prose ("the programme board owns the go/no-go") — do not
  emit `[TO FILL]` slots: D14 gates a finished document at zero placeholders,
  and a template that mandates brackets while the gate bans them fails every
  compliant author (the contradiction a conformance run proved, GAP-001).
  `[TO FILL]` belongs only in a draft the user will fill BEFORE delivery.
  End with the colophon (owner · date · "built with lumi-style X.Y.Z" · the
  number-discipline line).
- **Version lockstep**: by default a deliverable's version number **is** the
  lumi-style version that produced it. When the user assigns a document-edition
  sequence instead (e.g. v1.01), the filename and masthead carry the document
  edition and the colophon still records "built with lumi-style X.Y.Z" — the
  producing-skill version is never lost either way.

## Part openers (every deck scenario)

A deck's content arc is broken into named parts, and **every part boundary gets
an opener page**: the lime field carrying the part label, one claim at display
scale saying where the reader is, and one run line saying what the next pages
argue — the `.openpart` / `.openclaim` / `.openrun` composition in
`tokens/lumi-layouts.css`. Nothing else sits in its content area: no figure,
no map, no icon (the footer keeps its handling marker, inverted with the
field).
The ground runs at its medium tier, and the vector mark stays on the cover and
closing, where the page is the mark's to hold.

**Pacing: about five content pages between openers is a target, not a floor and
not a gate.** `inspect_layout.py` reports the opener count and the longest run
of content pages between openers; a run that stretches far past the target is a
prompt to ask whether the argument has an unmarked seam, and the author answers
it — in the page structure or in the delivery note — never a checker. Read as a
quota, the same number would force openers where the argument has no seam and
manufacture the uniformity the parallel-structure rule exists to suppress.

## Shared discipline

- **Title contract** (all four scenarios, decks included): every page/section
  title names its **subject** and carries at least one **verifiable fact** — a
  figure, a date, a named mechanism. Length follows the fact; **there is no word
  ceiling**, only the two-line budget in `design-rules.md`.
  **"Topic: assertive subtitle" is the reference form, not the required one.**
  PwC's structure carrying a McKinsey conclusion is what to reach for when a page
  needs a frame, but a document in which *every* title is a colon construction
  reads as generated — twenty identically-shaped headings is itself a tell. Vary
  the frame: a plain assertion, a question the page answers, a colon title, a
  number-led title and a verb-led opening all satisfy the contract as long as
  the subject and the fact are there — those five are exactly the frames the
  checker counts (`TITLE_FRAMES` in check_prose.py), and M11 caps any one of
  them at 60% of titles. The five were code-only until a ten-round build
  discovered them from the failure instead of from any rule.
- **Information floor**: a title that states only a contrast ("codes, not words"),
  only a slogan, or only a section label ("the end-state") is not a title.
  Contrast is a *lead-in*, never the whole title — keep the evidence that earns
  it: "Codes, not words: same task, different criteria, 18× recall gap".
  (Lesson: a word ceiling amputated the evidence clause from every title in a
  deck; what survived was the rhetorical shell, and readers correctly called it
  AI-flavored.)
- **Titles-only test**: concatenate all titles — they must read as a complete
  argument, or rewrite them.
- **So-what is a writing discipline, not a page element**: sales/client material
  never carries a "→ so-what" label — the takeaway lives in the title and the
  figure title. Only internal analysis documents keep explicit so-what lines.
  (Lesson: pasted-on labels correlate poorly with content; they visualize the
  failure of the discipline.)
- **Comparisons always use tables** (columns = options, rows = dimensions). What
  is banned is the bullet *pileup* — a page of fragments standing in for an
  argument — **not the list**. A numbered list is the right form for a sequence a
  reader must perform in order; a bulleted list is right for a small set of
  criteria that must all hold; a dashed list is right for options that are
  alternatives. These are clearer than the same content buried in prose and far
  easier to remember, which is the whole point of enumerating.
  *Provenance: the ban was read as a ban on lists, and a 27-page deck shipped with
  **zero** `ul` or `ol` elements — M10 could not even be computed. Prose that
  should have been three numbered steps was three sentences in a paragraph.*
- **Every page answers one question a real reader would ask** — write that
  question down before writing the page;
- Parallel structure **only where it aids comparison** — a genuine enumeration
  (three options scored on the same dimensions) earns matching shapes. Consecutive
  value or capability pages do not: forcing "Factor 1: X" / "Factor 2: Y" across a
  run of pages manufactures the uniformity readers read as machine-written. When in
  doubt, let sibling pages differ;
- **Pre-delivery critic gate** (structure before polish): four checks
  (structure / rigor / so-what / completeness) → Green (ship) / Yellow (fixable —
  don't ship as-is) / Red (the argument collapsed) → Top 3 fixes (what's wrong +
  how to fix) → name one strength that must be protected.
- **The conflict exit** (`PRINCIPLES.md` §3): if two MUST clauses cannot both be
  satisfied after the rule has been read as precisely as it can be — not merely
  when one is inconvenient — **record the conflict and the reasoning, do not
  emit, and hand it to a person.** It is rare by construction, and a refusal is
  evidence that a rule needs redrafting rather than a way to stop work: name
  both clauses and what each demanded.
- **The red-team pass rides the critic gate** (owner directive 2026-08-09): the
  half of you that built the document — the blue team — argued for it, so before
  delivery the other half reads it as its most skeptical reader — which claim is overstated,
  which number would they check first, which page is designed past what its
  content needs. **Over-design is a finding here, not a virtue**: a device the
  content did not ask for fails this pass the same way an unsupported claim
  does. Each hit is fixed or defended in the delivery note; the document ships
  only after both halves have had it.
