"""The three instruments born from the second blind review (D16), red and green.

Each metric is proven able to FAIL and to pass on synthetic input (a check only
ever seen passing is FM-01), and each red case is the reviewer's own finding in
miniature: an agenda written twice in different words, a page that leaves no
line behind, a figure carrying words but none of the page's numbers, and the
templated parallel frame she called AI at sight.
"""
import check_design
import check_prose


def _deck(agenda_lines, titles, opener=""):
    agenda = ('<section class="page" id="agenda"><p class="eyebrow">Agenda</p>'
              + "".join(f"<li>{ln}</li>" for ln in agenda_lines)
              + "</section>")
    pages = "".join(
        f'<section class="page" id="p{i}"><h2>{t}</h2></section>'
        for i, t in enumerate(titles, start=2))
    return f"<html><body>{agenda}{opener}{pages}</body></html>"


# D27 — the agenda quotes the document, never paraphrases it.

def test_d27_fresh_words_are_orphans():
    r = check_design.d27_agenda_mirror(_deck(
        ["A story the pages never tell"], ["The rules move documents"]))
    assert r["orphans"] == ["A story the pages never tell"]


def test_d27_a_quoted_title_passes_with_punctuation_and_case_blind():
    r = check_design.d27_agenda_mirror(_deck(
        ["The rules move documents!"], ["the rules MOVE documents"]))
    assert r["orphans"] == []


def test_d27_a_line_containing_its_title_passes():
    """An agenda row may add its part letter or a trim without failing."""
    r = check_design.d27_agenda_mirror(_deck(
        ["Part A · The rules move documents"], ["The rules move documents"]))
    assert r["orphans"] == []


def test_d27_reads_openclaim_titles_too():
    opener = ('<section class="page opener" id="openA">'
              '<div class="openclaim">Proof, then a one-week start</div>'
              '</section>')
    r = check_design.d27_agenda_mirror(_deck(
        ["Proof, then a one-week start"], ["Another page"], opener=opener))
    assert r["orphans"] == []


def test_d27_no_agenda_is_none():
    assert check_design.d27_agenda_mirror(
        '<html><body><section class="page" id="p1"><h2>T</h2></section>'
        "</body></html>") is None


# D28 — every external content page leaves one line behind.

def _genre_deck(genre, body):
    return (f'<html><body data-genre="{genre}">'
            f'<section class="page" id="p1"><div class="body">{body}</div>'
            f"</section></body></html>")


def test_d28_missing_takeaway_is_named():
    r = check_design.d28_takeaway(_genre_deck("sales", "prose only"))
    assert r["missing"] == ["p1"]


def test_d28_a_take_block_satisfies_the_page():
    r = check_design.d28_takeaway(
        _genre_deck("sales", '<p class="take">One line to keep.</p>'))
    assert r["missing"] == []


def test_d28_internal_genre_owes_nothing():
    assert check_design.d28_takeaway(_genre_deck("internal", "prose")) is None


# D29 — the page's numbers go into the geometry, not beside it.

def _fig_page(title, svg_text):
    return (f'<html><body><section class="page" id="p1">'
            f"<h2>{title}</h2>"
            f'<div class="fig"><svg><text>{svg_text}</text></svg></div>'
            f"</section></body></html>")


def test_d29_step_indices_do_not_satisfy_a_page_claiming_206():
    """The reviewed staircase in miniature: digits present, values absent."""
    r = check_design.d29_figure_numbers(
        _fig_page("206 shapes, 16 layouts", "1 · brand"))
    assert r["naked"] == ["p1"]


def test_d29_a_stated_value_drawn_in_the_figure_passes():
    r = check_design.d29_figure_numbers(
        _fig_page("206 shapes, 16 layouts", "206 units, tagged"))
    assert r["naked"] == []


def test_d29_a_page_stating_no_numbers_owes_none():
    r = check_design.d29_figure_numbers(_fig_page("The loop", "words only"))
    assert r["naked"] == []


# M14 — the templated parallel frame.

def _roles(*texts):
    return ("<html><body>"
            + "".join(f'<p class="gd">{t}</p>' for t in texts)
            + "</body></html>")


def test_m14_the_reviewed_frame_fires():
    echoes = check_prose.m14_parallel_frames(_roles(
        "Worth your attention if your documents read machine-made.",
        "Worth your attention before you commit anything."))
    assert echoes == [("gd: worth your attention …", 2)]


def test_m14_different_openings_stay_silent():
    assert check_prose.m14_parallel_frames(_roles(
        "Worth your attention if your documents read machine-made.",
        "Every number here is measured on documents.")) == []


def test_m14_roles_do_not_cross():
    """A gd and a sup sharing an opening is not a sibling echo."""
    raw = ('<html><body><p class="gd">Worth your attention if it echoes.</p>'
           '<p class="sup">Worth your attention before it does.</p>'
           "</body></html>")
    assert check_prose.m14_parallel_frames(raw) == []


def test_m14_svg_text_is_figure_ink_and_exempt():
    raw = ("<html><body><svg>"
           '<text class="gd">Worth your attention once.</text>'
           '<text class="gd">Worth your attention twice.</text>'
           "</svg></body></html>")
    assert check_prose.m14_parallel_frames(raw) == []
