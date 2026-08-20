#!/usr/bin/env python3
"""Accept a language model's findings about a document — only with quotations.

A judge that scores gets fooled by fluent verbosity; that is measured, and it is
why C1–C7 is ticked rather than rated. But a judge that points at a specific
sentence and says what is wrong with it is doing something a metric cannot: it
reads register, and register is the half of P-3 that will not mechanise.

So the contract is narrow and the enforcement is the whole point:

**Every finding carries a verbatim quotation, and the quotation must appear in
the document.** Not "resemble", not "paraphrase" — appear. A model that cannot
produce the sentence it is objecting to has not found anything, and this is
where a hallucinated finding dies. The check is a substring match after
whitespace normalisation, which a real quotation survives and an invented one
does not.

**No scores.** There is no field for one. A finding is a location, a claim, and
the words it rests on.

**Reported, never gating.** These are opinions with evidence attached, and the
one thing worse than ignoring them would be gating on them: an author would
then be editing a document to satisfy a model's taste, which is the register
this whole rule set exists to keep out.

Input — JSON, from whatever produced it:

    [{"where": "p4 title", "claim": "sounds like a press release",
      "quote": "revolutionising how teams unlock value"}]

Usage
  judge_findings.py findings.json --document deck.html
  judge_findings.py findings.json --document deck.html --json
"""
from __future__ import annotations

import argparse
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
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

FIELDS = {"where", "claim", "quote"}
MIN_QUOTE_WORDS = 3


def normalise(text: str) -> str:
    """Whitespace-flattened plain text. A real quotation survives this; the
    line breaks and markup a model did not see are what it must not be held to."""
    return markup.visible_text(text).lower()


def review(findings, document_text: str):
    """-> (accepted, rejected). Rejection is a fact about the finding, not a
    judgement about the document."""
    haystack = normalise(document_text)
    accepted, rejected = [], []
    for i, f in enumerate(findings):
        where = f"findings[{i}]"
        if not isinstance(f, dict):
            rejected.append((where, "not an object"))
            continue
        extra = sorted(set(f) - FIELDS)
        if extra:
            rejected.append((where, f"carries {extra}; the contract is "
                                    f"where/claim/quote and there is no field "
                                    f"for a score on purpose"))
            continue
        missing = sorted(FIELDS - set(f))
        if missing:
            rejected.append((where, f"missing {missing}"))
            continue
        quote = str(f["quote"]).strip()
        if len(quote.split()) < MIN_QUOTE_WORDS:
            rejected.append((where, f"quote is {len(quote.split())} word(s); "
                                    f"fewer than {MIN_QUOTE_WORDS} is a "
                                    f"fragment that would match anything"))
            continue
        if normalise(quote) not in haystack:
            rejected.append((where, "the quoted words do not appear in the "
                                    "document — a model that cannot produce "
                                    "the sentence it objects to has not found "
                                    "anything"))
            continue
        accepted.append(f)
    return accepted, rejected


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("findings", type=pathlib.Path)
    ap.add_argument("--document", type=pathlib.Path, required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    for p in (a.findings, a.document):
        if not p.is_file():
            sys.exit(f"no such file: {p}")

    try:
        findings = json.loads(a.findings.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"{a.findings}: not valid JSON ({exc})")
    if not isinstance(findings, list):
        sys.exit(f"{a.findings}: expected a list of findings")

    accepted, rejected = review(
        findings, a.document.read_text(encoding="utf-8", errors="replace"))

    if a.json:
        print(json.dumps({"accepted": accepted,
                          "rejected": [{"at": w, "why": r} for w, r in rejected]},
                         indent=1, ensure_ascii=False))
        return

    print(f"{a.findings} against {a.document}\n")
    print(f"  {len(accepted)} accepted, {len(rejected)} rejected\n")
    for f in accepted:
        print(f"  note  {f['where']}: {f['claim']}")
        print(f"        \"{f['quote']}\"")
    for where, why in rejected:
        print(f"  drop  {where}: {why}")
    if accepted:
        print("\n  These are opinions with evidence attached. They are reported "
              "and never gate:\n  an author editing a document to satisfy a "
              "model's taste is the register this\n  rule set exists to keep out.")


if __name__ == "__main__":
    main()
