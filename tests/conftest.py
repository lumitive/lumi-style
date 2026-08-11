# scripts/ is deliberately not a package (the scripts are operator commands,
# not a library), so tests import them the same way check_repo.py:1532 imports
# lock.py: by putting scripts/ on sys.path. This is the one place that happens
# for tests.
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
