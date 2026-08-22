# LUMI Storyline Templates

*Serves: **GOAL*** — narrative skeletons serve the reader's decision rather than a constitutional clause; the cover and closing pages inside it serve **P-1** as brand apparatus. · id `ST-1`

> Narrative skeletons — one per storyline in the roster below — plus the
> shared discipline. (Repository language: English only — red line.)

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
| `market-analysis` | the market is this, it is moving that way, and here is what that means for us | Template 7 |
| `gtm` | who we sell to, through what motion, and what has to be true for it to work | Template 8 |
| `status-report` | what was planned, what happened, what is off track, and what is being done about it | Template 9 |
| `due-diligence` | what we examined, what we found, and what would change the answer | Template 10 |
| `product-intro` | what it does, who it is for, and what it deliberately does not do | Template 6 |
| `training-curriculum` | what the reader will be able to do, taught one idea at a time | Template 4 |
| `proposal` | here is a decision, here is what I recommend, what it costs, and what blocks it | Template 5 |
| `pitch-deck` | we built this, it works and grows, the prize is this big, and money is what unlocks it | Template 11 |

Every name in the roster carries a full skeleton. Templates 7–10 were written from the
2026-08 consulting-standards research, which had already documented each
structure section by section before they sat in a backlog for four releases —
the analysis-engine retrospective is what moved them (IDEA-10 closes with
them). The section names below are the industry-typical ones; C5 reports
against them and never gates, and an outline departs from any of them by
declaring the omission.

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

> Second lesson, one review later (D16): the pages above were all present and
> the deck still scored 1 on first-impression — because a skeleton is not an
> arc. The parts had been laid in the order the *package* explains itself, and
> the reviewer asked for the order a *consultant* leads a client:
> `是什么 → 为什么（初衷、痛点）→ 怎么做（方法、步骤、流程）→ 对企业的核心价值`.
> The macro-narrative below is hers, and it is the template.

An external product introduction is one argument told in the reader's
direction, on the **What → Why → How → Value** arc, and it answers **5W+1H**
along the way — Who it is for and When/Where it applies are woven in, not
appendixed. The reader should be able to answer all six from the deck alone.

1. **What** — the first-impression page, and the one the reader must remember:
   what this is in one sentence, who it is for, and the one claim to carry out
   of the room. Not the agenda: the agenda routes, this page asserts.
2. **Why** — the product's reason to exist, in the reader's own terms: the
   problem, the pain it costs, and one verifiable fact per pain. This is where
   the deck earns the right to explain anything.
3. **How** — the solution's shape and its working: the parts, the method, the
   steps, the flow a user actually walks. What it deliberately does not do
   belongs here, not scattered. Evidence pages sit inside How — measured,
   sourced, **and anchored**: every key number stands beside what the reader
   should conclude from it (writing-rules §4 rule 0).
4. **Value** — the summing page: what adopting this is worth to the reader's
   organisation, each value quantified from the evidence already shown, never
   asserted fresh. The arc lands here; a deck that ends on mechanism has
   stopped one page early.
5. **Get started** — four artifacts, and a page missing any of them is a
   missing page, not a thin one: the repository or install link; the install
   step per capability tier; the first command that produces something; and
   the feedback channel. (D16 raised the bar for this page's *form*: it is a
   shop window, not a manual — platform marks, the repository address large,
   one line on the constitution, and a glimpse of real output. See the
   visual-identity note below.)
6. **The ask** — who does what by when. "Pick one document" names nobody and
   no date; "your team runs one build this week and returns the score sheet"
   is an ask.

**The get-started visual identity.** The page shows, not lists: the platform
marks of the agents it names (official logo assets where the package ships
them in `assets/logos/` — a platform whose mark is not shipped gets its name
set in type, never a redrawn imitation), the repository address as the page's
largest value, one sentence on the constitution (`references/PRINCIPLES.md` —
what the skill refuses to do is part of what it is), and one or two thumbnails
of pages the skill itself produced — from this deck or the scaffold, never
from an engagement document (red line 9).

