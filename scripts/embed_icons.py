#!/usr/bin/env python3
"""Emit an inline <symbol> sprite from the vendored icon library.

design-rules.md §5 has required "symbol library embedded per document" since 1.2.
Until 0.1.338 the package shipped nothing, so deliverables carried no icons. The
first fix shipped eight hand-drawn icons, and a reader said the expressiveness
was still short and the icons did not match the content: eight meanings cannot
cover a twenty-five page deck, so they were reused for meanings they did not fit.
A vocabulary too small to say the thing is worse than none, because it teaches a
mapping and then breaks it.

The library is now Lucide (2007 icons, ISC, vendored in assets/icons/lucide/).
Breadth solves expressiveness; the CORE map below solves consistency by reserving
one icon per recurring LUMI meaning. Both halves are needed.

assets/icons/lumi/ is the hand-drawn skin on top of that vocabulary — first-party
glyphs for the expressive register (references/brand.md), same names, same grid,
slightly heavier stroke. A skin never adds a name Lucide cannot resolve, so the
meaning of an icon is register-independent and a missing skin degrades to Lucide
rather than to nothing.

    python3 scripts/embed_icons.py radar route code     # sprite of just these
    python3 scripts/embed_icons.py --core               # sprite of the reserved set
    python3 scripts/embed_icons.py --core --register expressive   # hand-drawn skin
    python3 scripts/embed_icons.py --search tariff      # find an icon by name or tag
    python3 scripts/embed_icons.py --list               # the reserved meanings
    python3 scripts/embed_icons.py --check              # library integrity

Embed only what a document uses. A 2007-icon sprite in every deliverable would be
0.9 MB of dead weight, which is how a library becomes a liability.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / "assets" / "icons" / "lucide"
LIB_LUMI = ROOT / "assets" / "icons" / "lumi"
STROKE = "1.25"          # LUMI hairline; Lucide ships at 2
LUMI_STROKE = "1.75"     # the hand-drawn skin is friendlier and slightly heavier
MIN_LIBRARY = 300        # below this the set is too thin to express a document

# Reserved bindings: one icon per recurring LUMI meaning, so the same concept
# looks the same in every deliverable. Anything outside this map is free choice,
# but within one document an icon still means exactly one thing.
CORE = {
    "master data": "book-open",
    "watch, collection": "radar",
    "adjudication, convergence": "funnel",
    "alert, push": "bell",
    "compliance, red line": "shield",
    "signature, the human who signs": "pen-tool",
    "measurement, metrics": "gauge",
    "not built, refused, out of scope": "ban",
    "a classification code, the tariff line": "code",
    "the origin path, a supply chain leg": "route",
    "a dated event, the timeline": "calendar",
    "a fork in the rules, a watershed": "git-branch",
    "stacked evidence, an evaluation ladder": "layers",
    "what may be said, claim wording": "message-square-quote",
    "an ask, an input the client owes": "list-checks",
    "two dimensions judged separately": "split",
    "a legal determination": "scale",
    "accuracy, the target": "target",
    "a tip, the aside worth keeping": "lightbulb",
    "a step in a procedure": "footprints",
    "practice, the exercise the reader does": "pencil",
    "caution before the sharp edge": "triangle-alert",
    "a check of understanding": "circle-help",
    "done, the completed state": "circle-check",
}

# The two skins. The expressive register (references/brand.md) resolves a name
# against the hand-drawn LUMI set first and falls back to Lucide, so the
# semantic vocabulary never forks — `shield` means compliance in both skins,
# and a document mixes skins only where the hand-drawn set has no glyph yet.
REGISTERS = ("restrained", "expressive")


def resolve(name, register="restrained"):
    """The path an icon name resolves to under a register, or None."""
    if register == "expressive":
        p = LIB_LUMI / f"{name}.svg"
        if p.exists():
            return p
    p = LIB / f"{name}.svg"
    return p if p.exists() else None


def load(name, register="restrained"):
    path = resolve(name, register)
    if path is None:
        raise SystemExit(
            f"no icon named {name!r} in {LIB.relative_to(ROOT)} — "
            f"try: python3 scripts/embed_icons.py --search {name}")
    return path


def inner(svg):
    body = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.S)
    return re.sub(r"</svg>\s*$", "", body).strip()


def sprite(names, register="restrained"):
    seen, out = [], ['<svg width="0" height="0" style="position:absolute" '
                     'aria-hidden="true" focusable="false"><defs>']
    for n in names:
        if n in seen:
            continue
        seen.append(n)
        path = load(n, register)
        stroke = LUMI_STROKE if path.parent == LIB_LUMI else STROKE
        out.append(
            f'<symbol id="i-{n}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round">{inner(path.read_text(encoding="utf-8"))}</symbol>')
    out.append("</defs></svg>")
    return "".join(out)


def tags():
    p = LIB / "tags.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def search(term, limit=40):
    term = term.lower()
    t = tags()
    hits = []
    for path in sorted(LIB.glob("*.svg")):
        name = path.stem
        kw = t.get(name, [])
        if term in name:
            hits.append((0, name, kw))
        elif any(term in k.lower() for k in kw):
            hits.append((1, name, kw))
    hits.sort()
    return hits[:limit]


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="icon names to include in the sprite")
    ap.add_argument("--core", action="store_true", help="sprite of the reserved set")
    ap.add_argument("--search", metavar="TERM", help="find an icon by name or tag")
    ap.add_argument("--list", action="store_true", help="the reserved meanings")
    ap.add_argument("--check", action="store_true", help="library integrity")
    ap.add_argument("--register", choices=REGISTERS, default="restrained",
                    help="expressive resolves the hand-drawn LUMI skin first")
    args = ap.parse_args(argv)

    if args.list:
        width = max(len(v) for v in CORE.values())
        for meaning, name in CORE.items():
            skin = " (lumi skin)" if (LIB_LUMI / f"{name}.svg").exists() else ""
            print(f"  i-{name:<{width}}  {meaning}{skin}")
        print(f"\n  {len(list(LIB.glob('*.svg')))} icons available; "
              f"the {len(CORE)} above are reserved bindings; "
              f"{len(list(LIB_LUMI.glob('*.svg')))} carry the hand-drawn skin.")
        return 0

    if args.search:
        hits = search(args.search)
        if not hits:
            print(f"nothing matches {args.search!r}")
            return 1
        for rank, name, kw in hits:
            where = "name" if rank == 0 else "tag"
            print(f"  {name:<32} ({where}) {', '.join(kw[:6])}")
        return 0

    if args.check:
        files = sorted(LIB.glob("*.svg"))
        lumi_files = sorted(LIB_LUMI.glob("*.svg"))
        bad = False
        if len(files) < MIN_LIBRARY:
            print(f"FAIL  only {len(files)} icons; the library floor is {MIN_LIBRARY}")
            bad = True
        if not (LIB / "LICENSE").exists():
            print("FAIL  assets/icons/lucide/LICENSE is missing — vendored work ships its license")
            bad = True
        if not (LIB_LUMI / "README.md").exists():
            print("FAIL  assets/icons/lumi/README.md is missing — first-party work ships its provenance")
            bad = True
        for meaning, name in CORE.items():
            if not (LIB / f"{name}.svg").exists():
                print(f"FAIL  reserved binding {name!r} ({meaning}) has no icon")
                bad = True
        # A skin never forks the vocabulary: every hand-drawn icon shares its
        # name with a Lucide icon, so a restrained document and a missing skin
        # both fall back to the same meaning.
        for f in lumi_files:
            if not (LIB / f.name).exists():
                print(f"FAIL  lumi skin {f.stem!r} has no Lucide counterpart — "
                      f"a skin may not introduce a name the library cannot resolve")
                bad = True
        malformed = []
        for f in files + lumi_files:
            s = f.read_text(encoding="utf-8")
            if 'stroke="currentColor"' not in s or 'viewBox="0 0 24 24"' not in s \
                    or re.search(r"#[0-9A-Fa-f]{3,6}\b", s):
                malformed.append(f.name)
        if malformed:
            bad = True
            print(f"FAIL  {len(malformed)} icons are not on the 24x24 currentColor grid: "
                  f"{', '.join(malformed[:5])}")
        if not bad:
            print(f"ok    {len(files)} icons + {len(lumi_files)} hand-drawn skins, "
                  f"LICENSE and provenance present, "
                  f"{len(CORE)} reserved bindings all resolve")
        return 1 if bad else 0

    names = list(CORE.values()) if args.core else args.names
    if not names:
        ap.error("give icon names, or --core / --search / --list / --check")
    print(sprite(names, args.register))
    print()
    print("<!-- .ic{width:1.4em;height:1.4em;flex:none} on a flex parent; never nudge "
          "an inline icon with vertical-align (design-rules.md §5). -->")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
