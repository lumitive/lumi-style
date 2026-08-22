#!/usr/bin/env python3
"""Emit the @font-face block for the vendored display face, fonts inlined.

design-rules.md requires the face to be embedded, not linked: a deliverable that
references a font by URL renders in a fallback the moment it is opened offline,
emailed, or printed from a machine that never fetched it. Version 1.2 shipped
with the face declared but not vendored and it rendered nothing at all, which is
why the woff2 files now live in this repository instead of being found again for
every deck.

    python3 scripts/build/embed_font.py            # print the CSS block
    python3 scripts/build/embed_font.py --check    # verify the vendored files are intact

Paste the output into the deliverable's <style>. Roughly 56 KB of base64 for the
display pair and 45 KB for the mono pair, which is the whole cost of never
thinking about fonts again.
"""

import base64
import hashlib
import pathlib
import sys

FONTS = next(p for p in pathlib.Path(__file__).resolve().parents
             if p.name == "scripts").parent / "assets" / "fonts"
# (file, family, weight). The family is carried per face because this package
# now ships TWO: the display face and the data voice.
FACES = [
    ("D-DIN.woff2", "D-DIN", 400),
    ("D-DIN-Bold.woff2", "D-DIN", 700),
    # THE DATA VOICE, vendored 2026-08-22. `--mono` named "IBM Plex Mono",
    # "SF Mono", Menlo and Consolas and this package embedded NONE of them, so
    # every caption, footer, colophon and cover key column in every deliverable
    # rendered in whatever mono the reader's machine happened to have — and
    # whatever that face called 700, often a synthesised bold. An owner review
    # read the cover's key column as "not bold" twice, five releases apart, on
    # a rule that measures as weight 700 both times. design-rules §2 has said
    # since v1.2 that a Latin face is embedded and never linked; the display
    # face obeyed it and the data voice was hoped for.
    ("IBMPlexMono-Regular.woff2", "IBM Plex Mono", 400),
    ("IBMPlexMono-Bold.woff2", "IBM Plex Mono", 700),
]

# Recorded when the files were vendored. A mismatch means the font changed, which
# would silently alter every deliverable's metrics.
EXPECTED = {
    "D-DIN.woff2": 20744,
    "D-DIN-Bold.woff2": 22052,
    "IBMPlexMono-Regular.woff2": 16624,
    "IBMPlexMono-Bold.woff2": 17048,
}


def check():
    problems = []
    for name, size in EXPECTED.items():
        path = FONTS / name
        if not path.is_file():
            problems.append(f"missing: {path}")
            continue
        actual = path.stat().st_size
        if actual != size:
            problems.append(f"{name}: {actual} bytes, expected {size}")
    if not (FONTS / "COPYING.txt").is_file():
        problems.append("missing: COPYING.txt — the OFL requires it to ship alongside")
    for problem in problems:
        print(f"FAIL  {problem}", file=sys.stderr)
    if not problems:
        for name in EXPECTED:
            digest = hashlib.sha256((FONTS / name).read_bytes()).hexdigest()[:16]
            print(f"ok    {name}  sha256:{digest}")
    return 1 if problems else 0


def css():
    """The @font-face block as a string, for callers that build documents.

    new_deck.py inlines this into every scaffold: two 0.1.442-era deliverables
    shipped with zero @font-face blocks and fell back to the system stack,
    because embedding was a separate step an author had to remember.
    """
    out = []
    for name, family, weight in FACES:
        data = base64.b64encode((FONTS / name).read_bytes()).decode("ascii")
        out.append(
            f"@font-face{{font-family:'{family}';font-style:normal;"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
        )
    return "\n".join(out)


def emit():
    print(css())
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else emit())
