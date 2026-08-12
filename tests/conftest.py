# scripts/ is deliberately not a package (the scripts are operator commands,
# not a library), so tests import them by bare name with every drawer on
# sys.path. UNLIKE the canonical bootstrap block (which APPENDS so stdlib
# and the caller's environment win), tests insert(0) on purpose: the suite
# must test THIS repo's modules even when site-packages carries a same-named
# package (`lock` is a real pypi name). The threat the append order defends
# against — PR-controlled trees — does not exist in the test environment.
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
for _sub in ("", "lib", "render", "check", "build", "ops"):
    sys.path.insert(0, str(_SCRIPTS / _sub) if _sub else str(_SCRIPTS))
