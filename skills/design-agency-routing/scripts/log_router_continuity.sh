#!/usr/bin/env bash
# Log a continuity_inline outcome to the router audit log.
#
# Cache path constant:
#   ROUTER_AUDIT_LOG = ~/.claude/cache/router/audit.jsonl
#   (override via env var ROUTER_AUDIT_LOG)
#
# Usage:
#   log_router_continuity.sh <router_decision_id> <model>

set -euo pipefail

ROUTER_AUDIT_LOG="${ROUTER_AUDIT_LOG:-${HOME}/.claude/cache/router/audit.jsonl}"

if [[ $# -ne 2 ]]; then
  echo "Usage: log_router_continuity.sh <router_decision_id> <model>" >&2
  exit 1
fi

router_decision_id="$1"
model="$2"

mkdir -p "$(dirname "${ROUTER_AUDIT_LOG}")"

# This log is the auto-model-router's audit trail — an optional companion plugin.
# Writing it is best-effort: the caller proceeds regardless, and jq is not assumed
# to be installed (it is absent on a stock macOS/Linux box).
emit() {
  if command -v jq >/dev/null 2>&1; then
    jq -nc \
      --arg id "${router_decision_id}" \
      --arg outcome "continuity_inline" \
      --arg model "${model}" \
      '{ts: (now|todate), decision_id: $id, outcome: $outcome, model: $model}'
  else
    printf '{"ts":"%s","decision_id":"%s","outcome":"continuity_inline","model":"%s"}\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${router_decision_id}" "${model}"
  fi
}

emit >> "${ROUTER_AUDIT_LOG}" || {
  echo "[log_router_continuity] write failed (non-fatal)" >&2
  exit 2
}
