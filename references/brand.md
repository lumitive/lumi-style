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

## 1 · The thesis

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

Water and light behind every page: strongest on the cover and closing, medium on
the part openers, faintest on the body pages, so the texture recedes as the
evidence gets denser.

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
**surface and never text**, and `check_design.py` D13 enforces exactly that. On
the dark canvas it is the accent proper at 13.90:1.

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

Weight, scale and leading are where a deck sounds young or sounds like a filing.
The reference this was studied against runs **245 elements at weight 700 and 52 at
900**, display at 254px and 120px, line-height ~0.9, and letter-spacing `normal`
everywhere. This deck ran D-DIN 400, uppercase, `.3em` tracking — a spec sheet.

- **Display** (cover, closing, part openers): `clamp(64px, 9vw, 132px)`, weight
  **700**, leading **0.92**, tracking negative.
- **Page titles**: weight **700** at `clamp(24px, 2.7vw, 34px)` — half again the
  old size. A title is the claim, not a caption.
- **Support lines**: 16px weight 500. A second voice, not small print.
- **Numbers**: the lead tier runs to 116px and figure numerals are set bold.
- **Tracking**: gone. `.3em` on eyebrows was the most dated device in the deck.

**We ship D-DIN Regular and Bold under SIL OFL and nothing else.** No rule here
names a face the package does not carry — that is `CLAUDE.md` §5, and it exists
because 1.2.0 required an embedded display face, shipped none, and rendered
nothing until 1.7.0. The register comes from weight, scale and leading, which are
free.

## 3 · Accelerators — what a LUMI page should be willing to do

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

**The brand is never the loudest thing on the page. The evidence is.**

Wordmark small. No watermark, no ornament, no flourish, no logo behind the
content. LUMI's mark appears twice in a deck — the cover and the closing — and is
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

The 23:1 measurement and the fix come from a documented study of this exact
failure mode (`impeccable.style/research`, ~30 skill iterations, ~200 sampled
concepts). Two findings drove this file:

**"65% commitment is what bland looks like."** A five-to-one ratio of brakes to
accelerators produced work that was correct and lifeless. Measured on 3.0.0's
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
