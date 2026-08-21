"""The 0.1.549 gates, each shown passing AND failing.

Convention 11: a gate's first proof is that it can go red. Each of these fired
on a real artifact before it was written into a fixture — `opener_subject_mark`'s
repetition arm on this package's own passing deck, `opener_pacing` on a
conformance deck with ten unbroken content pages, `D35` on one that put a
stat band on its agenda — and the units here pin the behaviour that produced it.
"""
import check_design as cd
import inspect_layout as il

# ── D33: an icon's geometry is a file in the sets this package ships ─────────

# A SYMBOL PLUS THE USE THAT MAKES IT AN ICON. The gate keys on `svg.ic`
# pointing at a symbol, not on the symbol's id, so a definition nobody draws is
# correctly `checked: 0` — the accepted reference defines a library shape and a
# trademark mark that way.
SPRITE = ('<svg style="display:none"><symbol id="i-{name}" viewBox="0 0 24 24">'
          '{geo}</symbol></svg>'
          '<svg class="ic" aria-hidden="true"><use href="#i-{name}"/></svg>')


def _lucide(name):
    f = cd.ROOT / "assets" / "icons" / "lucide" / f"{name}.svg"
    body = f.read_text(encoding="utf-8")
    return body[body.index(">") + 1:body.rindex("</svg>")]


def test_an_icon_lifted_from_the_shipped_set_passes():
    raw = SPRITE.format(name="shield", geo=_lucide("shield"))
    r = cd.d33_icon_provenance(raw)
    assert r["checked"] == 1 and not r["unknown"] and not r["altered"]


def test_an_invented_icon_is_named_as_unknown():
    raw = SPRITE.format(name="not-a-real-icon", geo='<path d="M3 3 L21 21"/>')
    r = cd.d33_icon_provenance(raw)
    assert r["unknown"] == ["i-not-a-real-icon"]


def test_a_shipped_name_over_a_different_drawing_is_named_as_altered():
    """The harder half to catch by eye: the set's label on somebody's own path."""
    raw = SPRITE.format(name="shield", geo='<path d="M12 2 L4 6 L20 13 Z"/>')
    r = cd.d33_icon_provenance(raw)
    assert r["altered"] == ["i-shield"] and not r["unknown"]


def test_geometry_compares_the_drawing_not_the_spelling():
    """Attribute order and whitespace are how a file was written, not what it
    draws. A comparison that failed on those would fail every real document."""
    a = cd._geometry('<path d="M 4 6 L 8 10"/>')
    b = cd._geometry('<path  d="M 4  6 L 8 10"  fill="none"/>')
    assert a == b


# ── D35: the agenda page carries the agenda and nothing else ────────────────

def _agenda(inner):
    return ('<section class="page" id="agenda"><div class="body stack">'
            + inner +
            '</div><div class="foot"><div class="terms"><span class="conf">x'
            '</span></div><span class="site">y</span></div></section>')


LAUNCH = '<div class="fill"><div class="launch"><div class="lrow">a</div></div></div>'


def test_a_launch_sequence_with_its_lede_passes():
    raw = _agenda('<div class="lede"><h2 class="t">T</h2></div>' + LAUNCH)
    assert cd.d35_agenda_exclusive(raw)["strays"] == []


def test_the_footer_is_not_read_as_a_stray():
    """The first version walked past the body's own `</div>` and reported the
    footer's `.terms` and `.site`, failing the accepted reference deck."""
    r = cd.d35_agenda_exclusive(_agenda(LAUNCH))
    assert r["strays"] == []


def test_a_stat_band_on_the_agenda_is_a_stray():
    raw = _agenda(LAUNCH + '<div class="band"><div class="k">9</div></div>')
    assert any("band" in s for s in cd.d35_agenda_exclusive(raw)["strays"])


def test_a_private_stylesheet_on_the_agenda_is_a_stray():
    raw = _agenda('<style>.agenda-grid{display:grid}</style>' + LAUNCH)
    assert any("<style>" in s for s in cd.d35_agenda_exclusive(raw)["strays"])


def test_a_deck_with_no_agenda_owes_nothing_here():
    """A measured absence, the ruling D27 already carries: `deck_structure` is
    what asks whether the page should exist."""
    assert cd.d35_agenda_exclusive('<section class="page" id="p1">x</section>') is None


# ── opener_pacing: the seam rate ────────────────────────────────────────────

def _rows(kinds, declared=False):
    out = []
    for i, k in enumerate(kinds, 1):
        out.append({"id": f"p{i}", "isCover": k == "cover",
                    "isClosing": k == "closing", "isOpener": k == "opener",
                    "partsDeclaredNone": declared})
    return out


