# Shape library — provenance, and why nothing was excluded

## Where it comes from

Extracted from a commercial consulting slide template (159 pages) whose licence
the owner settled on 2026-08-14: purchased, and free to use. One clarification,
because it has confused a reader once — the confidentiality notice on the
template's first page is **sample body text of the template**, of a kind with
"EXHIBIT TITLE" and "Source:", not a licence term for the asset.

Extraction was three-route: structured SVG export where it kept the geometry, a
PDF intermediate where it did not, and a flattened path for the pages built from
true 3D extrusions, which no vectoriser reaches. Every unit was then recoloured
so its fills and strokes bind **design tokens** rather than literal colours,
which is why they are correct on both canvases and why D20 cannot fail on them.

## Why the library is complete

All 206 units are here. Two earlier attempts curated by page name, and **both
units sampled against the rendered preview were classified wrong**: `box` is a
2×2 quadrant grid with a four-arrow cycle through it, not a text box, and
`surround` is a large directional arrow. A name does not tell you what a drawing
is, and neither does a tag that was never applied — 138 units carry no relation
tag at all, and among them are the `flow-2` … `flow-6` and `cycle-2` … `cycle-8`
families, which are the most useful thing a shape library holds: one relation at
several arities, so the choice is "how many steps do I have".

The rule that follows: **an absent shape cannot be chosen by anything, while an
unclassified one merely carries no recommendation.** So nothing is excluded, and
`relation` is guidance rather than an entry fee.

## Choosing one

`tags.json` carries, per shape: `family` (the template's own page name),
`relation`, `relation_from`, `slots`, `primitives`, `decoration_risk`, `three_d`
and `preview`.

- **Choose by the relation the content has**, never by how a shape looks. A
  funnel whose values do not decrease and a 2×2 whose axes are not independent
  are drawings asserting something the data does not.
- **`relation_from: unclassified` means nobody has classified it, not that it is
  unusable.** 70 units are in that state. Look at the preview.
- **`decoration_risk: true` marks a metaphor family.** Each can carry an
  argument and most get reached for because they fill a page — P-4 says a figure
  carrying no argument violates the clause rather than satisfying it.

## How a shape reaches a deliverable

Only through `scripts/build/embed_shapes.py`, which emits a sprite of the
symbols a document actually referenced. Nothing else has a path in, so
original-palette geometry cannot reach a reader by accident, and D19 already
fails a reference resolving to no symbol. A deliverable using two shapes carries
about 37 KB; the library is 2.8 MB, which is the whole reason the embed is
selective.

## Previews

2560px renders of every unit live with the raw material outside this repository
(`_refactor/assets-staging/previews-2k/`, plus 30 vector-3D renders). `tags.json`
names each shape's preview path so a person can look before choosing — which is
the step whose absence produced two wrong curations.

## The originals, and the tool that makes the library from them (0.1.532)

`source/` holds the 206 un-recoloured units exactly as extracted, with the
extraction's `index.json`. `scripts/build/recolor_shapes.py` regenerates every
unit in this directory from them, reading the light ramp, the ink, the cold
white, the lime and the canvas from `tokens/design-tokens.json`; its `--check`
runs in CI and fails on one byte of difference, so the committed library is
held to the tokens the same way every other vendored asset here is. Until
0.1.532 the tool lived outside the repository and the originals were not
vendored: the library was a fact about one machine (GAP-017). The first
`--check` against the committed files was byte-identical, which is the proof
that the in-repo tool is the tool that made them.

The originals are the extraction's output, not the template: they carry the
template's own colours (black master, saturated faces, white edges) and are
never embedded in a deliverable — `embed_shapes.py` reads only this directory's
recoloured units, and that is what keeps P-1 an engineering fact.

