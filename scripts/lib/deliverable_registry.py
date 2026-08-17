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


# THE RULE TIER. `genre` was carrying two jobs at once: which thresholds and
# prose rules apply, and which story the document tells. Those are different
# questions — a market analysis and a status report are the same tier and
# different stories — and one field answering both is why five scripts once
# disagreed about what a genre was.
#
# The tier is derived from what actually keys on genre today, not invented:
# check_prose's DASH_BANNED exempts `internal`, and inspect_layout's
# VISUAL_SHARE_TARGET puts `training` at 30 where everything else is 50. Three
# tiers, and the `genre tiers` guard holds this table to those two.
TIERS = {"sales": "sales", "marketing": "sales", "consulting": "sales",
         "internal": "internal", "training": "training"}


# THE STORYLINE VOCABULARY — the narrative skeleton, the other half of the
# split. It answers "what shape is the argument", never "which rules apply".
#
# **The accepted-reference obligation hangs off the TIER, not off this.** Three
# tiers means three reference documents to accumulate, and adding a storyline
# adds none — the split does not multiply the corpus requirement, which is the
# first thing every reader assumes it does.
# `proposal` was added at 0.1.491 from GAP-013: a real internal design proposal
# could not open a trace because no name covered "here is a decision, here is
# what I recommend and why". Its skeleton is Template 5 in
# `references/storyline-templates.md`, and the `storyline templates` guard holds
# this tuple and that file to each other — a name here with no template there is
# a label with no shape behind it.
STORYLINES = ("market-analysis", "gtm", "status-report", "due-diligence",
              "product-intro", "training-curriculum", "proposal")


def tier_of(genre: str) -> str:
    """-> the rule tier for `genre`; raises KeyError loudly on an unknown one.

    Loudly, for the reason the checker map is loud: a genre that silently
    resolved to a default tier would grade a document against rules that are
    not its own and report it green.
    """
    return TIERS[genre]



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

# --- geometry: three vocabularies for one word, and the map between two -------
#
# The word `geometry` names three different things in this package, and until
# 0.1.499 nothing connected any pair of them:
#
#   · the COMPOSITION a document declares — `<body data-geometry="landscape">`,
#     which is what `tokens/` styles and `check_design.py` grades;
#   · the STAGE a build trace records — `trace_schema.ENUMS["geometry"]`;
#   · the VIEWPORTS `inspect_layout.py` renders at, which is a test matrix and
#     not a property of the document at all.
#
# The third is rightly its own list. The first two describe the same document
# and could disagree without anything noticing: a trace reading `a4` beside a
# body reading `landscape` was a contradiction no code could see. So the map
# between them is declared ONCE, here, and both sides derive from it.
COMPOSITIONS = ("landscape", "portrait")
STAGE_OF = {"landscape": "16x9", "portrait": "a4"}

# The sections a storyline typically carries. This is a CHECKLIST APPLIED AT
# THE END, never a template to start from — the evidence against template-first
# work is why the pipeline was turned around, and a list like this used as a
# starting point would reintroduce exactly what that turn was for.
#
# It is reported and never gated. Structural compliance does not predict
# quality; what is enforceable is that an absence be DECLARED, which is what
# `data-omitted` and the outline's `omitted:` line are for.
TYPICAL_SECTIONS = {
    "market-analysis": ("market size", "segments", "competitive landscape",
                        "demand drivers", "risks", "implication"),
    "gtm": ("target segment", "positioning", "channel", "pricing",
            "launch sequence", "success measure"),
    "status-report": ("headline", "progress", "risks and blockers", "asks",
                      "next checkpoint"),
    "due-diligence": ("scope and method", "findings", "quantified exposure",
                      "limitations", "recommendation"),
    # Extended from five to seven at the first blind review: the deck built
    # from the five words alone satisfied each word and scored 1 on
    # completeness — "overview" (the page the reader must remember) and
    # "get started" (link, install, first command, feedback channel) are the
    # substance the old words let an author skip. Template 6 is the skeleton.
    "product-intro": ("overview", "problem", "what it does",
                      "evidence it works", "get started", "next step"),
    "training-curriculum": ("objective", "prerequisites", "modules",
                            "practice", "assessment"),
}