def test_a_deck_inside_the_ceiling_passes():
    kinds = ["cover"] + ["c"] * 6 + ["opener"] + ["c"] * 6 + ["closing"]
    assert il._pacing_overrun(_rows(kinds)) == []


def test_a_run_past_the_ceiling_is_a_finding():
    kinds = ["cover"] + ["c"] * 7 + ["opener"] + ["c"] * 3 + ["closing"]
    assert il._pacing_overrun(_rows(kinds)) == [7]


def test_a_deck_with_no_openers_at_all_is_the_case_that_gates():
    """No seam at all — the shape of the conformance deck the reported version
    printed and did not fail. That artifact is twelve PAGES with ten unbroken
    content pages; this fixture uses twelve content pages, which is the same
    finding one page further along."""
    kinds = ["cover"] + ["c"] * 12 + ["closing"]
    assert il._pacing_overrun(_rows(kinds)) == [12]


def test_a_declared_undivided_deck_is_exempt():
    kinds = ["cover"] + ["c"] * 12 + ["closing"]
    assert il._pacing_overrun(_rows(kinds, declared=True)) == []


def test_a_prose_report_has_no_seams_to_rate():
    """No cover, no closing, no opener: not a deck, and the rule is a deck rule.
    Page count is deliberately not the test — two accepted intro decks are as
    long as a report."""
    assert il._pacing_overrun(_rows(["c"] * 12)) == []


def test_the_ceiling_is_the_accepted_reference_not_the_prose_target():
    """Five is the writing target and six is the limit; a ceiling of five would
    fail the deck the owner accepted, which runs 6."""
    assert il.OPENER_RUN_CEILING == 6


# ── opener_subject_mark: one silhouette per part, and never twice ───────────

def _openers(sigs):
    return [{"id": f"open{c}", "openerMark": None if s is None
             else {"sig": s, "filled": 2, "stroked": 0, "img": False}}
            for c, s in zip("ABCDE", sigs)]


def test_three_distinct_marks_pass():
    assert il._openers_repeating_a_mark(_openers(["a", "b", "c"])) == []


def test_a_repeated_mark_names_the_second_opener():
    hits = il._openers_repeating_a_mark(_openers(["a", "b", "a"]))
    assert [r["id"] for r in hits] == ["openC"]


def test_an_opener_with_no_mark_is_not_a_repetition():
    """It is the OTHER arm's finding. Reporting it twice would say a deck has
    two defects where it has one."""
    assert il._openers_repeating_a_mark(_openers(["a", None])) == []


# ── The 0.1.550 review findings, each pinned ────────────────────────────────
#
# Four of these gates were wrong on their first version and a review found all
# four by running them rather than reading them. Convention 15's point exactly:
# reading the code uses the model that produced it.

def test_a_body_it_cannot_read_is_a_finding_not_a_clean_result():
    """The worst outcome for a checker. The first version used a depth counter,
    so an unclosed element made it record NOTHING — and "no children" is
    indistinguishable from "no strays". On a body whose depth happened to return
    to zero at its own closing tag it did worse: it recorded the whole remaining
    content as one child under the FIRST child's class name, swallowing a stat
    band inside what it believed was the lede. Both readings reported `ok`."""
    kids, balanced = cd._direct_children(
        '<div class="a"><span>x</div><div class="band">S</div>')
    assert balanced is False
    raw = _agenda('<div class="lede"><span>t</div>' + LAUNCH
                  + '<div class="band">S</div>')
    assert any("could not be read" in s
               for s in cd.d35_agenda_exclusive(raw)["strays"])


def test_balanced_markup_reads_as_balanced():
    assert cd._direct_children('<div class="a">x</div><div class="b">y</div>')[1]


def test_an_svg_shape_written_without_a_slash_does_not_blind_the_scan():
    """`<circle cx=.. r=..>` is how a hand-written or agent-written deck spells
    it, and HTML has no void list covering SVG. It defeated the counter."""
    raw = _agenda('<div class="lede"><svg><circle cx="1" cy="1" r="1"></svg></div>'
                  '<div class="band">S</div>')
    assert any("band" in s for s in cd.d35_agenda_exclusive(raw)["strays"])


