// Sphere-to-screen maths for the LUMI globe.
//
// A hand port of scripts/lib/geo_projection.py. THE PYTHON IS THE AUTHORITY: this
// file is checked against it over a golden grid by scripts/check/check_globe.py, to
// 1e-9 on every sample. Change one and you must change the other in the same
// commit, or that check fails and says so.
//
// Nothing here touches the DOM, reads a token, or knows a colour.
//
// One porting hazard worth naming, because it is silent: JavaScript's % takes
// the sign of the dividend and Python's does not. Every wrap below is written
// ((v % 360) + 360) % 360 for that reason.

const D2R = Math.PI / 180;
const R2D = 180 / Math.PI;

function wrap180(deg) {
  return (((deg + 180) % 360) + 360) % 360 - 180;
}

/**
 * Position on the sphere-to-plane interpolation, then orthographic.
 *
 * t=0 is the globe and t=1 an equirectangular map; every value between is a
 * real geometry rather than a crossfade, which has no coherent state at t=0.5.
 * The plane spans 2R by R, so the flat map is exactly as wide as the globe.
 *
 * view: {lon0, lat0, t, R, cx, cy}
 * -> {x, y, visible}
 */
export function project(lon, lat, view) {
  const { lon0, lat0, t, R, cx, cy } = view;
  const lam = (lon - lon0) * D2R;
  const phi = lat * D2R;
  const phi0 = lat0 * D2R;
  const cphi = Math.cos(phi);
  const sphi = Math.sin(phi);
  const clam = Math.cos(lam);
  const xs = cphi * Math.sin(lam);
  const ys = Math.cos(phi0) * sphi - Math.sin(phi0) * cphi * clam;
  const zs = Math.sin(phi0) * sphi + Math.cos(phi0) * cphi * clam;
  const lonRel = wrap180(lon - lon0);
  const xp = lonRel / 180;
  const yp = (lat / 90) * 0.5;
  const x = xs + (xp - xs) * t;
  const y = ys + (yp - ys) * t;
  return { x: cx + R * x, y: cy - R * y, visible: zs >= -t };
}

/** Cosine of the angular distance from the projection centre. Depth: larger is
 *  nearer the viewer, and non-negative exactly on the near hemisphere. */
export function cosC(lon, lat, view) {
  const lam = (lon - view.lon0) * D2R;
  const phi = lat * D2R;
  const p0 = view.lat0 * D2R;
  return Math.sin(p0) * Math.sin(phi)
       + Math.cos(p0) * Math.cos(phi) * Math.cos(lam);
}

function seeds(u, v, view) {
  const { lon0, lat0 } = view;
  const clampLat = (d) => Math.max(-90, Math.min(90, d));
  const out = [[lon0 + u * 180, clampLat(v * 180)]];
  const rho = Math.hypot(u, v);
  if (rho <= 1 && rho > 1e-12) {
    const c = Math.asin(Math.max(-1, Math.min(1, rho)));
    const p0 = lat0 * D2R;
    const latS = Math.asin(Math.cos(c) * Math.sin(p0)
                         + (v * Math.sin(c) * Math.cos(p0)) / rho) * R2D;
    const lonS = lon0 + Math.atan2(
      u * Math.sin(c),
      rho * Math.cos(c) * Math.cos(p0) - v * Math.sin(c) * Math.sin(p0)) * R2D;
    out.push([lonS, latS]);
  }
  for (let k = 0; k < 4; k += 1) out.push([lon0 + 90 * k, clampLat(v * 180)]);
  return out;
}

function newton(x, y, lon, lat, view) {
  for (let i = 0; i < 24; i += 1) {
    const f = project(lon, lat, view);
    const ex = f.x - x;
    const ey = f.y - y;
    if (Math.abs(ex) < 1e-11 && Math.abs(ey) < 1e-11) break;
    const h = 1e-6;
    const a = project(lon + h, lat, view);
    const b = project(lon, lat + h, view);
    const j11 = (a.x - f.x) / h;
    const j21 = (a.y - f.y) / h;
    const j12 = (b.x - f.x) / h;
    const j22 = (b.y - f.y) / h;
    const det = j11 * j22 - j12 * j21;
    if (Math.abs(det) < 1e-14) return null;
    lon -= (ex * j22 - ey * j12) / det;
    lat -= (ey * j11 - ex * j21) / det;
    lat = Math.max(-90, Math.min(90, lat));
  }
  const f = project(lon, lat, view);
  const residual = Math.hypot(f.x - x, f.y - y);
  if (residual > 1e-6 || !f.visible) return null;
  return { lon, lat, residual, depth: cosC(lon, lat, view) };
}

