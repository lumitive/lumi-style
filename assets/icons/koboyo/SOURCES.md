# Koboyo icons · provenance and terms

Hand-drawn SVG icons, fetched from https://koboyo.com/icons/svg/<name>.svg on
2026-08-19, for use as **part-opener subject marks** (design-rules.md §3: one
oversized subject mark, no text of its own, reversed out of the lime field).

**Terms** (https://koboyo.com/icons/license, read 2026-08-19): free for personal
and commercial use; attribution never required; embedding in a product is
permitted "as long as the icons are part of something bigger rather than the
product itself". Redistributing the library as a competing icon product, or
building a competing icon/canvas product from it, is not permitted — which is
why only the icons actually used are vendored here rather than the set.

**Why this library and not Lucide**, which this package already ships: these are
**fill-based** (`fill="currentColor"`, no stroke), and a subject mark is rendered
at display scale. A stroked icon scaled to that size renders as the accident
design-rules.md §6 records; a filled silhouette renders as a deliberate graphic.
Lucide remains the semantic inline set at 14-24px.

| file | mark | used on |
|---|---|---|
| key.svg | key | Part A opener |
| globe.svg | globe | Part B opener |
| rocket.svg | rocket | Part C opener |
