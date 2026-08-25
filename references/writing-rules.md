# LUMI Writing Rules

> The single source of truth for LUMI's output writing style. Self-contained — no
> third-party skill dependencies. Every rule traces to a real delivery iteration or
> reader review; revisions go through CHANGELOG.
>
> **Repository language: English only (red line — LUMI serves a global audience).**
> Chinese strings appear below *only as rule data* for Chinese-language output;
> they are examples, not document prose.

## Contents

- [0 · Output language](#0--output-language)
- [1 · Terminology red lines](#1--terminology-red-lines)
- [2 · Banned AI-tell phrases (hard block)](#2--banned-ai-tell-phrases-hard-block)
- [3 · Punctuation and glyphs [zh-output]](#3--punctuation-and-glyphs-zh-output)
- [4 · Number discipline (honest metrics — all languages)](#4--number-discipline-honest-metrics--all-languages)
- [5 · Voice (the LUMI register)](#5--voice-the-lumi-register)
- [6 · De-AI-flavor pass (mandatory, pre-delivery)](#6--de-ai-flavor-pass-mandatory-pre-delivery)
- [6b · [zh-output] De-translationese pass](#6b--zh-output-de-translationese-pass)
- [7 · Fact red lines (outrank every style rule)](#7--fact-red-lines-outrank-every-style-rule)

## 0 · Output language

*Serves: **GOAL**.* · id `WR-1`

**Default: American English.** When the user does not specify a language, LUMI
writes in American English — spelling (-ize, -or, -og: organize, color, catalog),
idiom, and punctuation (double quotation marks with periods and commas inside;
the serial comma). Dates in prose follow the client's convention; dates in data,
filenames, and version strings stay ISO (YYYY-MM-DD) in every language.

When the user specifies a language, produce in that language. Rules in sections
1–7 are language-agnostic unless marked **[zh-output]** (Simplified Chinese
deliverables only) or **[en-output]**.

**A deliverable DECLARES the language it is in.** An HTML document carries
`lang="en"` or `lang="zh"` on its root element; a file may say it in its name
instead (`deck.en.html`, `deck.zh.html`). This is not bookkeeping: M12 is the
check that catches Chinese a reader can see in an English deliverable, and it
has nothing to compare against when the document will not say what it is. A
document that carries Chinese and declares nothing — or declares a language
this package does not produce — is reported **blind**, which fails the run in
the same way a hit does. Silence is not an exemption; it is the cheapest one
there would be.

**American English is the default, and another language is asked for.** The
scaffold emits English and needs no flag:

```
new_deck.py                                              # English
new_deck.py --lang zh-Hans --lang-asked "<their words>"  # they asked for Chinese
new_deck.py --lang ja      --lang-asked "<their words>"  # they asked for Japanese
```

A deliverable the user asked for in another language is **authored in that
language, directly** — not written in English and translated, which produces the
same content twice.

**`--lang-asked` carries the user's own words**, and the document keeps them as
`data-lang-ask-quote`. **M16 fails a non-English deliverable with no quotation**
(under three tokens is a fragment that would match anything; a CJK character
counts as a token). The record is of an INSTRUCTION and never of an inference:
the language of the source material, the venue, the audience's nationality and
**the language the user is writing to you in** are evidence about the reader, and
a language the same user chose for a comparable deliverable outranks all of it.

*Why the quotation, when the default is already English. This rule was written,
restated in four entry points, and catalogued as FM-18 — and then broken three
times in three days, on two platforms and two models, from a source document
with no Chinese in it at all. Every one of those builds started from an
`lang="en"` scaffold. A default alone stopped none of them.*

*0.1.581: M12 fired and the build changed `lang="en"` to `lang="zh-Hans"`, which
moved the document out of M12's question entirely. 0.1.586: the build script
wrote `lang="zh-Hans"` from the start, so M12 read `n/a` on the first
measurement and never spoke. 0.1.587 required a record that somebody had asked
— and the build ran `--lang zh-Hans --lang-asked`, signing a boolean on the same
command line as the language it was attesting to.*

*So the flag carries words now. No script can verify they are the user's; what
changes is that inventing them means attributing a sentence to a person who will
read it in the document.*

**And the Chinese metrics are conditional on M16, not on the declaration.**
Declaring `zh` used to silence M12 and, in the same move, wake `M4zh` and `M5`
— so a build's first machine reading was "you have 93 Chinese punctuation
errors" and it answered by improving its Chinese. When M16 has not passed, the
Chinese half reports `n/a` and offers nothing to fix: **the improvement is to
deliver in English, and a package that coaches the prose is arguing the other
side.**

*Two language versions of one deliverable* — the pair shipped side by side — is
`scripts/ops/localize.py`, which copies a finished deck and records where the
copy came from. It is not the path to a non-English deliverable.

## 1 · Terminology red lines

*Serves: **P-3**.* · id `WR-2`

**[zh-output] Never coin Chinese.** For new technical concepts with no established
Chinese term, use the English term directly — never invent a Chinese word or a
homemade metaphor. Three-bucket adjudication, word by word:

1. **An established Chinese term exists → use it** (e.g. 风险敞口, 台账, 维度).
2. **Engineering/industry term with no Chinese equivalent → use English as-is**
   (golden set, gate, inner loop / outer loop, eval, pipeline). Keep a half-width
   space between English words and adjacent Chinese characters.
3. **Homemade metaphor or compressed coinage → eliminate**, replacing with bucket
   1 or 2. Signal: the word cannot be found in industry corpora — only your own
   documents use it.

**[zh-output] Bilingual annotation.** When a technical term is written in Chinese,
its **first occurrence** carries the English in parentheses — 中文(English).
Chart labels, quick-reference tables, and glossaries are always bilingual. Body
text after first occurrence uses the Chinese only (duplicating everywhere is an
AI tell).

**Term consistency (all languages).** One name per concept across the whole
document — no synonym rotation. When renaming, demote the old name to an alias so
it stays searchable. Watch substring collisions: a term can be a legal substring
of an ordinary word (rule data: 金标 ⊂ 金标准; 弃推 ⊂ 放弃推送) — matchers must
recognize fixed collocations before flagging.

## 2 · Banned AI-tell phrases (hard block)

*Serves: **P-3**.* · id `WR-3`

**[zh-output]** rule data: 值得注意的是 · 值得一提的是 · 不可否认 · 综上所述 ·
让我们一起 · 总而言之 · 众所周知.

Qualified ban (rule data): 赋能 is allowed **only** in the fixed industry
collocations 销售赋能 / 市场赋能 (sales/marketing enablement); every other use
(科技赋能, 为 X 赋能) is an AI tell and blocked. Lesson: ban predicates must
distinguish fixed collocations from abuse — check the collocation first.

**[en-output] — hard block.** English has been the default output language since
0.1.333 while this list stayed a five-item seed; it is now the real list. Grouped by
tell, because a writer who knows the *kind* of tell catches variants the list
misses.

1. **Significance inflation** — stands/serves as · is a testament to · a vital /
   crucial / pivotal / key role · underscores its importance · reflects broader ·
   marking a shift · a turning point · evolving landscape · indelible mark ·
   deeply rooted.
2. **Promotional register** — boasts · vibrant · rich (figurative) · profound ·
   showcasing · exemplifies · commitment to · groundbreaking (figurative) ·
   renowned · breathtaking · stunning · seamless · robust · comprehensive ·
   best-in-class · world-class.
3. **AI high-frequency vocabulary** — actually · additionally · align with ·
   crucial · delve · enhance · fostering · garner · highlight (verb) · interplay ·
   intricate · key (adjective) · landscape (abstract) · leverage (verb) · pivotal ·
   showcase · tapestry · testament · underscore (verb) · valuable · utilize.
4. **Filler, with the fix** — "in order to" → "to" · "due to the fact that" →
   "because" · "at this point in time" → "now" · "in the event that" → "if" ·
   "has the ability to" → "can" · "it is important to note that" → (delete).
5. **Authority tropes** — the real question is · at its core · in reality · what
   really matters · fundamentally · it's not about X, it's about Y.
6. **Signposting** — let's dive in · let's explore · let's break this down ·
   here's what you need to know · now let's look at · without further ado.
7. **Fake-candid openers**, used standalone — "Honestly?" · "Look," ·
   "The thing is," · "Here's the thing."
8. **Closing filler** — "It's worth noting that" · "Undeniably" · "In conclusion"
   as filler · "Let's embark" · adjective stacks in place of numbers.

**Quoting a banned phrase as an example puts it in figure ink, never in HTML
prose.** The checkers strip `<svg>` before measuring, on purpose — text drawn
inside a figure is the figure's ink, not the document's prose — so an example
of the tell lives inside the drawing that discusses it, struck through, and the
same string typed into a paragraph fails M4 as a hit. This is how the rules
can show what they ban: the A4 handbook's ban-list figure carries one struck
sample per group and passes, and a product deck that quoted three filler
phrases in a swap block failed on all three until they moved into the figure.

Attribution: groups 1–7 are adapted from the `humanizer` skill
(github.com/blader/humanizer, MIT) — see `NOTICE`. Rules were adapted, not copied
wholesale: entries that conflict with LUMI's fact discipline were dropped, and
LUMI's own seed survives as group 8.

## 3 · Punctuation and glyphs [zh-output]

*Serves: **P-3**.* · id `WR-4`

- Simplified-Chinese body text uses full-width punctuation (,→, :→: ;→; ?→?);
  half-width stays inside code, URLs, emails, version strings, filenames, and pure
  English runs.
- Chinese quotes are 「」; parentheses containing Chinese are full-width (),
  pure-ASCII content keeps half-width ().
- Half-width space between Chinese and English/digits.
- **Process discipline: run a punctuation-normalization pass after drafting, before
  delivery.** (Field-tested lesson: the same author re-introduces mixed punctuation
  repeatedly; a pass in the pipeline beats good intentions. Exempt code/pre/formula
  blocks/SVG defs.)

## 4 · Number discipline (honest metrics — all languages)

*Serves: **P-2**.* · id `WR-5`

0. **[external genres] A key number carries its judgment anchor.** A sourced,
   correct number is half the obligation; the other half is what the reader is
   supposed to feel about it and why — a benchmark, a comparison, or the
   implication spelled out. The first blind review put it exactly: a deck
   said "181 releases came from this loop" and the reviewer asked *is that Wow,
   or AAA-bad, or nothing?* — and "went from 28 to 50 in visual share" without
   saying what that buys the reader. In sales, marketing and consulting
   material, a stat band or centerpiece number with no anchor beside it is an
   unfinished sentence. (Reader review D15, divergence ≥2 on C4's dimension
   pair; the retrospective's rule outcome.)

1. **Every number carries its source** or its derivation; a range figure must trace
   to a single source or it may not appear.
2. **Illustrative values must be labeled** (illustrative / mock UI / proposal value /
   uncalibrated; in Chinese output the label word is 示意) — and the label
   travels with the number into every downstream document.
3. **Never cite an external benchmark that cannot be re-verified.** If a citation is
   later judged unreliable, retract it repo-wide and leave a retirement note in
   place ("the benchmark previously cited here was reviewed and retracted on
   <date>") — stating a retraction is not citing the conclusion.
4. Precision matches confidence: count precisely when you can; write "several"
   when you cannot; never fake precision.
5. No adjective stacks in place of numbers: if "significantly better" has no
   figure behind it, delete the adjective and keep the fact.
6. **What counts as a source marker, and how far it may sit from its number.**
   Rule 1 says every number carries its source. This says what "carries" means,
   because M2 and M6 in `references/eval-rubric.md` measure it and a metric that
   invents its own vocabulary is a second rule nobody wrote down. The markers
   are literal, and this list is the contract — `check_repo.py` holds
   `check_prose.py` to it exactly as it holds the ban list to §2:

   - `source` — "Source: meter management system"
   - `derived from`
   - `based on`
   - `as of` — a dated position
   - `per` — a named system or document
   - `n=` — a sample size
   - `extract` — a dated pull from a named system
   - `illustrative` — a declaration, with the three labels rule 2 puts beside
     it. These are declarations rather than sources, and they satisfy the same
     obligation: a number that says what it is is not a number pretending to be
     measured. **A declaration satisfies D6 too**, so a deck built on invented
     figures says so in its colophon and owes no source it does not have —
     `check_repo`'s `source-marker parity` guard reads the word *declaration*
     off these bullets and holds `check_design.py` to every one of them.
   - `mock` — a declaration
   - `proposal value` — a declaration
   - `uncalibrated` — a declaration
   - `来源` — the zh marker for "source"; matched without word boundaries,
     because CJK compounds have none
   - `出处` — "provenance / where it came from"
   - `示意` — a declaration; the zh illustrative label rule 2 already names
   - `实测` — "measured, not promised"; the zh counterpart of a dated position

   **The window is the page for an ordinary figure and the block for a range.**
   A reader takes in a page at once, so a title reading "coverage reached 41%"
   is sourced by the figure caption under it; requiring the marker in the same
   block would fail a correctly built deck, which is how the window was settled
   (measured on the tracked fixtures: page window 100%, block window 0%).
   A range is stricter because rule 1 makes it stricter — it "must trace to a
   single source or it may not appear" — and a single source cannot be inferred
   from a marker three blocks away. A dashed pair that is an enumeration label
   rather than a data range ("Plastics (1–2)" naming resin types) is not a
   range figure; the machine reports such labels and counts only pairs with
   quantitative context (GAP-001 found the overreach on a truthful label).
   **The test is what the numbers do, not how short the sentence is.** A
   counting noun in front of the pair — blocks 1–3, rows 4–9, steps 2–4 — means
   the numbers identify things; a percentage or a currency amount anywhere in
   the block means they measure, and that counts however it is worded. The
   machine carried a forty-character length proxy for this instead, and the
   proxy let go twice: it was written for the short label above, then it failed
   "Answer confirmation questions in blocks 1–3 and cross-region" in a shipped
   deliverable, whose author reworded a correct sentence to get past it.
   Length is a backstop here now, not the judgement (FM-13).

   A document with no page structure — Markdown, a plain report — has one page,
   so the window is the document.

**Never cite a statistic that has been publicly debunked, however widely it
circulates.** The presentation-evidence folklore is full of them, and two are
named here because they nearly reached a page: *"visuals make presenters 43%
more persuasive"* (the 1986 UM/3M working paper's own text does not support
its abstract's number) and *"the brain processes images 60,000× faster than
text"* (no source has ever been produced). A debunked number costs more than
no evidence: the one reader who knows discounts every honest number beside
it. When a claim's popular figure fails verification, cite the sturdier
finding instead — the picture-superiority recall pair (10% against 65% at
three days, Medina) and Mayer's controlled comparisons survived the same
check these two failed.

## 5 · Voice (the LUMI register)

*Serves: **P-3**.* · id `WR-6`

- **Negation-first openings** ("Not X. Y.", "not just X but Y"): **retired as a
  mandated signature.** At most one may appear in a document, on the cover or the
  hook, and only when the thing being rejected is named concretely enough that a
  reader could disagree with it. It is never a page-title form, never a section
  opener, and it carries **no exemption from the de-AI-flavor pass** — the former
  "this is a LUMI signature, do not de-flavor it away" clause is deleted. Reason:
  readers pattern-match the construction as machine-written, and a shape repeated
  down a deck is a tell no matter who signs it.
- **Numbers are the copy**: state parameters plainly and let them speak
  (rule data: 「每天最多 3 条 · 不够就不推」); strip marketing adjectives that
  wrap numbers.
- **Responsibility is always legible, but not templated**: a reader must be able to
  tell, for every claim, whether it is verified (and by what), recommended (their
  decision), or unverified (and what the gap is). **Say it in the sentence's own
  words.** The three fixed frames this rule used to mandate turned every claim in a
  document into one of three canned shapes — the requirement is the disclosure, not
  the wording.
- **Restrained certainty**: active voice, conclusion first; say "uncertain" plainly
  instead of stacking hedges. **Sentence length must vary** — the former "short
  sentences" mandate produced uniformly clipped prose, which is the dominant modern
  AI tell and which the old M8 metric scored as perfect. Runs of short emphatic
  fragments for drama ("The old rules were gone.") are banned outright.
- Colloquial ≠ degraded: ordinary formal verbs are fine; do not invent new
  translationese in pursuit of a casual tone.

## 5b · Register profiles — the audience decides the language

*Serves: **GOAL**.* · id `WR-10`

The LUMI voice (§5) is one voice; the REGISTER moves with the reader. Until
now the genre axis changed punctuation, sourcing placement and visual share,
and never diction — a sales deck and a training manual came out in the same
language, and a reader called it: market material must argue in the market's
language, product material in the product's. One profile per genre family,
each shown on the same underlying fact so the difference is the register and
nothing else. The fact: *the gate stack reads a deliverable in 16 seconds.*

- **Sales / marketing — the buyer's economics.** Value verbs, outcomes,
  risk retired, the buyer's own unit of account. Claims answer "what do I
  get and what does it cost me"; mechanism appears only as proof.
  *Register: "Sixteen seconds of machine time before any reader's minute is
  spent — review cycles stop being your bottleneck."*
- **Training / product manual — the operator's procedure.** Imperative
  steps, one action per sentence, checks after every step, terms defined at
  first use, no persuasion — the reader has already bought.
  *Register: "Run the gate stack. It completes in about 16 seconds. If the
  block reports any GATE line, fix that finding before continuing."*
- **Consulting / client document — the advisor's judgement.** Findings with
  their basis, implications for this client, options with a recommendation;
  confidence stated, counter-case acknowledged.
  *Register: "A 16-second machine pass shifts review effort from detection
  to judgement; for your volume that reallocates roughly one reviewer-day
  per week."*
- **Internal analysis — the colleague's reasoning.** Hypotheses, evidence
  quality, what would change the conclusion; hedges are honest here and
  banned in sales.
  *Register: "Gate-stack latency is 16s on the reference deck; unmeasured on
  larger documents — assume worse before relying on it."*

The de-AI pass (§6) runs after the profile is applied, never instead of it:
a page in the wrong register is not fixed by removing its tells.

## 6 · De-AI-flavor pass (mandatory, pre-delivery)

*Serves: **P-3**.* · id `WR-7`

> **Process discipline: this pass runs on every deliverable, before delivery — it
> is a gate, not advice.** It used to be named only inside a parenthesis and no
> workflow step invoked it; three versions of AI-flavored decks shipped past it.
> A pass in the pipeline beats good intentions.
>
> **And it leaves an artifact.** For an external deliverable the pass ends in a
> findings file run through `scripts/ops/judge_findings.py`, which accepts a
> finding only when it quotes the sentence it objects to. A pass that leaves
> nothing behind is indistinguishable from a pass that did not happen, and the
> behavioural record on that is one-directional: the build that shipped
> thirteen aphorisms had every mechanical check green and no record of this
> pass, because it was skipped. Machine metrics cannot stand in for it —
> when a document is in Chinese, M8 reads n/a and the register is unmeasured
> by construction (0.1.519), so the pass IS the instrument.

**Word and sentence moves**

1. Weak verb → direct verb (keep necessary nominalizations in academic/legal
   registers); **copula avoidance is a tell** — "serves as / stands as / boasts /
   features" become "is / are / has".
2. **Vary sentence length deliberately.** Not "fix the outliers" — check the
   distribution across each page or section: if every sentence is within a few
   words of every other, the passage reads as machine-written even when each
   sentence is fine.
3. Delete filler phrases losslessly (§2 group 4 lists the common ones with fixes).
4. Replace abstraction with concrete detail — **only detail already present in the
   source; never invent**. When the source is genuinely thin, say less rather than
   padding with abstraction.
5. Re-seat adverbials and conditions; unpack overlong attributives.
6. Cut idling connectives; keep real causality. Transitional openers
   (Moreover, Furthermore, Additionally, Notably) are almost always idle.
7. Convert passive voice and subjectless fragments back to an actor doing
   something.

**Structural moves** (these catch what a banned-word list cannot)

8. **[en-output] No em dashes or en dashes in sales, marketing, consulting or
   training deliverables — internal analysis alone is exempt.** Use a period,
   comma, colon, or parentheses. The dash is the single most recognized tell in
   English AI prose, and it is usually hiding a sentence that wants to be two.
   Training material binds because its readers quote it onward; consulting
   binds like sales, which this sentence failed to say for fifty releases while
   the checker enforced it — three statements of one rule carried three
   different genre sets until 0.1.512. A digit-to-digit range (2026-08) is
   data and exempt; a letter-digit range (a C1-C8 style span) is not, so write
   it "C1 to C8" in prose. (This does not bind this repository's own rule
   prose.)
9. **Break the rule of three.** Do not force ideas into triplets. When a list has
   exactly three items in every instance across a document, rewrite some as pairs
   or as integrated prose.
10. **Vary list shape.** Bullets whose every item shares one grammatical frame read
    as generated. Let items differ in length and construction unless the list is a
    genuine parallel enumeration.
11. **No inline-header bullets** (`**Item:** description`) as the default list
    form; prefer prose when the items are explanatory rather than enumerable.
12. **No manufactured punchlines, no aphorism formulas** ("X is the Y of Z"), no
    generic upbeat conclusion. End on the concrete fact.
12b. **A page-closing line is not a slot for a slogan, and the test is the
    distribution.** Item 12 catches one manufactured punchline; the deck-level
    form is thirteen of them, one per page, each balanced and quotable. Vary
    what the closing line DOES: one names the consequence, one states a limit
    the document has ("this figure is an evaluation-load number and live
    traffic has not tested it"), one asks the reader for something, one is a
    flat unremarkable fact. If more than half of a document's closing lines
    are short and quotable, the pattern is the tell, however good each line
    is. (Shipped instance: a build whose thirteen `.take` lines were thirteen
    aphorisms, every prose metric green, read as machine-written on sight.)
13. **Boldface carries meaning or comes out.** Mechanical bolding of every key
    phrase is emphasis inflation, and it makes a page look generated.
14. One name per concept, never synonym cycling — see §1 term consistency.
15. **No templated parallel frames.** Sibling blocks of the same role that open
    with the same words and differ only in the filled slot — "Worth your
    attention if your documents…" beside "Worth your attention before you
    commit…" — read as a template stamped twice, whatever the sentences say.
    Both quoted frames shipped side by side in one agenda and a reader called
    them AI at sight (review D16). Parallelism used deliberately is rhetoric;
    the tell is the frame with the swapped slot. `check_prose.py` M14 reports
    same-role siblings sharing a three-word opening so a writer can decide
    which one it is.

**Two-pass audit (mandatory second look)**

After the rewrite, ask the draft these two questions and act on the answers:

1. *"What makes this obviously AI-generated?"* — answer honestly, in specifics,
   then fix what you named. If the honest answer is "the shape of every title" or
   "every paragraph is the same size", the fix is structural, not lexical.
2. *"Does the rewrite state any fact, name, number, date, or citation that is not
   in the source?"* — if yes, remove it. De-flavoring must never add facts.

Then the final three checks: any word deletable without loss? any concrete detail
swallowed by abstraction? is the voice consistent?

## 6b · [zh-output] De-translationese pass

*Serves: **P-3**.* · id `WR-8`

Since sales/marketing material is now authored in English and Chinese is produced
by translating it, the Chinese deliverable carries a second risk that has already
bitten once: **English signature constructions round-tripping back into Chinese.**
In 0.1.329 the Chinese rule 「不是 X,是 Y」 was translated to "Not X. Y."; models
then rendered it back into Chinese, and the pattern amplified until readers called
the decks AI-flavored. Translationese is the Chinese equivalent of AI flavor.

After translating, before delivery:

1. Read the Chinese alone, without the English beside it. Any sentence you would
   not write from scratch in Chinese gets rewritten, not adjusted.
2. Kill inverted English word order, over-explicit pronouns and possessives
   (rule data: 「你的团队的效率」), and the imported "X, not Y" antithesis.
3. Restore Chinese-native connectives and rhythm; English clause chains split.
4. Re-run the §3 punctuation pass and the §1 terminology red lines — translation
   reintroduces both classes of defect.

## 7 · Fact red lines (outrank every style rule)

*Serves: **P-2**.* · id `WR-9`

- No invented facts — numbers, people, events, quotes come only from source
  material;
- Money/safety conclusions never come from a language model — deterministic rules
  only;
- AI never signs: legally signed steps belong to licensed humans;
- Style rewrites must not change facts or framing — cross-check item by item
  before/after; if a fact cannot be traced back, delete it.
