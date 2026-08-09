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

/** Even-odd crossing test on one screen-space polyline treated as closed. */
function inRun(x, y, run) {
  let inside = false;
  for (let i = 0, j = run.length - 1; i < run.length; j = i, i += 1) {
    const [xi, yi] = run[i];
    const [xj, yj] = run[j];
    if ((yi > y) !== (yj > y)
        && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

/**
 * Which region is under (x, y) in the SVG's own user units.
 *
 * A country's outer ring and its holes both arrive as runs of the same region,
 * so crossings are counted across all of them and the parity answers the
 * question — a point inside a hole lands outside the region, which is right.
 *
 * @param frame the object createSvgRenderer.draw() returned
 */
export function pickRegion(x, y, frame) {
  for (const [id, runs] of frame.regions) {
    let inside = false;
    for (const run of runs) {
      if (run.length > 2 && inRun(x, y, run)) inside = !inside;
    }
    if (inside) return id;
  }
  return null;
}

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

/** Convert a pointer event to the SVG's user-unit coordinate space. */
export function toUserSpace(svg, clientX, clientY) {
  const rect = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  if (!rect.width || !rect.height) return null;
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
