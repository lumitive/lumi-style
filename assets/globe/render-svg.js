// The deliverable back end: mutate the static frame, never replace it.
//
// scripts/globe_svg.py emits the markup and this file rewrites its `d`
// attributes as the view changes. It creates no elements and destroys none,
// which is what keeps three things true at once: the file on disk is a complete
// no-JavaScript fallback, every gate in this package can still read the figure
// as markup, and a screen reader's tree does not churn under animation.
//
// It also hands back the projected runs it just built, because the hit test
// wants exactly those and projecting the world twice per frame would be silly.

import { project, splitAtSeam, cosC } from './projection.js';
import { ringsOf, ringsOfRegion } from './worlddata.js';

const STEP_DEG = 2;
// Matches PAD in scripts/globe_svg.py, in the same user units.
const PAD = 40;

/**
 * The exact extent of everything drawable at this t, analytically.
 *
 * Sampling it per frame would make the box breathe as the globe turns, and
 * leaving it at whatever the generator computed puts a 2:1 flat map inside a 1:1
 * square — the frame renders at half the height its cell allows, which is the
 * aspect mismatch inspect_layout names and which check_globe gates the static
 * frame on. It has to move with t, and it must depend on t alone.
 *
 * x is always +/-R: the sphere term spans [-1, 1] and so does the plane term.
 * y shrinks to +/-R/2 as the plane term (+/-0.5) takes over, hence 1 - t/2.
 */
function viewBoxFor(view) {
  const halfW = view.R / view.zoom;
  const halfH = (view.R * (1 - view.t / 2)) / view.zoom;
  const pad = PAD * (view.R / 1000);
  return [view.cx - halfW - pad, view.cy - halfH - pad,
    2 * (halfW + pad), 2 * (halfH + pad)];
}

