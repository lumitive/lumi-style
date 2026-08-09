# LUMI globe — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a LUMI-branded world figure in two forms — a field of marks on a
rotating globe, and a trade-region map that unrolls flat — rendered from data, in
LUMI's palette, checkable by this package's own gates.

**Architecture:** One projection authored twice (Python is the authority,
JavaScript is a verified port). Geometry ships as a shared-arc topology so
borders simplify once. Three render targets over one core: a Python-emitted
static SVG for print, the same SVG mutated at runtime for on-screen
deliverables, and Canvas 2D for the product site.

**Tech Stack:** Python 3.12 standard library only. Vanilla ES modules, no
bundler, no dependency. Playwright only for the two operator checks that already
need it.

**Source spec:** `specs/2026-08-09-lumi-globe-design.md`. Where this plan and the
spec disagree, the spec wins and the plan is wrong.

## Global Constraints

- **Standard library only.** No pip dependency may be added. Playwright is an
  operator-installed extra, never imported at module scope in anything CI runs.
- **No literal colour in any renderer.** Colours are read from CSS custom
  properties at runtime, or written by the palette generator. `grep -n '#[0-9A-Fa-f]\{6\}' assets/globe/*.js` must return nothing.
- **Colour tokens ship as sRGB hex, never `oklch()`.** `parse_color`
  (`scripts/check_design.py:104`) reads `#rgb`, `#rrggbb`, `rgb()`, `rgba()` and
  returns `None` otherwise, so an `oklch()` token makes D1 skip it silently.
- **Simplification tolerance 0.35° — a ceiling.**
- **Adjacent-region separation CIEDE2000 ΔE00 ≥ 20 — a floor.**
- **Label contrast on a region fill 4.5 : 1 — a floor.**
- **Region boundary stroke 3 : 1 against the canvas — a floor.**
- **Region hue lightness: OKLCH L = 0.70 light canvas, L = 0.52 dark. Chroma =
  92% of the per-hue sRGB gamut maximum. Four hue bands at 90k°, within-band
  spread ±15°.**
- **The region adjacency graph must be 4-colourable.** Only B = 4 clears the ΔE
  floor on both canvases.
- **Pick target 12 px radius — a floor** (24 px diameter, WCAG 2.2 SC 2.5.8).
- **Inertia rest within 0.9 s — a ceiling.**
- **SVG back end 30 fps at 1280×720 — a floor. Canvas back end 4 ms/frame — a ceiling.**
- **Total added weight to a deliverable 110 KB uncompressed — a ceiling.**
- **Repository language is English.** CJK in the new JSON files is label data and
  is fine; CJK in any `.md` or `.py` prose is a red-line failure.
- **Stages are 1280×720 landscape and 794×1123 A4** (`references/design-rules.md` §7).
- **Every new check script joins the `py_compile` list in `.github/workflows/ci.yml`.**
- **The version bump happens once, in Task 15**, across all five stamps.
  Do not bump in any earlier task.

## File structure

| Path | Responsibility |
|---|---|
| `scripts/geo_projection.py` | Sphere↔screen maths. Pure, parameterised, no I/O |
| `scripts/build_worldmap.py` | Upstream GeoJSON → shared-arc topology + adjacency + golden fixture |
| `scripts/build_region_palette.py` | OKLCH → hex region hues, 4-colouring, ΔE floor, CSS emit |
| `scripts/globe_svg.py` | One static SVG frame for a given view |
| `scripts/check_globe.py` | Python maths self-test (CI-safe) + JS-port agreement (Playwright) |
| `assets/vectors/world-110m.json` | The topology |
| `assets/vectors/regions.json` | Region registry, node point layer |
| `assets/globe/projection.js` | Port of `geo_projection.py` |
| `assets/globe/worlddata.js` | Topology decoder, region index, bboxes |
| `assets/globe/render-svg.js` | Deliverable back end |
| `assets/globe/render-canvas.js` | Site back end |
| `assets/globe/pick.js` | Hit testing |
| `assets/globe/controls.js` | Arcball, wheel, keyboard |
| `assets/globe/globe.js` | Public component |
| `fixtures/globe-golden.json` | Golden projection vectors |

---

### Task 1: Extract the projection, byte-for-byte

The riskiest change in the plan and the only one whose test already exists.
`scripts/build_geography.py` holds the maths in module-private functions against
a module constant `R = 150.0`. Two new callers need it parameterised.

**Files:**
- Create: `scripts/geo_projection.py`
- Modify: `scripts/build_geography.py` (delete the moved functions, import them)
- Test: `python3 scripts/build_geography.py --check` — the existing CI guard

**Interfaces:**
- Produces: `cos_c(lon, lat, lon0, lat0) -> float`,
  `project(lon, lat, lon0, lat0, R) -> (x, y)`,
  `ortho(lon, lat, lon0, lat0, R) -> (x, y) | None`,
  `crossing(inside, outside, lon0, lat0, R) -> (x, y)`,
  `visible_runs(points, lon0, lat0, R, exact=True) -> list[list[(x, y)]]`,
  `great_circle(a, b, n=96) -> list[(lon, lat)]`,
  `densify(ring, step_deg) -> list[(lon, lat)]`,
  `on_limb(p, R) -> bool`, `limb_walk(a, b, R) -> list[(x, y)]`

- [ ] **Step 1: Capture the current output as the test oracle**

```bash
cd /Users/he123/Downloads/lumi-style
mkdir -p /tmp/globe-oracle
cp assets/vectors/globe-orthographic.svg assets/vectors/world-flat.svg /tmp/globe-oracle/
python3 scripts/build_geography.py --check   # must print ok before you start
```

- [ ] **Step 2: Create `scripts/geo_projection.py` by moving, not rewriting**

Copy each function body verbatim from `build_geography.py`. The only edits
permitted are: drop the leading underscore from the name, and add `R` as a
trailing parameter where the body referenced the module constant. Do not
"improve" anything — a cleanup here is indistinguishable from a bug.

```python
#!/usr/bin/env python3
"""Sphere-to-screen maths, shared by the static generator and the runtime port.

Extracted from build_geography.py in the LUMI globe work. It lived there as
module-private functions against a module constant R = 150.0; two more callers
need it parameterised, and assets/globe/projection.js is a port of exactly these
functions, verified against them by scripts/check_globe.py.

Nothing here does I/O and nothing here knows about colour. Standard library only.
"""
from __future__ import annotations

import math


def densify(ring, step_deg):
    """Insert intermediate points so a great-circle edge does not project as a
    straight line. Copied unchanged from build_geography.py."""
    out = []
    for i in range(len(ring) - 1):
        (x0, y0), (x1, y1) = ring[i], ring[i + 1]
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step_deg))
        for k in range(n):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    out.append(ring[-1])
    return out
```

Continue with `great_circle`, `cos_c`, `project`, `ortho`, `crossing`,
`visible_runs`, `on_limb`, `limb_walk`, in that order, each taking `R`
explicitly where it previously closed over the module constant.

- [ ] **Step 3: Rewire `build_geography.py` to import them**

Replace the moved definitions with one import and thin module-local wrappers
that supply `R`, so no call site in that file changes:

```python
from geo_projection import (
    cos_c as _cos_c_impl, crossing as _crossing_impl, densify as _densify_impl,
    great_circle as _great_circle, limb_walk as _limb_walk_impl,
    on_limb as _on_limb_impl, ortho as _ortho_impl, project as _project_impl,
    visible_runs as _visible_runs_impl,
)

def _project(lon, lat, lon0, lat0):
    return _project_impl(lon, lat, lon0, lat0, R)
```

