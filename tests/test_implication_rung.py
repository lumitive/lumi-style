"""GAP-031: a deck can delete its takeaway rung and every gate stays green.

The gate here reads NO PROSE. That is the whole design, and it was arrived at
by measurement rather than by reasoning.

The obvious candidate -- GAP-031's own wording, "a planned implication that
reached no page at all, in any element" -- was built and then tested against
every real outline/document pair on this machine, and it false-failed three
separate ways:

  * **Translation.** `r17zh` carries a faithful Chinese rendering of every one
    of its seventeen English implications. Text comparison scored 17 of 17
    MISSING. Chinese is the owner's real delivery language, so the gate would
    have red-lined correct accepted work, in the language it ships in.
  * **Rewriting.** This is the 2026-08-19 refusal, verbatim: "a take rewritten
    better than its outline is a legitimate outcome, and the check cannot tell
    that from a take that lost the point." Measured on the a2ui research deck:
    six of ten.
  * **The field is not always a reader implication.** Real outlines put build
    directives in it -- "state the positioning in one sentence, three core
    values one per cell" -- and the page obeys without quoting it.

What survives is the structural half of the same gap, which is what GAP-031
actually observed: the outline declared an implication for every page and the
build carried the rung on NONE of them. So the gate is the wholesale case only,
and partial is reported as a `note`.

An earlier draft of this docstring claimed "no real deliverable in the corpus is
partial". A review measured it and that is FALSE -- three documents are partial,
one of them a finished body fragment at 1 of 8. What the evidence supports is
narrower: every finished deliverable in the corpus carries a take on every
content page, in both languages across seventeen rounds, and the corpus offers
no case on which to place a partial line. That is why partial is reported rather
than gated -- absence of a line to draw, not absence of the shape.
"""

import check_outline as co

OUTLINE = ("genre: sales\nstoryline: pitch-deck\n\n## Part A · Alpha\n\n"
           "- Alpha beats beta on cost\n"
           "  analysis: compare | finding: alpha beats beta | "
           "implication: buyers save\n"
           "- Gamma holds the line\n"
           "  analysis: position | finding: gamma holds | "
           "implication: the moat is gamma\n")


def _page(pid, title, take=None):
    body = f'<h2 class="t">{title}</h2>'
    if take is not None:
        body += f'<p class="take">{take}</p>'
    return f'<section class="page" id="{pid}">{body}</section>'


def _rung(findings):
    return next((f for f in findings if f["check"] == "implication rung absent"),
                None)


def test_a_deck_that_deleted_the_rung_fails():
    """THE DELIBERATE RED. GAP-031's measured case: ten content pages, zero
    `.take` elements, the tier-1 callout substituted on some and nothing on the
    rest. Every gate was green."""
    html = (_page("p1", "Alpha beats beta on cost")
            + _page("p2", "Gamma holds the line"))
    found = _rung(co.drift(OUTLINE, html))
    assert found and found["verdict"] == "FAIL", found


def test_a_rewritten_take_is_not_failed():
    """The 2026-08-19 refusal, preserved. Nothing here matches the plan's
    wording; the rung is present, so the gate must stay silent and leave the
    judgement to the reported line."""
    html = (_page("p1", "Alpha beats beta on cost",
                  "Re-price the entry tier before the next cycle.")
            + _page("p2", "Gamma holds the line",
                    "Defend the quadrant you can actually hold."))
    found = _rung(co.drift(OUTLINE, html))
    assert found and found["verdict"] == "ok", found


def test_a_translated_deck_is_not_failed():
    """THE MEASURED FALSE FAIL that killed the text predicate: a faithful
    translation scored 17 of 17 missing. The gate reads no prose, so a document
    in a language the outline is not written in is graded exactly like any
    other."""
    html = (_page("p1", "Alpha beats beta on cost", "买方因此省钱。")
            + _page("p2", "Gamma holds the line", "护城河就是 gamma。"))
    found = _rung(co.drift(OUTLINE, html))
    assert found and found["verdict"] == "ok", found


def test_a_partial_rung_is_a_note_and_not_an_ok():
    """Partial is REPORTED and not gated -- the corpus gives no evidence for
    where the line belongs (convention 4: a floor at zero, never a rate).

    But it must not print `ok`. A review found a real deliverable at 1 of 8,
    and pointed out that `ok` at 1-of-10 and `ok` at 10-of-10 are the same
    verdict and the same exit code -- which is the silence this whole gate was
    written to end, committed by the gate itself."""
    html = (_page("p1", "Alpha beats beta on cost", "buyers save")
            + _page("p2", "Gamma holds the line"))
    found = _rung(co.drift(OUTLINE, html))
    assert found and found["verdict"] == "note", found
    assert "1 of 2" in found["detail"], found


