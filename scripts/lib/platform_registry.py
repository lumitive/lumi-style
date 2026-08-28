#!/usr/bin/env python3
"""The platform registry, read in one place.

`adapters/platforms.json` is the single source of install paths, capability
tiers, entry files and the model-vocabulary probe for every platform this
package claims. It was PARSED in five: the driver, the agent evaluation, two
generators and the debug log, each spelling `json.loads(...)["platforms"]` for
itself, with only one of the five checking that what came back was a non-empty
list. That one lived inside `check_repo`, which is the wrong direction for a
shared discipline to travel: the guard had the careful reader and the tools that
DEPEND on the registry had the careless ones.

Not merely a convenience. `run_conformance.load_agents()` was the closest thing
to a shared reader, and importing it is the coupling the agent-evaluation split
exists to undo — the analysis must not import the driver. A module below both
is what lets them share the reading without sharing the driving.

Failure is loud and named, never a silent `{}`: a registry that does not parse,
or that declares no platforms, is a broken repository rather than a repository
with no platforms.
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

RELATIVE = "adapters/platforms.json"


def _root(root: pathlib.Path | None = None) -> pathlib.Path:
    if root is not None:
        return root
    return next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / RELATIVE).exists())


def path(root: pathlib.Path | None = None) -> pathlib.Path:
    return _root(root) / RELATIVE


def registry_doc(root: pathlib.Path | None = None) -> dict:
    """-> the whole registry document, or an explanatory failure.

    Raises `ValueError` on a document that parses but declares nothing, because
    the difference between "no platforms" and "the file is broken" is the
    difference every caller here would otherwise get wrong.
    """
    data = json.loads(path(root).read_text(encoding="utf-8"))
    if not isinstance(data.get("platforms"), list) or not data["platforms"]:
        raise ValueError("platforms.json declares no platforms")
    return data


def platforms(root: pathlib.Path | None = None) -> list[dict]:
    """-> the platform records, in registry order."""
    return registry_doc(root)["platforms"]


def platform_by_id(root: pathlib.Path | None = None) -> dict[str, dict]:
    """-> {id: record}. Later records win, as `dict` has always done here."""
    return {p["id"]: p for p in platforms(root)}


def platform_ids(root: pathlib.Path | None = None) -> set[str]:
    return {p["id"] for p in platforms(root)}
