# LUMI globe — design

Date: 2026-08-09 · Baseline version: 0.1.385 · Status: approved for planning

A rotating, interactive world figure that carries LUMI's palette and both brand
devices, in two forms: a **field** of discrete marks on a globe, and a **region**
map that unrolls flat. One renderer, one projection module, no runtime
dependencies.

---

## 1 · Why this exists, and what it replaces

`scripts/build_geography.py` already ships orthographic projection, exact limb
clipping, great-circle routes and a `live / zero / out` marker vocabulary, and
emits two static SVGs (`assets/vectors/globe-orthographic.svg`,
`world-flat.svg`). What it cannot do is move, and its coastlines are a coarse
stylisation — roughly 2 degrees, no islands under about 500 km — which is
correct for a cover mark and cannot express *these 27 countries are one region*.

This design adds the runtime half and the country-level half, and makes them share
the static half's projection maths so the two cannot drift.

**Prior art examined.** Two reference sites were reverse-engineered before
choosing an approach.

| | Site A (data-driven) | Site B (asset-driven) |
|---|---|---|
| Engine | three.js r184 / WebGL2 | three.js r184 / WebGL2 |
| Geometry | generated at runtime from GeoJSON by `three-globe` + `h3-js` | authored in a DCC tool, exported as a Draco-compressed `.glb` (131 KB) |
| Driver | constant auto-rotation | GSAP scroll timeline |
| Payload | 185 KB three.js + 321 KB globe library, lazy-loaded; 246 KB GeoJSON | one bundle + model + Draco wasm |

The engine is identical; the method is opposite. **A figure that states data must be
data-driven** — site A's method — because changing a number must change the
picture without reopening a modelling tool. Site B's method is right for a brand
mark and wrong for anything carrying a figure. Neither payload fits a
self-contained deliverable, which is why neither library is used here.

---

## 2 · Constraints that shaped it

1. **Two delivery targets, one codebase.** The component must inline into a
   single-file HTML deliverable *and* run on a product site. That rules out
   three.js (506 KB unminified for engine + globe layer).
2. **No literal colour in the code.** Every colour is read from CSS custom
   properties at init and re-read on theme change — the runtime form of the rule
   `build_geography.py` already states in its docstring.
3. **A rule may not mandate an asset the package does not ship** (CLAUDE.md 5).
   The world geometry and the region registry ship in `assets/`.
4. **The skill's conventions are the reference, never a validation artifact**
   (CLAUDE.md 7). The region registry holds geography only. Coverage counts,
   region names specific to an engagement, and any figure come from the host
   document.
5. **A prescribed value carries the floor below which it stops working**
   (CLAUDE.md 6). Recorded in §5 as the redundancy rule.
6. **Metrics passing is not a verified document** (CLAUDE.md 8). §8.

---

## 3 · Module boundaries

Six modules under `assets/globe/`. Each is separately testable and none reaches
into another's internals.

| Module | Responsibility | Depends on |
|---|---|---|
| `projection.js` | Pure functions. `project(lon, lat, view) → {x, y, visible}`; `invert(x, y, view) → {lon, lat} \| null`. `view = {lon0, lat0, t, scale, cx, cy}` | — |
| `worlddata.js` | Decode the quantised geometry; build the `ADM0_A3 → region` index and per-region bounding boxes | — |
| `render.js` | Draw layers in order: plate, graticule, region fills, borders, field marks, nodes, labels. DPR-aware | projection, worlddata |
| `pick.js` | Inverse-projection hit test, bbox prefilter, spherical point-in-polygon; nearest-mark test for the field layer | projection, worlddata |
| `controls.js` | Arcball drag with inertia, wheel zoom, keyboard | projection |
| `globe.js` | Public component: state machine (form, unroll `t`, auto-rotation), rAF loop, event emission, token reading | all |

`projection.js` also exposes `toPathString(ring, view)` so
`scripts/build_worldmap.py` and the static SVG generator can emit paths through
the same maths the canvas uses. **This is the anti-drift measure**: the static
figure and the live figure are the same projection or they are a bug.

---

## 4 · The unroll

