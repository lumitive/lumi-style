"""D6 accepts a declaration and does not accept a coincidence.

The parity guard holds D6's word list against `check_prose`'s and against
`writing-rules.md` §4 rule 6. It says nothing about how those words are
MATCHED, and the two checkers matched them differently: `check_prose` bounds
every non-CJK marker, `check_design` bounded none. So the release that taught
D6 the declaration labels also taught it to pass on `mockup of the layout` and
on 表示意向 — "no offer intended", which is exactly what a closing colophon
says.

The CJK exclusions are a measured list, not a rule. `\\b` never fires between
CJK characters and a general compound-boundary rule is not something this
checker can have, so the three collocations a review found are named and the
list says it is a list.
"""
import check_design


def _hit(text):
    return bool(check_design.D6_PROVENANCE_RE.search(text.lower()))


def test_a_declaration_is_provenance():
    assert _hit("Built with lumi-style · all figures illustrative")
    assert _hit("proposal values throughout; uncalibrated")
    assert _hit("a mock of the final layout")
    assert _hit("示意数据，非实测")


def test_a_source_still_is():
    assert _hit("Source: meter management system")
    assert _hit("sourced from the meter management system")
    assert _hit("every claim traces back to the research report")
    assert _hit("来源：计量系统")


def test_mock_takes_both_boundaries():
    """"mockup" and "mocked up" describe a layout, not a number.

    Named in the release entry as the defect and left open by the first fix,
    which took a leading boundary for every English term. Rule 2's own label
    for this declaration is "mock UI".
    """
    assert _hit("a mock of the final layout")
    assert not _hit("a mockup of the dashboard")
    assert not _hit("deck mocked up by the design team")


def test_a_leading_boundary_without_a_trailing_one():
    """`sourced` must keep matching; `resourced` must stop.

    A trailing boundary would have broken "sourced from" and "sources", which
    is narrowing a checker until correct prose fails it — the direction the
    release this test ships in exists to reverse.
    """
    assert _hit("sourced from X") and _hit("sources: two systems")
    assert not _hit("resourced by the team")


def test_the_chinese_collocations_are_not_declarations():
    """Three ordinary compounds that 示意 rides inside."""
    assert not _hit("本文件不表示意向")
    assert not _hit("各页图表示意图见附录")
    assert not _hit("提示意义重大")


def test_a_colophon_with_no_provenance_at_all_still_fails():
    """The floor: widening the vocabulary may not make D6 unable to fail."""
    assert not _hit("Built with lumi-style 0.1.609.")


def test_every_declaration_label_is_matchable():
    """A label the guard demands and the regex cannot find is a dead entry."""
    for label in check_design.D6_DECLARATION_LABELS:
        assert _hit(f"figures are {label} here"), label


def test_every_both_boundary_term_is_in_the_vocabulary():
    """A term bounded on both sides that D6 does not accept is a dead entry."""
    for term in check_design.D6_BOTH_BOUNDARIES:
        assert term in check_design.D6_PROVENANCE, term


def test_every_cjk_exclusion_names_a_term_in_the_vocabulary():
    for term in check_design.D6_CJK_NOT_PRECEDED_BY:
        assert term in check_design.D6_PROVENANCE, term
