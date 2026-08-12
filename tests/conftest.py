# scripts/ is deliberately not a package (the scripts are operator commands,
# not a library), so tests import them by bare name with every drawer on
# sys.path — mirroring the canonical bootstrap block the scripts themselves
# carry (check_repo's bootstrap guard enforces it there).
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
for _sub in ("", "lib", "render", "check", "build", "ops"):
    sys.path.insert(0, str(_SCRIPTS / _sub) if _sub else str(_SCRIPTS))