Write one wrapper per moved function, each supplying `R` (and `STEP_DEG` for
`_densify`). Keep the original private names so the rest of the file is untouched.

- [ ] **Step 4: Prove the extraction was faithful**

```bash
python3 scripts/build_geography.py            # regenerate
diff -u /tmp/globe-oracle/globe-orthographic.svg assets/vectors/globe-orthographic.svg
diff -u /tmp/globe-oracle/world-flat.svg assets/vectors/world-flat.svg
python3 scripts/build_geography.py --check
python3 scripts/check_repo.py
```

Expected: both diffs empty, `--check` prints ok, `check_repo.py` 14/14.
**A single changed character means the move was not faithful — revert and redo
it, do not regenerate the oracle.**

- [ ] **Step 5: Add the new module to CI and commit**

In `.github/workflows/ci.yml`, add `scripts/geo_projection.py` to the
`py_compile` list.

```bash
git add scripts/geo_projection.py scripts/build_geography.py .github/workflows/ci.yml
git commit -m "extract the projection maths from build_geography, byte-identical output"
```

---

### Task 2: Vendor Natural Earth and record it in NOTICE

**Files:**
- Create: `assets/vectors/upstream/ne_110m_admin_0_countries.geojson`
- Modify: `NOTICE`, `.gitignore`

**Interfaces:**
- Produces: the upstream file at a fixed path, so `build_worldmap.py` never
  reaches the network.

- [ ] **Step 1: Fetch and verify**

```bash
mkdir -p assets/vectors/upstream
curl -sL -o assets/vectors/upstream/ne_110m_admin_0_countries.geojson \
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson
python3 - <<'PY'
import json
d = json.load(open("assets/vectors/upstream/ne_110m_admin_0_countries.geojson"))
assert d["type"] == "FeatureCollection", d["type"]
assert len(d["features"]) == 177, len(d["features"])
missing = [f["properties"]["NAME"] for f in d["features"] if not f["properties"].get("ADM0_A3")]
assert not missing, missing
print("ok 177 features, ADM0_A3 complete")
PY
```

Expected: `ok 177 features, ADM0_A3 complete`.

- [ ] **Step 2: Confirm `.gitignore` does not swallow it**

```bash
git check-ignore -v assets/vectors/upstream/ne_110m_admin_0_countries.geojson; echo "exit=$?"
```

Expected: `exit=1` (not ignored). If it is ignored, add a negation beside the
existing `!assets/vectors/*.svg` exception with a comment saying why, matching
the style of the entries already there.

- [ ] **Step 3: Add the NOTICE entry**

Append to `NOTICE`, in the voice of the existing entries — what was taken, why,
and what the licence requires:

```
Natural Earth — https://www.naturalearthdata.com/
Public domain. No rights reserved; the project asks for credit and does not
require it.

Vendored as assets/vectors/upstream/ne_110m_admin_0_countries.geojson, the 110m
admin-0 country set, unmodified. The LUMI globe needs country-level boundaries
that the hand-written coastlines in scripts/build_geography.py cannot express:
those are a 2-degree stylisation for a cover mark and cannot say "these 27
countries are one region". The file is vendored rather than fetched so that
scripts/build_worldmap.py never touches the network and its --check is
reproducible offline. Regenerate assets/vectors/world-110m.json with
scripts/build_worldmap.py.

At this scale the upstream set has no Singapore, Hong Kong, Bahrain or Malta;
they are merged away by the source, not dropped here. Those places ship as
points in assets/vectors/regions.json instead, which is what a port is anyway.
```

- [ ] **Step 4: Verify the red lines still hold**

```bash
python3 scripts/check_repo.py
```

Expected: 14/14 ok. (`NOTICE` is prose and English; the GeoJSON carries
`NAME_ZH` but `check_english_only` scans `PROSE_GLOBS` only.)

- [ ] **Step 5: Commit**

```bash
git add assets/vectors/upstream NOTICE .gitignore
git commit -m "vendor Natural Earth 110m admin-0, public domain"
```

---

### Task 3: The topology encoder

Per-country simplification breaks shared borders into 1–2 px slivers at deck
scale. Borders must be extracted once, simplified once, and referenced twice.

**Files:**
- Create: `scripts/build_worldmap.py`
- Create (generated): `assets/vectors/world-110m.json`
- Test: a `--check` mode plus assertions run inline

**Interfaces:**
- Produces the on-disk format every later task reads:

```
{ "schema": 1,
  "quantum": 1e4,                     # coordinates are ints, degrees * 1e4
  "arcs": [ [[x,y], [dx,dy], ...] ],  # first point absolute, rest delta-encoded
  "countries": [ {"a": "USA", "n": "United States of America", "z": "美国",
                  "rings": [[3, -7, 12]]} ],   # arc indices; ~i means reversed
  "neighbours": {"USA": ["CAN", "MEX"]} }
```

- [ ] **Step 1: Write the failing check first**

Create `scripts/build_worldmap.py` with only the check path implemented, so it
fails loudly before any encoder exists:

```python
#!/usr/bin/env python3
"""Build the shared-arc world topology from the vendored Natural Earth set.

Per-country simplification is the wrong algorithm for this figure: a border
simplified twice becomes two different lines, and at 0.35 degrees on a 1280px
world map that is a 1-2px sliver exactly where form 2 needs two countries of one
region to merge. So borders are extracted as arcs, each simplified once, and
referenced by both neighbours. Adjacency falls out of the same structure: two
countries are adjacent exactly when they share an arc.

    python3 scripts/build_worldmap.py           # write the topology and fixture
    python3 scripts/build_worldmap.py --check   # verify both are current

Standard library only. Never touches the network; the upstream file is vendored.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "assets" / "vectors" / "upstream" / "ne_110m_admin_0_countries.geojson"
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
TOLERANCE = 0.35   # degrees. A CEILING on simplification error: coarser than
                   # this and the set starts losing countries (0.6 drops
                   # thirteen, including Qatar and Cyprus).
QUANTUM = 10000    # coordinates are stored as degrees * QUANTUM, as integers


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    built = json.dumps(build(), separators=(",", ":"), ensure_ascii=False)
    current = TOPOLOGY.read_text(encoding="utf-8") if TOPOLOGY.exists() else None
    if args.check:
        if current != built:
            print(f"FAIL  {TOPOLOGY.relative_to(ROOT)} is stale or missing; "
                  f"re-run without --check")
            return 1
        print("ok    world topology is current")
        return 0
    TOPOLOGY.write_text(built, encoding="utf-8")
    print(f"wrote {TOPOLOGY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Run it and watch it fail**

```bash
python3 scripts/build_worldmap.py --check
```

Expected: `NameError: name 'build' is not defined`.

- [ ] **Step 3: Implement arc extraction, simplification and adjacency**

Add above `main`. The junction rule is what makes arcs shared: quantise every
coordinate first, then count how many rings each *directed segment*'s endpoints
belong to; a point shared by more than two rings is a junction and ends an arc.

```python
def _quantise(lon, lat):
    return (round(lon * QUANTUM), round(lat * QUANTUM))


