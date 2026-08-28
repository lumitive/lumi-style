#!/usr/bin/env python3
"""The package's own version, the release list, and the order they sort in.

WHY THIS MODULE EXISTS. Seven functions read SKILL.md's stamp with five
different regexes and three different failure behaviours, and they disagreed on
a real document: given a SKILL.md carrying another `*_version:` key above the
stamp, the unanchored ones return the NEIGHBOUR's value and the anchored ones
return the stamp — one file, two answers. Failure diverged too — `SystemExit`,
the string `"unknown"`, and an uncaught `IndexError` from a `.split()` — and
`"unknown"` was not inert: it was written into a trace's `skill_version`, which
is what the ordering functions below then had to compare.

The regex kept here is the strictest of the seven, the only one that cannot
match a neighbouring key: anchored to the start of a line, and closed by the
quote.

THREE QUESTIONS, NOT ONE, and the difference is the point rather than an
accident of history:

* `ver_key` RAISES on a string that is not a version. `gate_registry.held`
  needs that: it catches the error and answers "held", because an unparseable
  stamp must not become an exemption. A tolerant key would have made the
  comparison `() >= (0, 1, 449)` — False — and quietly exempted the document.
* `sort_key` never raises and sorts an unparseable version LOWEST. Ordering a
  board's cells needs that: a trace with no version belongs at the bottom, not
  in a traceback.
* `skill_version_in` answers about TEXT rather than about this tree, because
  the published package's SKILL.md arrives over the network and is not a file
  here at all.

`releases_between` is SIGNED, and the orientation is named: the CHANGELOG is
newest-first, so a positive answer means `older` sits that many releases behind
`newer`. The two implementations this replaces differed by exactly that — one
returned the signed distance and the other its absolute value — which is a
difference no caller could have seen from either name.
"""
import pathlib
import re

SKILL_STAMP = re.compile(r'^\s*version:\s*"(\d+\.\d+\.\d+)"', re.M)
RELEASE_HEADING = re.compile(r"^##\s+(\d+\.\d+\.\d+)", re.M)
RELEASE_HEADING_FULL = re.compile(r"^##\s+(\d+\.\d+\.\d+) — (.+)$", re.M)


def _root(root: pathlib.Path | None = None) -> pathlib.Path:
    if root is not None:
        return root
    return next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / "SKILL.md").exists())


def skill_version_in(text: str) -> str | None:
    """-> the version this SKILL.md text stamps, or None.

    Text rather than a path, because `release.py` asks the same question of the
    published package's SKILL.md, fetched over the API and never written down.
    """
    m = SKILL_STAMP.search(text)
    return m.group(1) if m else None


def skill_version(root: pathlib.Path | None = None) -> str:
    """-> the version SKILL.md declares here. Raises if it does not.

    One failure behaviour, chosen in the open. A tree whose SKILL.md carries no
    stamp is broken in a way no caller can paper over, and the two callers that
    used to paper over it wrote `"unknown"` into records that were later
    compared as versions.
    """
    v = skill_version_in((_root(root) / "SKILL.md").read_text(encoding="utf-8"))
    if v is None:
        raise SystemExit("FAIL  SKILL.md carries no metadata.version")
    return v


def ver_key(version: str) -> tuple[int, ...]:
    """-> a sortable version. Raises ValueError on anything else.

    The strict one. `max()` over version STRINGS is lexicographic, so `0.1.99`
    outranks `0.1.100`; every comparison of two versions goes through here or
    through `sort_key`.
    """
    return tuple(int(p) for p in version.split("."))


def sort_key(version: str | None) -> tuple[int, ...]:
    """-> a sortable version, tolerantly: unparseable sorts lowest.

    For ordering a list that may contain a record with no version. Never use it
    to decide whether a rule BINDS — that is `ver_key`, whose caller catches the
    error and refuses the exemption.
    """
    try:
        return ver_key(version or "")
    except ValueError:
        return ()


def releases(root: pathlib.Path | None = None,
             text: str | None = None) -> list[str]:
    """-> every released version, newest first, from the CHANGELOG headings."""
    if text is None:
        text = (_root(root) / "CHANGELOG.md").read_text(encoding="utf-8")
    return RELEASE_HEADING.findall(text)


def newest_heading(root: pathlib.Path | None = None,
                   text: str | None = None) -> tuple[str, str] | None:
    """-> the newest release heading as (version, summary), or None.

    The summary matters to `release.py`, which holds the commit subject to it,
    so the em dash is REQUIRED here where `releases()` does not require it: a
    heading without one has no summary to return.
    """
    if text is None:
        text = (_root(root) / "CHANGELOG.md").read_text(encoding="utf-8")
    m = RELEASE_HEADING_FULL.search(text)
    return (m.group(1), m.group(2)) if m else None


def releases_between(older: str | None, newer: str | None,
                     root: pathlib.Path | None = None) -> int | None:
    """-> how many release headings separate two versions, or None.

    SIGNED: positive means `older` is that many releases behind `newer`. A
    caller that only wants the distance takes `abs`.

    Counted from the CHANGELOG rather than from git or from arithmetic on the
    patch number: the published projection's commits are rewritten, so their
    hashes cannot be compared to this repository's, and the distance that
    matters is how many rule revisions have landed rather than how far apart
    two integers are.

    `root` because this is `check_repo`'s arithmetic too, and a shared function
    that hard-codes its own ROOT is not shared — one implementation read the
    board from one tree and the CHANGELOG from another.
    """
    if not older or not newer:
        return None
    try:
        found = releases(root)
    except OSError:
        return None
    if older not in found or newer not in found:
        return None
    return found.index(older) - found.index(newer)