Form 1 is an orthographic globe. Form 2 is an equirectangular flat map. They are
not two projections crossfaded — crossfading breaks limb clipping halfway
through, and there is no coherent geometry at `t = 0.5`.

Instead **the sphere itself flattens**. For each `(lon, lat)`:

- `P_sphere` = the unit-sphere position under the current `(lon0, lat0)` rotation
- `P_plane` = `(lon / 180, lat / 90, 0)`, scaled to the same extent
- `P = lerp(P_sphere, P_plane, t)`, then one orthographic projection of `P`

Visibility interpolates the same way: back-face culling at `t = 0`, nothing culled
at `t = 1`, and between them the cull threshold moves with `t` so no polygon pops.

One code path. `t = 0` is a correct globe, `t = 1` is a correct flat map, and every
value between is geometrically self-consistent, so the unroll animation needs no
separate authoring. `t` is a public property, so a document can hold it at any
value or drive it from scroll.

---

## 5 · Colour

### Form 1 — the field

The dot layer is the **field** device: one mark per datum, intensity from the
datum, order from the data. Marks take `--accent` and the light ramp; nothing in
this form encodes category by hue.

### Form 2 — regions

**Hue encodes region identity. This is an owner directive and it overrides the
default reading of "one colour one meaning".** It is safe only because the region
hues are declared to carry no data meaning, exactly as `light_ramp` already is:
identity is a label, not a measurement. Semantic colour — `accent`, `seal`,
`amber`, `brass`, the chart triple — is untouched and still governs data.

**Hues are generated, not hand-picked.** Tokens carry a spec, not a list: a fixed
lightness and chroma per canvas (tuned so every hue can carry its label text at
4.5:1) with hues spread evenly around the OKLCH circle. `scripts/build_region_palette.py`
bakes N hues into CSS custom properties, the same way `embed_font.py` and
`embed_icons.py` bake their blocks. A hand-picked list produces two
indistinguishable blues at around nine entries; a generated ramp does not, and
`N = 12` and `N = 20` come out of the same rule as `N = 6`.

**There is no cap on N.** An 8-hue ceiling was proposed and rejected by the owner:
the map layer needs to show more regions than that.

**Adjacency, not count, is what makes a map unreadable.** Hue assignment runs a
greedy graph colouring over the region adjacency graph so neighbouring regions
receive hues far apart on the circle. `check_design.py` gains a metric: perceptual
distance between every adjacent region pair must clear a threshold, and it names
the offending pair when it does not.

**The floor: above 8 hues, hue alone stops carrying identity.** No palette can keep
twelve categorical hues pairwise separable under deuteranopia — that is a property
of the eye, not of the palette. So the rule is redundancy rather than a ceiling:

> When a region map uses more than 8 hues, every coloured region must carry a
> label or a legend entry. Hue groups at a glance; text carries identity.

`check_design.py` checks for the text anchor, not for the hue count.

### State

State rides a second channel so hue stays free for identity: a covered region is a
solid fill, an uncovered one is the same hue at wash strength with a dashed edge
and a muted label. This is how the reference layout the owner supplied already
reads, and it keeps identity and state independently decodable.

---

## 6 · Geography

**Source: Natural Earth 110m admin-0, public domain.** 177 features, complete
`ADM0_A3`, plus `NAME` and `NAME_ZH` — bilingual labels need no second table.

Measured Douglas–Peucker simplification:

| Tolerance | Countries | Points | JSON | gzip |
|---|---|---|---|---|
| none | 177 | 10,654 | 159 KB | 54 KB |
| **0.35°** | **176** | **4,315** | **70 KB** | **25 KB** |
| 0.6° | 163 | 2,790 | 48 KB | 17 KB |

**0.35° is the shipped tolerance** — a target, not a floor or ceiling. 25 KB gzip
inlines acceptably. 0.6° drops thirteen countries including Qatar and Cyprus,
which a trade map cannot lose.

**110m has no Singapore, Hong Kong, Bahrain or Malta** — upstream merges them away
at this scale, and the 50m set that has them is 3 MB raw.

**Polygons are areas; nodes are points.** Country geometry comes from 110m; city
states and ports ship as a separate `nodes` point layer keyed by lat/lon. This is
cheaper and more honest — a port is a point — and it is the pattern
`build_geography.py`'s `MARKERS` already uses. Accepted by the owner as sufficient.

