// Decode the shared-arc world topology and index it for the renderers.
//
// The file this reads is written by scripts/build_worldmap.py, and
// scripts/check_globe.py compares what comes out of here against what went in:
// point counts, ring closure, and Germany landing where Germany is.
//
// The format, so this file can be read without the generator open:
//
//   quantum     coordinates are integers, degrees * quantum
//   arcs        flat [x, y, dx, dy, ...] — first point absolute, rest deltas.
//               Flat, not pairs: a nested pair costs three characters of
//               punctuation per point, and there are five thousand of them.
//   countries   [{a: ADM0_A3, n, z, rings: [[arcIndex, ...]]}]
//               A NEGATIVE index means arc ~i traversed backwards. Every border
//               is stored once and referenced by both neighbours, which is what
//               keeps two countries of one region from developing a sliver
//               between them.
//   neighbours  {ADM0_A3: [ADM0_A3, ...]} — derived from shared arcs, never
//               written by hand.
//
// Nothing here touches the DOM, reads a token, or knows a colour.

/** Un-delta and de-quantise one flat arc -> [[lon, lat], ...]. */
function decodeArc(flat, quantum) {
  const n = flat.length / 2;
  const out = new Array(n);
  let x = flat[0];
  let y = flat[1];
  out[0] = [x / quantum, y / quantum];
  for (let i = 1; i < n; i += 1) {
    x += flat[i * 2];
    y += flat[i * 2 + 1];
    out[i] = [x / quantum, y / quantum];
  }
  return out;
}

/**
 * -> {arcs, countries, neighbours, regionOf, regionMembers, nodes, regions}
 *
 * `regions` is the registry's own order, which is the order a legend prints in.
 */
export function decode(topology, registry) {
  const quantum = topology.quantum;
  const arcs = topology.arcs.map((a) => decodeArc(a, quantum));

  const countries = new Map();
  for (const c of topology.countries) countries.set(c.a, c);

  const regionOf = new Map();
  const regionMembers = new Map();
  for (const r of registry.regions) {
    regionMembers.set(r.id, r.members);
    for (const code of r.members) regionOf.set(code, r.id);
  }

  // The per-region bounding-box index lived here until 0.1.396. It fed the
  // hit-test prefilter, and that prefilter died with pickRegion when the map
  // took its hit testing to the browser's own pointer events — so this walked
  // every arc of every member on EVERY boot of every deliverable to build a
  // Map nothing read.

  return {
    quantum,
    arcs,
    countries,
    neighbours: topology.neighbours || {},
    regions: registry.regions,
    regionOf,
    regionMembers,
    nodes: registry.nodes || [],
  };
}

/**
 * Resolve a country's arc references into closed rings of [lon, lat].
 *
 * A negative reference is that arc backwards. Consecutive arcs share their
 * junction point, so the first point of each arc after the first is dropped —
 * keeping it would put a duplicate vertex at every junction, which is invisible
 * on screen and doubles the work of every projection pass.
 */
/**
 * The decoded polyline for one arc index, sign dropped.
 *
 * A ring references arcs with a sign for direction; a LINE has no winding, so
 * the three land-line layers (coast, bloc edge, border) index arcs directly.
 * Which arc belongs to which layer is decided once, in scripts/geo_frame.py,
 * and travels in the markup — this function only decodes.
 */
export function arcPoints(index, data) {
  return data.arcs[index >= 0 ? index : ~index];
}

export function ringsOf(code, data) {
  const country = data.countries.get(code);
  if (!country) return [];
  const out = [];
  for (const refs of country.rings) {
    const ring = [];
    for (const idx of refs) {
      const arc = data.arcs[idx >= 0 ? idx : ~idx];
      const seq = idx >= 0 ? arc : arc.slice().reverse();
      for (let i = ring.length ? 1 : 0; i < seq.length; i += 1) ring.push(seq[i]);
    }
    if (ring.length > 3) {
      const [fx, fy] = ring[0];
      const [lx, ly] = ring[ring.length - 1];
      if (Math.abs(fx - lx) > 1e-12 || Math.abs(fy - ly) > 1e-12) ring.push([fx, fy]);
      out.push(ring);
    }
  }
  return out;
}

/** Every ring of every country in a region, in registry member order. */
// ringsOfRegion was exported here until 0.1.396. Its only caller was the
// globe's region layer, and globe_svg.py stopped emitting regions when the
// split gave them their own component; the map runtime touches no geometry.