/**
 * Screen back to {lon, lat}, or null outside the figure.
 *
 * Analytic at both ends, where the map is injective. Between them it is NOT: a
 * point on the front of the sphere and one on the back can land on the same
 * pixel, so there is no single right answer and this returns the one nearest
 * the viewer — what a reader pointing at that pixel means.
 */
export function invert(x, y, view) {
  const { lon0, lat0, t, R, cx, cy } = view;
  const u = (x - cx) / R;
  const v = (cy - y) / R;

  if (t <= 0) {
    // A point exactly ON the limb computes rho = 1 plus or minus an ulp, and a
    // bare `rho > 1` rejects half of those. The limb is a legitimate place to
    // be. Python and this file landed on opposite sides of that ulp, which is
    // how the cliff was found; both now have the slack.
    let rho = Math.hypot(u, v);
    if (rho > 1 + 1e-9) return null;
    rho = Math.min(rho, 1);
    const c = Math.asin(Math.max(-1, Math.min(1, rho)));
    if (rho < 1e-12) return { lon: lon0, lat: lat0 };
    const p0 = lat0 * D2R;
    const lat1 = Math.asin(Math.cos(c) * Math.sin(p0)
                         + (v * Math.sin(c) * Math.cos(p0)) / rho) * R2D;
    const lon1 = lon0 + Math.atan2(
      u * Math.sin(c),
      rho * Math.cos(c) * Math.cos(p0) - v * Math.sin(c) * Math.sin(p0)) * R2D;
    return { lon: wrap180(lon1), lat: lat1 };
  }
  if (t >= 1) {
    if (Math.abs(u) > 1 || Math.abs(v) > 0.5) return null;
    return { lon: wrap180(lon0 + u * 180), lat: v * 180 };
  }

  let best = null;
  for (const [seedLon, seedLat] of seeds(u, v, view)) {
    const root = newton(x, y, seedLon, seedLat, view);
    if (!root) continue;
    if (best === null
        || -root.depth < -best.depth
        || (root.depth === best.depth && root.residual < best.residual)) {
      best = root;
    }
  }
  if (best === null) return null;
  return { lon: wrap180(best.lon), lat: best.lat };
}

/**
 * Split a [lon, lat] ring where it crosses the moving antimeridian.
 *
 * Longitude is relative to lon0, so the seam turns with the globe. A ring that
 * crosses it draws a horizontal streak across the whole map as t rises — the
 * two ends of the world joined by a straight line. Splitting is not optional.
 */
function seamCrossing(a, b, lon0) {
  const ra = wrap180(a[0] - lon0);
  const rb = wrap180(b[0] - lon0);
  const rbU = rb + (rb < ra ? 360 : -360);
  const edge = rbU > ra ? 180 : -180;
  const span = rbU - ra;
  let f = span === 0 ? 0 : (edge - ra) / span;
  f = Math.max(0, Math.min(1, f));
  const lat = a[1] + (b[1] - a[1]) * f;
  // Nudged a hair inside each side: exactly lon0+180 wraps to -180, so both
  // points would land on the same edge and the segment between them would run
  // the full width of the map.
  const inset = 1e-6 * (edge > 0 ? 1 : -1);
  return [[lon0 + edge - inset, lat], [lon0 - edge + inset, lat]];
}

