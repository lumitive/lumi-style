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
# The log IS the deliverable, so a log that cannot be written must not look
# like a night with nothing to say. cron mails stderr to a mailbox nobody
# reads on macOS, so say it there and stop.
mkdir -p "$(dirname "$LOG")" && : >> "$LOG" || {
  echo "nightly_cron: cannot write $LOG — the review was not recorded" >&2
  exit 1
}

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

# The one line a person reads, and it is READ FROM THE REPORT'S OWN STRUCTURE
# rather than grepped out of its prose. The grep version counted 34 lines on a
# real day: 16 of them were "a release happened", which is not a finding, and
# ZERO of them were the four `★ REFUSED PRECEDENT` lines — the single thing
# this apparatus exists for. A summary that cannot see the most severe class
# and inflates itself with the least is worse than no summary.
SUMMARY="$(/usr/bin/python3 scripts/ops/nightly_review.py --json 2>/dev/null \
  | /usr/bin/python3 -c '
import json, sys
try:
    r = json.load(sys.stdin)
except Exception:
    print("ERR 0 0"); raise SystemExit
classes = ("dangling_citations", "coverage_claims", "new_guards")
blind = sum(1 for c in classes if r.get(c) is None)
found = sum(len(r[c] or []) for c in classes if c != "new_guards")
found += sum(1 for g in (r.get("new_guards") or []) if g[2])
print("OK", found, blind)')"
read -r STATUS FINDINGS BLIND <<<"$SUMMARY"

# FOUR answers, because there are four states and the first version had two.
if [[ "$STATUS" != "OK" ]]; then
  echo "→ the report could not be read as JSON. Nothing here is a clean bill." >> "$LOG"
elif [[ "${BLIND:-0}" -gt 0 ]]; then
  echo "→ $BLIND check(s) COULD NOT LOOK. That is not a clean bill; open a "\
"session and run: python3 scripts/ops/nightly_review.py" >> "$LOG"
elif echo "$OUT" | grep -q "nothing shipped"; then
  echo "→ nothing shipped today, so nothing was reviewed. That is not a clean "\
"bill either." >> "$LOG"
elif [[ "${FINDINGS:-0}" -gt 0 ]]; then
  echo "→ $FINDINGS finding(s) need a person. Open a session and run:" >> "$LOG"
  echo "    python3 scripts/ops/nightly_review.py" >> "$LOG"
else
  echo "→ work shipped, every check looked, and nothing was flagged." >> "$LOG"
fi

# ── INSTALL ─────────────────────────────────────────────────────────────────
#   R=~/path/to/lumi-style; (crontab -l 2>/dev/null; \
#     echo "53 21 * * * $R/scripts/ops/nightly_cron.sh") | crontab -
#   (cron does not expand a tilde, so let the shell expand $R as you type it)
# REMOVE
#   crontab -l | grep -v nightly_cron | crontab -
# READ
#   tail -40 ~/path/to/lumi-style/docs/nightly-review.log
