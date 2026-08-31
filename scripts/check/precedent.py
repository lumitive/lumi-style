#!/usr/bin/env python3
"""Has this been tried, and was it refused? — step zero for any new mechanism.

**Why this exists, measured.** On 2026-09-01 a design proposed extending a
cross-boundary guard from Python to markdown. That mechanism had been declined
in writing on 2026-08-23 as `FM-23`, with a reason and a counterexample, and the
design did not mention it — because its author never looked. One keyword search
finds it. In the same session AG-10's shape was re-committed twice.

Overruling a written refusal is legitimate and needs convention 2's documented
case. Overruling one **without noticing it exists** is FM-15, and it is the
cheapest defect in this repository to prevent: the refusals are 37 structured
headings in two files.

    python3 scripts/check/precedent.py prose cross-boundary
    python3 scripts/check/precedent.py --body scatter figure

By default it searches the HEADINGS of `FAILURE_MODES.md` (failure modes and
abandoned gates) and `KNOWN_GAPS.md`. `--body` widens to the entries' text,
which is noisier and catches a mechanism described but not named.

It prints and never fails a run: deciding whether a hit is the same mechanism is
a person's judgement, and AG-1 declined the class of guard that decides such
things mechanically. What it removes is the excuse of not having looked.

Standard library only.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# id + title, and the paragraph under it. Both ledgers use `## <ID> · <title>`.
ENTRY = re.compile(r"^## ((?:FM|AG|GAP|IDEA)-\d+)\s*.\s*(.+)$", re.M)

SOURCES = ("FAILURE_MODES.md", "KNOWN_GAPS.md", "backlog/ideas-prd.md")


def entries(root: pathlib.Path | None = None):
    """-> [(id, title, body, source)] over every ledger that carries refusals.

    Returns the empty list only when no ledger could be read, which the caller
    reports rather than treating as "nothing has ever been refused" — the
    distinction FM-24 exists for.
    """
    # Resolved at CALL time, not at definition. `root=ROOT` in the signature
    # binds the module value once, so a caller that changes ROOT — a test, or a
    # run against another checkout — silently searches the wrong tree and
    # reports "no precedent found". A search of the wrong tree that reads as a
    # clean bill is this file's own subject matter.
    root = ROOT if root is None else root
    out = []
    for name in SOURCES:
        path = root / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # WHERE the entry sits decides what it means. FAILURE_MODES.md holds
        # two halves under one heading style: recorded failure modes, and —
        # after `# Abandoned gates` — mechanisms DECLINED with their reasons.
        # An `FM-` id below that line is a refusal, and calling it "a recorded
        # failure mode" is exactly the under-reading this tool exists to stop:
        # FM-23, the one that prompted this file, lives there.
        cut = text.find("\n# Abandoned gates")
        marks = list(ENTRY.finditer(text))
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            refused = cut != -1 and m.start() > cut
            out.append((m.group(1), m.group(2).strip(),
                        text[m.end():end], name, refused))
    return out


def search(terms, body=False, root: pathlib.Path | None = None):
    """-> the entries whose title (or body, with `body=True`) carries a term."""
    found = []
    for eid, title, text, src, refused in entries(root):
        hay = f"{title}\n{text}" if body else title
        hits = [t for t in terms if re.search(re.escape(t), hay, re.I)]
        if hits:
            found.append((eid, title, src, hits, refused))
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("terms", nargs="+", metavar="TERM",
                    help="words describing the mechanism you are about to design")
    ap.add_argument("--body", action="store_true",
                    help="search the entries' text too, not only their titles")
    a = ap.parse_args(argv)

    all_entries = entries()
    if not all_entries:
        print("could not read any ledger — this is a failed search, not an "
              "absence of precedent", file=sys.stderr)
        return 1

    hits = search(a.terms, body=a.body)
    scope = "title+body" if a.body else "title"
    print(f"searched {len(all_entries)} ledger entries ({scope}) "
          f"for {', '.join(a.terms)}")
    if not hits:
        print("  no precedent found.")
        print("  NOT a clean bill: a mechanism described in other words is "
              "still a mechanism that was refused. Try --body, and try the "
              "words the OTHER side would have used.")
        return 0
    print()
    for eid, title, src, matched, refused in hits:
        kind = ("REFUSED — read it before designing further" if refused else
                {"AG": "REFUSED — read it before designing further",
                 "FM": "a recorded failure mode",
                 "GAP": "an open gap",
                 "IDEA": "deferred work"}[eid.split("-")[0]])
        print(f"  {eid} · {title}")
        print(f"      {kind}  ({src}; matched {', '.join(matched)})")
    print()
    print("  Overruling a written refusal is legitimate and needs a documented")
    print("  case (CLAUDE.md convention 2). Overruling one without citing it")
    print("  is FM-15.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