export function splitAtSeam(ring, lon0) {
  const rel = (lon) => wrap180(lon - lon0);
  // A vertex sitting EXACTLY on the seam has no side, and wrap180 sends it to
  // the left edge whichever side it belongs to. Natural Earth carries such
  // vertices, and one next to a neighbour at 177.99 drew a line the full width
  // of the map. Give each the side its predecessor is on, first.
  let ring2 = ring;
  if (ring.length > 1) {
    ring2 = [];
    let prevRel = null;
    for (const [lon, lat] of ring) {
      let r = rel(lon);
      let lo = lon;
      if (Math.abs(Math.abs(r) - 180) < 1e-9 && prevRel !== null) {
        const side = prevRel >= 0 ? 1 : -1;
        lo = lon0 + side * (180 - 1e-6);
        r = side * (180 - 1e-6);
      }
      ring2.push([lo, lat]);
      prevRel = r;
    }
  }
  const parts = [];
  let cur = [];
  for (let i = 0; i < ring2.length; i += 1) {
    if (i && Math.abs(rel(ring2[i][0]) - rel(ring2[i - 1][0])) > 180) {
      // The exact crossing, on both sides. Cutting between samples leaves each
      // half ending short of the edge, and the two ends then sit on opposite
      // sides of the map: closing that half draws a chord across everything.
      const [outPt, inPt] = seamCrossing(ring2[i - 1], ring2[i], lon0);
      cur.push(outPt);
      if (cur.length > 1) parts.push(cur);
      cur = [inPt];
    }
    cur.push(ring2[i]);
  }
  if (cur.length > 1) parts.push(cur);
  // Deliberately NOT joining the last piece to the first. They are contiguous,
  // but a ring that wraps the world — Antarctica crosses the seam once — then
  // comes back as one piece with its ends on opposite edges, and closing that
  // runs a line across the map. With crossings inserted exactly, each piece
  // already ends on the edge it left by.
  return parts;
}

/**
 * Densify an edge so it curves under projection instead of cutting the sphere.
 * Mirrors densify in scripts/lib/geo_projection.py. It lives here rather than in a
 * renderer because clipToCap below needs it and both back ends need that.
 */
export function densify(ring, stepDeg) {
  const out = [];
  for (let i = 0; i < ring.length - 1; i += 1) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[i + 1];
    const n = Math.max(1, Math.floor(
      Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) / stepDeg));
    for (let k = 0; k < n; k += 1) {
      out.push([x0 + ((x1 - x0) * k) / n, y0 + ((y1 - y0) * k) / n]);
    }
  }
  out.push(ring[ring.length - 1]);
  return out;
}

/**
 * Chamberlain-Duquette signed spherical area of a [lon, lat] ring, in
 * steradians. The SIGN is the ring's handedness and is what callers want.
 *
 * Positive means the interior lies to the RIGHT of the traversal seen from
 * outside the sphere, which is the convention this package's topology carries:
 * of the 278 rings in the world topology, 277 are positive and the one negative
 * ring is South Africa's second — the hole that is Lesotho.
 *
 * ONLY MEANINGFUL WELL BELOW A HEMISPHERE: the branch wraps past one, so a cap
 * of 91 degrees scores negative where one of 89 scores positive. Country rings
 * are far below it; the visible cap is far above it for every t > 0, which is
 * why clipToCap takes the cap's handedness from its azimuth parameterisation
 * instead. Mirrors signed_area in scripts/lib/geo_projection.py.
 */
export function signedArea(ring) {
  const r = (ring[0][0] === ring[ring.length - 1][0]
    && ring[0][1] === ring[ring.length - 1][1]) ? ring : ring.concat([ring[0]]);
  let s = 0;
  for (let i = 0; i < r.length - 1; i += 1) {
    const [lo1, la1] = r[i];
    const [lo2, la2] = r[i + 1];
    s += ((((lo2 - lo1 + 180) % 360) + 360) % 360 - 180) * D2R
      * (2 + Math.sin(la1 * D2R) + Math.sin(la2 * D2R));
  }
  return s / 2;
}

/** Initial bearing from the projection centre to a point, in [0, 2pi). */
export function azimuth(lon, lat, view) {
  const lam = (lon - view.lon0) * D2R;
  const phi = lat * D2R;
  const p0 = view.lat0 * D2R;
  const a = Math.atan2(
    Math.sin(lam) * Math.cos(phi),
    Math.cos(p0) * Math.sin(phi) - Math.sin(p0) * Math.cos(phi) * Math.cos(lam));
  return ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
}

/**
 * The point at angular distance c and bearing az from the centre.
 *
 * Azimuth increasing runs N-E-S-W, so it traverses the cap with the interior on
 * the RIGHT seen from outside — the same handedness signedArea calls positive.
 * That correspondence is the whole direction rule.
 */
export function capPoint(az, c, view) {
  const p0 = view.lat0 * D2R;
  const lat = Math.asin(Math.max(-1, Math.min(1,
    Math.sin(p0) * Math.cos(c) + Math.cos(p0) * Math.sin(c) * Math.cos(az))));
  const lon = view.lon0 + Math.atan2(
    Math.sin(az) * Math.sin(c) * Math.cos(p0),
    Math.cos(c) - Math.sin(p0) * Math.sin(lat)) * R2D;
  return [lon, lat * R2D];
}

const CAP_STEP_DEG = 1.5;

