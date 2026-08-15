#!/usr/bin/env python3
"""Does anything in this deliverable cross the document boundary that should not?

This is the half of P-5 that had no execution. The other half — "every page
states how it may be handled" — has been D12 for a long time; "sensitive
information does not leave the document boundary" had nothing behind it at all.

**Three layers, because sensitivity is not one kind of question.**

Layer 1 is decidable and GATES: a credential-shaped string, or a term the user
declared out of bounds for this engagement. Both are yes/no facts about the
text — either the string is there or it is not.

Layer 2 is REPORTED: shapes that are usually but not always sensitive — an
email address, a direct phone number, a private-range host, a home directory
path. A deliverable legitimately contains a contact address; a gate here would
teach authors to delete real content to silence a checker.

Layer 3 is not mechanised at all, and says so: whether a passage of commercial
analysis is sensitive is a judgement. It appears in the pre-delivery step as a
question for a person, and this script names it rather than pretending to
answer it. A checker that implied it had covered layer 3 would be worse than
one that stops at layer 2.

**"Could not run" is not "passed".** With no out-of-bounds list supplied, the
term half of layer 1 reports `not_attempted` and the exit code is non-zero,
for the same reason `not_measured` is distinct from zero everywhere else here:
a check nobody ran must not read like a check that found nothing.

**The out-of-bounds list never enters this repository.** It is engagement data.
It is read from a path the operator supplies, it is held as strings for the
length of one run, and nothing writes it anywhere — not to a trace, not to a
report, not to the terminal beyond the count of terms loaded. Red line 9 says
this repository holds no engagement facts; a file of a client's forbidden words
is the most engagement-specific data there is.

Usage
  check_privacy.py deck.html                       # layer 1 credentials + layer 2
  check_privacy.py deck.html --terms /path/list.txt # + the declared terms
  check_privacy.py deck.html --json
"""
from __future__ import annotations

import argparse
import html as _html
import json
import pathlib
import re
import sys

# --- Layer 1 · credential shapes (decidable, gates) --------------------------
# Shapes, not entropy: a high-entropy string is often a hash of something
# public, and guessing costs an author a real deletion. Each pattern here names
# a format whose presence in a client-facing document has no innocent reading.
CREDENTIALS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."
                                  r"[A-Za-z0-9_-]{10,}\b")),
    ("credentials in a URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@")),
    ("assignment of a secret", re.compile(
        r"\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*"
        r"[\"']?[A-Za-z0-9_\-/+]{12,}", re.I)),
]

