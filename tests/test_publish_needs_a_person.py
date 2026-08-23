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


def test_push_refuses_without_a_terminal():
    """The half an agent cannot satisfy. Everything else in this script is a
    check a machine can pass; this one is not."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'if [ ! -t 0 ]; then' in src, "no terminal test guards the push"
    refusal = src[src.index('if [ ! -t 0 ]; then'):]
    assert "REFUSING" in refusal and "exit 2" in refusal
    # and it comes BEFORE any push
    assert src.index('if [ ! -t 0 ]; then') < src.index("git -C \"$WORK/proj\" push")


def test_the_confirmation_is_the_version_not_a_keypress():
    """Typing the version means reading what is about to happen. `y` does not."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'read -r answer' in src
    assert '[ "$answer" = "$here" ]' in src, "any answer would do"


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
    assert 'PUSH=0' in src and '[ "${1:-}" = "--push" ] && PUSH=1' in src


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
