"""A pass over eighteen gates and a pass over thirteen printed the same word.

"Zero gating failures" is the sentence a board's reader takes away, and it does
not say how much was held. The 2026-08-26 conformance round published that pair
side by side: one deck carried an agenda, part openers and pages declaring an
analysis move, so eighteen gates had a subject; the other had none of them, so
five of its clean rows graded nothing.

**The four rows that pass over an absence are not the defect.** `check_design`
argues the ruling in writing at D27 and D35 — a measured absence passes, and
`n/a` is for a gate that could not look — and a deck may legitimately have no
agenda: the two intro decks the owner accepted have none. The missing thing was
the count beside the verdict.
"""
import json
import pathlib

import check_design
import gate_registry

ROOT = pathlib.Path(__file__).resolve().parents[1]
PASS = ROOT / "fixtures" / "deck-pass.en.html"


def _graded(path):
    r = check_design.measure(path)
    return r, {n: v for n, _, _, v in check_design.grade(r)}


def test_a_fixture_that_carries_its_pages_holds_them_all():
    r, verdicts = _graded(PASS)
    held, vacuous = check_design.held_gates(r, verdicts)
    assert held, "no gate was counted as held on the passing fixture"
    assert not (held & vacuous), "a gate counted both ways"


def test_removing_the_agenda_moves_four_gates_out_of_held():
    """The measured difference between the two conformance decks, in one file."""
    r, verdicts = _graded(PASS)
    held_before, _ = check_design.held_gates(r, verdicts)
    stripped = dict(r)
    stripped["D27_agenda_mirror"] = None
    stripped["D35_agenda_exclusive"] = None
    stripped["D38_agenda_rows"] = None
    v2 = {n: v for n, _, _, v in check_design.grade(stripped)}
    held_after, vacuous_after = check_design.held_gates(stripped, v2)
    # `always` is not a missing declaration: the subject is the document
    # itself, so the gate can never be silent over a shape of deliverable.
    assert len(held_before) - len(held_after) == 4, (
        f"{len(held_before)} -> {len(held_after)}")
    assert {"D27_agenda_mirror", "D35_agenda_exclusive",
            "D38_agenda_highlight", "D38_agenda_page_spans"} <= vacuous_after
    # AND THEY STILL SAY `ok`. That is the ruling, not a bug — the count is
    # what tells the two clean sheets apart.
    for name in ("D27_agenda_mirror", "D35_agenda_exclusive"):
        assert v2[name] == "ok", name


def test_an_n_a_gate_is_not_held_either():
    """`n/a` and "nothing to grade" are the same answer to the same question.

    The first version of this test carried a conditional that always evaluated
    False, so its loop body never ran — a test that could not fail, in the file
    about a count that could not be seen.
    """
    import gating
    r, verdicts = _graded(PASS)
    held, vacuous = check_design.held_gates(r, verdicts)
    gates = gating.gating_metrics(verdicts, ROOT)
    na = {n for n in gates if verdicts[n] == "n/a"}
    assert na, "the passing fixture has no n/a gate; this asserts nothing"
    assert na <= vacuous and not (na & held)


def test_the_report_carries_the_count():
    import subprocess
    import sys
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check" / "check_design.py"),
         "--json", str(PASS)], capture_output=True, text=True, cwd=ROOT)
    doc = json.loads(out.stdout)[0]
    assert isinstance(doc["gates_held"], list) and doc["gates_held"]
    assert isinstance(doc["gates_with_nothing_to_grade"], list)
    assert not set(doc["gates_held"]) & set(doc["gates_with_nothing_to_grade"])


def test_every_declared_subject_is_a_measurement_the_checker_produces():
    """The register may add knowledge and may not invent it.

    `key` or `key.field` — the second is the count shape, a measurement that is
    present and reports zero of what it grades. `check_repo`'s guard cannot
    discover those, so this path validation is what holds them.
    """
    r = check_design.measure(PASS)
    for name, entry in gate_registry.load(ROOT).items():
        subject = entry.get("subject")
        if not subject or subject == "always":
            continue
        key, _, field = subject.partition(".")
        assert key in r, f"{name} declares subject {subject!r}"
        if field:
            assert isinstance(r[key], dict) and field in r[key], subject


def test_a_document_with_no_image_does_not_hold_the_imagery_gates():
    """The count shape of absence, which the probe cannot see.

    `D25_image_provenance` is present and says `rasters: 0`. It prints `ok`,
    correctly — there is no image failing to name its terms — and it graded
    nothing. None of the three conformance decks carries an image, which is why
    every held count in that round is two below the eighteen rows that gate.
    """
    r, verdicts = _graded(PASS)
    assert r["D25_image_provenance"]["rasters"] == 0
    held, vacuous = check_design.held_gates(r, verdicts)
    assert {"D24_images_embedded", "D25_image_provenance"} <= vacuous
    assert not ({"D24_images_embedded", "D25_image_provenance"} & held)


def test_a_document_that_carries_an_image_does_hold_them():
    """The other direction, on the one fixture that has a raster."""
    broken = ROOT / "fixtures" / "deck-broken.en.html"
    r, verdicts = _graded(broken)
    assert r["D25_image_provenance"]["rasters"] > 0
    held, _ = check_design.held_gates(r, verdicts)
    assert {"D24_images_embedded", "D25_image_provenance"} <= held
