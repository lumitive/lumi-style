#!/usr/bin/env python3
"""What a recorded result is a result *of*, and what version produced it.

Two questions, one implementation, because they are the same question asked of
two subjects. `run_conformance.py` already asks them of a conformance task:
hash the fields that can change a verdict, and read the deliverable's own
colophon for the version that built it — so a cell whose hash no longer matches
reads `stale: task changed` instead of reporting an answer to a question nobody
is asking. `trace.py` needs exactly that about a build's RECIPE.

The alternative was a second sha256-of-sorted-json in a second file, which is
the `no shadow math` guard's territory: a second copy of an implementation is
this repository's most-fixed defect class, and a fingerprint that differs
between two callers is worse than no fingerprint, because both sides report
matches.

**Why a recipe needs a vintage at all.** A trace's `skill_version` is read from
SKILL.md when the trace opens, so it always equals HEAD and can never be stale.
A build that replays a recipe frozen at 0.1.457 therefore produces a record
indistinguishable from one built to the current constitution — measured, not
supposed: a rebuild's argument sat two research rounds behind its own evidence
base while every gate reported green.
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

import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import re  # noqa: E402

# The stamp every deliverable carries in its closing colophon.
VERSION_STAMP = re.compile(r"lumi-style\s+(\d+\.\d+\.\d+)")

# The stamp a RECIPE carries, which is a different shape and needed its own
# pattern. One comment here used to claim the colophon pattern covered both;
# it does not, and the cost was measured. A build script writes its colophon as
# `f"Built with lumi-style {VERSION}"` — an interpolation, not a literal — so
# the colophon pattern finds nothing in the source and the recipe reads as
# UNSTAMPED even when the script's own `VERSION = "0.1.591"` line says
# otherwise. Convention 15 in one line: the pattern was written against the
# rendered artifact and then applied to the source that renders it.
#
# Eleven of the eighty stored traces carry a recipe hash and no version, and
# `unknown` is not `current`. This pattern is ONE cause of that; fingerprinting
# an outline (which carries no stamp at all, and which `new_deck.py` did until
# 0.1.592 — see `trace.py cmd_annotate`) is another, and the trace does not
# record which file was hashed, so no cause can be attributed to all eleven.
RECIPE_STAMP = re.compile(r"""^VERSION\s*=\s*["'](\d+\.\d+\.\d+)["']""",
                          re.MULTILINE)


def material_hash(material: dict, length: int = 12) -> str:
    """A stable digest of the fields that can change a result.

    Sorted keys and `ensure_ascii=False` so the digest does not depend on dict
    order or on how a non-ASCII string happens to be escaped.
    """
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:length]


def skill_version() -> str:
    """-> the version SKILL.md declares.

    `debug_log` had the only reader and the scaffold could not reach it, so
    `new_deck.py` shipped the literal `VERSION` in its colophon — a slot D14
    GATES on. Every build by every user was therefore one red round and one
    hand edit, to write a number the package already knows.

    Here rather than in `stamps.py` because that module names paths the
    consumer projection does not carry, and importing it from the scaffold
    would drag them across the boundary.
    """
    root = next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / "SKILL.md").exists())
    m = re.search(r'^\s*version:\s*"(\d+\.\d+\.\d+)"',
                  (root / "SKILL.md").read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit("FAIL  SKILL.md carries no metadata.version")
    return m.group(1)


def version_in(text: str) -> str | None:
    """-> the lumi-style version this text stamps, or None.

    THE COLOPHON ONLY. A recipe's own `VERSION = "..."` line is read by
    `recipe_version_in`, deliberately not by this — see that function for why
    widening this one silently handed documents an exemption from newer gates.

    None is honest and load-bearing: a recipe that names no version has not
    told us it is current, and the caller must not read that as agreement with
    HEAD. It is the difference between "built at 0.1.457" and "we do not know",
    and both are different from "built now".
    """
    m = VERSION_STAMP.search(text)
    return m.group(1) if m else None


def recipe_version_in(text: str) -> str | None:
    """-> the version a RECIPE's source stamps, or None. Not for deliverables.

    Two shapes, in order: the colophon a recipe writes as a literal, then its
    own `VERSION = "0.1.591"` at line start.

    **Deliberately a separate function from `version_in`, and it was one shared
    function for part of 0.1.592's development.** Sharing it widened the reader
    that `check_deliverable.py` uses to decide WHICH GATES BIND: a document with
    no colophon but a line-initial `VERSION = "9.9.9"` inside an inline script
    would manufacture a stamp, and gates newer than it would report `not held`
    instead of binding. CLAUDE.md is explicit that this must not happen — "a
    document with no version stamp is held to everything, because an absent
    stamp must not become an exemption" — so the widening belongs only on the
    recipe path, where an absent stamp means `unknown` rather than an exemption.

    It stays loose in one respect, and the looseness is real: a build script is
    operator code outside this repository, and nothing constrains its `VERSION`
    to mean lumi-style's version rather than the document's own revision. A
    recipe stamped `2.4.0` will be reported `stale` against `0.1.592`. That is a
    wrong reading, but it is a LOUD one — the ledger prints the pair — whereas
    the alternative (reading nothing) is the silent `unknown` this release set
    out to reduce. Recorded rather than hidden.
    """
    m = VERSION_STAMP.search(text)
    if m:
        return m.group(1)
    m = RECIPE_STAMP.search(text)
    return m.group(1) if m else None


def recipe_fingerprint(path: pathlib.Path, **context) -> tuple[str, str | None]:
    """-> (hash, version) for the recipe a build was actually driven by.

    `context` is whatever else changes what the recipe produces — the genre and
    storyline it was pointed at. Hashing the bytes alone would call two builds
    identical when they were told to make different documents.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    return material_hash({"recipe": text, **context}), recipe_version_in(text)
