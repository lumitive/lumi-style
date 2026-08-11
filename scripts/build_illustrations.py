#!/usr/bin/env python3
"""Author the LUMI illustration set: 12 scenes, drawn in code, tokens only.

First-party artwork for the expressive register (references/brand.md) — the
scenes are composed here so they stay regenerable and byte-stable, the way the
globe and the seigaiha drawings are. Style contract (design-rules.md):
320x240, flat shapes only (no gradients, no raster, no <text>), every paint a
`var()` token so the drawing re-skins with the palette, exaggerated cartoon
proportions (the head rivals the body), Japanese flat composition (asymmetry,
negative space, thick/thin contrast). Every scene carries a waterline, water
is seigaiha-derived arc texture, and the lime is a surface — at most one
filled panel per scene, never a stroke.

    python3 scripts/build_illustrations.py           # write the set + manifest
    python3 scripts/build_illustrations.py --check   # verify all are current

Per-document embedding is scripts/embed_illustrations.py, which also owns the
structural gate on these files. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math as _m
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / "assets" / "illustrations"

# ── helpers ──────────────────────────────────────────────────────────────────

def fan(cx, y, r, color="--acc-4", op=0.7, w=1.3, rings=3):
    """One seigaiha fan: concentric stroked arcs sitting on baseline y."""
    out = []
    for k in range(rings):
        rr = r * (1 - k / (rings + 1))
        out.append(f'<path d="M {cx - rr:.1f} {y} A {rr:.1f} {rr:.1f} 0 0 1 '
                   f'{cx + rr:.1f} {y}" fill="none" stroke="var({color})" '
                   f'stroke-width="{w}" stroke-opacity="{op}"/>')
    return out


def water(y, x0=0, x1=320, depth=None, fill="--acc-wash", rows=2):
    """A water body: flat band below the waterline, seigaiha texture on top."""
    depth = depth if depth is not None else 240 - y
    out = [f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="{depth}" '
           f'fill="var({fill})"/>',
           f'<path d="M {x0} {y} L {x1} {y}" fill="none" '
           f'stroke="var(--acc-4)" stroke-width="1.6"/>']
    step = 46
    for row in range(rows):
        yy = y + 12 + row * 16
        off = x0 + (23 if row % 2 else 0)
        n = int((x1 - x0) / step) + 2
        for i in range(n):
            cx = off + i * step
            if x0 - 24 < cx < x1 + 24:
                out += fan(cx, yy, 20 - row * 3, op=0.55 - row * 0.15)
    return out


def person(cx, base_y, s=1.0, shirt="--acc", skin="--acc-2", hair="--acc-5",
           arms=((-38, -18), (38, -18)), look=0.0, leg=True):
    """An exaggerated flat cartoon figure standing on base_y.

    Head is nearly the size of the body — the cartoon proportion. arms are
    (dx, dy) hand offsets from the shoulder; look shifts the eyes.
    """
    hr = 17 * s                       # head radius
    bw = 30 * s                       # body width
    bh = 34 * s                       # body height
    body_top = base_y - (8 * s if leg else 0) - bh
    head_cy = body_top - hr + 4 * s
    sh_y = body_top + 7 * s
    out = []
    if leg:
        for dx in (-8 * s, 8 * s):
            out.append(f'<path d="M {cx + dx:.1f} {base_y - 10 * s:.1f} '
                       f'L {cx + dx:.1f} {base_y:.1f}" fill="none" '
                       f'stroke="var({hair})" stroke-width="{6 * s:.1f}" '
                       f'stroke-linecap="round"/>')
    out.append(  # body: a rounded flat blob
        f'<path d="M {cx - bw / 2:.1f} {body_top + bh:.1f} '
        f'C {cx - bw / 2 - 2 * s:.1f} {body_top + 6 * s:.1f} '
        f'{cx - bw / 2 + 6 * s:.1f} {body_top:.1f} {cx:.1f} {body_top:.1f} '
        f'C {cx + bw / 2 - 6 * s:.1f} {body_top:.1f} '
        f'{cx + bw / 2 + 2 * s:.1f} {body_top + 6 * s:.1f} '
        f'{cx + bw / 2:.1f} {body_top + bh:.1f} Z" fill="var({shirt})"/>')
    for dx, dy in arms:
        out.append(f'<path d="M {cx + (12 * s if dx > 0 else -12 * s):.1f} '
                   f'{sh_y:.1f} Q {cx + dx * 0.6 * s:.1f} '
                   f'{sh_y + dy * 0.2 * s:.1f} {cx + dx * s:.1f} '
                   f'{sh_y + dy * s:.1f}" fill="none" stroke="var({shirt})" '
                   f'stroke-width="{7 * s:.1f}" stroke-linecap="round"/>')
        out.append(f'<circle cx="{cx + dx * s:.1f}" cy="{sh_y + dy * s:.1f}" '
                   f'r="{4.2 * s:.1f}" fill="var({skin})"/>')
    out.append(f'<circle cx="{cx:.1f}" cy="{head_cy:.1f}" r="{hr:.1f}" '
               f'fill="var({skin})"/>')
    out.append(  # hair: a flat cap with a side sweep
        f'<path d="M {cx - hr:.1f} {head_cy:.1f} '
        f'A {hr:.1f} {hr:.1f} 0 0 1 {cx + hr:.1f} {head_cy - 2 * s:.1f} '
        f'C {cx + hr * 0.4:.1f} {head_cy - hr * 1.02:.1f} '
        f'{cx - hr * 0.7:.1f} {head_cy - hr * 0.9:.1f} '
        f'{cx - hr:.1f} {head_cy:.1f} Z" fill="var({hair})"/>')
    ex = cx + look * 6 * s
    for dx in (-6 * s, 6 * s):
        out.append(f'<circle cx="{ex + dx:.1f}" cy="{head_cy + 3 * s:.1f}" '
                   f'r="{1.8 * s:.1f}" fill="var(--nw)"/>')
    out.append(  # a small content mouth
        f'<path d="M {ex - 3 * s:.1f} {head_cy + 9 * s:.1f} '
        f'Q {ex:.1f} {head_cy + 12 * s:.1f} {ex + 3 * s:.1f} '
        f'{head_cy + 9 * s:.1f}" fill="none" stroke="var(--nw)" '
        f'stroke-width="{1.6 * s:.1f}" stroke-linecap="round"/>')
    return out


def doc(x, y, w=26, h=32, tilt=0, fill="--bg"):
    """A little document with ruled lines."""
    g = [f'<g transform="rotate({tilt} {x + w / 2} {y + h / 2})">',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" '
         f'fill="var({fill})" stroke="var(--acc-5)" stroke-width="1.6"/>']
    for i in range(3):
        yy = y + 8 + i * 7
        g.append(f'<path d="M {x + 5} {yy} L {x + w - 5} {yy}" fill="none" '
                 f'stroke="var(--acc-3)" stroke-width="1.6" '
                 f'stroke-linecap="round"/>')
    g.append("</g>")
    return g


W = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" '
     'fill="none" role="img" aria-labelledby="il-{name}-t">'
     '<title id="il-{name}-t">{title}</title>{body}</svg>')

SCENES = {}

# ── 1 · onboarding: through the gate, into the water ─────────────────────────
e = []
e += water(150)
# the dock the newcomer stands on, and the torii out in the shallows
e.append('<rect x="24" y="142" width="128" height="10" rx="3" fill="var(--acc-5)"/>')
e.append('<path d="M 44 152 L 44 172 M 132 152 L 132 172" stroke="var(--acc-5)" stroke-width="5" stroke-linecap="round"/>')
e.append('<path d="M 196 150 L 199 62" stroke="var(--acc-5)" stroke-width="7" stroke-linecap="round"/>')
e.append('<path d="M 258 150 L 255 62" stroke="var(--acc-5)" stroke-width="7" stroke-linecap="round"/>')
e.append('<path d="M 184 62 C 208 55 246 55 270 62" stroke="var(--acc-5)" stroke-width="8" stroke-linecap="round"/>')
e.append('<path d="M 192 80 L 262 80" stroke="var(--acc-5)" stroke-width="5" stroke-linecap="round"/>')
e += fan(227, 150, 26, color="--d-teal", op=0.8)
e += person(92, 142, s=1.05, shirt="--d-blue", arms=((-30, -34), (40, -30)), look=0.5)
SCENES["onboarding"] = ("Onboarding: a figure on the dock, the gate ahead", e)

# ── 2 · search-empty: casting into still water, nothing yet ──────────────────
e = []
e += water(168, rows=2)
e += person(70, 168, s=1.0, shirt="--d-teal", arms=((-26, -30), (44, -46)), look=0.6)
e.append('<path d="M 114 90 C 158 78 208 94 236 126" fill="none" stroke="var(--acc-5)" stroke-width="2.2" stroke-linecap="round"/>')
e.append('<path d="M 236 126 L 236 168" fill="none" stroke="var(--acc-5)" stroke-width="1.4" stroke-dasharray="1 5" stroke-linecap="round"/>')
e += fan(236, 170, 16, color="--d-teal", op=0.9, w=1.5)
e.append('<circle cx="236" cy="170" r="4.5" fill="none" stroke="var(--d-teal)" stroke-width="1.6"/>')
# a drawn question mark — no <text>, the asset carries no font dependency
e.append('<path d="M 258 78 C 258 68 266 62 274 63 C 282 64 287 70 286 77 C 285 87 273 88 272 98" fill="none" stroke="var(--acc-3)" stroke-width="4" stroke-linecap="round"/>')
e.append('<circle cx="272" cy="108" r="2.6" fill="var(--acc-3)"/>')
SCENES["search-empty"] = ("Empty search: the line is cast, nothing on the hook yet", e)

# ── 3 · success: the catch held high on the crest ────────────────────────────
e = []
e += water(176, rows=2)
e.append('<rect x="216" y="52" width="66" height="46" rx="6" fill="var(--lime)"/>')
e.append('<path d="M 226 76 L 238 88 L 266 62" fill="none" stroke="var(--on-lime)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
e += person(112, 176, s=1.1, shirt="--d-teal", arms=((-34, -44), (36, -48)), look=0.3)
# the fish, exaggerated and happy, in the raised hand
e.append('<path d="M 138 112 C 150 100 170 100 180 112 C 170 122 150 123 138 112 Z" fill="var(--d-blue)"/>')
e.append('<path d="M 180 112 L 192 102 L 190 118 Z" fill="var(--d-blue)"/>')
e.append('<circle cx="148" cy="108" r="1.8" fill="var(--bg)"/>')
SCENES["success"] = ("Success: the catch held up, the panel says done", e)

# ── 4 · error: the bucket tipped, the water got out ──────────────────────────
e = []
e.append('<path d="M 24 190 L 296 190" stroke="var(--acc-4)" stroke-width="1.6"/>')
e += person(210, 190, s=1.05, shirt="--amber", arms=((-40, -6), (34, -12)), look=-0.6)
e.append('<g transform="rotate(-64 122 176)"><path d="M 102 158 L 142 158 L 136 192 L 108 192 Z" fill="var(--acc-2)"/><path d="M 102 158 L 142 158" stroke="var(--acc-5)" stroke-width="3" stroke-linecap="round"/></g>')
e.append('<path d="M 104 174 C 92 180 84 184 78 188" fill="none" stroke="var(--d-blue)" stroke-width="4" stroke-linecap="round"/>')
e.append('<path d="M 44 190 C 62 184 96 184 116 190 C 96 195 62 195 44 190 Z" fill="var(--acc-wash)" stroke="var(--d-blue)" stroke-width="2"/>')
e += fan(80, 189, 14, color="--d-blue", op=0.8, w=1.2, rings=2)
e.append('<path d="M 236 96 L 236 118 M 236 128 L 236 130" stroke="var(--seal)" stroke-width="5" stroke-linecap="round"/>')
SCENES["error"] = ("Error: the bucket tipped over, the spill is contained", e)

# ── 5 · teamwork: two rowers, one current ────────────────────────────────────
e = []
e += water(170, rows=2)
e.append('<path d="M 60 170 C 76 192 244 192 262 170 L 236 160 L 84 160 Z" fill="var(--acc-5)"/>')
e += person(126, 166, s=0.92, shirt="--acc-inbox", arms=((-30, 8), (26, -10)), look=0.5, leg=False)
e += person(196, 166, s=0.92, shirt="--d-blue", arms=((-26, 8), (30, -10)), look=0.5, leg=False)
e.append('<path d="M 100 148 L 74 186" stroke="var(--acc-5)" stroke-width="3.4" stroke-linecap="round"/>')
e.append('<path d="M 224 146 L 250 184" stroke="var(--acc-5)" stroke-width="3.4" stroke-linecap="round"/>')
SCENES["teamwork"] = ("Teamwork: two rowers pulling the same boat", e)

# ── 6 · data-flow: the current carries the record ────────────────────────────
e = []
e.append('<path d="M 0 96 C 60 84 90 120 150 110 C 214 99 240 132 320 118" fill="none" stroke="var(--acc-4)" stroke-width="1.8"/>')
e.append('<path d="M 0 128 C 60 116 92 150 152 140 C 216 129 244 160 320 148" fill="none" stroke="var(--d-teal)" stroke-width="1.6" stroke-opacity="0.7"/>')
e += doc(52, 84, tilt=-8)
e += doc(150, 96, tilt=5)
e += doc(248, 106, tilt=-4)
for cx, yy in ((100, 130), (206, 146), (288, 136)):
    e += fan(cx, yy, 13, color="--d-teal", op=0.5, w=1.1, rings=2)
e.append('<path d="M 296 112 L 312 118 L 296 126" fill="none" stroke="var(--acc-4)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
SCENES["data-flow"] = ("Data flow: records riding the current downstream", e)

# ── 7 · decision: the river forks at the rock ────────────────────────────────
e = []
# one stream in from the left, splitting around the rock into two channels
e.append('<path d="M 0 118 C 60 112 110 112 150 118 C 196 126 214 112 244 96 C 270 82 296 76 320 74 L 320 106 C 292 108 268 116 246 128 L 320 170 L 320 200 C 280 178 244 158 216 146 C 190 136 150 148 110 150 C 72 152 34 150 0 146 Z" fill="var(--acc-wash)"/>')
e.append('<path d="M 0 118 C 60 112 110 112 150 118 C 196 126 214 112 244 96 C 270 82 296 76 320 74" fill="none" stroke="var(--acc-4)" stroke-width="1.6"/>')
e.append('<path d="M 0 146 C 34 150 72 152 110 150 C 150 148 190 136 216 146 C 244 158 280 178 320 200" fill="none" stroke="var(--acc-4)" stroke-width="1.6"/>')
e.append('<path d="M 246 128 C 268 116 292 108 320 106" fill="none" stroke="var(--acc-4)" stroke-width="1.4" stroke-opacity="0.8"/>')
# the rock the fork happens at
e.append('<path d="M 228 118 C 234 108 250 106 258 114 C 264 122 260 132 248 134 C 236 135 224 128 228 118 Z" fill="var(--acc-5)"/>')
for cx, yy in ((70, 132), (170, 134), (282, 92)):
    e += fan(cx, yy, 11, op=0.5, w=1.1, rings=2)
# the figure on the bank, weighing the two channels
e.append('<path d="M 22 214 L 138 214" stroke="var(--acc-4)" stroke-width="1.6" stroke-linecap="round"/>')
e += person(80, 214, s=1.0, shirt="--d-blue", arms=((-38, -34), (26, -6)), look=0.6)
SCENES["decision"] = ("Decision: the river forks at the rock and one channel is taken", e)

# ── 8 · practice: writing it out, wave by wave ───────────────────────────────
e = []
e.append('<path d="M 30 196 L 290 196" stroke="var(--acc-4)" stroke-width="1.6"/>')
# the figure sits behind the desk, head and shoulders above it, pencil in hand
e += person(188, 180, s=1.0, shirt="--acc-inbox", arms=((-42, -8), (24, -16)), look=-0.7, leg=False)
e.append('<rect x="56" y="154" width="150" height="42" rx="5" fill="var(--acc-1)"/>')
e.append('<path d="M 56 154 L 206 154" stroke="var(--acc-3)" stroke-width="2"/>')
# the sheet on the desk and the wave being copied
e.append('<g transform="rotate(-4 116 148)"><rect x="80" y="134" width="72" height="28" rx="3" fill="var(--bg)" stroke="var(--acc-5)" stroke-width="1.6"/></g>')
e.append('<path d="M 90 149 C 98 143 106 143 114 149 C 122 155 130 155 138 149" fill="none" stroke="var(--acc-4)" stroke-width="2" stroke-linecap="round"/>')
e.append('<path d="M 146 154 L 158 138" stroke="var(--amber)" stroke-width="3.4" stroke-linecap="round"/>')
# the model wave, pinned on its own card above the desk
e.append('<rect x="236" y="76" width="72" height="36" rx="4" fill="var(--bg)" stroke="var(--acc-3)" stroke-width="1.6"/>')
e.append('<path d="M 246 94 C 254 88 262 88 270 94 C 278 100 286 100 294 94" fill="none" stroke="var(--d-teal)" stroke-width="2.2" stroke-linecap="round"/>')
SCENES["practice"] = ("Practice: copying the wave until the hand knows it", e)

# ── 9 · setup: tools out before the tide ─────────────────────────────────────
e = []
e += water(206, rows=1)
e += person(92, 206, s=1.05, shirt="--d-blue", arms=((-32, -8), (38, -30)), look=0.4)
# the spanner in the raised hand
e.append('<g transform="rotate(-34 146 156)"><path d="M 132 152 C 128 146 129 139 134 135 L 138 143 L 146 142 L 146 134 C 152 136 156 142 154 149 C 153 153 150 156 146 157 L 150 178 C 150 182 146 185 142 184 C 139 183 137 181 137 178 L 138 156 C 135 155 133 154 132 152 Z" fill="var(--acc-3)"/></g>')
# a proper gear: ring, eight teeth, centre hole
e.append('<circle cx="224" cy="120" r="15" fill="none" stroke="var(--acc-5)" stroke-width="7"/>')
e.append('<circle cx="224" cy="120" r="4" fill="none" stroke="var(--acc-5)" stroke-width="2.4"/>')
for k in range(8):
    a = _m.pi / 4 * k + 0.2
    x1, y1 = 224 + 21 * _m.cos(a), 120 + 21 * _m.sin(a)
    x2, y2 = 224 + 26 * _m.cos(a), 120 + 26 * _m.sin(a)
    e.append(f'<path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}" stroke="var(--acc-5)" stroke-width="6" stroke-linecap="round"/>')
e += fan(262, 208, 16, op=0.6, w=1.2, rings=2)
SCENES["setup"] = ("Setup: the spanner out and the gear waiting, before the tide", e)

# ── 10 · feedback: the ripple that comes back ────────────────────────────────
e = []
e += water(186, rows=1)
e += person(84, 186, s=1.0, shirt="--d-blue", arms=((-26, -18), (36, -40)), look=0.5)
e.append('<circle cx="150" cy="186" r="3.5" fill="var(--d-teal)"/>')
for r in (12, 24, 38):
    e.append(f'<path d="M {150 - r} 186 A {r} {r} 0 0 1 {150 + r} 186" fill="none" stroke="var(--d-teal)" stroke-width="1.6" stroke-opacity="{0.9 - r * 0.012:.2f}"/>')
e.append('<path d="M 214 118 C 214 104 228 96 244 96 C 262 96 274 106 274 120 C 274 132 262 140 246 140 C 242 140 238 140 234 139 L 222 148 C 224 142 224 138 222 134 C 217 130 214 125 214 118 Z" fill="var(--acc-inbox)"/>')
e.append('<path d="M 232 112 C 238 108 250 108 256 112" fill="none" stroke="var(--on-acc)" stroke-width="2.4" stroke-linecap="round"/>')
e.append('<path d="M 232 122 C 240 126 248 126 256 122" fill="none" stroke="var(--on-acc)" stroke-width="2.4" stroke-linecap="round"/>')
SCENES["feedback"] = ("Feedback: a ripple sent out and the reply that returns", e)

# ── 11 · security: the breakwater holds ──────────────────────────────────────
e = []
# rough sea left, the jetty in the middle, calm harbour right
e += water(148, x0=0, x1=148, rows=2)
e += water(170, x0=196, x1=320, rows=1, fill="--acc-1")
e.append('<path d="M 148 128 L 188 128 C 194 128 196 132 196 138 L 196 240 L 140 240 L 140 136 C 140 130 142 128 148 128 Z" fill="var(--acc-5)"/>')
e.append('<path d="M 148 128 L 188 128" stroke="var(--acc-4)" stroke-width="3" stroke-linecap="round"/>')
# the wave curling against the wall
e.append('<path d="M 108 148 C 116 122 132 112 140 122 C 146 130 138 138 128 137" fill="none" stroke="var(--d-blue)" stroke-width="3.4" stroke-linecap="round"/>')
e += fan(122, 150, 24, color="--d-blue", op=0.85, w=1.6)
for cx, cy in ((104, 116), (130, 104), (144, 112)):
    e.append(f'<circle cx="{cx}" cy="{cy}" r="2.2" fill="var(--d-blue)" fill-opacity="0.6"/>')
# the little boat, flat water, sail up
e.append('<path d="M 234 170 C 240 178 262 178 268 170 Z" fill="var(--acc-5)"/>')
e.append('<path d="M 251 166 L 251 138 C 260 142 266 150 268 160 L 251 162 Z" fill="var(--acc-inbox)"/>')
# the harbour-master's little pier
e.append('<rect x="264" y="198" width="56" height="9" rx="3" fill="var(--acc-5)"/>')
e.append('<path d="M 278 207 L 278 226 M 308 207 L 308 226" stroke="var(--acc-5)" stroke-width="4" stroke-linecap="round"/>')
e += person(296, 198, s=0.95, shirt="--d-teal", arms=((-26, -16), (26, -18)), look=-0.5, leg=False)
SCENES["security"] = ("Security: the breakwater takes the wave, the harbour stays calm", e)

# ── 12 · progress: the koi climbs the fall ───────────────────────────────────
e = []
# the cliff shoulder and the fall, pouring into the pool
e.append('<path d="M 320 0 L 320 240 L 262 240 L 262 60 C 246 52 238 34 240 0 Z" fill="var(--acc-1)"/>')
e.append('<path d="M 240 0 C 238 34 246 52 262 60 L 262 240" fill="none" stroke="var(--acc-3)" stroke-width="1.6"/>')
e.append('<path d="M 196 0 C 196 70 194 140 190 196" fill="none" stroke="var(--d-teal)" stroke-width="7" stroke-opacity="0.55" stroke-linecap="round"/>')
e.append('<path d="M 214 0 C 214 74 213 148 210 200" fill="none" stroke="var(--d-teal)" stroke-width="10" stroke-opacity="0.4" stroke-linecap="round"/>')
e.append('<path d="M 228 0 C 228 76 227 150 226 202" fill="none" stroke="var(--d-teal)" stroke-width="6" stroke-opacity="0.55" stroke-linecap="round"/>')
e += water(202, rows=1)
e += fan(206, 204, 24, color="--d-teal", op=0.8, w=1.5)
# the koi, nose to the fall, most of the way up
e.append('<g transform="rotate(56 166 112)"><path d="M 138 112 C 152 96 178 96 192 112 C 178 126 152 127 138 112 Z" fill="var(--d-blue)"/><path d="M 138 112 L 120 98 L 124 124 Z" fill="var(--d-blue)"/><circle cx="180" cy="106" r="2.4" fill="var(--bg)"/><path d="M 158 100 C 163 106 163 118 158 124 M 170 99 C 175 105 175 119 170 125" fill="none" stroke="var(--bg)" stroke-width="1.8" stroke-opacity="0.8"/></g>')
# spray where the fish broke the fall
for cx, cy in ((186, 66), (200, 54), (162, 58)):
    e.append(f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="var(--d-teal)" fill-opacity="0.6"/>')
e.append('<path d="M 36 202 C 48 194 66 194 78 200" fill="none" stroke="var(--acc-3)" stroke-width="1.8" stroke-linecap="round"/>')
SCENES["progress"] = ("Progress: the koi climbing the waterfall, most of the way up", e)

# ── the manifest: one meaning per scene, searchable ──────────────────────────
# Within one document an illustration means exactly one thing (the icon rule,
# at scene scale); this is where that one thing is stated.
MANIFEST = {
    "onboarding": {"meaning": "the first arrival: on the dock, the gate ahead",
                   "tags": ["welcome", "start", "begin", "intro", "gate", "torii"]},
    "search-empty": {"meaning": "an empty result: the line is cast, nothing on the hook yet",
                     "tags": ["empty", "no-results", "search", "fishing", "missing"]},
    "success": {"meaning": "the catch held up, the panel says done",
                "tags": ["done", "complete", "achievement", "check", "catch"]},
    "error": {"meaning": "the bucket tipped: something spilled, and it is contained",
              "tags": ["failure", "spill", "mistake", "alert", "broken"]},
    "teamwork": {"meaning": "two rowers, one boat, one current",
                 "tags": ["collaboration", "together", "crew", "rowing"]},
    "data-flow": {"meaning": "records riding the current downstream",
                  "tags": ["pipeline", "stream", "documents", "integration", "flow"]},
    "decision": {"meaning": "the river forks at the rock; one channel is taken",
                 "tags": ["choice", "fork", "branch", "tradeoff", "crossroads"]},
    "practice": {"meaning": "copying the wave until the hand knows it",
                 "tags": ["exercise", "training", "learn", "repeat", "drill"]},
    "setup": {"meaning": "the spanner and the gear, before the tide",
              "tags": ["install", "configure", "tools", "prepare", "wrench"]},
    "feedback": {"meaning": "a ripple sent out and the reply that returns",
                 "tags": ["response", "review", "echo", "comment", "reply"]},
    "security": {"meaning": "the breakwater takes the wave; the harbour stays calm",
                 "tags": ["protection", "safety", "defense", "compliance", "harbour"]},
    "progress": {"meaning": "the koi climbing the waterfall, most of the way up",
                 "tags": ["advance", "growth", "milestone", "koi", "waterfall"]},
}
assert set(MANIFEST) == set(SCENES), "every scene carries a manifest entry"


def targets():
    out = []
    for name, (title, elems) in sorted(SCENES.items()):
        svg = W.format(name=name, title=title, body="".join(elems)) + "\n"
        out.append((LIB / f"{name}.svg", svg))
    out.append((LIB / "manifest.json",
                json.dumps(MANIFEST, indent=2, ensure_ascii=False) + "\n"))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    stale = []
    for path, content in targets():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if args.check:
            stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if args.check:
        for path in stale:
            print(f"FAIL  {path.relative_to(ROOT)} is stale or missing; "
                  f"re-run without --check")
        if not stale:
            print(f"ok    {len(SCENES)} illustrations and the manifest are current")
        return 1 if stale else 0
    print(f"wrote {len(SCENES)} illustrations + manifest to {LIB.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
