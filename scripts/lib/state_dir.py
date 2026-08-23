"""Where this package writes things that belong to an OPERATOR, not to a repo.

Four stores were resolved against the repository root: the trace store, the
local corpus registry, the price table and the review scores. TWO of them are
gitignored on purpose — the corpus registry and the price table, one machine's
facts with dates on them; the traces and the review scores are tracked, because
a record that is not kept is not a record. What all four share is that they
would have no directory to live in once the skill is installed from a projection
that carries no `evals/traces/` and no `reviews/`. (It does carry `evals/` —
`gates.json` and `thresholds.json` ship.)

The resolution is deliberately NOT a flat default. It prefers the in-repo
directory **when this checkout actually has it**, so a maintainer's existing
data stays exactly where it is and nothing has to be moved; it falls back to
the user state directory everywhere else, which is what an installed skill
sees. `LUMI_STATE` overrides both, and the per-store variables that already
existed (`LUMI_TRACES`) still win over everything.

Nothing here creates a directory. `check_privacy.py`'s `LUMI_TERMS_DIR` is the
precedent, and the 2026-08-09 instruction is explicit: create on an explicit
write, never on import and never on a read.
"""
from __future__ import annotations

import os
import pathlib

# The fallback is not decoration: a synthetic tree built by a guard test has no
# SKILL.md, and a bare `next()` would raise StopIteration from an import. Same
# shape corpus.py already carries, for the same reason.
ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "SKILL.md").exists()),
            pathlib.Path(__file__).resolve().parents[2])


def state_dir() -> pathlib.Path:
    """-> `$LUMI_STATE`, else `$XDG_STATE_HOME/lumi`, else `~/.lumi`."""
    override = os.environ.get("LUMI_STATE")
    if override:
        return pathlib.Path(override)
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return pathlib.Path(xdg) / "lumi"
    return pathlib.Path.home() / ".lumi"


def store(*parts: str, in_repo: tuple[str, ...] = (),
          root: pathlib.Path | None = None) -> pathlib.Path:
    """-> where one store lives.

    `in_repo` names the path this store had inside the repository. When that
    path exists in `root`, it wins — a maintainer's checkout keeps its data
    where the checkout already has it, and no release has to move a file. An
    installed skill has no such path, so the state directory answers.
    """
    if in_repo:
        candidate = (root or ROOT).joinpath(*in_repo)
        if candidate.exists():
            return candidate
    return state_dir().joinpath(*parts)
