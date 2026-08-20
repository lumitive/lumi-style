"""The local corpus registry — one reader for evals/corpus.local.json.

The file is gitignored (a path to a real deliverable is an engagement fact,
red line 9) and its absence is a normal state on any machine but the
operator's. Three scripts read it and each parsed it its own way until
0.1.534, when a value stopped being a bare path: an entry may now be
`{path, archived}` so a document that was scored and then deleted is a
recorded loss rather than a dangling id.
"""
from __future__ import annotations

import json
import pathlib

# The repo root by its SKILL.md; in a synthetic tree under test (no SKILL.md)
# the drawer layout still locates the tree two levels up from scripts/lib.
ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "SKILL.md").exists()),
            pathlib.Path(__file__).resolve().parents[2])
LOCAL_CORPUS = ROOT / "evals" / "corpus.local.json"


def entry(value) -> tuple[str | None, dict | None]:
    """-> (path, archived) from one registry value: a path string, or an
    object {path?, archived?}."""
    if isinstance(value, str):
        return value, None
    if isinstance(value, dict):
        return value.get("path"), value.get("archived")
    return None, None


def load() -> dict[str, tuple[str | None, dict | None]] | None:
    """-> {corpus id: (path, archived)}, or None when the file is absent —
    the caller says the lookup was impossible rather than reading an empty
    corpus."""
    if not LOCAL_CORPUS.exists():
        return None
    raw = json.loads(LOCAL_CORPUS.read_text(encoding="utf-8"))
    return {k: entry(v) for k, v in raw.items()}


def paths() -> dict[str, pathlib.Path]:
    """-> {corpus id: expanded path} for entries that name a path (an
    archived entry with no path is not here)."""
    loaded = load() or {}
    return {k: pathlib.Path(p).expanduser() for k, (p, _a) in loaded.items() if p}
