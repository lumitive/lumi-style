# LUMI Writing Rules

> The single source of truth for LUMI's output writing style. Self-contained — no
> third-party skill dependencies. Every rule traces to a real delivery iteration or
> reader review; revisions go through CHANGELOG.
>
> **Repository language: English only (red line — LUMI serves a global audience).**
> Chinese strings appear below *only as rule data* for Chinese-language output;
> they are examples, not document prose.

## 0 · Output language

LUMI produces in the client's language. Rules in sections 1–7 are language-agnostic
unless marked **[zh-output]** — those apply only when the deliverable is Simplified
Chinese.

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

**[en-output]** avoid the English equivalents: "It's worth noting that",
"Undeniably", "In conclusion" as filler, "Let's embark", "delve into",
"game-changing", adjective stacks in place of numbers.

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

- **Negation-first openings**: "Not X. Y." — reject the peer approach, then define
  your own. This is a LUMI signature, not an AI tell; do not "de-flavor" it away.
- **Numbers are the copy**: state parameters plainly and let them speak
  (rule data: 「每天最多 3 条 · 不够就不推」); strip marketing adjectives that
  wrap numbers.
- **Three-tier responsibility phrasing**: every claim lands in one of —
  "verified (source Z)" / "we recommend; the decision is yours" /
  "X unverified; the gap is Y".
- **Restrained certainty**: short sentences, active voice, conclusion first; say
  "uncertain" plainly instead of hedging stacks.
- Colloquial ≠ degraded: ordinary formal verbs are fine; do not invent new
  translationese in pursuit of a casual tone.

## 6 · De-AI-flavor pass (six moves, pre-delivery)

1. Weak verb → direct verb (keep necessary nominalizations in academic/legal
   registers);
2. Break uniform sentence lengths: merge fragments, split run-ons;
3. Delete filler phrases losslessly;
4. Replace abstraction with concrete detail — **only detail already present in the
   source; never invent**;
5. Re-seat adverbials and conditions; unpack overlong attributives;
6. Cut idling connectives; keep real causality.

Final three checks: any word deletable without loss? any concrete detail swallowed
by abstraction? is the voice consistent?

## 7 · Fact red lines (outrank every style rule)

- No invented facts — numbers, people, events, quotes come only from source
  material;
- Money/safety conclusions never come from a language model — deterministic rules
  only;
- AI never signs: legally signed steps belong to licensed humans;
- Style rewrites must not change facts or framing — cross-check item by item
  before/after; if a fact cannot be traced back, delete it.