def _rdp(pts, eps_q):
    """Douglas-Peucker on quantised integer coordinates. Iterative, because a
    177-country set recurses deep enough to matter."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        den = dx * dx + dy * dy
        worst, wi = -1.0, i
        for k in range(i + 1, j):
            x, y = pts[k]
            if den == 0:
                d = (x - x1) ** 2 + (y - y1) ** 2
            else:
                t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / den))
                d = (x - (x1 + t * dx)) ** 2 + (y - (y1 + t * dy)) ** 2
            if d > worst:
                worst, wi = d, k
        if worst > (eps_q * eps_q):
            keep[wi] = True
            stack.append((i, wi))
            stack.append((wi, j))
    return [p for p, k in zip(pts, keep) if k]


def _cut_into_arcs(rings):
    """rings: list of (owner, [quantised points]). Returns (arcs, ring_refs).

    A point is a junction when the set of rings it belongs to DIFFERS from that
    of the point before or after it. The naive rule — "shared by more than one
    ring" — is wrong and was caught in review: every interior point of a shared
    border is shared by two rings, so it would cut a single border into one arc
    per point. What actually ends an arc is the place where the sharing changes,
    which is exactly where a third country arrives or the coast begins.
    """
    from collections import defaultdict
    owners = defaultdict(set)
    for owner, pts in rings:
        for p in pts:
            owners[p].add(owner)
    arcs, index, refs = [], {}, []
    for owner, pts in rings:
        cuts = [0, len(pts) - 1]
        for i in range(1, len(pts) - 1):
            if owners[pts[i]] != owners[pts[i - 1]] or owners[pts[i]] != owners[pts[i + 1]]:
                cuts.append(i)
        cuts = sorted(set(cuts))
        ref = []
        for a, b in zip(cuts, cuts[1:]):
            seg = pts[a:b + 1]
            key, rkey = tuple(seg), tuple(reversed(seg))
            if key in index:
                ref.append(index[key])
            elif rkey in index:
                ref.append(~index[rkey])
            else:
                index[key] = len(arcs)
                arcs.append(seg)
                ref.append(index[key])
        refs.append((owner, ref))
    return arcs, refs


def _delta(arc):
    out = [list(arc[0])]
    for (x0, y0), (x1, y1) in zip(arc, arc[1:]):
        out.append([x1 - x0, y1 - y0])
    return out


def build():
    raw = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    rings, meta = [], {}
    for feat in raw["features"]:
        p = feat["properties"]
        code = p["ADM0_A3"]
        meta[code] = {"a": code, "n": p["NAME"], "z": p.get("NAME_ZH") or p["NAME"]}
        geom = feat["geometry"]
        polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        for poly in polys:
            for ring in poly:
                q = [_quantise(lon, lat) for lon, lat in ring]
                dedup = [q[0]] + [b for a, b in zip(q, q[1:]) if a != b]
                if len(dedup) >= 4:
                    rings.append((code, dedup))
    arcs, refs = _cut_into_arcs(rings)
    eps_q = TOLERANCE * QUANTUM
    arcs = [_rdp(a, eps_q) if len(a) > 2 else a for a in arcs]
    countries, by_code = {}, {}
    for code, ref in refs:
        countries.setdefault(code, {**meta[code], "rings": []})["rings"].append(ref)
        for i in ref:
            by_code.setdefault(i if i >= 0 else ~i, set()).add(code)
    neighbours = {c: set() for c in countries}
    for owners in by_code.values():
        for a in owners:
            neighbours[a] |= (owners - {a})
    return {"schema": 1, "quantum": QUANTUM,
            "arcs": [_delta(a) for a in arcs],
            "countries": [countries[c] for c in sorted(countries)],
            "neighbours": {c: sorted(v) for c, v in sorted(neighbours.items()) if v}}
```

- [ ] **Step 4: Build it and assert the invariants that matter**

```bash
python3 scripts/build_worldmap.py
python3 - <<'PY'
import json, pathlib
t = json.load(open("assets/vectors/world-110m.json"))
codes = {c["a"] for c in t["countries"]}
assert len(codes) >= 176, len(codes)
for must in ("QAT", "CYP", "USA", "CHN", "MEX", "VNM", "DEU"):
    assert must in codes, must
# adjacency sanity: known land borders present, known non-borders absent
n = t["neighbours"]
assert "MEX" in n["USA"] and "CAN" in n["USA"], n["USA"]
assert "AUS" not in n.get("USA", []), "USA must not border Australia"
# every arc index a country references must exist
for c in t["countries"]:
    for ring in c["rings"]:
        for i in ring:
            assert 0 <= (i if i >= 0 else ~i) < len(t["arcs"]), (c["a"], i)
size = pathlib.Path("assets/vectors/world-110m.json").stat().st_size
print(f"ok {len(codes)} countries, {len(t['arcs'])} arcs, {size//1024} KB")
# The 110 KB ceiling is on the TOTAL added to a deliverable, checked in Task 8.
# Topology alone must leave room for regions.json and the modules, so 80 KB here.
assert size < 80 * 1024, f"{size} leaves no room under the 110 KB total ceiling"
PY
python3 scripts/build_worldmap.py --check
```

Expected: the `ok` line, then `ok world topology is current`.

- [ ] **Step 5: Wire into CI and commit**

Add `scripts/build_worldmap.py` to `py_compile`, and
`python3 scripts/build_worldmap.py --check` to the `--check` sequence in
`.github/workflows/ci.yml`, beside `build_geography.py --check`.

```bash
git add scripts/build_worldmap.py assets/vectors/world-110m.json .github/workflows/ci.yml
git commit -m "shared-arc world topology from the 110m set, adjacency included"
```

---

### Task 4: The region registry and its coverage guard

**Files:**
- Create: `assets/vectors/regions.json`
- Modify: `scripts/check_repo.py`

**Interfaces:**
- Produces `regions.json`:

```
{ "schema": 1,
  "regions": [ {"id": "north-america", "n": "North America", "z": "北美",
                "anchor": [-100, 40], "members": ["USA", "CAN", "MEX"]} ],
  "nodes":   [ {"id": "SGP", "n": "Singapore", "z": "新加坡",
                "lon": 103.8, "lat": 1.35, "region": "southeast-asia"} ] }
```

- [ ] **Step 1: Write the guard before the data**

Add to `scripts/check_repo.py`, beside the other `check_*` functions:

```python
def check_region_coverage():
    """Every country in the topology belongs to exactly one region.

    A country that reaches the renderer with no region is a hole in the map and
    a silent one — it draws in the default fill and reads as deliberate. The
    registry is data, so this is decidable, so it is checked rather than
    remembered.
    """
    topo_path = ROOT / "assets" / "vectors" / "world-110m.json"
    reg_path = ROOT / "assets" / "vectors" / "regions.json"
    if not topo_path.exists() or not reg_path.exists():
        return [f"{rel(reg_path)} or {rel(topo_path)} missing; "
                f"run scripts/build_worldmap.py"]
    topo = json.loads(topo_path.read_text(encoding="utf-8"))
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    countries = {c["a"] for c in topo["countries"]}
    seen, errors = {}, []
    for region in reg["regions"]:
        for code in region["members"]:
            if code in seen:
                errors.append(f"regions.json: {code} is in both "
                              f"{seen[code]} and {region['id']}")
            seen[code] = region["id"]
            if code not in countries:
                errors.append(f"regions.json: {region['id']} names {code}, "
                              f"which is not in the topology")
    for code in sorted(countries - set(seen)):
        errors.append(f"regions.json: {code} belongs to no region")
    return errors
```

Register it by adding `("region coverage", check_region_coverage),` to the
`CHECKS` tuple at `scripts/check_repo.py:1334`, after `("token references", ...)`.

- [ ] **Step 2: Run it and watch it fail**

```bash
python3 scripts/check_repo.py 2>&1 | grep -A2 "region coverage"
```

Expected: `FAIL region coverage` naming the missing `regions.json`.

- [ ] **Step 3: Generate a complete registry, then hand-correct it**

Seed from the upstream `SUBREGION`/`REGION_WB` fields so no country is missed,
then edit the result into trade blocs by hand. Ten default regions:
`north-america`, `latin-america`, `europe`, `middle-east`, `central-asia`,
`south-asia`, `southeast-asia`, `northeast-asia`, `africa`, `oceania`.

```bash
python3 - <<'PY'
import json
raw = json.load(open("assets/vectors/upstream/ne_110m_admin_0_countries.geojson"))
buckets = {}
for f in raw["features"]:
    p = f["properties"]
    buckets.setdefault(p["SUBREGION"], []).append(p["ADM0_A3"])
print(json.dumps({k: sorted(v) for k, v in sorted(buckets.items())}, indent=1))
PY
```

Write `assets/vectors/regions.json` from that listing, mapping every subregion
into one of the ten ids. Add the node layer: Singapore, Hong Kong, Bahrain and
Malta at minimum, since the 110m set has no polygon for any of them.

**These are geography, not engagement facts** — CLAUDE.md 7 and 9. No coverage
counts, no client region names, no figures.

- [ ] **Step 4: Verify**

```bash
python3 scripts/check_repo.py
```

Expected: 15/15 ok, including `ok region coverage`.

- [ ] **Step 5: Commit**

```bash
git add assets/vectors/regions.json scripts/check_repo.py
git commit -m "region registry with a coverage guard: every country in exactly one region"
```

---

### Task 5: The region palette generator

**Files:**
- Create: `scripts/build_region_palette.py`
- Create (generated): `tokens/region-palette.css`

**Interfaces:**
- Produces `oklch_to_srgb(L, C, h) -> (r, g, b) in 0..1`,
  `max_chroma(L, h) -> float`, `ciede2000(lab1, lab2) -> float`,
  `assign_bands(neighbours) -> {region_id: band}`,
  `hue_angles(regions, neighbours) -> {region_id: degrees}`,
  `hue_hex(L, degrees) -> "#rrggbb"`, `stroke_hex(L, degrees) -> "#rrggbb"`

- [ ] **Step 1: Write the failing self-test**

The repository has no unit-test home, so the generator carries its own, in the
idiom `check_fixtures.py` uses: assert, print, exit non-zero.

```python
#!/usr/bin/env python3
"""Generate the region hues and prove they clear their floors.

