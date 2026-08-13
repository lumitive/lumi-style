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


# THE GENRE VOCABULARY, in one place, for the same reason the checker map is.
# Five scripts carried five different lists: check_prose 3, new_deck 4,
# inspect_layout 5, review_scores 5, export_pdf "check_prose's 3 plus a
# hand-appended consulting". The consequence was not cosmetic — a consulting
# deliverable could be scaffolded, layout-graded and review-scored, but
# `check_prose.py --genre consulting` refused the value, so its prose had to be
# checked under a genre it is not. An Evals suite keyed on genre cannot be built
# on five vocabularies that disagree.
#
# The NAMES are one set. The BEHAVIOUR keyed on them stays with each script —
# visual-share targets, the dash ban, which scaffolds exist — because those
# genuinely differ and pretending otherwise would be the opposite mistake.
GENRES = ("sales", "marketing", "consulting", "internal", "training")


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
