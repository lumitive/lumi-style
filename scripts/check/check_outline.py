#!/usr/bin/env python3
"""Check a storyline outline before anything is built.

The fourth beat of the discussion path is a storyline review: titles, order and
the logic joining them, agreed before the document exists. That beat is **the
only defence completeness has** — C5 reports and never gates, so a missing
section is caught here or not at all. This script is the machine half of that
beat; the argument itself stays a person's.

**What it decides**

- **Topic-label titles.** "Market overview" names a subject and asserts
  nothing. A title that carries no verb and no figure is a label, and a deck of
  labels cannot read as an argument no matter how good the pages are.
- **Group size.** A group of one is not a group, and a group of eight is a list
  the reader has to sort themselves. Two to five, and the reviewer should be
  able to state the ordering logic — the second half is theirs.
- **Completeness, reported.** Sections the storyline typically carries and this
  outline does not name. **An outline may declare an omission** with
  `omitted: <section> — <reason>`, which is the distinction between having
  forgotten a section and having decided against it.

**What it deliberately refuses to decide**

The read-through: whether the titles in order are an argument. It prints them
in order so a person can read them as one paragraph, and says nothing about
whether they cohere. That judgement is the whole point of the beat and a
checker pretending to make it would replace the beat rather than serve it.

It also does not decide section existence by matching headings loosely: the
checklist is compared against what the outline **names**, and every regulator
that mandates structure mandates the declaration rather than the name.

That comparison is a substring match against the titles, and an author who
wanted to could satisfy it by putting a section's name in a title that is not
about it. **That is exactly why it is reported and not gated**: gaming a
reported line costs the author effort and buys them nothing, while gaming a
gate buys them a green run. A completeness gate would be worth defeating.

**Format** — markdown, written by whoever is running the beat:

    genre: consulting
    storyline: market-analysis

    ## Where the market is going
    - Demand grew 12% while capacity grew 3%
    - Three segments carry that growth, and one is closing

    omitted: competitive landscape — commissioned separately

Usage
  check_outline.py outline.md
  check_outline.py outline.md --json
"""
from __future__ import annotations

import argparse
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import re
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

from deliverable_registry import (  # noqa: E402 — after the bootstrap
    GENRES,
    STORYLINES,
    TYPICAL_SECTIONS,
)

GROUP_MIN, GROUP_MAX = 2, 5

# A title asserts something if it has a verb or a figure. This is the same
# question M1 asks of a built document, asked early enough to be cheap to fix.
VERBISH = re.compile(
    r"\b(is|are|was|were|has|have|will|can|cannot|must|should|does|do|"
    r"grew|grow|fell|fall|rose|rise|beats?|costs?|needs?|closes?|stops?|"
    r"stopped|carries|carry|leads?|drives?|misses?|holds?|breaks?|wins?|"
    r"loses?|shifts?|moves?|keeps?|adds?|cuts?|doubles?|halves?)\b", re.I)
FIGURE = re.compile(r"\d")
QUESTION = re.compile(r"\?\s*$")


def parse(text: str):
    """-> (meta, groups, omissions). A group is (heading, [titles])."""
    meta: dict[str, str] = {}
    groups: list[tuple[str, list[str]]] = []
    omissions: list[dict[str, str]] = []
    current: tuple[str, list[str]] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(genre|storyline)\s*:\s*(\S+)", line, re.I)
        if m:
            meta[m.group(1).lower()] = m.group(2)
            continue
        m = re.match(r"^omitted\s*:\s*(.+)$", line, re.I)
        if m:
            body = m.group(1)
            name, _, reason = body.partition("—")
            omissions.append({"section": name.strip().lower(),
                              "reason": reason.strip()})
            continue
        if line.startswith("#"):
            current = (line.lstrip("#").strip(), [])
            groups.append(current)
            continue
        if line.startswith(("- ", "* ")):
            if current is None:
                current = ("(ungrouped)", [])
                groups.append(current)
            current[1].append(line[2:].strip())
    return meta, groups, omissions


def is_label(title: str) -> bool:
    """A title that asserts nothing: no verb, no figure, and not a question."""
    return not (VERBISH.search(title) or FIGURE.search(title)
                or QUESTION.search(title))


def review(text: str):
    meta, groups, omissions = parse(text)
    titles = [t for _h, ts in groups for t in ts]
    findings: list[dict[str, object]] = []

    for key, vocab in (("genre", GENRES), ("storyline", STORYLINES)):
        value = meta.get(key)
        if value is None:
            findings.append({"check": key, "verdict": "FAIL",
                             "detail": f"the outline does not declare its {key}; "
                                       f"without it the checklist and the "
                                       f"thresholds are guesses"})
        elif value not in vocab:
            findings.append({"check": key, "verdict": "FAIL",
                             "detail": f"{value!r} is not one of {list(vocab)}"})

    if not titles:
        findings.append({"check": "titles", "verdict": "FAIL",
                         "detail": "no titles found — nothing to review"})
        return meta, groups, omissions, titles, findings

    labels = [t for t in titles if is_label(t)]
    findings.append({
        "check": "topic-label titles", "verdict": "FAIL" if labels else "ok",
        "detail": labels or "every title asserts something"})

    for heading, ts in groups:
        if len(ts) < GROUP_MIN or len(ts) > GROUP_MAX:
            findings.append({
                "check": "group size", "verdict": "FAIL",
                "detail": f"{heading!r} holds {len(ts)}; a group is "
                          f"{GROUP_MIN}-{GROUP_MAX} claims of one kind"})

    storyline = meta.get("storyline")
    expected = TYPICAL_SECTIONS.get(storyline, ())
    if expected:
        blob = " ".join(t.lower() for t in titles)
        declared = {o["section"] for o in omissions}
        missing = [s for s in expected
                   if s not in blob and s not in declared]
        undeclared_reason = [o["section"] for o in omissions if not o["reason"]]
        findings.append({
            "check": "type completeness", "verdict": "note",
            "detail": missing or "every typical section is named or declared"})
        if undeclared_reason:
            findings.append({
                "check": "declared omission", "verdict": "FAIL",
                "detail": f"{undeclared_reason} declared without a reason; the "
                          f"declaration is what separates a decision from a "
                          f"gap, and a bare one does neither"})
    return meta, groups, omissions, titles, findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("outline", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.outline.is_file():
        sys.exit(f"no such outline: {a.outline}")

    meta, groups, omissions, titles, findings = review(
        a.outline.read_text(encoding="utf-8"))
    failed = [f for f in findings if f["verdict"] == "FAIL"]

    if a.json:
        print(json.dumps({"meta": meta, "titles": titles,
                          "omissions": omissions, "findings": findings},
                         indent=1, ensure_ascii=False))
        sys.exit(1 if failed else 0)

    print(f"{a.outline}  ({len(titles)} title(s), {len(groups)} group(s), "
          f"genre={meta.get('genre')}, storyline={meta.get('storyline')})\n")
    for f in findings:
        mark = {"ok": "ok  ", "FAIL": "FAIL", "note": "note"}[f["verdict"]]
        detail = f["detail"]
        if isinstance(detail, list):
            detail = ", ".join(detail) if detail else "—"
        print(f"  {mark}  {f['check']:22} {detail}")

    print("\n  THE READ-THROUGH — read these as one paragraph. Whether they")
    print("  cohere is the point of this beat, and this script does not judge it:\n")
    for t in titles:
        print(f"    {t}")
    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
