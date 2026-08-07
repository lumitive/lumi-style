# Changelog

Rule revisions come only from review retrospectives (divergence ≥2 → retrospective
→ revision), recorded here with a version bump.

## 1.7.0 — 2026-08-07

Two operational gaps, both found by asking why a step kept costing time.

**The display face now ships with the skill.** `design-rules.md` has required
D-DIN to be embedded since 1.2, and 1.2 itself shipped with the face declared but
not vendored, so it rendered nothing. The rule was right and the package could not
satisfy it: every deliverable's author had to find the font again. The two woff2
files (43 KB together) now live in `assets/fonts/` with their OFL text, and
`scripts/embed_font.py` prints the ready `@font-face` block or verifies the files
with `--check`. Confirmed the vendored files produce base64 byte-identical to the
already-shipped deck, so nothing about existing deliverables changes. CI checks
the sizes, because a silently swapped face would alter the metrics of every
document that embeds it. Note that `.gitignore` blocks font formats as
deliverable output and now carries an explicit exception — the face is part of the
design language, not a render.

**Waiting on CI is now bounded and outage-aware.** During the 2026-08-06 Actions
incident, open-ended polling consumed most of a working session and merged
nothing: runs queued for six minutes, were cancelled, were re-run, queued again.
`scripts/ci_wait.sh` asks the status page *before* waiting and short-circuits when
Actions is degraded, otherwise checking three times over about four minutes and
then stopping. The protocol behind it is recorded in `CLAUDE.md`: correctness is
answered locally by `check_repo.py` in seconds, CI only unlocks the merge button,
a cancelled run is a symptom rather than a verdict, and re-running into a declared
incident adds to the load causing it.

## 1.6.0 — 2026-08-07

Internal review: sales and marketing deliverables still read as AI-written. The
`humanizer` skill (github.com/blader/humanizer, MIT) was evaluated as a candidate
fix and its rules adapted rather than the skill adopted — LUMI keeps one source of
truth and no runtime dependency. See `NOTICE` for attribution and scope.

The evaluation found three causes, and humanizer only addresses the first:

1. **Coverage was lexical, not structural.** The `[en-output]` ban list was a
   five-item seed while English had been the default output language since 1.3.0,
   and the "delete filler phrases" move shipped without a list of filler phrases.
2. **The de-AI-flavor pass was an orphan.** It is the repo's only real
   anti-AI-flavor machinery and no workflow step, checklist, gate, or metric
   invoked it; it was absent from `prompts/lumi-style-core.md` entirely, so Kimi
   and DeepSeek users got none of it. The repo already knew the lesson — "a pass
   in the pipeline beats good intentions" — and had applied it only to punctuation.
3. **The mandated forms were themselves the tells.** A deliverable could satisfy
   every rule, score clean on all eight metrics, and still read as machine-written,
   because compliance is what made it read that way.

Changes:

- **[en-output] ban list grown from 5 entries to 8 grouped classes** — significance
  inflation, promotional register, AI high-frequency vocabulary, filler with its
  fixes, authority tropes, signposting, fake-candid openers, closing filler.
- **De-AI-flavor pass is now mandatory and gated**, with seven structural moves
  added (em/en dash ban for en sales/marketing, rule-of-three, list-shape variety,
  inline-header bullets, manufactured punchlines and aphorism formulas, boldface
  inflation, synonym cycling) and a two-pass audit: ask the draft what makes it
  obviously AI-generated, then fix what you named, and confirm no fact was added.
- **New section 6b, de-translationese** — sales and marketing material is now
  authored in English with Chinese translated from it, which imports a second
  failure mode. Precedent: 1.1.0 translated the Chinese rule "not X, but Y" into
  "Not X. Y.", models rendered it back into Chinese, and the round trip amplified
  until readers called the decks AI-flavored.
- **Conflicts with LUMI house style resolved in humanizer's favor**: negation-first
  openings retired as a mandated signature and stripped of their de-flavor
  exemption; the three canned responsibility frames reduced to a disclosure
  requirement phrased in the sentence's own words; the "short sentences" mandate
  replaced by a variance requirement; the accent-word bold made optional.
- **Structural loosening** — the colon title is the reference form, not the
  required one (capped at 60% of titles by M11); sibling-page parallelism only
  where it aids comparison; one to three support sentences of visibly differing
  length per page; the page arc is a default order rather than "never reorder";
  the stock metaphor and the imperative closing line are no longer mandated.
- **M8 is now two-tailed** (overlong share plus a sentence-length variance floor)
  and never waived for decks: it used to count only long sentences, so uniformly
  clipped prose — the dominant modern AI tell, and what the voice rule itself
  mandated — scored a perfect zero. **M9-M11 added**: em dashes, triad rate,
  title-shape uniformity.
- **`scripts/check_prose.py` added.** M1-M8 were called "scriptable" for six
  versions with no script in the repo. This measures M4 and M8-M11 on a real
  deliverable, and reports a file it could not parse as *unmeasurable* rather
  than clean — a linter that says "pass" when it read nothing is worse than none.
