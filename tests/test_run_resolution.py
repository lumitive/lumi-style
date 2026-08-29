"""One `--run` value means one directory, whichever verb reads it.

It did not. `run` expanded `~` and resolved a bare name under the results root;
`score` did neither, so the run id an operator had just passed to `run` came
back from `score` as **"does not exist; run `run` first"** — a wrong diagnosis
of a directory that existed. Two readers of the board's history did the same,
and a third expanded `~` and nothing else.

Nobody hit it for a hundred releases because `run`'s closing line prints the
ABSOLUTE path for the next command: the tool was routing its operator around
its own defect. It surfaced the first time somebody typed the id instead of
pasting the path (2026-08-29, the three-round cursor collection).

The lesson is the branch's, not the bug's: a defect a tool works around in its
own output is a defect nothing will report.
"""
import pathlib

import run_conformance as rc


def test_a_bare_name_is_a_run_id_under_the_results_root():
    """Not a path against the working directory. Taken literally and invoked
    from the checkout, `--run r13` writes a whole run — transcripts, driver
    records, an agent's deck — into the repository, which is the one place the
    2026-08-21 directive says conformance results may not go."""
    assert rc.resolve_run("r13") == rc.RESULTS / "r13"


def test_a_value_that_names_a_path_is_honoured_as_one():
    """An operator pointing at a scratch directory means it."""
    absolute = "/srv/scratch"          # any absolute path; not written to
    assert rc.resolve_run(absolute) == pathlib.Path(absolute)
    assert rc.resolve_run("sub/dir") == pathlib.Path("sub/dir")


def test_a_tilde_is_expanded():
    """`history.json` records run directories with `~`, so a reader that does
    not expand resolves none of them."""
    got = rc.resolve_run("~/x/y")
    assert got == pathlib.Path.home() / "x" / "y"
    assert "~" not in str(got)


def test_the_id_and_the_path_it_becomes_are_the_same_directory():
    """THE CASE THAT BROKE. `run --run X` then `score --run X` must reach one
    directory, and so must the absolute path `run` prints afterwards."""
    by_id = rc.resolve_run("0.1.648-r2")
    by_path = rc.resolve_run(str(by_id))
    by_tilde = rc.resolve_run(str(by_id).replace(str(pathlib.Path.home()), "~"))
    assert by_id == by_path == by_tilde


def test_every_reader_of_a_run_directory_goes_through_it():
    """A parity check rather than a behaviour one: the four call sites had four
    behaviours, and the only thing stopping a fifth is that nothing else builds
    a run path by hand. Read off the source, because a new reader is added by
    writing a line and not by failing a test."""
    src = (pathlib.Path(rc.__file__)).read_text(encoding="utf-8")
    stray = [ln.strip() for ln in src.splitlines()
             if 'pathlib.Path(r)' in ln or 'pathlib.Path(runs[' in ln]
    assert stray == [], (
        f"a run directory is built without resolve_run: {stray}")
