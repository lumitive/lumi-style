# Carrying winding through the clip — design

Date: 2026-08-10 · Written against 0.1.388 · **Status: implemented in 0.1.389,
option A. §7 records what implementation found that this design did not.**

0.1.388 shipped the globe with two recorded defects and one sentence of
diagnosis: *the limb walk picks the arc that is shorter BY INDEX, and the correct
arc is the one that keeps the polygon's interior on the correct side.* This
record is the result of taking that sentence apart. The diagnosis was right and
incomplete. Fixing only what it names makes the figure **worse** — measurably so,
and the measurement is in §3.

---

## 1 · What is recorded today

| Entry | Where | What it holds |
|---|---|---|
| `KNOWN_FLAT_CLOSURES` | `scripts/check_globe.py:267` | `("field", 0.25)`, `("field", 0.5)`, `("regions", 0.5)` |
| `KNOWN_RENDERER_DIVERGENCE` | `scripts/check_globe.py:347` | `("t0.5_lon0.0", "oceania")` |

Both are two-way locks: a fourth flat closure fails the check, and so does
fixing one of the three without deleting its line. That design is why this change
cannot be done quietly, and it is the right design.

The code under them is `_boundary_walk` (`scripts/globe_svg.py:179`) and its
mirror `boundaryWalk` (`assets/globe/render-svg.js:103`). Both choose by index
distance:

```python
fwd = (ib - ia + n) % n
if fwd <= n - fwd: ...        # the shorter way round
```

`scripts/geo_projection.py:122` `limb_walk` — the static generator's copy, used
by `build_geography.py` — makes the same choice by angle rather than by index.
Three implementations, one rule, and the rule is wrong.

---

## 2 · Four findings, all measured

### 2.1 The direction rule is derivable, not a guess

The topology carries real winding. Over all 278 rings in
`assets/vectors/world-110m.json`, the Chamberlain–Duquette signed spherical area

```
A = ½ Σ (λ₂−λ₁)(2 + sin φ₁ + sin φ₂),   λ differences wrapped to (−180°, 180°]
```

is **positive for 277 and negative for exactly one** — South Africa's second
ring, the six-point hole that is Lesotho. Every ring is closed; none is
degenerate. So the data distinguishes an outer ring from a hole, and the sign of
that integral is the distinction.

A cap of angular radius `c` traversed with azimuth increasing scores positive by
the same integral (`c=5°` → `+0.0239`, `c=30°` → `+0.8417`, both equal to the
true area). Azimuth increasing runs N→E→S→W, which is interior-on-the-right seen
from outside. **So positive means interior on the right, and the cap sampled in
`_boundary`'s own azimuth order already has that handedness.**

Both operands then carry the same orientation, and the standard result applies:
the boundary of `P ∩ D` uses the arcs of `∂D` **in `∂D`'s own direction**. The
rule is therefore

> walk the boundary array **forward** for a ring with positive signed area,
> **backward** for a negative one (a hole).

No index distance anywhere. It does not depend on `t`, `lon0` or `lat0`, it is
four lines in each renderer, and it is trivially identical across the port.

### 2.2 That integral must never be applied to the cap

The sign flips at a hemisphere. Measured, same function, azimuth increasing:

| cap radius `c` | signed | true area | note |
|---|---|---|---|
| 30° | `+0.8417` | `0.8418` | agrees |
| 89° | `+6.1732` | `6.1735` | agrees |
| **90°** | `+3.6312` | `6.2832` | already wrong |
| 91° | `−6.1732` | `6.3928` | sign flipped, reports the complement |
| 120° | `−3.1414` | `9.4248` | `= −(4π − true)` |

The visible cap is `c = acos(−t)`, so it is **larger than a hemisphere for every
`t > 0`** — 104.5° at `t=0.25`, 120° at `t=0.5`. Deriving the cap's handedness
from its own signed area would silently invert the walk for the entire animated
range. §2.1 avoids this by taking the cap's handedness from the azimuth
parameterisation, which is exact at any radius, and reserving the integral for
country rings, all of which sit far below a hemisphere (the largest, Russia, is
`0.41` sr against `12.57` for the sphere).

This is the trap the change has to be designed around, and it is invisible until
`t` leaves zero.

### 2.3 The boundary polyline is not a closed curve at `t > 0`

This is why the diagnosis in the changelog is incomplete, and it is the finding
that reshapes the change.

`_boundary` builds 240 samples in azimuth order and projects each through
`unrolled`. `unrolled` wraps longitude into `(−180°, 180°]` before mixing in the
equirectangular term, so the sampled ring **jumps the full width of the seam,
twice, at every `t > 0`**:

| `t` | jumps > R/4 | at samples | width | seam verticals sit at |
|---|---|---|---|---|
| 0.0 | 0 | — | — | — |
| 0.25 | 2 | 0, 120 | 511.0 | x = 750.0 / 1250.0 |
| 0.5 | 2 | 0, 120 | 1004.1 | x = 500.0 / 1500.0 |
| 0.75 | 2 | 0, 119 | 1498.8 | x = 250.0 / 1750.0 |
| 0.9 | 2 | 0, 119 | 1797.5 | x = 100.0 / 1900.0 |

