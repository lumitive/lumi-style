#!/usr/bin/env python3
"""Generate references/eval-inventory.md — every quantitative constraint, one page.

The owner asked where all the hidden metric constraints live, and the honest
answer was: everywhere. A sweep found roughly one hundred and eighty numbers
constraining a deliverable, some seventy of them stated nowhere in
`references/`, plus ten contradictions between prose copies — including one
inside a single file. The scattered state was not an accident; it is what
per-defect patching produces over a hundred releases.

The consolidation is GENERATED, not hand-copied, because the alternative was
tried and measured: twenty-six releases of this repository carry a fix for a
prose copy disagreeing with its code. A hand-written inventory would be the
largest such copy ever created. This one is extracted from the code that
enforces each number, so it cannot disagree with it; `--check` in CI refuses a
stale render.

    python3 scripts/build/build_eval_inventory.py            # write
    python3 scripts/build/build_eval_inventory.py --check    # verify current (CI)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
OUT = ROOT / "references" / "eval-inventory.md"
FIXTURE = ROOT / "fixtures" / "deck-pass.en.html"

# The files whose module-level numeric constants are inventoried. Adding a file
# here is adding a source; the constants themselves are discovered, never
# listed, so a new constant appears in the inventory on the next build.
CONSTANT_SOURCES = (
    "scripts/check/check_prose.py",
    "scripts/check/check_design.py",
    "scripts/check/inspect_layout.py",
    "scripts/check/check_globe.py",
    "scripts/ops/eval_corpus.py",
    "scripts/ops/export_pdf.py",
    "scripts/ops/run_conformance.py",
    "scripts/ops/debug_log.py",
    "scripts/build/build_region_palette.py",
)

JS_SOURCES = ("assets/globe/globe.js",)


def tier_of(target: str) -> str:
    if "(gates)" in target:
        return "gate"
    if target.strip() == "reported" or "(reported)" in target:
        return "reported"
    return "graded"


def checker_rows() -> list[tuple[str, str, str, str]]:
    """(checker, metric, target, tier) from the checkers' own row tables,
    obtained by running them on the passing fixture — the same authority the
    exit code reads, so this section cannot disagree with the behaviour."""
    rows = []
    for kind, argv in (
        ("check_prose", [sys.executable, "scripts/check/check_prose.py",
                         str(FIXTURE), "--genre", "training", "--json"]),
        ("check_design", [sys.executable, "scripts/check/check_design.py",
                          str(FIXTURE), "--json"]),
    ):
        out = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
        try:
            report = json.loads(out.stdout)[0]
        except (ValueError, IndexError) as exc:
            raise SystemExit(f"FAIL  {kind} emitted no parseable report against "
                             f"the passing fixture: {exc}") from exc
        for name, target in sorted(report["targets"].items()):
            rows.append((kind, name, target, tier_of(target)))
    return rows


def layout_verdicts() -> list[str]:
    """The names deliverable_verdicts emits, read from its source."""
    text = (ROOT / "scripts/check/inspect_layout.py").read_text(encoding="utf-8")
    start = text.index("def deliverable_verdicts")
    end = text.index("\ndef ", start + 1)
    body = text[start:end]
    names = re.findall(r'add\("(\w+)"', body)
    names += re.findall(r'out\["(\w+)"\] = \(', body)
    return sorted(set(names))


def module_constants(relpath: str) -> list[tuple[str, str, str]]:
    """(name, value, trailing comment) for every module-level ALL_CAPS literal."""
    text = (ROOT / relpath).read_text(encoding="utf-8")
    rows = []
    for m in re.finditer(
            r"^([A-Z][A-Z0-9_]{2,}) = ((?:[^#\n]|\([^)]*\))+?)(?:  # (.*))?$",
            text, re.M):
        name, value, comment = m.group(1), m.group(2).strip(), m.group(3) or ""
        # Only values that carry a number: a regex table or a string vocabulary
        # is a different kind of constant and has its own guards.
        if not re.search(r"\d", value) or value.startswith(("re.", "'", '"')):
            continue
        if len(value) > 60:
            value = value[:57] + "…"
        rows.append((name, value, comment.strip()))
    return rows


def js_constants(relpath: str) -> list[tuple[str, str, str]]:
    text = (ROOT / relpath).read_text(encoding="utf-8")
    return [(m.group(1), m.group(2), "")
            for m in re.finditer(r"^const ([A-Z][A-Z0-9_]+) = ([\d.]+);",
                                 text, re.M)]


def stated_in_references(value: str) -> str:
    """Which reference files state this number — a rough, honest cross-check.

    Values of one or two characters match everywhere and prove nothing, so they
    are not searched; the column says so rather than reporting a false home.
    """
    token = value.rstrip("%").strip()
    token = token[:-2] if token.endswith(".0") else token
    if len(token) < 3 or not re.fullmatch(r"[\d.]+", token):
        return "(not searched: too short)"
    hits = []
    for path in sorted((ROOT / "references").glob("*.md")):
        if path.name == "eval-inventory.md":
            continue
        if re.search(rf"(?<![\d.]){re.escape(token)}(?![\d.])",
                     path.read_text(encoding="utf-8")):
            hits.append(path.name)
    return ", ".join(hits) if hits else "CODE ONLY"


def render() -> str:
    lines = [
        "# Eval inventory — every quantitative constraint, extracted",
        "",
        "**GENERATED by `scripts/build/build_eval_inventory.py` — do not edit.**",
        "This is the one deliberate exception to \"references/ is hand-written\":",
        "an inventory is a table, not prose, and a hand-written copy of some one",
        "hundred and eighty numbers is the drift class this repository has fixed",
        "twenty-six times. Regenerate after any checker change; `--check` in CI",
        "refuses a stale render.",
        "",
        "What each tier means: a **gate** fails the run; **graded** prints FAIL",
        "and does not fail the run; **reported** carries no predicate. The",
        "`stated in references/` column is a rough textual cross-check — CODE",
        "ONLY means the number appears in no reference file, which is exactly",
        "the hidden-constraint condition this inventory exists to surface.",
        "",
        "## Metric rows (from the checkers' own row tables)",
        "",
        "| checker | metric | target | tier |",
        "|---|---|---|---|",
    ]
    for kind, name, target, tier in checker_rows():
        lines.append(f"| {kind} | {name} | `{target}` | {tier} |")

    lines += ["", "## Rendered-layout verdicts (`inspect_layout.py --deliverable`)",
              "",
              "All of these **gate** a pre-delivery run. `deliverable_verdicts`",
              "is the authority; five files once counted this list four",
              "different ways.", ""]
    lines.append("`" + "`, `".join(layout_verdicts()) + "`")

    lines += ["", "## Module constants (discovered, with their own comments)", ""]
    for relpath in CONSTANT_SOURCES:
        rows = module_constants(relpath)
        if not rows:
            continue
        lines += [f"### {relpath}", "",
                  "| constant | value | comment | stated in references/ |",
                  "|---|---|---|---|"]
        for name, value, comment in rows:
            lines.append(f"| {name} | `{value}` | {comment} | "
                         f"{stated_in_references(value)} |")
        lines.append("")
    for relpath in JS_SOURCES:
        rows = js_constants(relpath)
        if rows:
            lines += [f"### {relpath}", "",
                      "| constant | value | comment | stated in references/ |",
                      "|---|---|---|---|"]
            for name, value, _comment in rows:
                lines.append(f"| {name} | `{value}` |  | "
                             f"{stated_in_references(value)} |")
            lines.append("")

    table = json.loads((ROOT / "evals" / "thresholds.json").read_text(
        encoding="utf-8"))
    lines += ["## Evals thresholds (`evals/thresholds.json`)", "",
              f"Status: **{table.get('status', 'unstated')}** — see the file's "
              f"`status_note` for why these report rather than gate.", "",
              "| metric | direction | genre bars | evidence |", "|---|---|---|---|"]
    for name, spec in sorted(table["metrics"].items()):
        bars = "; ".join(
            f"{g} {b['value'] if b.get('value') is not None else '—'}"
            for g, b in sorted(spec["genres"].items()))
        evidence = "/".join(sorted({b["evidence"]
                                    for b in spec["genres"].values()}))
        lines.append(f"| {name} | {spec['direction']} | {bars} | {evidence} |")
    lines += ["",
              f"`min_content_pages` = {table['min_content_pages']} — below it, "
              f"per-page ratios report `too few pages` rather than a verdict.",
              ""]

    tokens = json.loads((ROOT / "tokens" / "design-tokens.json").read_text(
        encoding="utf-8"))
    lines += ["## Declared design values (`tokens/design-tokens.json`)", "",
              "The tokens are the authority over every prose copy (CLAUDE.md).",
              "Palette values are held to the CSS by the `token palette parity`",
              "guard and are not repeated here.", "",
              "| group | key | value |", "|---|---|---|"]
    def walk(group, prefix, d):
        for k, v in sorted(d.items()):
            if isinstance(v, dict):
                walk(group, f"{prefix}{k}.", v)
            elif isinstance(v, (int, float, str)) and re.search(r"\d", str(v)):
                lines.append(f"| {group} | {prefix}{k} | `{v}` |")

    for group in ("contrast", "chart_scale_px", "typography", "layout"):
        node = tokens.get(group)
        if isinstance(node, dict):
            walk(group, "", node)
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="verify the tracked render is current (CI)")
    args = ap.parse_args(argv)
    rendered = render()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            print(f"FAIL  {OUT.relative_to(ROOT)} is stale or missing; "
                  f"re-run without --check")
            return 1
        print(f"ok    {OUT.relative_to(ROOT)} is current")
        return 0
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} "
          f"({len(rendered.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
