#!/bin/bash
# The nightly self-review, as a machine job. Installed by hand into crontab;
# see the INSTALL block at the foot of this file.
#
# WHAT THIS CAN AND CANNOT DO, because the difference matters. It runs the
# mechanical half of `nightly_review.py` and leaves the evidence in a log. It
# CANNOT read a flagged sentence and decide whether the claim is true, fix a
# dangling citation, or judge whether a guard repeats a refusal — those need a
# session. So its job is narrow and honest: every night, put the findings
# somewhere the owner will see them, and say plainly when there are none.
#
# It expires. `EXPIRES` below is three months from installation, at the owner's
# instruction. After that date the job prints why it stopped and does nothing —
# a cron entry that outlives its decision is the same defect as a waiver that
# outlives its reason.

set -uo pipefail

# Derived from this script's own location, never written down: a hard-coded
# path ships a username into a public package, and `local paths` caught
# exactly that on this file's first commit.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG="$REPO/docs/nightly-review.log"      # docs/ is gitignored, so nothing here
                                         # is ever committed by accident
EXPIRES="2026-12-01"

TODAY="$(date +%Y-%m-%d)"
mkdir -p "$(dirname "$LOG")"

{
  echo "════════════════════════════════════════════════════════════"
  echo "nightly review · $(date '+%Y-%m-%d %H:%M')"
} >> "$LOG"

if [[ "$TODAY" > "$EXPIRES" ]]; then
  {
    echo "STOPPED. This job was installed for three months and expired on"
    echo "$EXPIRES. Nothing was checked tonight. Remove it with"
    echo "  crontab -l | grep -v nightly_cron | crontab -"
    echo "or extend EXPIRES in scripts/ops/nightly_cron.sh — a deliberate"
    echo "decision either way, which is the point of it expiring."
  } >> "$LOG"
  exit 0
fi

cd "$REPO" || { echo "the repository is not at $REPO — nothing was checked, "\
"which is not the same as nothing being wrong" >> "$LOG"; exit 1; }

OUT="$(/usr/bin/python3 scripts/ops/nightly_review.py 2>&1)"
RC=$?
echo "$OUT" >> "$LOG"

if [[ $RC -ne 0 ]]; then
  echo "the review itself failed (exit $RC) — this is a failed check, not a "\
"clean one" >> "$LOG"
  exit 0
fi

# The one line a person reads. Anything below "none" in a section is a finding
# that needs a session; say how many rather than leaving the log to be scrolled.
FINDINGS="$(echo "$OUT" | grep -cE '^  (\S+\.(md|py|json|sh):[0-9]+|0\.1\.[0-9]+ )')"
# THREE answers, not two. "nothing shipped" and "nothing wrong" are different
# facts, and the first version of this script printed the same line for both —
# the exact defect the review it runs exists to find.
if echo "$OUT" | grep -q "nothing shipped"; then
  echo "→ nothing shipped today, so nothing was reviewed. That is not a clean "\
"bill." >> "$LOG"
elif [[ "$FINDINGS" -gt 0 ]]; then
  echo "→ $FINDINGS line(s) need a person. Open a session and run:" >> "$LOG"
  echo "    python3 scripts/ops/nightly_review.py" >> "$LOG"
else
  echo "→ work shipped and nothing was flagged." >> "$LOG"
fi

# ── INSTALL ─────────────────────────────────────────────────────────────────
#   R=~/path/to/lumi-style; (crontab -l 2>/dev/null; \
#     echo "53 21 * * * $R/scripts/ops/nightly_cron.sh") | crontab -
#   (cron does not expand a tilde, so let the shell expand $R as you type it)
# REMOVE
#   crontab -l | grep -v nightly_cron | crontab -
# READ
#   tail -40 ~/path/to/lumi-style/docs/nightly-review.log
