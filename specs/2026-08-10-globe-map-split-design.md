# The globe and the map become two components — design

Date: 2026-08-10 · Written against 0.1.390 · Status: approved by the owner;
supersedes the product decision at the head of
`2026-08-09-lumi-globe-design.md`, which stays as history.

---

## 1 · The decision being reversed, and the case for reversing it

The globe spec opens with: *"A world figure that carries LUMI's palette and both
brand devices, in two forms: a **field** of discrete marks on a globe, and a
**region** map that unrolls flat. One projection, one geometry model, no
third-party runtime dependency."* One component, two forms, and the `t` unroll
animation joining them.

The owner has reversed it (owner directive, 2026-08-10 — a documented case
under maintenance convention 2): **two separate frontend components**, designed,
developed and verified separately, each configurable per instance with its own
regions and colours, each usable in its own scenarios.

The documented case is the first delivered demo, audited in §2. The audit
supports the reversal on three independent grounds:

1. **One of the two forms was never built.** The field form has no mark data
   path at all: `hostData.marks` is documented in `globe.js` and read by
   nothing, `globe_svg.py` has a `marks=` parameter and no `--marks` flag, and
   `embed_globe.py` never passes marks. A "component with two forms" where one
   form has no data is one component wearing two names.
2. **The joins are where the defects live.** Every entanglement point between
   the forms is broken in a way neither form is broken alone: `setForm` toggles
   CSS classes that no stylesheet defines; `render-canvas.js` branches on a
   `state.form` that `globe.js` never sets; a `--form both` frame double-draws
   with JavaScript off; the a11y layer builds region buttons under the field
   form. The shared *maths* has held (0.1.389's golden grid and parity checks);
   the shared *product surface* has not.
3. **The unroll — the feature the coupling exists to serve — is unreachable.**
   The delivered demo ships zero controls. Nothing in the package emits a
   control, so every deliverable author must hand-write the trigger for the
   component's headline feature, and the first real one didn't.

## 2 · The demo audit (the documented case)

`~/Documents/LUMI-Style/globe-demo.en.html`, assembled 2026-08-10 10:29 by
`_sources/globe-demo/assemble.py`. Two root causes.

**Stale build.** Assembled two hours before 0.1.389 merged (12:47). The inlined
runtime carries `boundaryFor`/`boundaryWalk` (shorter-by-index) and the t=1-only
`poleClose`; `clipToCap`/`signedArea` are absent. Both static frames were
emitted by the pre-fix generator. The figure at t=0 autorotates, so the
superseded clip re-runs every frame — the polar spill 0.1.389 fixed is live in
the deliverable.

**Defects that survive a rebuild** (each verified against the current tree):

| # | Defect | Where |
|---|---|---|
| 1 | Region hues shipped, never bound: no `.rg-*` rule in `tokens/`, black regions for any document that does not hand-write ~88 rules | `tokens/region-palette.css` + every consumer |
| 2 | `.is-hover` has no rule anywhere — hover works and shows nothing | runtime toggles it; no CSS ships |
| 3 | `outline:none` with no `:focus-visible`; `tabindex="0"` set by the runtime | demo CSS + `globe.js:225` |
| 4 | `--gl-plate/-graticule/-land/-land-edge` custom properties read by the canvas back end, defined nowhere — canvas paints transparent | `render-canvas.js:85-88` |
| 5 | JS-off `--form both` frame draws land and all 11 regions stacked | `globe_svg.py` emits bare `class="gl"`; `form-*` added only at boot |
| 6 | No authored controls; `setForm`/`unroll`/`setT` unreachable | `embed_globe.py` ships no chrome |
| 7 | Second figure never booted (`data-globe` on one element only) | assemble.py |
| 8 | a11y double-announcement: region `<button>` list built even on the SVG back end, whose paths already carry `role="img"` | `globe.js:152-177` |
| 9 | `aria-label="{name}, {state}"` — the spec asked for name and VALUE — and the renderer never updates it, so it goes stale on `setData` | `globe_svg.py:297-299`, `render-svg.js` |
| 10 | Legend decorative (`data-legend` listened by nothing); fixture `<title>` leaked into the deliverable | assemble.py |
| 11 | `regions.json` carries `anchor:[lon,lat]` and `z` (Chinese name) per region — read by nothing; no renderer draws a region label, so D18 forces every document to hand-author a legend | registry + all renderers |

## 3 · Decisions (owner, 2026-08-10)

1. **The unroll retires.** The globe pins `t=0`; the map pins `t=1`. The shared
   projection core keeps `t` internally — the 1300-sample golden grid, the
   clip-invariant checks and the t∈(0,1) markup sweeps that guard 0.1.389's
   winding work all stay, moved to a shared suite. `--form both`, `setForm`,
   `unroll`, `setT`, `formchange`, `unrollstart/end` are deleted, not
   deprecated: a half-retired flag is a standing stale promise.
2. **`tokens/` ships the bindings.** `build_region_palette.py` generates,
   beside the custom properties, the rules joining them to the classes the
   emitters write: `.rg-<id>` fill/stroke, the state classes, `.is-hover`,
   `:focus-visible`, and the `.gl-*` base chrome with its `--gl-*` variables.
   One include paints the figure. This closes the question 0.1.390's changelog
   left open, in the direction maintenance convention 5 demands.
3. **Chinese type uses the default stack.** No CJK face is vendored. The
   embed-the-face rule is scoped to the Latin faces the package ships; Chinese
   deliverables state the system-font fallback. (This also unblocks the
   rendered Chinese fixture — separate work, not this change.)

## 4 · The two components

**Shared core — one library, unchanged maths.** `assets/geo/`: `projection.js`
(with `t`), `worlddata.js`, `pick.js`. Python mirror `scripts/geo_projection.py`
(the authority) and a new `scripts/geo_frame.py` holding the frame assembly both
emitters share (`_load`, `_rings_of`, `_project_ring`, `_project_area`,
`_pole_close`, `_guard`, `_d`, `extent`). The golden grid is the lock, as it has
been since 0.1.387.

**Component A — the globe** (`assets/globe/`): a rotating orthographic globe
carrying a field of marks. `createGlobe(container, {topology, registry, marks,
autorotate, interactive})`. `t` pinned to 0. Keeps `controls.js` (arcball,
inertia, keys) and both back ends; the canvas back end draws the field only —
its regions path and the dead `state.form` branch are deleted. Mark contract:

    marks: [{lon, lat, weight, label?, id?}]     weight >= 0

Radius scales with `sqrt(weight)` (area encodes quantity) between token bounds
`--gl-mark-r-min/-max`; culling by the shared visibility test; marks render as
`class="mk"` circles. A11y: a visually-hidden list, one entry per mark,
"{label}, {weight}" — the region buttons leave this component. Static emitter:
`globe_svg.py` (drops `--form`, gains `--marks`). Embed: `embed_globe.py`
(drops `--form`, gains per-element `data-globe-marks="#json-id"`).

**Component B — the region map** (`assets/regionmap/`): a flat map with regions
coloured by identity. `createRegionMap(container, {topology, registry,
hostData: {regions: {id: {state, value}}}, labels: 'en'|'zh'|'none',
interactive, classPrefix})`. `t` pinned to 1. SVG only — a static map has no
frame loop, and the deliverable embed order has always excluded the canvas. No
arcball. Labels emitted as `<text>` at the registry's `anchor` from `n`/`z` —
wiring the two fields nothing has ever read, and giving D18 a component-emitted
answer. A11y: the one-button-per-region list moves here;
`aria-label="{name}, {value}"`, kept current by the renderer on `setData`.
Static emitter: new `scripts/regionmap_svg.py` (root `class="regionmap"`, not
bare `gl`). Embed: new `scripts/embed_regionmap.py`, booting
`[data-regionmap]`, states via an adjacent
`<script type="application/json">` — no fetch, file://-safe.

**Per-instance configuration** (the owner's "different regions and colours,
different scenarios"): `build_region_palette.py --regions <path> --out <path>
--prefix <cls>` emits a scoped palette+bindings block so two maps with
different registries coexist on one page; `--regions` plumbed through
`regionmap_svg.py`, `embed_regionmap.py` and `geo_frame.py`. The contrast and
ΔE floors run against whatever registry is given — the floors are the contract,
not the registry. `check_repo.py::check_region_coverage` keeps guarding the
default registry only; a custom registry is validated by the CLI (no
double-claimed members, members exist, nodes name real regions) with full
coverage optional, because a scoped map legitimately covers less than the
world.

## 5 · Verification re-cut

`check_globe.py` stays one file, gains `--suite shared|globe|map` (default all;
CI's `--python-only` invocation unchanged):

- **shared**: round trip, poles, culling, seam, clip invariants, viewbox
  extent, decoder, port parity — plus the t∈{0, 0.5, 1} static-svg and
  seam-segment sweeps re-pointed at both emitters. The t=0.5 rows are the
  0.1.389 regression guard and outlive the pinned products.
- **globe**: field frame sanity, marks markup, and field renderer parity
  (SVG vs canvas) — the parity gap that has existed since the canvas back end
  was written closes here.
- **map**: map frame sanity, the existing regions renderer parity re-homed,
  labels present at anchors, `.rg` classes ⊆ the tokens bindings.

Browser assertions extend the existing Playwright sessions; the suite adds no
new browser boots. Every new graded verdict gets a failing case (the 0.1.390
coverage guard enforces this mechanically).

## 6 · Sequencing and the two hard constraints

Five releases: (1) this spec + the tokens bindings + the font rule; (2) the
shared-core re-layout, byte-identical; (3) the map component, built beside the
untouched globe; (4) the globe rework and the retirements, with every document
that teaches `--form` re-flowed in the same release; (5) per-instance
configuration. The demo rebuild happens outside the repository afterwards, as
two documents.

The two constraints that must not be violated: **(3) and (4) do not merge** —
otherwise a commit exists in which the repository can draw no region map; and
**nothing regenerates the golden grid** — it is form-agnostic by construction,
and it is the only thing holding the JavaScript port to the Python authority.

---

## 8 · Audit against the shipped tree, and what it corrected (0.1.396)

The owner asked for a full audit of the delivery against these specs. It was
run over all three records against 0.1.395 and produced one bug report, a list
of unkept promises, and a list of phantom options. This section records the
findings and the decisions, so the next reader of these specs is reading
something true.

### The bug the audit did not find — a reader did

**`hidden` does not hide an SVG shape.** The emitter wrote ` hidden` on every
far-side mark and node and the runtime toggled it per frame. In a browser a
`<circle hidden>` computes `display: inline` and keeps its full bounding box,
so every point on the BACK of the sphere kept drawing — at its orthographic
position, which for a far-side point lands INSIDE the visible disc. Twelve dots
slid across the geography on every frame of a shipped deliverable.

Nothing here could see it, and the reason is the fifth instance of one pattern:
**every gate in this package reads markup, and `hidden` reads correct in
markup.** The comment at `globe_svg.py:107` even asserted "`hidden` is
honoured". Fixed by `display="none"`, a real SVG presentation attribute that
needs no stylesheet, so the JS-off frame hides them too. The new check
(`check_far_side_hidden`) measures `getBoundingClientRect().width` in a browser
and refuses to believe an attribute.

### Promises this release kept that the audit found unkept

- **`--suite globe` contained zero checks.** The suite flag shipped in 0.1.394
  and its contents did not; §5's "field frame sanity, marks markup, field
  renderer parity" was a promise with no code behind it. Two checks now fill it.
- **`.is-hover` regressed onto the globe.** §2 defect 2 was closed for regions
  in 0.1.391 and reopened by 0.1.394, which toggled the class on marks and
  nodes against no rule at all. `tokens/` ships both now.
- **The globe's event vocabulary was wrong.** A mark click announced itself as
  `nodeselect`; `globe.js`'s own header advertised a `markselect` that was
  emitted nowhere; hover used a `pointenter`/`pointleave` pair no spec names.
  Now `markenter/markleave/markselect` for data and `nodeenter/nodeleave/
  nodeselect` for places.
- **The theme re-read was deleted with the form machinery.** `render-canvas.js`
  snapshots the palette at construction and its `readPalette()` had no caller,
  so a canvas globe held the light palette through a theme flip.
- **The watchdog could not fire** outside the autorotate branch, and
  `visibilitychange` resumed a globe that was scrolled out of view.
- **`lon0` accumulated without bound**, spending precision on a number whose
  only meaningful part is the remainder.

### Dead weight removed

The globe's region layer (`render-svg.js`), `ringsOfRegion`, and the per-region
bounding-box index — the last of which walked every arc of every member on
every boot of every deliverable to build a Map whose only consumer, the
hit-test prefilter, died with `pickRegion` in 0.1.394.

### Phantom options — the spec was wrong, not the code

These appear in §4 above and were never implemented. They are corrected here
rather than built, because in each case the shipped choice is the better one:

- **`class="mk"`** — marks ship as `gl-mark`, consistent with `gl-node`,
  `gl-land` and the rest of the figure's vocabulary.
- **`--gl-mark-r-min/-max` tokens** — the radius rule lives in the two
  renderers and is parity-held. CSS cannot size a canvas mark, so a token
  binding one back end would be a divergence wearing a token's clothes.
- **`data-globe-marks="#json-id"`** — marks reach the runtime by being baked
  into the frame, which is the same path that makes the JS-off document
  correct. A second path would let the two disagree.
- **`createRegionMap({topology, labels, classPrefix})`** — `topology` is not
  needed by a runtime that touches no geometry; `labels` is an emit-time
  decision because the text is baked into the frame; `classPrefix` is the
  palette generator's `--prefix`, and belongs to the CSS, not the runtime.
- **`createGlobe({interactive})`** — implemented for the map, where a static
  figure is a real use; the globe's whole subject is a rotating field, and a
  non-interactive one is a still image, which `globe_svg.py` already emits.
- **Host-supplied node `value`/`state`** (2026-08-09 §7) — nodes are places
  from the registry, not data. A datum is a mark.

### Recorded and still open

- **The canvas back end is unreachable from any deliverable** — `embed_globe.py`
  turns its dynamic import into a rejected promise, by design, since a
  deliverable must be SVG. It is verified against the SVG renderer by the
  parity check but no shipped artifact runs it.
- **The 30 fps floor and the 4 ms canvas ceiling are unmeasured.** The watchdog
  enforces the first at runtime; neither is asserted by a check.
- **No deliverable consumes a component event.** §7 hands tooltips and panels to
  the host document and nothing has ever exercised that. The trade-bloc map is
  where it gets built.
