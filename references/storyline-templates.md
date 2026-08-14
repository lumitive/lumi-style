# LUMI Storyline Templates

> Four narrative skeletons for four output scenarios, plus the shared
> discipline. (Repository language: English only — red line.)

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

## Shared discipline

- **Title contract** (all four scenarios, decks included): every page/section
  title names its **subject** and carries at least one **verifiable fact** — a
  figure, a date, a named mechanism. Length follows the fact; **there is no word
  ceiling**, only the two-line budget in `design-rules.md`.
  **"Topic: assertive subtitle" is the reference form, not the required one.**
  PwC's structure carrying a McKinsey conclusion is what to reach for when a page
  needs a frame, but a document in which *every* title is a colon construction
  reads as generated — twenty identically-shaped headings is itself a tell. Vary
  the frame: a plain assertion, a question the page answers, and a colon title all
  satisfy the contract as long as the subject and the fact are there. M11 caps
  one frame at 60% of titles.
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
- **The red-team pass rides the critic gate** (owner directive 2026-08-09): the
  half of you that built the document — the blue team — argued for it, so before
  delivery the other half reads it as its most skeptical reader — which claim is overstated,
  which number would they check first, which page is designed past what its
  content needs. **Over-design is a finding here, not a virtue**: a device the
  content did not ask for fails this pass the same way an unsupported claim
  does. Each hit is fixed or defended in the delivery note; the document ships
  only after both halves have had it.
