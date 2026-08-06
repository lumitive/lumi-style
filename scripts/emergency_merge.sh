#!/bin/bash
# Emergency manual merge for when GitHub Actions cannot run the required check.
#
# Branch protection on main requires the "checks" status and enforces it for
# admins too, so nobody can merge while Actions is down. This opens that lock for
# one merge and closes it again — including on failure, Ctrl-C, or any error, via
# the EXIT trap.
#
#   Usage:  bash scripts/emergency_merge.sh <PR-NUMBER>
#
# Threat model. This runs on a maintainer's machine with live gh credentials, on
# a PUBLIC repo where anyone may open a pull request. Three rules follow:
#
#   1. Never execute code that came from the pull request. An earlier version of
#      this script cloned the PR branch and ran *its* copy of check_repo.py —
#      arbitrary code execution for any fork contributor. The checker is now
#      always the trusted local copy, overwritten on top of the fetched tree;
#      only the data being checked comes from the PR.
#   2. Fork PRs are refused outright. A same-repo branch means someone with push
#      access created it; a fork branch means anyone did.
#   3. Verify what will actually be merged, not what the branch tip happens to
#      be. We fetch refs/pull/N/merge (the merge result) and pin the head SHA so
#      a push landing mid-run aborts the merge instead of sneaking in.

set -uo pipefail

REPO=lumitive/lumi-style
PR="${1:?usage: bash scripts/emergency_merge.sh <PR-NUMBER>}"
PROT="repos/$REPO/branches/main/protection/enforce_admins"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRUSTED_CHECK="$SCRIPT_DIR/check_repo.py"
UNLOCKED=0
WORK=""

cleanup() {
  [ -n "$WORK" ] && rm -rf "$WORK"
  if [ "$UNLOCKED" -eq 1 ]; then
    echo
    echo "==> Restoring enforce_admins"
    for attempt in 1 2 3; do
      if gh api --method POST "$PROT" >/dev/null 2>&1; then break; fi
      echo "    retry $attempt failed"
      sleep 3
    done
    STATE=$(gh api "$PROT" --jq '.enabled' 2>/dev/null || echo "unknown")
    echo "    enforce_admins = $STATE"
    if [ "$STATE" != "true" ]; then
      echo "    !! PROTECTION IS STILL OFF. Run this now:"
      echo "       gh api --method POST $PROT"
    fi
  fi
}
trap cleanup EXIT INT TERM

[ -f "$TRUSTED_CHECK" ] || { echo "!! $TRUSTED_CHECK not found."; exit 1; }

echo "==> PR #$PR"
# One call, tab-separated, read straight into shell vars. Every guard below is
# fail-closed: an empty or unexpected value takes the refusing branch.
IFS=$'\t' read -r TITLE STATE MERGEABLE FORK HEAD_SHA HEAD_REF < <(
  gh pr view "$PR" --repo "$REPO" \
    --json title,state,mergeable,isCrossRepository,headRefOid,headRefName \
    --jq '[.title, .state, .mergeable, (.isCrossRepository|tostring),
           .headRefOid, .headRefName] | @tsv'
) || true

echo "    ${TITLE:-<no title>}"
echo "    state=${STATE:-?} mergeable=${MERGEABLE:-?} fork=${FORK:-?} head=${HEAD_REF:-?}@${HEAD_SHA:0:7}"

if [ "${FORK:-true}" != "false" ]; then
  echo "!! This PR comes from a fork (or its origin could not be determined). Refusing."
  echo "   Merging it would mean trusting a tree anyone could have authored, with no"
  echo "   CI having run on it. Wait for Actions, or review and merge it by hand."
  exit 1
fi
if [ "${STATE:-}" != "OPEN" ]; then
  echo "!! PR state is ${STATE:-unknown}, not OPEN. Nothing changed."
  exit 1
fi
if [ "${MERGEABLE:-}" != "MERGEABLE" ]; then
  echo "!! Not mergeable (${MERGEABLE:-unknown}). Nothing changed."
  exit 1
fi
if ! [[ "${HEAD_SHA:-}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "!! Could not read a valid head SHA. Refusing: without it the merge cannot"
  echo "   be pinned, and a push landing mid-run would slip in unchecked."
  exit 1
fi

echo
echo "==> Fetching the merge result (refs/pull/$PR/merge), not the branch tip"
WORK=$(mktemp -d)
git init --quiet "$WORK/repo" || { echo "!! git init failed"; exit 1; }
if ! git -C "$WORK/repo" fetch --quiet --depth 1 \
       "https://github.com/$REPO.git" "refs/pull/$PR/merge" 2>/dev/null; then
  echo "!! Could not fetch refs/pull/$PR/merge. GitHub may not have computed it"
  echo "   yet, or the PR is not mergeable. Nothing changed."
  exit 1
fi
git -C "$WORK/repo" checkout --quiet FETCH_HEAD || { echo "!! checkout failed"; exit 1; }

echo "==> Running the TRUSTED local checker over that tree"
mkdir -p "$WORK/repo/scripts"
cp "$TRUSTED_CHECK" "$WORK/repo/scripts/check_repo.py"   # never run the PR's copy
if ! python3 "$WORK/repo/scripts/check_repo.py"; then
  echo
  echo "!! The required check FAILS on the merge result. Not unlocking, not merging."
  echo "   This is a real defect, not the Actions outage. Fix it and re-run."
  exit 2
fi
echo "    all checks pass on the exact tree that merging would produce"

echo
echo "==> Opening the lock (enforce_admins off)"
# Arm the restore BEFORE the call. If the request reaches GitHub but the response
# is lost, the lock is open and we would otherwise never put it back — an extra
# restore is free, a missed one leaves main unprotected.
UNLOCKED=1
if ! gh api --method DELETE "$PROT" >/dev/null 2>&1; then
  echo "!! Could not disable enforce_admins. Nothing merged; trap will re-assert it."
  exit 1
fi
if [ "$(gh api "$PROT" --jq '.enabled' 2>/dev/null)" != "false" ]; then
  echo "!! enforce_admins did not actually turn off. Aborting; trap will restore."
  exit 1
fi
echo "    enforce_admins = false"

echo
echo "==> Merging PR #$PR (pinned to ${HEAD_SHA:0:7})"
MERGED=1
if gh pr merge "$PR" --repo "$REPO" --rebase --delete-branch --admin \
     --match-head-commit "$HEAD_SHA"; then
  echo "    merged"
  MERGED=0
else
  echo "!! Merge failed or was refused (a mid-run push to the branch will do this)."
  echo "   Protection is restored by the trap regardless."
fi

trap - EXIT INT TERM
cleanup

echo
echo "==> Final state"
gh api "repos/$REPO/branches/main/protection" --jq \
  '"    enforce_admins=\(.enforce_admins.enabled) required=\(.required_status_checks.checks[].context) linear=\(.required_linear_history.enabled) force_push_blocked=\(.allow_force_pushes.enabled|not)"'
gh pr view "$PR" --repo "$REPO" --json state --jq '"    PR state=\(.state)"'
exit "$MERGED"
