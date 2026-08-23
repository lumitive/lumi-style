#!/bin/bash
# Rebuild the consumer projection from origin/main and publish it.
#
# The public repository is not edited: it is a mechanical `git filter-repo`
# projection of this one's history, force-published, so an edit made there is
# overwritten by the next run of this script. `adapters/shipped.json` plus the
# reachability computation in `scripts/lib/shipped.py` decide what crosses.
#
# EVERYTHING IS CHECKED BEFORE THE PUSH, and the push is the last line. A
# projection is easy to rebuild and a published name is not, which is why the
# order is this way round rather than "push, then look".
#
# The privacy scan is the one that needs saying out loud. `check_secrets`'s
# client-name half reads the operator's out-of-bounds list, and its default
# location is usually EMPTY — so the guard reports the same green whether it
# checked or skipped. This script refuses to publish without a list, because an
# empty directory is not an absence of clients. It found one on its first run.
#
# THE PUSH NEEDS A PERSON. `--push` is not enough on its own: the last step
# asks for a typed confirmation and refuses when stdin is not a terminal, so an
# agent running this non-interactively cannot publish and must hand the command
# back. Owner instruction, 2026-08-23 — publishing is hers to authorise, one
# publication at a time, and a rule that lives only in an agent's memory is a
# rule until the next session. Convention 16: a rule written down and then
# broken needs a tool that holds it.
#
# Usage:  scripts/ops/publish.sh                 # dry run: check, do not push
#         scripts/ops/publish.sh --push          # check, then ASK, then publish
set -euo pipefail

