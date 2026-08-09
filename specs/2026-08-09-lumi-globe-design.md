# LUMI globe — design

Date: 2026-08-09 · Written against 0.1.385 · Status: converged after six adversarial rounds

A world figure that carries LUMI's palette and both brand devices, in two forms:
a **field** of discrete marks on a globe, and a **region** map that unrolls flat.
One projection, one geometry model, no third-party runtime dependency.

---

## 1 · Why this exists

`scripts/build_geography.py` already ships orthographic projection, exact limb
clipping, great-circle routes and a `live / zero / out` marker vocabulary, and
emits two static SVGs (`assets/vectors/globe-orthographic.svg`,
`world-flat.svg`). What it cannot do is move, and its coastlines are a coarse
stylisation — roughly 2 degrees, no islands under about 500 km — correct for a
cover mark and unable to express *these 27 countries are one region*.

This design adds the country-level half and the runtime half, and makes them
share the static half's projection maths so the two cannot drift.

**Prior art examined.** Two reference sites were reverse-engineered first.

| | Site A (data-driven) | Site B (asset-driven) |
|---|---|---|
| Engine | three.js r184 / WebGL2 | three.js r184 / WebGL2 |
| Geometry | generated at runtime from GeoJSON by `three-globe` + `h3-js` | authored in a DCC tool, exported as a Draco-compressed `.glb` (131 KB) |
| Driver | constant auto-rotation | GSAP scroll timeline |
| Payload | 185 KB + 321 KB **compressed over the wire**, lazy-loaded, plus 246 KB GeoJSON | one bundle, model, and Draco wasm |

The engine is identical; the method is opposite. **A figure that states data must
be data-driven** — site A's method — because changing a number must change the
picture without reopening a modelling tool. Site B's method is right for a brand
mark and wrong for anything carrying a figure. Roughly half a megabyte
*compressed* rules out both libraries for a self-contained deliverable.

---

## 2 · The constraint that reshaped this design

The first draft proposed a single Canvas 2D renderer. Review against the current
tree killed it:

- `d5_drawn_share` (`check_design.py:338`) counts a `.fig` as drawn only if it
  contains `<svg>`. A canvas figure reports as *laid out* — precisely the defect
  that metric exists to catch.
- `d5_figure_parity` iterates `<svg>` elements only.
- `d17_export_weight` counts `points=` attributes and `<path ` occurrences; a
  canvas contributes zero.
- `inspect_layout.py` measures rendered geometry and cannot see inside a canvas.

**A canvas is invisible to every gate this package owns.** So the target decides
the renderer, and there are three targets over one core:

| Target | Renderer | Motion and interaction | Checkable |
|---|---|---|---|
| Deliverable, print/PDF | SVG emitted by Python at build time | none | fully — it is markup |
| Deliverable, on screen | the same SVG, `d` attributes mutated by the runtime | full | fully — the static frame is in the file |
| Product site | Canvas 2D | full | not applicable |

**SVG is the default and the fallback.** The deliverable path degrades to the
static frame with JavaScript disabled, in print, and under
`prefers-reduced-motion`. The canvas renderer is an alternate back end behind the
same interface, used where no gate applies and frame rate is the constraint.
`pick.js` and `controls.js` are shared, so interaction is identical on both.

The shared core — projection, geometry, region logic — is the hard part and is
written once.

---

## 3 · Module boundaries

`projection` is authored **twice on purpose**: Python is the authority,
JavaScript is a port verified against it (§8).

Python, in `scripts/`:

| Module | Responsibility |
|---|---|
| `build_worldmap.py` | Build the shared-arc topology from upstream geometry, simplify each arc once, derive adjacency; emit `world-110m.json` (a topology, not a FeatureCollection), `regions.json` and the golden fixture; `--check` verifies currency |
| `build_region_palette.py` | Generate region hues; emit CSS; `--check` verifies currency and adjacency separation |
| `globe_svg.py` | Emit a static SVG frame for a given view |
| `geo_projection.py` | The projection functions, extracted from `build_geography.py` (see below) |

