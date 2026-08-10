// Hit testing.
//
// The design called for inverse projection plus spherical point-in-polygon.
// Implementation found something both cheaper and more correct: test the
// SCREEN-SPACE runs the renderer just produced.
//
// It is more correct because it tests what is actually drawn. Those runs are
// already cut at the limb and already split at the antimeridian, so a hemisphere
// boundary and a seam-crossing country like Russia need no special case — and
// spherical point-in-polygon needs one for each. It is cheaper because the runs
// exist: the alternative projects the world a second time, or renders an ID
// buffer, which mid-drag is a second full pass per frame.
//
// invert() is still what the arcball needs, and controls.js uses it there.

// pickRegion and its even-odd crossing test lived here until 0.1.394.
// The region map does its hit testing with the browser's own pointer
// events on real path elements — a flat map needs no inverse projection —
// and the globe's targets are points, so the polygon test had no caller
// left and 30 lines of dead code in every deliverable is not a keepsake.

// A FLOOR, in the SVG's user units after scaling: 12 CSS px of radius, so a
// 24 px target, which is WCAG 2.2 SC 2.5.8. Passed in rather than assumed,
// because user units are not pixels and the figure's scale is the document's
// business, not this module's.
export const MARK_RADIUS_CSS_PX = 12;

/** Nearest mark within `radius` user units, or null. */
export function pickMark(x, y, frame, radius) {
  let best = null;
  let bestD = radius * radius;
  for (const m of frame.marks.concat(frame.nodes)) {
    const d = (m.x - x) ** 2 + (m.y - y) ** 2;
    if (d <= bestD) {
      bestD = d;
      best = m;
    }
  }
  return best;
}

/**
 * Convert a pointer event to the SVG's user-unit coordinate space, and undo
 * any transform the drawing sits under.
 *
 * The globe's layers live inside a group carrying the axial tilt and the
 * flattening, so a pointer lands in the TILTED frame while every coordinate
 * the renderer produced is in the projection's own. Without the inverse the
 * hit test is off by the tilt — worst at the limb, exactly where the marks a
 * reader aims at are smallest. getScreenCTM does the arithmetic the browser
 * already knows, so the transform can change without this changing.
 */
export function toUserSpace(svg, clientX, clientY) {
  const rect = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  if (!rect.width || !rect.height) return null;
  const layer = svg.querySelector('.gl-earth');
  if (layer && layer.getScreenCTM) {
    const ctm = layer.getScreenCTM();
    if (ctm) {
      const pt = svg.createSVGPoint();
      pt.x = clientX;
      pt.y = clientY;
      const local = pt.matrixTransform(ctm.inverse());
      const scale = Math.min(rect.width / vb.width, rect.height / vb.height);
      return { x: local.x, y: local.y, scale };
    }
  }
  // preserveAspectRatio defaults to xMidYMid meet, so the drawing is uniformly
  // scaled and centred. Reproducing that here is what keeps the hit test aligned
  // with what the reader sees in a cell that is not the figure's own aspect.
  const scale = Math.min(rect.width / vb.width, rect.height / vb.height);
  const offX = (rect.width - vb.width * scale) / 2;
  const offY = (rect.height - vb.height * scale) / 2;
  return {
    x: vb.x + (clientX - rect.left - offX) / scale,
    y: vb.y + (clientY - rect.top - offY) / scale,
    scale,
  };
}
