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


def test_the_token_files_are_all_stamped_paths():
    for name, _pattern in stamps.TOKEN_STAMPS:
        assert name in stamps.stamped_paths()


def test_a_directory_gets_a_wider_line_budget_than_a_file():
    """A regenerated fixture moves its version line in several places; an entry
    point moves one. The budget is the evidence gate's business and stays
    there, which is why the shared table carries paths and not budgets."""
    budgets = dict(check_evidence.STAMPED_PREFIXES)
    assert budgets["fixtures/"] > budgets["SKILL.md"]
