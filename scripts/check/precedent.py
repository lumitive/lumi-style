#!/usr/bin/env python3
"""Has this been tried, and was it refused? — step zero for any new mechanism.

**Why this exists, measured.** On 2026-09-01 a design proposed extending a
cross-boundary guard from Python to markdown. That mechanism had been declined
in writing on 2026-08-23 as `FM-23`, with a reason and a counterexample, and the
design did not mention it — because its author never looked. One keyword search
finds it. In the same session AG-10's shape was re-committed twice.

Overruling a written refusal is legitimate and needs convention 2's documented
case. Overruling one **without noticing it exists** is FM-15, and it is the
cheapest defect in this repository to prevent: every refusal is a structured
heading in a ledger, and `SOURCES` below says which ledgers. How many there are
is whatever they hold today, never a number written here.

    python3 scripts/check/precedent.py prose cross-boundary
    python3 scripts/check/precedent.py --body scatter figure

By default it searches the HEADINGS of every ledger in `SOURCES`. `--body`
widens to the entries' text, which is noisier and catches a mechanism described
but not named.

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

# id and title only; the body is sliced by index in `entries()`. Every ledger
# in SOURCES uses `## <ID> · <title>`.
ENTRY = re.compile(r"^## ((?:FM|AG|GAP|IDEA)-\d+)\s*.\s*(.+)$", re.M)

SOURCES = ("FAILURE_MODES.md", "KNOWN_GAPS.md", "backlog/ideas-prd.md")


def entries(root: pathlib.Path | None = None):
    """-> [(id, title, body, source, refused)] over every ledger in SOURCES.

    **Raises `ValueError` when any ledger could not be read or yielded no
    entries at all.** It used to `continue` past an unreadable file, so losing
    `FAILURE_MODES.md` alone still returned the other two ledgers' entries and
    the tool printed "no precedent found" over a corpus missing every refusal
    in it. A partial search that reads as a complete one is the defect this
    file exists to prevent, one layer up: the caller must be able to tell a
    search that found nothing from a search that did not happen.
    """
    # Resolved at CALL time, not at definition. `root=ROOT` in the signature
    # binds the module value once, so a caller that changes ROOT — a test, or a
    # run against another checkout — silently searches the wrong tree and
    # reports "no precedent found". A search of the wrong tree that reads as a
    # clean bill is this file's own subject matter.
    root = ROOT if root is None else root
    out, per_source = [], {}
    for name in SOURCES:
        path = root / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"{name} could not be read ({exc}); a search "
                             f"missing a whole ledger is not a search") from exc
        # WHAT THE ENTRY SAYS decides what it is, never where it sits. This
        # keyed on the `# Abandoned gates` heading until 0.1.666 and was wrong
        # about four entries out of eighteen: FM-20, FM-21, FM-22 and FM-24 are
        # filed below that heading and are RECORDED FAILURE MODES — FM-24 is
        # "the check that printed a clean result because it could not look" —
        # so the tool printed "REFUSED — read it before designing further" over
        # all four. A marker that fires on almost every input carries no
        # information, and an author who learns to ignore it learns to ignore
        # FM-23 with it.
        #
        # Read against the material instead (convention 15): every `AG-` id is
        # an abandoned gate by construction, and a declined `FM-` says DECLINED
        # in its own body with a date and a reason. Measured on this ledger:
        # 14 AG entries and 4 declined FM entries, against 4 failure modes that
        # position alone had mislabelled.
        marks = list(ENTRY.finditer(text))
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            body = text[m.end():end]
            refused = m.group(1).startswith("AG-") or "DECLINED" in body
            out.append((m.group(1), m.group(2).strip(), body, name, refused))
        per_source[name] = len(marks)
    empty = [n for n, c in per_source.items() if not c]
    if empty:
        raise ValueError(
            f"{', '.join(empty)} parsed but yielded no entries — either the "
            f"ledger is empty or ENTRY has stopped matching its headings. A "
            f"source contributing nothing is not a source agreeing with you.")
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

    try:
        all_entries = entries()
        hits = search(a.terms, body=a.body)
    except ValueError as exc:
        print(f"the search did not run: {exc}", file=sys.stderr)
        print("This is a FAILED search, not an absence of precedent.",
              file=sys.stderr)
        return 1
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
                {"FM": "a recorded failure mode",
                 "AG": "a recorded failure mode",
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