def test_the_page_whose_id_says_agenda_wins_over_an_eyebrow_that_mentions_one():
    """A content page whose eyebrow read "PART A - agenda for the quarter" was
    graded in place of the real agenda, which was then never examined. One word
    in an eyebrow mis-graded two decks in opposite directions."""
    decoy = ('<section class="page" id="p2">'
             '<p class="eyebrow">PART A - agenda for the quarter</p>'
             '<div class="body stack">' + LAUNCH + '</div></section>')
    r = cd.d35_agenda_exclusive(decoy + _agenda(LAUNCH + '<div class="band">S</div>'))
    assert r["found"] == "agenda"
    assert any("band" in s for s in r["strays"])


ICON_USE = '<svg class="ic" aria-hidden="true"><use href="#{ref}"/></svg>'


def _doc(ref, geo):
    return (f'<svg><symbol id="{ref}" viewBox="0 0 24 24">{geo}</symbol></svg>'
            + ICON_USE.format(ref=ref))


def test_an_off_convention_icon_id_is_reported_rather_than_skipped():
    """The first version matched `id="i-[a-z0-9-]+"` and did not COUNT anything
    else, so `#handdrawn` — or `#i-myIcon`, one capital letter — returned `ok` on
    a document whose every icon was drawn by hand. A gate a naming choice walks
    past is not a gate."""
    for ref in ("handdrawn", "i-myIcon"):
        r = cd.d33_icon_provenance(_doc(ref, '<path d="M3 3 L21 21"/>'))
        assert r["unknown"] == [ref], (ref, r)


def test_a_symbol_that_is_not_drawn_as_an_icon_is_left_alone():
    """The accepted reference defines a library shape and a trademark mark, and
    neither is drawn as `.ic`. Demanding every symbol come from the icon sets
    would fail it on markup that is correct."""
    raw = ('<svg><symbol id="shape-p009-arrow-3d-01"><path d="M1 1 L2 2"/></symbol>'
           '<symbol id="Snoo"><path d="M9 9 L8 8"/></symbol></svg>'
           '<svg class="shape"><use href="#shape-p009-arrow-3d-01"/></svg>')
    r = cd.d33_icon_provenance(raw)
    assert r == {"checked": 0, "unknown": [], "altered": []}


def test_a_minified_copy_of_a_shipped_icon_is_not_a_false_red():
    """An SVG minifier strips exactly the separators a raw string compare keys
    on. The docstring claimed this normalisation before the code did it, and the
    test asserted the weaker claim the code actually made."""
    spaced = cd._geometry('<path d="M 4 6 L 8 10"/>')
    assert cd._geometry('<path d="M4 6L8 10"/>') == spaced
    assert cd._geometry('<path d="M4,6L8,10"/>') == spaced
    assert cd._geometry('<path d="M4 6 L8 11"/>') != spaced


# ── D34: the reuse count is what answers the owner's complaint ──────────────

def _content(pid, ref):
    return (f'<section class="page" id="{pid}"><p class="eyebrow">'
            + ICON_USE.format(ref=ref) + f'PART A · {pid}</p></section>')


def test_two_content_pages_sharing_an_eyebrow_icon_are_counted():
    raw = _content("p1", "i-radar") + _content("p2", "i-radar") + _content("p3", "i-scale")
    r = cd.d34_icon_uniqueness(raw)
    assert r["reused"] == {"i-radar": ["p1", "p2"]}
    assert r["distinct"] == 2 and r["pages"] == 3


def test_the_agendas_own_eyebrow_icon_is_out_of_scope():
    """It names the act of routing rather than a subject being argued, and
    counting it made this package's model document report a reuse it should not."""
    raw = _content("agenda", "i-list-checks") + _content("p13", "i-list-checks")
    assert cd.d34_icon_uniqueness(raw)["reused"] == {}


def test_a_hyphenated_class_is_not_mistaken_for_the_eyebrow_or_the_icon():
    """`\\bic\\b` matches `fig-ic` and `\\beyebrow\\b` matches `sub-eyebrow`,
    because a word boundary sits at a hyphen. Three false checker failures in
    this repository have come from exactly that."""
    raw = ('<section class="page" id="p1"><p class="sub-eyebrow">'
           '<svg class="fig-ic"><use href="#i-radar"/></svg>x</p></section>')
    assert cd.d34_icon_uniqueness(raw)["pages"] == 0


# ── The 0.1.550 review remediation ──────────────────────────────────────────
#
# Four independent reviews of 0.1.549 ran the gates rather than reading them and
# found nine ways through. Each is pinned below with the input that walked past.