// A point this close to the cap is ON it, and a point on the boundary is not
// INSIDE it. Natural Earth closes Antarctica along the lat = -90 edge of its
// rectangular source map, so 181 of its 433 densified points are a pole
// artifact rather than coastline; at t=0, where the cap passes exactly through
// both poles, every one of them evaluates to cos_c = +-6.1e-17. Counted as
// interior they form a phantom run and the fill walks the entire limb.
// Mirrors CAP_EPS in scripts/lib/geo_projection.py.
const CAP_EPS = 1e-9;

/**
 * Intersect a [lon, lat] ring with the visible cap. -> array of closed rings.
 *
 * THE CLIP HAPPENS ON THE SPHERE, before projection, and that is the point.
 * Clipping in screen space means closing along a projected cap, and a projected
 * cap is not a closed curve: project wraps longitude into (-180, 180] before
 * mixing in the plane term, so a sampled cap jumps the full width of the seam
 * twice at every t > 0. Every flat closure recorded in 0.1.388 was one of those
 * jumps. On the sphere the cap is a circle in azimuth with no seam in it at
 * all. Splitting at the seam then happens afterwards, to a ring that is already
 * correctly closed.
 *
 * Runs are LINKED rather than each closed on itself, so a country the cap cuts
 * into two visible pieces comes back as one polygon when that is what it is.
 * Mirrors clip_to_cap in scripts/lib/geo_projection.py, and the golden grid in
 * scripts/check/check_globe.py is what holds the two together.
 */
// How much larger than its source a clipped ring may be before its closure is
// judged to have gone the wrong way, in steradians. Mirrors CLOSURE_SLACK in
// scripts/lib/geo_projection.py: larger than any country ring in this topology
// (Russia, the largest, is 0.41 sr) and far smaller than the 2*pi a wrong-way
// closure encloses.
const CLOSURE_SLACK = 0.35;

/** Re-walk one closed piece's cap arc in the given direction. */
function reclose(seq, view, c, step, forward) {
  const onCap = new Set();
  seq.forEach((p, i) => {
    const d = Math.acos(Math.max(-1, Math.min(1, cosC(p[0], p[1], view))));
    if (Math.abs(d - c) < 1e-6) onCap.add(i);
  });
  if (!onCap.size) return null;
  const keep = seq.filter((_p, i) => !onCap.has(i));
  if (keep.length < 2) return null;
  const a0 = azimuth(keep[keep.length - 1][0], keep[keep.length - 1][1], view);
  const a1 = azimuth(keep[0][0], keep[0][1], view);
  const TAU = 2 * Math.PI;
  const span = forward ? ((a1 - a0) % TAU + TAU) % TAU : ((a0 - a1) % TAU + TAU) % TAU;
  const steps = Math.max(1, Math.ceil(span / step));
  const arc = [];
  for (let i = 1; i < steps; i += 1) {
    const az = (a0 + (span * i / steps) * (forward ? 1 : -1)) % TAU;
    arc.push(capPoint((az + TAU) % TAU, c, view));
  }
  return keep.concat(arc, [keep[0]]);
}

