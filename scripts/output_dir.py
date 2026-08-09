#!/usr/bin/env python3
"""Resolve the directory a finished deliverable belongs in, per design-rules §7.

The rule is `Documents/LUMI-Style/` under the user's home directory, and the rule
is the authority — it is written as a literal path precisely so that a model with
no filesystem and no tools can still write it down. This script exists for the
one thing prose cannot do: **find the Documents folder on Windows**, where it is
routinely redirected to OneDrive and localized into another language, so
`~/Documents` is a guess rather than an answer. On macOS it is the answer, and on
Linux the XDG user-dirs file is consulted first for the same reason.

    python3 scripts/output_dir.py            # print the path and whether it exists
    python3 scripts/output_dir.py --create   # create it — only with the user's say-so
    python3 scripts/output_dir.py --path     # the bare path, for a shell to consume

**Creating the directory needs the user's authorization** (owner directive,
2026-08-09), which is why `--create` exists and why nothing here makes a folder
without it. A package that silently writes into someone's home directory is one
nobody installs twice.

Exit is non-zero only when the location genuinely cannot be determined — no home
directory, or a Windows shell-folder lookup that fails and leaves no fallback.
It never invents a path and reports success, because a deliverable written to a
guessed location is lost rather than misplaced (the 0.1.350 lesson: a tool that
cannot measure has to say so instead of reassuring).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

# The literal from references/design-rules.md §7, output axis. It is duplicated
# here rather than parsed out of the prose because a checker that reads the rule
# it enforces proves nothing; check_repo.py's output-default guard holds the two
# together instead, and will fail if they ever disagree.
FOLDER = "LUMI-Style"
DOCUMENTS = "Documents"


class Unresolvable(Exception):
    """The Documents folder could not be located. Never silently a guess."""


def _windows_documents() -> pathlib.Path:
    """The real Documents folder, which on Windows is frequently not ~/Documents.

    OneDrive redirection rewrites the shell folder to
    `%USERPROFILE%\\OneDrive\\Documents`, and a localized install names it in the
    user's own language. The registry holds the truth; `USERPROFILE\\Documents` is
    the fallback for the case where the value is missing, which is rare enough
    that guessing there is defensible and guessing before reading is not.
    """
    try:
        import winreg  # noqa: PLC0415 — Windows-only, and importing it elsewhere fails
    except ImportError as exc:                                  # pragma: no cover
        raise Unresolvable("winreg is unavailable on this Python") from exc
    key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            value, _ = winreg.QueryValueEx(handle, "Personal")
        if value:
            return pathlib.Path(os.path.expandvars(value))
    except OSError:
        pass
    profile = os.environ.get("USERPROFILE")
    if not profile:
        raise Unresolvable(
            "the Personal shell folder is unset and USERPROFILE is empty; "
            "name an output directory explicitly")
    return pathlib.Path(profile) / DOCUMENTS


def _xdg_documents(home: pathlib.Path) -> pathlib.Path:
    """XDG_DOCUMENTS_DIR when the desktop declares one, else ~/Documents.

    A localized Linux desktop names the folder in the user's language, so the
    declaration is read before the English default is assumed.
    """
    config = pathlib.Path(os.environ.get("XDG_CONFIG_HOME") or (home / ".config"))
    dirs = config / "user-dirs.dirs"
    try:
        for line in dirs.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line.startswith("XDG_DOCUMENTS_DIR="):
                continue
            raw = line.split("=", 1)[1].strip().strip('"')
            resolved = raw.replace("$HOME", str(home))
            if resolved:
                return pathlib.Path(os.path.expandvars(resolved))
    except OSError:
        pass
    return home / DOCUMENTS


def documents_dir() -> pathlib.Path:
    if sys.platform.startswith("win"):
        return _windows_documents()
    try:
        home = pathlib.Path.home()
    except (RuntimeError, OSError) as exc:
        raise Unresolvable("no home directory for this user") from exc
    if sys.platform == "darwin":
        return home / DOCUMENTS
    return _xdg_documents(home)


def output_dir() -> pathlib.Path:
    return documents_dir() / FOLDER


def main(argv):
    ap = argparse.ArgumentParser(add_help=True,
                                 description=__doc__.split("\n")[0])
    ap.add_argument("--create", action="store_true",
                    help="create the directory; the user has to authorize this, "
                         "so nothing here creates it by default")
    ap.add_argument("--path", action="store_true",
                    help="print only the path, for a shell to consume")
    args = ap.parse_args(argv)

    try:
        target = output_dir()
    except Unresolvable as exc:
        print(f"FAIL  cannot resolve the deliverable directory: {exc}")
        return 1

    if args.create:
        try:
            existed = target.is_dir()
            target.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"FAIL  {target}: {exc}")
            return 1
        print(f"ok    {target} ({'already there' if existed else 'created'})")
        return 0

    if args.path:
        print(target)
        return 0

    print(f"ok    {target}")
    if not target.is_dir():
        print("      does not exist yet — ask the user, then "
              "`python3 scripts/output_dir.py --create`")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
