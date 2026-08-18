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
import re

import check_design
import new_deck
import pytest


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


def test_the_card_names_every_provenance_word_d6_accepts():
    html = scaffold("--genre", "sales")
    for word in check_design.D6_PROVENANCE:
        assert word in html


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
