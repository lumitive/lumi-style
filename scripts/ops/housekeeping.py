#!/usr/bin/env python3
"""Keep the delivery folder a folder of deliverables.

`inspect_layout.py` renders every page of a document at 4K to look at it, and
`export_pdf.py` does the same for print. Those files are **renders, not
records**: they are reproducible from the document in seconds and they carry no
information the document does not. Left beside the deliverables they measure,
they took the owner's delivery folder to 5,834 rasters and 1.0GB by 2026-08-18,
and — after a cleanup and a standing order not to put them there — to 2,164 and
349MB again by 2026-08-21, a fortnight later.

The second recurrence is the reason this file exists rather than a calendar
reminder. **A rule that has been written down and then broken does not need
writing more firmly; it needs a tool that holds it** (CLAUDE.md convention 16,
which produced `release.py` on the same reasoning). Two things hold it:

* `inspect_layout.default_sheet_dir` now writes to the system temp directory,
  so the renders are never created in the delivery folder in the first place.
  That is the fix.
* `--check` here fails when any turn up anyway — a `--out` pointed at the
  folder, an older build of this package, another tool. That is the guard, and
  it exists because the fix above is one flag away from being bypassed.

**What it will never delete.** Anything that is not a render: documents, PDFs,
sources, the corpus registry's files, this package's own conformance runs. The
retention policy for *documents* — which superseded build of a family to keep —
is the owner's and is not encoded here. This tool knows one rule: a page raster
and a contact sheet can be made again, so they do not need keeping.

    python3 scripts/ops/housekeeping.py            # what is there
    python3 scripts/ops/housekeeping.py --check    # exit 1 if any render is there
    python3 scripts/ops/housekeeping.py --apply    # delete them (renders only)

`--check` is safe in CI and in preflight: a machine with no delivery folder has
nothing to check and says so, rather than inventing a failure or a pass.
"""
from __future__ import annotations

import argparse
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
# --- end bootstrap ---
import output_dir  # noqa: E402 — after the bootstrap

# A render is one of these and nothing else. Deliberately narrow: this list is
# the whole authority for what may be deleted, so a category nobody has thought
# about stays untouched rather than being swept up by a wildcard.
RASTER_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
# The contact sheet is HTML, which is also what a deliverable is. The infix is
# what tells them apart, and it comes from inspect_layout's own naming:
# `<stem>-sheet-<geometry>-<palette>.html`. Matching on ".html" alone would
# propose deleting the documents themselves.
SHEET_INFIX = "-sheet-"
# THE INPUT TREE IS NOT AN OUTPUT TREE. `_sources/` holds what documents are
# BUILT FROM, and some of that is images: the 2026-08-18 cleanup kept two
# thumbnails under `_sources/adopting-16x9/thumbs/` because a recipe reads them.
# The first run of this tool against the real folder proposed exactly those two
# and nothing else, which is the whole argument for looking at the material
# before shipping a pattern that keys on its shape (CLAUDE.md convention 15).
# A raster is a render because of WHERE it is, not only what it is.
INPUT_DIRS = ("_sources",)


def is_render(path: pathlib.Path) -> bool:
    """Is this file reproducible from a document by re-rendering it?

    Three tests, and the order matters. Nothing under an input directory is a
    render whatever it looks like. A raster anywhere else is one, because this
    package delivers no PNG. An HTML file is one only when it carries
    inspect_layout's sheet infix, because every deliverable this package makes
    is also HTML and a rule that got that wrong would propose deleting the work.
    """
    if not path.is_file():
        return False
    if any(part in INPUT_DIRS for part in path.parts):
        return False
    if path.suffix.lower() in RASTER_SUFFIXES:
        return True
    return path.suffix.lower() == ".html" and SHEET_INFIX in path.name


def renders_in(root: pathlib.Path) -> list[pathlib.Path]:
    """Every render under `root`, newest first. Symlinks are not followed —
    a link into a checkout would walk this package's own tracked assets."""
    found: list[tuple[float, pathlib.Path]] = []
    for p in root.rglob("*"):
        try:
            if p.is_symlink() or not is_render(p):
                continue
            found.append((p.stat().st_mtime, p))
        except OSError:
            continue
    found.sort(reverse=True)
    return [p for _, p in found]


def _human(size: float) -> str:
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}GB"


def size_of(paths: list[pathlib.Path]) -> int:
    total = 0
    for p in paths:
        try:
            total += p.stat().st_size
        except OSError:
            continue
    return total


def resolve_folder() -> tuple[pathlib.Path | None, str]:
    """-> (the delivery folder, why it is None).

    Never creates it: `output_dir.py --create` is the one place authorized to,
    by the 2026-08-09 directive, and a housekeeping tool that makes the folder
    it tidies would be absurd.
    """
    try:
        folder = output_dir.output_dir()
    except output_dir.Unresolvable as exc:
        return None, f"the delivery folder cannot be located ({exc})"
    if not folder.is_dir():
        return None, f"{folder} does not exist on this machine"
    return folder, ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when the delivery folder holds any render")
    ap.add_argument("--apply", action="store_true",
                    help="delete the renders it lists. Renders only — never a "
                         "document, a PDF or a source")
    args = ap.parse_args(argv)

    folder, why = resolve_folder()
    if folder is None:
        # NOT A FAILURE AND NOT A PASS-BY-LUCK. CI has no delivery folder, and a
        # guard that failed there would be red on every machine that is not the
        # owner's; one that printed "ok" would be claiming it had looked.
        print(f"skip  {why}; nothing to check here")
        return 0

    found = renders_in(folder)
    if not found:
        print(f"ok    {folder}: no renders — every file in it is a record")
        return 0

    total = size_of(found)
    print(f"{'FAIL' if args.check else 'note'}  {folder}: {len(found)} render(s), "
          f"{_human(total)}")
    by_dir: dict[pathlib.Path, int] = {}
    for p in found:
        by_dir[p.parent] = by_dir.get(p.parent, 0) + 1
    for d, n in sorted(by_dir.items(), key=lambda kv: -kv[1])[:8]:
        try:
            shown = d.relative_to(folder)
        except ValueError:                                  # pragma: no cover
            shown = d
        print(f"        {n:>5}  {shown or '.'}")
    print("        they are reproducible from the document; "
          "inspect_layout writes to the temp directory unless --out says otherwise")

    if args.apply:
        removed = 0
        for p in found:
            try:
                p.unlink()
                removed += 1
            except OSError as exc:
                print(f"        could not remove {p}: {exc}")
        print(f"ok    removed {removed} render(s), {_human(total)} reclaimed")
        return 0
    if args.check:
        return 1
    print("        run with --apply to remove them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