**Agenda rows state value, not contents.** A row that reads "the ban list, the
rule set, the gates: pages 4 to 7" is a table of contents wearing an agenda's
clothes — the row says what the part *establishes for the reader* and why they
should care; page spans are apparatus and sit in the apparatus position.
(Reader review D15: the contents-style rows read as machine-written, and the
page ranges read as emphasis on the wrong thing.)

## The agenda and the takeaway (every deck scenario)

**The agenda renders as the launch sequence** — one row per part: a numbered
dark chip, the part's claim at title weight quoting its opener, a quiet run
line naming the pages (`tokens/lumi-layouts.css` `.launch`; the scaffold emits
it). Adopted at 0.1.519 from an owner review that read the grades agenda as
too quiet for a deck that opens a pitch, piloted and accepted on a real
roadshow build. The energy comes from weight and the lime chip, never from a
louder ground: the agenda stays a body page.

**The launch rows are the agenda's statement, so the agenda carries NO LEDE —
no title, no support line.** A title saying "what this document argues" above rows that already
argue it is the same sentence twice, and an owner review called it redundant
(0.1.521). Set `body stack no-lede` and the rows centre in the page — the
centring is not a separate instruction, it is what removing the lede does:
`no-lede` drops the title's reserved grid row and `.fill` already centres what
it holds. **Remove the lede whole, or not at all**: deleting the title while keeping the `.lede` block
leaves a page reserving a title it does not carry, which `inspect_layout.py`
counts as a check that could not run and reports as NOT SHIPPABLE. D8 then
reports the agenda as missing a support line, correctly and without gating.

This was written as a permission — "may carry no lede" — for four releases, and
two of three conformance agents kept the lede. The scaffold is why: it emitted
`body stack` with a placeholder title reading *"What this document argues, and
where"*, which is the exact redundant sentence the paragraph above asks authors
to delete. Measured on the accepted reference the rows sit 119px below the body
top and 115px above the footer; on a deck that kept its lede, 267 and 99 — the
same page, 2.7 times out of balance. `check_design.py` D35 gates it now.

**The agenda page carries the agenda and nothing else.** Its `.body` holds the
launch sequence in a `.fill`, and optionally the `.lede` above it. No stat band,
no figure, no second block of any kind, and no stylesheet of the page's own —
`check_design.py` D35 gates on it.

This is an owner ruling, from three conformance decks in one round: one put a
stat band on its agenda, one invented an `.agenda-grid` class with a private
`<style>` element to lay it out, and the third was clean. An agenda that also
argues something is two pages sharing one sheet, and the page that routes the
deck is the last one that should need routing itself.

**The agenda quotes the document; it never paraphrases it.** Every claim line
on the agenda — a part title, an item — is a line the deck's own titles say,
verbatim or containing one, and the mechanical way to be right is to derive
the agenda from the page titles at assembly rather than writing it twice.
`check_design.py` D27 gates on this: an agenda line matching no title fails
the document. (Reader review D16, opened with it as its first `严重 BUG`: the agenda's
part titles matched no opener and its items matched no page — the author had
written the deck's story a second time, in different words, and a reader
holding the two against each other trusted neither.)

**Every content page leaves one line behind.** In the external genres a
content page closes with a `.take` — the takeaway a reader could quote in the
elevator: what this page established and why it matters to them. It is a tier
below the callout (`.key` interrupts to change a decision; `.take` closes),
one per page, and `check_design.py` D28 reports the coverage. (Reader review
D16, C6: a deck whose every gate was green read as `无感` — nothing asked to
be remembered, so nothing was.)

## Template 7 · Market analysis · storyline `market-analysis`

The reader is deciding whether and where to play. Seven sections, in the
order a sizing has to be believed before an implication can be:

1. **Market definition** — the scope, drawn: what is in, what is out, and why
   the line sits there. A sizing with no boundary is a number with no noun.
2. **Sizing** — TAM/SAM/SOM, computed **both top-down and bottom-up**, and
   the two reconciled: a sizing that only ever ran one direction has no check
   on itself. The reconciliation gap is stated, not hidden.
3. **Customer segments** — decomposed (AR-1) so the segments are MECE, each
   with the measure that matters, and the segment carrying the story named.
4. **Competitive landscape** — positioned (AR-1): the players on two axes
   the reader cares about, read by quadrant, never a logo zoo.
