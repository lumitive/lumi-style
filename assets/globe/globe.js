// The globe component: a rotating field of marks on a sphere
// (specs/2026-08-10-globe-map-split-design.md).
//
//   import { createGlobe } from './globe.js';
//   const g = await createGlobe(container, { topology, registry });
//   container.addEventListener('markselect', e => …);
//
// The flat region map is its own component (assets/regionmap/). This one owns
// the frame loop, rotation, the mark field and its accessibility surface. The
// geometry the old one-figure design animated between sphere and plane is
// pinned to the sphere here: t=0, always. The shared projection core keeps the
// t parameter — the winding checks from 0.1.389 sweep it — but no product
// exposes it, and setForm / unroll / setT are gone rather than deprecated: a
// half-retired flag is a standing stale promise.
//
// The mark contract, and nothing about it is invented here:
//   marks: [{ lon, lat, weight, label?, id? }]      weight >= 0
// In the SVG back end the marks are BAKED into the frame by globe_svg.py
// (this runtime mutates markup and never creates it); the option exists for
// the canvas back end, which draws from data. When both are present the markup
// is the truth, because it is what a reader without JavaScript already saw.

import { decode } from '../geo/worlddata.js';
import { createSvgRenderer } from './render-svg.js';
import { pickMark, toUserSpace, MARK_RADIUS_CSS_PX } from '../geo/pick.js';
import { attachControls } from './controls.js';

const AUTOROTATE_DEG_PER_SEC = 6;
// A FLOOR on the SVG back end at the 1280x720 stage. Below it the watchdog pins
// the static frame rather than animating badly: a figure that stutters reads as
// broken, where a still one reads as a figure.
const MIN_FPS = 30;
const WATCHDOG_FRAMES = 45;

