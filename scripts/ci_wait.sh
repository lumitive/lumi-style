#!/bin/bash
# Bounded wait on a PR's required check, with an outage short-circuit.
#
#   bash scripts/ci_wait.sh <PR-NUMBER>
#
# Exit codes:
#   0  check passed
#   1  check failed — a real defect
#   2  GitHub Actions is degraded; did not wait. Local verification reported.
#   3  budget exhausted while Actions was healthy; still pending
#
# Why this exists. Waiting on CI cost most of a working session during the
# 2026-08-06 Actions outage: runs sat queued for six minutes, got cancelled, were
# re-run, and sat queued again, while an open-ended polling loop watched them. The
# three rules below come straight out of that:
#
#   1. Ask the status page BEFORE waiting. One HTTP call answers "is it even worth
#      waiting", and during a declared outage the answer is no. Polling a
#      capacity-constrained service also adds to the load causing the outage.
#   2. Bound the wait. Three checks over four minutes, then stop and report. An
#      unbounded loop converts a service problem into a person problem.
#   3. Separate correctness from the gate. check_repo.py answers "is this change
#      good" locally and immediately; CI is only what unlocks the merge button. On
#      an outage, report the local verdict and hand over the decision rather than
#      blocking on a queue nobody can drain.

set -uo pipefail

REPO=lumitive/lumi-style
PR="${1:?usage: bash scripts/ci_wait.sh <PR-NUMBER>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> GitHub Actions status"
STATUS=$(curl -fsS --max-time 10 https://www.githubstatus.com/api/v2/components.json 2>/dev/null \
  | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print("unknown"); raise SystemExit
for c in d.get("components", []):
    if c.get("name") == "Actions":
        print(c.get("status","unknown")); break
else:
    print("unknown")
' 2>/dev/null || echo "unknown")
echo "    Actions: $STATUS"

if [ "$STATUS" != "operational" ] && [ "$STATUS" != "unknown" ]; then
  echo
  echo "==> Actions is '$STATUS'. Not waiting."
  echo "    Verifying locally instead — this answers whether the change is good,"
  echo "    which is a different question from whether the merge button is unlocked."
  echo
  python3 "$SCRIPT_DIR/check/check_repo.py"
  RC=$?
  echo
  if [ "$RC" -eq 0 ]; then
    echo "    Local checks pass. The change is verified; only the gate is blocked."
    echo "    Options: wait for the incident to clear, or merge through"
    echo "             bash scripts/emergency_merge.sh $PR"
  else
    echo "    Local checks FAIL. Fix these first; the outage is not your problem yet."
  fi
  exit 2
fi

echo
echo "==> Waiting on PR #$PR (bounded: 3 checks over ~4 minutes)"
for delay in 45 90 105; do
  sleep "$delay"
  ROLLUP=$(gh pr view "$PR" --repo "$REPO" --json statusCheckRollup \
    --jq '[.statusCheckRollup[]? | "\(.status)/\(.conclusion)"] | join(",")' 2>/dev/null)
  echo "    $(date +%H:%M:%S)  ${ROLLUP:-<no checks reported>}"
  case "$ROLLUP" in
    *COMPLETED/SUCCESS*)
      echo
      echo "==> Passed. Merge with: gh pr merge $PR --rebase --delete-branch"
      exit 0
      ;;
    *COMPLETED/FAILURE*)
      echo
      echo "==> FAILED. This is a defect, not the queue:"
      gh run list --branch "$(gh pr view "$PR" --repo "$REPO" --json headRefName --jq .headRefName)" \
        --limit 1 --json databaseId --jq '.[0].databaseId' \
        | xargs -I{} gh run view {} --log-failed 2>/dev/null \
        | sed 's/^[^Z]*Z //' | grep -E "^FAIL|^ {6}" | head -8
      exit 1
      ;;
    *COMPLETED/CANCELLED*)
      echo "    cancelled — an infrastructure symptom, not a verdict; re-run once:"
      echo "    gh run rerun \$(gh run list --branch <branch> --limit 1 --json databaseId --jq '.[0].databaseId')"
      exit 3
      ;;
  esac
done

echo
echo "==> Still pending after the budget. Not waiting further."
echo "    Re-run this script later, or check https://www.githubstatus.com"
exit 3
