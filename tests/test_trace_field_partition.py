"""One flat record, two populations, and until now nothing said which was which.

A trace carries the document's facts (pages, layouts, gates) and the producer's
(agent, model, effort, tokens) as siblings. That was tolerable while one tool
read them; it stopped being tolerable when the model x effort cost matrix moved
out of the document ledger into `scripts/lib/agent_runs.py`, because the two
readers now have opposite obligations:

  * the DOCUMENT reader may read producer fields only to GROUP, never to grade;
  * the AGENT reader may read document fields only to QUALIFY, never to
    describe the agent.

Declared as a PARTITION rather than two lists. A list can omit a member in
silence — a field added to `FIELDS` and assigned to neither side would simply
never be anybody's, and no guard would say so. A partition cannot.
"""
import pathlib

import check_repo
import trace_schema

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIDES = ("DOCUMENT_FIELDS", "PRODUCER_FIELDS", "RUN_FIELDS")


def test_the_shipped_partition_is_exhaustive_and_disjoint():
    union = set().union(*(getattr(trace_schema, s) for s in SIDES))
    assert union == set(trace_schema.FIELDS)
    for i, a in enumerate(SIDES):
        for b in SIDES[i + 1:]:
            assert not (getattr(trace_schema, a) & getattr(trace_schema, b)), (a, b)


def test_the_shipped_repo_passes_the_guard():
    assert check_repo.check_trace_schema() == []


def test_a_field_belonging_to_no_side_is_a_finding(monkeypatch):
    """The case a two-list design cannot see: nobody claimed it."""
    monkeypatch.setattr(trace_schema, "DOCUMENT_FIELDS",
                        trace_schema.DOCUMENT_FIELDS - {"genre"})
    errors = check_repo.check_trace_schema()
    assert any("'genre'" in e and "no side claims it" in e for e in errors), errors


def test_a_field_claimed_twice_is_a_finding(monkeypatch):
    monkeypatch.setattr(trace_schema, "PRODUCER_FIELDS",
                        trace_schema.PRODUCER_FIELDS | {"genre"})
    errors = check_repo.check_trace_schema()
    assert any("both DOCUMENT_FIELDS and PRODUCER_FIELDS" in e for e in errors)


def test_a_side_claiming_an_undeclared_field_is_a_finding(monkeypatch):
    monkeypatch.setattr(trace_schema, "RUN_FIELDS",
                        trace_schema.RUN_FIELDS | {"invented_field"})
    errors = check_repo.check_trace_schema()
    assert any("'invented_field'" in e and "does not declare" in e
               for e in errors), errors


def test_the_partition_is_checked_even_with_no_traces_on_disk(tmp_path,
                                                              monkeypatch):
    """What it prints when it cannot look at the store.

    The guard's older half returns `[]` for a tree with no `evals/traces/`,
    which is right — an empty store is a legal state. But the partition is a
    property of the SCHEMA, not of the store, so it must still be checked. The
    first draft returned `[]` before reaching it, which would have made every
    synthetic tree — the house pattern for red-testing a guard — a green pass
    over an unchecked partition. FM-24, in the guard being added.
    """
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)          # no evals/traces/
    monkeypatch.setattr(trace_schema, "RUN_FIELDS",
                        trace_schema.RUN_FIELDS | {"invented_field"})
    assert check_repo.check_trace_schema(), (
        "a tree with no trace store skipped the partition check entirely")


def test_every_field_a_producer_reader_uses_is_on_the_producer_side():
    """`agent_runs` groups by model and effort; both must be producer fields."""
    assert {"model", "effort"} <= trace_schema.PRODUCER_FIELDS
    assert "gates" in trace_schema.DOCUMENT_FIELDS, (
        "the board's admission ticket is a document fact and must stay one")


# The guard must NOT follow `LUMI_TRACES`. This is the one call site in the
# repository where hand-resolving `evals/traces` is correct, and a reviewer
# asked for `trace_store.traces_dir(ROOT)` instead. Measured before declining:
# `conftest.py` redirects the whole suite to an empty scratch store, so that
# call would have walked zero files against 255 tracked ones and returned
# clean — FM-24 arriving inside the fix for FM-24. Without this test the next
# reader makes the same request and nothing argues back.

def test_the_guard_reads_the_tracked_store_not_the_redirected_one(monkeypatch):
    import os
    assert os.environ.get("LUMI_TRACES"), (
        "conftest redirects the suite's store; if that stops being true this "
        "test is measuring nothing")
    tracked = list((check_repo.ROOT / "evals" / "traces").glob("*.json"))
    redirected = list(pathlib.Path(os.environ["LUMI_TRACES"]).glob("*.json"))
    assert len(tracked) > len(redirected), (
        "the two stores must differ for this test to be able to fail")

    seen = []
    real = trace_schema.validate
    def _watch(rec):
        seen.append(rec)
        return real(rec)

    monkeypatch.setattr(trace_schema, "validate", _watch)
    check_repo.check_trace_schema()
    assert len(seen) == len(tracked), (
        f"the guard validated {len(seen)} traces; the tracked store holds "
        f"{len(tracked)}. It followed LUMI_TRACES.")
