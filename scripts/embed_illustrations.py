#!/usr/bin/env python3
"""Emit an inline <symbol> sprite from the LUMI illustration set.

Illustrations are the expressive register's scene vocabulary
(references/brand.md; the style contract is design-rules.md) — first-party,
drawn by scripts/build_illustrations.py, painted only with `var()` tokens so a
scene re-skins with the palette of the document it lands in. The manifest
beside the files states each scene's one meaning; within one document an
illustration means exactly one thing, the same rule an icon obeys.

    python3 scripts/embed_illustrations.py onboarding success   # sprite of these
    python3 scripts/embed_illustrations.py --search empty       # find a scene
    python3 scripts/embed_illustrations.py --list               # the set + meanings
    python3 scripts/embed_illustrations.py --check              # structural gate

Embed only what the document uses. The structural gate reads the allowed paint
roles from tokens/design-tokens.json (`illustration.roles`) rather than
carrying a private copy — a probe that asserts a vocabulary the tokens do not
ship is borrowing conventions from nowhere. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / "assets" / "illustrations"
TOKENS = ROOT / "tokens" / "design-tokens.json"
VIEWBOX = 'viewBox="0 0 320 240"'


def manifest():
    p = LIB / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def roles():
    data = json.loads(TOKENS.read_text(encoding="utf-8"))
    return data.get("illustration", {}).get("roles", [])


def inner(svg):
    body = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.S)
    return re.sub(r"</svg>\s*$", "", body).strip()


def load(name):
    path = LIB / f"{name}.svg"
    if not path.exists():
        raise SystemExit(
            f"no illustration named {name!r} in {LIB.relative_to(ROOT)} — "
            f"try: python3 scripts/embed_illustrations.py --search {name}")
    return path.read_text(encoding="utf-8")


def sprite(names):
    seen, out = [], ['<svg width="0" height="0" style="position:absolute" '
                     'aria-hidden="true" focusable="false"><defs>']
    for n in names:
        if n in seen:
            continue
        seen.append(n)
        out.append(f'<symbol id="il-{n}" {VIEWBOX}>{inner(load(n))}</symbol>')
    out.append("</defs></svg>")
    return "".join(out)


def check():
    files = sorted(LIB.glob("*.svg"))
    man = manifest()
    allowed = set(roles())
    bad = False
    if not allowed:
        print("FAIL  tokens/design-tokens.json carries no illustration.roles — "
              "the paint vocabulary must ship in the tokens")
        return 1
    if not man:
        print("FAIL  assets/illustrations/manifest.json is missing or empty")
        bad = True
    names = {f.stem for f in files}
    for n in sorted(names - set(man)):
        print(f"FAIL  {n}.svg has no manifest entry — a scene ships its meaning")
        bad = True
    for n in sorted(set(man) - names):
        print(f"FAIL  manifest names {n!r} but {n}.svg does not exist")
        bad = True
    paint_re = re.compile(r'(?:fill|stroke)="([^"]+)"')
    var_re = re.compile(r"^var\((--[a-z0-9-]+)\)$")
    for f in files:
        s = f.read_text(encoding="utf-8")
        errs = []
        if VIEWBOX not in s:
            errs.append("not on the 320x240 viewBox")
        if re.search(r"#[0-9A-Fa-f]{3,6}\b", s):
            errs.append("hardcoded hex")
        for banned, why in (("<image", "raster"), ("<text", "font dependency"),
                            ("Gradient", "gradient")):
            if banned in s:
                errs.append(why)
        for m in re.finditer(r'id="([^"]+)"', s):
            if not m.group(1).startswith("il-"):
                errs.append(f'id {m.group(1)!r} not namespaced il-')
        for val in paint_re.findall(s):
            if val == "none":
                continue
            vm = var_re.match(val)
            if not vm:
                errs.append(f"paint {val!r} is not a var() token")
            elif vm.group(1) not in allowed:
                errs.append(f"paint {vm.group(1)!r} not in illustration.roles")
        if s.count('fill="var(--lime)"') > 1:
            errs.append("more than one lime surface")
        if 'stroke="var(--lime)"' in s:
            errs.append("the lime is a surface, never a stroke")
        if errs:
            bad = True
            print(f"FAIL  {f.name}: " + "; ".join(sorted(set(errs))))
    if not bad:
        print(f"ok    {len(files)} illustrations, manifest 1:1, "
              f"every paint a token from illustration.roles")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="illustration names for the sprite")
    ap.add_argument("--search", metavar="TERM", help="find a scene by name, meaning or tag")
    ap.add_argument("--list", action="store_true", help="the set and its meanings")
    ap.add_argument("--check", action="store_true", help="structural gate")
    args = ap.parse_args(argv)

    if args.list:
        man = manifest()
        width = max((len(n) for n in man), default=0)
        for name in sorted(man):
            print(f"  il-{name:<{width}}  {man[name]['meaning']}")
        print(f"\n  {len(man)} scenes; one meaning per scene per document.")
        return 0

    if args.search:
        term = args.search.lower()
        man = manifest()
        hits = [(n, e) for n, e in sorted(man.items())
                if term in n or term in e["meaning"].lower()
                or any(term in t for t in e["tags"])]
        if not hits:
            print(f"nothing matches {args.search!r}")
            return 1
        for n, e in hits:
            print(f"  {n:<16} {e['meaning']}")
        return 0

    if args.check:
        return check()

    if not args.names:
        ap.error("give illustration names, or --search / --list / --check")
    print(sprite(args.names))
    print()
    print('<!-- instantiate as <svg class="illo"><use href="#il-NAME"/></svg> '
          "inside a flex/grid cell; the .illo base rendering ships in "
          "tokens/lumi-layouts.css (design-rules.md, the illustration section). -->")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
