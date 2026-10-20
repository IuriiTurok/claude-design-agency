#!/usr/bin/env bash
# Run design-intent.py against every fixture in fixtures.jsonl.
# Hermetic: HOME and DESIGN_AGENCY_CACHE_DIR point at a throwaway dir, so
# fixture runs never reach the real ~/.claude/cache/design-agency telemetry.
# Fixtures run in file order and share one cache, so a sequence of rows with
# the same session_id exercises the per-session markers.
# Exits nonzero if any case FAILs.

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURES="$PLUGIN_DIR/tests/fixtures.jsonl"
HOOK="$PLUGIN_DIR/hooks/design-intent.py"
TEST_HOME="$(mktemp -d)"
export HOME="$TEST_HOME"
export DESIGN_AGENCY_CACHE_DIR="$TEST_HOME/.claude/cache/design-agency"

PASS=0
FAIL=0
FAILURES=""

# Hermetic marker repo for the brandbook auto-engage case: a throwaway dir
# carrying the DesignAgencyAgent/master_agent.md marker the hook walks up for.
# Avoids depending on a real repo path that can move between sessions.
MARKER_REPO="$TEST_HOME/marker-repo"
mkdir -p "$MARKER_REPO/DesignAgencyAgent"
: > "$MARKER_REPO/DesignAgencyAgent/master_agent.md"
# Repo with a per-project config carrying negative_signals.
NEG_REPO="$TEST_HOME/neg-repo"
mkdir -p "$NEG_REPO/.claude"
printf '{"negative_signals": ["\\\\bopenrocket\\\\b", "\\\\bsimulations?\\\\b"]}\n' > "$NEG_REPO/.claude/design-agency.json"
# Repo with the README's short-form extra_signals (bare strings).
EXTRA_REPO="$TEST_HOME/extra-repo"
mkdir -p "$EXTRA_REPO/.claude"
printf '{"ask_threshold": 0.45, "extra_signals": ["palette", "mockup"]}\n' > "$EXTRA_REPO/.claude/design-agency.json"
trap 'rm -rf "$TEST_HOME"' EXIT

while IFS= read -r line || [ -n "$line" ]; do
    # Skip blank lines or comments.
    [[ -z "$line" || "$line" == \#* ]] && continue

    NAME=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(d['name'])" "$line")
    EXPECT=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(d['expect'])" "$line")
    PAYLOAD=$(python3 -c "import sys,json; d=json.loads(sys.argv[1]); print(json.dumps(d['payload']))" "$line")
    # Substitute the hermetic marker-repo path for the brandbook-engage case.
    PAYLOAD=${PAYLOAD//\{\{MARKER_REPO\}\}/$MARKER_REPO}
    PAYLOAD=${PAYLOAD//\{\{NEG_REPO\}\}/$NEG_REPO}
    PAYLOAD=${PAYLOAD//\{\{EXTRA_REPO\}\}/$EXTRA_REPO}
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

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
    printf "Failures:\n%b" "$FAILURES"
    exit 1
fi

exit 0
