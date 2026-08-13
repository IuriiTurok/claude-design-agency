#!/usr/bin/env bash
# Run design-intent.py against every fixture in fixtures.jsonl.
# Cleans fixture-* markers before and after the run.
# Exits nonzero if any case FAILs.

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURES="$PLUGIN_DIR/tests/fixtures.jsonl"
HOOK="$PLUGIN_DIR/hooks/design-intent.py"
ENGAGED_DIR="$HOME/.claude/cache/design-agency/engaged"
GATE_DIR="$HOME/.claude/cache/design-agency/gate"

PASS=0
FAIL=0
FAILURES=""

# Hermetic marker repo for the brandbook auto-engage case: a throwaway dir
# carrying the DesignAgencyAgent/master_agent.md marker the hook walks up for.
# Avoids depending on a real repo path that can move between sessions.
MARKER_REPO="$(mktemp -d)"
mkdir -p "$MARKER_REPO/DesignAgencyAgent"
: > "$MARKER_REPO/DesignAgencyAgent/master_agent.md"
trap 'rm -rf "$MARKER_REPO"' EXIT

cleanup_fixtures() {
    # Remove any engaged / gate markers created by fixture runs.
    if [ -d "$ENGAGED_DIR" ]; then
        find "$ENGAGED_DIR" -maxdepth 1 -name 'fixture-*' -delete 2>/dev/null || true
    fi
    if [ -d "$GATE_DIR" ]; then
        find "$GATE_DIR" -maxdepth 1 -name 'fixture-*' -delete 2>/dev/null || true
    fi
}

cleanup_fixtures

while IFS= read -r line || [ -n "$line" ]; do
    # Skip blank lines or comments.
    [[ -z "$line" || "$line" == \#* ]] && continue

    NAME=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(d['name'])" "$line")
    EXPECT=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(d['expect'])" "$line")
    PAYLOAD=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(json.dumps(d['payload']))" "$line")
    # Substitute the hermetic marker-repo path for the brandbook-engage case.
    PAYLOAD=${PAYLOAD//\{\{MARKER_REPO\}\}/$MARKER_REPO}
    EXPECT_SOURCE=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(d.get('expect_source',''))" "$line")
    EXPECT_TYPE=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(d.get('expect_type',''))" "$line")

    # Run the hook, capture stdout.
    RAW=$(echo "$PAYLOAD" | python3 "$HOOK" 2>/dev/null || true)

    # Parse the band from the emitted JSON; empty output → none.
    if [ -z "$RAW" ]; then
        BAND="none"
        ACTUAL_SOURCE=""
        ACTUAL_TYPE=""
    else
        BAND=$(python3 -c "
import sys, json, re
raw = sys.stdin.read().strip()
if not raw:
    print('none'); sys.exit(0)
try:
    outer = json.loads(raw)
    ctx = outer['hookSpecificOutput']['additionalContext']
    m = re.search(r'<design-agency-decision>\n(.*?)\n</design-agency-decision>', ctx, re.DOTALL)
    if not m:
        print('none'); sys.exit(0)
    dec = json.loads(m.group(1))
    print(dec.get('band','none'))
except Exception:
    print('none')
" <<< "$RAW")
        ACTUAL_SOURCE=$(python3 -c "
import sys, json, re
raw = sys.stdin.read().strip()
if not raw:
    print(''); sys.exit(0)
try:
    outer = json.loads(raw)
    ctx = outer['hookSpecificOutput']['additionalContext']
    m = re.search(r'<design-agency-decision>\n(.*?)\n</design-agency-decision>', ctx, re.DOTALL)
    if not m:
        print(''); sys.exit(0)
    dec = json.loads(m.group(1))
    print(dec.get('source',''))
except Exception:
    print('')
" <<< "$RAW")
        ACTUAL_TYPE=$(python3 -c "
import sys, json, re
raw = sys.stdin.read().strip()
if not raw:
    print(''); sys.exit(0)
try:
    outer = json.loads(raw)
    ctx = outer['hookSpecificOutput']['additionalContext']
    m = re.search(r'<design-agency-decision>\n(.*?)\n</design-agency-decision>', ctx, re.DOTALL)
    if not m:
        print(''); sys.exit(0)
    dec = json.loads(m.group(1))
    print(dec.get('engagement_type',''))
except Exception:
    print('')
" <<< "$RAW")
    fi

    # Compare band.
    OK=1
    REASON=""
    if [ "$BAND" != "$EXPECT" ]; then
        OK=0
        REASON="band: got '$BAND', want '$EXPECT'"
    fi
    # Optional source check.
    if [ -n "$EXPECT_SOURCE" ] && [ "$ACTUAL_SOURCE" != "$EXPECT_SOURCE" ]; then
        OK=0
        REASON="${REASON:+$REASON; }source: got '$ACTUAL_SOURCE', want '$EXPECT_SOURCE'"
    fi
    # Optional type check.
    if [ -n "$EXPECT_TYPE" ] && [ "$ACTUAL_TYPE" != "$EXPECT_TYPE" ]; then
        OK=0
        REASON="${REASON:+$REASON; }type: got '$ACTUAL_TYPE', want '$EXPECT_TYPE'"
    fi

    if [ "$OK" -eq 1 ]; then
        echo "PASS  $NAME"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $NAME  ($REASON)"
        FAIL=$((FAIL + 1))
        FAILURES="${FAILURES}  - ${NAME}: ${REASON}\n"
    fi

done < "$FIXTURES"

cleanup_fixtures

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
    printf "Failures:\n%b" "$FAILURES"
    exit 1
fi

exit 0
