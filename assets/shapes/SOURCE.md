# Shape library — provenance and the rule that selected it

## Where it comes from

Extracted from a commercial consulting slide template (159 pages) whose licence
the owner settled on 2026-08-14: purchased, and free to use. One clarification
belongs here because it has confused a reader once already — the confidentiality
notice on the template's first page is **sample body text of the template**, of
a kind with "EXHIBIT TITLE" and "Source:", and is not a licence term for the
asset.

Extraction was three-route: structured SVG export where it kept the geometry,
a PDF intermediate where it did not, and a flattened path for the pages built
from true 3D extrusions, which no vectoriser reaches. Every unit was then
recoloured so its fills and strokes bind **design tokens** rather than literal
colours, which is why they are correct on both the light and the dark canvas
and why D20 cannot fail on them.

## What selected these 68 out of 206

One rule, from `references/design-rules.md` §4.1:

> **A shape enters the library only if the relation it encodes serves the chart
> rules.**

Applied mechanically: a unit is here if it carries an explicit relation tag —
composition, order, process, hierarchy, degree or correlation. The other 138 are
page furniture (source lines, footnote blocks), single-primitive fragments, and
label art. **They draw no relation**, so ingesting them would have produced a
second figure vocabulary standing next to §4 rather than a figure library
serving it — the state this package spent releases leaving.

Two units were set aside for a person rather than dropped silently:
`p124-process-objectives-01` and `p109-change-vision-01` are large enough to be
real diagrams (146 and 54 primitives) and carry no relation tag. Their slide
labels suggest process and vision diagrams, but a slide label is OCR'd text, not
a taxonomy — the 134 "families" that text produced are noise, and reading them
as evidence is how a curation becomes arbitrary.

## How a shape reaches a deliverable

Only through `scripts/build/embed_shapes.py`, which emits a sprite of the
symbols a document actually referenced. Nothing else has a path in, so
original-palette geometry cannot reach a reader by accident, and D19 already
fails a reference that resolves to no symbol.

## Choosing one

`tags.json` carries each shape's relation, its family words, its slot count and
whether it is a metaphor. **Choose by the relation the content has**, never by
how a shape looks: a funnel whose values do not decrease and a 2×2 whose axes
are not independent are drawings asserting something the data does not.
