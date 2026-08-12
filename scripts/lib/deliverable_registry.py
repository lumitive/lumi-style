"""The one map from checker kind to checker script.

check_fixtures.py and run_conformance.py carried identical private copies of
this map — FM-07's shape (a producer/consumer pair held together by nothing),
found by the PR #87 review's coupling analysis. One copy, resolved relative
to this file's own scripts/ root, so the drawer the checkers live in is
encoded in exactly one place.

Zero repo imports on purpose: both consumers import this leaf, and a leaf
that imported either of them would knot the dependency graph.
"""
from __future__ import annotations

import pathlib

_SCRIPTS = next(p for p in pathlib.Path(__file__).resolve().parents
                if p.name == "scripts")

# kind -> script filename. The drawer prefix is added by checker_path, so a
# future move edits _DRAWER alone.
_DRAWER = "check"  # the checkers' drawer since the 0.1.439 move
_SCRIPTS_BY_KIND = {
    "prose": "check_prose.py",
    "design": "check_design.py",
    "layout": "inspect_layout.py",
}


def checker_path(kind: str) -> pathlib.Path:
    """-> absolute path of the checker for `kind`; raises KeyError on an
    unknown kind, loudly, because a misspelled kind that silently resolved
    to nothing would score an artifact as unchecked-green."""
    base = _SCRIPTS / _DRAWER if _DRAWER else _SCRIPTS
    path = base / _SCRIPTS_BY_KIND[kind]
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} does not exist — the checker moved and this registry "
            f"was not updated (_DRAWER is the one knob)")
    return path


def kinds() -> tuple[str, ...]:
    return tuple(_SCRIPTS_BY_KIND)
