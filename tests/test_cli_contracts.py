"""Every operator-facing script answers --help with exit 0.

The cheapest possible behavioral floor: an import-time crash, a broken
argparse wiring, or a missing dependency at module scope all surface here
before an operator hits them mid-release. Scripts without argparse are exempt by not being listed —
note that set includes four flag-less operator CLIs (check_repo,
check_js, check_fixtures, embed_font), not only library modules.

**Membership is the IMPORT, not the word.** The rule was "the file contains the
string `argparse`" and it could not tell a script that wires one up from a
library module whose comment mentions the name: 0.1.558 added a note to
`scripts/lib/trace_schema.py` explaining that argparse had rejected a value, and
that sentence conscripted a data module into the CLI list, where it failed for
printing no help it was never meant to print. Convention 15 — the pattern met
material it had not been shown.
"""
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMPORTS_ARGPARSE = re.compile(r"^import argparse\b", re.M)
SCRIPTS = sorted(
    (p.relative_to(ROOT) for p in (ROOT / "scripts").rglob("*.py")
     if "__pycache__" not in p.parts
     and IMPORTS_ARGPARSE.search(p.read_text(encoding="utf-8"))),
    key=str)


def test_the_list_is_not_empty():
    assert len(SCRIPTS) > 15  # a floor, not a target: most scripts are CLIs


@pytest.mark.parametrize("script", SCRIPTS)
def test_help_exits_zero(script):
    p = subprocess.run([sys.executable, str(ROOT / script),
                        "--help"], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, (script, p.stderr[-300:])
    assert p.stdout.strip(), f"{script} --help printed nothing"
