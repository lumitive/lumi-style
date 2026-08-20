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

import markup  # noqa: E402 — after the bootstrap
from deliverable_registry import (  # noqa: E402 — after the bootstrap
    GENRES,
    STORYLINES,
    TYPICAL_SECTIONS,
)

GROUP_MIN, GROUP_MAX = 2, 5

# A title asserts something if it has a verb or a figure. This is the same
# question M1 asks of a built document, asked early enough to be cheap to fix.
VERBISH = re.compile(
    r"\b(is|are|was|were|has|have|will|can|cannot|may|might|must|should|"
    r"would|could|does|do|"
    r"grew|grow|fell|fall|rose|rise|beats?|costs?|needs?|closes?|stops?|"
    r"stopped|carries|carry|leads?|drives?|misses?|holds?|breaks?|wins?|"
    r"loses?|shifts?|moves?|keeps?|adds?|cuts?|doubles?|halves?|"
    r"stands?|buys?|sells?|prices?|pays?|takes?|puts?|makes?|gives?|"
    r"leaves?|leaving|consumes?|declares?|refuses?|blocks?|owns?|runs?|"
    r"ships?|names?|signs?|exposes?|settles?|settled|arrives?|arrived|"
    r"fails?|reaches?|turns?|shows?|asks?|answers?|goes|go|comes?|lets?)\b",
    re.I)
FIGURE = re.compile(r"\d")
QUESTION = re.compile(r"\?\s*$")


def parse(text: str):
    """-> (meta, groups, omissions). A group is (heading, [titles])."""
    meta: dict[str, str] = {}
    groups: list[tuple[str, list[str]]] = []
    omissions: list[dict[str, str]] = []
    analyses: list[dict[str, object]] = []
    current: tuple[str, list[str]] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(genre|storyline)\s*:\s*(\S+)", line, re.I)
        if m:
            meta[m.group(1).lower()] = m.group(2)
            continue
        m = re.match(r"^analysis\s*:\s*(\S+)(.*)$", line, re.I)
        if m:
            analyses.append({"move": m.group(1).strip().lower(),
                             "rest": m.group(2).strip(),
                             "after_title": (current[1][-1]
                                             if current and current[1]
                                             else None)})
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
    return meta, groups, omissions, analyses


def is_label(title: str) -> bool:
    """A title that asserts nothing: no verb, no figure, and not a question.

    The verb list is a closed list and is therefore INCOMPLETE BY
    CONSTRUCTION — English has no closed set of verbs, and no amount of
    extending it makes one. At 0.1.522 it flagged five titles that were
    plainly sentences ("Three things stand between us and the first contract,
    each dated") because `stand`, `buys`, `consume`, `price` and `leaving`
    were not in it. That is why this check REPORTS and does not gate: whether
    a title asserts something is a judgement about prose, and this repo does
    not gate on those. The gate in this file is the outline mirror, which asks
    only whether two artifacts still agree — a question a string comparison
    can actually answer.
    """
    return not (VERBISH.search(title) or FIGURE.search(title)
                or QUESTION.search(title))


ANALYTICAL_MOVES = ("compare", "decompose", "position", "correlate", "bridge")


# --- the drift check (0.1.522) -----------------------------------------------
# The analysis beat produced a plan and nothing carried it into the markup.
# Measured on a shipped deck: the outline declared a move, a finding and an
# implication for all fourteen content sections, and NOT ONE of its titles still
# described a page — the beat ran and its output was discarded in composition.
#
# This is the same class as D27, which holds the agenda to the deck's real
# titles and gates. It is a CONSISTENCY check, never a judgement: it asks
# whether the artifact still says what its own plan says, and either the deck or
# the outline is then corrected. It cannot and does not ask whether either is good.
# A CJK run is a word here. Without the second alternative `_WORD` was
# `[a-z0-9]+` alone, so a title written entirely in Chinese produced NO words:
# containment needs two non-empty strings and the overlap test needs a
# non-empty plan, so both branches fell through and `_matches` returned False
# for a title against ITSELF. On the shipped zh deck exactly the three titles
# carrying no Latin word and no digit failed the gate, and all three were on
# the page character for character. The zh build had been passing this gate on
# its digits.
_WORD = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+")
_CJK = re.compile(r"[\u4e00-\u9fff]")
_STOP = frozenset("a an the and or of to in on for is are it its that this with "
                  "we our you your be by as at from not no one".split())


