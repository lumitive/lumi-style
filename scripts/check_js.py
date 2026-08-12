#!/usr/bin/env python3
"""Syntax-check every JavaScript surface this repository ships.

    python3 scripts/check_js.py

Two surfaces, one blind spot this closes. The tracked `.js` files under
`assets/` are the runtimes deliverables inline; the three probe strings inside
`scripts/inspect_layout.py` are JavaScript that executes in a browser but lives
as Python string literals, where `py_compile` sees prose. Until 0.1.416 neither
surface had any syntax check at all — 0.1.414's lesson ("the guard shipped in
Python, the runtime is JavaScript") happened in exactly this gap.

The check is `node --check` with `--input-type=module`, source on stdin, so it
needs no package.json and no toolchain — a bare `node` binary is enough. The
embedded probes stay embedded (extracting them would change inspect_layout's
single-file operator story for zero added checking power); they are arrow
function expressions, so each is wrapped in parentheses to make it a complete
program before parsing.

A missing `node` is a FAILURE, not a skip. A check that quietly skips is the
failure mode this repository keeps rediscovering (0.1.386: "a check that skips
is not a check that passed").
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

def embedded_probes(module):
    """Every module-level string constant named like a probe (PROBE or
    *_PROBE) — DISCOVERED, not hand-listed. The PR #87 review pointed out
    that a hand-maintained three-name tuple here had the exact failure mode
    this release removed from ci.yml: a fourth probe would ship with zero
    syntax checking and a reassuring 'all 3 probes parse' line. Each probe
    is an arrow-function expression; wrapped in parens it parses as a
    complete module.
    """
    return sorted(name for name in dir(module)
                  if (name == "PROBE" or name.endswith("_PROBE"))
                  and isinstance(getattr(module, name), str))


def tracked_js():
    p = subprocess.run(["git", "ls-files", "*.js"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {p.stderr.strip()}")
    return [f for f in p.stdout.splitlines() if f.strip()]


def node_check(source):
    """-> (ok, message) for one JS module source, parsed by `node --check`."""
    p = subprocess.run(["node", "--input-type=module", "--check"],
                       input=source, capture_output=True, text=True)
    if p.returncode == 0:
        return True, ""
    # node's stderr ends with its version banner; the useful line is the
    # SyntaxError (or, failing that, the first non-empty line).
    lines = [ln for ln in p.stderr.strip().splitlines() if ln.strip()]
    err = next((ln for ln in lines if "Error" in ln), lines[0] if lines else
               "syntax error")
    return False, err.strip()


def main():
    if shutil.which("node") is None:
        print("FAIL  node not found — the JavaScript surfaces were NOT checked.")
        print("      Install node (any recent version); this check never skips.")
        return 1

    failures = []

    files = tracked_js()
    if not files:
        failures.append("git ls-files returned no .js files — the repository "
                        "tracks several; the listing itself is broken")
    for rel in files:
        ok, msg = node_check((ROOT / rel).read_text(encoding="utf-8"))
        print(f"{'ok  ' if ok else 'FAIL'}  {rel}")
        if not ok:
            failures.append(f"{rel}: {msg}")

    sys.path.insert(0, str(ROOT / "scripts"))
    import inspect_layout  # noqa: E402 — import after sys.path, deliberately
    probes = embedded_probes(inspect_layout)
    if not probes:
        failures.append("no *_PROBE strings discovered in inspect_layout — "
                        "either the naming convention changed (update the "
                        "discovery) or the probes are gone; both are findings")
    for name in probes:
        ok, msg = node_check(f"({getattr(inspect_layout, name)})")
        print(f"{'ok  ' if ok else 'FAIL'}  inspect_layout.{name} (embedded)")
        if not ok:
            failures.append(f"inspect_layout.{name}: {msg}")

    print()
    if failures:
        print(f"{len(failures)} JavaScript surface(s) failed the syntax check:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"all {len(files)} tracked .js files and "
          f"{len(probes)} discovered probes parse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
