# LUMI Brand — the water thesis

> **This file loads first, and it is the only one that tells you what to reach
> for.** Everything else in `references/` is craft knowledge and defect history:
> what has gone wrong before and what fixed it. Those rules are real and none of
> them is going away, but they answer *is this correct*. This file answers *what
> is this, and why does it look like nothing else*.
>
> **Order of operations: commit first, clarify second.** Land the concept fully,
> then apply the red lines and the craft rules to make it clear. Not the reverse.
> (Provenance below. The reverse is measurably how you get bland.)
>
> (Repository language: English only — red line. The Chinese below is the source
> text of the thesis, quoted in backticks as data, the way banned phrases are.
> Every sentence around it is English, so this file reads on a platform that
> renders CJK poorly.)

---

## Contents

- [1 · The thesis](#1--the-thesis)
- [2 · The two devices](#2--the-two-devices)
  - [The field](#the-field)
  - [The ground — and why it may be decorative when a field may not](#the-ground--and-why-it-may-be-decorative-when-a-field-may-not)
  - [The waterline](#the-waterline)
  - [The acid green](#the-acid-green)
  - [The light: an accent with intensity](#the-light-an-accent-with-intensity)
- [2b · The register: heavy, large, tight](#2b--the-register-heavy-large-tight)
- [3 · Accelerators — what a LUMI page should be willing to do](#3--accelerators--what-a-lumi-page-should-be-willing-to-do)
- [4 · Non-contention as a visual rule](#4--non-contention-as-a-visual-rule)
- [5 · Provenance](#5--provenance)

## 1 · The thesis

*Serves: **P-1**.* · id `BR-1`

> `上善若水，水利万物而不争`
> *The supreme good is like water: it nourishes all things without contending.*
> — Laozi, Daodejing 8

This is not a metaphor chosen for its sound. Three of its four parts are already
true of what LUMI does, and one of them is already in the source code.

**It nourishes all things** (`水利万物`) **— one apparatus, every vessel.** The
same signal machinery serves customs, energy, pharmaceuticals, logistics. Water takes the shape of any
container without becoming a different substance. That is a platform thesis, and
it is why *design per page* is a brand rule and not only a craft rule: the work
takes the shape of the content it is poured into.

**Without contending** (`而不争`)**.** This is the rare part, and LUMI already
lives it in engineering rather than in marketing:

- click-through never measures relevance, because it rewards the clickbait the
  client asked us to remove;
- no accuracy figure before the golden set exists, however much a buyer wants one;
- AI never signs — the licensed broker does, and how often they correct us is the
  only accuracy number committed externally;
- a refusal is honoured, including by hand: 40 of 161 sources sit off the
  automated chain because they said no.

Every AI company on earth claims bold, transformative, 10×. LUMI's actual
differentiator is that it **declines, and can show you the code where it
declines**. Non-contention (`而不争`) is not modesty and not softness. It is a
competitive position:
*we are the one you can check.*

**LUMI is light** (`光`)**.** You cannot see a current. You can see light on it.
LUMI does not create the trade flows, the regulations or the supply chain; it
makes them legible. The product is already named for this.

**Shimmer on water** (`波光鳞鳞`) **— the visual key.** Light on water is **many
small discrete marks at varying intensity, arranged by a flow you cannot
otherwise see.** Not a glow. Not
a gradient wash. Not a logo. The pattern is the evidence of the current.

---

## 2 · The two devices

*Serves: **P-1**.* · id `BR-2`

Both are **structural**. They set how a page is built, not what is sprinkled on
top of it. A committed surface over a template grid is the failure this whole file
exists to avoid.

### The field

Many small marks, varying in intensity, ordered by the thing they measure.

Use it when a set has a shape: thirty pages by handling tier, 194 codes by policy
list, 161 sources by authority level, seven verification layers by whether they
run. One mark per datum, intensity from the datum, order from the data's own
sequence. At a glance a reader sees the distribution; up close they can count.

The field is LUMI's signature because it is what the company does — take a mass
of things and make the pattern in them visible without arguing about it.

> **What makes a field dishonest: nothing behind it.** A shimmer with no data
> under it is decoration, and decoration is contention — the page competing for
> attention it has not earned. Every mark maps to one real item. If you want the
> texture but do not have the data, you do not want the texture.
> `inspect_layout.py` checks this.

### The ground — and why it may be decorative when a field may not

Water and light behind every page: **dense** on the cover and closing
(`--ground-strong`), **medium** on the part openers (`--ground-mid`), **sparse**
on the body pages (`--ground-faint`), so the texture recedes as the evidence
gets denser. The three values are ceilings on loudness — quieter is always
allowed — and the tier follows from the page class alone. A document defines
its ripple drawing once and instantiates it per page (a `<defs>`/`<use>` pair
or one repeated block); it draws it with `preserveAspectRatio="xMidYMid
slice"`, which crops at the A4 sheet instead of stretching, so the marks keep
their drawn weight in both geometries. **It never carries a blend mode.** On the
lime opener the ground must darken the field rather than tint it, and that is a
colour — the strokes take the field's own foreground — not a compositing mode.
*Measured: `mix-blend-mode: multiply` on five opener pages took an exported
31-page PDF from 448ms to 4515ms, because one blended element makes the reader
composite the whole page. The look was identical either way.* A cropped ground still concentrates its
densest band on a narrower page, so the strong tier steps down on the sheet —
the token file carries both values, each measured against the ceiling in its
own geometry.

That is decoration, and the field rule above forbids decoration. The
contradiction resolves on one distinction, and it is the distinction that makes
both rules true at once:

> **A field is discrete and countable. A ground is continuous and uncountable.**
> If a reader can count the marks, every mark must mean something. If there is
> nothing to count, there is nothing to misread — so a ground may be decorative
> *precisely because* it can never be mistaken for evidence.

The ground's honesty test is therefore different in kind from the field's, and
both halves are measured:

> **What makes a ground dishonest: being loud, or being countable.**
> It may never exceed **1.40:1** against its canvas — measured on the *rendered*
> page with every foreground element hidden, not reasoned about from the alpha,
> because a texture that computes fine and looks like graffiti is the failure
> mode. And it may never resolve into repeated identical marks: the moment a
> ground can be counted it is a field pretending to be water, and a reader will
> try to read meaning into it.

**The ground carries the colour, and the foreground does not.** This is where a
wider hue range lives — lime into forest into teal into blue, gradients along the
length of each line — safely, because the ground cannot be read as data. The
foreground stays one colour, one meaning. It is also why the flows crowd *below*
the waterline and thin out above it: water sits under the surface, so the air
where the claim lives stays clear. That is what makes the ground structural
rather than wallpaper.

### The waterline

Every page has one horizon where the light collects.

**Above it is air**: the claim, the title, the one thing to carry out of the room.
**On and below it is record**: the evidence, the figure, the tiers, the handling
terms. The footer rule is that datum — not a border closing a box, but the surface
the page sits on.

This is the cheapest thing in the entire system and the one that most changes how
a page reads. A page composed against a horizon reads as *placed*; a page filled
from the top down reads as *poured*.

> **What makes a waterline dishonest: two of them, or none.** More than one
> horizon and the page has no datum, it has stripes. None, and it is a document
> again.

### The acid green

`--lime: #B8FF00`. It measures **1.21:1 as text on the white canvas** — unreadable
— and **16.44:1 with near-black reversed out of it**, so on light it is a
**surface and never text**, and `check_design.py` D13 measures exactly that
(reported like every design judgement there — only D12/D14/D15/D19/D20/D21/D22 gate). On
the dark canvas it is the accent proper at 13.90:1.

**Two greens, and the canvas forces them apart.** Counted on the content pages,
the accent appears **84 times as a fill, 71 times as a stroke, 23 times as a wash
and 0 times as text**. The lime cannot do the strokes: 1.21:1 on white makes a
chart rule, a connector or a decision outline invisible, and §1 already counts a
mark a reader must tell apart as text. It could do the fills — but 84 acid panels
is the opposite of non-contention and destroys the thing that makes it an event.
So:

- **`--acc`, the forest, is the working green in text.** Emphasis, pass states,
  table furniture, the footer's site — everything that reads as *words* on
  white. It is not a legacy colour and it is not going away.
- **`--acc-live` is the working green in figures.** Strokes, chart marks, small
  fills — the `f-acc` / `s-acc` paint classes bind to it. Same meaning as the
  forest, measured for the other medium: the forest reads brown at figure
  scale, and the live green clears the stroke and text floors in both palettes
  (5.21:1 on white, 3.23:1 on the dark ground) while reading as the lime's
  family. *Provenance: this bullet said "strokes, chart marks" belonged to the
  forest while the token file said figures take the live green, and the 0.1.442
  owner review saw the result — a document whose dividers, titles and figures
  ran three unrelated greens. One meaning, two measured inks, and each file
  now says so.*
- **`--lime` is the event green.** Large panels, and the cover/closing title's
  subject chip — always with the near-black reversed out of it or backing it,
  never bare on the light canvas.

This is not an inconsistency to be tidied up later. It is one meaning in two
measured inks plus an event colour, and the only way to collapse them into one
ink is a dark content canvas.

**Key numbers rank in three steps.** A number that is the argument is set like
one — the display weight, not a caption with large type:

| tier | how | which number |
|---|---|---|
| the argument | a **lime panel**, near-black numerals, 16.44:1 | the one the page turns on |
| its support | **forest** | the number that qualifies it |
| context | **ink** | everything else |

One lime panel per page.

**One lime event per body page, and it is a fill.** The lime may appear once in
the body of a deck, on the number the page turns on — measured, it is comfortable
there and the numbers say why. Its edge against the canvas is **1.21:1**, so the
panel *glows rather than cuts*; near-black on it is **16.44:1**; and at **chroma
102** it is right at panel size and harsh as a hairline or as small text, so it is
never a rule, a stroke or a caption. **Once per page**: ΔE against the semantic
forest is **94**, plainly a different colour, so two greens on one page would read
as two meanings.

**The lime marks a number panel. It never marks a chart mark.** A chart mark
encodes a value a reader compares across pages, so a bar that is lime here and
forest there asks what the difference means. A page with no number panel simply
has no lime, and that is fine — not every page needs one. *Provenance: two
comparison bars, one lime and one forest, and a reader asked why. It was a
collision between two of these rules — one lime event per page met the same
component always looks the same — and the component lost.*

**One role, one rendering.** Every role that repeats across a deck — title,
support line, eyebrow, band value, band label, caption, listhead, callout, footer
terms, page number — renders exactly one way. Exceptions exist (band values rank
by importance; the footer inverts on a lime opener) and every one of them is
**declared in the probe**, because "that one is on purpose" living in someone's
head is how a deck ends up with a callout at three sizes.

**The roles have names, and the names ship.** `tokens/lumi-layouts.css` defines
each of them — `.eyebrow`, `h2.t`, `.sup`, `.listhead`, `.gd`, `.cap .n`,
`.band .k`, `.band .v` — and that block is the contract the probe checks against.
A document may add roles freely; renaming one of these silently removes it from
the audit. *Provenance: six of the ten class names lived only in a deliverable,
so a document built from the tokens matched two of ten roles and lost the other
eight without a word. The probe now names any role it could not find, and a
title is checked in three registers — content, cover, closing — rather than one
role with size ignored, because ignoring the size axis made the very defect this
rule was written for undetectable.*

**One datum.** The content area begins at the same height on every page of a
geometry. Reserve the title block, do not let it float: titles all started at the
same y here while the first content cell started at **ten different heights**, and
that is what a reader feels flipping through even when every type style matches.
The datum is per geometry — portrait releases the reserve, because portrait is a
composition and not a reflow.

The reserve is a **ceiling on the title block, not a target**: two title lines
plus one support line, and a page needing more gets shorter text rather than a
taller reserve. Say it that way round or an author pads to fill it — the deck
that introduced this datum paid for it by trimming six support lines to two.
`tokens/lumi-layouts.css` ships the reserve on `.body .lede`; a rule that
mandates a mechanism the package does not ship is one nobody can follow.

**A page that no longer fits gets its content trimmed, never its type nudged.**
Nudging type per page is what produced three callout sizes over three releases,
each fix locally right and the accumulation an inconsistency a reader could see.

**It carries no meaning.** `--acc` stays the semantic accent for data, and one
colour one meaning is untouched. The lime is where the brand is loud: the part
openers are full lime fields with the claim in near-black at display size, and
they are the only pages in the deck that are. A quiet system that opens onto one
of those reads as confidence.

### The light: an accent with intensity

`--accent` is one flat green, used sixty times in a thirty-page deck. Light on
water is never one value.

The accent gains a **discrete ramp** — a small number of named steps, not a
gradient. One figure can then say near/far, strong/weak, now/later, built/partial
in a single voice, instead of reaching for a second and third hue to express
gradation that was always the same dimension.

**The semantic tokens do not change.** One colour, one meaning still governs data:
accent = built/pass, seal = red line, amber = partial, brass = reference. Those
stay flat and measurable. **The ramp belongs to fields and surfaces, not to
meaning.** Keeping those two jobs in separate tokens is the whole architectural
move — it is what lets the brand shimmer without the data lying.

---

## 2b · The register: heavy, large, tight

*Serves: **P-3**.* · id `BR-3`

Weight, scale and leading are where a deck sounds young or sounds like a filing.
The reference this was studied against runs **245 elements at weight 700 and 52 at
900**, display at 254px and 120px, line-height ~0.9, and letter-spacing `normal`
everywhere. This deck ran D-DIN 400, uppercase, `.3em` tracking — a spec sheet.

- **Display** (part openers): **80px on the slide, 72px on the sheet** (fixed
  per stage since 0.1.382, because a viewport-relative size on a fixed box lets
  the reader's window resize the design), weight **700**, leading **0.92**,
  tracking negative. **The cover and closing set SMALLER, at 58px** — an opener
  carries one line and a cover carries four things; the rank is stated at the
  token (`--fs-cover`) and is not a preference. (This bullet folded the cover
  into display at "80/50", and both numbers disagreed with the tokens.) It was a third larger on first
  build and a reader pulled it back — big enough to be the event, not so big the
  page becomes a poster with a caption.
- **Page titles**: weight **700** at **34px on the slide, 26px on the sheet** — half again the
  old size. A title is the claim, not a caption.
- **Support lines**: 17px weight 500 (`--fs-support`). A second voice, not
  small print.
- **Numbers**: the lead tier runs to 116px and figure numerals are set bold.
- **Tracking**: gone. `.3em` on eyebrows was the most dated device in the deck.

**We ship D-DIN Regular and Bold under SIL OFL and nothing else.** No rule here
names a face the package does not carry — that is `CLAUDE.md` §5, and it exists
because 0.1.332 required an embedded display face, shipped none, and rendered
nothing until 0.1.337. The register comes from weight, scale and leading, which are
free.

## 3 · Accelerators — what a LUMI page should be willing to do

*Serves: **P-1**.* · id `BR-4`

This section exists because for four releases this skill said only what not to do,
and an author who is only ever braked stops at 65% commitment on every axis. These
are permissions. They are not requirements, and none of them outranks a red line.

- **Give one number the whole page.** If the argument is 5.6% against 100%, set it
  at ninety points and let the rest of the page get out of its way.
- **Let a figure run to the paper's edge.** A drawing that is the argument does not
  need a margin on both sides to prove it is well behaved.
- **Use the accent as a field, not a hairline.** A part opener that is a full
  surface of colour with one sentence reversed out of it is not decoration — it is
  the reader being told where they are.
- **Compose asymmetrically.** The frame is fixed at 1280×720. A figure off-centre
  against a narrow column of type reads as placed. Centred everything reads as
  defaulted.
- **Draw the set.** When something is countable, count it on the page: thirty
  ticks, 194 codes, seven layers. The field is always available and almost always
  better than saying the number in a sentence.
- **Let a quiet page be very quiet.** One line at display scale on an empty
  surface is a legitimate page. The contrast between that and a dense evidence
  page is most of what makes the dense one read as dense *on purpose*.
- **Say the hard thing at full size.** "That one was missed, and the root cause was
  collection" belongs at the same scale as the good news. Honesty set small reads
  as a disclaimer; honesty set large reads as confidence, which is what it is.

---

## 4 · Non-contention as a visual rule

*Serves: **P-1**.* · id `BR-5`

**The brand is never the loudest thing on the page. The evidence is.**

Wordmark small — the literal string "LUMI Style". No watermark, no ornament,
no flourish, no logo behind the content. LUMI's mark appears twice in a deck —
the cover and the closing, and by default it is the locked FIELD GLOBE
(`assets/brand/lumivate/globe-field.svg`), embedded live so it turns — and is
never larger than it needs to be to be read.

This is the part that makes impact and non-contention compatible rather than
opposed. If
impact came from brand furniture, restraint would kill it and you would have to
choose. Impact here comes from **the scale of the evidence and the quality of the
light on it**. A quiet system that opens onto something vast reads as confidence.
A loud one reads as insecurity, and a buyer of a compliance product can smell the
difference immediately.

---

## 5 · Provenance

*Serves: **P-2**.* · id `BR-6`

The 23:1 measurement and the fix come from a documented study of this exact
failure mode (`impeccable.style/research`, ~30 skill iterations, ~200 sampled
concepts). Two findings drove this file:

**"65% commitment is what bland looks like."** A five-to-one ratio of brakes to
accelerators produced work that was correct and lifeless. Measured on 0.1.345's
predecessor, this repo ran at **272 restricting lines against 12 inviting ones —
23:1**, nearly five times more braked than the ratio that already produced bland.
Every release had added brakes, because every release fixed defects a reader
found. Nothing was ever added on the other side.

**Inverting the order was "the biggest single quality jump" in the study.** Land
fully committed first, then make it clear. This file therefore loads before the
craft rules, and `SKILL.md`'s workflow was reordered to match. No brake was
removed to achieve it — all 272 are hard-won defect history and all of them still
apply. They moved from being the frame the work is born inside to being the second
pass that makes it clear.

**"Committed skin hides template bones."** A fully-committed visual can still sit
on a standard grid, which is why both devices here are structural. If the field
and the waterline end up as things sprinkled onto the existing layout, this file
has failed and the deck will look exactly as it did.