(`R = 1000`, `lon0 = 0`, `cx = R`.) The jump lands exactly on `x = cx ± tR`,
which is where the seam maps: at `λ = ±180°` the orthographic term `xs = cos φ
sin λ` vanishes, so `x = ±tR` regardless of latitude. **The seam is a pair of
vertical lines and the boundary array steps across the figure between them.**

Every recorded flat closure is one of those steps. Their widths — 511 at
`t=0.25`, 996 at `t=0.5` — are the jump widths above.

The consequence for any fix: a walk that is allowed to run *further* along the
boundary crosses these jumps more often, not less. A prototype implementing §2.1
alone, with run linking, was measured against the flat-segment probe:

| form | `t` | flat segments before | after §2.1 alone |
|---|---|---|---|
| field | 0.25 | 1 | **114** |
| field | 0.5 | 1 | 1 |
| regions | 0.25 | 1 | **114** |
| regions | 0.5 | 1 | 1 |

The index-shortest rule was not merely wrong; it was **accidentally suppressing a
second defect** by almost never walking far enough to meet a jump. Removing it
without repairing the boundary trades three recorded flat closures for a hundred
and fourteen.

### 2.4 The clip boundary is not only the cap

Following 2.3 to its end: the region actually drawn at `0 < t < 1` is the cap
*cut open along the seam*, and a cut has edges. Its boundary has three kinds of
piece, and only the first is modelled today:

1. **cap arcs**, where `cos c = −t`;
2. **seam verticals**, `x = cx ± tR` — derived above, exact;
3. **pole edges**, `y = cy ∓ R(1 − t/2)` — a pole is a point on the sphere and a
   segment on the unrolled map, spanning `x ∈ [−tR, +tR]`.

`_pole_close` (`scripts/globe_svg.py:200`) already knows the third expression —
`half = R * (1 - t / 2)` — and is restricted to `t = 1` because firing it
anywhere else drew a box under the globe. That restriction is a symptom: the
pole edge is real at every `t > 0`, and closing along it only misbehaved because
the other two pieces were missing, so a piece ending on a seam vertical was
matched to a pole edge instead.

At `t = 1` the cap is the whole sphere and pieces 2 and 3 are the whole
boundary, which is why the flat map is correct today. At `t = 0` the seam
verticals collapse to `x = cx` and the pole edges to points, leaving the cap
alone, which is why the globe is correct today. **Everything between is where all
four recorded defects live, and it is exactly the range that has no complete
boundary model.**

---

## 3 · What this means for the change

The change is not "pick the other arc". It is:

1. Build the clip boundary in **`(lon_rel, lat)` parameter space**, where the
   seam is the domain's own left and right edge and therefore not a
   discontinuity, then project it. Trace: cap arcs where the cap constrains,
   seam verticals and pole edges where the map's cut does.
2. Walk it in the direction §2.1 gives, from each run's exit to the next entry
   encountered — linking a ring's runs to each other rather than closing each on
   itself, which is what makes a country cut into two visible pieces close as one
   polygon.
3. Delete `_pole_close` as a special case; it becomes the `t = 1` limit of the
   traced boundary.
4. Mirror all of it in `assets/globe/render-svg.js` and `render-canvas.js`,
   held by the golden grid.
5. Apply the same direction rule to `geo_projection.limb_walk` for
   `build_geography.py`. Its eight hand-coded rings have **accidental** winding —
   `maritime-se-asia` and `australia` score negative with no hole to justify it —
   so they are normalised to positive rather than trusted.
6. Delete both recorded entries in `check_globe.py`, which the checker requires.

---

## 4 · The open decision — the projection folds

**Half known.** `invert` (`scripts/geo_projection.py:162`) already documents the
non-injectivity from the inverse side — *"a point on the front of the sphere and
one on the back can land on the same pixel"* — and resolves it by returning the
root nearest the viewer. What was not recorded is the forward consequence
measured here: that the fold puts **drawn content outside the curve everything is
clipped against**. The two are the same fact seen from opposite ends, and only
one end had been written down.

`unrolled` calls a point visible when `zs ≥ −t`. For `t > 0` that admits a strip
of the **far** side of the sphere, and the orthographic term folds that strip
back over the front. Measured by the sign of the Jacobian of `(lon, lat) → screen`
over the visible set:

| `t` | samples with flipped orientation | where |
|---|---|---|
| 0.0 | 0 (2 degenerate, ~1e-8, at the limb) | — |
| 0.25 | 1488 | `cos c ∈ [−0.25, −0.107]` |
| 0.5 | 1428 | `cos c ∈ [−0.5, −0.318]` |
| 0.75 | 0 | — |

So the drawn image self-overlaps at intermediate `t`, and the `cos c = −t` curve
is **not** the silhouette:

| `t` | radius of the `cos c = −t` curve | radius reached by drawn content |
|---|---|---|
| 0.25 | 86.8 – 88.2 | 91.0 |
| 0.5 | 76.6 – 79.3 | **90.1** |
| 0.75 | 74.3 – 82.3 | 97.6 |

