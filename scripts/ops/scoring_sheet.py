#!/usr/bin/env python3
"""Emit a blind scoring sheet for C1–C7, built from the rubric's own items.

**Blind means no mechanical number appears on it.** A reader who has seen the
machine's answer is no longer an independent measurement, and the agreement
study — the whole reason a human score is recorded at all — is worth nothing
without that independence.

The items are read out of `references/eval-rubric.md` rather than restated
here, so a sheet cannot describe a rubric that no longer exists. Struck items
are omitted: they name a gate that already holds them, and asking a reviewer to
re-check something a gate holds spends the scarcest resource in this process on
nothing.

Each dimension is scored 1–5, **and the score is arrived at by ticking the
evidence items rather than by forming an impression** — that ordering is the
finding the rubric is built on, not a formatting preference.

Usage
  scoring_sheet.py deck-a.en.html deck-b.en.html > sheet.md
  scoring_sheet.py --corpus-id A1 deck.en.html
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
RUBRIC = ROOT / "references" / "eval-rubric.md"


def dimensions():
    """-> [(id, title, [item, ...])] read out of the rubric, struck items dropped."""
    text = RUBRIC.read_text(encoding="utf-8")
    section = text[text.index("## Human dimensions"):text.index("### 7.3")] \
        if "### 7.3" in text else text[text.index("## Human dimensions"):]
    out = []
    for m in re.finditer(r"^### (C\d) · ([^\n·]+)(?:·[^\n]*)?$(.*?)(?=^### C\d|\Z)",
                         section, re.M | re.S):
        items = []
        for row in re.finditer(r"^\| (①|②|③|④|⑤|⑥|⑦|⑧) (.+?) \|", m.group(3), re.M):
            body = re.sub(r"\*\*|`|\[outline\]|·", "", row.group(2)).strip(" ·")
            items.append(f"{row.group(1)} {body}")
        if items:
            out.append((m.group(1), m.group(2).strip(), items))
    return out


def sheet(files, corpus_ids):
    lines = [
        "# Blind scoring sheet · C1–C7",
        "",
        "Open each document in a browser and score each dimension **1–5**, "
        "arriving at the number by ticking the evidence items rather than by "
        "forming an impression.",
        "",
        "**No mechanical number appears here on purpose.** A reader who has seen "
        "the machine's answer is no longer an independent measurement, and the "
        "agreement study is worth nothing without that independence — so do not "
        "open the checker output before scoring.",
        "",
        "Items a gate already holds are not listed: re-checking those spends your "
        "time on something already decided.",
        "",
        "**A note on the protocol** (`references/eval-rubric.md`): a dimension a "
        "reader marked down cannot be self-scored above 3 in the round that fixes "
        "it, and a divergence of two points between the self-score and yours "
        "forces a retrospective.",
        "",
    ]
    dims = dimensions()
    for path, cid in zip(files, corpus_ids):
        p = pathlib.Path(path)
        lines += [f"## {cid} · {p.stem}", "",
                  f"`file://{p.resolve()}`", ""]
        for did, title, items in dims:
            lines.append(f"### {did} · {title}")
            lines.append("")
            for it in items:
                lines.append(f"- [ ] {it}")
            lines += ["", "**分数 1–5**: ____   **一句理由**: ", ""]
        lines.append("---")
        lines.append("")
    lines += [
        "## When you are done",
        "",
        "Give the scores back in any form — the table, a list, or just "
        "`C1=4 C2=3 …` per document. They are transcribed into "
        "`reviews/scores.json` with the corpus id above, which is the key the "
        "agreement study joins on; **a record without one cannot be compared to "
        "anything**, and the two records that predate that rule are why the study "
        "has never had a joinable row.",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--corpus-id", action="append", dest="corpus_ids",
                    help="one per file, in order; defaults to A1, A2, …")
    a = ap.parse_args()
    ids = a.corpus_ids or [f"A{i}" for i in range(1, len(a.files) + 1)]
    if len(ids) != len(a.files):
        sys.exit("give one --corpus-id per file, in order")
    print(sheet(a.files, ids))


if __name__ == "__main__":
    main()