def test_an_unreadable_document_is_not_called_clean():
    """FM-24's third answer. A document no content page could be read out of
    has not been measured, and must not print what a document carrying the rung
    prints -- the failure this repository shipped six times in 0.1.608-612."""
    absent = _rung(co.drift(OUTLINE, "<html><body><p>no sections</p></body></html>"))
    clean = _rung(co.drift(OUTLINE, _page("p1", "Alpha beats beta on cost", "buyers save")
                           + _page("p2", "Gamma holds the line", "the moat is gamma")))
    assert absent is not None, "an unreadable document must still say something"
    assert absent["verdict"] == "not_measured", absent
    assert str(absent["detail"]) != str(clean["detail"]), (
        "the blind branch prints what the clean branch prints")


def test_an_outline_declaring_no_implication_is_silent():
    """An honest silence: there is no declaration, so there is no
    contradiction to find."""
    outline = ("genre: sales\nstoryline: pitch-deck\n\n## Part A · Alpha\n\n"
               "- Alpha beats beta on cost\n")
    assert _rung(co.drift(outline, _page("p1", "Alpha beats beta on cost"))) is None


def test_an_empty_takeaway_element_is_not_a_takeaway():
    """The cheapest way to fake a rung past a structural gate is to ship the
    element with nothing in it. A whitespace-only take is the absence it looks
    like. (A take of one full stop is NOT caught, and raising the floor to
    catch it is refused on the record: `evals/thresholds.json`'s status_note is
    this repository's measured case that a satisfiable number ends the
    looking.)"""
    for empty in ("", "   ", "\n\t"):
        html = (_page("p1", "Alpha beats beta on cost", empty)
                + _page("p2", "Gamma holds the line", empty))
        assert _rung(co.drift(OUTLINE, html))["verdict"] == "FAIL", repr(empty)


def test_a_document_that_parsed_fine_with_no_content_page_is_not_measured():
    """The OTHER blind shape. The parse-failure case is not the only way
    `pages` comes back empty: a document of nothing but cover and closing
    parsed perfectly and has simply nothing to grade. FM-24 is this branch's
    whole justification, so both shapes need the third answer."""
    html = ('<section class="page cover" id="c"><h2 class="t">Title</h2></section>'
            '<section class="page closing" id="z"><h2 class="t">End</h2></section>')
    assert _rung(co.drift(OUTLINE, html))["verdict"] == "not_measured"


# --- the outline axis: the gate's OTHER input, which the first cut left blind -

def _beats(*lines):
    body = "".join(f"- Title {i}\n  {ln}\n" for i, ln in enumerate(lines, 1))
    return f"genre: sales\nstoryline: pitch-deck\n\n## Part A\n\n{body}"


NO_TAKES = (_page("p1", "Title 1") + _page("p2", "Title 2"))


def test_a_beat_declaring_no_implication_stays_silent():
    """PINS THE TRIGGER. A mutation replacing the predicate with `list(analyses)`
    -- gating on any declared analysis rather than on a declared implication --
    survived the first cut of this suite. An outline that declares moves and
    findings and no implication has promised nothing about the rung, and must
    not be red-lined for breaking a promise it did not make."""
    outline = _beats("analysis: compare | finding: alpha beats beta",
                     "analysis: position | finding: gamma holds")
    assert _rung(co.drift(outline, NO_TAKES)) is None


def test_an_implication_the_parser_could_not_read_is_not_silence():
    """FM-24's third answer on the OUTLINE axis. AR-3's beat is ONE line; an
    outline writing the three fields on separate lines still parses as beats
    and every implication becomes invisible, so a document with the rung
    deleted from every page printed exactly what an outline declaring nothing
    prints. The discriminator is the outline's own text: `implication:` is
    written, and no beat yielded one."""
    outline = ("genre: sales\nstoryline: pitch-deck\n\n## Part A\n\n"
               "- Title 1\n  analysis: compare\n  finding: alpha\n"
               "  implication: buyers save\n"
               "- Title 2\n  analysis: position\n  finding: gamma\n"
               "  implication: the moat\n")
    found = _rung(co.drift(outline, NO_TAKES))
    assert found and found["verdict"] == "not_measured", found
    silent = _rung(co.drift(
        _beats("analysis: compare | finding: alpha beats beta"), NO_TAKES))
    assert silent is None, "the honest-silence case must stay silent"


def test_a_blank_implication_value_is_not_a_declaration():
    """`implication:` with nothing after it. The `\\S` in the predicate is what
    separates it from a filled one, and a mutation dropping it survived."""
    outline = _beats("analysis: compare | finding: a | implication:")
    found = _rung(co.drift(outline, NO_TAKES))
    assert found and found["verdict"] == "not_measured", found


