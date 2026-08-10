#!/usr/bin/env python3
"""Measure the AI-flavor metrics from references/eval-rubric.md on a deliverable.

M1-M11 were described as "scriptable" for six versions while no script existed,
so every AI-flavor rule was enforced by good intentions alone. This runs the
machine-checkable half against a real file.

    python3 scripts/check_prose.py deck.en.html [more files ...]
    python3 scripts/check_prose.py --genre internal report.md   # skips M9
    python3 scripts/check_prose.py --json deck.en.html

Both output languages, since 0.1.390. English gets the full set; a document that
declares `zh` gets the banned-phrase list and the punctuation pass (M4zh, M5) and
n/a for the rest. Sentence rhythm stays out — the segmentation here does not
transfer to Chinese — and the de-translationese pass in writing-rules.md section
6b is recorded as NOT mechanized rather than approximated, because it is
judgement about register.

    python3 scripts/check_prose.py report.zh.html        # the Chinese path
    python3 scripts/check_prose.py --lang zh report.html # when the file does not say

A Chinese document used to come back UNMEASURABLE, which was the real reason
this file was English-only: the word splitter needs spaces, so every Chinese
deliverable yielded zero sentences and tripped the empty-prose guard.

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

# ── the Chinese half ──────────────────────────────────────────────────────────
# This package's rules cover Chinese output across four sections and, until
# 0.1.390, its machinery covered none of it: the only Chinese string CI touched
# was the negative case that makes M12 fail. For a team that writes Chinese, an
# asymmetry that complete is structural rather than incidental.
#
# BANNED_ZH mirrors writing-rules.md section 2's [zh-output] rule data, and
# check_repo.py's `zh ban-list parity` guard holds the two together under the
# same discipline as the English list — which is the point of doing this first:
# it closes the drift channel before there is new code to drift.
BANNED_ZH = [
    (r"值得注意的是", "值得注意的是"),
    (r"值得一提的是", "值得一提的是"),
    (r"不可否认", "不可否认"),
    (r"综上所述", "综上所述"),
    (r"让我们一起", "让我们一起"),
    (r"总而言之", "总而言之"),
    (r"众所周知", "众所周知"),
    # QUALIFIED. 赋能 is legitimate in two fixed industry collocations and an AI
    # tell everywhere else, so the collocation is tested FIRST — section 2 states
    # that lesson explicitly ("ban predicates must distinguish fixed
    # collocations from abuse"), and a bare 赋能 ban would flag 销售赋能.
    (r"(?<!销售)(?<!市场)赋能", "赋能 outside 销售赋能 / 市场赋能"),
]

# Half-width punctuation that must be full-width in Chinese body text (M5).
# The exemptions are section 3's, not invented here: half-width stays inside
# code, URLs, emails, version strings, filenames, and pure English runs.
ZH_PUNCT = {",": "，", ":": "：", ";": "；", "?": "？", "!": "！"}

OVERLONG_WORDS = 32
MIN_SENTENCES = 30      # below this, rhythm is noise
MIN_TITLES = 8          # below this, one frame dominating means nothing

# ── M1, M2, M6 ────────────────────────────────────────────────────────────────
# The rubric called M1-M11 "scriptable" for six versions while no script existed.
# These three were the remainder, and they are the three that stand behind a FACT
# red line rather than a style rule — M2 and M6 behind "every number carries its
# source", M1 behind the title contract's demand that a title carry a verifiable
# fact. A deliverable could break all three and pass every check this package
# shipped.
#
# SOURCE_MARKERS is a second copy of writing-rules.md section 4 rule 6, and
# check_repo.py's `source-marker parity` guard holds the two together exactly as
# `ban-list parity` holds section 2. The rules are the source: a marker here that
# the rules do not list fails CI, and so does the reverse.
SOURCE_MARKERS = [
    "source", "derived from", "based on", "as of", "per", "n=", "extract",
    "illustrative", "mock", "proposal value", "uncalibrated",
]
SOURCE_RE = re.compile(
    "|".join(r"\bn\s*=\s*\d" if m == "n=" else rf"\b{re.escape(m)}\b"
             for m in SOURCE_MARKERS), re.I)

# A percentage or a currency amount. Deliberately NOT every number: a page
# number, a figure number and a count of regions are not claims that need a
# source, and a metric that flags them is one reviewers learn to skip.
FIGURE_RE = re.compile(
    r"\d[\d,.]*\s*%|\d[\d,.]*\s*percent\b|[$€£¥]\s?\d[\d,.]*"
    r"|\b\d[\d,.]*\s*(?:USD|EUR|GBP|CNY|RMB)\b", re.I)

M2_TARGET = 90.0        # percent of figures whose page carries a marker
M1_TARGET = 70.0        # percent of titles naming a subject and a fact
MIN_FIGURES = 4         # below this, a sourcing rate is one number's opinion


def _has_fact(title):
    """M1's proxy: a numeral, a named entity, or a dated term.

    M1 has no decidable predicate — "names a subject and carries a verifiable
    fact" is a judgement — so this is a PROXY and M1 is REPORTED, never gated.
    That is not timidity. A metric that gates gets satisfied, and the cheapest
    way to satisfy a regex is to write titles the regex likes: 0.1.339's page
    fill floor was met by stretching table rows rather than improving pages and
    was withdrawn one release later. A reported number cannot be satisfied, so
    this prints the titles it doubts and a reader overrules it.
    """
    if re.search(r"\d", title):
        return True
    # A NUMERAL includes a spelled-out one. "Three assumptions carry the
    # forecast" states a checkable count, and a proxy reading only digits misses
    # it — which is how the first cut scored a well-formed deck at 18.8% and
    # would have taught a reviewer to skip the line.
    if re.search(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|"
                 r"eleven|twelve|half|double|triple)\b", title, re.I):
        return True
    # A DATED TERM: a fiscal period, or a named span of time.
    if re.search(r"\b(?:Q[1-4]|H[12]|FY\d{2,4}|quarter|month|week|year|cycle|"
                 r"day|today|monthly|weekly|annual)\b", title, re.I):
        return True
    # A NAMED ENTITY: a capitalised word that is not the first. The first word
    # is capitalised by orthography and says nothing.
    return bool(re.search(r"\s[A-Z][A-Za-z0-9-]{2,}", title))

# The genre vocabulary, in one place. run_conformance.py and export_pdf.py
# import this tuple rather than hand-copying it: a hand-copy in the
# conformance harness rejected `training` for two releases after 0.1.376
# created it, and only a person writing a training task would have noticed.
# (`consulting` deliberately has no flag — the recorded no-change in 0.1.378:
# it inherits the sales dash ban and has produced no defect case.)
GENRES = ("sales", "internal", "training")
BLOCK_END = re.compile(r"</(?:p|li|h[1-6]|td|th|div|section|figcaption|blockquote)>", re.I)
NUMERIC_RANGE = re.compile(r"\d\s*[–—]\s*\d")
# A cell whose entire content is a dash means "no value" — the standard
# typographic convention in a table, not a dash in prose. M9 bans the AI-flavor
# tell of em-dashes in sentences; it counted `<td>—</td>` and failed a
# deliverable that had no such dash anywhere in its prose. Found by running the
# checker against real agent output rather than against a fixture we wrote.
EMPTY_CELL_DASH = re.compile(
    r"<t[dh][^>]*>\s*(?:[–—]|&#8211;|&#8212;|&[mn]dash;)\s*</t[dh]>", re.I)


# A RUN of CJK, not a character. Per-character matching reported one four-glyph
# phrase as four findings with four overlapping snippets, which reads as four
# defects and is one. A run may be broken by spaces, ASCII digits and the
# punctuation that travels with Chinese, so `已回收 15/15 题` counts once: it is
# one piece of text in the wrong language.
_CJK_CHAR = "[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"
CJK = re.compile(_CJK_CHAR + r"(?:[\s\d/%\-\u3001\uff0c\u3002\uff1a\uff1b\u00b7]*" + _CJK_CHAR + r")*")
# Where a deliverable may legitimately hold CJK while claiming English: quoted as
# DATA. Exactly the exemption `check_repo.py:check_english_only` gives this
# repository's own prose — backticks and fenced blocks in markdown, <code> and
# <pre> in HTML — and it is the same rule, applied outward instead of inward.
# No allowlist file: a name that must appear in Chinese is quoted, and quoting it
# is a decision a reader can see rather than a line in a config nobody reads.
CODE_HTML = re.compile(r"<(code|pre|script|style|svg|head)\b.*?</\1>", re.S | re.I)
LANG_ATTR = re.compile(r"<html[^>]*\blang\s*=\s*[\"']([\w-]+)", re.I)


def zh_punctuation(text):
    """-> [(what, context)] half-width punctuation adjacent to CJK.

    Section 3's rule, and its exemptions are section 3's too. A mark counts only
    when a CJK character sits on one side of it: `--json` in an English run, a
    version string and a URL all keep half-width marks and none of them is
    adjacent to a Han character. That single test does the work of the whole
    exemption list without needing to detect code, and it is why this is
    mechanizable when the de-translationese pass is not.
    """
    hits = []
    for mark, full in ZH_PUNCT.items():
        for m in re.finditer(rf"{_CJK_CHAR}\s*{re.escape(mark)}|{re.escape(mark)}\s*{_CJK_CHAR}",
                             text):
            start = max(0, m.start() - 12)
            hits.append((f"{mark} should be {full}",
                         text[start:m.end() + 12].strip()))
    return hits


def declared_language(path, raw, override=None):
    """What language the document says it is, and how it said so.

    Three channels, in order of how explicitly the document commits: the
    operator's flag, the `lang` attribute the file itself declares, then the
    `*.en.*` naming convention. Returns (code, where) or (None, reason) — never
    a guess, because a language check that assumes English would fail every
    Chinese deliverable in the package's own default second language.
    """
    if override:
        return override, "--lang"
    m = LANG_ATTR.search(raw)
    if m:
        return m.group(1).split("-")[0].lower(), "the document's lang attribute"
    parts = path.name.lower().split(".")
    for tag in parts[1:-1]:
        if tag in ("en", "zh", "zh_cn", "zh-cn"):
            return tag.split("_")[0].split("-")[0], "the filename"
    return None, ("no lang attribute, no language tag in the filename, and no "
                  "--lang given")


def visible_cjk(raw, suffix):
    """CJK in text a reader sees, with quoted data removed.

    M12 exists because `references/writing-rules.md` §0 has set the output
    language since 0.1.333 and nothing has ever measured it. A deliverable named
    `*.en.html`, carrying `lang="en"`, shipped `已回收 15/15 题` in a page lede
    and passed every metric in this package — while `check_repo.py` was enforcing
    the identical red line on the repository's own prose. The guard existed and
    pointed inward.
    """
    if suffix in {".html", ".htm"}:
        text = CODE_HTML.sub(" ", raw)
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    else:
        text = re.sub(r"```.*?```", " ", raw, flags=re.S)
        text = re.sub(r"`[^`\n]*`", " ", text)
    hits = []
    for m in CJK.finditer(text):
        start = max(0, m.start() - 24)
        hits.append(re.sub(r"\s+", " ", text[start:m.start() + 24]).strip())
    return hits


class Unmeasurable(Exception):
    """The file yielded nothing to measure. Never silently a pass."""


def _pages_and_blocks(raw_nostrip):
    """-> [(page_text, [block_text])], the two windows section 4 rule 6 defines.

    A page is `<section class="page">`; a document with no page structure has
    one page, which is the document. Blocks come from the same BLOCK_END
    boundaries the sentence splitter uses, so "its block" means the same thing
    to a reader of the rules and to this file.
    """
    pages = re.findall(
        r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
        raw_nostrip, re.S | re.I) or [raw_nostrip]
    out = []
    for page in pages:
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
        chunks = html.unescape(re.sub(r"<[^>]+>", " ", BLOCK_END.sub(".\n", page)))
        blocks = [re.sub(r"\s+", " ", b).strip()
                  for b in chunks.split("\n") if b.strip()]
        out.append((text, blocks))
    return out


def extract(path):
    """Return (body_text, [titles], [enumeration_sizes], [(page, [blocks])])."""
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
        # (wrapper class, item, what the item IS). The third field was implicit
        # and wrong for one pair: every item was matched as `class="…item…"`, and
        # a glossary's items are `<dt>` ELEMENTS, so the gloss wrapper counted
        # zero on every definition list ever written and M10 silently sampled one
        # enumeration shape fewer than it claimed. Found by widening
        # check_repo.py's probe-vocabulary guard to read this tuple: `.dt` came
        # back as a class name `tokens/` does not ship, which it is not and never
        # was. Saying which kind each item is fixes the count and lets the guard
        # read only the class assertions.
        for wrapper, item, kind in (("swaps", "swap", "class"),
                                    ("vows", "vow", "class"),
                                    ("grades", "gr", "class"),
                                    ("gloss", "dt", "tag"),
                                    ("duo", "gd", "class")):
            pattern = (rf'class="[^"]*\b{item}\b' if kind == "class"
                       else rf'<{item}\b')
            for m in re.finditer(rf'<[^>]*class="[^"]*\b{wrapper}\b[^"]*"[^>]*>(.*?)(?=<div class="(?:foot|body|listhead)|</section>)',
                                 raw_nostrip, re.S | re.I):
                n = len(re.findall(pattern, m.group(1), re.I))
                if n >= 2:
                    enums.append(n)
        # Block boundaries become sentence boundaries; without this a nav bar, a
        # heading and six list items merge into one 27-word "sentence".
        body = BLOCK_END.sub(".\n", raw_nostrip)
        body = html.unescape(re.sub(r"<[^>]+>", " ", body))
        windows = _pages_and_blocks(raw_nostrip)
    else:
        titles = [m.group(2).strip() for m in re.finditer(r"^(#{1,2})\s+(.*)$", raw, re.M)]
        enums = [len(list(g)) for g in _markdown_lists(raw)]
        body = re.sub(r"^#{1,6}\s+", "", raw, flags=re.M)
        # No page structure, so the document is the page and a paragraph is the
        # block — exactly what section 4 rule 6 says for a plain report.
        windows = [(re.sub(r"\s+", " ", body),
                    [re.sub(r"\s+", " ", b).strip()
                     for b in re.split(r"\n\s*\n", body) if b.strip()])]

    body = re.sub(r"[ \t]+", " ", body)
    return body, [t for t in titles if t], enums, windows


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


def measure(path, genre, lang=None):
    raw = path.read_text(encoding="utf-8", errors="replace")
    language, where = declared_language(path, raw, lang)
    cjk = visible_cjk(raw, path.suffix.lower()) if language == "en" else None
    body, titles, enums, windows = extract(path)
    lengths = sentences(body)
    # A Chinese document has no spaces, so the English word splitter returns
    # nothing and every Chinese deliverable came back UNMEASURABLE — which is
    # the real reason this file was English-only, underneath the docstring that
    # said so. Rhythm still does not transfer and M8 stays n/a for Chinese, but
    # "I cannot measure your sentence lengths" is not "I cannot measure your
    # document": the ban list and the punctuation pass do not need sentences.
    if not lengths and not re.search(_CJK_CHAR, body):
        raise Unmeasurable("no prose extracted (0 sentences)")

    hits = []
    for pattern, label in BANNED:
        n = len(re.findall(pattern, body, re.I | re.M))
        if n:
            hits.append((label, n))

    # The Chinese half runs only on a document that says it is Chinese. Both
    # halves are measured against the same body text; nothing here changes what
    # an English deliverable is graded on.
    is_zh = language == "zh"
    zh_hits, zh_punct = [], []
    if is_zh:
        for pattern, label in BANNED_ZH:
            n = len(re.findall(pattern, body, re.M))
            if n:
                zh_hits.append((label, n))
        zh_punct = zh_punctuation(body)

    mean = statistics.fmean(lengths) if lengths else 0.0
    cv = statistics.pstdev(lengths) / mean if len(lengths) > 1 and mean else 0.0
    overlong = (100.0 * sum(1 for n in lengths if n > OVERLONG_WORDS) / len(lengths)
                if lengths else 0.0)

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

    # M2 and M6. The windows are section 4 rule 6's: the PAGE for an ordinary
    # figure, the BLOCK for a range. Both record what they missed, because a
    # rate with no list of misses tells an author a number and not a place.
    figures = sourced = 0
    m2_missing, m6_missing = [], []
    for page_text, blocks in windows:
        page_sourced = bool(SOURCE_RE.search(page_text))
        for block in blocks:
            found = FIGURE_RE.findall(block)
            figures += len(found)
            if page_sourced:
                sourced += len(found)
            elif found:
                m2_missing.append(block[:90])
            block_sourced = bool(SOURCE_RE.search(block))
            if not block_sourced:
                m6_missing.extend(block[:90] for _ in NUMERIC_RANGE.findall(block))
    m2_rate = 100.0 * sourced / figures if figures else None

    m1_missing = [t for t in titles if not _has_fact(t)]
    m1_rate = (100.0 * (len(titles) - len(m1_missing)) / len(titles)
               if titles else None)

    return {
        "file": str(path),
        "genre": genre,
        "language": language, "language_from": where,
        "M12_visible_cjk": None if cjk is None else len(cjk),
        "M12_detail": cjk or [],
        "sentences": len(lengths),
        "titles": len(titles),
        "enumerations": len(enums),
        "M4_banned_hits": sum(n for _, n in hits),
        "M4_detail": hits,
        "M4zh_banned_hits": sum(n for _, n in zh_hits) if is_zh else None,
        "M4zh_detail": zh_hits,
        "M5_zh_punctuation": len(zh_punct) if is_zh else None,
        "M5_detail": zh_punct[:12],
        "figures": figures,
        "M1_assertive_titles": None if m1_rate is None else round(m1_rate, 1),
        "M1_detail": m1_missing,
        "M2_number_sourcing": None if m2_rate is None else round(m2_rate, 1),
        "M2_detail": m2_missing,
        "M6_unsourced_ranges": len(m6_missing),
        "M6_detail": m6_missing,
        "M8_overlong_share": round(overlong, 1),
        "M8_length_cv": round(cv, 3),
        "M9_dashes": dashes if genre in ("sales", "training") else None,
        "M10_triad_rate": None if triad_rate is None else round(triad_rate, 1),
        "M11_title_uniformity": None if uniformity is None else round(uniformity, 1),
    }


def grade(r):
    """[(metric, value, target, verdict)] — verdict is ok / FAIL / n/a."""
    thin_rhythm = r["sentences"] < MIN_SENTENCES
    rows = [
        # M12 first: a document in the wrong language is not a document whose
        # sentence rhythm is worth discussing.
        ("M12_visible_cjk", r["M12_visible_cjk"], "=0 (gates)",
         not r["M12_visible_cjk"], r["M12_visible_cjk"] is None),
        ("M4_banned_hits", r["M4_banned_hits"], "=0", r["M4_banned_hits"] == 0, False),
        # The Chinese pair. n/a on any document that is not Chinese — not "ok",
        # because a metric that passes on a document it never looked at is the
        # reassuring line this package keeps removing.
        ("M4zh_banned_hits", r["M4zh_banned_hits"], "=0",
         (r["M4zh_banned_hits"] or 0) == 0, r["M4zh_banned_hits"] is None),
        ("M5_zh_punctuation", r["M5_zh_punctuation"], "=0",
         (r["M5_zh_punctuation"] or 0) == 0, r["M5_zh_punctuation"] is None),
        ("M8_overlong_share", r["M8_overlong_share"], "<=8%",
         r["M8_overlong_share"] <= 8.0, thin_rhythm),
        ("M8_length_cv", r["M8_length_cv"], ">=0.35", r["M8_length_cv"] >= 0.35, thin_rhythm),
        ("M9_dashes", r["M9_dashes"], "=0", r["M9_dashes"] == 0, r["M9_dashes"] is None),
        # M6 first of the three: the most decidable predicate. A range figure
        # must trace to ONE source or it may not appear (writing-rules section 4
        # rule 1), so its window is its own block and its target is zero.
        ("M6_unsourced_ranges", r["M6_unsourced_ranges"], "=0",
         r["M6_unsourced_ranges"] == 0, False),
        # M2 gates. The window is the page, and a document with too few figures
        # to rate reads n/a rather than a perfect score on nothing.
        ("M2_number_sourcing", r["M2_number_sourcing"], f">={M2_TARGET:g}%",
         (r["M2_number_sourcing"] or 0) >= M2_TARGET,
         r["M2_number_sourcing"] is None or r["figures"] < MIN_FIGURES),
        # M1 REPORTS and never gates. See _has_fact: the predicate is a proxy for
        # a judgement, and a proxy that gates is a proxy authors write toward.
        ("M1_assertive_titles", r["M1_assertive_titles"],
         f">={M1_TARGET:g}% (reported)", True,
         r["M1_assertive_titles"] is None or r["titles"] < MIN_TITLES),
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
    ap.add_argument("--genre", choices=list(GENRES), default="sales",
                    help="internal analysis documents are exempt from the M9 dash "
                         "ban; training binds like sales — its readers quote it")
    ap.add_argument("--lang", default=None,
                    help="the language the deliverable claims. Overrides the "
                         "document's own lang attribute and the *.en.* filename "
                         "convention; M12 is n/a when none of the three answers.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    reports, failed = [], 0
    for name in args.files:
        path = pathlib.Path(name)
        try:
            if not path.is_file():
                raise Unmeasurable("not a readable file")
            r = measure(path, args.genre, args.lang)
        except (Unmeasurable, OSError) as exc:
            failed += 1
            print(f"FAIL  {path}: unmeasurable — {exc}", file=sys.stderr)
            reports.append({"file": str(path), "unmeasurable": str(exc)})
            continue

        rows = grade(r)
        r["verdicts"] = {n: v for n, _, _, v in rows}
        # The TARGET string, so a caller can tell a metric that could have
        # failed from one that is reported and cannot. check_fixtures.py needs
        # exactly that to say which verdicts it asserted and which it could not.
        r["targets"] = {n: t for n, _, t, _ in rows}
        failed += sum(1 for _, _, _, v in rows if v == "FAIL")
        reports.append(r)
        if args.json:
            continue

        print(f"\n{r['file']}  ({r['sentences']} sentences, {r['titles']} titles, "
              f"{r['enumerations']} lists, genre={r['genre']})")
        for name_, value, target, verdict in rows:
            note = ""
            if verdict == "n/a":
                # Each n/a states ITS OWN reason. One `else` served every metric,
                # so M12 came back "too little data: 160 sentences" on a document
                # it had skipped for declaring Chinese — a true verdict under a
                # false explanation, which is the reassuring-line failure this
                # package keeps finding in its own output.
                note = ("  (exempt for internal documents)" if name_ == "M9_dashes"
                        else f"  (this document declares "
                             f"{r['language'] or 'no language'}, per "
                             f"{r['language_from']})" if name_ == "M12_visible_cjk"
                        else f"  (too little data: {r['sentences']} sentences, "
                             f"{r['titles']} titles)")
            print(f"  {verdict:<4}  {name_:<22} {str(value):<8} target {target}{note}")
        if r["M4_detail"]:
            worst = sorted(r["M4_detail"], key=lambda kv: -kv[1])[:8]
            print("        banned: " + ", ".join(f"{p}x{n}" for p, n in worst))
        for snippet in r["M12_detail"][:6]:
            print(f"        CJK in reader text: …{snippet}…")

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print(f"\n{failed} metric failure(s)" if failed else "\nall metrics pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