**`build_geography.py` must be refactored first, as its own commit.** Its
projection lives in module-private functions (`_project`, `_ortho`, `_cos_c`,
`_crossing`) against a module constant `R = 150.0` and a fixed centre. Two callers
need it parameterised. The refactor is byte-output-preserving and
`build_geography.py --check` — which runs in CI — is the proof: if the emitted
SVGs change by one character, the extraction was not faithful. Doing it in a
separate commit is what makes that signal readable.

JavaScript, in `assets/globe/`:

| Module | Responsibility | Depends on |
|---|---|---|
| `projection.js` | Pure. `project(lon, lat, view) → {x, y, visible}`; `invert(x, y, view) → {lon, lat} \| null` | — |
| `worlddata.js` | Decode geometry; build the `ADM0_A3 → region` index and per-region bounding boxes | — |
| `render-svg.js` | Mutate `d` attributes on the existing SVG. The deliverable back end | projection, worlddata |
| `render-canvas.js` | Immediate-mode Canvas 2D. The site back end | projection, worlddata |
| `pick.js` | Inverse-projection hit test, bbox prefilter, spherical point-in-polygon; nearest-mark test for the field layer | projection, worlddata |
| `controls.js` | Arcball drag with inertia, wheel zoom, keyboard | projection |
| `globe.js` | Public component: state machine (form, unroll `t`, auto-rotation), rAF loop, events, token reading, back-end selection | all |

---

## 4 · The unroll

Form 1 is an orthographic globe; form 2 is an equirectangular flat map. They are
not two projections crossfaded — crossfading breaks limb clipping halfway through
and there is no coherent geometry at `t = 0.5`.

Instead **the sphere itself flattens**. For each `(lon, lat)`:

- `P_sphere` = the unit-sphere position, radius `R`, under the current
  `(lon0, lat0)` rotation
- `P_plane` = `(R · lon' / 180, R · lat / 90 · 0.5, 0)` where `lon'` is longitude
  relative to `lon0`, wrapped to `(-180, 180]`. The plane spans `2R × R`, so the
  flat map is exactly as wide as the globe and the 2:1 equirectangular aspect
  holds.
- `P = lerp(P_sphere, P_plane, t)`, then one orthographic projection of `P`

Visibility interpolates the same way: back-face culling at `t = 0`, nothing culled
at `t = 1`, and the cull threshold moves with `t` so no polygon pops.

**The antimeridian must be cut, not merely watched.** Because `lon'` is relative
to `lon0`, the seam moves as the globe turns, and any ring crossing it would draw
a horizontal streak across the whole map as `t` rises. Rings are split at the
seam during projection — the same machinery `_visible_runs` already uses for the
limb, with the seam as the boundary instead of the horizon. Both halves close
along the map edge. This is an implementation requirement, not a review note.

One code path. `t = 0` is a correct globe, `t = 1` a correct flat map, every value
between geometrically self-consistent — so the unroll needs no separate
authoring. `t` is public, so a document can hold it or drive it from scroll.

---

## 5 · Colour

### Form 1 — the field

The mark layer is the **field** device: one mark per datum, intensity from the
datum, order from the data. Marks take `--accent` and the light ramp. Nothing in
this form encodes category by hue.

### Form 2 — regions

**Hue encodes region identity. This is an owner directive and it overrides the
default reading of "one colour one meaning".** It is safe only because region
hues are declared to carry no data meaning, exactly as `light_ramp` already is:
identity is a label, not a measurement. Semantic colour — `accent`, `seal`,
`amber`, `brass`, the chart triple — is untouched and still governs data.

**There is no cap on the number of regions.** An 8-hue ceiling was proposed and
rejected by the owner: the map layer needs more regions than that.

#### The construction

OKLCH is the *design space*; sRGB hex is the shipped value.
`build_region_palette.py` converts and emits **hex**, never `oklch()`:
`parse_color` (`check_design.py:104`) reads only `#rgb`, `#rrggbb`, `rgb()` and
`rgba()` and returns `None` otherwise, so an `oklch()` token would make D1 skip
every region hue **silently** — the failure mode this repository fears most.

