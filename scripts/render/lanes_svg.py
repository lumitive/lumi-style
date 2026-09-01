#!/usr/bin/env python3
"""Draw a comparison as two labelled LAYERS, one item per chip.

**Why this exists.** The owner's review of one page: the drawing was complex,
expressed none of the prose beside it, and left her asking what the relation
between its left half and its right half was supposed to be. The page's claim
was that a stack has two layers with different properties — a transport layer
and a content layer — and the figure had no layer in it at all.

A lane figure answers that question in its structure rather than in a legend.
Each layer is a named horizontal band; each item is a chip inside the band it
belongs to; and one criterion is drawn ON the chip, so the reader takes the
split and the verdict in one look.

    python3 scripts/render/lanes_svg.py --data spec.json

The spec is `compare`, with `lanes` naming the LAYERS and each item declaring
which one it sits in. `lanes` is exclusive with `criteria`, which is what a
radar draws — a spec carrying both has not chosen its figure:

    {
      "move": "compare",
      "subject": {"label": "A2UI", "lane": "content", "chip": "Google-led"},
      "lanes": [{"name": "transport", "note": "who moves the bytes"},
                {"name": "content",   "note": "who decides what renders"}],
      "references": [{"label": "A2A", "lane": "transport",
                      "chip": "Linux Foundation", "state": "neutral"}]
    }

`state` colours the chip and is the whole verdict: `neutral`, `single` (one
vendor, no foundation), `partial`, `absent`. Naming it on the item rather than
inferring it from the chip text is deliberate — a renderer that reads English
to decide a colour is a renderer that will be wrong about a name it has not
seen.

An item whose `lane` is not one of the declared criteria is a REFUSAL, never a
default lane: silently dropping it into the first band would draw a claim the
spec does not make, which is the class of defect this whole tool set exists
against.

Standard library only.
"""
from __future__ import annotations

import argparse
import html
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import figure_scale  # noqa: E402
import figure_spec  # noqa: E402

BOX_W = {"landscape": 1180, "portrait": 620}

LANE_LABEL_W = 168.0     # the band's own name, upright, left of the chips
LANE_H = 118.0
LANE_GAP = 18.0
TOP = 12.0
CHIP_H = 74.0
CHIP_GAP = 14.0

# The four verdicts a chip can carry, and the tokens they take. `one colour one
# meaning` (tokens/lumi-theme.css): built/pass, partial, reference, red line.
STATE = {
    "neutral": ("var(--acc)", "var(--acc-wash)"),
    "partial": ("var(--amber)", "var(--amber-wash)"),
    "absent": ("var(--brass)", "var(--brass-wash)"),
    "single": ("var(--seal)", "var(--seal-wash)"),
}


def _check(spec, path):
    figure_spec.refuse_if_unusable(spec, path)
    if str(spec.get("move")).lower() != "compare":
        raise SystemExit(
            f"{path} declares move {spec.get('move')!r}; this tool draws "
            f"`compare` as layers. assets/frameworks.json says which tool "
            f"draws which move.")
    lanes = [str(c.get("name") or "").strip()
             for c in (spec.get("lanes") or [])]
    if len(lanes) < 2 or not all(lanes):
        raise SystemExit(
            f"{path}: a lane figure needs at least two named `lanes` — the "
            f"layers. With one, there is nothing for the split to say, and the "
            f"figure is a row of chips.")
    items = [spec["subject"], *(spec.get("references") or [])]
    for it in items:
        lane = str(it.get("lane") or "").strip()
        if lane not in lanes:
            # NEVER A DEFAULT LANE. Dropping it into the first band would draw
            # a claim the spec does not make, and the reader has no way to see
            # that it was a guess.
            raise SystemExit(
                f"{path}: {it.get('label')!r} declares lane {lane!r}, which is "
                f"not one of {', '.join(lanes)}. The lane is the figure's whole "
                f"argument, so it is stated rather than defaulted.")
        state = it.get("state") or "neutral"
        if state not in STATE:
            raise SystemExit(
                f"{path}: {it.get('label')!r} declares state {state!r}; the "
                f"verdicts are {', '.join(sorted(STATE))}. Colour is meaning "
                f"here, so there is no free-text option.")
        if not str(it.get("chip") or "").strip():
            raise SystemExit(
                f"{path}: {it.get('label')!r} carries no `chip`. A name in a "
                f"lane says only which lane; the chip is the criterion being "
                f"compared, and without it the figure has one dimension.")
    empty = [lane for lane in lanes
             if not [it for it in items if str(it.get("lane")).strip() == lane]]
    if empty:
        # A BAND DRAWN WITH NOTHING IN IT is a two-layer claim on evidence for
        # one. The mirror refusal — an item in an undeclared lane — was written
        # and this one was not, so a spec whose items all sat in one lane drew
        # a full-width empty band and exited 0.
        raise SystemExit(
            f"{path}: lane(s) {', '.join(repr(x) for x in empty)} carry no "
            f"items. A band drawn empty claims a layer the data does not "
            f"support; drop the lane, or put something in it.")
    dupes = [x for x in lanes if lanes.count(x) > 1]
    if dupes:
        raise SystemExit(
            f"{path}: lane {dupes[0]!r} is declared twice, so its items would "
            f"be drawn into both bands and counted twice by a reader.")
    return lanes, items