def test_the_field_is_matched_case_insensitively():
    """A mutation dropping `re.I` survived. An outline capitalising the field
    still declares the rung."""
    outline = _beats("analysis: compare | finding: a | Implication: buyers save",
                     "analysis: position | finding: b | IMPLICATION: the moat")
    found = _rung(co.drift(outline, NO_TAKES))
    assert found and found["verdict"] == "FAIL", found


# --- the CLI, which is what build.py actually runs ---------------------------

def test_the_command_line_gates_and_the_blind_branch_gates_too(tmp_path):
    """END TO END, because `build.py:314` consumes the EXIT CODE and nothing
    tested that path. The third answer counts as a failure here for the reason
    `check_prose` counts `blind`: a document the parser could not read must not
    reach the only gating consumer as a passing stage."""
    import pathlib as _pl
    import subprocess
    import sys as _sys
    root = _pl.Path(__file__).resolve().parents[1]
    outline = tmp_path / "o.md"
    outline.write_text(OUTLINE, encoding="utf-8")

    def run(html):
        deck = tmp_path / "d.html"
        deck.write_text(f"<html><body>{html}</body></html>", encoding="utf-8")
        return subprocess.run(
            [_sys.executable, str(root / "scripts/check/check_outline.py"),
             str(outline), "--against", str(deck)],
            capture_output=True, text=True, cwd=root)

    red = run(_page("p1", "Alpha beats beta on cost")
              + _page("p2", "Gamma holds the line"))
    assert red.returncode == 1, red.stdout
    assert "implication rung absent" in red.stdout

    green = run(_page("p1", "Alpha beats beta on cost", "buyers save")
                + _page("p2", "Gamma holds the line", "the moat is gamma"))
    assert green.returncode == 0, green.stdout

    blind = run("<p>no sections here</p>")
    assert blind.returncode == 1, (
        "a document the parser could not read must not exit 0: " + blind.stdout)


# --- the exit contract, and the regression a review caught in it -------------

def test_a_clean_proposal_outline_still_exits_zero(tmp_path):
    """THE PLANTED RED FOR THE FIX, and a real regression this release shipped
    for an hour.

    Making every `not_measured` gate broke `proposal` — the one storyline with
    no `TYPICAL_SECTIONS` row, whose `type completeness` check therefore reports
    `not_measured` on a perfectly good outline. It also overruled this module's
    own refusal, written three times in its docstring: completeness reports and
    never gates, because "structural compliance does not predict quality".

    The measurement that justified the change had only visited the `--against`
    axis. This test is the other one."""
    import pathlib as _pl
    import subprocess
    import sys as _sys
    root = _pl.Path(__file__).resolve().parents[1]
    outline = tmp_path / "p.md"
    outline.write_text(
        "genre: sales\nstoryline: proposal\n\n## Part A · Alpha\n\n"
        "- Alpha beats beta on cost\n"
        "  analysis: compare | finding: alpha beats beta | "
        "implication: buyers save\n"
        "- Gamma holds the line\n"
        "  analysis: position | finding: gamma holds | "
        "implication: the moat is gamma\n", encoding="utf-8")
    proc = subprocess.run(
        [_sys.executable, str(root / "scripts/check/check_outline.py"),
         str(outline)], capture_output=True, text=True, cwd=root)
    assert "not_measured" in proc.stdout or "n/m" in proc.stdout, (
        "this outline must still REACH the completeness check: " + proc.stdout)
    assert proc.returncode == 0, (
        "a clean proposal outline must not fail because one reported check has "
        "no rubric for its storyline: " + proc.stdout)


def test_the_gating_set_is_exactly_the_checks_that_can_fail():
    """The parity guard on `GATING_CHECKS`. A hand-written list of check names
    is the kind of thing that goes stale silently — a new gating check added
    without an entry would gate on FAIL and print a passing exit when it was
    blinded, which is the exact failure the constant exists to prevent. So the
    names are read back out of the module's own source."""
    import pathlib as _pl
    import re as _re
    src = (_pl.Path(__file__).resolve().parents[1]
           / "scripts/check/check_outline.py").read_text(encoding="utf-8")
    # Split on the `"check":` keys and ask whether each record reaches a
    # `"verdict": "FAIL"` before the next one starts. A brace-matching regex
    # does NOT work here: the detail strings are f-strings full of `{}`.
    keys = list(_re.finditer(r'"check":\s*"([^"]+)"', src))
    emits = set()
    for i, m in enumerate(keys):
        end = keys[i + 1].start() if i + 1 < len(keys) else len(src)
        if '"verdict": "FAIL"' in src[m.start():end]:
            emits.add(m.group(1))
    assert emits, "found no FAIL-emitting check at all — the reader is broken"
    assert emits == set(co.GATING_CHECKS), (
        f"only in the source: {emits - set(co.GATING_CHECKS)}; "
        f"only in GATING_CHECKS: {set(co.GATING_CHECKS) - emits}")