1. **Four bands.** Band `k ∈ {0,1,2,3}` centres on hue `90k`; the region
   adjacency graph is 4-coloured and each region takes its band's hue range.
2. **Within a band**, hues spread over ±15°, so any two regions in *different*
   bands sit at least **60°** apart on the hue circle. Same-band regions may be
   close, and by construction they never share a border.
3. **Chroma is 92% of the per-hue sRGB gamut maximum**, found by bisection. A
   fixed chroma puts three to ten hues out of gamut where they are clipped,
   which silently destroys the even spread.
4. **Lightness: 0.70 on the light canvas, 0.52 on the dark.**

**Four bands is a hard requirement on the registry, not a guarantee from the
map.** An earlier draft claimed the four-colour theorem covers this. It does not:
the theorem is about contiguous regions of a planar map, and trade blocs are
routinely non-contiguous, which can make the adjacency graph non-planar and push
the chromatic number above four. Measured, with band pitch `360/B` and within-band
spread `±pitch/6`:

| Bands | Cross-band separation | light ΔE00 | dark ΔE00 |
|---|---|---|---|
| **4** | 60.0° | **24.3** | **21.5** |
| 5 | 48.0° | 20.2 | 17.1 — below floor |
| 6 | 40.0° | 17.2 — below floor | 14.1 — below floor |
| 8 | 30.0° | 13.3 — below floor | 10.3 — below floor |

Only `B = 4` clears the floor on both canvases. So:

> **The region adjacency graph must be 4-colourable.**
> `build_region_palette.py --check` fails and names the regions that force a
> fifth colour; the fix is to merge or re-cut them.

This constrains the *shape* of the registry, never the *number* of regions —
twenty regions fit in four bands as easily as eight do, which is what keeps the
owner's directive intact.

#### The measured floors

Computed with CIEDE2000 over the whole hue circle at 3° steps:

| | light L=0.70 | dark L=0.52 |
|---|---|---|
| Label text (`--ink`) on the fill, worst hue | **4.98 : 1** | **4.56 : 1** |
| Adjacent regions (≥60° apart), normal vision | **ΔE00 24.3** | **ΔE00 21.5** |
| Adjacent regions at the theoretical maximum 90°, deuteranopia | ΔE00 9.6 | ΔE00 11.4 |
| Same, protanopia | ΔE00 8.5 | ΔE00 10.4 |

> **Adjacent-region separation: ΔE00 ≥ 20 — a floor.** The construction above
> delivers 21.5 at worst. `build_region_palette.py` fails and names the pair
> rather than shipping an assignment it cannot satisfy.

> **Label contrast on a region fill: 4.5 : 1 — the existing floor**, met at 4.56
> at worst. The lightness values are chosen for this and nothing else.

An earlier draft of this spec set the separation floor at ΔE00 ≥ 20 measured over
*all* pairs. That is unsatisfiable at every N — the best achievable is 18.1 at
N=8 and 6.8 at N=20 — and it is recorded here so the number is not reintroduced.
Constraining *adjacent* pairs instead is what makes 20 reachable.

**The shape of a region is carried by its stroke, not by fill-against-canvas
contrast.** The worst hue reaches only 2.48 : 1 against white, and no lightness
fixes it — raising L improves the label and worsens the edge. WCAG 1.4.11 is met
by the boundary instead:

> **Every region carries a boundary stroke clearing 3 : 1 against the canvas.**
> The stroke is the region's own hue at `L ∓ 0.20` — darker on the light canvas,
> lighter on the dark one — so the boundary reads as the region's edge rather
> than as a separate grid. Measured worst case: **5.64 : 1** against white,
> **5.96 : 1** against `#1D1D1F`.

#### Text carries identity, always

At the theoretical maximum separation of 90°, deuteranopia collapses ΔE00 to 9.6.
That is the best case, and real maps are at 60°. So the rule is unconditional
rather than triggered by a hue count:

> **Every coloured region carries a label or a legend entry.** Hue separates
> neighbours at a glance; text carries identity.

An earlier draft made this conditional on more than 8 hues. The measurement above
does not support a threshold, and an unconditional rule is the one
`check_design.py` can check without counting hues.

