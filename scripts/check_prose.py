#!/usr/bin/env python3
"""Measure the AI-flavor metrics from references/eval-rubric.md on a deliverable.

M1-M11 were described as "scriptable" for six versions while no script existed,
so every AI-flavor rule was enforced by good intentions alone. This runs the
machine-checkable half against a real file.

    python3 scripts/check_prose.py deck.en.html [more files ...]
    python3 scripts/check_prose.py --genre internal report.md   # skips M9
    python3 scripts/check_prose.py --json deck.en.html

English deliverables only: the segmentation here does not apply to Chinese, which
is governed by the de-translationese pass in writing-rules.md section 6b.

Extraction is regex-based and best-effort. It is deliberately loud about what it
could NOT measure: a file that yields no prose is reported unmeasurable and fails,
because a linter that says "clean" when it read nothing is worse than no linter.

The banned list below mirrors references/writing-rules.md section 2 [en-output].
It is a second copy, so check_repo.py's `ban-list parity` guard holds the two
together: every phrase in section 2 must appear here either as a pattern or in
NOT_MECHANIZED with a reason, and nothing may appear here that section 2 does not
list. Adding a phrase to the rules without deciding what the machine does about
it now fails CI.
"""

import argparse
import html
import json
import pathlib
import re
import statistics
import sys

# (regex, phrase). The phrase is verbatim from writing-rules.md section 2 and is
# the key the parity guard matches on -- do not reword it to read better.
#
# Patterns are explicit because the two obvious shortcuts are both wrong: bare
# substrings match inside ordinary words ("serves as" inside "deserves as much"),
# and \bword\b misses the inflections that are the actual tell ("leveraging").
# Entries that are ordinary business English on their own are qualified rather
# than banned outright.
BANNED = [
    # 1 significance inflation
    (r"\b(?:serves?|stands?)\s+as\b", "stands/serves as"),
    (r"\b(?:is|are|was|were)\s+a\s+testament\s+to\b", "is a testament to"),
    (r"\ba\s+(?:vital|crucial|pivotal|key)\s+(?:role|moment)\b",
     "a vital / crucial / pivotal / key role"),
    (r"\bunderscor(?:es?|ing)\s+(?:its|the)\s+(?:importance|significance)\b",
     "underscores its importance"),
    (r"\breflects?\s+broader\b", "reflects broader"),
    (r"\bmark(?:s|ing)\s+a\s+shift\b", "marking a shift"),
    (r"\ba\s+turning\s+point\b", "a turning point"),
    (r"\bevolving\s+landscape\b", "evolving landscape"),
    (r"\bindelible\s+mark\b", "indelible mark"),
    (r"\bdeeply\s+rooted\b", "deeply rooted"),
    # 2 promotional register
    (r"\bboasts?\b", "boasts"),
    (r"\bvibrant\b", "vibrant"),
    (r"\bshowcasing\b", "showcasing"),
    (r"\bexemplif(?:y|ies|ied)\b", "exemplifies"),
    (r"\bcommitment\s+to\s+(?:excellence|quality|innovation)\b", "commitment to"),
    (r"\bgroundbreaking\b", "groundbreaking (figurative)"),
    (r"\brenowned\b", "renowned"),
    (r"\bbreathtaking\b", "breathtaking"),
    (r"\bstunning\b", "stunning"),
    (r"\bseamless(?:ly)?\b", "seamless"),
    (r"\b(?:a|an|our|the)\s+robust\b", "robust"),
    (r"\bbest-in-class\b", "best-in-class"),
    (r"\bworld-class\b", "world-class"),
    # 3 AI high-frequency vocabulary
    (r"(?:^|(?<=[.!?]\s))Additionally\s*,", "additionally"),
    (r"\bdelv(?:e|es|ed|ing)\b", "delve"),
    (r"\bfoster(?:s|ed|ing)\b", "fostering"),
    (r"\bgarner(?:s|ed|ing)?\b", "garner"),
    (r"\binterplay\b", "interplay"),
    (r"\bintricat(?:e|ies)\b", "intricate"),
    (r"\bleverag(?:es|ed|ing)\b", "leverage (verb)"),
    (r"\bpivotal\b", "pivotal"),
    (r"\bshowcas(?:e|es|ed)\b", "showcase"),
    (r"\btapestry\b", "tapestry"),
    (r"\btestament\b", "testament"),
    (r"\bunderscor(?:es|ed|ing)\b", "underscore (verb)"),
    (r"\butiliz(?:e|es|ed|ing)\b", "utilize"),
    # 4 filler
    (r"\bin\s+order\s+to\b", "in order to"),
    (r"\bdue\s+to\s+the\s+fact\s+that\b", "due to the fact that"),
    (r"\bat\s+this\s+point\s+in\s+time\b", "at this point in time"),
    (r"\bin\s+the\s+event\s+that\b", "in the event that"),
    (r"\bhas\s+the\s+ability\s+to\b", "has the ability to"),
    (r"\bit\s+is\s+important\s+to\s+note\s+that\b", "it is important to note that"),
    # 5 authority tropes
    (r"\bthe\s+real\s+question\s+is\b", "the real question is"),
    (r"\bat\s+its\s+core\b", "at its core"),
    (r"\bwhat\s+really\s+matters\b", "what really matters"),
    (r"\bit'?s\s+not\s+about\s+.{1,40}?,\s*it'?s\s+about\b",
     "it's not about X, it's about Y"),
    # 6 signposting
    (r"\blet'?s\s+dive\s+in\b", "let's dive in"),
    (r"\blet'?s\s+explore\b", "let's explore"),
    (r"\blet'?s\s+break\s+this\s+down\b", "let's break this down"),
    (r"\bhere'?s\s+what\s+you\s+need\s+to\s+know\b", "here's what you need to know"),
    (r"\bnow\s+let'?s\s+look\s+at\b", "now let's look at"),
    (r"\bwithout\s+further\s+ado\b", "without further ado"),
    # 7 fake-candid openers — sentence-initial only
    (r"(?:^|(?<=[.!?]\s))Honestly\s*\?", "honestly?"),
    (r"(?:^|(?<=[.!?]\s))Look\s*,", "look,"),
    (r"(?:^|(?<=[.!?]\s))The\s+thing\s+is\s*,", "the thing is,"),
    (r"(?:^|(?<=[.!?]\s))Here'?s\s+the\s+thing\b", "here's the thing"),
    # 8 closing filler
    (r"\bit'?s\s+worth\s+noting\s+that\b", "it's worth noting that"),
    (r"\bundeniably\b", "undeniably"),
    (r"\bin\s+conclusion\b", "in conclusion as filler"),
    (r"\blet'?s\s+embark\b", "let's embark"),
]

