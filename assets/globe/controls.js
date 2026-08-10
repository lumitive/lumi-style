// Arcball drag, wheel zoom, keyboard.
//
// Drag is an arcball, not pixels mapped to longitude. Mapping horizontal pixels
// to degrees stops tracking the pointer as soon as the grab is away from the
// equator — the globe slides out from under the cursor, and near the pole it
// barely moves at all. Inverting both the grab point and the current point to
// sphere vectors and applying the rotation between them keeps the point under
// the cursor under the cursor, which is the only behaviour that reads as
// picking the object up.

import { invert } from '../geo/projection.js';
import { toUserSpace } from '../geo/pick.js';

const D2R = Math.PI / 180;
const R2D = 180 / Math.PI;

// A CEILING. Longer than this and the release reads as the component ignoring
// it rather than as momentum.
const REST_SECONDS = 0.9;
const DECAY = Math.exp(Math.log(0.02) / (REST_SECONDS * 60));   // per frame at 60fps
const MIN_SPIN = 0.02;   // degrees per frame; below this, stop
// A CEILING on the fling, in degrees per frame. Without it a fast drag over a
// couple of milliseconds divides by a tiny dt and launches the globe: a 120px
// drag measured 39 degrees of coast, which reads as the thing having been
// thrown rather than released.
const MAX_SPIN = 3.0;

function toVec(lon, lat) {
  const p = lat * D2R;
  const l = lon * D2R;
  return [Math.cos(p) * Math.cos(l), Math.cos(p) * Math.sin(l), Math.sin(p)];
}

/**
 * @param {Element} el       the element that receives pointer events
 * @param {object} opts
 *   getView()   -> the current view
 *   setView(v)  -> apply a new view
 *   onIdle()    -> called when a fling comes to rest
 *   reducedMotion -> boolean; no inertia when true
 */
export function attachControls(el, opts) {
  const { getView, setView, onIdle = () => {}, reducedMotion = false } = opts;
  let dragging = null;
  let spin = 0;
  let spinLat = 0;
  let raf = null;

  function pointFor(ev) {
    const view = getView();
    const u = toUserSpace(el, ev.clientX, ev.clientY);
    if (!u) return null;
    const geo = invert(u.x, u.y, view);
    return geo ? { geo, u } : { geo: null, u };
  }

  function onDown(ev) {
    const p = pointFor(ev);
    if (!p) return;
    spin = 0;
    spinLat = 0;
    dragging = { start: p, view: { ...getView() }, last: performance.now() };
    el.setPointerCapture?.(ev.pointerId);
    el.classList.add('is-dragging');
  }

  function onMove(ev) {
    if (!dragging) return;
    const view = getView();
    const u = toUserSpace(el, ev.clientX, ev.clientY);
    if (!u) return;
    const from = dragging.start.geo;
    if (!from) return;
    const to = invert(u.x, u.y, { ...view, lon0: dragging.view.lon0,
      lat0: dragging.view.lat0 });
    if (!to) return;
    // `to` is the place currently under the cursor, read in the view as it was
    // when the drag began. To put `from` there instead, the centre moves by the
    // difference — MINUS (to - from), on both axes. Getting the longitude sign
    // backwards here is not subtle in the numbers and is very subtle on screen:
    // the globe still turns when you drag, just the wrong way and at twice the
    // rate, which reads as sensitivity rather than as a defect. Measured: a
    // 150px drag left the grabbed point 64.7 degrees from the cursor.
    //
    // Two Euler steps rather than a quaternion, because the view carries only
    // lon0/lat0 and a third degree of freedom it cannot store would be
    // discarded silently every frame.
    const lon0 = dragging.view.lon0 - (to.lon - from.lon);
    const lat0 = Math.max(-89, Math.min(89,
      dragging.view.lat0 - (to.lat - from.lat)));
    const now = performance.now();
    const dt = Math.max(1, now - dragging.last);
    const clamp = (v) => Math.max(-MAX_SPIN, Math.min(MAX_SPIN, v));
    spin = clamp(((lon0 - view.lon0) / dt) * 16.7);
    spinLat = clamp(((lat0 - view.lat0) / dt) * 16.7);
    dragging.last = now;
    setView({ ...view, lon0, lat0 });
  }

  function fling() {
    if (Math.abs(spin) < MIN_SPIN && Math.abs(spinLat) < MIN_SPIN) {
      raf = null;
      spin = 0;
      spinLat = 0;
      onIdle();
      return;
    }
    const view = getView();
    setView({
      ...view,
      lon0: view.lon0 + spin,
      lat0: Math.max(-89, Math.min(89, view.lat0 + spinLat)),
    });
    spin *= DECAY;
    spinLat *= DECAY;
    raf = requestAnimationFrame(fling);
  }

  function onUp(ev) {
    if (!dragging) return;
    dragging = null;
    el.releasePointerCapture?.(ev.pointerId);
    el.classList.remove('is-dragging');
    if (reducedMotion) {
      spin = 0;
      spinLat = 0;
      onIdle();
      return;
    }
    if (raf === null) raf = requestAnimationFrame(fling);
  }

  function onWheel(ev) {
    ev.preventDefault();
    const view = getView();
    const next = Math.max(0.6, Math.min(3, view.zoom * (ev.deltaY > 0 ? 0.92 : 1.087)));
    setView({ ...view, zoom: next });
  }

  function onKey(ev) {
    const view = getView();
    const step = ev.shiftKey ? 15 : 5;
    let handled = true;
    switch (ev.key) {
      case 'ArrowLeft': setView({ ...view, lon0: view.lon0 - step }); break;
      case 'ArrowRight': setView({ ...view, lon0: view.lon0 + step }); break;
      case 'ArrowUp':
        setView({ ...view, lat0: Math.min(89, view.lat0 + step) }); break;
      case 'ArrowDown':
        setView({ ...view, lat0: Math.max(-89, view.lat0 - step) }); break;
      case '+': case '=':
        setView({ ...view, zoom: Math.min(3, view.zoom * 1.15) }); break;
      case '-': case '_':
        setView({ ...view, zoom: Math.max(0.6, view.zoom / 1.15) }); break;
      default: handled = false;
    }
    if (handled) ev.preventDefault();
  }

  el.addEventListener('pointerdown', onDown);
  el.addEventListener('pointermove', onMove);
  el.addEventListener('pointerup', onUp);
  el.addEventListener('pointercancel', onUp);
  el.addEventListener('wheel', onWheel, { passive: false });
  el.addEventListener('keydown', onKey);

  return {
    get flinging() { return raf !== null; },
    destroy() {
      if (raf !== null) cancelAnimationFrame(raf);
      el.removeEventListener('pointerdown', onDown);
      el.removeEventListener('pointermove', onMove);
      el.removeEventListener('pointerup', onUp);
      el.removeEventListener('pointercancel', onUp);
      el.removeEventListener('wheel', onWheel);
      el.removeEventListener('keydown', onKey);
    },
  };
}

export { REST_SECONDS };
