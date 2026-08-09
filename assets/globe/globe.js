// The public component.
//
// Owns the state machine (form, unroll t, auto-rotation), the frame loop, the
// accessibility layer, and the failure behaviour. It selects a back end but
// contains no drawing of its own.
//
//   import { createGlobe } from './globe.js';
//   const g = await createGlobe(container, { hostData });
//   g.setForm('regions');           // unrolls to the flat map
//   container.addEventListener('regionselect', e => …);
//
// Host data, and nothing about it is invented here:
//   { regions: { <id>: { value, state } },
//     marks:   [ { lon, lat, weight } ],
//     nodes:   [ { id, value, state } ] }
// state is live | partial | zero | out. A region absent from the object renders
// as zero, because no data is not coverage.

import { decode } from './worlddata.js';
import { createSvgRenderer } from './render-svg.js';
import { pickRegion, pickMark, toUserSpace, MARK_RADIUS_CSS_PX } from './pick.js';
import { attachControls } from './controls.js';

const AUTOROTATE_DEG_PER_SEC = 6;
// The unroll is a FIXED duration, not an exponential ease toward the target.
// An asymptote never arrives: at a 450ms time constant and a 0.001 threshold the
// figure was still visibly settling three seconds after the switch, which reads
// as the page being slow and makes anything measured during it wrong. 700ms with
// a symmetric ease arrives, and arrives exactly.
const UNROLL_MS = 700;
const easeInOut = (u) => (u < 0.5 ? 4 * u * u * u : 1 - ((-2 * u + 2) ** 3) / 2);
// A FLOOR on the SVG back end at the 1280x720 stage. Below it the watchdog pins
// the static frame rather than animating badly: a figure that stutters reads as
// broken, where a still one reads as a figure.
const MIN_FPS = 30;
const WATCHDOG_FRAMES = 45;

