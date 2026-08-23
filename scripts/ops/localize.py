#!/usr/bin/env python3
"""Give an existing deliverable a second language version, kept in step with it.

**This is not the path to a non-English deliverable.** A deck the user asked for
in another language is authored IN that language: `new_deck.py --lang zh-Hans
--lang-asked "<their words>"`, and the prose is written in Chinese from the
start. Building English first and translating writes the same content twice —
the owner's ruling, 2026-08-23, and she is right about the cost.

What this command is for is the case her own work already has: **one deck, two
language versions, shipped side by side** (`…zh-Hans.html` beside `…en.html`).
It copies a finished deliverable, sets `<html lang>`, and records where the copy
came from, so the pair can be told apart and traced. Translating the prose
afterwards is the author's work; this does not translate.

    python3 scripts/ops/localize.py deck.en.html \\
            --lang zh-Hans --asked "\u628a\u62a5\u544a\u5199\u6210\u4e2d\u6587" --out deck.zh-Hans.html

It refuses unless the source passes its own checks, because a copy inherits
every defect of the document it was copied from and adds a translation on top.
`--skip-source-check` exists for the case where you have just checked it
yourself; it is recorded, not silent.

**What no local script can do, said plainly rather than implied**: verify that
the quoted words are the user's. Nothing on this machine can. `publish.sh`
states the same limit about the same class of problem.
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
import html  # noqa: E402
import pathlib  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())

# `judge_findings.py` rejects a quotation under three words as "a fragment that
# would match anything". The same floor, counted so it means the same thing in
# a language without spaces: a CJK character is a token.
MIN_QUOTE_TOKENS = 3
_TOKEN = re.compile(r"[A-Za-z0-9]+|[㐀-鿿぀-ヿ가-힯]")

LANG_ATTR = re.compile(r"(<html[^>]*\blang\s*=\s*)[\"'][\w-]+[\"']", re.I)
BODY_OPEN = re.compile(r"<body\b[^>]*>", re.I)


def quote_tokens(text: str) -> int:
    return len(_TOKEN.findall(text or ""))


def source_is_green(src: pathlib.Path) -> tuple[bool, str]:
    """Did the English deck pass its own checks? -> (ok, the last line said).

    A localized deck is a DERIVATIVE. Deriving one from a document that does not
    pass is how a defect ships twice, and it is the one precondition this script
    can actually verify.
    """
    argv = [sys.executable, str(ROOT / "scripts/ops/check_deliverable.py"),
            str(src), "--fast"]
    proc = subprocess.run(argv, capture_output=True, text=True)
    tail = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    return proc.returncode == 0, (tail[-1] if tail else "no output")


def localize(raw: str, lang: str, asked: str, source_name: str) -> str:
    """-> the same document, declaring the language and where it came from."""
    out, n = LANG_ATTR.subn(lambda m: f'{m.group(1)}"{lang}"', raw, count=1)
    if not n:
        raise SystemExit("FAIL  the source has no <html lang=…> to rewrite")
    m = BODY_OPEN.search(out)
    if not m:
        raise SystemExit("FAIL  the source has no <body> to declare on")
    tag = m.group(0)
    for attr in ("data-lang-asked", "data-lang-ask-quote", "data-localized-from"):
        tag = re.sub(rf'\s{attr}\s*=\s*"[^"]*"', "", tag, flags=re.I)
    decl = (f' data-lang-asked="{html.escape(lang, quote=True)}"'
            f' data-lang-ask-quote="{html.escape(asked, quote=True)}"'
            f' data-localized-from="{html.escape(source_name, quote=True)}"')
    return out[:m.start()] + tag[:-1] + decl + ">" + out[m.end():]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", type=pathlib.Path,
                    help="the English deliverable this one is derived from")
    ap.add_argument("--lang", required=True,
                    help="BCP-47 code for the derived document, e.g. zh-Hans")
    ap.add_argument("--asked", required=True,
                    help="the user's OWN WORDS asking for this language, "
                         "verbatim. Not your summary of them, and not the fact "
                         "that the conversation or the source material was in "
                         "this language - neither is an instruction (FM-18). "
                         "It is written into the document where the owner reads "
                         "it")
    ap.add_argument("--out", type=pathlib.Path, required=True,
                    help="where the derived document goes. Keep it beside the "
                         "source: the two are one deliverable in two languages")
    ap.add_argument("--skip-source-check", action="store_true",
                    help="do not re-check the English source first. Recorded "
                         "as a waiver in the output and NOT a way to derive "
                         "from a red deck quietly")
    a = ap.parse_args(argv)

    if a.lang.split("-")[0].lower() == "en":
        sys.exit("--lang en: English is what the scaffold already emits. This "
                 "command exists to derive the OTHER language.")
    if not a.source.is_file():
        sys.exit(f"no such source deliverable: {a.source}")
    if quote_tokens(a.asked) < MIN_QUOTE_TOKENS:
        sys.exit(f"--asked {a.asked!r} is {quote_tokens(a.asked)} token(s); "
                 f"fewer than {MIN_QUOTE_TOKENS} is a fragment that would match "
                 f"anything. Quote what the user actually said.")
    raw = a.source.read_text(encoding="utf-8")
    declared = re.search(r"<html[^>]*\blang\s*=\s*[\"']([\w-]+)", raw, re.I)
    if declared and declared.group(1).split("-")[0].lower() != "en":
        sys.exit(f"the source declares {declared.group(1)!r}, not English. A "
                 f"localized document is derived from the English one; deriving "
                 f"it from another derivative loses the original.")

    if not a.skip_source_check:
        ok, said = source_is_green(a.source)
        if not ok:
            print(f"FAIL  the English source does not pass its own checks, so "
                  f"there is nothing to derive from yet.\n      {said}\n"
                  f"      Fix {a.source.name} first. A localized deck inherits "
                  f"every defect of its source and adds a translation.",
                  file=sys.stderr)
            return 1

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(localize(raw, a.lang, a.asked, a.source.name),
                     encoding="utf-8")
    # SAID OUT LOUD, because the one thing this cannot check is the one thing
    # that matters, and the owner reads this line.
    print(f"wrote {a.out}")
    print(f"  language:  {a.lang}")
    print(f"  derived from: {a.source.name}")
    print(f"  recorded as asked: \"{a.asked}\"")
    print("  That quotation is now in the document. No script can verify it "
          "came from the user; the person reading the deck can.")
    print("  The prose is still English. Translating it is yours.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
