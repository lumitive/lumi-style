// The region map component. The flat half of the split
// (specs/2026-08-10-globe-map-split-design.md).
//
//   import { createRegionMap } from './regionmap.js';
//   const m = createRegionMap(container, { registry, hostData });
//   m.setData({ regions: { europe: { state: 'live', value: 71 } } });
//   container.addEventListener('regionselect', e => …);
//
// This runtime touches NO GEOMETRY. The static frame scripts/regionmap_svg.py
// emits is complete — a flat map does not rotate, unroll or animate — so what
// is left for a runtime is state: classes, values, labels, hover, focus and
// the accessibility layer. That is also why creation is synchronous and needs
// no topology: the 68 KB of world geometry the globe must carry to re-project
// every frame is already baked into this component's markup, and hit testing
// is the browser's own pointer events on real <path> elements rather than an
// inverse projection.
//
// hostData, and nothing about it is invented here:
//   { regions: { <id>: { value, state } } }
// state is live | partial | zero | out. A region absent from the object renders
// as zero, because no data is not coverage.

/** aria text: name and VALUE — what a sighted reader takes from the colour and
 *  the label together. State only when there is no value to speak. */
function ariaFor(name, entry) {
  if (entry && entry.value !== undefined && entry.value !== null) {
    return `${name}, ${entry.value}`;
  }
  return `${name}, ${entry && entry.state ? entry.state : 'zero'}`;
}