function reducedMotion() {
  return typeof matchMedia === 'function'
    && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** Read the region tokens off the document once, and again when the theme flips. */
function readTokens(el, ids) {
  const cs = getComputedStyle(el);
  const out = new Map();
  for (const id of ids) {
    out.set(id, {
      fill: cs.getPropertyValue(`--rg-${id}`).trim(),
      stroke: cs.getPropertyValue(`--rg-${id}-stroke`).trim(),
      wash: cs.getPropertyValue(`--rg-${id}-wash`).trim(),
    });
  }
  return out;
}

export async function createGlobe(container, options = {}) {
  const {
    topologyUrl = null,
    regionsUrl = null,
    topology = null,
    registry = null,
    hostData = {},
    form = 'field',
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
  const known = new Set(data.regionMembers.keys());
  for (const id of Object.keys(hostData.regions || {})) {
    if (!known.has(id)) {
      console.warn(`[lumi-globe] host data names region "${id}", which is not in `
                   + 'the registry; it is ignored for rendering');
    }
  }

  let renderer;
  if (backend === 'canvas') {
    try {
      const mod = await import('./render-canvas.js');
      renderer = mod.createCanvasRenderer(container, data);
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
    t: form === 'regions' ? 1 : Number(svg.dataset.t || 0),
    R: Number(svg.dataset.r || 1000),
    cx: Number(svg.dataset.cx || 1000),
    cy: Number(svg.dataset.cy || 1000),
    zoom: 1,
  };
  let currentForm = form;
  let targetT = view.t;
  let unroll = null;   // {from, to, start} while a form change is in flight
  let frame = null;
  let hovered = null;
  let hoveredNode = null;
  let raf = null;
  let slowFrames = 0;
  let pinned = false;
  let tokens = readTokens(svg, known);

  const state = { regions: hostData.regions || {} };

  function emit(name, detail) {
    container.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }));
  }

  function paint() {
    frame = renderer.draw(view, state);
  }

  // ── the accessibility layer ────────────────────────────────────────────────
  // A canvas is empty to a screen reader and an SVG path is nearly so, and the
  // two back ends must be equivalent. So one real button per region, visually
  // hidden, carrying the name and the value, driving the same state machine the
  // pointer drives.
  const a11y = document.createElement('ul');
  a11y.className = 'gl-a11y';
  a11y.setAttribute('aria-label', 'Regions in this figure');
  for (const region of data.regions) {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.region = region.id;
    const entry = state.regions[region.id];
    btn.textContent = entry && entry.value !== undefined
      ? `${region.n}: ${entry.value}`
      : `${region.n}: no data`;
    btn.addEventListener('focus', () => setHover(region.id));
    btn.addEventListener('blur', () => setHover(null));
    btn.addEventListener('click', () => emit('regionselect', { region: region.id }));
    li.appendChild(btn);
    a11y.appendChild(li);
  }
  container.appendChild(a11y);

  function setHover(id) {
    if (id === hovered) return;
    if (hovered) emit('regionleave', { region: hovered });
    hovered = id;
    for (const el of svg.querySelectorAll('[data-region]')) {
      el.classList.toggle('is-hover', el.getAttribute('data-region') === id);
    }
    if (id) emit('regionenter', { region: id });
  }

  function setNodeHover(id) {
    if (id === hoveredNode) return;
    if (hoveredNode) emit('nodeleave', { node: hoveredNode });
    hoveredNode = id;
    for (const el of svg.querySelectorAll('.gl-node')) {
      el.classList.toggle('is-hover', el.dataset.node === id);
    }
    if (id) emit('nodeenter', { node: id });
  }

  // ── pointer ────────────────────────────────────────────────────────────────
  function onPointerMove(ev) {
    if (!frame || svg.classList.contains('is-dragging')) return;
    const u = toUserSpace(svg, ev.clientX, ev.clientY);
    if (!u) return;
    // A node wins over the region beneath it, because it is the smaller and more
    // specific target and the reader aimed at it. It must SAY so, though: an
    // earlier version merely cleared the region highlight, so hovering within
    // 12px of Bahrain looked like hovering over nothing at all.
    const mark = pickMark(u.x, u.y, frame, MARK_RADIUS_CSS_PX / u.scale);
    setNodeHover(mark && mark.id ? mark.id : null);
    setHover(mark ? null : pickRegion(u.x, u.y, frame));
  }
  function onClick(ev) {
    if (!frame) return;
    const u = toUserSpace(svg, ev.clientX, ev.clientY);
    if (!u) return;
    const mark = pickMark(u.x, u.y, frame, MARK_RADIUS_CSS_PX / u.scale);
    if (mark && mark.id) emit('nodeselect', { node: mark.id });
    else {
      const id = pickRegion(u.x, u.y, frame);
      if (id) emit('regionselect', { region: id });
    }
  }
  svg.addEventListener('pointermove', onPointerMove);
  svg.addEventListener('click', onClick);
  svg.setAttribute('tabindex', '0');

  const controls = attachControls(svg, {
    getView: () => view,
    setView: (v) => { Object.assign(view, v); paint(); },
    reducedMotion: reduced,
  });

  // ── the loop ───────────────────────────────────────────────────────────────
  let last = performance.now();
  function tick(now) {
    const dt = Math.min(100, now - last);
    last = now;
    let moved = false;

    if (unroll) {
      const u = Math.min(1, (now - unroll.start) / UNROLL_MS);
      view.t = unroll.from + (unroll.to - unroll.from) * easeInOut(u);
      if (u >= 1) {
        view.t = unroll.to;
        unroll = null;
        emit('unrollend', { t: view.t, form: currentForm });
      }
      moved = true;
    }
    if (autorotate && !reduced && !controls.flinging
        && !svg.classList.contains('is-dragging') && currentForm === 'field') {
      view.lon0 += (AUTOROTATE_DEG_PER_SEC * dt) / 1000;
      moved = true;
    }

    if (moved) {
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

  const themeQuery = typeof matchMedia === 'function'
    ? matchMedia('(prefers-color-scheme: dark)') : null;
  const onTheme = () => { tokens = readTokens(svg, known); paint(); };
  themeQuery?.addEventListener?.('change', onTheme);

  paint();

  return {
    get view() { return { ...view }; },
    // The projected runs of the last frame. A host doing its own hit
    // testing needs them, and so does anything verifying this component.
    get frame() { return frame; },
    get tokens() { return tokens; },
    setForm(next) {
      if (next === currentForm) return;
      currentForm = next;
      targetT = next === 'regions' ? 1 : 0;
      if (reduced) {
        // No unroll under reduced motion: the form change cuts.
        view.t = targetT;
        unroll = null;
        paint();
      } else {
        unroll = { from: view.t, to: targetT, start: performance.now() };
      }
      emit('formchange', { form: next });
      start();
    },
    setT(value) {
      targetT = Math.max(0, Math.min(1, value));
      view.t = targetT;
      unroll = null;
      paint();
    },
    get settled() { return unroll === null; },
    setData(next) {
      state.regions = next.regions || {};
      paint();
    },
    destroy() {
      stop();
      controls.destroy();
      io?.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      themeQuery?.removeEventListener?.('change', onTheme);
      svg.removeEventListener('pointermove', onPointerMove);
      svg.removeEventListener('click', onClick);
      a11y.remove();
      renderer.destroy();
    },
  };
}
