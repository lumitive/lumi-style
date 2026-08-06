#!/usr/bin/env python3
"""Measure the AI-flavor metrics from references/eval-rubric.md on a deliverable.

M1-M11 were described as "scriptable" for six versions while no script existed,
so every AI-flavor rule was enforced by good intentions alone. This runs the
machine-checkable half against a real file.

    python3 scripts/check_prose.py deck.en.html [more files ...]
    python3 scripts/check_prose.py --json report.html

Reports M4 (banned phrases), M8 (sentence rhythm, two-tailed), M9 (em dashes),
M10 (triad rate) and M11 (title-shape uniformity). English deliverables only —
sentence and word segmentation here does not apply to Chinese, and the zh side is
governed by the de-translationese pass in writing-rules.md section 6b.
"""

import html
import json
import pathlib
import re
import statistics
import sys

# references/writing-rules.md section 2, [en-output]. Substrings, matched
# case-insensitively on word boundaries where the entry is a single word.
BANNED = [
    # 1 significance inflation
    "serves as", "stands as", "is a testament", "a testament to", "vital role",
    "crucial role", "pivotal role", "key role", "underscores its importance",
    "reflects broader", "evolving landscape", "indelible mark", "deeply rooted",
    "turning point",
    # 2 promotional register
    "boasts", "vibrant", "profound", "showcasing", "exemplifies",
    "commitment to", "groundbreaking", "renowned", "breathtaking", "stunning",
    "seamless", "robust", "comprehensive", "best-in-class", "world-class",
    # 3 AI high-frequency vocabulary
    "delve", "garner", "interplay", "intricate", "pivotal", "showcase",
    "tapestry", "testament", "underscore", "leverage", "utilize", "foster",
    # 4 filler
    "in order to", "due to the fact that", "at this point in time",
    "in the event that", "has the ability to", "it is important to note",
    # 5 authority tropes
    "the real question is", "at its core", "in reality", "what really matters",
    "fundamentally",
    # 6 signposting
    "let's dive in", "let's explore", "let's break this down",
    "here's what you need to know", "without further ado",
    # 7 fake-candid openers
    "honestly,", "the thing is,", "here's the thing",
    # 8 closing filler
    "it's worth noting", "undeniably", "in conclusion", "let's embark",
]

OVERLONG_WORDS = 32
THRESHOLDS = {
    "M4_banned_hits": ("=0", lambda v: v == 0),
    "M8_overlong_share": ("<=8%", lambda v: v <= 8.0),
    "M8_length_cv": (">=0.35", lambda v: v >= 0.35),
    "M9_dashes": ("=0", lambda v: v == 0),
    "M10_triad_rate": ("<=50%", lambda v: v <= 50.0),
    "M11_title_uniformity": ("<=60%", lambda v: v <= 60.0),
}


def extract(path):
    """Return (body_text, [titles]) for an HTML or Markdown file."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        raw = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", raw, flags=re.S | re.I)
        titles = [
            re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()
            for m in re.finditer(r"<h[12][^>]*>(.*?)</h[12]>", raw, re.S | re.I)
        ]
        body = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    else:
        titles = [m.group(2).strip() for m in re.finditer(r"^(#{1,2})\s+(.*)$", raw, re.M)]
        body = re.sub(r"^#{1,6}\s+", "", raw, flags=re.M)
    return re.sub(r"[ \t]+", " ", body), [t for t in titles if t]


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", p)
        if len(words) >= 3:          # ignore labels, nav fragments, stray numbers
            out.append(len(words))
    return out


def measure(path):
    body, titles = extract(path)
    low = body.lower()

    hits = []
    for phrase in BANNED:
        pattern = (r"\b%s\b" % re.escape(phrase) if phrase.isalpha()
                   else re.escape(phrase))
        n = len(re.findall(pattern, low))
        if n:
            hits.append((phrase, n))

    lengths = sentences(body)
    mean = statistics.fmean(lengths) if lengths else 0.0
    cv = (statistics.pstdev(lengths) / mean) if len(lengths) > 1 and mean else 0.0
    overlong = 100.0 * sum(1 for n in lengths if n > OVERLONG_WORDS) / len(lengths) if lengths else 0.0

    dashes = body.count("—") + body.count("–")

    # Enumerations: HTML/markdown lists are counted by the caller's structure, so
    # approximate with comma series -- "A, B, and C" and "A, B, C" -- which is the
    # form the rule-of-three tell actually takes in prose.
    series = re.findall(r"\b\w[\w'-]*(?:,\s+\w[\w'-]*){1,5}(?:,?\s+and\s+\w[\w'-]*)?", body)
    triples = [s for s in series if s.count(",") == 2]
    triad_rate = 100.0 * len(triples) / len(series) if series else 0.0

    def frame(t):
        head = t[: max(1, len(t) // 2)]
        if ":" in head:
            return "colon"
        if t.rstrip().endswith("?"):
            return "question"
        return "plain"

    frames = [frame(t) for t in titles]
    uniformity = (100.0 * max((frames.count(f) for f in set(frames)), default=0)
                  / len(frames)) if frames else 0.0

    return {
        "file": str(path),
        "sentences": len(lengths),
        "titles": len(titles),
        "M4_banned_hits": sum(n for _, n in hits),
        "M4_detail": hits,
        "M8_overlong_share": round(overlong, 1),
        "M8_length_cv": round(cv, 3),
        "M9_dashes": dashes,
        "M10_triad_rate": round(triad_rate, 1),
        "M11_title_uniformity": round(uniformity, 1),
    }


def main(argv):
    as_json = "--json" in argv
    paths = [pathlib.Path(a) for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__.strip())
        return 1

    reports, failed = [], 0
    for path in paths:
        if not path.exists():
            print(f"missing: {path}")
            failed += 1
            continue
        r = measure(path)
        reports.append(r)
        if as_json:
            continue
        print(f"\n{r['file']}  ({r['sentences']} sentences, {r['titles']} titles)")
        for key, (label, ok) in THRESHOLDS.items():
            value = r[key]
            # A rhythm share computed over a handful of sentences swings wildly on
            # one long sentence, so report it without failing the run.
            thin = key.startswith("M8") and r["sentences"] < 30
            good = ok(value)
            if thin:
                print(f"  n/a   {key:<22} {value:<8} target {label}  (only "
                      f"{r['sentences']} sentences — too few to judge)")
                continue
            failed += 0 if good else 1
            print(f"  {'ok  ' if good else 'FAIL'}  {key:<22} {value:<8} target {label}")
        if r["M4_detail"]:
            worst = sorted(r["M4_detail"], key=lambda kv: -kv[1])[:8]
            print("        banned: " + ", ".join(f"{p}×{n}" for p, n in worst))

    if as_json:
        print(json.dumps(reports, indent=2))
        return 0
    print(f"\n{failed} metric failure(s)" if failed else "\nall metrics pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
