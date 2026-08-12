#!/usr/bin/env python3
"""Emit the globe runtime as one inline <script> a deliverable can carry.

The gap this closes was real and it was mine: 0.1.387 shipped seven ES modules,
verified them over HTTP in a harness, and then produced a demo deck with a static
frame and no JavaScript at all. A deliverable is opened from the filesystem, and
**ES modules cannot be imported over file://** — the browser refuses them as
cross-origin. So `<script type="module" src="assets/globe/globe.js">` in a
deliverable does not merely fail to be self-contained; it does not run.

This inlines instead: the modules concatenated in dependency order with their
import and export lines removed, the geometry as JSON, and one call. The result
is a classic script with no fetch, no module graph and no network.

    python3 scripts/build/embed_globe.py > block.html          # runtime + geometry
    python3 scripts/build/embed_globe.py --states '{"europe":"live"}'
    python3 scripts/build/embed_globe.py --no-autorotate
    python3 scripts/build/embed_globe.py --check               # can it build, and is it sane

**SVG back end only.** The canvas back end is for pages where no gate applies,
and it is loaded by dynamic import, which file:// refuses for the same reason.
A deliverable gets the renderer its checks can read.

Pair it with scripts/render/globe_svg.py, which emits the markup this mutates. Without
that markup there is nothing to animate — the runtime never creates elements.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
ASSETS = ROOT / "assets"
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
REGIONS = ROOT / "assets" / "vectors" / "regions.json"

# Dependency order. Concatenation replaces the module graph, so a module must
# appear after everything it names. render-canvas is deliberately absent.
# Paths are relative to assets/: the shared geometry core lives in geo/ (one
# library, two components) and the globe's own modules in globe/.
ORDER = [
    "geo/projection.js",
    "geo/worlddata.js",
    "geo/pick.js",
    "globe/render-svg.js",
    "globe/controls.js",
    "globe/globe.js",
]

# Same-package ('./x.js') and shared-core ('../geo/x.js') imports both strip:
# the concatenation replaces the whole module graph, wherever an edge points.
IMPORT_RE = re.compile(r"^\s*import\s+[^;]*?from\s+'\.\.?/(?:geo/)?[\w-]+\.js';\s*$", re.M)
EXPORT_RE = re.compile(r"^export\s+(?=(?:async\s+)?function|const|class)", re.M)
EXPORT_LIST_RE = re.compile(r"^export\s*\{[^}]*\};\s*$", re.M)


def strip_module_syntax(src: str) -> str:
    src = IMPORT_RE.sub("", src)
    src = EXPORT_LIST_RE.sub("", src)
    src = EXPORT_RE.sub("", src)
    return src


def no_fetch(src: str) -> str:
    """Remove the URL-loading branch from the inlined build.

    globe.js can fetch its geometry when a host gives it URLs. A deliverable
    never does — the geometry is inlined above — so those lines are dead code in
    this build, and dead code that says `fetch` in a file the reader opens from
    their disk is worth deleting rather than explaining. The check below refuses
    to emit a block containing one.
    """
    return src.replace(
        """  try {
    if (!topo) topo = await (await fetch(topologyUrl)).json();
    if (!reg) reg = await (await fetch(regionsUrl)).json();
  } catch (err) {""",
        """  try {
    if (!topo || !reg) {
      throw new Error('the inlined runtime carries its own geometry; '
                      + 'topologyUrl and regionsUrl are not available here');
    }
  } catch (err) {""")


def canvas_stub(src: str) -> str:
    """Replace globe.js's dynamic import of the canvas back end.

    A deliverable has no module loader, and `await import()` throws there rather
    than falling through the try/catch the way a missing file would. Replaced by
    a rejected promise so the existing fallback path runs and says why.
    """
    return src.replace(
        "const mod = await import('./render-canvas.js');",
        "const mod = await Promise.reject(new Error("
        "'the canvas back end is not inlined into deliverables; "
        "see scripts/build/embed_globe.py'));")


TOP_CONST_RE = re.compile(r"^const\s+([A-Za-z_$][\w$]*)\s*=\s*([^;]+);", re.M)


def dedupe_top_consts(name, src, seen):
    """Drop a top-level const a previous module already declared identically.

    Every module is written to stand alone, so projection.js and controls.js both
    declare D2R — correct as modules, a SyntaxError once concatenated, and the
    reader sees a static figure with one line in a console they never open.

    Identical initialisers are dropped. A DIFFERENT initialiser is refused
    outright: silently keeping the first would make one module quietly compute
    with another's constant, which is worse than not shipping.
    """
    out, conflicts = src, []
    for m in TOP_CONST_RE.finditer(src):
        ident, init = m.group(1), m.group(2).strip()
        if ident not in seen:
            seen[ident] = (name, init)
            continue
        prev_mod, prev_init = seen[ident]
        if prev_init != init:
            conflicts.append(f"{ident} is declared in both {prev_mod} and "
                             f"{name} with different values "
                             f"({prev_init!r} vs {init!r})")
            continue
        out = out.replace(m.group(0),
                          f"/* {ident} declared in {prev_mod} */", 1)
    return out, conflicts


def build(autorotate=True):
    seen: dict[str, tuple[str, str]]
    parts, seen, conflicts = [], {}, []
    for name in ORDER:
        path = ASSETS / name
        if not path.exists():
            raise SystemExit(f"FAIL  {path.relative_to(ROOT)} is missing")
        src = path.read_text(encoding="utf-8")
        if name == "globe/globe.js":
            src = no_fetch(canvas_stub(src))
        src, bad = dedupe_top_consts(name, strip_module_syntax(src), seen)
        conflicts += bad
        parts.append(f"/* ── {name} ─────────────────────────────── */\n"
                     + src.strip())
    if conflicts:
        raise SystemExit("FAIL  " + "\n      ".join(conflicts))
    runtime = "\n\n".join(parts)

    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    reg = json.loads(REGIONS.read_text(encoding="utf-8"))

    return f"""<script>
/* LUMI globe runtime — GENERATED by scripts/build/embed_globe.py. Do not edit here.
 *
 * Inlined rather than imported: a deliverable is opened over file://, where the
 * browser refuses ES modules as cross-origin. The SVG back end only; it mutates
 * the markup scripts/render/globe_svg.py emitted and never creates any, so with
 * JavaScript off the reader still gets exactly that frame.
 */
(function () {{
  var TOPOLOGY = {json.dumps(topo, separators=(',', ':'), ensure_ascii=False)};
  var REGISTRY = {json.dumps(reg, separators=(',', ':'), ensure_ascii=False)};
{runtime}

  function boot() {{
    var figures = document.querySelectorAll('[data-globe]');
    for (var i = 0; i < figures.length; i += 1) {{
      // Marks are read from the markup globe_svg.py --marks baked in; the
      // host data the old block carried was region states, and regions belong
      // to the region map component now.
      createGlobe(figures[i], {{
        topology: TOPOLOGY,
        registry: REGISTRY,
        autorotate: {str(bool(autorotate)).lower()},
      }});
    }}
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', boot);
  }} else {{
    boot();
  }}
}})();
</script>"""


def check():
    errors = []
    try:
        block = build()
    except SystemExit as exc:
        print(exc)
        return 1
    # The three failures this can have that would not be visible until a reader
    # opened the file: a module left behind an import the concatenation cannot
    # satisfy, an export keyword that makes a classic script a syntax error, or
    # a fetch that file:// would refuse.
    body = block[block.index("<script>"):]
    for pat, why in (
        (r"^\s*import\s", "an unresolved import survived the strip"),
        (r"^export\s", "an export keyword survived the strip"),
        (r"\bawait import\(", "a dynamic import survived; file:// refuses it"),
        (r"\bfetch\(", "a fetch survived; a deliverable has nothing to fetch from"),
    ):
        for m in re.finditer(pat, body, re.M):
            line = body[:m.start()].count("\n") + 1
            errors.append(f"line {line}: {why}")
    for name in ORDER:
        if f"── {name} ─" not in block:
            errors.append(f"{name} is not in the block")
    if "createGlobe" not in block:
        errors.append("createGlobe is not defined in the block")
    # A duplicate top-level declaration is a SyntaxError, and a SyntaxError in a
    # deliverable is invisible: the static frame renders and nothing moves.
    decls: dict[str, int] = {}
    # No leading whitespace: top level means column zero. Allowing indentation
    # matched every local inside every function and reported eleven collisions
    # that do not exist — a check that cannot read scope is noise.
    for m in re.finditer(r"^(?:const|let|function)\s+([A-Za-z_$][\w$]*)",
                         body, re.M):
        decls[m.group(1)] = decls.get(m.group(1), 0) + 1
    for ident, n in sorted(decls.items()):
        if n > 1:
            errors.append(f"{ident} is declared {n} times at top level; "
                          f"concatenation makes that a SyntaxError")
    for e in errors[:10]:
        print(f"FAIL  {e}")
    if not errors:
        print(f"ok    globe runtime inlines cleanly "
              f"({len(block) // 1024} KB, {len(ORDER)} modules, SVG back end)")
    return 1 if errors else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # --form and --states retired with the component split: regions and their
    # states belong to scripts/build/embed_regionmap.py, and the globe's marks are
    # baked into the frame by globe_svg.py --marks rather than passed here.
    ap.add_argument("--no-autorotate", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.check:
        return check()
    print(build(autorotate=not args.no_autorotate))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
