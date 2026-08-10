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
  project, splitAtSeam, densify, clipToCap, cosC,
} from '../geo/projection.js';
import { ringsOf } from '../geo/worlddata.js';

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
  const markEls = [...svg.querySelectorAll('.gl-mark')];
  const nodeEls = [...svg.querySelectorAll('.gl-node')];
  // The bloc fills, if this globe carries a registry. Each path names its own
  // members in the markup, so the runtime needs no registry of its own — the
  // same reason a mark carries its lat/lon rather than an index into a table.
  const blocEls = [...svg.querySelectorAll('.gl-rg')];
  const blocLabelEls = [...svg.querySelectorAll('.gl-rg-label')];
  const cityDots = [...svg.querySelectorAll('.gl-city-dot')];
  // Trade lanes and the signals riding them. Lanes sit ON the sphere, so they
  // turn with the geography and are redrawn every frame like the coastline.
  const linkEls = [...svg.querySelectorAll('.gl-link')];
  const hubEls = [...svg.querySelectorAll('.gl-hub')];
  const linkRings = new Map(linkEls.map((el) => {
    const route = (el.dataset.route || '').split(';')
      .map((p) => p.split(',').map(Number))
      .filter((p) => p.length === 2 && Number.isFinite(p[0]));
    return [el, greatCircleRoute(route)];
  }));
  const linkById = new Map(linkEls.map((el) => [el.dataset.link, el]));
  const sigEls = [...svg.querySelectorAll('.gl-sig')].map((g) => ({
    g,
    dot: g.querySelector('circle'),
    txt: g.querySelector('text'),
    path: linkById.get(g.dataset.sigLink) || null,
    t: Number(g.dataset.t) || 0,
    ci: Number(g.dataset.code) || 0,
  })).filter((s) => s.path);
  const cityLabels = new Map();
  for (const el of svg.querySelectorAll('.gl-city')) {
    cityLabels.set(el.dataset.cityLabel, el);
  }

  // lat/lon geometry is resolved once. Only the projection runs per frame.
  // Routed exactly as scripts/globe_svg.py routes it: a country belongs to one
  // bloc or to none, so every ring is resolved once and lands in one bucket.
  // Without blocs this is the single land list it has always been.
  const claimed = new Map();
  for (const el of blocEls) {
    for (const code of (el.dataset.members || '').split(' ').filter(Boolean)) {
      claimed.set(code, el);
    }
  }
  const blocRings = new Map(blocEls.map((el) => [el, []]));
  const landRings = [];
  if (land || blocEls.length) {
    for (const code of data.countries.keys()) {
      const target = claimed.has(code) ? blocRings.get(claimed.get(code)) : landRings;
      for (const ring of ringsOf(code, data)) target.push(ring);
    }
  }
  // 15 degrees, mirroring GLOBE_GRATICULE in scripts/globe_svg.py. The
  // graticule is the cue that makes a flat disc read as a sphere, and the
  // first cut's 30 degrees was too sparse to do that work once the geography
  // went quiet. The equator is skipped here because it is a NAMED line below.
  const graticuleRings = [];
  for (let lon = -180; lon <= 180; lon += 15) {
    const r = [];
    for (let lat = -90; lat <= 90; lat += 3) r.push([lon, lat]);
    graticuleRings.push(r);
  }
  for (let lat = -90; lat <= 90; lat += 15) {
    if (lat === 0) continue;
    const r = [];
    for (let lon = -180; lon <= 180; lon += 3) r.push([lon, lat]);
    graticuleRings.push(r);
  }
  // The named circles. They rotate with the geography like anything else, and
  // leaving them out of the redraw would pin them to the frame they were
  // generated in while the world turned underneath.
  const equator = svg.querySelector('.gl-equator');
  const tropics = svg.querySelector('.gl-tropic');
  const OBLIQUITY = 23.4392811;
  const ringAt = (lat) => {
    const r = [];
    for (let lon = -180; lon <= 180; lon += 3) r.push([lon, lat]);
    return r;
  };
  const equatorRing = ringAt(0);
  const tropicRings = [ringAt(OBLIQUITY), ringAt(-OBLIQUITY)];

  // A city's label is placed by the same two rules the emitter uses, ported
  // here rather than shared: the frame the emitter wrote is correct for its own
  // rotation only, and the moment the globe turns the crowding changes. See
  // place_city_labels in scripts/geo_frame.py — same order, same comparison,
  // same drop, so a paused globe and a printed one agree.
  const CITY_GAP = 0.9;
  // Cancel the earth group's tilt for one label, about its own anchor. Mirrors
  // _upright in scripts/globe_svg.py: every layer lives inside .gl-earth, and
  // a name set at 23 degrees is a name the reader tips their head for.
  const upright = (x, y) => `rotate(${-OBLIQUITY} ${x.toFixed(1)} ${y.toFixed(1)})`;
  const TILT = (OBLIQUITY * Math.PI) / 180;
  // A point in the earth group's space, as the reader SEES it. Placement asks
  // a screen question — does this word land on that word — and the group
  // rotates, so asking it in group space compares boxes nobody ever sees.
  // Mirrors tilt_to_screen in scripts/geo_frame.py.
  const toScreen = (x, y, cx, cy) => {
    const dx = x - cx;
    const dy = y - cy;
    return [cx + dx * Math.cos(TILT) - dy * Math.sin(TILT),
      cy + dx * Math.sin(TILT) + dy * Math.cos(TILT)];
  };
  // A screen-space offset back in group space: each label is counter-rotated
  // so its glyphs run horizontally on screen, and the gap to its dot must too.
  const fromScreen = (dx, dy) => [dx * Math.cos(-TILT) - dy * Math.sin(-TILT),
    dx * Math.sin(-TILT) + dy * Math.cos(-TILT)];

  // 0.66: an over-estimate of the shipped face, which measures 0.48-0.62
  // em/char on real names. Mirrors CITY_EM_W in scripts/geo_frame.py.
  const CITY_EM_W = 0.66;
  const CITY_EM_H = 1.15;
  const LABEL_LIMB_COS = 0.25;

  // Bloc labels first: anchored to their region, hidden well before the limb,
  // and their boxes handed to the city pass. Mirrors scripts/globe_svg.py —
  // the layer that cannot move goes in first.
  function drawBlocLabels(view) {
    const boxes = [];
    for (const el of blocLabelEls) {
      const lon = Number(el.dataset.lon);
      const lat = Number(el.dataset.lat);
      const p = project(lon, lat, view);
      const size = view.R * 0.030;
      el.setAttribute('x', r0(p.x));
      el.setAttribute('y', r0(p.y));
      el.setAttribute('font-size', Math.round(size));
      el.setAttribute('transform', upright(p.x, p.y));
      const shown = p.visible && cosC(lon, lat, view) >= LABEL_LIMB_COS;
      if (shown) el.removeAttribute('display');
      else el.setAttribute('display', 'none');
      if (shown) {
        const w = CITY_EM_W * size * (el.textContent || '').length;
        const h = CITY_EM_H * size;
        const [sx, sy] = toScreen(p.x, p.y, view.cx, view.cy);
        boxes.push([sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2]);
      }
    }
    return boxes;
  }

  // Spherical linear interpolation between two places: the shortest path
  // across a sphere. Mirrors great_circle in scripts/geo_frame.py — same
  // sampling, so the frame the emitter wrote and the frame this draws are the
  // same curve rather than two curves that look alike.
  function greatCircle(a, b, n = 64) {
    const unit = (lon, lat) => {
      const p = lon * Math.PI / 180;
      const q = lat * Math.PI / 180;
      return [Math.cos(q) * Math.cos(p), Math.cos(q) * Math.sin(p), Math.sin(q)];
    };
    const p = unit(a[0], a[1]);
    const q = unit(b[0], b[1]);
    const dot = Math.max(-1, Math.min(1, p[0] * q[0] + p[1] * q[1] + p[2] * q[2]));
    const w = Math.acos(dot);
    if (w < 1e-9) return [[a[0], a[1]]];
    const out = [];
    for (let i = 0; i <= n; i += 1) {
      const t = i / n;
      const s1 = Math.sin((1 - t) * w) / Math.sin(w);
      const s2 = Math.sin(t * w) / Math.sin(w);
      const v = [s1 * p[0] + s2 * q[0], s1 * p[1] + s2 * q[1], s1 * p[2] + s2 * q[2]];
      const m = Math.hypot(v[0], v[1], v[2]);
      let lon = Math.atan2(v[1] / m, v[0] / m) * 180 / Math.PI;
      const lat = Math.asin(Math.max(-1, Math.min(1, v[2] / m))) * 180 / Math.PI;
      // UNWRAP, exactly as great_circle does in scripts/geo_frame.py. atan2
      // returns (-180, 180], so a Pacific lane steps 355 degrees between two
      // adjacent samples and densify sweeps the whole world filling the gap —
      // the lane closes into a ring around the globe.
      if (out.length) {
        while (lon - out[out.length - 1][0] > 180) lon -= 360;
        while (out[out.length - 1][0] - lon > 180) lon += 360;
      }
      out.push([lon, lat]);
    }
    return out;
  }

  // A route through chokepoints, each leg the shortest path, unwrapped across
  // the joints so the whole thing is one continuous ring.
  function greatCircleRoute(waypoints, n = 24) {
    if (waypoints.length < 2) return waypoints.slice();
    let out = [];
    for (let i = 0; i < waypoints.length - 1; i += 1) {
      let leg = greatCircle(waypoints[i], waypoints[i + 1], n);
      if (out.length) {
        let shift = 0;
        while (leg[0][0] + shift - out[out.length - 1][0] > 180) shift -= 360;
        while (out[out.length - 1][0] - (leg[0][0] + shift) > 180) shift += 360;
        leg = leg.map((p) => [p[0] + shift, p[1]]);
        leg = leg.slice(1);
      }
      out = out.concat(leg);
    }
    return out;
  }

  const LINK_R = 1.004;
  const scaled = (view) => ({ ...view, R: view.R * LINK_R });

  function drawLinks(view) {
    const sv = scaled(view);
    for (const el of linkEls) {
      el.setAttribute('d', pathData(projectRing(linkRings.get(el), sv), false));
    }
    for (const el of hubEls) {
      const p = project(Number(el.dataset.lon), Number(el.dataset.lat), sv);
      el.setAttribute('cx', r0(p.x));
      el.setAttribute('cy', r0(p.y));
      if (p.visible) el.removeAttribute('display');
      else el.setAttribute('display', 'none');
    }
  }

  // A signal is one code in transit. Position comes from the lane's own path —
  // the browser already knows where a path goes — so a signal is always exactly
  // on its lane, including where the lane is clipped at the limb.
  function placeSignals(view, codes) {
    for (const s of sigEls) {
      const len = s.path.getTotalLength ? s.path.getTotalLength() : 0;
      if (!len) { s.g.setAttribute('display', 'none'); continue; }
      s.g.removeAttribute('display');
      const p = s.path.getPointAtLength(s.t * len);
      s.dot.setAttribute('cx', r0(p.x));
      s.dot.setAttribute('cy', r0(p.y));
      const ty = p.y - view.R * 0.021;
      s.txt.setAttribute('x', r0(p.x));
      s.txt.setAttribute('y', r0(ty));
      // Upright: every layer here lives inside .gl-earth, which is tilted.
      s.txt.setAttribute('transform', upright(p.x, ty));
      if (codes && codes.length) s.txt.textContent = codes[s.ci % codes.length];
    }
  }

  function drawCities(view, reserved) {
    const size = view.R * 0.026;
    const pts = cityDots.map((el) => {
      const p = project(Number(el.dataset.lon), Number(el.dataset.lat), view);
      const [sx, sy] = toScreen(p.x, p.y, view.cx, view.cy);
      return { el, name: el.dataset.city, x: p.x, y: p.y, sx, sy, visible: p.visible };
    });
    for (const q of pts) {
      q.el.setAttribute('cx', r0(q.x));
      q.el.setAttribute('cy', r0(q.y));
      if (q.visible) q.el.removeAttribute('display');
      else q.el.setAttribute('display', 'none');
    }
    const order = pts
      .map((q, i) => i)
      .filter((i) => pts[i].visible)
      .sort((a, bIdx) => {
        const da = (pts[a].sx - view.cx) ** 2 + (pts[a].sy - view.cy) ** 2;
        const db = (pts[bIdx].sx - view.cx) ** 2 + (pts[bIdx].sy - view.cy) ** 2;
        return da - db;
      });
    const boxes = [...reserved];
    const drawn = new Set();
    for (const i of order) {
      const q = pts[i];
      const w = CITY_EM_W * size * q.name.length;
      const h = CITY_EM_H * size;
      const rightHalf = q.sx >= view.cx;
      const x0 = rightHalf ? q.sx - CITY_GAP * size - w : q.sx + CITY_GAP * size;
      // Padded before comparing: two labels that merely abut both pass a bare
      // overlap test and read as one word. Mirrors CITY_PAD_EM in geo_frame.py.
      const pad = 0.35 * size;
      const box = [x0 - pad, q.sy - h / 2, x0 + w + pad, q.sy + h / 2];
      if (boxes.some((r) => box[0] < r[2] && r[0] < box[2]
                         && box[1] < r[3] && r[1] < box[3])) continue;
      boxes.push(box);
      drawn.add(i);
    }
    pts.forEach((q, i) => {
      const el = cityLabels.get(q.name);
      if (!el) return;
      const rightHalf = q.sx >= view.cx;
      const [ox, oy] = fromScreen((rightHalf ? -1 : 1) * CITY_GAP * size, 0);
      el.setAttribute('x', r0(q.x + ox));
      el.setAttribute('y', r0(q.y + oy + size * 0.34));
      el.setAttribute('transform', upright(q.x + ox, q.y + oy));
      el.setAttribute('text-anchor', rightHalf ? 'end' : 'start');
      el.setAttribute('font-size', Math.round(size));
      if (drawn.has(i)) el.removeAttribute('display');
      else el.setAttribute('display', 'none');
    });
  }

  function draw(view, state = {}) {
    const out = { marks: [], nodes: [], view };
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
    if (equator) {
      equator.setAttribute('d', pathData(projectRing(equatorRing, view), false));
    }
    if (tropics) {
      let d = '';
      for (const ring of tropicRings) d += `${pathData(projectRing(ring, view), false)} `;
      tropics.setAttribute('d', d.trim());
    }
    // .gl-night is deliberately NOT redrawn. The sun is fixed in screen space
    // — the Earth turns under it — so the subsolar longitude advances with
    // lon0 and the night polygon's projected shape is invariant. The frame the
    // emitter produced stays correct for every rotation, which is why this
    // runtime needs no solar maths and no second clip.
    if (land) {
      let d = '';
      for (const ring of landRings) d += `${pathData(projectArea(ring, view), true, view)} `;
      land.setAttribute('d', d.trim());
    }
    for (const el of blocEls) {
      let d = '';
      for (const ring of blocRings.get(el)) d += `${pathData(projectArea(ring, view), true, view)} `;
      el.setAttribute('d', d.trim());
    }
    if (linkEls.length) {
      drawLinks(view);
      placeSignals(view, state.codes);
    }
    const reserved = drawBlocLabels(view);
    if (cityDots.length) drawCities(view, reserved);
    // The region-drawing block lived here until 0.1.396. globe_svg.py has not
    // emitted a single [data-region] element since the split gave regions
    // their own component, so it selected nothing, projected nothing, and
    // shipped inline in every globe deliverable — along with ringsOfRegion and
    // the bbox index it fed.
    for (const el of markEls) {
      const lon = Number(el.dataset.lon);
      const lat = Number(el.dataset.lat);
      const p = project(lon, lat, view);
      el.setAttribute('cx', r0(p.x));
      el.setAttribute('cy', r0(p.y));
      // display, not `hidden`. The HTML `hidden` attribute does not hide an
      // SVG shape — a <circle hidden> computes display:inline and keeps its
      // box — so every far-side point stayed drawn and drifted across the
      // globe. Mirrors globe_svg.py.
      if (p.visible) el.removeAttribute('display');
      else el.setAttribute('display', 'none');
      if (p.visible) out.marks.push({ x: p.x, y: p.y, el, id: el.dataset.mark });
    }
    for (const el of nodeEls) {
      const lon = Number(el.dataset.lon);
      const lat = Number(el.dataset.lat);
      const p = project(lon, lat, view);
      el.setAttribute('cx', r0(p.x));
      el.setAttribute('cy', r0(p.y));
      if (p.visible) el.removeAttribute('display');
      else el.setAttribute('display', 'none');
      if (p.visible) out.nodes.push({ x: p.x, y: p.y, el, id: el.dataset.node });
    }
    return out;
  }

  // The signal clock. Exposed rather than run here: this module draws a frame
  // and owns no time, and globe.js already has the loop, the reduced-motion
  // gate and the off-screen gate that everything else on this figure obeys.
  function advanceSignals(dt, codes) {
    for (const s of sigEls) {
      const w = Number(s.path.dataset.w) || 0.5;
      s.t += (0.055 + 0.055 * w) * dt;
      if (s.t >= 1) {
        s.t -= 1;
        // Step by a stride coprime with nothing in particular — the point is
        // that a lane works through the whole list rather than looping a few.
        s.ci = (s.ci + 11) % Math.max(1, (codes || []).length || 1);
      }
    }
  }

  return { draw, destroy() {}, svg, advanceSignals, hasSignals: sigEls.length > 0 };
}

export {
  projectRing, projectArea, pathData, viewBoxFor,
};
