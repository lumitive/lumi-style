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

import markup  # noqa: E402
import rubric_items  # noqa: E402 — after the bootstrap

FIELDS = {"where", "claim", "quote"}
# `fixed` marks a finding the author ACTED ON. It is optional and it is
# not a verdict: it only says which text the quotation is held to.
OPTIONAL_FIELDS = {"fixed", "dimension"}

# The reviewer's own dimensions, imported rather than retyped. A second list of
# C1-C8 in this file would be the drift `rubric_items` was extracted to stop —
# it already outlived one, offering C1-C7 after C8 shipped, and a reader who
# filled that form produced a record `review_scores.py` rejects.
DIMENSIONS = tuple(rubric_items.DIM_TITLE)
MIN_QUOTE_WORDS = 3


def normalise(text: str) -> str:
    """Whitespace-flattened plain text. A real quotation survives this; the
    line breaks and markup a model did not see are what it must not be held to."""
    return markup.visible_text(text).lower()


def review(findings, document_text: str, before_text: str | None = None):
    """-> (accepted, rejected). Rejection is a fact about the finding, not a
    judgement about the document.

    `before_text` is the pre-repair snapshot, and it exists because the tool
    could otherwise only ever validate the advice you did NOT take. The de-AI
    pass exists to change the sentence; once it has, the quotation that caused
    the repair no longer appears in the document, so the finding was refused
    for having worked. A build was left splitting its findings into two files
    for this reason — the ones it adopted, which the script could not read, and
    the ones it declined, which it could.

    **The contract does not move.** A quotation must still appear VERBATIM, and
    a model that cannot produce the sentence it objects to has still found
    nothing. What widens is WHICH text it is held to, and only for a finding
    that declares `fixed` — which in turn requires the snapshot, because
    claiming a repair without producing the text repaired is a claim with no
    evidence.
    """
    haystack = normalise(document_text)
    was = normalise(before_text) if before_text is not None else None
    accepted, rejected = [], []
    for i, f in enumerate(findings):
        where = f"findings[{i}]"
        if not isinstance(f, dict):
            rejected.append((where, "not an object"))
            continue
        extra = sorted(set(f) - FIELDS - OPTIONAL_FIELDS)
        if extra:
            rejected.append((where, f"carries {extra}; the contract is "
                                    f"where/claim/quote and there is no field "
                                    f"for a score on purpose"))
            continue
        missing = sorted(FIELDS - set(f))
        if missing:
            rejected.append((where, f"missing {missing}"))
            continue
        dim = f.get("dimension")
        if dim is not None and dim not in DIMENSIONS:
            rejected.append((where, f"names dimension {dim!r}; the rubric's "
                                    f"are {', '.join(DIMENSIONS)}"))
            continue
        quote = str(f["quote"]).strip()
        # COUNTED AFTER NORMALISING. The floor ran on the raw string and the
        # membership test ran on the normalised one, so `<b> <i> <u>` counted
        # as three words, normalised to the empty string, and `"" in haystack`
        # is True — a finding quoting nothing, printed as evidence attached.
        words = len(normalise(quote).split())
        if words < MIN_QUOTE_WORDS:
            rejected.append((where, f"quote is {words} word(s) once markup is "
                                    f"stripped; fewer than {MIN_QUOTE_WORDS} "
                                    f"is a fragment that would match anything"))
            continue
        # `is True`, not `bool(...)`: the string "no" is truthy, and a finding
        # that says `"fixed": "no"` meant the opposite of what it was read as.
        fixed = f.get("fixed") is True
        if fixed:
            # `fixed` ASSERTS TWO THINGS and both are checkable: the sentence
            # was there, and it is not there now. Accepting on "in either text"
            # let the same file be passed as both --document and --before, so
            # a finding could be declared repaired against an unrepaired
            # document and printed as validated.
            if was is None:
                rejected.append((where, "declares `fixed` and no --before "
                                        "snapshot was given; a repair claimed "
                                        "without the text it repaired is a "
                                        "claim with no evidence"))
                continue
            if normalise(quote) not in was:
                rejected.append((where, "declares `fixed` and the quoted words "
                                        "are not in the --before snapshot "
                                        "either — nothing here was repaired"))
                continue
            if normalise(quote) in haystack:
                rejected.append((where, "declares `fixed` and the quoted words "
                                        "are still in the document; a repair "
                                        "that left the sentence in place is "
                                        "not a repair"))
                continue
            accepted.append(f)
            continue
        found = normalise(quote) in haystack
        if not found:
            rejected.append((where, "the quoted words do not appear in the "
                                    + ("document or the --before snapshot"
                                       if fixed else "document")
                                    + " — a model that cannot produce "
                                      "the sentence it objects to has not found "
                                      "anything"))
            continue
        accepted.append(f)
    return accepted, rejected


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("findings", type=pathlib.Path)
    ap.add_argument("--document", type=pathlib.Path, required=True)
    ap.add_argument("--before", type=pathlib.Path,
                    help="the pre-repair snapshot. A finding marked `fixed` is "
                         "held to THIS text, because the pass that adopted it "
                         "removed the sentence it quoted. Without it a `fixed` "
                         "finding is refused.")
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

    before_text = None
    if a.before is not None:
        if not a.before.is_file():
            sys.exit(f"no such file: {a.before}")
        if a.before.resolve() == a.document.resolve():
            sys.exit("--before and --document are the same file. A repair is a "
                     "difference between two texts; handing over one text twice "
                     "asserts nothing.")
        before_text = a.before.read_text(encoding="utf-8", errors="replace")
    accepted, rejected = review(
        findings, a.document.read_text(encoding="utf-8", errors="replace"),
        before_text=before_text)

    if a.json:
        print(json.dumps({"accepted": accepted,
                          "rejected": [{"at": w, "why": r} for w, r in rejected]},
                         indent=1, ensure_ascii=False))
        return

    print(f"{a.findings} against {a.document}\n")
    print(f"  {len(accepted)} accepted, {len(rejected)} rejected\n")
    # GROUPED BY DIMENSION, because a list of twenty findings in arrival order
    # is a list nobody acts on. The dimension is optional: a finding that names
    # none is still a finding, and lands under `unfiled`.
    by_dim: dict[str, list] = {}
    for f in accepted:
        by_dim.setdefault(f.get("dimension") or "unfiled", []).append(f)
    for dim in [d for d in DIMENSIONS if d in by_dim] + (
            ["unfiled"] if "unfiled" in by_dim else []):
        title = rubric_items.DIM_TITLE.get(dim, "no dimension named")
        print(f"  ── {dim} · {title}")
        for f in by_dim[dim]:
            print(f"     note  {f['where']}: {f['claim']}")
            print(f"           \"{f['quote']}\"")
    for where, why in rejected:
        print(f"  drop  {where}: {why}")
    if accepted:
        print("\n  These are opinions with evidence attached. They are reported "
              "and never gate:\n  an author editing a document to satisfy a "
              "model's taste is the register this\n  rule set exists to keep out.")


if __name__ == "__main__":
    main()
