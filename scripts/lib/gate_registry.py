#!/usr/bin/env python3
"""What this package knows about a verdict, in one place.

**Why this exists, and what it replaces.** A gate used to be a tuple in a
function body, classified by whether its *display string* contained the
substring `(gates)`. Four readers parsed that string with three different
rules — `gating.py` by AST on the source, `check_design`/`check_prose` at
runtime for their exit codes, `check_deliverable` on the emitted JSON, and
`check_fixtures` inverted (`"reported" in target`). Three rows were
misclassified in production because of it:

* `M4zh_banned_hits` gates in `check_prose`'s own exit and was **invisible** to
  `gating.py`, whose `(M\\d+)_` cannot match `M4zh_`. The Chinese banned-phrase
  gate was therefore absent from `run_conformance`'s `all-gating` require set.
* `D37_caption_name_len` and `D38_agenda_run_echo` say `reported` in their own
  targets and were counted as **gates** by every consumer, because `gating.py`
  keyed on the `D\\d+` PREFIX rather than the row name.

A substring in a string meant for a human was carrying a contract. This module
makes the contract a declaration, and holds the declaration to the checkers.

**The register cannot lie.** `checker` and `severity` are compared against what
the checkers themselves say, by `check_repo`'s `gate declarations` guard, on the
same reasoning that makes `check_rule_coverage` compare the rule register
against `gating`'s AST reader rather than trusting it. What the register adds is
what no checker knows: **`family`** — the concept a verdict belongs to, the
classification that was missing while the set grew one verdict at a time —
**`since`**, the release that introduced it, and **`na_means`**, present on a
gate whose `n/a` is an honest silence and absent on one whose `n/a` is a
measurement that did not happen.

**`since` and what it is for.** A document carries `built with lumi-style
X.Y.Z`. A gate introduced after that version has nothing to say about the
document: it is reported `not held`, which is neither a pass nor a failure. The
owner's rule, 2026-08-22: historical deliverables were never meant to be
upgraded to satisfy rules written after them; a NEW deliverable is held to
everything.

`always` is a real value, not a default. Six gates predate the version history
this CHANGELOG keeps, and the scheme they were numbered under (1.6.0–3.3.0)
sorts ABOVE 0.1.560 — written as numbers they would have silenced themselves.
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

import json  # noqa: E402
import pathlib  # noqa: E402

import versioning  # noqa: E402 — the one version comparator

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
REGISTER = "evals/gates.json"

SEVERITIES = ("gate", "graded", "reported")
# `privacy` is the fiftieth gate: check_privacy reports one verdict per FILE
# rather than a verdicts map, so it fits no row table and check_deliverable
# promotes it in code. Omitting it here made this tuple disagree with the
# register it describes.
CHECKERS = ("design", "prose", "layout", "privacy")
ALWAYS = "always"


def load(root: pathlib.Path | None = None) -> dict:
    """-> {name: {checker, family, severity, since, na_means?}}.

    `root` is the caller's, not this module's: `check_repo`'s guard tests build
    a synthetic tree and point the guard at it. A module that resolved the path
    from its own location would read the REAL register and the tests would pass
    against the wrong file — a guard test that cannot control its input is
    testing the repository rather than the guard.
    """
    path = (root or ROOT) / REGISTER
    return json.loads(path.read_text(encoding="utf-8"))["gates"]


def gates(root: pathlib.Path | None = None) -> set[str]:
    """-> every verdict name that can fail a deliverable."""
    return {n for n, g in load(root).items() if g["severity"] == "gate"}


def families(root: pathlib.Path | None = None) -> dict[str, list[str]]:
    """-> {family: [verdict names]}, sorted. The classification itself."""
    out: dict[str, list[str]] = {}
    for name, g in sorted(load(root).items()):
        out.setdefault(g["family"], []).append(name)
    return out


def held(name: str, built: str | None, root: pathlib.Path | None = None) -> bool:
    """Does this gate bind a document built at version `built`?

    `built is None` — a document with no colophon, such as a markdown answer —
    is held to EVERYTHING. An absent stamp must not become an exemption: the
    cheapest way to escape every gate would otherwise be to omit the one line
    that says which rules you were written against.
    """
    reg = load(root)
    if name not in reg:
        return True                       # unknown name: never silently exempt
    since = reg[name]["since"]
    if since == ALWAYS or built is None:
        return True
    try:
        return versioning.ver_key(built) >= versioning.ver_key(since)
    except (TypeError, ValueError):
        return True                       # unparseable stamp is not an exemption