def test_a_stray_survives_none_of_the_four_ways_it_used_to():
    """A single-level allowlist was walked past four ways, and every one of them
    is what ordinary generated markup looks like."""
    band = '<div class="band"><div class="k">9</div></div>'
    for name, inner in (
        ("an unclassed wrapper", LAUNCH + "<div>" + band + "</div>"),
        ("a class list starting with foot", LAUNCH + '<div class="foot band">x</div>'),
        ("a class list containing an allowed token", LAUNCH + '<div class="band lede">x</div>'),
        ("three levels down", '<div class="fill"><div class="launch">' + band + "</div></div>"),
        ("inside the allowed lede", '<div class="lede">' + band + "</div>" + LAUNCH),
    ):
        strays = cd.d35_agenda_exclusive(_agenda(inner))["strays"]
        assert any("band" in s for s in strays), f"{name} still walks past D35"


def test_the_agenda_is_found_however_it_says_it_is_one():
    """`id="Agenda"` escaped, and so did a Chinese deck — whose agenda then
    scored as "no agenda page", a pass. Worse, `inspect_layout` lowercases the
    id, so the two checkers disagreed about whether the deck had an agenda."""
    band = '<div class="band">x</div>'
    for pid, eyebrow in (("Agenda", ""), ("toc", "议程"), ("toc", "目录"),
                         ("p9", "x" * 130 + " AGENDA")):
        eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
        raw = ('<section class="page" id="' + pid + '">' + eb
               + '<div class="body stack">' + LAUNCH + band + "</div></section>")
        r = cd.d35_agenda_exclusive(raw)
        assert r and any("band" in s for s in r["strays"]), (pid, eyebrow, r)


def test_both_shipped_icon_sets_are_accepted_for_a_name_they_share():
    """32 of koboyo's 36 names also exist in lucide, and the first version kept
    whichever it read first — always lucide's. A document drawing a genuinely
    shipped koboyo silhouette was reported as forging it."""
    import pathlib
    def inner(p):
        t = pathlib.Path(p).read_text(encoding="utf-8")
        return t[t.index(">") + 1:t.rindex("</svg>")]
    use = '<svg class="ic"><use href="#i-shield"/></svg>'
    for setname in ("lucide", "koboyo"):
        raw = ('<svg><symbol id="i-shield">'
               + inner(f"assets/icons/{setname}/shield.svg") + "</symbol></svg>" + use)
        assert cd.d33_icon_provenance(raw)["altered"] == [], setname
    forged = '<svg><symbol id="i-shield"><path d="M1 1 L2 2"/></symbol></svg>' + use
    assert cd.d33_icon_provenance(forged)["altered"] == ["i-shield"]


def test_a_single_quoted_attribute_is_read_like_a_double_quoted_one():
    """Reading only double quotes gave `d='M20 6'` an all-empty geometry, so a
    shipped icon written that way was reported altered AND two different
    single-quoted icons compared equal — the gate failing both ways at once."""
    assert cd._geometry("<path d='M20 6'/>") == cd._geometry('<path d="M20 6"/>')
    assert cd._geometry("<path d='M20 6'/>") != cd._geometry("<path d='M20 7'/>")


def test_a_run_of_content_pages_ends_at_the_closing_page():
    """The accepted reference carries six appendix pages after its closing, and
    they were counted as one unbroken stretch of argument — which is where the
    ceiling of six came from. Its real longest run is five."""
    rows = _rows(["cover"] + ["c"] * 3 + ["opener"] + ["c"] * 3 + ["closing"]
                 + ["c"] * 6)
    assert il._opener_runs(rows) == [0, 3, 3]
    assert il._pacing_overrun(rows) == []


def test_a_declared_apparatus_page_is_a_seam():
    """A glossary is not the argument continuing, and this file already exempts
    apparatus pages from the visual-share target for the same reason."""
    rows = _rows(["cover"] + ["c"] * 4 + ["c"] + ["c"] * 4 + ["closing"])
    rows[5]["isApparatus"] = True
    assert max(il._opener_runs(rows)) == 4


def test_a_declared_pacing_exemption_reads_as_not_applicable_not_as_a_pass():
    """`run_conformance` records which of `ok` and `n/a` a gate returned, so an
    `ok` made one <body> attribute the cheapest way to switch this gate off with
    no trace in the score."""
    rows = _rows(["cover"] + ["c"] * 12 + ["closing"], declared=True)
    assert il._pacing_not_applicable(rows) is True
    assert il._pacing_overrun(rows) == []
    # And a deck that simply passes is NOT reported as exempt.
    fine = _rows(["cover"] + ["c"] * 5 + ["closing"])
    assert il._pacing_not_applicable(fine) is False
