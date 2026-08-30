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
It is read from a path the operator supplies — or, with no path, from every
`*.terms.txt` under `~/.lumi/terms/`, the cross-engagement home
references/operating-rules.md OR-8 names — it is held as strings for the
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
import html
import json
import os
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
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
import secret_patterns  # noqa: E402 — after the bootstrap

# --- Layer 1 · credential shapes (decidable, gates) --------------------------
# The table is scripts/lib/secret_patterns.py, shared with check_repo's
# secrets guard; the `secret patterns parity` guard keeps it the only one.
CREDENTIALS = secret_patterns.PATTERNS

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




def whole_file(raw: str) -> str:
    """What layer 1 searches: everything. A credential in a `data-` attribute
    has left the document boundary just as surely as one in a paragraph."""
    return html.unescape(raw)


def actionable_text(raw: str) -> str:
    """What layer 2 searches: only what a reader sees.

    Layer 2 is about contact details a reader could act on, so markup is not
    its business — and scanning it produced pure noise. The geography SVG's
    `data-arcs` attribute is a list of a few hundred indices, and
    "104 105 1061" is phone-shaped. Six findings on a clean fixture, none of
    them a phone number: exactly the volume that teaches a reader to skip the
    reported section.

    **Not `reader_text`, which is what this was called until 0.1.634.**
    `markup.reader_text` is a DIFFERENT corpus — visible text minus what only a
    machine reads — and this scan deliberately keeps the machine-only part: a
    phone number inside a `<style>` comment has still left the document. One
    name for two corpora is how the `single-source` register found this, and
    the two are kept apart rather than merged.
    """
    return markup.strip_tags(raw)


# The statuses in which the term half DID NOT RUN. Named once, because the
# verdict expression and the exit ladder both consulted `not_attempted` by hand
# and `missing` was added to `load_terms` without either learning about it: a
# typo in --terms scored BETTER than omitting the flag, exiting 0 with verdict
# "ok". The list is engagement data living outside this repository, so a moved
# or stale path is the expected failure rather than an exotic one.
DID_NOT_RUN = ("not_attempted", "missing")


# Where the out-of-bounds lists live when no --terms is given: one file per
# engagement, accumulated across engagements (the owner's 2026-08-15 ruling),
# outside every repository. The location is named in
# references/operating-rules.md (OR-8) and nowhere else is a copy of it —
# this constant reads the same string the rule states.
TERMS_DIR = pathlib.Path(os.environ.get("LUMI_TERMS_DIR")
                         or pathlib.Path.home() / ".lumi" / "terms")
TERMS_GLOB = "*.terms.txt"


def _read_terms(path: pathlib.Path) -> list[str]:
    # `.strip()` before the comment test so an indented `# note` is a comment,
    # not a live term (it would otherwise be scanned for verbatim).
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def load_terms(path: pathlib.Path | None):
    """-> (terms, status). Terms are held as strings for one run and written
    nowhere. With no --terms, every `*.terms.txt` under ~/.lumi/terms/ is
    loaded (the cross-engagement list); `status` is 'not_attempted' when
    neither a path nor that directory yields a list."""
    if path is not None:
        if not path.is_file():
            return [], "missing"
        return _read_terms(path), "loaded"
    lists = sorted(TERMS_DIR.glob(TERMS_GLOB)) if TERMS_DIR.is_dir() else []
    if not lists:
        return [], "not_attempted"
    terms: list[str] = []
    for f in lists:
        terms.extend(_read_terms(f))
    return terms, "loaded"


# What a term scan must NOT read: an embedded font or image is base64, and a
# three-letter Latin term ("Ray") fired six times inside one font on a real
# build (IDEA-15) — the term had to be dropped from the list to keep the check
# usable, which is a privacy check weakened in production. `data:` URIs and
# long base64 runs are blanked before the term scan only; the credential scan
# keeps the whole file because a JWT is base64 by construction.
_DATA_URI = re.compile(r"data:[\w.+-]+/[\w.+-]+;base64,[A-Za-z0-9+/=\s]+")
_BASE64_RUN = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/])")


def term_text(text: str) -> str:
    """The file with its binary payloads blanked, same length so `_where`
    still points at the right line."""
    text = _DATA_URI.sub(lambda m: " " * len(m.group(0)), text)
    return _BASE64_RUN.sub(lambda m: " " * len(m.group(0)), text)


def term_pattern(term: str) -> re.Pattern[str]:
    """A pure-Latin term matches on word boundaries; anything carrying a CJK
    character or punctuation matches as a substring, because those scripts
    do not put spaces where a boundary would be."""
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 '&.-]*[A-Za-z0-9]|[A-Za-z0-9]", term):
        return re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", re.I)
    return re.compile(re.escape(term), re.I)


def scan(raw: str, terms):
    """Layer 1 over the whole file, layer 2 over what a reader sees."""
    text = whole_file(raw)
    visible = actionable_text(raw)
    layer1, layer2 = [], []
    for label, pattern in CREDENTIALS:
        for m in pattern.finditer(text):
            layer1.append({"layer": 1, "kind": label, "where": _where(text, m.start())})
    scannable = term_text(text)
    for term in terms:
        for m in term_pattern(term).finditer(scannable):
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
                    help="a file of terms declared out of bounds, one per line; "
                         "default: every *.terms.txt under ~/.lumi/terms/. Never "
                         "committed, never echoed, never written to a trace.")
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
            # A loaded-but-empty list (comment-only *.terms.txt) means the scan
            # had nothing to search for — the same "did not run" as a missing
            # list, and it must not read as clean (GAP-047, FM-24). The gating
            # question is `not terms`, not `status in DID_NOT_RUN`.
            "verdict": "FAIL" if layer1 else
                       (status if status in DID_NOT_RUN else
                        ("no_terms" if not terms else "ok")),
        }
        reports.append(report)
        if layer1 or not terms:
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
                  "supplied and ~/.lumi/terms/ holds none, so this half did not run.\n"
                  "        A check nobody ran is not a check that found nothing. "
                  "Pass --terms, put a\n"
                  "        *.terms.txt under ~/.lumi/terms/ (OR-8), or record the "
                  "omission against an\n        open KNOWN_GAPS entry.")
        elif r["declared_terms"] == "missing":
            print("  FAIL  layer 1 · declared terms: the file given to --terms "
                  "does not exist")
        elif r["declared_terms"] == 0:
            print("  FAIL  layer 1 · declared terms: a list was found but held "
                  "no usable terms (comment-only or empty), so this half had "
                  "nothing to search for and did not run.")
        elif not r["layer1_gating"]:
            print(f"  ok    layer 1 · {r['declared_terms']} declared term(s), none present")
        print("  ——    layer 3 is a person's: is any commercial analysis here "
              "sensitive? This\n"
              "        script does not answer that and does not imply it has.")
    sys.exit(worst)


if __name__ == "__main__":
    main()