export function clipToCap(ring, view, stepDeg, forwardIn) {
  if (view.t >= 1) return [ring.slice()];
  const c = Math.acos(Math.max(-1, Math.min(1, -view.t)));
  let dense = ring.length > 1 ? densify(ring, stepDeg) : ring.slice();
  if (dense.length < 3) return [];

  const vis = (p) => cosC(p[0], p[1], view) > -view.t + CAP_EPS;
  const cross = (inside, outside) => {
    let a = inside;
    let b = outside;
    for (let i = 0; i < 40; i += 1) {
      const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      if (vis(m)) a = m; else b = m;
    }
    return capPoint(azimuth(a[0], a[1], view), c, view);
  };

  // Rotate so the walk BEGINS AT A RUN's first vertex — a visible vertex whose
  // predecessor is hidden — not merely at a visible one. Starting inside a run
  // splits it across the seam of the traversal, and the tail then has no exit
  // crossing of its own; dropped as degenerate, it takes an entry crossing with
  // it and the closure is linked to an INTERIOR point, walking to an azimuth
  // that is not on the cap. Mirrors clip_to_cap in geo_projection.py.
  if (dense[0][0] === dense[dense.length - 1][0]
    && dense[0][1] === dense[dense.length - 1][1]) dense = dense.slice(0, -1);
  const n = dense.length;
  const seen = dense.map(vis);
  if (seen.every(Boolean)) return [ring.slice()];
  if (!seen.some(Boolean)) return [];
  let first = 0;
  for (let i = 0; i < n; i += 1) {
    if (seen[i] && !seen[(i + n - 1) % n]) { first = i; break; }
  }
  const order = [];
  for (let k = 0; k < n; k += 1) order.push(dense[(first + k) % n]);

  // prev starts on the hidden vertex before the rotation point, so the first
  // run gets its entry crossing like any other. The last vertex walked is that
  // same hidden one, so the loop closes every run and none is left over.
  const runs = [];
  let cur = [];
  let prev = [dense[(first + n - 1) % n], false];
  for (const pt of order) {
    const v = vis(pt);
    if (v) {
      if (!prev[1]) cur.push(cross(pt, prev[0]));
      cur.push(pt);
    } else {
      if (prev[1]) {
        cur.push(cross(prev[0], pt));
        if (cur.length > 2) runs.push(cur);
        cur = [];
      }
    }
    prev = [pt, v];
  }
  if (!runs.length) return [];

  // `forward` overrides the handedness for a ring built by capPoint, whose
  // interior is on the right by construction. signedArea cannot read a ring
  // within a hair of a hemisphere — the terminator is exactly that — so the
  // Python authority takes the same override. Mirrors clip_to_cap in
  // scripts/lib/geo_projection.py.
  const forwardGiven = forwardIn !== undefined;
  const forward = forwardIn === undefined ? signedArea(ring) > 0 : forwardIn;
  const step = CAP_STEP_DEG * D2R;
  const ends = runs.map((r) => [azimuth(r[0][0], r[0][1], view),
    azimuth(r[r.length - 1][0], r[r.length - 1][1], view), r]);

  const out = [];
  const used = new Set();
  for (let start = 0; start < ends.length; start += 1) {
    if (used.has(start)) continue;
    let seq = [];
    let k = start;
    while (!used.has(k)) {
      used.add(k);
      const exitAz = ends[k][1];
      seq = seq.concat(ends[k][2]);
      let best = k;
      let bestd = null;
      for (let j = 0; j < ends.length; j += 1) {
        const raw = forward ? ends[j][0] - exitAz : exitAz - ends[j][0];
        let d = ((raw % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
        // An entry sitting ON this run's exit is a JOIN when it belongs to
        // another run and a FULL WRAP when it is this run's own. Antarctica's
        // source ring carries an artificial break at lon 180, so at a
        // Pacific-centred view its coastline arrives as two runs meeting
        // exactly there; reading that zero as a wrap painted the whole disc.
        if (d <= 1e-12 && j === k) d = 2 * Math.PI;
        if (bestd === null || d < bestd) { bestd = d; best = j; }
      }
      const span = bestd;
      const steps = Math.max(1, Math.ceil(span / step));
      for (let s = 1; s < steps; s += 1) {
        const az = exitAz + ((span * s) / steps) * (forward ? 1 : -1);
        seq.push(capPoint(((az % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI), c, view));
      }
      k = best;
    }
    if (seq.length > 2) out.push(seq.concat([seq[0]]));
  }

  // THE TANGENT GUARD. Mirrors clip_to_cap in scripts/lib/geo_projection.py, and
  // the reason it is here rather than only there is the whole point: the fix
  // shipped in Python, the emitter's sweep went green, and every frame after
  // the first is drawn by THIS file — so a country grazing the limb went on
  // being painted over the entire disc, six frames per revolution, with the
  // repair sitting in a language the runtime does not run. That is the second
  // time a repair has reached one side of this hand-maintained port; 0.1.405
  // is the first, and it has its own paragraph in the changelog saying so.
  //
  // A clipped ring cannot enclose more of the sphere than the ring it came
  // from plus the sliver a cap arc adds. Where it does, both closure
  // directions are re-walked and the smaller kept.
  if (forwardGiven) return out;
  const source = Math.abs(signedArea(ring));
  const fixed = [];
  for (const seq of out) {
    if (Math.abs(signedArea(seq)) <= source + CLOSURE_SLACK) { fixed.push(seq); continue; }
    let best = seq;
    for (const dir of [true, false]) {
      const alt = reclose(seq, view, c, step, dir);
      if (alt && Math.abs(signedArea(alt)) < Math.abs(signedArea(best))) best = alt;
    }
    fixed.push(best);
  }
  return fixed;
}
