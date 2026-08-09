# LUMI Writing Rules

> The single source of truth for LUMI's output writing style. Self-contained — no
> third-party skill dependencies. Every rule traces to a real delivery iteration or
> reader review; revisions go through CHANGELOG.
>
> **Repository language: English only (red line — LUMI serves a global audience).**
> Chinese strings appear below *only as rule data* for Chinese-language output;
> they are examples, not document prose.

## 0 · Output language

**Default: American English.** When the user does not specify a language, LUMI
writes in American English — spelling (-ize, -or, -og: organize, color, catalog),
idiom, and punctuation (double quotation marks with periods and commas inside;
the serial comma). Dates in prose follow the client's convention; dates in data,
filenames, and version strings stay ISO (YYYY-MM-DD) in every language.

When the user specifies a language, produce in that language. Rules in sections
1–7 are language-agnostic unless marked **[zh-output]** (Simplified Chinese
deliverables only) or **[en-output]**.

## 1 · Terminology red lines

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

Attribution: groups 1–7 are adapted from the `humanizer` skill
(github.com/blader/humanizer, MIT) — see `NOTICE`. Rules were adapted, not copied
wholesale: entries that conflict with LUMI's fact discipline were dropped, and
LUMI's own seed survives as group 8.

## 3 · Punctuation and glyphs [zh-output]

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

1. **Every number carries its source** or its derivation; a range figure must trace
   to a single source or it may not appear.
2. **Illustrative values must be labeled** (illustrative / mock UI / proposal value /
   uncalibrated) — and the label travels with the number into every downstream
   document.
3. **Never cite an external benchmark that cannot be re-verified.** If a citation is
   later judged unreliable, retract it repo-wide and leave a retirement note in
   place ("the benchmark previously cited here was reviewed and retracted on
   <date>") — stating a retraction is not citing the conclusion.
4. Precision matches confidence: count precisely when you can; write "several"
   when you cannot; never fake precision.
5. No adjective stacks in place of numbers: if "significantly better" has no
   figure behind it, delete the adjective and keep the fact.

## 5 · Voice (the LUMI register)

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

## 6 · De-AI-flavor pass (mandatory, pre-delivery)

> **Process discipline: this pass runs on every deliverable, before delivery — it
> is a gate, not advice.** It used to be named only inside a parenthesis and no
> workflow step invoked it; three versions of AI-flavored decks shipped past it.
> A pass in the pipeline beats good intentions.

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

8. **[en-output] No em dashes or en dashes in sales/marketing or training
   deliverables.** Use a period, comma, colon, or parentheses. The dash is the
   single most recognized tell in English AI prose, and it is usually hiding a
   sentence that wants to be two. Training material binds because its readers
   quote it onward. (This does not bind internal analysis documents or this
   repository's own rule prose.)
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
13. **Boldface carries meaning or comes out.** Mechanical bolding of every key
    phrase is emphasis inflation, and it makes a page look generated.
14. One name per concept, never synonym cycling — see §1 term consistency.

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

- No invented facts — numbers, people, events, quotes come only from source
  material;
- Money/safety conclusions never come from a language model — deterministic rules
  only;
- AI never signs: legally signed steps belong to licensed humans;
- Style rewrites must not change facts or framing — cross-check item by item
  before/after; if a fact cannot be traced back, delete it.