function reducedMotion() {
  return typeof matchMedia === 'function'
    && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** The marks as data, read back from the markup the emitter baked. */
function marksFromMarkup(svg) {
  return [...svg.querySelectorAll('.gl-mark')].map((el) => ({
    lon: Number(el.dataset.lon),
    lat: Number(el.dataset.lat),
    weight: Number(el.dataset.w || 1),
    id: el.dataset.mark || undefined,
    label: (el.querySelector('title') || {}).textContent || undefined,
  }));
}

export async function createGlobe(container, options = {}) {
  const {
    topologyUrl = null,
    regionsUrl = null,
    topology = null,
    registry = null,
    marks = null,
    autorotate = true,
    backend = 'svg',
  } = options;

  const svg = container.querySelector('svg.gl');
  if (!svg) {
    console.error('[lumi-globe] no <svg class="gl"> in the container; '
                  + 'generate one with scripts/globe_svg.py');
    return null;
  }

  let topo = topology;
  let reg = registry;
  try {
    if (!topo) topo = await (await fetch(topologyUrl)).json();
    if (!reg) reg = await (await fetch(regionsUrl)).json();
  } catch (err) {
    // The static frame stays exactly as generated. That is the whole reason the
    // renderer mutates markup instead of producing it.
    console.error('[lumi-globe] geometry could not be loaded; the static frame '
                  + 'is left in place', err);
    return null;
  }

  const data = decode(topo, reg);
  const markData = marks || marksFromMarkup(svg);

  let renderer;
  if (backend === 'canvas') {
    try {
      const mod = await import('./render-canvas.js');
      renderer = mod.createCanvasRenderer(container, data, { marks: markData });
    } catch (err) {
      console.warn('[lumi-globe] the canvas back end is unavailable; '
                   + 'falling back to SVG', err);
      renderer = null;
    }
  }
  if (!renderer) renderer = createSvgRenderer(svg, data);

  const reduced = reducedMotion();
  const view = {
    lon0: Number(svg.dataset.lon0 || 0),
    lat0: Number(svg.dataset.lat0 || 0),
    // Pinned. The globe is a sphere; the flat geometry belongs to the region
    // map component. The dataset value is ignored on purpose: a frame generated
    // by the retired one-figure emitter at some intermediate t must not make
    // this component animate a geometry it no longer owns.
    t: 0,
    R: Number(svg.dataset.r || 1000),
    cx: Number(svg.dataset.cx || 1000),
    cy: Number(svg.dataset.cy || 1000),
    zoom: 1,
  };
  let frame = null;
  let hoveredPoint = null;   // a mark id or a node id
  let raf = null;
  let slowFrames = 0;
  let pinned = false;

  function emit(name, detail) {
    container.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }));
  }

  function paint() {
    frame = renderer.draw(view, {});
  }

  // ── the accessibility layer ────────────────────────────────────────────────
  // The field's data, spoken: one visually-hidden entry per mark, name and
  // weight. Marks are not interactive targets the way the map's regions are —
  // a datum is read, not operated — so entries, not buttons. The registry's
  // NODES are targets (a place a reader selects), so they keep buttons. The
  // region-button list this component used to build lives in the region map
  // now; a field figure announced eleven regions it was not showing.
  const a11y = document.createElement('ul');
  a11y.className = 'gl-a11y';
  a11y.setAttribute('aria-label', 'Marks in this figure');
  a11y.style.cssText = 'position:absolute;width:1px;height:1px;margin:-1px;'
    + 'padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);'
    + 'white-space:nowrap;border:0;';
  for (const m of markData) {
    const li = document.createElement('li');
    li.textContent = m.label
      ? (m.label.includes(',') ? m.label : `${m.label}, ${m.weight}`)
      : `mark at ${m.lat}, ${m.lon}: ${m.weight}`;
    a11y.appendChild(li);
  }
  for (const node of reg.nodes || []) {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.node = node.id;
    btn.textContent = node.n;
    btn.addEventListener('focus', () => setPointHover(node.id));
    btn.addEventListener('blur', () => setPointHover(null));
    btn.addEventListener('click', () => emit('nodeselect', { node: node.id }));
    li.appendChild(btn);
    a11y.appendChild(li);
  }
  container.appendChild(a11y);

  function setPointHover(id) {
    if (id === hoveredPoint) return;
    if (hoveredPoint) emit('pointleave', { point: hoveredPoint });
    hoveredPoint = id;
    for (const el of svg.querySelectorAll('.gl-node, .gl-mark[data-mark]')) {
      el.classList.toggle('is-hover',
        (el.dataset.node || el.dataset.mark) === id);
    }
    if (id) emit('pointenter', { point: id });
  }

  // ── pointer ────────────────────────────────────────────────────────────────
  function onPointerMove(ev) {
    if (!frame || svg.classList.contains('is-dragging')) return;
    const u = toUserSpace(svg, ev.clientX, ev.clientY);
    if (!u) return;
    const hit = pickMark(u.x, u.y, frame, MARK_RADIUS_CSS_PX / u.scale);
    setPointHover(hit && hit.id ? hit.id : null);
  }
  function onClick(ev) {
    if (!frame) return;
    const u = toUserSpace(svg, ev.clientX, ev.clientY);
    if (!u) return;
    const hit = pickMark(u.x, u.y, frame, MARK_RADIUS_CSS_PX / u.scale);
    if (hit && hit.id) emit('nodeselect', { node: hit.id });
  }
  svg.addEventListener('pointermove', onPointerMove);
  svg.addEventListener('click', onClick);
  svg.setAttribute('tabindex', '0');

  const controls = attachControls(svg, {
    getView: () => view,
    setView: (v) => { Object.assign(view, v, { t: 0 }); paint(); },
    reducedMotion: reduced,
  });

  // ── the loop ───────────────────────────────────────────────────────────────
  let last = performance.now();
  function tick(now) {
    const dt = Math.min(100, now - last);
    last = now;
    if (autorotate && !reduced && !controls.flinging
        && !svg.classList.contains('is-dragging')) {
      view.lon0 += (AUTOROTATE_DEG_PER_SEC * dt) / 1000;
      const t0 = performance.now();
      paint();
      const cost = performance.now() - t0;
      // The watchdog is a floor with teeth. A figure that stutters reads as
      // broken; a still one reads as a figure, so it stops rather than limps.
      if (cost > 1000 / MIN_FPS) slowFrames += 1;
      else slowFrames = Math.max(0, slowFrames - 1);
      if (slowFrames > WATCHDOG_FRAMES && !pinned) {
        pinned = true;
        console.warn('[lumi-globe] the frame budget was missed for '
                     + `${WATCHDOG_FRAMES} frames; pinning the static frame`);
        emit('pinned', { reason: 'frame-budget' });
        return;
      }
    }
    raf = requestAnimationFrame(tick);
  }

  function start() {
    if (raf === null && !pinned) {
      last = performance.now();
      raf = requestAnimationFrame(tick);
    }
  }
  function stop() {
    if (raf !== null) cancelAnimationFrame(raf);
    raf = null;
  }

  const io = typeof IntersectionObserver === 'function'
    ? new IntersectionObserver((es) => (es[0].isIntersecting ? start() : stop()),
      { threshold: 0 })
    : null;
  if (io) io.observe(container); else start();

  const onVisibility = () => (document.hidden ? stop() : start());
  document.addEventListener('visibilitychange', onVisibility);

  paint();

  return {
    get view() { return { ...view }; },
    // The projected runs of the last frame. A host doing its own hit
    // testing needs them, and so does anything verifying this component.
    get frame() { return frame; },
    get marks() { return markData.slice(); },
    destroy() {
      stop();
      controls.destroy();
      io?.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      svg.removeEventListener('pointermove', onPointerMove);
      svg.removeEventListener('click', onClick);
      a11y.remove();
      renderer.destroy();
    },
  };
}