DEV=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
PUBLIC=${LUMI_PUBLIC_REMOTE:-https://github.com/lumitive/lumi-style-skill.git}
SOURCE=${LUMI_SOURCE_REMOTE:-https://github.com/lumitive/lumi-style.git}
TERMS=${LUMI_TERMS_DIR:-$HOME/.lumi/terms}
WORK=$(mktemp -d)
PUSH=0
[ "${1:-}" = "--push" ] && PUSH=1
trap 'rm -rf "$WORK"' EXIT

command -v git-filter-repo >/dev/null 2>&1 || {
  echo "git-filter-repo is not on PATH (pip install --user git-filter-repo)"; exit 1; }

# 0. the out-of-bounds list must exist, or the privacy half does not run
shopt -s nullglob
found=("$TERMS"/*.terms.txt)
[ ${#found[@]} -gt 0 ] || {
  echo "REFUSING: no *.terms.txt under $TERMS."
  echo "  check_secrets's client-name half reads that list. Without it the scan"
  echo "  reports green having looked for nothing, and this script publishes."
  echo "  Point LUMI_TERMS_DIR at the list, or put it there."; exit 1; }
echo "ok  out-of-bounds list present (${#found[@]} file(s))"

cd "$DEV"
python3 - > "$WORK/paths.txt" <<'PY'
import sys, subprocess
sys.path.insert(0, 'scripts/lib'); import shipped
consumer = shipped.consumer_scripts()
tracked = [x for x in subprocess.run(["git", "ls-files", "-z"], capture_output=True,
                                     text=True).stdout.split("\0") if x]
for f in tracked:
    if shipped.side_of(f, consumer=consumer) == "consumer":
        print(f)
PY
echo "ok  $(wc -l < "$WORK/paths.txt" | tr -d ' ') consumer paths"

git clone -q --branch main --single-branch "$SOURCE" "$WORK/proj"
echo "ok  source $(git -C "$WORK/proj" log --oneline -1)"
( cd "$WORK/proj" && git filter-repo --force --paths-from-file "$WORK/paths.txt" >/dev/null 2>&1 )
echo "ok  projection: $(git -C "$WORK/proj" ls-files | wc -l | tr -d ' ') files, \
$(git -C "$WORK/proj" rev-list --count HEAD) commits"

# 1. no release subject lost: check_evidence and shipping read them to find a version
lost=$(comm -23 \
  <(git -C "$DEV" log --format=%s origin/main | grep -E "^[0-9]+\.[0-9]+\.[0-9]+ — " | sort -u) \
  <(git -C "$WORK/proj" log --format=%s | grep -E "^[0-9]+\.[0-9]+\.[0-9]+ — " | sort -u))
[ -z "$lost" ] || { echo "FAIL release subjects lost:"; echo "$lost"; exit 1; }
echo "ok  every release subject preserved"

# 2. nothing from the development side rode along
stray=$(git -C "$WORK/proj" ls-files | grep -E \
  "^(tests|specs|releases|conformance|backlog|reviews)/|^(CLAUDE|CONTRIBUTING|KNOWN_GAPS|FAILURE_MODES)\.md|^pyproject|^requirements-dev|^assets/shapes/source/|^scripts/README" || true)
[ -z "$stray" ] || { echo "FAIL development files in the projection:"; echo "$stray"; exit 1; }
echo "ok  no development file in the projection"

# 3. the guards, asked of the PROJECTION and pointed at the real terms list
LUMI_TERMS_DIR="$TERMS" python3 - "$WORK/proj" "$DEV" <<'PY'
import pathlib, sys
proj, dev = sys.argv[1], sys.argv[2]
sys.path[:0] = [f"{dev}/scripts/{d}" for d in
                ("check", "lib", "ops", "build", "render")] + [f"{dev}/scripts"]
import check_repo
check_repo.ROOT = pathlib.Path(proj).resolve()
bad = 0
for name, fn in (("secrets and client names", check_repo.check_secrets),
                 ("home paths", check_repo.check_local_paths),
                 ("english only", check_repo.check_english_only)):
    errs = fn()
    print(("FAIL " if errs else "ok   ") + name)
    for e in errs[:5]:
        print(f"       {e}")
    bad |= bool(errs)
sys.exit(bad)
PY

# 4. a fresh clone of the projection is a working skill
git clone -q "$WORK/proj" "$WORK/fresh"
( cd "$WORK/fresh"
  export LUMI_STATE="$WORK/state"
  python3 scripts/ops/new_deck.py --no-trace > "$WORK/deck.html" 2>/dev/null
  # a floor under the embedded font, icons and shape sprite, not a target
  [ "$(wc -c < "$WORK/deck.html")" -gt 400000 ]
  python3 scripts/check/check_design.py fixtures/deck-pass.en.html >/dev/null
  python3 scripts/check/check_prose.py fixtures/deck-pass.en.html >/dev/null
  python3 scripts/check/check_prose.py "$WORK/deck.html" --genre sales >/dev/null
  python3 scripts/build/embed_icons.py --check >/dev/null
  id=$(python3 scripts/ops/trace.py open --entry-path A --genre sales --storyline gtm)
  where=$(python3 -c "import sys; sys.path.append('scripts/lib'); import trace_store; print(trace_store.traces_dir())")
  [ -f "$where/$id.json" ] )
echo "ok  a fresh clone builds a $(wc -c < "$WORK/deck.html" | tr -d ' ') byte deck and passes its own checks"

echo
if [ "$PUSH" -eq 0 ]; then
  echo "DRY RUN — every check passed, nothing was published. Re-run with --push."
  exit 0
fi

here=$(cd "$DEV" && grep -m1 -o '"[0-9.]*"' SKILL.md | tr -d '"')
# The API, never raw.githubusercontent: the raw host is a CDN and caches for
# minutes, so right after a publish it names the PREVIOUS version — which is
# exactly when this line is read (0.1.583).
slug=${PUBLIC#https://github.com/}; slug=${slug%.git}
there=$(gh api "repos/$slug/contents/SKILL.md" --jq .content 2>/dev/null \
        | base64 -d 2>/dev/null | grep -m1 -o '"[0-9.]*"' | tr -d '"' || true)
echo "About to FORCE-PUSH the projection of $here over ${there:-an unknown version}"
echo "at $PUBLIC — the published history is replaced, not merged."
echo

if [ ! -t 0 ]; then
  cat <<'MSG'
REFUSING: --push needs a person, and stdin is not a terminal.

  Publishing is the owner's to authorise, one publication at a time. Every
  check above passed, so nothing is wrong with the projection — what is
  missing is the say-so.

  Run it yourself:  scripts/ops/publish.sh --push
  (in Claude Code, prefix with `!` to run it in this session)
MSG
  exit 2
fi

printf 'Type the version to publish (%s) to confirm, anything else to stop: ' "$here"
read -r answer
[ "$answer" = "$here" ] || { echo "stopped — nothing was published."; exit 3; }

git -C "$WORK/proj" remote add publish "$PUBLIC"
git -C "$WORK/proj" push --force publish main:main
echo "published to $PUBLIC"