export function createRegionMap(container, options = {}) {
  const {
    registry = null,
    hostData = {},
    interactive = true,
  } = options;

  const svg = container.querySelector('svg.regionmap');
  if (!svg) {
    console.error('[lumi-regionmap] no <svg class="regionmap"> in the container; '
                  + 'generate one with scripts/regionmap_svg.py');
    return null;
  }
  if (!registry) {
    console.error('[lumi-regionmap] no registry given; region names are in it '
                  + 'and the component will not guess them');
    return null;
  }

  const names = new Map(registry.regions.map((r) => [r.id, r.n]));
  const counts = new Map(registry.regions.map((r) => [r.id, r.count]));
  const paths = new Map();
  for (const el of svg.querySelectorAll('[data-region]')) {
    paths.set(el.getAttribute('data-region'), el);
  }
  const labelEls = new Map();
  for (const el of svg.querySelectorAll('[data-region-label]')) {
    labelEls.set(el.getAttribute('data-region-label'), el);
  }
  // The full-membership outlines, one per bloc that overlaps another. Present
  // only when the registry carries overlapping membership, so a map of
  // disjoint regions has none and nothing below does any work.
  const overlays = new Map();
  for (const el of svg.querySelectorAll('[data-overlay]')) {
    overlays.set(el.getAttribute('data-overlay'), el);
  }
  let selected = null;

  // Initial state comes FROM THE MARKUP, host data only overrides it. The
  // frame bakes states in (`is-live`, an aria value), and a host that embeds
  // the runtime without data must not have the runtime "correct" the figure to
  // all-zero — which is exactly what the first cut did to its own test page
  // within minutes of existing. No data given is not data.
  function readInitial() {
    const out = {};
    for (const [id, el] of paths) {
      const cls = [...el.classList].find((c) => c.startsWith('is-') && c !== 'is-hover');
      const m = /,\s*([0-9][\d.,]*)\s*$/.exec(el.getAttribute('aria-label') || '');
      out[id] = { state: cls ? cls.slice(3) : 'zero',
                  value: m ? Number(m[1].replace(/,/g, '')) : undefined };
    }
    return out;
  }
  const given = hostData && hostData.regions
    && Object.keys(hostData.regions).length > 0;
  const state = { regions: given ? hostData.regions : readInitial() };
  for (const id of Object.keys(state.regions)) {
    if (!names.has(id)) {
      console.warn(`[lumi-regionmap] host data names region "${id}", which is `
                   + 'not in the registry; it is ignored');
    }
  }

  let hovered = null;
  function emit(name, detail) {
    container.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }));
  }

  function apply() {
    for (const [id, el] of paths) {
      const entry = state.regions[id];
      const s = (entry && entry.state) || 'zero';
      for (const c of [...el.classList]) {
        if (c.startsWith('is-') && c !== 'is-hover') el.classList.remove(c);
      }
      el.classList.add(`is-${s}`);
      // The aria-label moves with the data. The globe's first frame wrote it
      // once at generation time and never again, so a screen reader heard the
      // shipped value after the host had moved on.
      el.setAttribute('aria-label', ariaFor(names.get(id) || id, entry));
      const label = labelEls.get(id);
      if (label) {
        let v = label.querySelector('.rg-label-v');
        if (entry && entry.value !== undefined && entry.value !== null) {
          if (!v) {
            v = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            v.setAttribute('class', 'rg-label-v');
            label.appendChild(v);
          }
          v.textContent = ` ${entry.value}`;
        } else if (v) {
          v.remove();
        }
      }
    }
  }

  // ── the accessibility layer ────────────────────────────────────────────────
  // One real button per region, visually hidden, carrying name and value. It
  // lives in THIS component and not the globe: the globe's paths are marks and
  // land, the map's are regions, and the first build attached region buttons to
  // both — a field figure announced eleven regions it was not showing. Hidden
  // by the component, never by the host.
  const a11y = document.createElement('ul');
  a11y.className = 'gl-a11y';
  a11y.setAttribute('aria-label', 'Regions in this map');
  a11y.style.cssText = 'position:absolute;width:1px;height:1px;margin:-1px;'
    + 'padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);'
    + 'white-space:nowrap;border:0;';
  const buttons = new Map();
  for (const region of registry.regions) {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.region = region.id;
    btn.addEventListener('focus', () => setHover(region.id));
    btn.addEventListener('blur', () => setHover(null));
    btn.addEventListener('click', () => {
      const now = setSelected(region.id);
      emit('regionselect', {
        region: region.id, selected: now === region.id, count: counts.get(region.id),
      });
    });
    li.appendChild(btn);
    a11y.appendChild(li);
    buttons.set(region.id, btn);
  }
  function syncButtons() {
    for (const [id, btn] of buttons) {
      btn.textContent = ariaFor(names.get(id) || id, state.regions[id]);
    }
  }
  container.appendChild(a11y);

  // Selecting a bloc shows its WHOLE membership, including the countries whose
  // base fill belongs to another bloc. Without this a map of overlapping blocs
  // can state ASEAN and RCEP but never CPTPP, because no country is filled
  // CPTPP that is not also in a smaller bloc.
  function setSelected(id) {
    selected = selected === id ? null : id;
    for (const [oid, el] of overlays) {
      if (oid === selected) el.removeAttribute('display');
      else el.setAttribute('display', 'none');
    }
    for (const [rid, el] of paths) el.classList.toggle('is-selected', rid === selected);
    return selected;
  }

  function setHover(id) {
    if (id === hovered) return;
    if (hovered) emit('regionleave', { region: hovered });
    hovered = id;
    for (const [rid, el] of paths) el.classList.toggle('is-hover', rid === id);
    if (id) emit('regionenter', { region: id });
  }

  // ── pointer, by delegation ─────────────────────────────────────────────────
  // Real elements take real events; nothing here inverts a projection.
  function regionOf(ev) {
    const el = ev.target.closest && ev.target.closest('[data-region]');
    return el ? el.getAttribute('data-region') : null;
  }
  const onOver = (ev) => setHover(regionOf(ev));
  const onLeave = () => setHover(null);
  const onClick = (ev) => {
    const id = regionOf(ev);
    if (!id) return;
    // The detail carries what a host needs to open a panel without going back
    // to the registry: the id, whether this click selected or cleared, and the
    // membership count the label is already showing.
    const now = setSelected(id);
    emit('regionselect', {
      region: id,
      selected: now === id,
      count: counts.get(id),
    });
  };
  if (interactive) {
    svg.addEventListener('pointerover', onOver);
    svg.addEventListener('pointerleave', onLeave);
    svg.addEventListener('click', onClick);
    svg.setAttribute('tabindex', '0');
  }

  apply();
  syncButtons();

  return {
    get state() { return state; },
    get selected() { return selected; },
    select(id) { return setSelected(id); },
    setData(next) {
      state.regions = (next && next.regions) || {};
      apply();
      syncButtons();
    },
    destroy() {
      if (interactive) {
        svg.removeEventListener('pointerover', onOver);
        svg.removeEventListener('pointerleave', onLeave);
        svg.removeEventListener('click', onClick);
      }
      a11y.remove();
    },
    svg,
  };
}
