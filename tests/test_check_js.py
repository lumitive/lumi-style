"""check_js unit halves: node parsing and probe discovery.

The node tests skip ONLY when node is absent (it is present in CI, which
installs it via setup-node); discovery needs no node at all.
"""
import shutil
import types

import check_js
import pytest

needs_node = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node is not installed")


@needs_node
def test_node_check_rejects_a_syntax_error():
    ok, msg = check_js.node_check("const x = (")
    assert ok is False
    assert "Error" in msg


@needs_node
def test_node_check_accepts_a_wrapped_arrow_probe():
    # the shape main() feeds it: an arrow-function expression in parens
    ok, msg = check_js.node_check("(() => { const a = document; return a; })")
    assert ok is True
    assert msg == ""


def test_embedded_probes_discovers_exactly_the_string_probes():
    module = types.SimpleNamespace(
        PROBE="() => 1",
        EXTRA_PROBE="() => 2",
        SIZE_PROBE=7,             # probe-named but not a string: excluded
        NOT_A_PROBE_int=3,        # neither name shape nor string: excluded
        OTHER="a string without the probe name: excluded",
    )
    assert check_js.embedded_probes(module) == ["EXTRA_PROBE", "PROBE"]
