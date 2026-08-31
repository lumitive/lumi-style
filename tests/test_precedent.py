"""Step zero: has this been tried, and was it refused?

Every assertion here is a defect that actually happened on 2026-09-01, in one
session: a design proposed a mechanism declined in writing eight days earlier,
and re-committed a second refusal's shape twice. The refusals were structured
headings in files the author had open. Nobody looked.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import precedent  # noqa: E402


def test_it_finds_the_refusal_that_prompted_it():
    """FM-23 declined extending a cross-boundary guard to markdown on
    2026-08-23. A design proposed exactly that on 2026-09-01 without citing it.
    One search finds it."""
    hits = precedent.search(["prose", "cross-boundary"])
    ids = {h[0] for h in hits}
    assert "FM-23" in ids, ids


def test_a_refusal_below_the_abandoned_gates_line_reads_as_refused():
    """FM-23 carries an `FM-` id but lives under `# Abandoned gates`, so it is
    a DECLINED MECHANISM, not a recorded failure mode. Reporting it as the
    latter is the under-reading this tool exists to stop."""
    hit = next(h for h in precedent.search(["cross-boundary"]) if h[0] == "FM-23")
    assert hit[4] is True, "FM-23 must report as refused"
    fm01 = precedent.search(["A guard that has never"])
    for h in fm01:
        if h[0] == "FM-01":
            assert h[4] is False, "FM-01 is above the line and is not a refusal"


def test_it_finds_the_refusal_re_committed_twice_in_one_session():
    """AG-10 declined requiring every analytical move to bind a library shape,
    after shipping it for one commit and watching its author bind a wrong shape
    without opening the SVG."""
    ids = {h[0] for h in precedent.search(["library shape"], body=True)}
    assert "AG-10" in ids, ids


def test_no_hit_is_not_a_clean_bill(capsys):
    """The dangerous answer. A mechanism described in other words is still a
    mechanism that was refused, and a tool that printed a bare 'none' would be
    read as permission."""
    precedent.main(["zzzz-no-such-mechanism"])
    out = capsys.readouterr().out
    assert "NOT a clean bill" in out


def test_an_unreadable_ledger_is_a_failed_search(tmp_path, capsys):
    """FM-24's third answer. A search that could not read the refusals must not
    print what a search finding nothing prints."""
    assert precedent.entries(tmp_path) == []
    import unittest.mock
    with unittest.mock.patch.object(precedent, "ROOT", tmp_path):
        assert precedent.main(["anything"]) == 1
    assert "failed search" in capsys.readouterr().err


def test_every_ledger_it_claims_to_search_is_readable():
    """A source that quietly stopped parsing would shrink the corpus in
    silence."""
    seen = {e[3] for e in precedent.entries()}
    assert seen == set(precedent.SOURCES), seen
    assert len(precedent.entries()) > 50
