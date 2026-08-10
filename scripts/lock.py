#!/usr/bin/env python3
"""The brand lock: hashes for files that may not change unnoticed.

    python3 scripts/lock.py                      # report
    python3 scripts/lock.py --update "<why>"     # re-lock at current contents

`assets/brand/LOCKED.json` names a component, the version it was locked at, an
owner, and a SHA-256 per file. `check_repo.py` reads it and fails when a hash
does not match — so CI blocks the merge until the same commit records the new
hash and a reason.

WHAT A LOCK IN SOURCE CONTROL CAN HONESTLY PROMISE. Not that a file cannot be
edited: anyone with a checkout can edit anything. What it promises is that an
edit cannot arrive SILENTLY — that changing a published company mark is a
deliberate act with a sentence attached, rather than a diff nobody looked at
twice. That is the whole mechanism, and claiming more of it would be the kind
of security theatre this repository has a rule against.

Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCK = ROOT / "assets" / "brand" / "LOCKED.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    """-> list of human-readable failures. Empty means every hash matches."""
    if not LOCK.exists():
        return [f"{LOCK.relative_to(ROOT)} is missing; the brand lock is the "
                f"only thing standing between a published mark and a silent "
                f"edit"]
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    out = []
    for rel, want in sorted(lock["files"].items()):
        path = ROOT / rel
        if not path.exists():
            out.append(f"{rel} is LOCKED ({lock['component']}, since "
                       f"{lock['locked_at']}) and has been deleted")
            continue
        got = digest(path)
        if got != want:
            out.append(
                f"{rel} is LOCKED ({lock['component']}, since "
                f"{lock['locked_at']}) and its contents changed.\n"
                f"        locked  {want[:16]}…\n"
                f"        now     {got[:16]}…\n"
                f"        {lock['why']}\n"
                f"        Record the new hash and a reason in the SAME commit: "
                f"python3 scripts/lock.py --update \"<why>\" — or revert.")
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--update", metavar="WHY", default=None,
                    help="re-lock every file at its current contents, and "
                         "record WHY. The reason is kept in the lock file: the "
                         "next reader gets what was decided, not a guess.")
    args = ap.parse_args(argv)

    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if args.update:
        if not args.update.strip():
            raise SystemExit("FAIL  --update needs a reason; a lock changed "
                             "for no stated reason is a lock nobody can review")
        lock["why"] = args.update.strip()
        lock["files"] = {rel: digest(ROOT / rel) for rel in sorted(lock["files"])}
        LOCK.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"re-locked {len(lock['files'])} files: {lock['why']}")
        return 0

    bad = verify()
    for b in bad:
        print(f"FAIL  {b}")
    if not bad:
        print(f"ok    {len(lock['files'])} files locked "
              f"({lock['component']}, since {lock['locked_at']})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
