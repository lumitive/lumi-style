# The hand-drawn LUMI skin

First-party, drawn for this repository — nothing here is vendored, traced or
derived from another icon set's path data. (Koboyo's hand-drawn icons were the
style reference the owner pointed at; its license forbids redistribution, so
nothing from it ships here and none of these glyphs copies one of its
drawings.)

Every file shares its name with an icon in `../lucide/`, on the same 24×24
`stroke="currentColor"` grid, hex-free — `scripts/embed_icons.py --check`
enforces both, and the name parity is what keeps one semantic vocabulary
across the two skins: the expressive register (references/brand.md) resolves
a name here first and falls back to Lucide, so a missing skin degrades to the
neutral glyph rather than to nothing.

The hand-drawn character lives in the geometry, never in the invariants:
curved "straights", imperfect circles, slight asymmetry, and a slightly
heavier stroke at emit time (`LUMI_STROKE` in `scripts/embed_icons.py`).
Water appears where it means something — the shield's waterline, the layers'
strata, the route's current, the radar's ripples — not as ornament on every
glyph.

License: same as the repository (MIT, see /LICENSE).
