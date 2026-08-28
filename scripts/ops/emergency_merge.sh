#!/bin/bash
# Emergency manual merge for when GitHub Actions cannot run the required check.
#
# Branch protection on main requires a pull request, requires the "checks"
# status on it, and enforces both for admins, so nobody can merge while Actions
# is down. This opens that lock for one merge and closes it again. Turning
# enforce_admins off suspends the whole rule set for admins, so the one lock is
# still the only one to open — and this script merges a PR either way, which is
# what the pull-request rule asks for.
#
#   Usage:  bash scripts/ops/emergency_merge.sh <PR-NUMBER>
#
# Exit codes (a caller must be able to tell these apart):
#   0  merged, protection restored
#   1  refused before anything was touched
#   2  the required check failed on the merge result — a real defect in the PR
#   3  the checker could not RUN (local toolchain problem, not a PR defect)
#   4  unlocked, merge failed, protection restored
#   5  PROTECTION IS STILL OFF — act immediately
#
# Threat model. This runs on a maintainer's machine with live gh credentials
# against a PUBLIC repo. Three rules follow, each earned from a review finding:
#
#   1. Never execute code that came from the pull request. Overwriting the PR's
#      check_repo.py is NOT sufficient: the script's own directory is sys.path[0],
#      so a PR adding scripts/json.py hijacks an import and runs arbitrary code.
#      Verified. PYTHONSAFEPATH=1 (Python 3.11+) removes that directory from the
#      path, so we require 3.11 and refuse otherwise. Since 0.1.420 check_repo
#      imports sibling modules (color_math, css_tokens, lock — all pure
#      stdlib underneath), so the trusted copy is the whole EXECUTION closure
#      (imports plus the review_scores subprocess), each file overwriting the
#      PR's version at the same path. Three layers keep PR code dead: stdlib
#      resolves first (the bootstrap only APPENDS), lib/ precedes the scripts
#      root in the append order, and root-level *.py in the temp tree is
#      purged outright. Found broken by the restructuring audit
#      (specs/2026-08-13-audit-restructure-design.md): the single-file copy
#      left import color_math unresolvable under SAFEPATH, so this path
#      would have misdiagnosed EVERY PR as a real defect.
#   2. Fork PRs are refused. A same-repo branch means someone with push access
#      made it; a fork branch means anyone did.
#   3. Verify what will actually be merged. We fetch refs/pull/N/merge, confirm
#      its second parent is the head SHA we validated, and pin the merge with
#      --match-head-commit so a push landing mid-run aborts instead of sneaking in.

set -uo pipefail

REPO=lumitive/lumi-style
PR="${1:?usage: bash scripts/ops/emergency_merge.sh <PR-NUMBER>}"
PROT="repos/$REPO/branches/main/protection/enforce_admins"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRUSTED_CHECK="$SCRIPT_DIR/../check/check_repo.py"
# The trusted EXECUTION closure: everything that runs during the emergency
# check. Three files are check_repo's sibling imports (color_math,
# css_tokens, lock), one is the script it SUBPROCESSES (review_scores — the
# PR #92 review found the PR's own copy being executed here), and
# deliverable_registry rides along prophylactically. Every file must itself
# be pure-stdlib underneath. tests/test_emergency_checker_closure.py parses
# this array and asserts it against check_repo's actual imports — widening
# check_repo without widening this list fails the suite.
TRUSTED_CLOSURE=("$SCRIPT_DIR/../lib/color_math.py" "$SCRIPT_DIR/../lib/css_tokens.py" "$SCRIPT_DIR/../lib/lock.py" "$SCRIPT_DIR/../lib/trace_schema.py" "$SCRIPT_DIR/../lib/rubric_items.py" "$SCRIPT_DIR/../lib/deliverable_registry.py" "$SCRIPT_DIR/../lib/markup.py" "$SCRIPT_DIR/../lib/secret_patterns.py" "$SCRIPT_DIR/../check/check_privacy.py" "$SCRIPT_DIR/../check/check_prose.py" "$SCRIPT_DIR/../lib/corpus.py" "$SCRIPT_DIR/review_scores.py" "$SCRIPT_DIR/../lib/gate_registry.py" "$SCRIPT_DIR/check_deliverable.py" "$SCRIPT_DIR/../lib/stamps.py" "$SCRIPT_DIR/../lib/shipped.py" "$SCRIPT_DIR/../lib/state_dir.py" "$SCRIPT_DIR/../lib/gating.py" "$SCRIPT_DIR/../lib/trace_store.py" "$SCRIPT_DIR/../lib/versioning.py" "$SCRIPT_DIR/../lib/platform_registry.py" "$SCRIPT_DIR/../lib/history.py" "$SCRIPT_DIR/../lib/agent_capability.py")
UNLOCKED=0
RESTORE_FAILED=0
WORK=""