### State

State rides a second channel so hue stays free for identity, and it reuses the
vocabulary already in the tree — `live / zero / out` from
`build_geography.py`'s `MARKERS`, plus `partial`, which the tokens already define
as amber:

| State | Treatment |
|---|---|
| `live` | solid fill at full hue |
| `partial` | solid fill, amber boundary stroke |
| `zero` | same hue at wash strength, dashed boundary, muted label |
| `out` | `brass`, no region hue — it is out of scope, not uncovered |

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

**0.35° — a ceiling on simplification error.** Coarser and the set starts losing
countries: 0.6° drops thirteen including Qatar and Cyprus, which a trade map
cannot lose.

**Simplification must be topological, and the table above is not.** Those figures
come from simplifying each country's rings independently, which is the wrong
algorithm here: a shared border simplified twice produces two different lines, so
neighbouring countries develop slivers and overlaps. At 0.35° on a 1280 px world
map one degree is about 3.5 px, so the artefacts are **1–2 px and plainly
visible** — and they fall exactly where form 2 needs two countries of one region
to merge seamlessly.

So the geometry ships as **shared arcs**, TopoJSON-style: every border is stored
once, simplified once, and referenced by both countries. This buys three things
at once —

1. no slivers, and region fills that dissolve cleanly;
2. **adjacency for free**: two countries are adjacent exactly when they share an
   arc, so the region adjacency graph below is a lookup rather than a geometric
   test;
3. a smaller file, since each border is stored once.

The 70 KB above therefore stands as an **upper bound**. The exact size is an
output of the encoder, not an input to this design, and the 110 KB ceiling below
holds either way. A ~2 KB decoder ships with `worlddata.js`.

**Total added weight to a deliverable: 110 KB before compression — a ceiling.**
25 KB gzip of geometry plus the runtime. `d17_export_weight` counts `<path `
occurrences, so a page carrying the globe will dominate that report; D17 is
reported and never gating, and the CHANGELOG entry says so, because a reviewer
who sees the spike without the explanation will read it as a regression.

**110m has no Singapore, Hong Kong, Bahrain or Malta** — upstream merges them
away at this scale, and the 50m set that carries them is 3 MB raw.

**Polygons are areas; nodes are points.** Country geometry comes from 110m; city
states and ports ship as a separate `nodes` point layer keyed by lat/lon. Cheaper
and more honest — a port is a point — and it is the pattern
`build_geography.py`'s `MARKERS` already uses. Accepted by the owner as
sufficient.

**Two geographies now live in this repository, and that is a drift hazard.**
`build_geography.py` keeps its hand-written 2° `LAND` and this design adds the
110m set. They will disagree about where a coastline is. Re-deriving the coarse
set from 110m would change `globe-orthographic.svg` and `world-flat.svg`
byte-for-byte — that is, it would change the shipped cover mark — so it is **not**
done here. Instead the rule, which goes in `design-rules.md`:

> The coarse set is a **mark** and the 110m set is a **map**. A document may use
> either and must never place both in one view.

Re-deriving is a later increment with its own retrospective.

**Region registry** (`assets/vectors/regions.json`): `ADM0_A3 → region_id`, plus
each region's display name (English and Chinese) and label anchor. It ships a
generic trade-bloc default and a document may replace it wholesale.

**The adjacency the 4-colouring runs on is computed from the geometry, never
written by hand.** Two regions are adjacent when any of their countries share an
arc — a lookup in the topology of §6, not a geometric test. A hand-maintained
adjacency list beside real geometry is this repository's documented hazard in its
purest form: correct on the day it was written, silently wrong after any change
to the registry.

Invariant, checked by `check_repo.py`: **every country maps to exactly one region
— no gaps, no duplicates.** A country reaching the renderer with no region is a
hole in the map, and a silent one.

The Chinese names in both JSON files are label *data* for Chinese-language
output, the same standing the banned-phrase lists have. The English-only red line
binds repository prose and `check_repo.py` scans Markdown only, so no allowlist
entry is needed.

---

## 7 · Interaction, data, failure

