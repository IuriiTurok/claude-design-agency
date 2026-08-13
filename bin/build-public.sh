#!/usr/bin/env bash
# build-public.sh — export this plugin to its public distribution repo.
#
# Why this exists: the private repo's git HISTORY contains client brand data
# from before the 0.2.0 genericization (seeded style libraries, logo-generation
# prompt logs). Making that repo public would expose every one of those commits.
# So the private repo stays authoritative and this script mirrors the current
# tree into a separate public repo with its own history.
#
# The working tree itself is already brand-neutral — real values live in
# {AGENCY_STATE}, untracked — so this is a mirror plus a guard, not a transform.
# The guard is the point: it FAILS the build if anything client-identifying or
# machine-specific has crept back into a tracked file.
#
# Usage:
#   bin/build-public.sh <path-to-public-checkout> [--commit]
#
# Without --commit it stages the files and stops so you can review `git diff`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="${1:-}"
COMMIT="${2:-}"

if [ -z "$DEST" ]; then
  echo "usage: bin/build-public.sh <path-to-public-checkout> [--commit]" >&2
  exit 1
fi

if [ ! -d "$DEST/.git" ]; then
  echo "error: $DEST is not a git checkout." >&2
  echo "       Create the public repo first, then clone it there." >&2
  exit 1
fi

VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
  "$SRC/.claude-plugin/plugin.json")"

echo "building design-agency v$VERSION"
echo "  source: $SRC"
echo "  dest:   $DEST"
echo ""

# ---------------------------------------------------------------------------
# 1. Mirror tracked content
# ---------------------------------------------------------------------------
# --delete so files removed upstream disappear downstream. .git is excluded on
# BOTH sides: the destination keeps its own independent history.
rsync -a --delete \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.venv-vision/' \
  --exclude='.DS_Store' \
  --exclude='.env' \
  --exclude='.env.*' \
  "$SRC/" "$DEST/"

echo "  mirrored $(find "$DEST" -type f -not -path '*/.git/*' | wc -l | tr -d ' ') files"

# ---------------------------------------------------------------------------
# 2. Guard — fail the build rather than publish a leak
# ---------------------------------------------------------------------------
fail=0

# This script carries the guard patterns as literals, so it would always match
# itself. Exclude it from every scan below.
GUARD_SELF='bin/build-public.sh'

# Client and project names that must never appear in a distributed file.
CLIENTS='tworocks|heyfin|skillreveal|uzorymamy|bestrong|fasttrack|intenture|patyx|cloony|stirden'
if hits=$(grep -rIl -E -i "$CLIENTS" "$DEST" --exclude-dir=.git --exclude="$(basename "$GUARD_SELF")" 2>/dev/null); then
  echo ""
  echo "  FAIL: client-identifying strings in tracked files:"
  echo "$hits" | sed 's/^/    /'
  fail=1
fi

# Machine-specific paths.
if hits=$(grep -rIn '/Users/\|/home/[a-z]' "$DEST" --exclude-dir=.git --exclude="$(basename "$GUARD_SELF")" 2>/dev/null); then
  echo ""
  echo "  FAIL: absolute home paths:"
  echo "$hits" | cut -c1-140 | sed 's/^/    /'
  fail=1
fi

# Plugin self-references that break under a marketplace install.
if hits=$(grep -rIn '~/.claude/plugins/design-agency' "$DEST" --exclude-dir=.git --exclude="$(basename "$GUARD_SELF")" 2>/dev/null); then
  echo ""
  echo "  FAIL: hardcoded install paths (use \${CLAUDE_PLUGIN_ROOT}):"
  echo "$hits" | cut -c1-140 | sed 's/^/    /'
  fail=1
fi

# Anything that looks like a credential.
if hits=$(grep -rIn -E '(api[_-]?key|secret|token|password)[\"'"'"' ]*[:=][\"'"'"' ]*[A-Za-z0-9_\-]{16,}' \
    "$DEST" --exclude-dir=.git --exclude="$(basename "$GUARD_SELF")" 2>/dev/null); then
  echo ""
  echo "  FAIL: possible credential:"
  echo "$hits" | cut -c1-140 | sed 's/^/    /'
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "Build aborted. Nothing was committed." >&2
  exit 1
fi
echo "  guard: clean (no client data, no absolute paths, no credentials)"

# ---------------------------------------------------------------------------
# 3. Validate the built artifact, not the source
# ---------------------------------------------------------------------------
if command -v claude >/dev/null 2>&1; then
  ( cd "$DEST" \
    && claude plugin validate . --strict >/dev/null \
    && claude plugin validate .claude-plugin/plugin.json --strict >/dev/null )
  echo "  validate: both manifests pass --strict"
else
  echo "  validate: SKIPPED (claude CLI not on PATH)"
fi

( cd "$DEST" && bash tests/run.sh >/dev/null 2>&1 ) \
  && echo "  tests: pass" \
  || { echo "  FAIL: tests/run.sh failed in the built tree" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 4. Stage, and optionally commit
# ---------------------------------------------------------------------------
cd "$DEST"
git add -A

if [ "$COMMIT" = "--commit" ]; then
  if git diff --cached --quiet; then
    echo ""
    echo "  nothing to commit — public repo already matches v$VERSION"
    exit 0
  fi
  git commit -q -m "release: design-agency v$VERSION"
  echo ""
  echo "  committed v$VERSION. Review, then: git push && git tag v$VERSION"
else
  echo ""
  echo "  staged. Review with: git -C $DEST diff --cached"
  echo "  then re-run with --commit"
fi
