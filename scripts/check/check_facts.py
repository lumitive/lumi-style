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

import figure_scale  # noqa: E402
import figure_spec  # noqa: E402 — after the bootstrap
import markup  # noqa: E402 — after the bootstrap

# A quantity worth tracking: currency, percentage, or a grouped/multi-digit
# number. A bare single digit is usually a count derived on the page ("4 gates")
# and tracking it would drown the signal in arithmetic.
# The magnitude suffix carries a WORD BOUNDARY. Without it `[kmb]` consumed the
# first letter of the following word: `$10.95 Meal` normalised to ten million
# and `$9.00 back` to nine billion. It corrupted both sides of the comparison
# and which side depended on the sentence around the figure, so a contract and
# a document stating one price disagreed if one of them was followed by "Meal".
#
# The unit alternative (`75mg`, `4g`) is there because a dose was invisible to
# all three patterns: a contract stating 150mg and a document stating the same
# could never be compared, which is a hole in the gate rather than a quiet pass.
QUANTITY = re.compile(
    r"[$€£¥]\s?\d[\d,.]*(?:\s*(?:[kmb]|billion|million|thousand)\b)?"
    r"|\d[\d,.]*\s*(?:%|percent|¢|cents?)"
    r"|\b\d[\d,.]*\s*(?:mg|kcal|g)\b"
    r"|\b\d[\d,]{1,}(?:\.\d+)?\b", re.I)

# A filename: any run of non-space characters ending in one of the extensions a
# source file actually carries here. Deliberately not "anything with a dot" --
# that eats `$1.2m` and every sentence-ending decimal.
FILENAME = re.compile(
    r"\S*\.(?:html?|md|json|csv|tsv|pdf|pptx?|docx?|xlsx?|png|jpe?g|svg|py|js|css)\b",
    re.I)

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
# THE LEADING BOUNDARY WAS THE BUG. `\b` before the first digit is satisfied by
# a space and defeated by a letter, so `v0.1.597` kept its stamp and `\b597`
# then matched QUANTITY: a colophon typed with a `v` invented an unsourced
# number and tripped the gate that guards red line 1, while the bare form went
# through. Which way it fell depended on how the author typed a version string
# nobody reads as a claim (0.1.599).
VERSION = re.compile(r"(?<![\w.])v?\d+\.\d+\.\d+(?!\d)", re.I)
# A caption ordinal, a page number and a step number are the document's own
# apparatus. `FURNITURE` above has said so since it was written — and it is
# consulted only in the PROPER-NOUN branch, so the quantity branch never saw
# it. `Figure 3` was invisible only because QUANTITY's last alternative needs
# two digits; `Figure 10` was a claim about a quantity. Four words, each one
# already declared furniture somewhere in this file, and no more: `table`,
# `exhibit` and `section` are speculation until a document produces one
# (convention 2).
ORDINAL_LABEL = re.compile(r"\b(?:figure|fig\.?|page|step)\s*0*\d+\b", re.I)
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
    # AN AXIS TICK IS A SCALE MARK, NOT A CLAIM. `figure_scale.ticks` computes
    # `0 5 10 15 20` from the data's own ceiling; no author states them, and
    # they change when one datum changes. Counting them made the first deck
    # built through the figure contract fail red line 1 on 10 and 20 — numbers
    # nobody wrote — and the cheapest way to clear that is to add them to the
    # fact contract, which is the checker writing the document. Only `.ftick`
    # goes: `.fval` and `.flbl` carry the values and names a reader is asked to
    # believe, and they stay.
    s = re.sub(r'<text[^>]*class="(?:[^"]*\s)?ftick(?:\s[^"]*)?"[^>]*>.*?</text>',
               " ", s, flags=re.S | re.I)
    s = markup.visible_text(s)
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
    # BEFORE the ordinal strip below rather than instead of it: this one takes
    # the whole label ("Figure 10", "Page 00"), that one takes a bare
    # zero-padded ordinal wherever it stands. The lookahead below cannot do
    # this job — `(?<![\d.])0\d(?![\d.])` is defeated by the full stop in
    # "Page 00." and never saw a two-digit caption at all.
    s = ORDINAL_LABEL.sub(" ", s)
    # BEFORE the ordinal strip below, which would otherwise take the `00` out of
    # `22:00` and leave a bare `22` that the clock rule in `facts()` can no
    # longer recognise. Two strips in two files is not duplication here: this
    # one protects the ordering, and the one in `facts()` covers the contract
    # side, which never passes through this function.
    s = re.sub(r"\b\d{1,2}:\d{2}\b", " ", s)
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
    # A clock time is furniture and its minutes read as a quantity: `22:00`
    # produced a bare `0`. Stripped HERE rather than in `_visible`, because the
    # contract side never passes through `_visible` and a time in the contract
    # parsed the same wrong way.
    text = re.sub(r"\b\d{1,2}:\d{2}\b", " ", text)
    # A FILENAME is provenance of the same class. A converted deck names the
    # file it was converted from and that name usually carries a date, so
    # `Lumi-Agent-\u4ecb\u7ecd 260819.html` reported 260819 as an invented figure and
    # gated a document whose every real figure was sourced. Only the token
    # ending in a known extension goes; a figure standing beside a filename is
    # still a figure.
    text = FILENAME.sub(" ", text)
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