At `t = 0.5`, eleven units of content are drawn outside the curve everything is
being clipped and closed against.

This does not invalidate §2.1 — that rule is derived on the sphere, where the
clip is unambiguous, so the closure stays topologically correct and the fold is a
property of the projection, not of the clip. But it decides how much this change
is:

- **A · Clip only.** Ship §3, leave the fold. The recorded defects go, the
  figure stops spilling across the cap, and a narrow band near the limb still
  paints twice at mid-rotation. Smaller change, golden grid unaffected,
  `visible` semantics unchanged.
- **B · Clip and fold.** Additionally move the visibility threshold to the fold
  crease, so the drawn set is exactly the set the projection maps injectively.
  This changes `unrolled`'s third return value, which regenerates the 1300-sample
  golden grid, and the grid is the only thing holding the JS port to the Python.

**Recommendation: A now, B recorded as its own change.** B alters the one
artefact that certifies the port, and doing that in the same commit as a rewrite
of the clip means a grid disagreement has two candidate causes. A is also what
the recorded defects actually ask for. This mirrors 0.1.388's own reasoning for
deferring the winding question rather than bolting it on.

---

## 5 · How it will be verified

- The flat-segment probe over both forms × six `t` values, expecting **zero**
  with no recorded exceptions.
- Renderer parity over the existing frame set, expecting **zero** divergences
  with no recorded exceptions.
- Boundary continuity as a new assertion: no step in the traced boundary wider
  than a small multiple of its sample spacing — the invariant §2.3 shows was
  never held.
- Ring closure as a new assertion: for a ring wholly inside the cap the clip is
  the identity, and for one wholly outside it is empty.
- `check_globe.py --python-only` in CI; the full run, with Chromium, locally.
- `inspect_layout.py --deliverable` on a page carrying the figure, and a
  screenshot of each of the six `t` values looked at by a person — convention 8,
  which is what found these in the first place.

---

## 6 · What this does not do

- It does not change the palette, the region registry or any token.
- It does not touch `t = 0` or `t = 1` output, which are correct today; the
  golden grid and both fixtures must show them unchanged under option A.
- It does not address the fold (§4, option B).
- It does not add a rule to `references/`. This is a defect fix in a generator,
  not a rule revision, so it takes a version bump and a `CHANGELOG.md` entry
  under convention 3 and touches no rule prose.

---

## 7 · What implementation found that this design did not

Written after the fact, because a design record that only records what was
predicted is worth less than one that records where it was wrong.

**The route in §3 was not the route taken.** §3 proposed tracing the whole clip
boundary — cap arcs, seam verticals, pole edges — in `(lon_rel, lat)` space and
walking that. Implementation found a simpler decomposition with the same result:
clip to the cap **in azimuth on the sphere**, where the cap is a plain circle and
the seam does not exist at all, then hand the closed ring to the existing
`split_at_seam` and close each piece along the map's cut with `_pole_close`.
§2.4's derivation of the seam verticals and pole edges was still what made
`_pole_close` correct at every `t` instead of only at `t=1`; it just did not need
to be assembled into one traced loop. The finding survived; the plan for it did
not.

**Two defects survived every check in §5 and were found by looking at the
figure.** Both were caught by the contact sheet required by convention 8, after
the checks had gone green and the recorded entries had been removed.

1. **Antarctica painted over the whole disc at `t=0`.** Natural Earth closes its
   polygon along the `lat = -90` edge of a rectangular source map, so 181 of its
   433 densified points are a pole artifact rather than coastline. Where the cap
   passes through the poles they evaluate to `±6.1e-17` and read as interior,
   forming a phantom run whose ends carry the pole's own azimuth. A point ON the
   boundary is not INSIDE it — now `CAP_EPS`.
2. **The same figure filled again at a Pacific-centred view**, for an unrelated
   reason: the source ring's artificial break at `lon 180` delivers the visible
   coastline as two runs meeting exactly there, and a guard that read a
   zero-length arc as a full wrap turned the join into a 360-degree walk.

Both produce a closed path whose every point lies on or inside the cap with its
winding intact, so **both satisfied all six invariants this design proposed.**
The seventh, added in response, is the one that catches them: *a clip can only
remove area.* The full-disc closure returns 6.2965 sr from a 0.2985 sr input.

**Every invariant is now mutation-tested** — the fix reverted, the check
confirmed to fail — because §5 listed checks without asking whether any of them
could fail, which is item 3 of the backlog, in the design record for a release
whose subject is a check that could not.

**A known gap, recorded rather than closed.** One mutation — linking a run to its
own entry instead of the next run's — produces a geometrically wrong result too
small to trip the area invariant, and no check catches it. Asserting that the
run-to-run linking is a bijection would; it is not written.

**Three defects in the checker itself**, all found by using it rather than
reading it: `KNOWN_FLAT_CLOSURES` collected the pairs it saw and never compared
them, so its documented two-way lock only turned one way; the flat-segment loop
sat outside the per-path loop and examined one path per frame of twelve; and the
JS land layer was drawn without its `view`, so neither closure nor guard ran on
it. None was visible from the design, and all three were in the code this design
set out to fix.
