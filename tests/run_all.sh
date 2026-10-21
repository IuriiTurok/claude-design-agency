#!/usr/bin/env bash
# Run every plugin test suite hermetically (throwaway HOME + cache dir).
# Exits nonzero if any suite fails.

set -uo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REAL_HOME="$HOME"
TEST_HOME="$(mktemp -d)"
trap 'rm -rf "$TEST_HOME"' EXIT
export HOME="$TEST_HOME"
export DESIGN_AGENCY_CACHE_DIR="$TEST_HOME/.claude/cache/design-agency"

FAILED=0
run() {
    echo "== $*"
    if ! "$@"; then
        FAILED=$((FAILED + 1))
    fi
}

run bash "$PLUGIN_DIR/tests/run.sh"
for t in "$PLUGIN_DIR"/tests/test_*.py; do
    run python3 "$t"
done

# sil suites need the shared kernel; each file runs on its own (same basename).
KERNEL="$REAL_HOME/.claude/lib/self-improving-loop"
if [ -d "$KERNEL" ] && command -v uvx >/dev/null 2>&1; then
    for t in "$PLUGIN_DIR"/skills/*/sil/test_measure.py; do
        run env SIL_KERNEL="$KERNEL" uvx pytest -q "$t"
    done
else
    echo "== sil suites skipped (no $KERNEL or no uvx)"
fi

echo ""
if [ "$FAILED" -gt 0 ]; then
    echo "FAILED: $FAILED suite(s)"
    exit 1
fi
echo "All suites passed"