**Hit testing is inverse projection, not an ID buffer.** `invert(x, y)` recovers
`(lon, lat)`; a bbox prefilter narrows candidates; spherical point-in-polygon
decides. An ID buffer would need a second full draw per frame while dragging, or
would go stale mid-drag. Inverse projection is valid at every `t` and adds one
function rather than a second render path. The field layer picks by screen
distance to the projected mark: **12 px — a floor**, giving a 24 px target, which
is WCAG 2.2 SC 2.5.8.

**Drag is an arcball.** Mapping horizontal pixels to longitude stops tracking the
pointer at high latitude. Both the grab point and the current point are inverted
to sphere vectors and the rotation between them applied to the view, so the point
under the cursor stays under it. Release decays angular velocity exponentially;
**rest within 0.9 s — a ceiling**, because a longer glide reads as the component
ignoring the release.

**Data contract.** The host document supplies one JSON object:

```
{ regions: { <region_id>: { value, state } },
  marks:   [ { lon, lat, weight } ],
  nodes:   [ { id, value, state } ] }
```

`state ∈ {live, partial, zero, out}`, the vocabulary of §5. No value is invented
by the component and no default number ships — a region absent from the object
renders as `zero`.

**Failure behaviour**, explicit because a silent failure is worse than a visible
one:

| Case | Behaviour |
|---|---|
| Geometry file missing or unparseable | Render nothing, log one error, leave the container's static SVG in place |
| Region id in host data, absent from registry | Ignored for rendering, **named in one console warning** — never silently dropped |
| Country in registry with no region | Cannot occur at runtime; `check_repo.py` rejects it at build time |
| Canvas 2D unavailable | Fall back to the SVG back end |
| `prefers-reduced-motion: reduce` | No auto-rotation, no inertia; form switch cuts rather than unrolls |
| Frame budget missed repeatedly | Watchdog pins the static frame and stops the loop |

**Performance.** The stages are the two `design-rules.md` §7 fixes as shipped:
1280×720 landscape (checked at 1920×1080) and 794×1123 A4. **SVG back end: 30 fps
at 1280×720 — a floor**, with the watchdog above rather than animating badly.
**Canvas back end: 4 ms per frame — a ceiling.** rAF pauses on
`IntersectionObserver` exit and on `visibilitychange`. Geometry decodes once;
projected results write into reused `Float32Array`s so no per-frame allocation
reaches the collector.

**Accessibility is part of the component.** In the SVG back end each region is a
real element carrying `role="img"` and an `aria-label` of name and value. The
canvas back end maintains a parallel hidden DOM layer of one `<button>` per
region, so the two back ends are equivalent to a screen reader. Arrow keys
rotate, `+`/`-` zoom, Tab moves between regions, Enter selects — the same state
machine the pointer drives.

**Events.** `regionenter`, `regionleave`, `regionselect`, `formchange`, each
carrying the region id, so the host document owns tooltips and panels rather than
the component inventing chrome.

---

## 8 · Testing

**This repository contains no JavaScript and CI cannot check any.** There is no
`package.json` and no `.js` file; `ci.yml` runs `py_compile` over a fixed list of
Python scripts and `bash -n` over two shell scripts. Adding seven JS modules
without answering this would create the largest untested surface in the package.

1. **Python is the authority for the maths.** The projection functions move to
   `geo_projection.py` and are exercised by `build_geography.py`, whose `--check`
   runs in CI. To be exact about what that proves: `--check` is a **currency**
   check — it shows the emitted SVGs match the code, not that the projection is
   correct. Correctness comes from the golden fixture below and from the existing
   round-trip properties (`_crossing` lands on the limb, `_on_limb` within 0.5).
2. **A tracked golden-vector fixture.** `build_worldmap.py` emits
   `fixtures/globe-golden.json` — a grid of `(lon, lat, t, view) → (x, y, visible)`
   samples computed in Python. `fixtures/` is otherwise owned by
   `build_fixtures.py`, which iterates its own two named targets and does not
   scan the directory (`build_fixtures.py:565`), so an added file causes no
   conflict and no script needs teaching. Currency is guarded by
   `build_worldmap.py --check` in CI, so the fixture cannot rot.
