#!/usr/bin/env python3
"""Hold a built document to the fact list it was built from.

A rebuild is where facts go missing. Measured on two consecutive builds of one
business plan: the second silently dropped eleven facts the first carried --
four platform names, FIVE OF THE SEVEN MARKET NAMES the deck still claims a
count of, and two delivery figures -- and every one of the forty-odd gates in
this package reported green, because not one of them had anything to compare
the document to.

So this compares the document to its own source of facts, in both directions:

  ABSENT   a fact the contract permits and the document does not carry.
           REPORTED. A deck legitimately omits facts; a deck that names two of
           the seven markets whose count it states is a different thing, and a
           person can tell them apart in one line of output.

  UNSOURCED a quantity the document states that the contract does not.
           GATES. This is red line 1 -- no invented facts -- and it is the
           hardest rule the package has.

Both directions are CONSISTENCY, never judgement. The check cannot say whether
a fact is worth carrying; it says whether the document and its fact list agree.

Standard library only.

Usage
  check_facts.py CONTRACT.md deck.html
  check_facts.py CONTRACT.md deck.html --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from html import unescape

# A quantity worth tracking: currency, percentage, or a grouped/multi-digit
# number. A bare single digit is usually a count derived on the page ("4 gates")
# and tracking it would drown the signal in arithmetic.
QUANTITY = re.compile(
    r"[$€£¥]\s?\d[\d,.]*\s*(?:[kmb]|billion|million|thousand)?"
    r"|\d[\d,.]*\s*(?:%|percent|¢|cents?)"
    r"|\b\d[\d,]{1,}(?:\.\d+)?\b", re.I)

# A proper noun: two or more capitalised words, or a single capitalised word
# that is not a sentence opener. Kept deliberately narrow -- the point is to
# catch NAMES the document dropped (markets, platforms, partners).
# The third alternative admits an acronym carrying digits. Protocol names are
# the shape this module was built to protect -- MCP, A2A, AP2, A2UI -- and the
# letters-only pattern reached MCP and IBM while A2A and AP2 were invisible,
# which is half a guard against exactly the defect it names.
PROPER = re.compile(r"\b(?:[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+|"
                    r"[A-Z][A-Za-z]{2,}(?=\s|,|\.|$)|"
                    r"[A-Z][A-Z0-9]{1,}[A-Z0-9](?=\s|,|\.|$))")

# Things that are page furniture, not facts.
FURNITURE = re.compile(r"^\d+\s*/\s*\d+$|^figure\s*\d+$|^\d{4}-\d{2}(-\d{2})?$",
                       re.I)
# The package's own version stamp rides every colophon. It is provenance, not a
# claim the contract has to authorise.
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")
STOP_NOUNS = frozenset("""
The This That These Those Source Sources Every Each Which What When Where Why
Not Note Only One Two Three Four Five Six Seven Eight Nine Ten Part Page Figure
And But For With From Into Over Under After Before Their There They Then Than
Our Your His Her Its About Above Below Across Against Between Through During
Without Within Because Since Until While Both Some Most Many Much More Less
Live Dead Open Closed Ready Real True False Yes Nope Ask Read Write Build Draw
""".split())


def _visible(html: str) -> str:
    """Every word a reader sees as a CLAIM.

    The brand globe and the region map carry city names, bloc codes and
    coordinates as `<text>`. Those are geometry, not assertions, and counting
    them made the first run of this check report 391732 as an unsourced
    quantity. A drawing that decorates is excluded; a drawing that argues is
    inside `.fig` and stays.
    """
    s = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", " ",
               html, flags=re.S | re.I)
    # Matched as WHITESPACE-DELIMITED class tokens. `\b` treats `-` as a word
    # boundary, so `ground-truth` and `gl-panel` were read as decorative and
    # had every figure they carried deleted before measurement. Third time this
    # bug class has shipped here; see the repo's note on `\bcard\b` matching
    # `f-card`.
    s = re.sub(r'<svg[^>]*class="(?:[^"]*\s)?(?:gl|ground)(?:\s[^"]*)?".*?</svg>',
               " ", s, flags=re.S | re.I)
    s = " ".join(unescape(re.sub(r"<[^>]+>", " ", s)).split())
    s = re.sub(r"\b\d{1,3}\s*/\s*\d{1,3}\b", " ", s)
    # A telephone number is contact furniture. Left in, its runs read as three
    # separate invented quantities, and the author is told their phone number
    # is not in the contract.
    s = re.sub(r"\+\d[\d\s()-]{6,}\d", " ", s)
    s = VERSION.sub(" ", s)
    # An ISO date is provenance, and a zero-padded ordinal is a step number.
    # Both are furniture: without these two the check reported `08` eighteen
    # times, once per source line, and `02`/`03`/`04` once per numbered stage.
    s = re.sub(r"\b\d{4}-\d{2}(?:-\d{2})?\b", " ", s)
    return re.sub(r"(?<![\d.])0\d(?![\d.])", " ", s)


def permitted(contract: str) -> str:
    """The contract's FACT section and nothing else.

    A part-author contract is mostly instructions -- register, punctuation, the
    page skeleton. Scanning all of it made `American English` and `DASHED` read
    as facts the document had dropped. The facts live under a heading that says
    so; everything above it is how to write, not what is true.
    """
    m = re.search(r"^#+\s*FACTS\b.*$", contract, re.M | re.I)
    text = contract[m.start():] if m else contract
    return re.sub(r"\b\d{4}-\d{2}(?:-\d{2})?\b", " ", text)


def _value(tok: str) -> str | None:
    """A quantity as a comparable number, unit words and symbols removed.

    `0.85¢` in a drawing and `0.85 cents` in a contract are the same fact, and
    the first version of this check compared them as strings and called one of
    them invented.
    """
    m = re.search(r"\d[\d,]*(?:\.\d+)?", tok)
    if not m:
        return None
    v = m.group(0).replace(",", "")
    mult = 1
    tail = tok[m.end():].lower()
    if re.match(r"\s*(k|thousand)\b", tail):
        mult = 1_000
    elif re.match(r"\s*(m|million)\b", tail):
        mult = 1_000_000
    elif re.match(r"\s*(b|billion)\b", tail):
        mult = 1_000_000_000
    try:
        n = float(v) * mult
    except ValueError:
        return None
    return f"{n:.0f}" if n == int(n) else f"{n:g}"


def _is_year(token: str) -> bool:
    """A bare 1900-2099 integer is a date, not a quantity.

    Nothing else in this module could tell `2027` from `2027 units`, so a deck
    naming the years of its own roadmap failed the gate that guards red line 1
    — and the author's cheapest way to green was to delete a correct year. A
    year carrying a currency or percent marker is not caught here: `$2027` and
    `2027%` are claims and stay claims.
    """
    t = token.strip()
    return bool(re.fullmatch(r"\d{4}", t)) and 1900 <= int(t) <= 2099


def facts(text: str, names: bool = True) -> tuple[set[str], set[str]]:
    """-> (quantities as comparable values, proper nouns).

    A NAME has to earn the label. Capitalisation alone made section headings and
    sentence openers -- `Business`, `Case`, `Cost`, `Evaluation` -- read as facts
    the document had dropped, which is sixty lines of noise around the four that
    mattered. A real name appears mid-sentence at least once: preceded by a
    lowercase word or a comma, somewhere in the source. Multi-word names are
    taken as they are.
    """
    q = {v for m in QUANTITY.finditer(text)
         if not _is_year(m.group(0)) and (v := _value(m.group(0)))}
    if not names:
        return q, set()
    body = " ".join(re.sub(r"^#+.*$|\*\*", " ", text, flags=re.M).split())
    out = set()
    for m in PROPER.finditer(body):
        tok = m.group(0).strip()
        if tok in STOP_NOUNS or FURNITURE.match(tok):
            continue
        if " " in tok or tok.isupper():
            # An ACRONYM is admitted on sight. The measured defect this whole
            # module exists for was a rebuild dropping four PLATFORM names, and
            # platform and protocol names are acronym-shaped -- MCP, A2A, AP2.
            # Excluding them, as the first version did, made the check blind in
            # its own headline case.
            out.add(tok)
            continue
        # A single capitalised word is admitted unless it is a known opener.
        # The first version asked instead whether the word ever appeared
        # PRECEDED by a lowercase word or a comma, which is a proxy for
        # mid-sentence -- and it is false for every name in a BULLETED fact
        # list, where each line begins `- Berlin ...`. A list is the natural
        # shape for a FACTS section, and the check returned zero names from
        # one, reporting `0 of 0 permitted facts` on a document that had
        # dropped everything.
        out.add(tok)
    return q, out


def compare(contract: str, doc_html: str) -> dict:
    doc = _visible(doc_html)
    cq, cn = facts(permitted(contract))
    dq, _dn = facts(doc)
    absent_names = sorted(x for x in cn if x not in doc)
    absent_q = sorted(x for x in cq if x not in dq)
    unsourced = sorted(x for x in dq if x not in cq)
    # UNMEASURABLE, and the distinction is the point. `dq` comes back empty
    # both when a document invents nothing and when everything it states sits
    # in a region `_visible` strips -- and the first version printed the same
    # reassuring `ok` for both. A document whose every figure is drawn inside
    # an excluded `<svg>` was graded clean while claiming markets, revenue and
    # customers the contract had never heard of.
    #
    # The test is comparative rather than a size threshold: strip the tags but
    # NOT the exclusions, and if that text carries quantities while the visible
    # text carries none, then the exclusions ate the whole document and this
    # check has no opinion to offer. `check_design.py` reports UNMEASURABLE on
    # a document that declares no token block for the same reason.
    everything, _ = facts(" ".join(re.sub(r"<[^>]+>", " ", doc_html).split()),
                          names=False)
    unmeasurable = not dq and bool(everything)
    return {"contract_quantities": len(cq), "contract_names": len(cn),
            "absent_quantities": absent_q, "absent_names": absent_names,
            "unsourced_quantities": unsourced, "unmeasurable": unmeasurable}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("contract", type=pathlib.Path)
    ap.add_argument("document", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    for p in (a.contract, a.document):
        if not p.is_file():
            sys.exit(f"no such file: {p}")

    r = compare(a.contract.read_text(encoding="utf-8"),
                a.document.read_text(encoding="utf-8"))
    if a.json:
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 1 if (r["unsourced_quantities"] or r["unmeasurable"]) else 0

    print(f"{a.document.name} against {a.contract.name}\n")
    n = len(r["absent_names"]) + len(r["absent_quantities"])
    if r["unmeasurable"]:
        print("  FAIL  unsourced quantities   UNMEASURABLE (gates): this "
              "document states quantities, and every one of them sits in a "
              "region this check strips as decorative. It has not been "
              "graded — do not read this as a clean run.")
    else:
        print(f"  {'FAIL' if r['unsourced_quantities'] else 'ok  '}  "
              f"unsourced quantities   {len(r['unsourced_quantities'])} "
              f"(gates — red line 1): " + ", ".join(r["unsourced_quantities"][:12]))
    print(f"  note  absent from the document  {n} of "
          f"{r['contract_quantities'] + r['contract_names']} permitted facts")
    for x in r["absent_names"][:20]:
        print(f"          name  {x}")
    for x in r["absent_quantities"][:20]:
        print(f"          value {x}")
    return 1 if (r["unsourced_quantities"] or r["unmeasurable"]) else 0


if __name__ == "__main__":
    sys.exit(main())