# Phrases section 2 bans that this script deliberately does NOT match, each with
# the reason. The parity guard requires every section 2 phrase to be in exactly
# one of BANNED or here, so a rule added without deciding its mechanization fails
# CI instead of quietly going unenforced.
NOT_MECHANIZED = {
    "rich (figurative)": "sense-dependent; 'rich data' and 'rich history' need a human",
    "profound": "legitimate in analysis prose; too many false positives to gate on",
    "comprehensive": "ordinary business English ('a comprehensive review')",
    "actually": "legitimate adverb; only the discourse-marker use is a tell",
    "align with": "legitimate ('align with the strategy'); the tell is register, not the phrase",
    "crucial": "bare use is often legitimate; the 'a crucial role' collocation is matched",
    "enhance": "ordinary verb; banning it outright would rewrite honest sentences",
    "highlight (verb)": "legitimate ('the chart highlights the gap'); needs POS tagging",
    "key (adjective)": "far too common in legitimate business English",
    "landscape (abstract)": "needs sense disambiguation from the literal noun",
    "valuable": "ordinary adjective; the tell is unquantified praise, caught by M-number rules",
    "in reality": "legitimate contrastive marker outside authority-trope register",
    "fundamentally": "legitimate adverb in analysis; only the trope stacking is a tell",
    "adjective stacks in place of numbers": "not a fixed string; requires judgment about "
                                           "whether a number was available",
}

