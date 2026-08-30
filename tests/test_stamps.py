"""One table for "which files carry the version stamp", where there were three.

`check_versions` held `TOKEN_STAMPS`, `check_version_citations` held
`ENTRY_STAMP`, and `check_evidence` held `STAMPED_PREFIXES` — three hand-written
answers to one question, and CLAUDE.md said there were two. They had already
diverged: `references/PRINCIPLES.md` was declared in `ENTRY_STAMP` and absent
from the evidence gate's list.

The consequence was latent and exact. `check_evidence.TOUCH_MAP` maps
`references/` to the `conformance-freshness` obligation — a full multi-agent
round. Every release stamps `PRINCIPLES.md`, and the evidence gate could not
tell that stamp from an edit, so once the board went stale every release would
owe a conformance round for having changed no rule at all.
"""
import pathlib
import re

import check_evidence
import check_repo
import stamps


def test_the_three_readers_share_one_table():
    """Not "they agree" — that a divergence is impossible, because there is one
    table and the other two read it."""
    assert check_repo.TOKEN_STAMPS is stamps.TOKEN_STAMPS
    assert check_repo.ENTRY_STAMP is stamps.ENTRY_STAMP
    declared = {p for p, _ in check_evidence.STAMPED_PREFIXES}
    assert declared == set(stamps.stamped_paths())


def test_every_entry_point_that_declares_a_stamp_is_treated_as_stamped():
    """The divergence that existed: a file whose stamp position is declared, and
    whose stamp the evidence gate reads as a content edit."""
    prefixes = [p for p, _ in check_evidence.STAMPED_PREFIXES]
    for entry in stamps.ENTRY_STAMP:
        assert any(entry.startswith(p) for p in prefixes), (
            f"{entry} declares where its stamp lives and the evidence gate "
            f"would read that stamp as a touch")


def test_principles_md_is_the_case_that_was_wrong():
    """Named, because a general assertion would have passed before the fix too:
    PRINCIPLES.md is the file that was declared in one table and missing from
    another, and `references/` is the prefix that obliges a conformance round."""
    assert "references/PRINCIPLES.md" in stamps.ENTRY_STAMP
    assert any("references/PRINCIPLES.md".startswith(p)
               for p, _ in check_evidence.STAMPED_PREFIXES)


def test_build_card_is_the_case_that_was_wrong_the_second_time():
    """Named for the same reason PRINCIPLES.md is: `references/build-card.md` is
    GENERATED and stamped every release, but was missing from GENERATED_STAMPED
    until 0.1.658 — so the evidence gate read its version header as a
    `references/` rule change and obliged a full conformance round on every
    release that touched it (0.1.657 waived one without knowing why)."""
    assert "references/build-card.md" in stamps.GENERATED_STAMPED
    assert any("references/build-card.md".startswith(p)
               for p, _ in check_evidence.STAMPED_PREFIXES)


def test_every_generated_stamped_file_under_references_is_excluded():
    """The general form, so a third loss cannot happen quietly: any generated
    artifact that carries a version stamp must be stamp-listed, or its stamp
    reads as a rule change under an obligation-bearing prefix."""
    root = pathlib.Path(__file__).resolve().parents[1]
    prefixes = [p for p, _ in check_evidence.STAMPED_PREFIXES]
    visited = []
    for path in (root / "references").glob("*.md"):
        head = path.read_text(encoding="utf-8")[:400]
        if "**GENERATED**" not in head:
            continue
        rel = f"references/{path.name}"
        # a generated file with no version in its header carries no stamp
        if not re.search(r"\d+\.\d+\.\d+", head.splitlines()[0]):
            continue
        visited.append(rel)
        assert any(rel.startswith(p) for p in prefixes), (
            f"{rel} is generated and version-stamped but the evidence gate "
            f"would read its stamp as a rule change")
    # A SCAN THAT MATCHED NOTHING IS NOT A PASS. Both heuristics above key on
    # the header's wording; if it is reworded this loop silently inspects zero
    # files and reports green — FM-24, in the very test written to stop a third
    # silent loss. `check_one_home`'s selftest strings are the same discipline.
    assert visited, ("the generated-file scan matched no file — its heuristics "
                     "no longer fit the headers, so it is guarding nothing")


def test_the_token_files_are_all_stamped_paths():
    for name, _pattern in stamps.TOKEN_STAMPS:
        assert name in stamps.stamped_paths()


def test_a_directory_gets_a_wider_line_budget_than_a_file():
    """A regenerated fixture moves its version line in several places; an entry
    point moves one. The budget is the evidence gate's business and stays
    there, which is why the shared table carries paths and not budgets."""
    budgets = dict(check_evidence.STAMPED_PREFIXES)
    assert budgets["fixtures/"] > budgets["SKILL.md"]