SPEC_DECL = re.compile(r'data-figure-spec="([^"]+)"')

# Every number in a text, INCLUDING a lone digit and a sub-1 decimal. This is
# the contract's side of the figure comparison and it is deliberately not
# `QUANTITY`: a spec states nothing but claims, so both sides have to be able
# to express the same values or the comparison is between two vocabularies.
# `QUANTITY` keeps its prose reach unchanged; red line 1's existing verdict is
# computed exactly as before.
SPEC_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def spec_quantities(doc_html: str, base) -> tuple[set[str], list[str]]:
    """-> (the quantities the declared figure specs carry, problems reading them).

    **The hole this closes.** `_visible` strips `<svg>`, so a drawn figure's
    numbers were invisible to this check: a deck could state a market size only
    inside its chart and `unsourced` would be empty. The figure spec is where
    those numbers now live, so they are read from the spec and held to the
    contract like any other quantity in the document.

    **The spec is never the contract.** `unsourced = document quantities −
    contract quantities`; if one file were both, that set would be empty
    forever and red line 1's only instrument would go blind. `main` refuses a
    run whose contract is one of the document's own declared specs, so the
    rule is a mechanism rather than a sentence.
    """
    declared = SPEC_DECL.findall(doc_html)
    if base is None:
        if not declared:
            return set(), []
        # NOT the clean answer. `(set(), [])` is bit-for-bit what a document
        # with no specs returns, so a caller with no directory printed exactly
        # what a document with no figures prints — the hole this function was
        # written to close, reopened by its own default argument.
        return set(), [f"{len(declared)} figure spec(s) are declared and no "
                       f"document directory was given, so none of the numbers "
                       f"they hold were compared with the contract"]
    out: set[str] = set()
    problems: list[str] = []
    for m in SPEC_DECL.finditer(doc_html):
        ref = m.group(1)
        spec, problem = figure_spec.load(base / ref)
        if problem or spec is None:
            problems.append(problem or f"{ref}: no spec came back")
            continue
        # NUMBERS AS NUMBERS, never round-tripped through the prose regex.
        # `QUANTITY` deliberately ignores a lone digit and cannot start on
        # `0.` — right for prose, where "one of three" is not a claim, and
        # wrong for a spec, where every value is. Sent through it, `0.08` came
        # back as the quantity **8** and `0.5` came back as nothing.
        out |= {_canonical(v) for v in _spec_values(spec)}
    return out, problems


def _canonical(value) -> str:
    """-> a number written the way `facts()` writes the ones it finds in prose.

    One spelling on both sides of the comparison or the comparison is between
    two vocabularies. `_value` is what normalises the contract's side.
    """
    text = f"{value:g}" if isinstance(value, float) else str(value)
    return _value(text) or text