OVERLONG_WORDS = 32
MIN_SENTENCES = 30      # below this, rhythm is noise
MIN_TITLES = 8          # below this, one frame dominating means nothing
BLOCK_END = re.compile(r"</(?:p|li|h[1-6]|td|th|div|section|figcaption|blockquote)>", re.I)
NUMERIC_RANGE = re.compile(r"\d\s*[–—]\s*\d")
# A cell whose entire content is a dash means "no value" — the standard
# typographic convention in a table, not a dash in prose. M9 bans the AI-flavor
# tell of em-dashes in sentences; it counted `<td>—</td>` and failed a
# deliverable that had no such dash anywhere in its prose. Found by running the
# checker against real agent output rather than against a fixture we wrote.
EMPTY_CELL_DASH = re.compile(
    r"<t[dh][^>]*>\s*(?:[–—]|&#8211;|&#8212;|&[mn]dash;)\s*</t[dh]>", re.I)


class Unmeasurable(Exception):
    """The file yielded nothing to measure. Never silently a pass."""


def extract(path):
    """Return (body_text, [titles], [enumeration_sizes])."""
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise Unmeasurable(f"not valid UTF-8 ({exc.reason}) — re-export as UTF-8") from exc

    if path.suffix.lower() in {".html", ".htm"}:
        if re.search(r"<(script|style)\b", raw, re.I) and not re.search(
                r"</(script|style)>", raw, re.I):
            raise Unmeasurable("unclosed <script>/<style>; code would be scored as prose")
        raw = EMPTY_CELL_DASH.sub("<td></td>", raw)
        raw_nostrip = re.sub(r"<(script|style|svg|head)\b.*?</\1>", " ", raw, flags=re.S | re.I)
        titles = [
            re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()
            for m in re.finditer(r"<h[12][^>]*>(.*?)</h[12]>", raw_nostrip, re.S | re.I)
        ]
        # An enumeration is an enumeration whatever it is marked up as. Counting
        # only <ul>/<ol> made M10 measure three lists on a 30 page deck that
        # enumerates constantly in named blocks, and two of the three happening
        # to hold three items read as a 66.7% triad rate. The rule is about how
        # often an author reaches for three, so the sample has to be every place
        # they reached.
        enums = [len(re.findall(r"<li\b", m.group(1), re.I))
                 for m in re.finditer(r"<(?:ul|ol)\b[^>]*>(.*?)</(?:ul|ol)>",
                                      raw_nostrip, re.S | re.I)]
        for wrapper, item in (("swaps", "swap"), ("vows", "vow"), ("grades", "gr"),
                              ("gloss", "dt"), ("duo", "gd")):
            for m in re.finditer(rf'<[^>]*class="[^"]*\b{wrapper}\b[^"]*"[^>]*>(.*?)(?=<div class="(?:foot|body|listhead)|</section>)',
                                 raw_nostrip, re.S | re.I):
                n = len(re.findall(rf'class="[^"]*\b{item}\b', m.group(1), re.I))
                if n >= 2:
                    enums.append(n)
        # Block boundaries become sentence boundaries; without this a nav bar, a
        # heading and six list items merge into one 27-word "sentence".
        body = BLOCK_END.sub(".\n", raw_nostrip)
        body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    else:
        titles = [m.group(2).strip() for m in re.finditer(r"^(#{1,2})\s+(.*)$", raw, re.M)]
        enums = [len(list(g)) for g in _markdown_lists(raw)]
        body = re.sub(r"^#{1,6}\s+", "", raw, flags=re.M)

    body = re.sub(r"[ \t]+", " ", body)
    return body, [t for t in titles if t], enums


def _markdown_lists(raw):
    block = []
    for line in raw.splitlines():
        if re.match(r"^\s*(?:[-*+]|\d+\.)\s+\S", line):
            block.append(line)
        elif block:
            yield block
            block = []
    if block:
        yield block


def sentences(text):
    out = []
    for part in re.split(r"(?<=[.!?])\s+|\n+", text):
        # Count digits as words: a numbers-first house style otherwise reads as
        # systematically shorter than it is.
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'%$-]*", part)
        if len(words) >= 4:
            out.append(len(words))
    return out