- `scripts/emergency_merge.sh` added: a documented, self-restoring path to merge
  when GitHub Actions cannot run the required check. `.gitignore` now also blocks
  deliverable exports and renders — this repo holds the skill, never its output.
- **CI now covers `scripts/`** (`py_compile` plus `bash -n`). It had none, so a
  syntax error would have shipped silently — including into the emergency path
  that runs precisely when CI is unavailable.
- **Fifth guard: ban-list parity.** `check_prose.py`'s phrase list is a second
  copy of §2 and was held to it only by a comment saying "change both together".
  `check_repo.py` now parses §2 and the script's declarations (by AST, so the
  guard never executes the other script) and fails when they disagree in either
  direction. Phrases that cannot be matched mechanically — `rich (figurative)`,
  `key (adjective)`, "adjective stacks in place of numbers" — must now be listed
  in `NOT_MECHANIZED` with a reason, which turns the gap between what the rules
  ban and what the machine can enforce from invisible into documented.

Review round on this release, recorded because the findings were real:

- The emergency merge script executed code supplied by the pull request. Copying
  a trusted `check_repo.py` over the PR's copy was not enough — the script's own
  directory is `sys.path[0]`, so a planted `scripts/json.py` hijacks an import
  and runs. Reproduced, then fixed with `PYTHONSAFEPATH=1` (Python 3.11+ now
  required) plus fork refusal and a merge-ref parent check.
- Its restore path could leave `main` unprotected while exiting 0, and a signal
  handler that returned instead of exiting let a killed merge report success.
  Distinct exit codes now separate "refused", "check failed", "could not run the
  checker", "merge failed", and "protection still off".
- `check_prose.py` matched multi-word entries as unanchored substrings and single
  words with word boundaries — exactly backwards. It flagged "deserves as much"
  and a finance "leverage ratio" while missing "leveraging" and "fostering", the
  actual tells. Every entry is now an explicit anchored pattern with its
  inflections, and ordinary business words are qualified rather than banned.
- Empty, non-UTF-8, and unparseable files reported "all metrics pass"; `--json`
  never evaluated a threshold and always exited 0; HTML markup merged into
  27-word pseudo-sentences that inflated the rhythm metric. All fixed and each
  verified against the failing case.

## 1.5.0 — 2026-08-07

Reader review of two shipped sales decks (zh + en, V1.3.0) against their own
V4.1 predecessor: "page titles suddenly became very short and AI-flavored,
overusing the it-is-X-not-Y contrast — this violates the PwC title principle the
skill was founded on." Measured: title length fell from a median of ~29 CJK
characters to ~8; display type rose 29.8pt → 37.4pt; every evidence figure
(18×, 4,557, 194, 29,845) vanished from the title line.

Root cause: 1.2.0 answered a review complaint about *visual* divergence from
spacex.com by writing a *writing* rule — "a giant short headline (3–6 words)" —
into design-rules §3, without reconciling it against the PwC title contract that
already existed in storyline-templates. The word ceiling then collided with the
still-standing requirement that a title be a complete assertion carrying the
takeaway, and with the negation-first signature's explicit de-flavor exemption;
in ~6 CJK characters the only form that satisfies all three is a bare antithesis.

- **The word ceiling is removed.** design-rules §3 now defers to the title
  contract; headline length follows the fact, bounded only by the two-line budget.
- **Title contract promoted to shared discipline** (was scoped to the consulting
  template, so sales decks had no title rule at all): "Topic: assertive subtitle",
  naming a subject and carrying a verifiable fact.
- **Information floor added**: a bare contrast, a slogan, or a section label is
  not a title. Contrast is a lead-in that must keep the evidence that earns it.
- **Two-line guard rewritten**: display titles are a size *range*; a long title
  takes the lower end before any word is cut. The old "shorten the title, never
  shrink the type" left cutting words as the only legal move once titles went
  giant, and the evidence went first.
- **Negation-first scoped** to the cover and hook, once per document; it is not a
  page-title form.
- **M1 is never waived for decks.** It had been marked "distorted for slides —
  advisory", which removed the only metric that measures this exact failure; the
  regression ran three versions unmeasured.

## 1.4.0 — 2026-08-06

Reader review of the anchor document (five annotated screenshots):

- Long-document callout hierarchy: three tiers (tinted+bordered key conclusion /
  left-rule guidance / muted note) — one uniform left-rule flattens the page.
- Charts: legend at the top right above the plot; two-part caption anatomy
  ("Figure N · Name" centered bold, description left-aligned at figure width).
- Flow-diagram shape vocabulary: parallelogram=I/O, rectangle=process,
  diamond=decision, stadium=terminal, dashed=not built — shapes carry semantics.
- Figure vocabulary ⊆ body vocabulary: body renames must sweep figure labels.
- Deliverables state results, not process: revision stories live in the ledger.
- Version lockstep refined: a user-assigned document-edition sequence (v1.01)
  owns filename+masthead; the colophon still records the producing skill version.