def _spec_values(spec) -> list:
    """-> every number a spec states AS A QUANTITY, wherever its move keeps it.

    Two exclusions, and both are AG-10 — a gate a correct answer cannot satisfy
    does not get obeyed, it gets satisfied:

    **A `position` item's `x` and `y` are not quantities.** A two-by-two's axes
    are ordinal, and `quadrant_svg` refuses any placement outside 0 to 1 for
    exactly that reason: the number claims no precision, it says which side of
    the middle the item sits on. A fact contract cannot list 0.42, because
    0.42 is not a fact about the world. Held to this, a correct integration
    matrix reported eight unsourced quantities and the only ways to clear them
    were to invent facts or to delete the figure. `correlate` points keep their
    `x` and `y`: those ARE the measured data.

    **A key called `x` whose value is not a number is not a value.** `axes.x`
    is the x AXIS — a mapping of name, unit and the ramp's ends — and it was
    being appended whole and stringified, so the report named a dict among the
    unsourced numbers. Only numeric leaves are collected now.
    """
    found: list = []
    ordinal = str(spec.get("move") or "").lower() == "position"

    def take(v):
        if figure_scale.num(v) is not None:
            found.append(v)

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("value", "delta"):
                    take(v)
                elif k in ("x", "y"):
                    if ordinal:
                        continue        # a placement, not a measurement
                    if isinstance(v, (dict, list)):
                        walk(v)         # `axes.x` is an axis, not a value
                    else:
                        take(v)
                elif k == "values":
                    for one in (v or []):
                        take(one)
                else:
                    walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(spec)
    return found


def compare(contract: str, doc_html: str, base=None) -> dict:
    doc = _visible(doc_html)
    cq, cn = facts(permitted(contract))
    dq, _dn = facts(doc)
    sq, spec_problems = spec_quantities(doc_html, base)
    # A SEPARATE VERDICT, against a separate reading of the contract. Folding
    # the specs' values into `dq` compared exact numbers with prose-scraped
    # ones and reported four correct values as unsourced.
    permitted_numbers = {_canonical(m.group(0))
                         for m in SPEC_NUMBER.finditer(permitted(contract))}
    unsourced_specs = sorted(v for v in sq if v not in permitted_numbers)
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
    everything, _ = facts(markup.visible_text(doc_html),
                          names=False)
    unmeasurable = not dq and bool(everything)
    return {"contract_quantities": len(cq), "contract_names": len(cn),
            "absent_quantities": absent_q, "absent_names": absent_names,
            "unsourced_quantities": unsourced, "unmeasurable": unmeasurable,
            "spec_quantities": len(sq), "spec_problems": spec_problems,
            "unsourced_spec_values": unsourced_specs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("contract", type=pathlib.Path)
    ap.add_argument("document", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    for p in (a.contract, a.document):
        if not p.is_file():
            sys.exit(f"no such file: {p}")

    doc_html = a.document.read_text(encoding="utf-8")
    # THE SPEC MAY NEVER BE THE CONTRACT, and this is the mechanism rather than
    # the sentence. `unsourced = document quantities − contract quantities`; one
    # file as both makes that set empty forever and red line 1's only instrument
    # goes blind. The contract is written from the engagement, the spec is
    # written for a figure, and the check is that they agree.
    declared = {(a.document.parent / m.group(1)).resolve()
                for m in SPEC_DECL.finditer(doc_html)}
    if a.contract.resolve() in declared:
        sys.exit(
            f"{a.contract} is one of {a.document.name}'s own figure specs. A "
            f"document cannot be its own fact contract: `unsourced` would be "
            f"empty by construction and this check would report clean on any "
            f"document at all. Write the contract from the engagement.")

    r = compare(a.contract.read_text(encoding="utf-8"), doc_html,
                base=a.document.parent)
    if a.json:
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 1 if (r["unsourced_quantities"] or r["unmeasurable"]
                     or r["spec_problems"] or r["unsourced_spec_values"]) else 0

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
    if r["spec_problems"]:
        print(f"  FAIL  figure specs           {len(r['spec_problems'])} "
              f"declared spec(s) could not be read, so the numbers they hold "
              f"were NOT compared: " + "; ".join(r["spec_problems"][:3]))
    elif r["spec_quantities"]:
        bad = r["unsourced_spec_values"]
        print(f"  {'FAIL' if bad else 'ok  '}  figure spec values     "
              f"{len(bad)} of {r['spec_quantities']} unsourced (gates — red "
              f"line 1): " + ", ".join(bad[:12]))
        print(f"  note  `<svg>` is stripped as decorative, so before 0.1.671 "
              f"every one of those {r['spec_quantities']} numbers was "
              f"invisible to this comparison")
    print(f"  note  absent from the document  {n} of "
          f"{r['contract_quantities'] + r['contract_names']} permitted facts")
    for x in r["absent_names"][:20]:
        print(f"          name  {x}")
    for x in r["absent_quantities"][:20]:
        print(f"          value {x}")
    return 1 if (r["unsourced_quantities"] or r["unmeasurable"]
                 or r["spec_problems"] or r["unsourced_spec_values"]) else 0


if __name__ == "__main__":
    sys.exit(main())
