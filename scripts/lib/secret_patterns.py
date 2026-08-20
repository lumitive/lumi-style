"""The one table of credential shapes, shared by the repo guard and the
deliverable checker.

Until 0.1.525 there were two: `check_repo.SECRET_PATTERNS` (five shapes) and
`check_privacy.CREDENTIALS` (eight), written four months apart, neither a
superset of the other. A `github_pat_` token in a deliverable was caught by the
repo guard and missed by the deliverable checker; a Slack or Google key in a
tracked file was the other way round. The refactor design had forbidden this
by name ("reuse rather than rebuild, so that two pattern tables cannot
drift") and the 2026-08-20 audit found both tables anyway. So: one table, two
importers, and a `secret patterns parity` guard that refuses a private
credential regex anywhere else under scripts/.

Shapes, not entropy: a high-entropy string is often a hash of something
public, and guessing costs an author a real deletion. Each pattern names a
format whose presence has no innocent reading, and each is written so that it
cannot match its own source here.
"""
from __future__ import annotations

import re

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."
                                  r"[A-Za-z0-9_-]{10,}\b")),
    ("credentials in a URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@")),
    # The assignment shape is the union of both old tables: the repo guard
    # knew `api_key`/`secret_key` with a quoted 20+ value; the deliverable
    # checker knew `password`/`token` with an unquoted 12+ value.
    ("assignment of a secret", re.compile(
        r"\b(?:api[_-]?key|secret(?:[_-]?key)?|password|passwd|token)\b\s*[:=]\s*"
        r"[\"']?[A-Za-z0-9_\-/+]{12,}", re.I)),
)

# Fragments that identify a credential regex, spelled so this file's own
# patterns are the only place they appear whole. The parity guard looks for
# them inside any other `re.compile(` under scripts/.
MARKERS: tuple[str, ...] = tuple("".join(p) for p in (
    ("AK", "IA"), ("gh", "[pousr]_"), ("ghp", "_"), ("github", "_pat_"),
    ("xox", "[abprs]"), ("AI", "za["), ("ey", "J["), ("PRIVATE", " KEY"),
))