3. **`scripts/check_globe.py` — a new operator check.** Loads the JS modules in
   headless Chromium, evaluates `project`/`invert` over the golden grid, asserts
   agreement to 1e-9 and `invert(project(p)) == p` round-tripping. It needs
   Playwright, so like `check_prose.py`, `check_design.py` and
   `inspect_layout.py` it **cannot run in CI**, and the checks table in CLAUDE.md
   says so in the same words.
4. **Fixture defects for the new metrics.** `fixtures/expected.json` asserts every
   metric on both `deck-pass.en.html` and `deck-broken.en.html`, and
   `check_fixtures.py` runs in CI. Both new metrics — the region label anchor in
   `check_design.py`, region coverage in `check_repo.py` — ship with a planted
   defect in the broken fixture and an asserted verdict on both. Without this the
   metric is decorative; that file's own comment records that ten of thirteen
   design metrics once had no assertion on either side.

**What no automated check can see** (CLAUDE.md 8): polygons popping at the cull
threshold, label collisions near the limb, the antimeridian seam at `t = 1`, and
whether the unroll reads as one motion. Screenshot both forms ×
`t ∈ {0, 0.5, 1}` × light and dark × both stages and look at them.
`inspect_layout.py` already produces contact sheets and gets wired to it.

Two of its `--deliverable` findings do gate and both can fire on this figure: **a
drawing clipped by its own viewBox** — the globe's limb sits exactly on the
viewBox edge, which is how that defect was found in the first place — and **a
lost datum**. The static SVG that `globe_svg.py` emits must clear both, so
`globe_svg.py` sizes the viewBox from the projected extent at the requested `t`
rather than from a fixed square.

---

## 9 · Repository integration

New:

- `assets/vectors/world-110m.json`, `assets/vectors/regions.json`
- `assets/globe/*.js` — the seven modules of §3
- `scripts/geo_projection.py`, `build_worldmap.py`, `build_region_palette.py`,
  `globe_svg.py`, `check_globe.py`
- `fixtures/globe-golden.json`

Changed:

- `scripts/build_geography.py` — projection extracted (its own commit, §3)
- the three `tokens/` files — region-hue spec and the version stamp
- `SKILL.md`, `README.md`, `CHANGELOG.md`, `CLAUDE.md` (checks table, `specs/` note)
- `references/design-rules.md` — region colouring, the label rule, the mark-versus-map rule, the globe's place in the figure vocabulary
- `NOTICE` — Natural Earth, public domain
- `scripts/check_repo.py` — region coverage, adjacency separation
- `scripts/check_design.py` — label anchor per coloured region
- `fixtures/deck-broken.en.html`, `fixtures/expected.json` — the planted defects
- `.github/workflows/ci.yml` — new Python scripts join `py_compile` and the `--check` sequence
- generated artifacts — `SKILL.md` feeds `build_entrypoints.py`, whose `--check` runs in CI, so the derived tree is rebuilt in the same commit

Per CLAUDE.md 3 this is a rule revision: one version bump across the five places
that carry a version, and a CHANGELOG entry. The entry records the case honestly
— an owner directive, the rejected 8-hue ceiling, the unsatisfiable ΔE floor that
the first draft carried, and the rules that replaced them.

**Commit order**, because two of these are only readable in isolation:

1. Extract the projection. `build_geography.py --check` must stay green with no
   byte change to either SVG.
2. Data pipeline and palette generator, with their `--check` modes.
3. The JS modules, `check_globe.py`, and the golden fixture.
4. Rules, tokens, metrics and fixture defects — the version bump lands here.

---

## 10 · Out of scope

Zoom beyond a single globe (no tiling, no level-of-detail switching), choropleth
animation over time, route and arc rendering at runtime, re-deriving the coarse
mark geometry from 110m (§6), and any WebGL path.

## 11 · Noted, not fixed here

`CLAUDE.md` describes `check_design.py` as carrying "design metrics (D1-D6)". It
ships D1 through D17. Out of scope for this change and worth its own correction.
