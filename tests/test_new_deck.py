"""The scaffold is the thing an author starts from, so it gets held to what it
promises: the mark paints, the slots are the ones D14 knows, the standard order
is there, and the arithmetic on the page numbers is right.

Nothing here needs a browser. The mark-paints test is the machine form of the
0.1.442 review's BUG#1 — a cover globe whose eight trade blocs fell back to the
browser default because the palette that binds them was not in the document.
That defect was invisible to every check in this package (none reads rendered
colour) and cost an owner review to find; what makes it catchable is that the
bindings and the variables are both text, in files this repo ships.
"""
import contextlib
import io

# Scaffolds under test open traces into a scratch store, never the tracked
# one (new_deck opens a trace whenever a storyline is given, since 0.1.531).
# An autouse fixture, which now layers on top of conftest's suite-wide
# redirect rather than standing alone. Its original reason — "so the redirect
# cannot leak into test_trace.py's subprocesses" — was answered the other way:
# the leak was not this file's redirect escaping, it was every OTHER file
# having none, so the redirect moved to conftest and test_trace.py follows it.
# This stays because a per-module scratch store keeps these tests independent.
import pathlib  # noqa: E402
import re

import check_design
import new_deck
import pytest

_SCRATCH: list[pathlib.Path] = []


@pytest.fixture(autouse=True)
def _scratch_traces(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMI_TRACES", str(tmp_path))
    _SCRATCH[:] = [tmp_path]
    yield


def scaffold(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            contextlib.suppress(SystemExit):
        new_deck.main(list(argv))
    return out.getvalue()


# The mark paints.

def test_the_embedded_mark_carries_no_style_block():
    # Inline SVG shares the host's style scope: a vendored `:root` would
    # redefine the document's tokens.
    assert "<style" not in new_deck.brand_globe()


def test_every_region_class_the_mark_uses_is_bound_by_the_preamble():
    html = new_deck.preamble("training", "portrait") + new_deck.brand_globe()
    used = set()
    for attr in re.findall(r'class="([^"]*)"', new_deck.brand_globe()):
        classes = attr.split()
        if "rg" in classes:
            used |= {c for c in classes if c.startswith("rg-")}
    assert used, "the field globe carries no region classes at all"
    for cls in sorted(used):
        assert re.search(rf"\.{re.escape(cls)}\b[^{{]*{{[^}}]*fill", html), \
            f"{cls} has no fill binding in what the scaffold ships"
        assert re.search(rf"--{re.escape(cls)}\s*:", html), \
            f"--{cls} is referenced by a binding and defined nowhere"


def test_the_mark_rides_on_both_marked_pages_and_the_runtime_ships():
    html = scaffold("--genre", "internal", "--pages", "2")
    # The bare attribute, not `data-globe-print-lon0` and not the runtime's
    # own `[data-globe]` selector.
    assert len(re.findall(r"data-globe(?![-\]\w])", html)) == 2   # cover, closing
    assert "createGlobe" in html                  # the runtime that turns it


# The slots are the ones D14 knows.

def test_the_scaffold_trips_d14_and_only_on_declared_slots():
    html = scaffold("--genre", "training", "--pages", "2")
    found = check_design.d14_placeholders(html)
    assert found, "a raw scaffold must not pass the finished-document gate"
    filled = html
    for slot in check_design.AUTHOR_FILL:
        filled = filled.replace(slot, "written by the author")
    assert check_design.d14_placeholders(filled) == []


# The standard order, and the arithmetic under it.

def test_training_appends_one_apparatus_page_and_the_numbering_closes():
    html = scaffold("--genre", "training", "--pages", "4", "--parts", "A,B")
    assert html.count('data-role="apparatus"') == 1
    pages = html.count('<section class="page')
    last, total = re.findall(r"<span>(\d+) / (\d+)</span>", html)[-1]
    assert int(last) == int(total) == pages == 4 + 3 + 2 + 1


def test_a_non_training_genre_appends_no_apparatus_page():
    html = scaffold("--genre", "internal", "--pages", "4", "--parts", "A,B")
    assert 'data-role="apparatus"' not in html
    assert html.count('<section class="page') == 4 + 3 + 2


def test_the_display_face_rides_along():
    # Two deliverables in one week shipped with no @font-face and fell back to
    # the system stack, because embedding was a step an author had to remember.
    assert "@font-face" in scaffold("--genre", "internal", "--pages", "1")


@pytest.mark.parametrize("geometry", ("landscape", "portrait"))
def test_the_geometry_is_declared(geometry):
    html = scaffold("--geometry", geometry, "--pages", "1")
    assert f'data-geometry="{geometry}"' in html


# The scaffold reaches the shape library. Three shipped deliverables referenced
# NONE of its 206 units, and the rebuild spec's D1 calls that guaranteed rather
# than accidental: an agent following the entry points had no path to it, and
# `new_deck.py` did not import `embed_shapes` at all.

def test_the_scaffold_references_a_library_shape():
    html = scaffold()
    assert 'href="#shape-' in html


def test_the_sprite_is_built_so_the_reference_resolves():
    """D19 refuses a reference that resolves to nothing, and a scaffold that
    shipped one would hand every author a document already failing a gate."""
    html = scaffold()
    used = set(re.findall(r'href="#(shape-[\w-]+)"', html))
    defined = set(re.findall(r'id="(shape-[\w-]+)"', html))
    assert used and used <= defined


def test_the_use_declares_its_box_because_no_unit_has_a_zero_origin():
    """All 206 units have a non-zero viewBox origin, so a bare <use> renders
    shifted off frame. This is the one mechanic the worked example exists to
    show, and it is the one a reader cannot see is missing."""
    m = re.search(r'<use href="#shape-[\w-]+"[^>]*>', scaffold())
    assert m
    for attr in ("x=", "y=", "width=", "height="):
        assert attr in m.group(0)


def test_shape_labels_use_style_fill_because_the_attribute_loses_to_css():
    assert 'style="fill:' in scaffold()


def test_the_worked_example_s_labels_are_slots_d14_knows():
    """Furniture the placeholder list has not learned is furniture that ships."""
    html = scaffold()
    for slot in ("the step this end names", "and the step it leads to"):
        assert slot in html
        assert slot in check_design.AUTHOR_FILL


# --storyline seeds the agenda as a checklist, and says so when there is none.

def test_a_storyline_with_a_checklist_seeds_the_agenda():
    html = scaffold("--storyline", "gtm")
    assert "target customer" in html and "value proposition" in html


def test_a_storyline_without_a_checklist_says_so_rather_than_seeding_nothing():
    """`proposal` shipped for eight releases looking like a storyline whose
    sections were all present, because absence printed as silence."""
    html = scaffold("--storyline", "proposal")
    assert "no typical-section checklist exists for proposal" in html


def test_the_geometry_choices_are_the_registry_s_compositions():
    import deliverable_registry as reg
    assert reg.COMPOSITIONS == ("landscape", "portrait")
    assert set(reg.STAGE_OF) == set(reg.COMPOSITIONS)


@pytest.mark.parametrize("storyline", ["market-analysis", "gtm", "proposal"])
def test_every_storyline_produces_a_scaffold(storyline):
    assert scaffold("--storyline", storyline).count("<section") > 5


# The genre contract card: constraints an author needs at write time, imported
# from the checkers that enforce them. A card that retyped a value would be the
# twenty-seventh copy-drift fix waiting to happen, so the tests assert IDENTITY
# with the enforcing constants, not resemblance.

def test_the_card_names_every_title_frame_the_checker_counts():
    import check_prose
    html = scaffold("--genre", "sales")
    for frame in check_prose.TITLE_FRAMES:
        assert frame in html


def test_the_card_names_the_english_provenance_words_d6_accepts():
    """The card prints the words an English deliverable can use. It does NOT
    print the Chinese ones: D6 accepts them and the checker holds the list, but
    a card printed into an English document does not need to carry the other
    language's rule data — 0.1.589 shipped eight CJK characters into every
    English deck this way."""
    html = scaffold("--no-trace")
    for word in check_design.D6_PROVENANCE:
        if word.isascii():
            assert word in html, word
        else:
            assert word not in html, f"{word} is rule data, not deck content"


def test_the_card_states_the_dash_policy_for_the_genre():
    import check_prose
    assert "internal" not in check_prose.DASH_BANNED, (
        "the exemption the two cards below assert")
    assert "BANNED" in scaffold("--genre", "sales")
    assert "internal analysis exemption" in scaffold("--genre", "internal")


def test_the_card_does_not_poison_the_scaffold_s_own_gates():
    """The card quotes dash policy and provenance words inside an HTML comment;
    if the prose extractor ever started reading comments, the scaffold would
    fail M9 on its own contract card."""
    import contextlib
    import io
    import json as _json
    import pathlib as _pl
    import tempfile
    html = scaffold("--genre", "sales")
    with tempfile.TemporaryDirectory() as d:
        f = _pl.Path(d) / "s.html"
        f.write_text(html, encoding="utf-8")
        import check_prose
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            check_prose.main([str(f), "--genre", "sales", "--json"])
        r = _json.loads(buf.getvalue())[0]
        assert r["verdicts"]["M9_dashes"] == "ok"
        assert r["verdicts"]["M4_banned_hits"] == "ok"


# 0.1.531 — the scaffold opens the build record and the body carries its id.

def test_a_scaffold_with_a_storyline_opens_a_trace_and_carries_its_id():
    import json
    html = scaffold("--storyline", "gtm", "--pages", "2",
                    "--entry-path", "B")
    m = re.search(r'data-trace="(t-[0-9a-f]{12})"', html)
    assert m, "the body carries no data-trace"
    rec = json.loads((_SCRATCH[0] / f"{m.group(1)}.json").read_text())
    assert rec["entry_path"] == "B" and rec["storyline"] == "gtm"
    assert rec["closed_at"] is None
    clock = _SCRATCH[0] / ".phases" / f"{m.group(1)}.json"
    assert clock.exists() and "build" in json.loads(clock.read_text())


def test_no_storyline_means_no_trace_and_says_so():
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            contextlib.suppress(SystemExit):
        new_deck.main(["--pages", "2"])
    assert "data-trace" not in out.getvalue()
    assert "no trace opened" in err.getvalue()


def test_no_trace_flag_is_honoured():
    html = scaffold("--storyline", "gtm", "--pages", "2", "--no-trace",
                    "--entry-path", "B")
    assert "data-trace" not in html


def test_no_entry_path_means_no_trace_and_says_so():
    """The entry path is declared, never inferred — the same rule as the
    storyline above. Guessing it from the presence of an outline recorded two
    replays of one frozen script as original four-beat builds."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            contextlib.suppress(SystemExit):
        new_deck.main(["--storyline", "gtm", "--pages", "2"])
    assert "data-trace" not in out.getvalue()
    assert "no trace opened" in err.getvalue()
    assert "entry path" in err.getvalue()


# 0.1.533 — the question → framework → shape chain reaches the figure slot.

def test_a_declared_move_puts_the_frameworks_shape_in_the_slot():
    shape, note = new_deck.shape_for("position")
    assert shape and "2x2" in shape and "alternatives" in note


def test_a_named_framework_wins_over_the_moves_first_candidate():
    shape, _ = new_deck.shape_for("decompose", "value-chain")
    assert shape.startswith("p076") or shape.startswith("p077") or shape.startswith("p056")


def test_a_move_no_framework_draws_leaves_the_slot_a_prompt():
    """A move the registry cannot serve leaves the slot empty rather than
    inventing a figure. `correlate` used to be the example — it had no
    framework at all (GAP-032) — which meant this test died the moment the gap
    closed at 0.1.663, and until then a reader could not tell whether it
    asserted the rule or the hole. An unknown move is the honest fixture."""
    assert new_deck.shape_for("triangulate") == ("", "")
    assert new_deck.shape_for("") == ("", "")


def test_every_declared_move_now_arrives_with_guidance():
    """The GENERATION side of GAP-032, which is the half that decides what an
    author actually receives. A `correlate` page used to arrive with an empty
    slot AND an empty note — nothing at all. It now arrives with its framework
    named and its misuse line quoted, even though the library has no scatter to
    embed (AG-10: a shape was bound to satisfy a checker, a review opened the
    SVG, and the binding was withdrawn).

    A shape is asserted where the library HAS one; a note is asserted
    everywhere, because guidance is what the scaffold owes."""
    for move in ("compare", "decompose", "position", "bridge"):
        shape, note = new_deck.shape_for(move)
        assert shape and note, f"{move} arrives with no shape"
    shape, note = new_deck.shape_for("correlate")
    assert shape == "", "the library ships no scatter; see GAP-032"
    assert "scatter" in note and "natively" in note, note


def test_an_outline_with_moves_yields_shape_slots(tmp_path):
    outline = tmp_path / "o.md"
    outline.write_text(
        "# Plan\n\n## Part A\n\n- First title with a 40% fact\n"
        "  analysis: compare | finding: first | implication: one | framework: harvey-scorecard\n"
        "- Second title with 12 items\n"
        "  analysis: decompose | finding: second | implication: two\n",
        encoding="utf-8")
    html = scaffold("--storyline", "gtm", "--pages", "2", "--outline", str(outline),
                    "--no-trace")
    assert html.count('href="#shape-') >= 2
    assert "p156-very-attractiveaveragevery-unattractive-01" in html
    assert 'data-analysis="decompose"' in html


def test_the_field_device_rides_in_the_sample_rotation():
    html = scaffold("--storyline", "gtm", "--pages", "8", "--no-trace")
    assert 'class="field tall"' in html and "per real datum" in html


# --- the page count follows the plan -----------------------------------------
# `--pages` defaulted to 6 whatever the outline said, so a ten-title plan
# silently emitted six content pages and four findings had nowhere to go —
# silently, because the scaffold is valid either way and no check compares a
# scaffold to a plan. Recorded as a build trap after a 2026-08 build had to
# discover it by counting.

_OUTLINE = """A plan with more sections than the old default
genre: internal
storyline: market-analysis

## Part 1 · First
- The first finding says something about its subject
  analysis: compare | finding: f1 | implication: i1
- The second finding says something about its subject
  analysis: decompose | finding: f2 | implication: i2
- The third finding says something about its subject
  analysis: position | finding: f3 | implication: i3

## Part 2 · Second
- The fourth finding says something about its subject
  analysis: bridge | finding: f4 | implication: i4
- The fifth finding says something about its subject
  analysis: correlate | finding: f5 | implication: i5
- The sixth finding says something about its subject
  analysis: compare | finding: f6 | implication: i6
- The seventh finding says something about its subject
  analysis: decompose | finding: f7 | implication: i7
"""


def _content_pages(html):
    return len(re.findall(r'<section class="page"[^>]*id="p\d+"', html))


def test_the_page_count_defaults_to_the_outlines_section_count(tmp_path):
    o = tmp_path / "outline.md"
    o.write_text(_OUTLINE, encoding="utf-8")
    html = scaffold("--no-trace", "--outline", str(o), "--parts", "A,B")
    assert _content_pages(html) == 7, "the plan has seven sections"


def test_an_explicit_pages_still_wins(tmp_path):
    """An author may deliberately scaffold a subset."""
    o = tmp_path / "outline.md"
    o.write_text(_OUTLINE, encoding="utf-8")
    html = scaffold("--no-trace", "--outline", str(o), "--parts", "A,B",
                    "--pages", "4")
    assert _content_pages(html) == 4


def test_with_no_outline_the_default_is_the_owners_ten():
    """The owner's default, 2026-08-23, after three validation rounds. Six was
    this file's own invention and sat BELOW `evals/thresholds.json`'s
    `min_content_pages: 8`, so a default scaffold escaped the corpus ratios and
    M11 reported n/a for want of titles."""
    assert _content_pages(scaffold("--no-trace")) == new_deck.DEFAULT_PAGES == 10


def test_the_default_is_english_and_takes_no_flag():
    """English is the default, so the ordinary build types nothing."""
    html = scaffold("--no-trace")
    assert '<html lang="en"' in html
    assert "data-lang-asked" not in html


def test_another_language_is_authored_directly_and_needs_the_users_words():
    """The user asked, so the deck is written in that language from the start —
    not built in English and translated, which writes the same content twice.
    0.1.587's `--lang-asked` was a BOOLEAN the agent typed on the same command
    line as the language it was attesting to; it carries the words now."""
    with contextlib.redirect_stdout(io.StringIO()), \
            pytest.raises(SystemExit) as exc:
        new_deck.main(["--no-trace", "--lang", "zh-Hans"])
    assert "asked for" in str(exc.value), str(exc.value)

    html = scaffold("--no-trace", "--lang", "zh-Hans",
                    "--lang-asked", "\u7528\u4e2d\u6587\u5199\u8fd9\u4efd\u62a5\u544a")
    assert '<html lang="zh-Hans"' in html
    assert 'data-lang-asked="zh-Hans"' in html
    assert "data-lang-ask-quote=" in html


def test_a_fragment_is_not_a_quotation():
    with contextlib.redirect_stdout(io.StringIO()), \
            pytest.raises(SystemExit) as exc:
        new_deck.main(["--no-trace", "--lang", "ja", "--lang-asked", "ja"])
    assert "fragment" in str(exc.value), str(exc.value)


# --- an omission declared in the outline reaches the page (0.1.604) ---------
# C5 lets a document declare a deliberate gap, and the declaration is a
# reader-visible note carrying `data-omitted`. On entry path B the author
# declares it in the OUTLINE — `check_outline` parses it, reports it, and
# nothing carried it into the document. Measured on the two decks of the
# 2026-08-25 round: the one whose author hand-wrote the attribute passed D31,
# the one who used the outline's own syntax failed it, and the difference was
# not the documents.

OUTLINE = """genre: internal
storyline: market-analysis

## Part A
- A title carrying a fact about 12 markets

omitted: sizing (TAM/SAM/SOM) — the source carries no market sizing
omitted: customer segments — no segmentation data was commissioned
"""


def _with_outline(tmp_path, text=OUTLINE):
    path = tmp_path / "outline.md"
    path.write_text(text, encoding="utf-8")
    return scaffold("--genre", "internal", "--storyline", "market-analysis",
                    "--entry-path", "B", "--pages", "2",
                    "--outline", str(path))


def test_a_declared_omission_reaches_the_reader(tmp_path):
    html = _with_outline(tmp_path)
    assert 'class="scope-note"' in html, "the outline's omissions reached no page"
    assert "the source carries no market sizing" in html, (
        "the author's own reason was replaced by furniture")


def test_the_emitted_declaration_uses_the_checklist_s_own_name(tmp_path):
    """`a in declared` is exact set membership, not a substring test.

    The outline says "sizing (TAM/SAM/SOM)" and "customer segments"; the
    checklist says "sizing" and "segments". Emitting the author's phrasing
    verbatim would produce a note that looks right, reads right, and clears
    nothing — a fix indistinguishable from no fix.
    """
    html = _with_outline(tmp_path)
    scope = check_design.d26_declared_scope(html, "market-analysis")
    assert "sizing" in scope["declared"]
    assert "segments" in scope["declared"]
    assert "sizing" not in scope["missing"]
    assert "segments" not in scope["missing"]
    assert scope["hidden"] == []


def test_an_omission_with_no_reason_is_not_emitted(tmp_path):
    """`check_outline` already reports these; the scaffold must not invent one."""
    html = _with_outline(tmp_path, "genre: internal\nstoryline: market-analysis\n"
                                   "\n## Part A\n- A title with a fact\n"
                                   "\nomitted: sizing\n")
    assert 'data-omitted' not in html


def test_no_outline_emits_no_scope_note(tmp_path):
    """The counter-red: nothing is declared on the author's behalf."""
    html = scaffold("--genre", "internal", "--storyline", "market-analysis",
                    "--entry-path", "B", "--pages", "2")
    assert 'class="scope-note"' not in html


def test_a_named_native_framework_is_answered_with_nothing_not_with_a_sibling():
    """A review found this: naming a natively-drawn framework contributed no
    shapes, so a SIBLING of the same move filled the pool — and the author who
    asked for a benchmark table received Harvey balls, labelled
    `harvey-scorecard`. Answering a request with a different framework is worse
    than answering it with nothing."""
    for native in ("benchmark-table", "radar"):
        shape, note = new_deck.shape_for("compare", native)
        assert shape == "", f"{native} handed back {shape!r}"
        assert native in note and "natively" in note, note
    shape, note = new_deck.shape_for("bridge", "waterfall")
    assert shape == "" and "waterfall" in note, (shape, note)


def test_a_named_shape_bearing_framework_still_resolves():
    """The boundary: honouring the name must not stop it working."""
    shape, note = new_deck.shape_for("compare", "harvey-scorecard")
    assert shape.startswith("p156") and "harvey-scorecard" in note
