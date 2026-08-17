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

# The stamp every deliverable carries in its closing colophon, and the stamp a
# recipe carries in its own source. One pattern: they are the same claim about
# the same thing — which version of these rules produced this.
VERSION_STAMP = re.compile(r"lumi-style\s+(\d+\.\d+\.\d+)")


def material_hash(material: dict, length: int = 12) -> str:
    """A stable digest of the fields that can change a result.

    Sorted keys and `ensure_ascii=False` so the digest does not depend on dict
    order or on how a non-ASCII string happens to be escaped.
    """
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:length]


def version_in(text: str) -> str | None:
    """-> the lumi-style version this text stamps, or None.

    None is honest and load-bearing: a recipe that names no version has not
    told us it is current, and the caller must not read that as agreement with
    HEAD. It is the difference between "built at 0.1.457" and "we do not know",
    and both are different from "built now".
    """
    m = VERSION_STAMP.search(text)
    return m.group(1) if m else None


def recipe_fingerprint(path: pathlib.Path, **context) -> tuple[str, str | None]:
    """-> (hash, version) for the recipe a build was actually driven by.

    `context` is whatever else changes what the recipe produces — the genre and
    storyline it was pointed at. Hashing the bytes alone would call two builds
    identical when they were told to make different documents.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    return material_hash({"recipe": text, **context}), version_in(text)