cleanup() {
  [ -n "$WORK" ] && rm -rf "$WORK"
  WORK=""
  [ "$UNLOCKED" -eq 1 ] || return 0

  echo
  echo "==> Restoring enforce_admins"
  local out delay=2
  for attempt in 1 2 3 4; do
    if out=$(gh api --method POST "$PROT" 2>&1); then
      if [ "$(gh api "$PROT" --jq '.enabled' 2>/dev/null)" = "true" ]; then
        echo "    enforce_admins = true (restored)"
        UNLOCKED=0            # idempotent: a second call is now a no-op
        RESTORE_FAILED=0
        return 0
      fi
      out="POST reported success but .enabled is not true"
    fi
    # Show the reason. Expired token, missing scope, SAML re-auth and a rate
    # limit all look identical without it, and they need different responses.
    echo "    attempt $attempt failed: ${out//$'\n'/ | }"
    [ "$attempt" -lt 4 ] && sleep "$delay" && delay=$((delay * 2))
  done

  RESTORE_FAILED=1
  echo
  echo "    !!!!  PROTECTION IS STILL OFF ON main  !!!!"
  echo "    !!!!  Run this now:                    !!!!"
  echo "    !!!!  gh api --method POST $PROT"
  return 1
}
# Signal handlers must terminate. A bare `trap cleanup INT` returns and lets the
# script RESUME, which made a killed `gh pr merge` report success.
trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

die() { echo "!! $2"; exit "$1"; }

[ -f "$TRUSTED_CHECK" ] || die 1 "$TRUSTED_CHECK not found."
for f in "${TRUSTED_CLOSURE[@]}"; do
  [ -f "$f" ] || die 1 "$f not found — the trusted closure is incomplete."
done
python3 - <<'PY' || die 1 "Python 3.11+ required (PYTHONSAFEPATH); refusing to run PR code without it."
import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)
PY

echo "==> PR #$PR"
# One call, tab-separated. Every guard below is fail-closed: an empty or
# unexpected value takes the refusing branch.
IFS=$'\t' read -r TITLE STATE MERGEABLE FORK HEAD_SHA HEAD_REF < <(
  gh pr view "$PR" --repo "$REPO" \
    --json title,state,mergeable,isCrossRepository,headRefOid,headRefName \
    --jq '[.title, .state, .mergeable, (.isCrossRepository|tostring),
           .headRefOid, .headRefName] | @tsv'
) || true

echo "    ${TITLE:-<could not read PR metadata>}"
echo "    state=${STATE:-?} mergeable=${MERGEABLE:-?} fork=${FORK:-?} head=${HEAD_REF:-?}@${HEAD_SHA:0:7}"

[ -n "${STATE:-}" ] || die 1 "Could not read PR metadata (network or auth?). Nothing changed."
[ "${FORK:-true}" = "false" ] || die 1 "PR is from a fork. Refusing: merging it would trust a tree anyone could author, with no CI having run."
[ "${STATE}" = "OPEN" ] || die 1 "PR state is ${STATE}, not OPEN. Nothing changed."
[ "${MERGEABLE:-}" = "MERGEABLE" ] || die 1 "Not mergeable (${MERGEABLE:-unknown}). Nothing changed."
[[ "${HEAD_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || die 1 "No valid head SHA. Without it the merge cannot be pinned."

echo
echo "==> Fetching the merge result (refs/pull/$PR/merge), not the branch tip"
WORK=$(mktemp -d) || die 1 "mktemp failed."
git init --quiet "$WORK/repo" || die 1 "git init failed."
git -C "$WORK/repo" fetch --quiet --depth 2 \
  "https://github.com/$REPO.git" "refs/pull/$PR/merge" 2>/dev/null \
  || die 1 "Could not fetch refs/pull/$PR/merge. GitHub may not have computed it yet."
git -C "$WORK/repo" checkout --quiet FETCH_HEAD || die 1 "checkout failed."

# GitHub computes the merge ref asynchronously. A stale one means we would verify
# an older tree than the one --match-head-commit merges.
MERGE_PARENT=$(git -C "$WORK/repo" rev-parse --verify --quiet 'FETCH_HEAD^2' || true)
[ "$MERGE_PARENT" = "$HEAD_SHA" ] \
  || die 1 "Merge ref is stale (its head parent ${MERGE_PARENT:0:7} != ${HEAD_SHA:0:7}). Re-run in a moment."
echo "    merge ref confirmed against head ${HEAD_SHA:0:7}"

echo "==> Running the TRUSTED local checker over that tree"
mkdir -p "$WORK/repo/scripts/lib" "$WORK/repo/scripts/check" "$WORK/repo/scripts/ops" \
  || die 3 "could not prepare the trusted directories"
cp "$TRUSTED_CHECK" "$WORK/repo/scripts/check/check_repo.py" \
  || die 3 "could not install the trusted checker — refusing to run the PR's copy"
for f in "${TRUSTED_CLOSURE[@]}"; do
  case "$f" in
    */review_scores.py) dest="$WORK/repo/scripts/ops" ;;
    *)                  dest="$WORK/repo/scripts/lib" ;;
  esac
  cp "$f" "$dest/$(basename "$f")" \
    || die 3 "could not install trusted $(basename "$f") — a partial closure misdiagnoses PRs"
