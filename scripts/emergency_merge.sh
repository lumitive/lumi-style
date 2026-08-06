#!/bin/bash
# Emergency manual merge for when GitHub Actions cannot run the required check.
#
# Branch protection on main requires the "checks" status and enforces it for
# admins too, so nobody can merge while Actions is down. This opens that lock for
# the duration of one merge and closes it again — including on failure, Ctrl-C, or
# any error, via the EXIT trap. It is deliberately noisy: an emergency path that
# runs quietly is one that gets used casually.
#
#   Usage:  bash scripts/emergency_merge.sh <PR-NUMBER>
#   Example: bash scripts/emergency_merge.sh 8
#
# Before opening the lock it runs the very check Actions would have run, against
# the PR's merge-ready tree. If that check fails, nothing is unlocked and nothing
# is merged.

set -uo pipefail

REPO=lumitive/lumi-style
PR="${1:?usage: bash scripts/emergency_merge.sh <PR-NUMBER>}"
PROT="repos/$REPO/branches/main/protection/enforce_admins"
UNLOCKED=0

relock() {
  if [ "$UNLOCKED" -eq 1 ]; then
    echo
    echo "==> Restoring enforce_admins"
    if gh api --method POST "$PROT" --jq '.enabled' >/dev/null 2>&1; then
      STATE=$(gh api "$PROT" --jq '.enabled')
      echo "    enforce_admins = $STATE"
      [ "$STATE" = "true" ] || echo "    !! STILL OFF — re-enable it by hand, now."
    else
      echo "    !! FAILED to restore. Run this immediately:"
      echo "       gh api --method POST $PROT"
    fi
  fi
}
trap relock EXIT INT TERM

echo "==> PR #$PR: state and conflicts"
gh pr view "$PR" --repo "$REPO" --json state,mergeable,mergeStateStatus,title \
  --jq '"    \(.title)\n    state=\(.state) mergeable=\(.mergeable) mergeState=\(.mergeStateStatus)"'

MERGEABLE=$(gh pr view "$PR" --repo "$REPO" --json mergeable --jq '.mergeable')
if [ "$MERGEABLE" != "MERGEABLE" ]; then
  echo "!! Not mergeable ($MERGEABLE) — resolve conflicts first. Nothing changed."
  exit 1
fi

echo
echo "==> Running the required check locally against the PR head"
WORK=$(mktemp -d)
HEAD_REF=$(gh pr view "$PR" --repo "$REPO" --json headRefName --jq '.headRefName')
if ! git clone --quiet --branch "$HEAD_REF" --depth 1 \
       "https://github.com/$REPO.git" "$WORK/repo" 2>/dev/null; then
  echo "!! Could not clone $HEAD_REF. Nothing changed."
  rm -rf "$WORK"; exit 1
fi
if ! python3 "$WORK/repo/scripts/check_repo.py"; then
  echo
  echo "!! The required check FAILS on this branch. Not unlocking, not merging."
  echo "   This is a real defect, not the Actions outage. Fix it and re-run."
  rm -rf "$WORK"; exit 2
fi
rm -rf "$WORK"
echo "    all checks pass — this is what CI would have reported"

echo
echo "==> Opening the lock (enforce_admins off)"
gh api --method DELETE "$PROT" >/dev/null 2>&1
UNLOCKED=1
echo "    enforce_admins = $(gh api "$PROT" --jq '.enabled')"

echo
echo "==> Merging PR #$PR"
if gh pr merge "$PR" --repo "$REPO" --rebase --admin --delete-branch; then
  echo "    merged"
  MERGED=0
else
  echo "!! Merge failed — protection will still be restored by the trap."
  MERGED=1
fi

# relock() runs here via the EXIT trap, before the final report below.
trap - EXIT INT TERM
relock

echo
echo "==> Final state"
gh api "repos/$REPO/branches/main/protection" --jq \
  '"    enforce_admins=\(.enforce_admins.enabled) required=\(.required_status_checks.checks[].context) linear=\(.required_linear_history.enabled)"'
gh pr view "$PR" --repo "$REPO" --json state --jq '"    PR #'"$PR"' state=\(.state)"'
exit "${MERGED:-0}"