/** Densify an edge so it curves under projection instead of cutting the sphere. */
function densify(ring, stepDeg) {
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

const D2R = Math.PI / 180;
const R2D = 180 / Math.PI;
const BOUNDARY_SAMPLES = 240;

/**
 * The visibility boundary in screen space, as a closed polyline.
 *
 * A clipped ring has to be closed along this curve, not with a straight line
 * between its two ends. Closing with a chord is what produced the crimson
 * slivers down the right limb of the mid-unroll frame: `Z` joins the last point
 * to the first, and for a country cut in half by the horizon those two points
 * are nowhere near each other. build_geography.py has always walked the limb for
 * exactly this reason; the runtime has to as well, and mid-unroll the boundary
 * is no longer a circle so it is sampled rather than drawn as an arc.
 *
 * The boundary is where cos_c = -t: a small circle at angular distance
 * acos(-t) from the view centre, which is the horizon at t=0 and the whole
 * sphere at t=1.
 */
function boundaryFor(view) {
  if (view.t >= 1) return null;
  const c = Math.acos(Math.max(-1, Math.min(1, -view.t)));
  const p0 = view.lat0 * D2R;
  const out = [];
  for (let i = 0; i < BOUNDARY_SAMPLES; i += 1) {
    const az = (2 * Math.PI * i) / BOUNDARY_SAMPLES;
    const lat = Math.asin(Math.sin(p0) * Math.cos(c)
      + Math.cos(p0) * Math.sin(c) * Math.cos(az));
    const lon = view.lon0 + Math.atan2(
      Math.sin(az) * Math.sin(c) * Math.cos(p0),
      Math.cos(c) - Math.sin(p0) * Math.sin(lat)) * R2D;
    const p = project(lon, lat * R2D, view);
    out.push([p.x, p.y]);
  }
  return out;
}

function nearestBoundaryIndex(pt, boundary) {
  let best = 0;
  let bestD = Infinity;
  for (let i = 0; i < boundary.length; i += 1) {
    const d = (boundary[i][0] - pt[0]) ** 2 + (boundary[i][1] - pt[1]) ** 2;
    if (d < bestD) { bestD = d; best = i; }
  }
  return best;
}

/** The shorter way round the boundary from index a to index b. */
function boundaryWalk(a, b, boundary) {
  const n = boundary.length;
  const fwd = (b - a + n) % n;
  const out = [];
  if (fwd <= n - fwd) {
    for (let k = 1; k <= fwd; k += 1) out.push(boundary[(a + k) % n]);
  } else {
    for (let k = 1; k <= n - fwd; k += 1) out.push(boundary[(a - k + n) % n]);
  }
  return out;
}

/** Project one lat/lon ring into screen-space runs, cut at the seam and the limb. */
function projectRing(ring, view, boundary) {
  const runs = [];
  for (const part of splitAtSeam(ring, view.lon0)) {
    const dense = part.length > 1 ? densify(part, STEP_DEG) : part;
    let cur = [];
    for (const [lon, lat] of dense) {
      const p = project(lon, lat, view);
      if (p.visible) {
        cur.push([p.x, p.y]);
      } else {
        if (cur.length > 1) runs.push(cur);
        cur = [];
      }
    }
    if (cur.length > 1) runs.push(cur);
  }
  // A run that starts and ends on the boundary was cut by it, so close it along
  // the boundary. Without this the fill balloons across the sphere.
  if (!boundary) return runs;
  return runs.map((run) => {
    if (run.length < 3) return run;
    const startI = nearestBoundaryIndex(run[0], boundary);
    const endI = nearestBoundaryIndex(run[run.length - 1], boundary);
    const near = (pt, i) => (boundary[i][0] - pt[0]) ** 2
      + (boundary[i][1] - pt[1]) ** 2 < (view.R * 0.03) ** 2;
    if (!near(run[0], startI) || !near(run[run.length - 1], endI)) return run;
    return run.concat(boundaryWalk(endI, startI, boundary));
  });
}

function pathData(runs, close) {
  let d = '';
  for (const pts of runs) {
    d += `M${pts[0][0].toFixed(0)} ${pts[0][1].toFixed(0)}`;
    for (let i = 1; i < pts.length; i += 1) {
      d += `L${pts[i][0].toFixed(0)} ${pts[i][1].toFixed(0)}`;
    }
    if (close) d += 'Z';
  }
  return d;
}

/**
 * @param {SVGElement} svg   the markup globe_svg.py emitted
 * @param {object} data      decode() output
 * @returns {{draw(view, state): object, destroy(): void}}
 *   draw returns {regions: Map<id, runs[]>, marks: [{x,y,index}], t}
 *   — the hit test reads that rather than projecting the world a second time.
 */
export function createSvgRenderer(svg, data) {
  const plate = svg.querySelector('.gl-plate');
  const graticule = svg.querySelector('.gl-graticule');
  const land = svg.querySelector('.gl-land');
  const regionPaths = new Map();
  for (const el of svg.querySelectorAll('[data-region]')) {
    regionPaths.set(el.getAttribute('data-region'), el);
  }
  const markEls = [...svg.querySelectorAll('.gl-mark')];
  const nodeEls = [...svg.querySelectorAll('.gl-node')];

  // lat/lon geometry is resolved once. Only the projection runs per frame.
  const regionRings = new Map();
  for (const id of regionPaths.keys()) regionRings.set(id, ringsOfRegion(id, data));
  const landRings = land
    ? [...data.countries.keys()].flatMap((c) => ringsOf(c, data))
    : [];
  const graticuleRings = [];
  for (let lon = -180; lon <= 180; lon += 30) {
    const r = [];
    for (let lat = -90; lat <= 90; lat += 3) r.push([lon, lat]);
    graticuleRings.push(r);
  }
  for (let lat = -90; lat <= 90; lat += 30) {
    const r = [];
    for (let lon = -180; lon <= 180; lon += 3) r.push([lon, lat]);
    graticuleRings.push(r);
  }

  function draw(view, state = {}) {
    const out = { regions: new Map(), marks: [], nodes: [], view };
    const boundary = boundaryFor(view);
    const vb = viewBoxFor(view);
    svg.setAttribute('viewBox',
      `${vb[0].toFixed(1)} ${vb[1].toFixed(1)} ${vb[2].toFixed(1)} ${vb[3].toFixed(1)}`);

    if (plate) {
      plate.setAttribute('cx', view.cx.toFixed(0));
      plate.setAttribute('cy', view.cy.toFixed(0));
      plate.setAttribute('r', view.R.toFixed(0));
      plate.setAttribute('opacity', (1 - view.t).toFixed(3));
    }
    if (graticule) {
      let d = '';
      for (const ring of graticuleRings) d += `${pathData(projectRing(ring, view, null), false)} `;
      graticule.setAttribute('d', d.trim());
    }
    if (land) {
      let d = '';
      for (const ring of landRings) d += `${pathData(projectRing(ring, view, boundary), true)} `;
      land.setAttribute('d', d.trim());
    }
    for (const [id, el] of regionPaths) {
      const runs = [];
      let d = '';
      for (const ring of regionRings.get(id) || []) {
        const r = projectRing(ring, view, boundary);
        for (const run of r) runs.push(run);
        d += `${pathData(r, true)} `;
      }
      el.setAttribute('d', d.trim());
      // Only the STATE class, and only via classList. Rewriting the whole
      // class attribute here silently wiped is-hover on every frame: the hit
      // test was returning the right region the whole time and the highlight
      // was being erased 60 times a second, which looked exactly like a broken
      // hit test. The renderer owns state; it does not own the element.
      const s = (state.regions && state.regions[id] && state.regions[id].state) || 'zero';
      for (const c of [...el.classList]) {
        if (c.startsWith('is-') && c !== 'is-hover') el.classList.remove(c);
      }
      el.classList.add('rg', `rg-${id}`, `is-${s}`);
      out.regions.set(id, runs);
    }
    for (const el of markEls) {
      const lon = Number(el.dataset.lon);
      const lat = Number(el.dataset.lat);
      const p = project(lon, lat, view);
      el.setAttribute('cx', p.x.toFixed(0));
      el.setAttribute('cy', p.y.toFixed(0));
      if (p.visible) el.removeAttribute('hidden');
      else el.setAttribute('hidden', '');
      if (p.visible) out.marks.push({ x: p.x, y: p.y, el });
    }
    for (const el of nodeEls) {
      const lon = Number(el.dataset.lon);
      const lat = Number(el.dataset.lat);
      const p = project(lon, lat, view);
      el.setAttribute('cx', p.x.toFixed(0));
      el.setAttribute('cy', p.y.toFixed(0));
      if (p.visible) el.removeAttribute('hidden');
      else el.setAttribute('hidden', '');
      if (p.visible) out.nodes.push({ x: p.x, y: p.y, el, id: el.dataset.node });
    }
    return out;
  }

  return { draw, destroy() {}, svg };
}

export { projectRing, pathData, viewBoxFor };