Hue encodes region identity here, which overrides the default reading of "one
colour one meaning". That is an owner directive and it is safe only because
these hues are declared to carry no data meaning, exactly as light_ramp already
is. Semantic colour is untouched.

OKLCH is the design space; sRGB hex is what ships. It must be hex:
check_design.py's parse_color reads only #rgb, #rrggbb, rgb() and rgba(), so an
oklch() token would make D1 skip every region hue in silence.

    python3 scripts/build_region_palette.py           # write the CSS
    python3 scripts/build_region_palette.py --check   # verify current + floors
    python3 scripts/build_region_palette.py --selftest

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGIONS = ROOT / "assets" / "vectors" / "regions.json"
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
OUT = ROOT / "tokens" / "region-palette.css"

L_LIGHT, L_DARK = 0.70, 0.52   # chosen so the label clears 4.5:1 and nothing else
CHROMA_FRACTION = 0.92         # of the per-hue sRGB gamut maximum
BANDS = 4                      # a REQUIREMENT on the registry, not a preference
BAND_SPREAD = 15.0             # degrees either side of the band centre
DELTA_E_FLOOR = 20.0           # adjacent regions, CIEDE2000
LABEL_CONTRAST_FLOOR = 4.5
STROKE_CONTRAST_FLOOR = 3.0
STROKE_L_OFFSET = 0.20         # darker on light canvas, lighter on dark
INK_LIGHT, INK_DARK = "#212621", "#F0F0FA"
BG_LIGHT, BG_DARK = "#FFFFFF", "#1D1D1F"


def selftest():
    """The floors, asserted against the shipped registry. Exits non-zero on any
    miss, so a palette that stopped clearing its floors cannot ship quietly."""
    errors = []
    reg = json.loads(REGIONS.read_text(encoding="utf-8"))
    neigh = region_neighbours(reg)
    for L, ink, bg, name in ((L_LIGHT, INK_LIGHT, BG_LIGHT, "light"),
                             (L_DARK, INK_DARK, BG_DARK, "dark")):
        hues_hue = hue_angles(reg["regions"], neigh)   # region_id -> hue degrees
        hues = {rid: hue_hex(L, h) for rid, h in hues_hue.items()}
        for rid, hexcol in hues.items():
            c = contrast(hexcol, ink)
            if c < LABEL_CONTRAST_FLOOR:
                errors.append(f"{name}: label on {rid} is {c:.2f}:1, "
                              f"floor {LABEL_CONTRAST_FLOOR}")
            s = contrast(stroke_hex(L, hues_hue[rid]), bg)
            if s < STROKE_CONTRAST_FLOOR:
                errors.append(f"{name}: stroke of {rid} is {s:.2f}:1 on the "
                              f"canvas, floor {STROKE_CONTRAST_FLOOR}")
        for a, bs in neigh.items():
            for b in bs:
                d = ciede2000(lab_of(hues[a]), lab_of(hues[b]))
                if d < DELTA_E_FLOOR:
                    errors.append(f"{name}: {a} and {b} are adjacent and "
                                  f"only ΔE00 {d:.1f} apart, floor "
                                  f"{DELTA_E_FLOOR}")
    for e in sorted(set(errors)):
        print(f"FAIL  {e}")
    if not errors:
        print("ok    region palette clears every floor on both canvases")
    return 1 if errors else 0
```

- [ ] **Step 2: Run it and watch it fail**

```bash
python3 scripts/build_region_palette.py --selftest
```

Expected: `NameError` on `region_neighbours` — the floors are declared before
anything can satisfy them.

- [ ] **Step 3: Implement the colour maths and the band assignment**

Add above `selftest`. `assign_bands` greedily 4-colours the region adjacency
graph in descending-degree order and **fails rather than reaching for a fifth
band**: only B = 4 clears the ΔE floor on both canvases (measured 24.3 light /
21.5 dark at B=4; 20.2 / 17.1 at B=5).

```python
def oklch_to_srgb(L, C, h):
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    in_gamut = all(-0.001 <= v <= 1.001 for v in lin)

    def enc(v):
        v = max(0.0, min(1.0, v))
        return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return tuple(enc(v) for v in lin), in_gamut


def max_chroma(L, h):
    """Largest in-gamut chroma at this lightness and hue, by bisection. A fixed
    chroma puts three to ten hues out of gamut, where clipping silently
    destroys the even spread the construction depends on."""
    lo, hi = 0.0, 0.4
    for _ in range(40):
        mid = (lo + hi) / 2
        if oklch_to_srgb(L, mid, h)[1]:
            lo = mid
        else:
            hi = mid
    return lo


def hue_hex(L, h):
    rgb, _ = oklch_to_srgb(L, max_chroma(L, h) * CHROMA_FRACTION, h)
    return "#" + "".join(f"{round(v * 255):02X}" for v in rgb)


def region_neighbours(reg):
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    of = {c: r["id"] for r in reg["regions"] for c in r["members"]}
    out = {r["id"]: set() for r in reg["regions"]}
    for country, others in topo["neighbours"].items():
        for other in others:
            a, b = of.get(country), of.get(other)
            if a and b and a != b:
                out[a].add(b)
                out[b].add(a)
    return out