# --- Layer 2 · usually-but-not-always (reported) -----------------------------
LIKELY = [
    ("email address", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    # A phone number, not "any long run of digits". It must be preceded by a
    # country code or carry the separators a phone number carries, and it must
    # not sit inside a word — the first version called an SVG path coordinate
    # run and the digits inside an API token phone numbers, and layer 2 noise
    # is what makes a reported finding get ignored.
    ("direct phone number", re.compile(
        r"(?<![\w.-])(?:\+\d{1,3}[ -]\d[\d -]{6,}\d"
        r"|\(\d{3}\)\s?\d{3}[ -]\d{4}"
        # the trailing guard excludes a letter or digit, NOT punctuation: a
        # phone number at the end of a sentence is followed by a full stop
        r"|\b\d{3}[ -]\d{3}[ -]\d{4}\b)(?![\w-])(?![ -]?\d)")),
    ("private-range host", re.compile(
        r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")),
    ("home directory path", re.compile(r"(?:/Users/|/home/|C:\\\\Users\\\\)[A-Za-z0-9._-]+")),
    ("internal hostname", re.compile(r"\b[\w-]+\.(?:internal|corp|local|lan|intranet)\b")),
]

# A source line naming a public dataset is not a leak, and neither is the
# origin site D12 requires on every page.
EXEMPT_CONTEXT = re.compile(r"(?:source|来源|资料来源)\s*[:：]", re.I)


TAG = re.compile(r"<[^>]+>")


def whole_file(raw: str) -> str:
    """What layer 1 searches: everything. A credential in a `data-` attribute
    has left the document boundary just as surely as one in a paragraph."""
    return _html.unescape(raw)


def reader_text(raw: str) -> str:
    """What layer 2 searches: only what a reader sees.

    Layer 2 is about contact details a reader could act on, so markup is not
    its business — and scanning it produced pure noise. The geography SVG's
    `data-arcs` attribute is a list of a few hundred indices, and
    "104 105 1061" is phone-shaped. Six findings on a clean fixture, none of
    them a phone number: exactly the volume that teaches a reader to skip the
    reported section.
    """
    return _html.unescape(TAG.sub(" ", raw))


def load_terms(path: pathlib.Path | None):
    """-> (terms, status). Terms are held as strings for one run and written
    nowhere. `status` is 'not_attempted' when no list was supplied."""
    if path is None:
        return [], "not_attempted"
    if not path.is_file():
        return [], "missing"
    terms = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    return terms, "loaded"


def scan(raw: str, terms):
    """Layer 1 over the whole file, layer 2 over what a reader sees."""
    text = whole_file(raw)
    visible = reader_text(raw)
    layer1, layer2 = [], []
    for label, pattern in CREDENTIALS:
        for m in pattern.finditer(text):
            layer1.append({"layer": 1, "kind": label, "where": _where(text, m.start())})
    for term in terms:
        for m in re.finditer(re.escape(term), text, re.I):
            # the term itself is never echoed: it is engagement data
            layer1.append({"layer": 1, "kind": "declared out of bounds",
                           "where": _where(text, m.start())})
    for label, pattern in LIKELY:
        for m in pattern.finditer(visible):
            line_start = visible.rfind("\n", 0, m.start()) + 1
            if EXEMPT_CONTEXT.search(visible[line_start:m.start()]):
                continue
            layer2.append({"layer": 2, "kind": label,
                           "where": _where(visible, m.start())})
    return layer1, layer2


def _where(text: str, pos: int) -> str:
    return f"line {text.count(chr(10), 0, pos) + 1}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--terms", type=pathlib.Path,
                    help="a file of terms declared out of bounds for this "
                         "engagement, one per line. Never committed, never "
                         "echoed, never written to a trace.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    terms, status = load_terms(a.terms)
    reports, worst = [], 0
    for name in a.files:
        path = pathlib.Path(name)
        if not path.is_file():
            print(f"FAIL  {name}: no such file", file=sys.stderr)
            worst = max(worst, 2)
            continue
        layer1, layer2 = scan(path.read_text(encoding="utf-8", errors="replace"), terms)
        report = {
            "file": name,
            "layer1_gating": layer1,
            "layer2_reported": layer2,
            "declared_terms": status if status != "loaded" else len(terms),
            "layer3": "not mechanised — whether a passage of commercial analysis "
                      "is sensitive is a judgement, and it belongs to the "
                      "pre-delivery step",
            "verdict": "FAIL" if layer1 else
                       ("not_attempted" if status == "not_attempted" else "ok"),
        }
        reports.append(report)
        if layer1:
            worst = max(worst, 1)
        elif status == "not_attempted":
            worst = max(worst, 1)

    if a.json:
        print(json.dumps(reports, indent=1, ensure_ascii=False))
        return sys.exit(worst)

    for r in reports:
        print(f"\n{r['file']}")
        for f in r["layer1_gating"]:
            print(f"  FAIL  layer 1 · {f['kind']} · {f['where']}")
        for f in r["layer2_reported"]:
            print(f"  note  layer 2 · {f['kind']} · {f['where']}")
        if r["declared_terms"] == "not_attempted":
            print("  FAIL  layer 1 · declared terms: NOT ATTEMPTED — no list was "
                  "supplied, so this half did not run.\n"
                  "        A check nobody ran is not a check that found nothing. "
                  "Pass --terms, or record\n"
                  "        the omission against an open KNOWN_GAPS entry.")
        elif r["declared_terms"] == "missing":
            print("  FAIL  layer 1 · declared terms: the file given to --terms "
                  "does not exist")
        elif not r["layer1_gating"]:
            print(f"  ok    layer 1 · {r['declared_terms']} declared term(s), none present")
        print("  ——    layer 3 is a person's: is any commercial analysis here "
              "sensitive? This\n"
              "        script does not answer that and does not imply it has.")
    sys.exit(worst)


if __name__ == "__main__":
    main()
