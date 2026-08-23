"""A deliverable's stamp and a recipe's stamp are read by different functions.

0.1.592 widened one shared reader so a build script's own `VERSION = "..."`
line would be seen. `check_deliverable.py` uses that same reader to decide
WHICH GATES BIND, so the widening let a document with no colophon manufacture a
stamp out of a line-initial VERSION in an inline script and exempt itself from
every gate newer than the number it invented. CLAUDE.md: "a document with no
version stamp is held to everything, because an absent stamp must not become an
exemption."
"""
import fingerprint


def test_a_deliverable_stamp_is_the_colophon_only():
    assert fingerprint.version_in("<p>Built with lumi-style 0.1.591</p>") == "0.1.591"


def test_a_script_variable_never_stamps_a_deliverable():
    """The exemption case. This is the one that must stay None."""
    assert fingerprint.version_in('<script>\nVERSION = "9.9.9"\n</script>') is None
    assert fingerprint.version_in('VERSION = "0.1.100"\n') is None


def test_an_unstamped_deliverable_is_none_not_a_guess():
    assert fingerprint.version_in("<p>no stamp here</p>") is None


def test_a_recipe_stamps_itself_in_its_own_source():
    assert fingerprint.recipe_version_in('VERSION = "0.1.591"\nprint(1)\n') == "0.1.591"


def test_a_recipe_colophon_wins_over_its_variable():
    """The colophon is the one that reached a reader."""
    assert fingerprint.recipe_version_in(
        'VERSION = "0.1.500"\nfoot = "lumi-style 0.1.400"\n') == "0.1.400"


def test_an_interpolated_colophon_is_not_a_literal_stamp():
    """The defect that started it: a build script writes
    `f"Built with lumi-style {VERSION}"`, so the colophon pattern finds nothing
    in the source and the recipe read as unstamped."""
    src = 'VERSION = "0.1.591"\nfoot = f"Built with lumi-style {VERSION}"\n'
    assert fingerprint.VERSION_STAMP.search(src) is None
    assert fingerprint.recipe_version_in(src) == "0.1.591"


def test_an_indented_recipe_stamp_is_not_read():
    """Recorded, not fixed: the pattern is anchored at line start, so a stamp
    inside a class or function still reads as unstamped. `unknown` is the
    honest answer for a shape this has not been shown to handle."""
    assert fingerprint.recipe_version_in('class R:\n    VERSION = "0.1.591"\n') is None


def test_an_unstamped_recipe_is_none():
    assert fingerprint.recipe_version_in("print(1)\n") is None