5. **Customer decision journey** — how buying actually happens, and where in
   it the contest is won.
6. **Growth drivers, trends and risks** — correlated (AR-1): what moves
   demand, with direction of causation stated or plainly unknown.
7. **Strategic implication** — the so-what for THIS reader: where to play,
   how to win, what to watch. A market analysis that ends on the market has
   stopped one page early (the same failure FM-17 names for product decks).

## Template 8 · Go-to-market · storyline `gtm`

Six decisions, each a page or a spread, each closing with the decision taken
rather than the options listed:

1. **Target customer / ICP** — who exactly, and who deliberately not.
2. **Problem and value proposition** — the pain in the buyer's economics,
   and the positioning sentence against the named alternative.
3. **Channels and distribution** — how it reaches them, with the unit
   economics per channel.
4. **Messaging** — what is said to whom; the market's language, not the
   product's (writing-rules, register profiles).
5. **Sales motion and pricing** — the motion, the price metric, and what has
   to be true for the number to hold.
6. **Success measures and timeline** — the metrics that would prove it, with
   dates and owners.

## Template 9 · Status report · storyline `status-report`

**Health and decisions open the document; an activity list never does.**
Eight elements, typically one page:

1. Period, and per-dimension RAG status — **with the RAG thresholds defined
   in the document**, because an undefined amber is a negotiation.
2. A two-to-three sentence summary a skip-level can act on.
3. Completed this period (after the health, never instead of it).
4. Next milestones, dated.
5. **Top three risks, each with a concrete ask** — a risk without an ask is
   a worry, not a report line.
6. Decisions needed, each named to its owner.
7. Budget position.
8. The next checkpoint.

## Template 10 · Due diligence · storyline `due-diligence`

Answer-first, and the answer carries its confidence:

1. **Summary** — the recommendation and the two or three findings that
   drive it, first.
2. **Scope, method, limitations** — what was examined, how, and what was
   not; the limitation section is load-bearing, not an appendix courtesy.
3. **Market** — Template 7's discipline, compressed.
4. **Competition** — positioned, with the target's defensibility argued.
5. **Customers** — concentration and retention measured; the top-N revenue
   share stated.
6. **Financial model review** — the assumptions that carry the valuation,
   each stress-tested.
7. **Risks and synergies** — as a red-flag matrix: severity × likelihood,
   each flag with its diligence trail.
8. **Recommendation** — with bid implications: what the findings do to the
   price, not just to the mood.
9. Appendix — everything that supports and nothing that argues.

## Template 11 · Investor pitch (BP) · storyline `pitch-deck`

Added at 0.1.518 by owner directive (2026-08-18): the package needed a
roadshow BP capability, imported from Y Combinator's published fundraising
guidance the way the consulting standards were — the study is
`references/exemplars/yc-pitch-notes.md` (EX-3), and this skeleton is its
argument shape. **It is a storyline, not a genre**: a BP is external sales
material, so the `sales` tier binds its prose and thresholds; this template
decides the shape, and the shape is: *we built this, it works and grows, the
prize is this big, and money is what unlocks it.*

The reader is an investor deciding whether the next hour of conversation is
worth having — not a customer. The deck is an overview that leaves room for
questions, and it is built vertebrae-first: the page titles are written and
agreed as one 10–15 line argument before any page exists (the storyline
review beat, bound hardest here — the concatenated titles ARE the investment
case). Eleven sections, in the order credibility is earned before it is spent:

1. **Title and one-liner** — the company name and one sentence a layperson
   can picture: concrete and specific, never a vision slogan. A scaffold
   built ahead of real data says so here, on the title page (red line 1).
2. **Traction teaser** — the one hero fact that buys attention for
   everything after it, bridging the one-liner into the problem.
3. **Problem** — how the world works today for the paying customer, told
   concretely with numbers, scoped to the part this product actually
   solves. A problem too big to solve sets up a solution page it cannot
   have.
4. **Solution** — the mirror of the problem page: the same situation with
   the product, side by side, quantified. What exists NOW — futures mixed
   in here get discounted to zero. Customer steps, never screenshots.