def _stem(w: str) -> str:
    """A crude suffix strip, enough that `hold` and `holding` are one word.

    Without it the overlap test failed on morphology alone: a page whose take
    said "holding it takes a corpus" was reported as diverging from a plan that
    said "the corpus it takes to hold it" — the same claim, counted as two.
    This is not linguistics; it is the smallest thing that stops the check
    reporting a difference that is not there.
    """
    if w.endswith(("ss", "us")):          # corpus, class — not plurals
        return w
    for suf in ("ing", "ies", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def _joined(s: str) -> str:
    """The words in order, with the space between two CJK characters removed.

    The CJK rule is `markup.join_cjk`, shared with `check_design._norm_line`.
    """
    return markup.join_cjk(" ".join(_WORD.findall(s.lower())))


def _content_words(s: str) -> set[str]:
    """Latin words stemmed; a CJK run as its character BIGRAMS.

    A whole run taken as one token makes the 60% overlap test all-or-nothing in
    Chinese, so a title legitimately tightened during composition -- the case
    the threshold exists for -- would read as replaced. Bigrams give Chinese the
    same tolerance the stemmer gives English.
    """
    out: set[str] = set()
    for w in _WORD.findall(s.lower()):
        if _CJK.match(w):
            out.update(w[i:i + 2] for i in range(max(len(w) - 1, 1)))
        elif w not in _STOP:
            out.add(_stem(w))
    return out


def _matches(plan: str, shipped: str) -> bool:
    """Containment either way, or a 60% content-word overlap.

    Containment alone is too brittle: a title legitimately tightened during
    composition ("4 existing approaches" -> "4 approaches") would read as
    replaced. Overlap alone is too loose. Both, and the threshold is stated so
    it can be argued with.
    """
    a, b = _joined(plan), _joined(shipped)
    if a and b and (a in b or b in a):
        return True
    pw = _content_words(plan)
    return bool(pw) and len(pw & _content_words(shipped)) / len(pw) >= 0.60


def _flatten(fragment: str) -> str:
    """Markup fragment -> the words a reader sees, entities resolved."""
    return markup.visible_text(fragment)


class _NoMatch:
    """A stand-in so an absent attribute reads as empty rather than raising."""

    @staticmethod
    def group(_n: int) -> str:
        return ""


_NOMATCH = _NoMatch()


def deck_pages(html: str) -> list[dict[str, str]]:
    """-> [{id, title, take}] for every page that carries a title."""
    out = []
    # The tag's attributes are read in WHATEVER ORDER they appear. Requiring
    # class before id made `<section id="p4" class="page">` -- valid markup,
    # and what a hand-written page tends to look like -- parse to nothing, and
    # the report then told the author their outline described a different
    # document. A parser that fails must not deliver a verdict about the
    # author's work.
    for m in re.finditer(r"<section\b([^>]*)>(.*?)</section>", html, re.S | re.I):
        attrs, body = m.groups()
        cls = (re.search(r'class="([^"]*)"', attrs, re.I) or _NOMATCH).group(1) or ""
        pid = (re.search(r'id="([^"]*)"', attrs, re.I) or _NOMATCH).group(1) or ""
        classes = cls.split()
        if "page" not in classes:
            continue
        # Compared as whitespace-delimited TOKENS: `discovery` and `recovery`
        # both contain the substring `cover`, and a substring test silently
        # dropped those pages from the mirror. Same bug class as `\bcard\b`
        # matching `f-card`, which this repo has already shipped three times.
        if {"cover", "closing", "opener"} & set(classes):
            continue
        t = re.search(r'<h2 class="t">(.*?)</h2>', body, re.S)
        if not t:
            continue
        k = re.search(r'class="(?:[^"]*\s)?take(?:\s[^"]*)?"[^>]*>(.*?)</p>', body, re.S)
        out.append({"id": pid, "title": _flatten(t.group(1)),
                    "take": _flatten(k.group(1)) if k else ""})
    return out


def drift(text: str, html: str):
    """-> findings comparing the outline's plan against the built document.

    Returns the findings alone. It used to return `(out, len(pages),
    len(shipped))`, and `shipped` is derived from `pages`, so the last two
    were always equal and every caller discarded both -- a shape inviting
    a future reader to trust a distinction that does not exist.
    """
    _meta, groups, _om, analyses = parse(text)
    titles = [t for _h, ts in groups for t in ts]
    pages = deck_pages(html)

    orphans, paired = [], {}
    for t in titles:
        hit = next((p for p in pages if _matches(t, p["title"])), None)
        if hit is None:
            orphans.append(t[:60])
        else:
            paired[t] = hit

    out = [{
        "check": "outline mirror",
        "verdict": "FAIL" if orphans else "ok",
        "detail": (orphans if orphans else
                   f"all {len(titles)} planned titles reached the document"),
    }]

    # The implication rung. AR-2 binds it to `.take`; a take that carries the
    # title instead of the reader's stake is the ladder's middle rung missing.
    # Reported at first ship, on the new-gate caution: a take rewritten better
    # than its plan is a legitimate outcome, and only a person can tell.
    lost, checked = [], 0
    for a in analyses:
        title = a.get("after_title")
        imp = re.search(r"implication\s*:\s*(.+)$", str(a.get("rest", "")), re.I)
        if not (title and imp and title in paired):
            continue
        checked += 1
        if not _matches(imp.group(1).strip(), paired[title]["take"]):
            lost.append(paired[title]["id"])
    if analyses:
        # `checked`, not `len(analyses)`. An implication whose page does not
        # exist is skipped by the loop above, and counting it in the
        # denominator produced a report that contradicted itself: the mirror
        # named a planned title that reached no page, and this line directly
        # beneath it said all of them reached a takeaway.
        unpaired = len(analyses) - checked
        tail = (f" ({unpaired} more could not be checked: their page is not in "
                f"the document)" if unpaired else "")
        out.append({
            "check": "implication rung",
            "verdict": "note",
            "detail": (f"{len(lost)} of {checked} planned implications are "
                       f"not in their page's takeaway: " + ", ".join(lost[:10]) + tail
                       if lost else
                       f"all {checked} planned implications reached a takeaway" + tail),
        })
    if titles and not pages:
        # Nothing was read. `not_measured` is the tier this file introduced for
        # exactly this and then did not apply to its own new code: the first
        # version emitted a FAIL per planned title plus "this outline describes
        # a different document", on a document the parser had not managed to
        # read a single page out of. The outline may be perfect.
        out[:] = [f for f in out if f["check"] != "outline mirror"]
        out.append({"check": "outline mirror", "verdict": "not_measured",
                    "detail": "no page could be read out of this document, so "
                              "the plan has not been compared to anything — "
                              "this is a parse failure, not a verdict on the "
                              "outline"})
    elif titles and len(orphans) == len(titles):
        out.append({"check": "outline stale", "verdict": "FAIL",
                    "detail": "not one planned title matched a page — this "
                              "outline describes a different document"})
    return out


def review(text: str):
    meta, groups, omissions, analyses = parse(text)
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
        "check": "topic-label titles", "verdict": "note" if labels else "ok",
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
        findings.append({
            "check": "type completeness", "verdict": "note",
            "detail": missing or "every typical section is named or declared"})
    else:
        # A storyline with no checklist must SAY it has none. Nesting this
        # whole block under `if expected:` meant `proposal` — admitted to
        # STORYLINES at 0.1.491 and never given a TYPICAL_SECTIONS row —
        # printed a clean report and exited 0 where every other storyline
        # exited 1 on the same file. The docstring calls this beat "the only
        # defence completeness has"; for the newest storyline it was no
        # defence, and it looked like a pass.
        findings.append({
            "check": "type completeness", "verdict": "not_measured",
            "detail": f"no typical-section checklist exists for "
                      f"{storyline!r}, so completeness was not assessed — "
                      f"a checklist nobody wrote is not a document with "
                      f"nothing missing"})

    # Analysis declarations (analysis-rules.md AR-3): REPORTED coverage,
    # never a content judgement. "analysis: <move> | finding … | implication …"
    # after a title declares which analytical move produced it. The moves come
    # from AR-1's five; a declared move outside them is a vocabulary fact and
    # does FAIL — same reasoning as the genre vocabulary above. Coverage
    # itself is a note: the benchmark review, not this script, asks whether
    # the declared analysis is real.
    bad_moves = [str(a["move"]) for a in analyses
                 if a["move"] not in ANALYTICAL_MOVES]
    if bad_moves:
        findings.append({
            "check": "analysis vocabulary", "verdict": "FAIL",
            "detail": f"{bad_moves} not in {list(ANALYTICAL_MOVES)} — the "
                      f"five moves are analysis-rules.md AR-1's"})
    declared_n = sum(1 for a in analyses if a["move"] in ANALYTICAL_MOVES)
    findings.append({
        "check": "analysis coverage", "verdict": "note",
        "detail": f"{declared_n} of {len(titles)} titles declare the "
                  f"analytical move that produced them"
                  + ("" if declared_n else " — a deck of findings starts "
                     "here, and zero declarations reads as display, "
                     "not analysis")})

    # The declared-omission GATE is outside that branch on purpose: whether a
    # stated omission carries a reason is a fact about the outline, not about
    # the storyline's checklist, and it must hold for every storyline.
    undeclared_reason = [o["section"] for o in omissions if not o["reason"]]
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
    ap.add_argument("--against", type=pathlib.Path, metavar="DECK.html",
                    help="the built document. Holds it to this outline: every "
                         "planned title must have reached a page (gates), and "
                         "every planned implication its page's takeaway "
                         "(reported). Without it the outline is reviewed alone.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.outline.is_file():
        sys.exit(f"no such outline: {a.outline}")

    text = a.outline.read_text(encoding="utf-8")
    meta, groups, omissions, titles, findings = review(text)
    if a.against:
        if not a.against.is_file():
            sys.exit(f"no such document: {a.against}")
        more = drift(text, a.against.read_text(encoding="utf-8"))
        findings.extend(more)
    failed = [f for f in findings if f["verdict"] == "FAIL"]

    if a.json:
        print(json.dumps({"meta": meta, "titles": titles,
                          "omissions": omissions, "findings": findings},
                         indent=1, ensure_ascii=False))
        sys.exit(1 if failed else 0)

    print(f"{a.outline}  ({len(titles)} title(s), {len(groups)} group(s), "
          f"genre={meta.get('genre')}, storyline={meta.get('storyline')})\n")
    for f in findings:
        # `not_measured` prints as itself rather than as a pass. A dict lookup
        # here would KeyError on a verdict tier nobody updated it for, which is
        # the loud failure and the right one — but the tier has to be listed.
        mark = {"ok": "ok  ", "FAIL": "FAIL", "note": "note",
                "not_measured": "n/m "}[f["verdict"]]
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