def render(spec, orientation: str = "landscape", path: str = "the spec") -> str:
    if orientation not in BOX_W:
        raise SystemExit(f"orientation must be one of {sorted(BOX_W)}")
    lanes, items = _check(spec, path)
    W = BOX_W[orientation]
    subject_label = str(spec["subject"].get("label"))

    parts: list[str] = []
    y = TOP
    for li, lane in enumerate(lanes):
        crit = (spec.get("lanes") or [])[li]
        mine = [it for it in items if str(it.get("lane")).strip() == lane]
        parts += [
            f'<rect x="0" y="{y:.0f}" width="{W}" height="{LANE_H:.0f}" '
            f'fill="var(--card-bg)" stroke="var(--ln1)"/>',
            f'<text class="flbl" x="16" y="{y + 28:.0f}" '
            f'style="fill:var(--tx1);font-size:14px;font-weight:800;'
            f'letter-spacing:.06em">{html.escape(lane.upper())}</text>',
        ]
        for j, line in enumerate(figure_scale.wrap(
                str(crit.get("note") or ""), LANE_LABEL_W - 32, at_px=12)):
            parts.append(
                f'<text class="ftick" x="16" y="{y + 50 + j * 16:.0f}" '
                f'style="fill:var(--tx3);font-size:12px">'
                f'{html.escape(line)}</text>')

        avail = W - LANE_LABEL_W - 16
        cw = (avail - CHIP_GAP * (len(mine) - 1)) / max(1, len(mine))
        for k, it in enumerate(mine):
            x = LANE_LABEL_W + k * (cw + CHIP_GAP)
            ink, wash = STATE[it.get("state") or "neutral"]
            top = y + (LANE_H - CHIP_H) / 2
            is_subject = str(it.get("label")) == subject_label
            parts += [
                f'<rect x="{x:.1f}" y="{top:.0f}" width="{cw:.1f}" '
                f'height="{CHIP_H:.0f}" rx="6" fill="{wash}" '
                f'stroke="{ink}" stroke-width="{2 if is_subject else 1}"/>',
                f'<text class="flbl" x="{x + 11:.1f}" y="{top + 25:.0f}" '
                f'style="fill:var(--tx1);font-size:14px;'
                f'font-weight:{800 if is_subject else 700}">'
                f'{html.escape(str(it["label"]))}</text>',
            ]
            # THE CHIP HOLDS TWO LINES. `wrap`'s budget floor keeps emitting
            # lines however narrow the box, so a long chip in a crowded lane
            # ran its third line past the chip's own bottom edge. Two lines is
            # what the 74-unit chip has room for; a third is a chip whose text
            # is a sentence, and the refusal says so rather than drawing it.
            chip_lines = figure_scale.wrap(str(it["chip"]), cw - 22, at_px=12)
            if len(chip_lines) > 2:
                raise SystemExit(
                    f"{path}: {it['label']!r}'s chip needs {len(chip_lines)} "
                    f"lines and the chip holds two. Shorten it — a chip is the "
                    f"criterion, not the explanation.")
            for j, line in enumerate(chip_lines):
                parts.append(
                    f'<text class="ftick" x="{x + 11:.1f}" '
                    f'y="{top + 45 + j * 15:.0f}" '
                    f'style="fill:{ink};font-size:12px;font-weight:700">'
                    f'{html.escape(line)}</text>')
        y += LANE_H + LANE_GAP

    measure = spec["measure"]
    unit = str(measure.get("unit") or "")
    parts.append(
        f'<text class="axname-x" x="0" y="{y + 6:.0f}">'
        f'{html.escape(str(measure["name"]))}'
        f'{" · " + html.escape(unit) if unit else ""}</text>')
    read = figure_scale.wrap(str(spec["reading"]), W - 40, at_px=13)
    for j, line in enumerate(read):
        parts.append(f'<text class="fread" x="0" y="{y + 32 + j * 20:.0f}" '
                     f'style="font-size:14px;font-weight:600">{html.escape(line)}</text>')
    # LAST, and small: the evidence line is a note, not the page's subject.
    note_y = y + 36 + len(read) * 20
    parts.append(
        f'<text class="fnote" x="0" y="{note_y:.0f}" '
        f'style="fill:var(--tx4);font-size:12px">'
        f'{html.escape(str(spec["source"]))} · '
        f'{html.escape(str(spec["period"]))}</text>')

    H = round(note_y + 8)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" role="img" '
            f'aria-label="{html.escape(str(spec["reading"]))}">\n'
            + "\n".join(parts) + "\n</svg>")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, metavar="PATH",
                    help="the JSON spec; a `compare` whose criteria are layers")
    ap.add_argument("--orientation", choices=sorted(BOX_W), default="landscape")
    a = ap.parse_args(argv)
    spec, problem = figure_spec.load(pathlib.Path(a.data))
    if problem:
        sys.exit(problem)
    print(render(spec, orientation=a.orientation, path=a.data))


if __name__ == "__main__":
    main()