5. **Traction in depth** (one to three pages) — the numbers tell one story:
   revenue and growth on the business model, acquisition and unit
   economics, engagement and retention. Trends, not points: monthly or
   quarterly lines with four to six months of history as the floor of
   believability; cumulative-only and double-axis charts are banned by
   name; every number defines what it measures.
6. **Market** — a bottoms-up equation drawn as a labeled arithmetic band:
   prospective customers × value per customer, from the business's own
   numbers (`market-sizing` in frameworks.json). Top-down report figures
   are the named misuse.
7. **Competition** — why 10× better, positioned on axes the investor cares
   about, closing with the moat sentence.
8. **Vision** — how this becomes a very large company; the hypotheticals
   deliberately kept out of pages 1–7, licensed now because everything
   before was real.
9. **Team** — quantified: exits, domain authority, what was built with how
   little. Founders, not an advisor wall; it moves to second position only
   when the team is itself the comparative advantage.
10. **The ask** — the climax, never omitted: the amount, what it buys, and
    where that lands the company in 18–24 months, in traction terms, as
    who-does-what-by-when. The page that shows money is the binding
    constraint.
11. **Appendix** — the anticipated investor questions, each answered with
    data; financial projections; the detailed use of funds. It grows as
    pitches surface new questions.

### The seed / first-meeting register (0.1.521)

Added by owner directive after a real roadshow build: *"for a first
conversation with a seed investor, concepts and figures should be 80 percent —
the investor is there to hear the pitch."* The eleven sections above are
unchanged; this is how they are SET.

**The reader is listening, not reading.** The deck is what the room looks at
while a founder talks, so concepts and figures carry about **80% of every
content page** and the prose is the title, one support line, the labels inside
the drawing, and the takeaway. Say the direction, because it decides what an
author does with it: 80% is a **floor on the drawing**, and therefore a
**ceiling on the prose**. Read as a target it produces an inflated figure
instead of a cut paragraph.

**The layout is part of the rule, not a separate decision.** A `split` page
gives the figure half the area and measures about 43% once the lede and the
takeaway are counted, so it cannot reach this number however the words are
trimmed. A figure-led page is `stack` or `split-wide` with the drawing in the
wide cell. *Provenance: the deck that triggered this rule carried a captioned
figure on all thirteen of its content pages and still read text-heavy — every
page a 50/50 split, 130 words of prose at the median, and the argument carried
in 15-23 word titles rather than in the drawings. `inspect_layout.py` keys the
target on the storyline; `check_prose.py` M15 reports the words from the other
side.*

**Which figure draws which section.** Choose by the relation in the data, never
by how a shape looks — the §4.0 chain is question → framework → shape, and a
BP is where the temptation to reach for a professional-looking diagram is
strongest:

| Section | The relation | The figure |
|---|---|---|
| Problem | a process with a failure point | the customer's path, the break marked on it |
| Solution | before and after on one task | paired states on one axis, quantified |
| Traction | order over time | a trend over four to six periods; cumulative-only and double-axis stay banned by name |
| Market | composition, as arithmetic | the labeled bottoms-up band (`market-sizing`) |
| Unit economics | two quantities at different scale | both marks on one scale, the lever named |
| Competition | position on independent axes | a 2x2 or capability matrix, the empty cell carrying the finding |
| Moat | composition of an asset | the asset as a field, the load-bearing slice separated out |
| Roadmap | order with dependency | milestones with what each reuses; unbuilt drawn as unbuilt |
| Ask | composition against constraints | the uses against the constraint each removes |

**A seed deck's numbers carry their standing.** The ask is in money and the
traction is in measured numbers; every other figure on the page is either
externally sourced or labeled as the business's own measurement. That is red
line 1 in this storyline's dialect, and it is stated here so an author meets it
while writing rather than at the gate.

### Stage decides what leads (0.1.521)

Owner directive: *"for a seed or pre-A conversation the data is not the point;
an unbounded market, a grand narrative and disruption are."* This is a **stage
axis on the ordering below, not a repeal of it.**

At **seed and pre-A** a company has no traction to put first, so demanding
evidence first demands it of something that does not exist. The vision leads,
and the evidence changes job rather than disappearing: it stops proving *this
already earns* and starts proving *we can build what we say* — the corpus, the
gates, the markets already live. From **Series A** the original ordering binds
unchanged, because by then there is something to count.