**Region registry** (`assets/vectors/regions.json`): `ADM0_A3 → region_id`, plus
each region's display name (English and Chinese) and label anchor. It ships a
generic trade-bloc default and a document may replace it wholesale.

The Chinese names in both JSON files are label *data* for Chinese-language
output, the same standing the banned-phrase lists have. The English-only red
line binds repository prose, and `check_repo.py` scans Markdown only, so no
allowlist entry is needed.

Invariant, checked by `check_repo.py`: **every country maps to exactly one region —
no gaps, no duplicates.** A country that reaches the renderer with no region is a
hole in the map, and a silent one.

---

## 7 · Interaction

**Hit testing is inverse projection, not an ID buffer.** `invert(x, y)` recovers
`(lon, lat)`; a bbox prefilter narrows candidates; spherical point-in-polygon
decides. An ID buffer would need a second full draw per frame while dragging, or
would go stale mid-drag. Inverse projection is valid at every `t` and adds one
function rather than a second render path. The field layer picks by screen
distance to the projected mark, 12 px threshold.

**Drag is an arcball.** Mapping horizontal pixels to longitude stops tracking the
pointer at high latitude. Instead both the grab point and the current point are
inverted to sphere vectors and the rotation between them is applied to the view,
so the point under the cursor stays under the cursor. Release decays angular
velocity exponentially to rest in about 0.9 s.

**Performance.** DPR-aware. rAF pauses on `IntersectionObserver` exit and on
`visibilitychange`. Geometry decodes once; projected results write into reused
`Float32Array`s so no per-frame allocation reaches the collector. Budget: ≤ 4 ms
per frame at 800×800 @ DPR 2 — a target, and 4,315 points of Canvas 2D path
building sits well inside it.

**Accessibility is part of the component, not a later patch.** A canvas is empty to
a screen reader, so the component maintains a parallel DOM layer: one `<button>`
per region carrying its name and value, visually hidden and fully tabbable.
Arrow keys rotate, `+`/`-` zoom, Tab moves between regions, Enter selects — the
same state machine the pointer drives. Under `prefers-reduced-motion: reduce`
there is no auto-rotation, no inertia, and form switching cuts rather than unrolls.

**Events.** `regionenter`, `regionleave`, `regionselect`, `formchange` — each
carrying the region id, so the host document owns tooltips and side panels
rather than the component inventing chrome.

---

## 8 · Repository integration and verification

New:

- `assets/vectors/world-110m.json` — simplified country geometry
- `assets/vectors/regions.json` — region registry and node layer
- `assets/globe/*.js` — the six modules
- `scripts/build_worldmap.py` — generate both JSONs from upstream; `--check` verifies currency
- `scripts/build_region_palette.py` — bake the region hues into CSS

Changed: the three `tokens/` files (region-hue spec plus the version stamp),
`SKILL.md`, `CHANGELOG.md`, `references/design-rules.md` (region colouring and the
redundancy rule), `README.md`, `NOTICE` (Natural Earth, public domain),
`check_repo.py` (region coverage completeness), `check_design.py` (adjacent-pair
perceptual distance, text anchor per coloured region).

Per CLAUDE.md 3 this is a rule revision: one version bump across five places, and
a CHANGELOG entry. The entry records the case honestly — an owner directive, with
the rejected 8-hue ceiling and the redundancy rule that replaced it — so a later
reader can see the rule was decided, not invented.

**Verification.** Metrics passing is not a verified figure. Screenshot and look at:
both forms × `t ∈ {0, 0.5, 1}` × light and dark × two viewport widths. The
contact-sheet mechanism in `scripts/inspect_layout.py` already does this shape of
work and gets wired to it. Specifically checked by eye, because no metric sees
them: polygons popping at the cull threshold, label collisions near the limb,
and the antimeridian seam at `t = 1`.

---

## 9 · Out of scope

Zoom beyond a single globe (no tiling, no level-of-detail switching), choropleth
animation over time, route/arc rendering (the static generator already has
great-circle maths; wiring it into the runtime is a later increment), and any
WebGL path.
