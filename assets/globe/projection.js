// Sphere-to-screen maths for the LUMI globe.
//
// A hand port of scripts/geo_projection.py. THE PYTHON IS THE AUTHORITY: this
// file is checked against it over a golden grid by scripts/check_globe.py, to
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
