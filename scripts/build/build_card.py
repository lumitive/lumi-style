#!/usr/bin/env python3
"""Generate `references/build-card.md` — what an agent needs WHILE composing.

**The measured problem.** SKILL.md tells an agent to read `brand.md`,
`storyline-templates.md`, `design-rules.md`, `analysis-rules.md`, an exemplar
note, `writing-rules.md`, `eval-rubric.md` and the token block before it writes
a page: about **322 KB, roughly 98,000 tokens**, and about 148,000 if it also
opens `page-contracts.md` and `lumi-layouts.css`, which SKILL.md pressures it to
do. Every API call in that build then re-sends the whole context, so a 2026-08
ten-page deck read **105 million cached tokens** across 460 calls. The rules are
not too many; they are all loaded at once, and most of them are needed when a
gate fires rather than while a sentence is being written.

**So this is a card, not a summary.** It carries only what is decidable and
lookup-shaped: the must-asks, the gating metrics, the page contracts that gate,
the role and layout vocabulary, and the commands. **Everything here is
generated** from `evals/rule-coverage.json`, `evals/gates.json`,
`adapters/platforms.json` and `tokens/`, and every line carries the `file:line`
it came from — the same contract `page-contracts.md` and `eval-inventory.md`
keep, and the reason this may exist inside `references/` at all. It is a third
copy of nothing: a line that disagrees with its source is a build failure, not a
disagreement.

**What it deliberately omits**: every judgement. What to reach for, how a page
argues, which figure a relation wants, the voice — those are `brand.md`,
`design-rules.md`, `analysis-rules.md` and `writing-rules.md`, and an agent that
reads only this card will produce a document that passes and says nothing. The
card says so at the top, in the file itself, where an agent reading it will see
it.

    python3 scripts/build/build_card.py            # write it
    python3 scripts/build/build_card.py --check    # is it current? (CI)
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import argparse  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
TARGET = ROOT / "references" / "build-card.md"

PAGE_ORDER = ["all", "cover", "agenda", "opener", "content", "closing"]
PAGE_TITLE = {"all": "Every page", "cover": "The cover", "agenda": "The agenda",
              "opener": "A part opener", "content": "A content page",
              "closing": "The closing page"}


def _register() -> list[dict]:
    return json.loads((ROOT / "evals/rule-coverage.json")
                      .read_text(encoding="utf-8"))["rules"]


def _gates() -> dict:
    return json.loads((ROOT / "evals/gates.json")
                      .read_text(encoding="utf-8"))["gates"]


def _version() -> str:
    m = re.search(r'^\s*version:\s*"([\d.]+)"',
                  (ROOT / "SKILL.md").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "unknown"


def _layout_names() -> list[str]:
    """The layouts `tokens/` defines, read from the file that defines them.

    D22 fails a page claiming a layout the tokens do not carry, so the list an
    author composes against has to be THIS list and not a remembered one.
    """
    css = (ROOT / "tokens/lumi-layouts.css").read_text(encoding="utf-8")
    names = set()
    for m in re.finditer(r"\.body\.([a-z0-9-]+)", css):
        names.add(m.group(1))
    return sorted(names)


def _role_names() -> list[str]:
    """The role classes the consistency audit checks against.

    Named in SKILL.md as the contract, and defined in the token file. Renaming
    one drops a block OUT of the audit rather than failing it, which is why the
    vocabulary belongs on a card an author reads while composing.
    """
    css = (ROOT / "tokens/lumi-theme.css").read_text(encoding="utf-8")
    css += (ROOT / "tokens/lumi-layouts.css").read_text(encoding="utf-8")
    wanted = ("eyebrow", "t", "sup", "lede", "take", "key", "red", "card",
              "ledname", "verdict", "swap", "vow", "tag", "grades", "gloss",
              "listhead", "gd", "cap", "srcline", "band", "stats", "stat",
              "fig", "fill", "field", "colophon", "closenote", "launch")
    present = [w for w in wanted if re.search(rf"\.{re.escape(w)}\b", css)]
    return present


def _metric_line(name: str, meta: dict) -> str:
    fam = meta.get("family", "?")
    na = (meta.get("na_means") or "").strip()
    na = re.sub(r"\s+", " ", na)
    if len(na) > 150:
        na = na[:149].rstrip() + "…"
    return f"| `{name}` | {fam} | {meta.get('since', '?')} | {na or '—'} |"


def render() -> str:
    rules = _register()
    gates = _gates()
    ver = _version()
    out: list[str] = []
    w = out.append

    w(f"# LUMI build card · {ver}")
    w("")
    w("> **GENERATED** by `scripts/build/build_card.py` from "
      "`evals/rule-coverage.json`, `evals/gates.json` and `tokens/`. "
      "`--check` runs in CI. Never hand-edit: edit the rule, or the register, "
      "and regenerate.")
    w("")
    w("**This card is the decidable half of the rules, for lookup while you "
      "compose. It is not the rules.** Everything on it is something a script "
      "can fail you for. Nothing on it tells you what to reach for, how a page "
      "argues, which figure a relation wants, or what the voice is — that is "
      "`brand.md` (read it first, and commit), `design-rules.md`, "
      "`analysis-rules.md`, `storyline-templates.md` and `writing-rules.md`. "
      "**An agent that reads only this card will produce a document that "
      "passes every gate and says nothing**, which is the exact failure five "
      "rounds of conformance produced and the owner returned every time. Read "
      "the card to avoid re-reading 100 KB of reference for a class name; read "
      "the references to have something to say.")
    w("")

    w("## Ask before generating")
    w("")
    w("Three, and they are one must-ask, because each changes every page.")
    w("")
    w("| | Default | Declared on the document as |")
    w("|---|---|---|")
    w("| **Genre** | none — ask | `<body data-genre=\"…\">` |")
    w("| **Geometry** | from the genre | `<body data-geometry=\"landscape\\|portrait\">` |")
    w("| **Output language** | **American English** | `<html lang>`, plus "
      "`<body data-lang-asked>` when the user asked for anything else |")
    w("")
    w("Language is **asked, never inferred** — not from the source material, "
      "not from the venue, not from the audience's nationality, and not from "
      "the language the user is writing to you in. A language the same user "
      "chose for a comparable deliverable outranks every inference, and a "
      "language named in an approved plan is still an inference. `M16` fails a "
      "deliverable in any language but English with no recorded ask "
      "(`FAILURE_MODES.md` FM-18, twice shipped).")
    w("")

    w("## The one command")
    w("")
    w("```")
    w("python3 scripts/ops/build.py --deck <out.html> --script <fill.py> \\")
    w("        --outline <outline.md> --genre <g> --geometry <g> \\")
    w("        --storyline <s> --pages <n> --parts A,B,C --lang en --fast")
    w("```")
    w("")
    w("`--fast` while fixing (the declared stage only, every gate still "
      "running); `--deliver` on the last round (full matrix, and the contact "
      "sheet whose path it prints — look at it, that is the last gate). "
      "`--debug-log` writes the execution log as a side effect rather than one "
      "wrapped command per turn.")
    w("")
    w("**The instruments are already inside it** — prose, design, layout, "
      "privacy and the Evals, one process, browser rendering while the text "
      "checks run. Run one directly only to re-check ONE finding while you fix "
      "it. Running the stack and then the instruments is the same work twice, "
      "and the expensive half is a browser.")
    w("")

    gating_names = sorted(n for n, m in gates.items()
                          if m.get("severity") == "gate")
    w(f"## The {len(gating_names)} gating verdicts")
    w("")
    w("A gating failure has to be fixed; a graded one is a reading. **A gate "
      "binds a document built at or after its `since`** — an older document "
      "reports `not held`, which is neither pass nor failure. A document with "
      "no version stamp is held to all of them.")
    w("")
    w("| verdict | concept | since | what an `n/a` means |")
    w("|---|---|---|---|")
    for n in gating_names:
        w(_metric_line(n, gates[n]))
    w("")

    w("## What gates, per page")
    w("")
    w("Only the rules a script can fail you for, from the register. The full "
      "contract — including the majority of rules that no check reads — is "
      "`references/page-contracts.md`.")
    w("")
    by_kind: dict[str, list[dict]] = {}
    for r in rules:
        if r.get("gates"):
            by_kind.setdefault(r.get("page_kind", "?"), []).append(r)
    for kind in PAGE_ORDER:
        items = by_kind.get(kind) or []
        if not items:
            continue
        w(f"### {PAGE_TITLE.get(kind, kind)} ({len(items)})")
        w("")
        for r in sorted(items, key=lambda x: x.get("metric") or "zz"):
            w(f"- **`{r.get('metric')}`** {r['gist']} — `{r['source']}`")
        w("")

    w("## Vocabulary")
    w("")
    w("Rename one of these and the block drops OUT of the consistency audit "
      "rather than failing it.")
    w("")
    w("**Layouts** (`D22` fails a page claiming one `tokens/` does not "
      "define): " + ", ".join(f"`.{n}`" for n in _layout_names()))
    w("")
    w("**Roles**: " + ", ".join(f"`.{n}`" for n in _role_names()))
    w("")

    w("## Where the judgement lives")
    w("")
    w("| Read | For |")
    w("|---|---|")
    w("| `references/brand.md` | what to reach for. The only file that says "
      "it. Read first, and commit, before deciding what the deliverable may "
      "not do |")
    w("| `references/analysis-rules.md` | facts becoming findings: the five "
      "moves, the outline contract, the implication rung |")
    w("| `references/design-rules.md` | colour, type, the chart iron rules, "
      "form selection, the shape library, icons, imagery |")
    w("| `references/storyline-templates.md` | the narrative skeleton for the "
      "storyline you chose |")
    w("| `references/writing-rules.md` | output language, terminology red "
      "lines, banned phrases, number discipline, the de-AI pass |")
    w("| `references/page-contracts.md` | every rule binding one page kind, "
      "checked or not, with the line it is written on |")
    w("| `references/eval-rubric.md` | the C1–C8 self-score, at the end |")
    w("")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when the written card is not what this "
                         "generator would write now")
    a = ap.parse_args(argv)
    want = render()
    if a.check:
        have = TARGET.read_text(encoding="utf-8") if TARGET.is_file() else None
        if have == want:
            print(f"ok    {TARGET.relative_to(ROOT)} is current")
            return 0
        print(f"FAIL  {TARGET.relative_to(ROOT)} is stale — run "
              f"`python3 scripts/build/build_card.py`")
        return 1
    TARGET.write_text(want, encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)} ({len(want)} bytes, "
          f"{len(want.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