## 1.3.0 — 2026-08-06

Reviewer-driven round (five inputs from deck review):

- **Light-first**: the default canvas is near-white with the ink ladder; dark is
  applied only on explicit request via one `body.dark` override block. Both
  palettes share one token structure; literal colors in components or inline
  SVG are defects. Full dual-palette token set in `tokens/` (lumi-theme.css
  rewritten to v1.3.0; design-tokens.json restructured as palette.light /
  palette.dark).
- **American English by default**: when the user does not specify a language,
  output is American English (spelling, idiom, double quotes, serial comma);
  writing-rules §0 rewritten.
- **Icon-alignment guard** (from a reported alignment bug): an icon on a text
  line lives in a flex container with align-items:center — never a bare inline
  SVG nudged with vertical-align; icon ≈ 1.4× the accompanying text size.
- **Version lockstep**: a deliverable's version number is the lumi-style version
  that produced it; carried on the cover meta strip and closing colophon.
- **Cover and closing templates**: every deck opens with a typographic cover
  (wordmark / title / meta strip) and ends with a closing page (closing
  statement / recap / contact placeholder slots `[TO FILL]` — inventing contact
  details is inventing a fact / colophon). Added to storyline-templates.

## 1.2.0 — 2026-08-06

Direction change, reviewer-driven: "the output diverged from spacex.com — why?"
The 1.x fusion ("skeleton only, keep rounded type and light canvas") kept too
much consulting-deck idiom, and the one adopted SpaceX element (D-DIN in the
data voice) never shipped because the font was declared but not vendored.

- design-rules: decks are **dark-first** (near-black canvas, cold-white ink
  ladder); light canvas stays for long documents.
- design-rules: **D-DIN takes over** as the single Latin face; ALL-CAPS
  display titles at weight 400; rounded faces retired from decks; vendor and
  embed the font — a declared-but-unshipped face renders nothing.
- design-rules: one-statement-per-screen sharpened (giant short headline, one
  support sentence, one centerpiece, thin footer); hairline rows over card
  boxes on dark canvases.
- Accent green lifts to a dark-canvas form (#7C9F63); red text on black uses a
  lifted form while fills keep the seal red.

## 1.1.2 — 2026-08-06

- design-rules: added three field-tested guards from a reader-reported bug round —
  two-line title budget (shorten, never shrink); icon size independent of
  container scaling (blanket `svg{width:100%}` rules must exclude icons; an
  accidentally-stretched icon is not a design choice); in-row card alignment
  constraints (equalized title heights, stat numbers stacked above labels).
- design-rules: new "Verification matrix" section — language axis × viewport axis
  (design / print / short-laptop); footer rule and page number must be visible at
  every matrix point; height-based media queries as the mechanism. Supersedes the
  standalone localization guard (merged in).

## 1.1.1 — 2026-08-06

- Added the localization layout guard to design-rules: translated text runs
  30–50% longer/shorter — re-inspect every fixed-width container page by page
  after any localization pass. (From the English-deck audit: seven layout defects
  found — a wrapped stat band, ragged stat labels, and three SVG text overflows.)

## 1.1.0 — 2026-08-06

- **Repository language: English only — declared a red line.** LUMI serves a
  global audience; all rule prose, entry points, adapters, tokens, and this
  changelog are now English. Chinese strings remain only as rule data for
  Chinese-language output (banned phrases, punctuation patterns, collocation
  examples).
- Rules generalized to be output-language-aware: language-agnostic core
  (facts / voice / structure / charts) + a marked [zh-output] module; an
  [en-output] banned-phrase seed added.
- New field-tested layout guard in design-rules: right-anchored labels on
  full-width bars must anchor inside the fill (white-on-white invisibility bug,
  caught in per-page inspection).

## 1.0.0 — 2026-08-06

Initial release. Rules distilled from six rounds of real delivery polishing and a
first round of reader review on a consulting engagement's deliverables:

- Terminology red lines: no coined Chinese; direct English for concepts without
  an established Chinese term; substring-collision exemptions;
- Banned AI-tell phrases (with the "sales enablement" fixed-collocation lesson);
- Number discipline: sourcing, illustrative labels, repo-wide retraction with
  retirement notes for unreliable citations;
- The "value & future" sales storyline (boundaries converge to one trust page) —
  from a reader review scoring H5=2;
- "So-what is a writing discipline, not a page element" — from a reader review
  scoring H1=1;
- Plain-language scoring anchors ("anchors must be written in the reviewer's
  language") — from a reader review scoring H2=1;
- Five chart iron rules and form selection (partly adapted from
  enterprise-ai-skills, localized);
- Visual tokens v2: space-gray canvas + natural green single accent + China red
  warnings; layout skeleton informed by SpaceX/Tesla research (transparency
  ladder, dual-voice typography, cold-white dark canvas).
