// The site back end: immediate-mode Canvas 2D, behind the same interface as the
// SVG renderer so globe.js selects between them without branching anywhere else.
//
// Use this only where no gate applies. A canvas is invisible to every check this
// package owns — d5_drawn_share counts a figure as drawn only if it holds an
// <svg>, d17_export_weight reads path markup, inspect_layout cannot see inside —
// so a deliverable uses render-svg.js and a product page can use this.
//
// Colour still comes from tokens. getComputedStyle on the host element resolves
// the same custom properties the stylesheet gives the SVG, so the two back ends
// paint the same figure and neither has a hex in it.

import { project, splitAtSeam } from './projection.js';
import { ringsOf, ringsOfRegion } from './worlddata.js';

const STEP_DEG = 2;

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

export function createCanvasRenderer(container, data, options = {}) {
  const svg = container.querySelector('svg.gl');
  let canvas = container.querySelector('canvas.gl-canvas');
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.className = 'gl-canvas';
    container.insertBefore(canvas, svg || null);
  }
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D is unavailable');
  // The SVG is replaced, not augmented: hidden as well as aria-hidden, because
  // aria-hidden alone leaves it on the page and the first canvas render drew a
  // globe with a second globe underneath it. Reversed in destroy(), and the
  // fallback path never gets here.
  if (svg) {
    svg.setAttribute('aria-hidden', 'true');
    svg.hidden = true;
  }

  // Geometry is resolved once. Only the projection runs per frame, and it writes
  // into these buffers rather than allocating: a full world is about 15,000
  // points and a fresh pair of arrays per frame is what makes a canvas globe
  // stutter every few seconds under the collector rather than steadily.
  const regionRings = new Map();
  for (const r of data.regions) regionRings.set(r.id, ringsOfRegion(r.id, data));
  const landRings = [...data.countries.keys()].flatMap((c) => ringsOf(c, data));
  const graticule = [];
  for (let lon = -180; lon <= 180; lon += 30) {
    const r = [];
    for (let lat = -90; lat <= 90; lat += 3) r.push([lon, lat]);
    graticule.push(r);
  }
  for (let lat = -90; lat <= 90; lat += 30) {
    const r = [];
    for (let lon = -180; lon <= 180; lon += 3) r.push([lon, lat]);
    graticule.push(r);
  }
  const dense = new Map();
  const denseOf = (ring) => {
    let d = dense.get(ring);
    if (!d) { d = densify(ring, STEP_DEG); dense.set(ring, d); }
    return d;
  };

  const buf = { xy: new Float32Array(4096), n: 0 };
  function ensure(n) {
    if (buf.xy.length < n * 2) buf.xy = new Float32Array(n * 2);
  }

  const styleHost = svg || container;
  let palette = new Map();
  function readPalette() {
    const cs = getComputedStyle(styleHost);
    palette = new Map();
    for (const r of data.regions) {
      palette.set(r.id, {
        fill: cs.getPropertyValue(`--rg-${r.id}`).trim() || 'transparent',
        stroke: cs.getPropertyValue(`--rg-${r.id}-stroke`).trim() || 'transparent',
        wash: cs.getPropertyValue(`--rg-${r.id}-wash`).trim() || 'transparent',
      });
    }
    palette.set('__base', {
      plate: cs.getPropertyValue('--gl-plate').trim() || 'transparent',
      graticule: cs.getPropertyValue('--gl-graticule').trim() || 'transparent',
      land: cs.getPropertyValue('--gl-land').trim() || 'transparent',
      landEdge: cs.getPropertyValue('--gl-land-edge').trim() || 'transparent',
      mark: cs.getPropertyValue('--acc').trim() || 'transparent',
      out: cs.getPropertyValue('--brass').trim() || 'transparent',
      partial: cs.getPropertyValue('--amber').trim() || 'transparent',
    });
  }
  readPalette();

  function tracePart(part, view, scale, ox, oy) {
    const pts = denseOf(part);
    ensure(pts.length);
    let n = 0;
    const runs = [];
    let start = 0;
    for (let i = 0; i < pts.length; i += 1) {
      const p = project(pts[i][0], pts[i][1], view);
      if (p.visible) {
        buf.xy[n * 2] = (p.x - ox) * scale;
        buf.xy[n * 2 + 1] = (p.y - oy) * scale;
        n += 1;
      } else if (n - start > 1) {
        runs.push([start, n]);
        start = n;
      } else {
        n = start;
      }
    }
    if (n - start > 1) runs.push([start, n]);
    buf.n = n;
    return runs;
  }

  function strokeOrFill(ring, view, scale, ox, oy, close) {
    for (const part of splitAtSeam(ring, view.lon0)) {
      if (part.length < 2) continue;
      const runs = tracePart(part, view, scale, ox, oy);
      for (const [a, b] of runs) {
        ctx.moveTo(buf.xy[a * 2], buf.xy[a * 2 + 1]);
        for (let i = a + 1; i < b; i += 1) {
          ctx.lineTo(buf.xy[i * 2], buf.xy[i * 2 + 1]);
        }
        if (close) ctx.closePath();
      }
    }
  }

  function draw(view, state = {}) {
    const rect = container.getBoundingClientRect();
    const dpr = Math.min(3, window.devicePixelRatio || 1);
    const halfW = view.R / view.zoom;
    const halfH = (view.R * (1 - view.t / 2)) / view.zoom;
    const w = Math.max(1, Math.round(rect.width));
    const h = Math.max(1, Math.round((rect.width * halfH) / halfW));
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
    }
    const scale = (w * dpr) / (2 * halfW);
    const ox = view.cx - halfW;
    const oy = view.cy - halfH;
    const base = palette.get('__base');

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (view.t < 1) {
      ctx.globalAlpha = 1 - view.t;
      ctx.fillStyle = base.plate;
      ctx.beginPath();
      ctx.arc((view.cx - ox) * scale, (view.cy - oy) * scale, view.R * scale,
        0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    ctx.lineWidth = Math.max(1, dpr);
    ctx.strokeStyle = base.graticule;
    ctx.beginPath();
    for (const ring of graticule) strokeOrFill(ring, view, scale, ox, oy, false);
    ctx.stroke();

    const showRegions = state.form === 'regions' || view.t > 0.5;
    if (showRegions) {
      for (const r of data.regions) {
        const entry = (state.regions && state.regions[r.id]) || {};
        const s = entry.state || 'zero';
        const tone = palette.get(r.id);
        ctx.beginPath();
        for (const ring of regionRings.get(r.id) || []) {
          strokeOrFill(ring, view, scale, ox, oy, true);
        }
        ctx.fillStyle = s === 'out' ? base.out
          : (s === 'zero' ? tone.wash : tone.fill);
        ctx.fill('evenodd');
        ctx.strokeStyle = s === 'partial' ? base.partial : tone.stroke;
        ctx.setLineDash(s === 'zero' ? [6 * dpr, 4 * dpr] : []);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    } else {
      ctx.beginPath();
      for (const ring of landRings) strokeOrFill(ring, view, scale, ox, oy, true);
      ctx.fillStyle = base.land;
      ctx.fill('evenodd');
      ctx.strokeStyle = base.landEdge;
      ctx.stroke();
    }

    // The frame object is the same shape the SVG renderer returns, so pick.js
    // works against either without knowing which drew.
    const out = { regions: new Map(), marks: [], nodes: [], view, backend: 'canvas' };
    for (const r of data.regions) {
      const runs = [];
      for (const ring of regionRings.get(r.id) || []) {
        for (const part of splitAtSeam(ring, view.lon0)) {
          if (part.length < 2) continue;
          const pts = denseOf(part);
          let cur = [];
          for (const [lon, lat] of pts) {
            const p = project(lon, lat, view);
            if (p.visible) cur.push([p.x, p.y]);
            else { if (cur.length > 1) runs.push(cur); cur = []; }
          }
          if (cur.length > 1) runs.push(cur);
        }
      }
      out.regions.set(r.id, runs);
    }
    ctx.fillStyle = base.mark;
    for (const node of data.nodes) {
      const p = project(node.lon, node.lat, view);
      if (!p.visible) continue;
      ctx.beginPath();
      ctx.arc((p.x - ox) * scale, (p.y - oy) * scale, view.R * 0.017 * scale,
        0, Math.PI * 2);
      ctx.fill();
      out.nodes.push({ x: p.x, y: p.y, id: node.id });
    }
    return out;
  }

  return {
    draw,
    readPalette,
    canvas,
    destroy() {
      canvas.remove();
      if (svg) {
        svg.removeAttribute('aria-hidden');
        svg.hidden = false;
      }
    },
  };
}
