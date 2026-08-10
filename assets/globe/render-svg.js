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

import {
  project, splitAtSeam, densify, clipToCap,
} from '../geo/projection.js';
import { ringsOf, ringsOfRegion } from '../geo/worlddata.js';

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

/**
 * Close a piece whose two ends sit on OPPOSITE sides of the seam.
 *
 * Only a world-wrapping ring does this — Antarctica crosses the seam once — and
 * the way a map draws it is around the pole, not straight across.
 *
 * Both edges are exact rather than fitted. At lon_rel = +-180 the sphere term
 * cos(phi) sin(lam) vanishes at every latitude, so THE SEAM IS A PAIR OF
 * VERTICAL LINES at x = cx +- tR. A pole is a point on the sphere and a SEGMENT
 * on the unrolled map, at y = cy -+ R(1 - t/2), spanning those two verticals.
 * Both collapse at t=0 and both are the whole boundary at t=1.
 *
 * Mirrors _pole_close in scripts/globe_svg.py. Until 0.1.389 both sides were
 * restricted to t=1 and measured against x = cx +- R, the seam's position at
 * t=1 only.
 */
function poleClose(a, b, view) {
  if (view.t <= 0) return [];
  const left = view.cx - view.t * view.R;
  const right = view.cx + view.t * view.R;
  const eps = Math.max(view.R * 0.002, view.t * view.R * 0.02);
  const on = (p, e) => Math.abs(p[0] - e) < eps;
  if (!((on(a, left) || on(a, right)) && (on(b, left) || on(b, right)))) return [];
  if ((on(a, left) && on(b, left)) || (on(a, right) && on(b, right))) return [];
  const half = view.R * (1 - view.t / 2);
  const edgeY = (a[1] + b[1]) / 2 > view.cy ? view.cy + half : view.cy - half;
  return [[a[0], edgeY], [b[0], edgeY]];
}

/**
 * Project an OPEN line such as a graticule into screen-space runs.
 * No closure and no cap closing: a line that leaves the figure simply stops.
 */
function projectRing(ring, view) {
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
  return runs;
}

/**
 * Project a FILLED ring into screen-space runs, already closed.
 *
 * Three steps in this order, and the order is the fix that 0.1.389 is: clip to
 * the cap ON THE SPHERE in the ring's own winding, split the closed result at
 * the seam, then project. Clipping in screen space means closing along a
 * projected cap, and a projected cap jumps the width of the seam twice at every
 * t > 0. Mirrors _project_area in scripts/globe_svg.py.
 */
function projectArea(ring, view) {
  const runs = [];
  for (const closed of clipToCap(ring, view, STEP_DEG)) {
    for (const part of splitAtSeam(closed, view.lon0)) {
      const pts = part.map(([lo, la]) => {
        const p = project(lo, la, view);
        return [p.x, p.y];
      });
      if (pts.length > 1) runs.push(pts);
    }
  }
  return runs;
}

/**
 * Split any run wherever consecutive points are more than R apart.
 *
 * An invariant, not a patch over one bug: in this projection no real polygon
 * edge spans half the figure, so a pair that does means a cut that did not
 * take. Mirrors _guard in scripts/globe_svg.py.
 */
function guard(runs, R) {
  const out = [];
  for (const run of runs) {
    let cur = [run[0]];
    for (let i = 1; i < run.length; i += 1) {
      if (Math.hypot(run[i][0] - run[i - 1][0], run[i][1] - run[i - 1][1]) > R) {
        if (cur.length > 1) out.push(cur);
        cur = [];
      }
      cur.push(run[i]);
    }
    if (cur.length > 1) out.push(cur);
  }
  return out;
}

/** Round half away from zero. Mirrors _r in scripts/globe_svg.py; the two
 *  renderers must produce the same integer for the same coordinate. */
function r0(v) {
  return (v >= 0 ? 1 : -1) * Math.floor(Math.abs(v) + 0.5);
}

function pathData(runs, close, view) {
  let d = '';
  const closedRuns = runs.map((raw) => ((close && view && raw.length > 2)
    ? raw.concat(poleClose(raw[raw.length - 1], raw[0], view)) : raw));
  // The guard runs LAST, after every closure: a closure can introduce the very
  // thing it guards against.
  for (const pts of (view ? guard(closedRuns, view.R) : closedRuns)) {
    d += `M${r0(pts[0][0])} ${r0(pts[0][1])}`;
    for (let i = 1; i < pts.length; i += 1) {
      d += `L${r0(pts[i][0])} ${r0(pts[i][1])}`;
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
    const vb = viewBoxFor(view);
    svg.setAttribute('viewBox',
      `${vb[0].toFixed(1)} ${vb[1].toFixed(1)} ${vb[2].toFixed(1)} ${vb[3].toFixed(1)}`);

    if (plate) {
      plate.setAttribute('cx', r0(view.cx));
      plate.setAttribute('cy', r0(view.cy));
      plate.setAttribute('r', r0(view.R));
      plate.setAttribute('opacity', (1 - view.t).toFixed(3));
    }
    if (graticule) {
      let d = '';
      for (const ring of graticuleRings) d += `${pathData(projectRing(ring, view), false)} `;
      graticule.setAttribute('d', d.trim());
    }
    if (land) {
      let d = '';
      for (const ring of landRings) d += `${pathData(projectArea(ring, view), true, view)} `;
      land.setAttribute('d', d.trim());
    }
    for (const [id, el] of regionPaths) {
      const runs = [];
      let d = '';
      for (const ring of regionRings.get(id) || []) {
        const r = projectArea(ring, view);
        for (const run of r) runs.push(run);
        d += `${pathData(r, true, view)} `;
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
      el.setAttribute('cx', r0(p.x));
      el.setAttribute('cy', r0(p.y));
      if (p.visible) el.removeAttribute('hidden');
      else el.setAttribute('hidden', '');
      if (p.visible) out.marks.push({ x: p.x, y: p.y, el, id: el.dataset.mark });
    }
    for (const el of nodeEls) {
      const lon = Number(el.dataset.lon);
      const lat = Number(el.dataset.lat);
      const p = project(lon, lat, view);
      el.setAttribute('cx', r0(p.x));
      el.setAttribute('cy', r0(p.y));
      if (p.visible) el.removeAttribute('hidden');
      else el.setAttribute('hidden', '');
      if (p.visible) out.nodes.push({ x: p.x, y: p.y, el, id: el.dataset.node });
    }
    return out;
  }

  return { draw, destroy() {}, svg };
}

export {
  projectRing, projectArea, pathData, viewBoxFor,
};
