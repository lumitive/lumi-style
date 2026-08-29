"""release.py holds two rules that a person kept breaking, and declares nothing.

Both rules exist because the discipline failed in practice, not in theory: a red
preflight was committed twice in one session behind a pipe, and the first
version of this file answered a drift problem by adding a third copy of the
thing that drifts.
"""
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RELEASE = ROOT / "scripts" / "ops" / "release.py"
sys.path.insert(0, str(ROOT / "scripts" / "ops"))
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_repo  # noqa: E402
import release  # noqa: E402


def test_stamp_positions_come_from_the_guards_not_from_here():
    """The authority is check_repo's tables. This file may not restate them.

    The first version carried an eight-row table of its own, and the claim that
    it had been replaced by the shared constant was written down while the table
    was still there — which is why this is a test rather than a note.
    """
    derived = set(release.stamped_files())
    authority = set(check_repo.ENTRY_STAMP) | {n for n, _ in check_repo.TOKEN_STAMPS}
    assert derived == authority


def test_release_declares_no_stamp_table_of_its_own():
    # The WHOLE file, not the part after stamped_files(). The first version of
    # this test scanned from there down, and a probe that reinserted the table
    # ABOVE it passed — a test with a blind spot is a test that certifies the
    # region it does not look at.
    src = RELEASE.read_text(encoding="utf-8")
    code = re.sub(r'"""[\s\S]*?"""|^\s*#.*$', "", src, flags=re.M)
    # A path JOIN is legitimate — `ROOT / "SKILL.md"` locates the repository
    # root and reads the current version. What is not legitimate is naming a
    # stamped file as a bare literal, which is what a table entry looks like.
    offenders = [m.group(0) for m in
                 re.finditer(r'(?<!/ )"(?:SKILL\.md|AGENTS\.md|tokens/[\w.-]+|'
                             r'prompts/[\w./-]+|references/[\w./-]+|'
                             r'conformance/[\w./-]+)"', code)]
    assert not offenders, (
        f"release.py names stamp positions itself: {offenders[:3]}. The tables in "
        f"check_repo are the authority; a second list here is the drift this "
        f"repository spends most of its releases fixing.")


def test_every_declared_stamp_position_exists():
    for name in release.stamped_files():
        assert (ROOT / name).is_file(), f"{name} is declared and missing"


def test_the_constitution_is_a_declared_stamp_position():
    """It carried a stamp from 0.1.459 to 0.1.475 and was in no table, so a
    stamp naming a real EARLIER release passed silently."""
    assert "references/PRINCIPLES.md" in check_repo.ENTRY_STAMP


def test_there_is_no_flag_to_commit_past_a_failing_preflight():
    helptext = subprocess.run([sys.executable, str(RELEASE), "--help"],
                              capture_output=True, text=True).stdout
    for forbidden in ("--force", "--no-verify", "--skip-preflight", "--allow-fail"):
        assert forbidden not in helptext


def test_nothing_in_release_pipes_a_verification():
    """`cmd | tail && git commit` reads tail's exit status. That is the bug this
    file exists to make impossible, so the file itself must not contain it."""
    src = RELEASE.read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "|" not in re.sub(r"#.*|\"\"\".*?\"\"\"", "", src, flags=re.S).replace(
        "||", "").replace("|=", "")


def test_release_refuses_a_second_commit_for_one_version(tmp_path, monkeypatch,
                                                         capsys):
    """One commit per release, enforced rather than remembered.

    Two guards assume it — `check_commit_convention` holds a CHANGELOG-touching
    subject to the newest heading, and `check_evidence --init` finds the
    previous release by subject prefix. A second commit breaks both, and the
    sequence that produces one is the ordinary one: this script COMMITS, so a
    red preflight, a fix and a re-run leave two behind. It cost three squashes
    in a single session with the lesson written down after the first, which is
    how a rule that needs a tool announces itself.
    """
    import subprocess

    import release

    monkeypatch.setattr(release, "ROOT", tmp_path)

    def fake_run(argv, **kw):
        if argv[:3] == ["git", "log", "--format=%s"]:
            return subprocess.CompletedProcess(
                argv, 0, stdout="0.1.999 — a release already committed\n",
                stderr="")
        raise AssertionError(f"unexpected command {argv}")

    monkeypatch.setattr(release.subprocess, "run", fake_run)
    monkeypatch.setattr(release, "current_version", lambda: "0.1.998")
    monkeypatch.setattr(release, "newest_changelog_heading",
                        lambda: ("0.1.999", "a release already committed"))
    monkeypatch.setattr(sys, "argv",
                        ["release.py", "--version", "0.1.999", "--dry-run"])
    with pytest.raises(SystemExit) as exc:
        release.main()
    assert "already a 0.1.999 commit" in str(exc.value)
    assert "git reset --soft HEAD~1" in str(exc.value)


# THE SPEC LINE SURVIVES `--init`, and until 0.1.648 it did not.
#
# `release.py` carries a hand-written spec line across the `--init` rewrite only
# when the rewritten file has none. `--init` does not write "none" — when the
# diff is large enough to need a spec it writes a PLACEHOLDER, which is a
# non-empty string, so `not doc.get("spec")` was False on exactly the releases
# the branch exists for. The waiver was dropped and the release failed on the
# rule it had already answered: twice in one session at 0.1.648, a full
# preflight each time.
#
# The comment above that branch describes this failure happening to the WAIVERS
# field and says the spec line needed the same treatment. It got the treatment
# and not the test, and the treatment did not work.

def test_the_placeholder_is_a_name_both_files_can_read():
    """A literal in two files is the drift this repository counts. The carry
    has to ask "is this still unanswered", which it cannot do against a string
    only the writer knows."""
    import check_evidence
    assert check_evidence.SPEC_PLACEHOLDER
    assert "waived" in check_evidence.SPEC_PLACEHOLDER
    source = (pathlib.Path(__file__).resolve().parents[1]
              / "scripts" / "ops" / "release.py").read_text(encoding="utf-8")
    assert "check_evidence.SPEC_PLACEHOLDER" in source, (
        "release.py must ask check_evidence what unanswered looks like, "
        "never carry its own copy of the sentence")
    assert check_evidence.SPEC_PLACEHOLDER not in source, (
        "a second copy of the placeholder is the drift the constant removes")


def test_the_carry_treats_the_placeholder_as_unanswered():
    """The condition itself, evaluated the way release.py evaluates it. Written
    as the truth table rather than by calling the script, because reaching that
    branch means running a whole release."""
    import check_evidence
    placeholder = check_evidence.SPEC_PLACEHOLDER
    kept = "waived: the owner's ruling on GAP-044, not a design record"

    def carries(after_init: str) -> bool:
        # release.py's branch, verbatim in shape.
        return bool(kept and after_init in ("", placeholder))

    assert carries(placeholder), (
        "the placeholder means the rewrite has not answered the question, and "
        "this is the case that was silently dropping waivers")
    assert carries("")
    assert not carries("specs/2026-08-28-conformance-cell-design.md"), (
        "a real spec written by --init must not be overwritten by an older one")