What does **not** move with the stage: red line 1, the M4 ban list, and the
title contract's information floor. **Bigness is a property of the claim, never
of the adjectives** — "we build and operate robot greenhouses" is licensed at
any size; "reinventing agriculture" is not, at any stage. An unbounded market is
stated the way the study already permits: **a category creator draws analogy
companies as its scale reference instead of a top-down TAM.** That invents no
number, and the bottoms-up band moves to the appendix where it is still
available to the question it answers.

Two boundary rules. **Evidence before vision is the arc's one inviolable
ordering at Series A and beyond** — a deck that opens on the dream has spent credibility it has
not earned, which is FM-16's completeness failure wearing a different coat.
And **the YC floor is not the LUMI ceiling**: the study's design advice
(grey bullets, bare charts) is a clarity floor; LUMI's figure and
composition rules still bind every page, so the deck reads as LUMI telling
the investor story, not as a template filled in.

## Cover and closing pages (every deck scenario)

A deck opens with a **cover** and ends with a **closing page**; the content arc
sits between them.

- **Cover**: wordmark — **the name of the product or subject this document is
  for**, set typographically (no logo file needed). It comes from
  `brands/registry.json`'s `wordmark` field, or from `new_deck.py --wordmark` for
  a subject that is not a registered brand. *This read "the literal string LUMI
  Style" until 0.1.521. That string is the design system's own name, and it was
  never a designed rule — it existed because two generators emitted it, and an
  owner directive of 2026-08-12 wrote prose around the markup. It reached a
  product business plan, where the cover named the stylesheet instead of the
  company, and the owner caught it on the rendered page. The registry has carried
  a per-brand `wordmark` field the whole time and nothing read it.* · document title as the
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
`tokens/lumi-layouts.css`. Its content area takes no chart, no map, no navigation rail, and no icon carrying a second message.
**One oversized subject mark is permitted**: a single silhouette carrying no text
of its own, reversed out of the field, which restates the part's claim in another
modality rather than adding a second thing to the page (0.1.521, owner directive).
It is the part's subject or it is not there. (The footer
keeps its handling marker, inverted with the field.)
The ground runs at its medium tier, and the vector mark stays on the cover and
closing, where the page is the mark's to hold.

**Pacing: about five content pages between openers is the TARGET; six is the
CEILING, and it gates.** The two numbers do different jobs. Five is what to aim
for when the argument has no obvious seam; six is the point past which a deck
has stopped being divided into parts, and `inspect_layout.py`'s `opener_pacing`
fails a deck that goes past it.

Six rather than five, and the reason is about the rule rather than about any
one document. **The first version of this ceiling was set at six because the
accepted reference "runs 6" — and that six was the reference's six appendix
pages after its closing**, counted as an unbroken stretch of argument by a run
computation that did not know a deck ends. Re-measured: the reference's longest
run between seams is five, and this package's passing fixture also runs five.

Six stays because **a ceiling equal to the target is a target.** This repository
has shipped three regressions from that exact confusion — a 3–6 word headline
ceiling read as a target emptied every deck title of its evidence, "short
sentences" drove sentence variance to zero, and a two-line title budget folded
every title in half. One page of headroom is what keeps five a target
(convention 4).

**A deck that is deliberately one undivided sequence declares it**, with
`<body data-parts="none">`, and the seam rate then does not bind. This is the
"unless the author says otherwise" half of the rule, made explicit for the same
reason `data-role="apparatus"` is declared and never inferred: two decks
accepted in 2026-08 are page-for-page conversions that run seven and nine pages
without a seam, and no checker can tell those apart from a deck that forgot its
openers. Making the author say which keeps the exemption auditable and printed
instead of guessed at.

This was reported and not gated for four releases, on the argument that a quota
would force openers where the argument has no seam. What settled it was a
conformance deck that came back with **twelve content pages and no opener at
all**: the report said so, nothing failed, and the deck scored as shippable.
The quota risk is real and the ceiling is set high enough to leave it — five
remains the target precisely so that six is not one.

## Shared discipline

- **Title contract** (every scenario, decks included): every page/section
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
