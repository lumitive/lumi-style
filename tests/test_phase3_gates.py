"""The 0.1.549 gates, each shown passing AND failing.

Convention 11: a gate's first proof is that it can go red. Each of these fired
on a real artifact before it was written into a fixture — `opener_subject_mark`'s
repetition arm on this package's own passing deck, `opener_pacing` on a
conformance deck with twelve unbroken content pages, `D35` on one that put a
stat band on its agenda — and the units here pin the behaviour that produced it.
"""
import check_design as cd
import inspect_layout as il

# ── D33: an icon's geometry is a file in the sets this package ships ─────────

SPRITE = ('<svg style="display:none"><symbol id="i-{name}" viewBox="0 0 24 24">'
          '{geo}</symbol></svg>')


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
    assert r["unknown"] == ["not-a-real-icon"]


def test_a_shipped_name_over_a_different_drawing_is_named_as_altered():
    """The harder half to catch by eye: the set's label on somebody's own path."""
    raw = SPRITE.format(name="shield", geo='<path d="M12 2 L4 6 L20 13 Z"/>')
    r = cd.d33_icon_provenance(raw)
    assert r["altered"] == ["shield"] and not r["unknown"]


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
    """Twelve content pages and no seam — the conformance deck the reported
    version printed and did not fail."""
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