done
# Purge any PR-planted shadow at the scripts ROOT: the bootstrap appends the
# root LAST (after lib/), and this removes the class entirely rather than
# relying on order alone. preflight.py is the only legitimate root script
# and the emergency check never imports it.
find "$WORK/repo/scripts" -maxdepth 1 -name "*.py" -delete \
  || die 3 "could not purge root-level scripts from the PR tree"
# PYTHONSAFEPATH keeps the PR's scripts/ off sys.path, so a planted json.py
# cannot hijack an import. Overwriting the checker alone does not do this.
PYTHONSAFEPATH=1 python3 "$WORK/repo/scripts/check/check_repo.py"
RC=$?
if [ "$RC" -ge 126 ]; then
  die 3 "Could not RUN the checker (exit $RC) — a local toolchain problem, not a PR defect."
elif [ "$RC" -ne 0 ]; then
  die 2 "The required check FAILS on the merge result. Not unlocking, not merging. This is a real defect."
fi
echo "    all checks pass on the exact tree that merging would produce"

echo
echo "==> Opening the lock (enforce_admins off)"
# Arm the restore BEFORE the call: if the request lands but the response is lost,
# the lock is open and we must still put it back. An extra restore is free.
UNLOCKED=1
if ! OUT=$(gh api --method DELETE "$PROT" 2>&1); then
  echo "!! Could not disable enforce_admins: ${OUT//$'\n'/ | }"
  exit 1
fi
[ "$(gh api "$PROT" --jq '.enabled' 2>/dev/null)" = "false" ] \
  || { echo "!! enforce_admins did not actually turn off. Aborting."; exit 1; }
echo "    enforce_admins = false"

echo
echo "==> Merging PR #$PR (pinned to ${HEAD_SHA:0:7})"
MERGED=1
if gh pr merge "$PR" --repo "$REPO" --rebase --delete-branch --admin \
     --match-head-commit "$HEAD_SHA"; then
  echo "    merged"
  MERGED=0
else
  echo "!! Merge failed or was refused (a mid-run push to the branch does this)."
fi

# Restore while still trapped, then report. Disarming first would leave the
# slowest, most failure-prone part of the run unprotected against Ctrl-C.
cleanup
trap - EXIT INT TERM

echo
echo "==> Final state"
gh api "repos/$REPO/branches/main/protection" --jq \
  '"    enforce_admins=\(.enforce_admins.enabled)
    required=\(.required_status_checks.checks | map(.context) | join(","))
    pr_required=\(.required_pull_request_reviews != null) approvals=\(.required_pull_request_reviews.required_approving_review_count // 0)
    linear=\(.required_linear_history.enabled) force_push_blocked=\(.allow_force_pushes.enabled|not)"' \
  || echo "    !! could not read protection state — check it by hand"
gh pr view "$PR" --repo "$REPO" --json state --jq '"    PR state=\(.state)"' || true

if [ "$RESTORE_FAILED" -eq 1 ]; then
  echo
  echo "!!!! EXIT 5: main is UNPROTECTED. Restore it now:"
  echo "!!!! gh api --method POST $PROT"
  exit 5
fi
[ "$MERGED" -eq 0 ] || exit 4
exit 0
