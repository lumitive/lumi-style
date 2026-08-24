#!/usr/bin/env python3
"""Everything SKILL.md tells you to read before composing, in one command.

**It does not change WHAT you read. It changes how many round trips it costs.**

SKILL.md names, by line, eleven to fourteen files to open before the first page
is written: `brand.md`, the chosen storyline template, `design-rules.md`,
`page-contracts.md`, `analysis-rules.md`, an exemplar note, `writing-rules.md`,
the three token files, `frameworks.json`, the shape tags, and the build card.
Measured on one build, that was **20 API calls and 82,000 output tokens before
a single page existed** — and 84 KB of it was fetched twice by two different
tools in adjacent calls.

The card's own warning stands and is repeated at the end of this output: **the
references are what give you something to say.** This concatenates them; it
does not summarise them, and it is not a substitute for reading. What it
removes is the eleven separate fetches.

    python3 scripts/ops/brief.py --genre internal --storyline market-analysis
    python3 scripts/ops/brief.py --genre sales --storyline pitch-deck --full

Without `--full` the two longest files (`design-rules.md`, `page-contracts.md`)
are replaced by their section index plus the build card, which is the decidable
half of both. `--full` sends everything, which is what a first build wants.
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import argparse  # noqa: E402
import pathlib  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402

from deliverable_registry import GENRES, STORYLINES  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())

# In the order SKILL.md names them. `brand.md` first in every load order.
ALWAYS = (
    "references/brand.md",
    "references/analysis-rules.md",
    "references/writing-rules.md",
    "references/build-card.md",
)
LONG = ("references/design-rules.md", "references/page-contracts.md")
EXEMPLAR = "references/exemplars/mckinsey-design-notes.md"
PITCH_EXEMPLAR = "references/exemplars/yc-pitch-notes.md"


def _section_index(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines()
                     if re.match(r"^#{1,3} ", ln))


def _storyline_slice(text: str, storyline: str) -> str:
    """-> the one template for this storyline, or the whole file if unfound.

    Falling back to the whole file rather than to nothing: a missing slice is a
    reason to send more, never a reason to send less than the rule asks for.
    """
    m = re.search(rf"^#{{1,3}} .*`?{re.escape(storyline)}`?.*$", text, re.M | re.I)
    if not m:
        return text
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.start():m.end() + (nxt.start() if nxt else len(text))]


def brief(genre: str, storyline: str | None, full: bool) -> str:
    """-> the whole brief as one string, for a caller that can take it."""
    return "".join(body for _label, body in brief_parts(genre, storyline, full))


def brief_parts(genre: str, storyline: str | None,
                full: bool) -> list[tuple[str, str]]:
    """-> [(label, text)] — the brief in the pieces it is already made of.

    `brief()` joins these. The split exists because the joined form is tens of
    kilobytes — the manifest prints the real sizes, and a number written here
    would be a fourth copy that rots (convention 13) — and a harness with a
    single-output ceiling truncates it to a 2KB preview:
    the tool built to save a round trip cost five (run it, probe the file,
    fail a Read on the token ceiling, then read it in two halves). Measured at
    0.1.591. `--out` writes the parts and prints only the manifest.

    The labels are the section headers the joined form already carries, so the
    two cannot drift into naming different things.
    """
    parts: list[tuple[str, str]] = []

    def add(label: str, text: str) -> None:
        parts.append((label, text))

    out = [f"# LUMI build brief · genre={genre}"
           + (f" · storyline={storyline}" if storyline else "")]
    out.append("\nEverything SKILL.md asks you to read before composing, "
               "fetched once. Read it; it is not a summary.\n")
    for rel in ALWAYS:
        p = ROOT / rel
        if p.is_file():
            out.append(f"\n\n{'=' * 70}\n== {rel}\n{'=' * 70}\n")
            out.append(p.read_text(encoding="utf-8"))
    if storyline:
        p = ROOT / "references/storyline-templates.md"
        if p.is_file():
            body = p.read_text(encoding="utf-8")
            out.append(f"\n\n{'=' * 70}\n== references/storyline-templates.md "
                       f"— the {storyline} template\n{'=' * 70}\n")
            out.append(_storyline_slice(body, storyline))
    ex = PITCH_EXEMPLAR if storyline == "pitch-deck" else EXEMPLAR
    if (ROOT / ex).is_file():
        out.append(f"\n\n{'=' * 70}\n== {ex}\n{'=' * 70}\n")
        out.append((ROOT / ex).read_text(encoding="utf-8"))
    for rel in LONG:
        p = ROOT / rel
        if not p.is_file():
            continue
        body = p.read_text(encoding="utf-8")
        if full:
            out.append(f"\n\n{'=' * 70}\n== {rel}\n{'=' * 70}\n{body}")
        else:
            out.append(f"\n\n{'=' * 70}\n== {rel} — section index only "
                       f"(pass --full for the file)\n{'=' * 70}\n"
                       + _section_index(body))
    out.append("\n\n" + "=" * 70 + "\n")
    out.append(
        "The build card above is the decidable half. It is not the rules, and "
        "an agent that composes from it alone produces a document that passes "
        "every gate and says nothing — which is what five conformance rounds "
        "produced. The rest of this brief is what gives you something to say.\n"
        "\nShape geometry, when you place labels: assets/shapes/geometry.json "
        "carries every unit's viewBox, its `use` attributes and its aspect. "
        "All 206 origins are non-zero; composing against an estimated one "
        "draws outside the viewBox, which is `figure_clipped` and a rebuild "
        "round.\n")
    # CUT WHERE THE JOINED FORM ALREADY CUTS. Each `== <name>` banner starts a
    # section; the text before the first is the preamble. Splitting the buffer
    # the builder produced — rather than assembling it a second way — is what
    # keeps `--out` and stdout from ever disagreeing about the bytes.
    whole = "".join(out)
    chunks = re.split(r"(?m)^={70}\n== (.+)\n={70}\n", whole)
    add("preamble", chunks[0])
    for i in range(1, len(chunks) - 1, 2):
        add(chunks[i].strip(),
            "=" * 70 + f"\n== {chunks[i]}\n" + "=" * 70 + "\n" + chunks[i + 1])
    return parts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--genre", choices=list(GENRES), required=True)
    ap.add_argument("--storyline", choices=list(STORYLINES))
    ap.add_argument("--out", type=pathlib.Path, metavar="DIR",
                    help="write the brief as numbered parts in DIR and print "
                         "only the manifest. Use it on any harness with a "
                         "single-output ceiling; the manifest prints the real sizes.")
    ap.add_argument("--full", action="store_true",
                    help="send design-rules.md and page-contracts.md whole "
                         "rather than their section index")
    a = ap.parse_args(argv)
    if a.out is None:
        sys.stdout.write(brief(a.genre, a.storyline, a.full))
        return 0
    a.out.mkdir(parents=True, exist_ok=True)
    # A REUSED DIRECTORY MIXES TWO BRIEFS AND SAYS "9 parts". The part names
    # carry the section they hold, so a different genre, storyline or --full
    # writes a DIFFERENT set of names beside the old ones: two storyline
    # templates, two exemplars, and a full design-rules.md sitting next to the
    # stub that says "section index only". The manifest still says 9, the
    # directory holds 13, the exit code is 0, and the footer tells the reader
    # to read them in order.
    stale = sorted(a.out.glob("*.md"))
    for old_part in stale:
        old_part.unlink()
    written = []
    for i, (label, body) in enumerate(brief_parts(a.genre, a.storyline, a.full)):
        stem = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:60] or "part"
        path = a.out / f"{i:02d}-{stem}.md"
        path.write_text(body, encoding="utf-8")
        written.append((path, len(body)))
    if stale:
        print(f"replaced {len(stale)} part(s) from a previous brief in {a.out}")
    print(f"brief written in {len(written)} parts to {a.out}")
    for path, n in written:
        print(f"  {n:>7,}  {path.name}")
    print("\n  Read them in this order. They are the same bytes stdout would "
          "have carried;\n  the split exists because one write of the whole "
          "is a truncated preview on a harness\n  with an output ceiling, and a "
          "truncated brief is worse than none.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
