"""What the figure probe counts as a VALUE, in both directions.

`figure_axis_named` gates a figure that "puts numbers on a scale and names no
axis". Whether a drawing does that is decided by one regex over its `<text>`
nodes, and the regex allowed any three characters before the first digit — so
`AP2`, `x402`, `R1`, `Q3`, `H100` and `v1.2` all read as values, and two of them
in one drawing made a 2x2 of quadrant tags "a figure that scales numbers".

Both builds of the 2026-08-25 validation round then EDITED THEIR DOCUMENTS to
silence it: one added axis names to 2x2s that have no scale, the other merged a
figure's labels into a single `<text>` so its `textContent` ran past the
fourteen-character ceiling. That is FM-13 — a false positive that edits the
deliverable is worse than a miss, because nothing downstream records that it
happened.

This test runs the predicate itself rather than a copy of it: the regex is read
out of the probe source the way `check_repo`'s vocabulary guards read theirs, so
a rename or a rewrite fails here rather than silently checking nothing. It needs
node, not a browser, which is why it can run in CI while the rendered checks
cannot.
"""
import json
import shutil
import subprocess

import check_repo
import pytest

needs_node = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node is not installed")

# A value is a quantity: digits, optionally signed, with a unit or a currency.
COUNTS = ["62%", "28%", "96.2%", "71.4%", "41", "1,240", "12.5%", "3.5x",
          "US$4.2m", "41％", "4.2亿", "±1%", "$18", "0.85¢"]
# A name that contains a digit is not a value. Every one of these appeared in a
# real drawing: the protocol names and the risk ids come from the two decks
# built on 2026-08-25, the rest are the same shape. What they share is a LETTER
# in front of the digits.
#
# A digit-LED name — `5G`, `4K`, a bare `2024` — is deliberately absent, and
# not because it is unimportant: it is the same shape as `3.5x` and `4.2m`, so
# no pattern can separate the two and a fix would have to guess. That is a
# KNOWN_GAPS entry with the measurement that would settle it, not a row here
# quietly asserting something this release did not do.
DOES_NOT_COUNT = ["AP2", "x402", "R1", "R5", "P0", "P1", "Q3", "S3", "H100",
                  "v1.2", "T+1", "ADR-020", "ERC-8004", "Tier 2",
                  "Stage 3", "GPT-4", "Phase 2", "node-7"]


def _predicate():
    """-> the probe's own value test, as JavaScript."""
    probes = check_repo._probe_sources()
    return check_repo._js_const(probes["PROBE"], "VALUE_TEXT")


@needs_node
def test_the_probe_counts_quantities_and_not_names():
    """The table is the contract, and it is read from the probe, not retyped."""
    script = (f"const VALUE_TEXT ={_predicate()};\n"
              "const table = JSON.parse(process.argv[1]);\n"
              "const hit = v => v.length <= 14 && /\\d/.test(v)"
              " && VALUE_TEXT.test(v);\n"
              "console.log(JSON.stringify(table.map(hit)));\n")
    def run(words):
        out = subprocess.run(["node", "-e", script, json.dumps(words)],
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)

    counted = run(COUNTS)
    missed = [w for w, ok in zip(COUNTS, counted) if not ok]
    assert not missed, f"a quantity the probe stopped counting: {missed}"

    named = run(DOES_NOT_COUNT)
    wrong = [w for w, ok in zip(DOES_NOT_COUNT, named) if ok]
    assert not wrong, (f"a name with a digit in it counted as a value on a "
                       f"scale: {wrong}")


def test_the_predicate_is_named_in_the_probe():
    """Without a name there is nothing for the test above to read, and the
    check would quietly become a test of its own copy."""
    assert "\\d" in _predicate()