def assign_bands(neighbours):
    order = sorted(neighbours, key=lambda r: (-len(neighbours[r]), r))
    band = {}
    for rid in order:
        taken = {band[n] for n in neighbours[rid] if n in band}
        free = [k for k in range(BANDS) if k not in taken]
        if not free:
            raise SystemExit(
                f"FAIL  region adjacency needs more than {BANDS} colours; "
                f"{rid} borders {sorted(neighbours[rid])}, all of which are "
                f"already coloured. Only 4 bands clear the ΔE00 floor on both "
                f"canvases, so merge or re-cut these regions.")
        band[rid] = free[0]
    return band


def hue_angles(regions, neighbours):
    band = assign_bands(neighbours)
    per_band = {}
    for rid in sorted(band):
        per_band.setdefault(band[rid], []).append(rid)
    out = {}
    for k, members in per_band.items():
        n = len(members)
        for i, rid in enumerate(members):
            offset = 0.0 if n == 1 else -BAND_SPREAD + 2 * BAND_SPREAD * i / (n - 1)
            out[rid] = (90.0 * k + offset) % 360
    return out
```

Split `palette` into `hue_angles(regions, neighbours) -> {region_id: degrees}`
and `hue_hex(L, degrees)`, so the hue is available on its own. The self-test
needs the angle, not the hex, and a `stroke_of` that recomputed the palette
internally would be a second source of truth for the assignment. Then add
`stroke_hex(L, hue)` — the same hue at `L ∓ STROKE_L_OFFSET` — plus `lab_of`,
`ciede2000` and `contrast`. Copy `contrast` and the sRGB→Lab helper from `check_design.py:88-102`
rather than writing a second version with a different rounding.

- [ ] **Step 4: Run the self-test and the emit**

```bash
python3 scripts/build_region_palette.py --selftest
python3 scripts/build_region_palette.py
head -20 tokens/region-palette.css
python3 scripts/build_region_palette.py --check
grep -c "oklch(" tokens/region-palette.css
```

Expected: `ok region palette clears every floor on both canvases`; the CSS shows
`--rg-<id>`, `--rg-<id>-stroke`, `--rg-<id>-wash` per region under `:root` and a
`body.dark` block; `--check` prints ok; the `oklch(` count is **0**.

If the self-test reports a ΔE miss, the registry is at fault, not the generator —
merge the named regions in `regions.json` and re-run.

- [ ] **Step 5: Wire into CI and commit**

Add to `py_compile` and to the `--check` sequence.

```bash
git add scripts/build_region_palette.py tokens/region-palette.css .github/workflows/ci.yml
git commit -m "region hues generated in OKLCH, shipped as hex, floors self-tested"
```

---

### Task 6: The golden fixture and the Python maths check

**Files:**
- Create: `scripts/check_globe.py`
- Create (generated): `fixtures/globe-golden.json`
- Modify: `scripts/build_worldmap.py` (emit the fixture alongside the topology)

**Interfaces:**
- Consumes: `geo_projection` from Task 1
- Produces: `fixtures/globe-golden.json` as
  `{"schema": 1, "views": [{"lon0":…, "lat0":…, "t":…, "R":…}],
    "samples": [[view_index, lon, lat, x, y, visible], …]}`
- Produces: `scripts/check_globe.py --python-only` (CI-safe, no browser)

- [ ] **Step 1: Extend `geo_projection.py` with the unroll**

The static generator only ever needed `t = 0`. Add the flattening, exactly as
the spec's §4 states it, including the antimeridian cut:

```python
def unrolled(lon, lat, lon0, lat0, t, R, cx, cy):
    """Position on the sphere-to-plane interpolation, then orthographic.

    t=0 is the globe, t=1 an equirectangular map, and every value between is a
    real geometry rather than a crossfade — crossfading two projections has no
    coherent state at t=0.5 and breaks limb clipping halfway through.

    Returns (x, y, visible). `visible` interpolates the cull with t so no
    polygon pops as the sphere opens.
    """
    lam = math.radians(lon - lon0)
    phi, phi0 = math.radians(lat), math.radians(lat0)
    xs = math.cos(phi) * math.sin(lam)
    ys = math.cos(phi0) * math.sin(phi) - math.sin(phi0) * math.cos(phi) * math.cos(lam)
    zs = math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(lam)
    lon_rel = ((lon - lon0 + 180.0) % 360.0) - 180.0
    xp, yp = lon_rel / 180.0, (lat / 90.0) * 0.5
    x = xs + (xp - xs) * t
    y = ys + (yp - ys) * t
    return (cx + R * x, cy - R * y, zs >= -t)
```

`cx` and `cy` are explicit parameters, not `R` twice. The JS port takes them
separately and the golden fixture is compared across both, so a hidden
`cx = cy = R` here guarantees a mismatch the check would report as a port bug.

Add `invert` in the same commit — `check_globe.py` asserts
`invert(project(p)) == p` on the Python side too, and there is nothing to assert
against without it:

```python
def invert(x, y, lon0, lat0, t, R, cx, cy):
    """Screen back to (lon, lat), or None outside the figure.

    Analytic at the two ends; two Newton steps between them, which is enough
    because the interpolation is monotone in both coordinates and the
    round-trip assertion in check_globe.py is what proves the tolerance.
    """
```

- [ ] **Step 2: Emit the fixture from `build_worldmap.py`**

In `build_worldmap.py`, add `GOLDEN = ROOT / "fixtures" / "globe-golden.json"`
and a `build_golden()` that samples a fixed grid — every 15° of longitude,
every 15° of latitude, across four views — and have `main` write and `--check`
both files. A fixed grid, never a random one: the fixture must be reproducible.

```python
# (lon0, lat0, t, R, cx, cy). cx and cy are deliberately NOT equal to R in two
# of the views: the JS port takes them as separate parameters, and a fixture
# that only ever exercises cx == cy == R cannot catch a port that dropped them.
GOLDEN_VIEWS = [(0.0, 0.0, 0.0, 150.0, 150.0, 150.0),
                (-170.0, 20.0, 0.0, 150.0, 200.0, 180.0),
                (45.0, -10.0, 0.5, 150.0, 150.0, 150.0),
                (0.0, 0.0, 1.0, 120.0, 300.0, 90.0)]


def build_golden():
    import geo_projection as gp
    samples = []
    for vi, (lon0, lat0, t, R, cx, cy) in enumerate(GOLDEN_VIEWS):
        for lon in range(-180, 181, 15):
            for lat in range(-90, 91, 15):
                x, y, vis = gp.unrolled(lon, lat, lon0, lat0, t, R, cx, cy)
                samples.append([vi, lon, lat, round(x, 9), round(y, 9), bool(vis)])
    return {"schema": 1,
            "views": [{"lon0": a, "lat0": b, "t": c, "R": d, "cx": e, "cy": f}
                      for a, b, c, d, e, f in GOLDEN_VIEWS],
            "samples": samples}
```

- [ ] **Step 3: Write `check_globe.py` with a CI-safe half**

```python
#!/usr/bin/env python3
"""Verify the globe maths, and that the JS port agrees with it.

assets/globe/projection.js is a hand port of scripts/geo_projection.py. Nothing
in this repository can compile JavaScript — there is no package.json and CI runs
py_compile and bash -n — so the port is held to the Python authority by a golden
grid instead.

    python3 scripts/check_globe.py --python-only   # properties only; runs in CI
    python3 scripts/check_globe.py                 # also the JS port; needs Playwright

Like check_prose.py, check_design.py and inspect_layout.py, the full run cannot
run in CI. --python-only can, and does.
"""
```

The `--python-only` half asserts properties the golden values cannot:
`invert(project(p)) == p` to 1e-9 for every visible sample; `visible` is
`True` for every sample at `t = 1`; `unrolled(lon, 90, …)` is a single point
per view (the pole does not smear); and a point one degree behind the limb at
`t = 0` is invisible while one degree in front is visible.

- [ ] **Step 4: Run both halves**

```bash
python3 scripts/build_worldmap.py
python3 scripts/check_globe.py --python-only
python3 scripts/build_worldmap.py --check
```

Expected: `ok` from the check, `ok` from `--check`. The Playwright half will
report the missing `assets/globe/projection.js` — that is correct, it arrives in
Task 7.

- [ ] **Step 5: Wire into CI and commit**

Add `scripts/check_globe.py` to `py_compile` and
`python3 scripts/check_globe.py --python-only` to the CI step list.

```bash
git add scripts/geo_projection.py scripts/build_worldmap.py scripts/check_globe.py \
        fixtures/globe-golden.json .github/workflows/ci.yml
git commit -m "the unroll, a golden projection grid, and a CI-safe maths check"
```

---

### Task 7: `projection.js` and the port agreement check

**Files:**
- Create: `assets/globe/projection.js`
- Modify: `scripts/check_globe.py` (the Playwright half)

**Interfaces:**
- Produces: `project(lon, lat, view) -> {x, y, visible}`,
  `invert(x, y, view) -> {lon, lat} | null`,
  `splitAtSeam(ring, view) -> Array<Array<[lon, lat]>>`
  where `view = {lon0, lat0, t, R, cx, cy}`

- [ ] **Step 1: Write the Playwright half first, and watch it fail**

In `check_globe.py`, import Playwright inside the function so `--python-only`
never touches it. Load `assets/globe/projection.js` as a module in
`about:blank`, evaluate every golden sample, and assert agreement to 1e-9.

```bash
python3 scripts/check_globe.py
```

Expected: FAIL naming the missing `assets/globe/projection.js`.

- [ ] **Step 2: Port the module**

Port line by line from `geo_projection.py`. Same names, same order, same
formulae. Include `splitAtSeam`: because longitude is relative to `lon0` the
seam moves as the globe turns, and any ring crossing it draws a horizontal
streak across the whole map as `t` rises.

```javascript
// Port of scripts/geo_projection.py. The Python is the authority; this file is
// checked against it over a golden grid by scripts/check_globe.py. Change one
// and you must change the other in the same commit.
const D2R = Math.PI / 180, R2D = 180 / Math.PI;

export function project(lon, lat, view) {
  const { lon0, lat0, t, R, cx, cy } = view;
  const lam = (lon - lon0) * D2R, phi = lat * D2R, phi0 = lat0 * D2R;
  const cphi = Math.cos(phi), sphi = Math.sin(phi);
  const xs = cphi * Math.sin(lam);
  const ys = Math.cos(phi0) * sphi - Math.sin(phi0) * cphi * Math.cos(lam);
  const zs = Math.sin(phi0) * sphi + Math.cos(phi0) * cphi * Math.cos(lam);
  const lonRel = ((lon - lon0 + 180) % 360 + 360) % 360 - 180;
  const xp = lonRel / 180, yp = (lat / 90) * 0.5;
  const x = xs + (xp - xs) * t, y = ys + (yp - ys) * t;
  return { x: cx + R * x, y: cy - R * y, visible: zs >= -t };
}
```

Then `invert` (analytic for `t = 0`, linear for `t = 1`, Newton over two
iterations between — the check's round-trip assertion is what proves it), and
`splitAtSeam`.

- [ ] **Step 3: Run the agreement check**

```bash
python3 scripts/check_globe.py
```

Expected: `ok JS port agrees with the Python authority on N samples`.
If a sample disagrees, the port is wrong — **do not adjust the fixture.**

- [ ] **Step 4: Confirm no colour leaked in**

```bash
grep -n '#[0-9A-Fa-f]\{6\}' assets/globe/*.js; echo "exit=$?"
```

Expected: `exit=1`, no matches.

- [ ] **Step 5: Commit**

```bash
git add assets/globe/projection.js scripts/check_globe.py
git commit -m "projection.js, held to the Python authority by the golden grid"
```

---

### Task 8: `worlddata.js` — the topology decoder

**Files:**
- Create: `assets/globe/worlddata.js`

**Interfaces:**
- Produces: `decode(topology) -> {arcs, countries, regionOf, bboxOf, neighbours}`
  where `arcs` is `Array<Array<[lon, lat]>>` in degrees, `regionOf` is
  `Map<ADM0_A3, region_id>`, `bboxOf` is `Map<region_id, [w, s, e, n]>`
- Produces: `ringsOf(country, arcs) -> Array<Array<[lon, lat]>>`, resolving
  negative arc indices as reversed

- [ ] **Step 1: Write the failing browser assertion**

Add a case to the Playwright half of `check_globe.py`: decode the shipped
topology and assert the decoded coordinate count equals the sum of arc lengths
in the JSON, and that `ringsOf` returns closed rings (first point equals last)
for `USA`, `CHN` and `DEU`.

```bash
python3 scripts/check_globe.py
```

Expected: FAIL naming the missing `assets/globe/worlddata.js`.

- [ ] **Step 2: Implement the decoder**

Un-delta and de-quantise; resolve `~i` as a reversed arc; drop the duplicated
junction point when concatenating arcs into a ring.

- [ ] **Step 3: Run the check**

```bash
python3 scripts/check_globe.py
```

Expected: ok, including the new decoder assertions.

- [ ] **Step 4: Confirm the weight ceiling still holds**

```bash
python3 - <<'PY'
import pathlib
total = sum(p.stat().st_size for p in
            [pathlib.Path("assets/vectors/world-110m.json"),
             pathlib.Path("assets/vectors/regions.json")]
            + sorted(pathlib.Path("assets/globe").glob("*.js")))
print(f"{total//1024} KB of {110} KB ceiling")
assert total < 110 * 1024, total
PY
```

- [ ] **Step 5: Commit**

```bash
git add assets/globe/worlddata.js scripts/check_globe.py
git commit -m "worlddata.js: topology decoder, region index, bounding boxes"
```

---

### Task 9: `globe_svg.py` — the static frame

**Files:**
- Create: `scripts/globe_svg.py`

**Interfaces:**
- Produces: `render(view, data, palette, form) -> str` (an `<svg>` element), and
  a CLI that writes one to stdout

- [ ] **Step 1: Write the failing assertion**

The gate that matters here is `inspect_layout.py --deliverable`, two of whose
findings can fire on this figure: **a drawing clipped by its own viewBox** — the
globe's limb sits exactly on the edge, which is how that defect was found in the
first place — and **a lost datum**. So the viewBox is computed from the projected
extent at the requested `t`, never a fixed square.

Add to `check_globe.py --python-only`: render at `t ∈ {0, 0.5, 1}` and assert
every projected coordinate falls inside the emitted `viewBox` with at least
`stroke-width / 2` of margin.

- [ ] **Step 2: Run it and watch it fail**

```bash
python3 scripts/check_globe.py --python-only
```

Expected: FAIL on the missing `scripts/globe_svg.py`.

- [ ] **Step 3: Implement the renderer**

Every element carries a class and no literal colour, exactly as
`build_geography.py`'s docstring requires. Layer order: plate, graticule, region
fills, boundaries, field marks, nodes, labels. Each region is one `<path>` with
`class="rg rg-<id> is-<state>"`, `role="img"` and an `aria-label`.

- [ ] **Step 4: Verify against the real gate**

```bash
python3 scripts/globe_svg.py --t 0 > /tmp/globe-t0.svg
python3 scripts/globe_svg.py --t 1 > /tmp/globe-t1.svg
python3 scripts/check_globe.py --python-only
```

Expected: ok, with the viewBox assertion passing at all three `t` values.

- [ ] **Step 5: Commit**

```bash
git add scripts/globe_svg.py scripts/check_globe.py .github/workflows/ci.yml
git commit -m "globe_svg: static frames whose viewBox follows the projected extent"
```

---

### Task 10: `render-svg.js`, `pick.js`, `controls.js`, `globe.js`

Four modules in one task because none is independently demonstrable: a renderer
with no controls cannot be seen to work, and controls with no pick have nothing
to report.

**Files:**
- Create: `assets/globe/render-svg.js`, `pick.js`, `controls.js`, `globe.js`

**Interfaces:**
- `createSvgRenderer(svgEl, data, view) -> {draw(view, state), destroy()}`
- `pickRegion(x, y, view, data) -> region_id | null`
- `pickMark(x, y, view, marks) -> index | null` — 12 px radius floor
- `attachControls(el, view, {onChange}) -> {destroy()}`
- `createGlobe(container, {data, hostData, form, autorotate}) -> {setForm, setT, destroy}`
  emitting `regionenter`, `regionleave`, `regionselect`, `formchange`

- [ ] **Step 1: Build the manual harness first**

Create `/tmp/globe-harness.html` inlining `tokens/region-palette.css`, the
static SVG from Task 9, and the modules. This is the only way to see the thing;
there is no dev server in this repo.

- [ ] **Step 2: Implement, in dependency order**

`render-svg.js` mutates `d` on the existing paths — it never creates or destroys
elements, which is what keeps the static frame authoritative and the screen
reader tree stable. `pick.js` uses `invert` plus a bbox prefilter, then
spherical point-in-polygon. `controls.js` is an arcball: invert both the grab
point and the current point to sphere vectors and apply the rotation between
them, so the point under the cursor stays under it; mapping pixels to longitude
stops tracking at high latitude. Inertia decays exponentially to rest **within
0.9 s — a ceiling**. `globe.js` owns the state machine, reads tokens through
`getComputedStyle`, and implements every row of the spec's failure table.

- [ ] **Step 3: Verify behaviour by hand, against the list**

Open the harness and check: the pointer stays glued to its point while dragging
near the pole; hovering a region highlights it and no other; Tab reaches every
region and Enter selects; `+`/`-` zoom; with
`prefers-reduced-motion: reduce` forced on there is no auto-rotation, no inertia,
and the form switch cuts; disabling JavaScript leaves the static frame intact;
an unknown region id in the host data produces exactly one console warning.

- [ ] **Step 4: Measure the two performance floors**

```bash
python3 - <<'PY'
print("Record in the commit message:")
print("  SVG back end fps at 1280x720 (floor 30)")
print("  Canvas back end ms/frame (ceiling 4) — Task 11")
PY
```

Measure with `performance.now()` over 300 frames in the harness. If the SVG back
end is under 30 fps, the watchdog must pin the static frame — verify it does
rather than raising the budget.

- [ ] **Step 5: Commit**

```bash
git add assets/globe/render-svg.js assets/globe/pick.js \
        assets/globe/controls.js assets/globe/globe.js
git commit -m "the SVG back end, arcball controls, hit testing and the component"
```

---

### Task 11: `render-canvas.js`

**Files:**
- Create: `assets/globe/render-canvas.js`

**Interfaces:**
- `createCanvasRenderer(canvasEl, data, view) -> {draw(view, state), destroy()}` —
  the same shape as `createSvgRenderer`, so `globe.js` selects between them
  without branching anywhere else

- [ ] **Step 1: Add the selection test to the harness**

A second harness page that passes `backend: "canvas"`, and one that forces
`HTMLCanvasElement.prototype.getContext` to return `null` — the fallback row of
the failure table must put the SVG back end on screen.

- [ ] **Step 2: Implement**

DPR-aware. Geometry decodes once; projected results write into reused
`Float32Array`s so no per-frame allocation reaches the collector. rAF pauses on
`IntersectionObserver` exit and on `visibilitychange`.

- [ ] **Step 3: Measure against the ceiling**

300 frames at 1280×720, DPR 2. Expected: **≤ 4 ms per frame**.

- [ ] **Step 4: Confirm the fallback**

With `getContext` stubbed to `null`, the SVG back end renders and no error
reaches the console beyond the single explanatory warning.

- [ ] **Step 5: Commit**

```bash
git add assets/globe/render-canvas.js
git commit -m "canvas back end behind the same interface, with the SVG fallback"
```

---

### Task 12: The label-anchor metric and its fixture defect

A metric with no planted defect is decorative. `fixtures/expected.json` records
that ten of thirteen design metrics once had no assertion on either fixture, so
"a checker rewritten to return ok unconditionally would have passed".

**Files:**
- Modify: `scripts/check_design.py`, `scripts/build_fixtures.py`,
  `fixtures/expected.json`
- Regenerate: `fixtures/deck-pass.en.html`, `fixtures/deck-broken.en.html`

**Interfaces:**
- Produces: `d18_region_labels(raw) -> {"regions": n, "unlabelled": [ids]} | None`

- [ ] **Step 1: Assert the verdict before the metric exists**

Add `"D18_region_labels": "ok"` to the `deck-pass` design verdicts in
`fixtures/expected.json`, and `"D18_region_labels": "FAIL"` plus a `contains`
entry naming the unlabelled region to `deck-broken`.

- [ ] **Step 2: Run it and watch it fail**

```bash
python3 scripts/check_fixtures.py
```

Expected: FAIL — `D18_region_labels` is asserted and not emitted.

- [ ] **Step 3: Implement the metric and plant the defect**

```python
def d18_region_labels(raw):
    """Every coloured region carries a label or a legend entry.

    Hue encodes region identity in the globe figure, by owner directive. Measured
    at the theoretical maximum hue separation of 90 degrees, deuteranopia
    collapses adjacent regions to ΔE00 9.6 and protanopia to 8.5 — and real maps
    run at 60. Hue separates neighbours at a glance; text is what carries
    identity, so this checks for the text and never counts hues.
    """
    ids = re.findall(r'class="[^"]*\brg-([\w-]+)', raw)
    if not ids:
        return None
    labelled = set(re.findall(r'data-region-label="([\w-]+)"', raw))
    labelled |= set(re.findall(r'<li[^>]*data-legend="([\w-]+)"', raw))
    unlabelled = sorted({i for i in ids} - labelled)
    return {"regions": len(set(ids)), "unlabelled": unlabelled}
```

Register it in two places, both of which the fixture assertion depends on: add
`"D18_region_labels": d18_region_labels(raw),` to the dict returned by
`measure()` (`scripts/check_design.py:724`), and a row to `grade()`:

```python
    d18 = r["D18_region_labels"]
    rows.append(("D18_region_labels",
                 len(d18["unlabelled"]) if d18 else None, "=0",
                 not (d18 and d18["unlabelled"]), d18 is None))
    if d18:
        rows.append(("D18_detail", d18["unlabelled"], "reported", True, False))
```

The `_detail` row is what lets `deck-broken` assert *which* region was left
unlabelled, the way `D16_detail` and `D10_detail` already do — a metric that only
reports a count cannot tell a real catch from an off-by-one. In `build_fixtures.py`, add a small region figure to
both decks — every region labelled in `deck-pass`, one region deliberately
unlabelled in `deck-broken`.

- [ ] **Step 4: Verify**

```bash
python3 scripts/build_fixtures.py
python3 scripts/check_fixtures.py
python3 scripts/check_design.py fixtures/deck-broken.en.html --json | grep -A3 D18
```

Expected: `check_fixtures.py` passes; the broken deck reports `D18_region_labels`
FAIL naming exactly the region left unlabelled.

- [ ] **Step 5: Commit**

```bash
git add scripts/check_design.py scripts/build_fixtures.py fixtures/
git commit -m "D18: every coloured region carries a label, with a planted defect"
```

---

### Task 13: The rules, the tokens and the version bump

The single rule revision. Everything before this was mechanism; this is the part
`references/` publishes.

**Files:**
- Modify: `references/design-rules.md`, `tokens/lumi-theme.css`,
  `tokens/design-tokens.json`, `tokens/lumi-layouts.css`, `SKILL.md`,
  `README.md`, `CLAUDE.md`, `CHANGELOG.md`

- [ ] **Step 1: Write the rules into `references/design-rules.md`**

Four additions, each carrying its number's direction:

1. Region colouring — hue is identity and carries no data meaning, the way
   `light_ramp` already does. One colour one meaning still governs data.
2. **Every coloured region carries a label or a legend entry**, with the
   deuteranopia measurement as the reason.
3. **Every region carries a boundary stroke clearing 3 : 1 against the canvas**,
   the region's own hue at `L ∓ 0.20`. Measured worst case 5.64 : 1 on white,
   5.96 : 1 on `#1D1D1F`.
4. **Mark versus map:** the 2° coastlines in `build_geography.py` are a mark and
   the 110m set is a map. **A document may use either and must never place both
   in one view.** Two geographies now live here and they disagree about where a
   coastline is; re-deriving the coarse set would change the shipped cover mark
   byte-for-byte, so it is deferred to its own retrospective.

- [ ] **Step 2: Add the region spec to the tokens, in both files together**

`design-tokens.json` gets a `region` block recording the generator's inputs —
`L_light 0.70`, `L_dark 0.52`, `chroma_fraction 0.92`, `bands 4`,
`band_spread 15`, `delta_e_floor 20`, `stroke_l_offset 0.20` — plus a note in
the voice of the existing `palette.note`, naming the owner directive, the
rejected 8-hue ceiling, and the rejected all-pairs ΔE floor.

`lumi-theme.css` imports or inlines `tokens/region-palette.css`. **If any new
key lands in `palette.*`, it must also go in `PALETTE_KEY_TO_VAR` in
`check_repo.py`** — that map is what forces the two files to be edited together.

- [ ] **Step 3: Bump all five stamps and write the CHANGELOG entry**

```bash
python3 - <<'PY'
import re, pathlib
cl = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
cur = re.search(r"^##\s+(\d+\.\d+\.\d+)", cl, re.M).group(1)
major, minor, patch = cur.split(".")
print(f"current {cur} -> next {major}.{minor}.{int(patch) + 1}")
PY
```

Set that number in `SKILL.md` frontmatter, the newest `CHANGELOG.md` heading,
and the header of all three `tokens/` files. The CHANGELOG entry records the
case as CLAUDE.md 2 requires — an owner directive, the 8-hue ceiling proposed
and rejected, the all-pairs ΔE floor that was unsatisfiable at every N, and the
D17 node-count spike a globe page will show, so a reviewer does not read it as a
regression. **No client, no engagement, no figures** (red line 9).

- [ ] **Step 4: Re-flow the entry points and run everything**

Drift is this repo's main hazard and the checks catch only its mechanical half.
Re-read `SKILL.md`, `AGENTS.md`, `prompts/lumi-style-core.md` and `README.md`
against the changed rules by hand, then:

```bash
python3 scripts/build_entrypoints.py --check || python3 scripts/build_entrypoints.py
python3 scripts/build_geography.py --check
python3 scripts/build_worldmap.py --check
python3 scripts/build_region_palette.py --check
python3 scripts/build_fixtures.py --check
python3 scripts/check_fixtures.py
python3 scripts/check_globe.py --python-only
python3 scripts/check_repo.py
```

Expected: every line ok, `check_repo.py` all checks passing.

- [ ] **Step 5: Commit**

```bash
git add -A
V="$(python3 -c "import re,pathlib;print(re.search(r'^##\s+(\d+\.\d+\.\d+)',pathlib.Path('CHANGELOG.md').read_text(),re.M).group(1))")"
git commit -m "$V — the LUMI globe: region hue by owner directive, labels carry identity, mark and map kept apart"
```

---

### Task 14: Look at it

Metrics passing is not a verified figure (CLAUDE.md 8). `check_design.py`
reported all-clear on a figure whose band was clipped by its own viewBox.

**Files:** none. This task produces screenshots and a written verdict.

- [ ] **Step 1: Build a demonstration deliverable**

One deck with a globe page in form 1 and a region page in form 2, using
`globe_svg.py` output and the runtime, in `~/Documents/LUMI-Style/`
(`scripts/output_dir.py --path`). It is a deliverable, so it does **not** go in
this repository.

- [ ] **Step 2: Run the gates that measure a document**

```bash
DECK="$(python3 scripts/output_dir.py --path)/globe-demo.en.html"
python3 scripts/check_design.py "$DECK"
python3 scripts/check_prose.py "$DECK" --genre internal
python3 scripts/inspect_layout.py "$DECK" --deliverable
python3 scripts/inspect_layout.py "$DECK" --geometry a4 --deliverable
python3 scripts/inspect_layout.py "$DECK" --dark
```

Expected: no gating finding. `--deliverable` exits non-zero on a drawing clipped
by its own viewBox and on a lost datum; both can fire on this figure.

- [ ] **Step 3: Look at every state**

Both forms × `t ∈ {0, 0.5, 1}` × light and dark × 1280×720 and 794×1123. Twelve
screens on the contact sheet. Look specifically for what no metric sees:
polygons popping at the cull threshold, label collisions near the limb, the
antimeridian seam at `t = 1`, and whether the unroll reads as one motion.

- [ ] **Step 4: Write the verdict down**

Add the observations to the release notes for the version bumped in Task 13.
A defect found here is a retrospective, and a retrospective is what CLAUDE.md 2
requires before any further rule change.

- [ ] **Step 5: Report**

Report to the owner: the twelve screens, the gate output, the measured frame
rates from Tasks 10 and 11, and the total added weight against the 110 KB
ceiling.

---

## Self-review

**Spec coverage.** §1 → Task 1. §2 three targets → Tasks 9, 10, 11. §3 modules →
Tasks 1, 3, 5, 6, 7, 8, 9, 10, 11. §4 unroll and seam → Task 6 step 1, Task 7
step 2. §5 colour, all floors → Task 5, Task 13 step 2. §6 geography, topology,
adjacency, registry, mark-versus-map → Tasks 2, 3, 4, 13. §7 interaction, data
contract, failure table, performance, a11y → Tasks 10, 11. §8 testing → Tasks 6,
7, 12. §9 integration and commit order → Tasks 13, 14. §10 out of scope is
absent from the plan by design.

**Known gaps, stated rather than hidden.**

- The spec's `regions.json` node layer is created in Task 4 but nothing renders
  nodes until Task 9, and no task measures them. They are drawn and looked at in
  Task 14, which is weaker than a check. Accepted: a point marker has no
  geometry to get wrong that a screenshot will not show.
- Task 10 bundles four modules. It is the largest task here and the only one
  whose steps are not all independently testable, because the pieces are not
  independently demonstrable. If it proves too big in execution, split at
  `pick.js`.
- The `d18` metric checks that a label exists, not that it is legible or
  correctly placed. Placement is a Task 14 judgement.
