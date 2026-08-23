"""Publishing needs a person, and the script is what holds that.

Owner instruction, 2026-08-23: the push to the published repository waits for
her say-so, one publication at a time. A rule that lives only in an agent's
memory is a rule until the next session — convention 16's whole point, and the
reason `release.py` refuses to commit on a red preflight rather than trusting
anyone to check.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ops" / "publish.sh"


def test_the_script_parses():
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0


def test_push_refuses_without_a_named_version():
    """A bare `--push` had already become a habit — mine. The version changes
    every release, so naming it cannot."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'if [ -z "$CLAIMED" ]; then' in src
    refusal = src[src.index('if [ -z "$CLAIMED" ]; then'):]
    assert "REFUSING" in refusal and "exit 2" in refusal
    assert src.index('if [ -z "$CLAIMED" ]; then') < src.index('git -C "$WORK/proj" push')


def test_a_version_that_is_not_this_checkout_refuses():
    src = SCRIPT.read_text(encoding="utf-8")
    assert '[ "$CLAIMED" != "$here" ]' in src
    assert src.index('[ "$CLAIMED" != "$here" ]') < src.index('git -C "$WORK/proj" push')


def test_no_tty_test_guards_the_push():
    """The first version of this gate refused whenever stdin was not a
    terminal, and BLOCKED THE OWNER: `!` in Claude Code has no TTY either, so a
    check meant to distinguish an agent from a person distinguished neither and
    failed against the person it existed to serve."""
    code = "\n".join(line for line in SCRIPT.read_text(encoding="utf-8").splitlines()
                     if not line.lstrip().startswith("#"))
    assert "-t 0" not in code


def test_the_remote_version_comes_from_the_api_not_the_cdn():
    """raw.githubusercontent caches for minutes, so right after a publish it
    names the PREVIOUS version — which is exactly when this line is read."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'gh api "repos/$slug/contents/SKILL.md"' in src
    # the raw host may be NAMED in the comment that explains why it is not
    # used; what must not exist is a command fetching from it
    code = "\n".join(line for line in src.splitlines()
                     if not line.lstrip().startswith("#"))
    assert "raw.githubusercontent" not in code


def test_a_dry_run_is_the_default():
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'PUSH=0' in src
    assert '[ "${1:-}" = "--push" ] && { PUSH=1; CLAIMED=${2:-}; }' in src


def test_it_refuses_without_an_out_of_bounds_list():
    """The check that found a client name in CHANGELOG.md on its first real
    run. check_secrets' client-name half silently skips when the list is
    absent and then reports green."""
    src = SCRIPT.read_text(encoding="utf-8")
    needle = "REFUSING: no *.terms.txt"
    assert needle in src
    # before anything is built, let alone pushed
    assert src.index(needle) < src.index('git clone -q --branch main')
    assert src.index(needle) < src.index('git -C "$WORK/proj" push')