def measure(path, genre):
    body, titles, enums = extract(path)
    lengths = sentences(body)
    if not lengths:
        raise Unmeasurable("no prose extracted (0 sentences)")

    hits = []
    for pattern, label in BANNED:
        n = len(re.findall(pattern, body, re.I | re.M))
        if n:
            hits.append((label, n))

    mean = statistics.fmean(lengths)
    cv = statistics.pstdev(lengths) / mean if len(lengths) > 1 and mean else 0.0
    overlong = 100.0 * sum(1 for n in lengths if n > OVERLONG_WORDS) / len(lengths)

    # An en dash between digits is a numeric range, which is data, not prose
    # punctuation -- writing-rules.md exempts it.
    dashes = len(re.findall(r"[–—]", NUMERIC_RANGE.sub(" ", body)))

    triads = sum(1 for n in enums if n == 3)
    triad_rate = 100.0 * triads / len(enums) if enums else None

    def frame(t):
        return (
            "colon" if ":" in t else
            "question" if t.rstrip().endswith("?") else
            "number-led" if re.match(r"^\s*[\d$]", t) else
            "verb-led" if re.match(r"^\s*(?:[A-Z][a-z]+ing|How|Why|What|When)\b", t) else
            "plain"
        )

    frames = [frame(t) for t in titles]
    uniformity = (100.0 * max(frames.count(f) for f in set(frames)) / len(frames)
                  if frames else None)

    return {
        "file": str(path),
        "genre": genre,
        "sentences": len(lengths),
        "titles": len(titles),
        "enumerations": len(enums),
        "M4_banned_hits": sum(n for _, n in hits),
        "M4_detail": hits,
        "M8_overlong_share": round(overlong, 1),
        "M8_length_cv": round(cv, 3),
        "M9_dashes": dashes if genre == "sales" else None,
        "M10_triad_rate": None if triad_rate is None else round(triad_rate, 1),
        "M11_title_uniformity": None if uniformity is None else round(uniformity, 1),
    }


def grade(r):
    """[(metric, value, target, verdict)] — verdict is ok / FAIL / n/a."""
    thin_rhythm = r["sentences"] < MIN_SENTENCES
    rows = [
        ("M4_banned_hits", r["M4_banned_hits"], "=0", r["M4_banned_hits"] == 0, False),
        ("M8_overlong_share", r["M8_overlong_share"], "<=8%",
         r["M8_overlong_share"] <= 8.0, thin_rhythm),
        ("M8_length_cv", r["M8_length_cv"], ">=0.35", r["M8_length_cv"] >= 0.35, thin_rhythm),
        ("M9_dashes", r["M9_dashes"], "=0", r["M9_dashes"] == 0, r["M9_dashes"] is None),
        ("M10_triad_rate", r["M10_triad_rate"], "<=50%",
         (r["M10_triad_rate"] or 0) <= 50.0, r["M10_triad_rate"] is None),
        ("M11_title_uniformity", r["M11_title_uniformity"], "<=60%",
         (r["M11_title_uniformity"] or 0) <= 60.0,
         r["M11_title_uniformity"] is None or r["titles"] < MIN_TITLES),
    ]
    return [(name, value, target, "n/a" if skip else ("ok" if good else "FAIL"))
            for name, value, target, good, skip in rows]


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--genre", choices=["sales", "internal"], default="sales",
                    help="internal analysis documents are exempt from the M9 dash ban")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    reports, failed = [], 0
    for name in args.files:
        path = pathlib.Path(name)
        try:
            if not path.is_file():
                raise Unmeasurable("not a readable file")
            r = measure(path, args.genre)
        except (Unmeasurable, OSError) as exc:
            failed += 1
            print(f"FAIL  {path}: unmeasurable — {exc}", file=sys.stderr)
            reports.append({"file": str(path), "unmeasurable": str(exc)})
            continue

        rows = grade(r)
        r["verdicts"] = {n: v for n, _, _, v in rows}
        failed += sum(1 for _, _, _, v in rows if v == "FAIL")
        reports.append(r)
        if args.json:
            continue

        print(f"\n{r['file']}  ({r['sentences']} sentences, {r['titles']} titles, "
              f"{r['enumerations']} lists, genre={r['genre']})")
        for name_, value, target, verdict in rows:
            note = ""
            if verdict == "n/a":
                note = ("  (exempt for internal documents)" if name_ == "M9_dashes"
                        else f"  (too little data: {r['sentences']} sentences, "
                             f"{r['titles']} titles)")
            print(f"  {verdict:<4}  {name_:<22} {str(value):<8} target {target}{note}")
        if r["M4_detail"]:
            worst = sorted(r["M4_detail"], key=lambda kv: -kv[1])[:8]
            print("        banned: " + ", ".join(f"{p}x{n}" for p, n in worst))

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print(f"\n{failed} metric failure(s)" if failed else "\nall metrics pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
