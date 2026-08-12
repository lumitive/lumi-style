"""Every operator-facing script answers --help with exit 0.

The cheapest possible behavioral floor: an import-time crash, a broken
argparse wiring, or a missing dependency at module scope all surface here
before an operator hits them mid-release. Scripts without argparse are exempt by not being listed —
note that set includes four flag-less operator CLIs (check_repo,
check_js, check_fixtures, embed_font), not only library modules.
"""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = sorted(
    p.name for p in (ROOT / "scripts").glob("*.py")
    if "argparse" in p.read_text(encoding="utf-8"))


def test_the_list_is_not_empty():
    assert len(SCRIPTS) > 15  # a floor, not a target: most scripts are CLIs


@pytest.mark.parametrize("script", SCRIPTS)
def test_help_exits_zero(script):
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / script),
                        "--help"], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, (script, p.stderr[-300:])
    assert p.stdout.strip(), f"{script} --help printed nothing"
