# LUMI Storyline Templates

> Three proven narrative skeletons for three output scenarios, plus the shared
> discipline. (Repository language: English only — red line.)

## Template 1 · Sales / marketing material: Value & Future

> Lesson provenance: a sales deck built around "honesty boundaries" as its spine
> was rejected in reader review — **"Leading with boundaries is wrong; value and
> future are the sales storyline."**

Page arc (add/remove pages, never reorder):

1. **Hook** — negation-first definition ("Not another X. Your Y.") + a stat band;
2. **Shift** — why now: external facts the reader can verify without your product;
3. **Value** (layered, one page each) — what the reader gets daily/weekly, made
   concrete as "what your morning looks like" (a mock-UI card beats a mechanism
   description);
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

- **Cover**: wordmark (typographic, no logo file needed) · document title as the
  page's single statement · one-line subtitle saying who it is for and what it
  answers · a meta strip in spec-band form (audience / date / version /
  classification) · a colophon line ("built with lumi-style X.Y.Z"). No charts,
  no body copy — the cover is typography.
- **Closing**: one closing statement (an imperative that echoes the action page,
  e.g. "Let the numbers decide.") · a one-sentence recap of the ask · contact
  slots in spec-band form. **Contact details are placeholder slots by design**
  (`[TO FILL]`) unless the user supplies real ones — inventing an email address
  is inventing a fact. State on the page that a bracketed version must not ship.
  End with the colophon (owner · date · "built with lumi-style X.Y.Z" · the
  number-discipline line).
- **Version lockstep**: by default a deliverable's version number **is** the
  lumi-style version that produced it. When the user assigns a document-edition
  sequence instead (e.g. v1.01), the filename and masthead carry the document
  edition and the colophon still records "built with lumi-style X.Y.Z" — the
  producing-skill version is never lost either way.

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

## Shared discipline

- **Title contract — "Topic: assertive subtitle"** (all three scenarios, decks
  included): PwC's structure carrying a McKinsey conclusion. Every page/section
  title names its **subject** and carries at least one **verifiable fact** — a
  figure, a date, a named mechanism. Length follows the fact; **there is no word
  ceiling**, only the two-line budget in `design-rules.md`.
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
- **Comparisons always use tables** (columns = options, rows = dimensions);
  bullet pileups are banned;
- **Every page answers one question a real reader would ask** — write that
  question down before writing the page;
- Parallel structure: sibling pages share sentence shape ("Factor 1: X" on page 5
  forces "Factor 2: Y" on page 6);
- **Pre-delivery critic gate** (structure before polish): four checks
  (structure / rigor / so-what / completeness) → Green (ship) / Yellow (fixable —
  don't ship as-is) / Red (the argument collapsed) → Top 3 fixes (what's wrong +
  how to fix) → name one strength that must be protected.
