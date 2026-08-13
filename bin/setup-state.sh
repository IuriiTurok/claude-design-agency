#!/usr/bin/env bash
# setup-state.sh — seed the agency's writable state and report optional deps.
#
# The plugin itself is installed by the marketplace:
#   /plugin marketplace add IuriiTurok/design-agency
#   /plugin install design-agency@design-agency-mp
#
# Skills, agents, and hooks all register from the plugin manifest. This script
# does NOT symlink anything into ~/.claude and does NOT touch settings.json —
# doing either alongside a marketplace install double-registers the hooks and
# they fire twice per prompt.
#
# All this does is create the writable state dir the agency reads and writes
# (see the State table in README.md), which is optional: every path also gets
# created lazily on first write.
#
# Safe to re-run: idempotent (copy-if-absent, mkdir -p).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_DIR="${DESIGN_AGENCY_STATE_DIR:-${HOME}/.claude/design-agency}"

echo "design-agency setup-state.sh"
echo "  plugin root: $PLUGIN_ROOT"
echo "  state dir:   $STATE_DIR"
echo ""

# ---------------------------------------------------------------------------
# 1. Seed state files (never overwrite — this is your agency's memory)
# ---------------------------------------------------------------------------
mkdir -p "$STATE_DIR" "$STATE_DIR/lessons"

seeded=()
skipped=()

for seed_file in style_library.md logo_feedback_log.json lessons_learned.md; do
  src="$PLUGIN_ROOT/seed/$seed_file"
  dst="$STATE_DIR/$seed_file"
  if [ ! -f "$dst" ]; then
    cp "$src" "$dst"
    seeded+=("$seed_file")
  else
    skipped+=("$seed_file")
  fi
done

if [ ! -f "$STATE_DIR/lessons/README.md" ]; then
  cp "$PLUGIN_ROOT/seed/lessons/README.md" "$STATE_DIR/lessons/README.md"
  seeded+=("lessons/README.md")
fi

# ---------------------------------------------------------------------------
# 2. Cache directories for hook state
# ---------------------------------------------------------------------------
mkdir -p "${HOME}/.claude/cache/design-agency/engaged"
mkdir -p "${HOME}/.claude/cache/design-agency/gate"
echo "  ensured: ~/.claude/cache/design-agency/{engaged,gate}"

# ---------------------------------------------------------------------------
# 3. Brand config
# ---------------------------------------------------------------------------
if [ -f "$STATE_DIR/config.json" ]; then
  echo "  ok: brand config present at $STATE_DIR/config.json"
else
  echo "  note: no brand config at $STATE_DIR/config.json"
  echo "        The agency runs brand-neutral without one — bleed-through checks"
  echo "        are skipped rather than guessed. See README.md § Brand config."
fi

# ---------------------------------------------------------------------------
# 4. Optional dependency report
# ---------------------------------------------------------------------------
echo ""
echo "  Optional dependencies:"

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "  optional: logo generation requires GEMINI_API_KEY + pip install google-generativeai"
else
  echo "  ok: GEMINI_API_KEY is set"
fi

if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then
  echo "  ok: node/npx present (marp, svgo, sharp tooling available)"
else
  echo "  optional: marp/svgo/sharp tooling requires node + npx"
fi

if [ -d "$STATE_DIR/.venv-vision" ] || [ -d "./.venv-vision" ]; then
  echo "  ok: vision venv found"
else
  echo "  optional: heatmap/vision analysis requires .venv-vision (see execution/setup_vision.sh)"
fi

if [ -d "${SIL_KERNEL:-${HOME}/.claude/lib/self-improving-loop}" ]; then
  echo "  ok: self-improving-loop kernel present"
else
  echo "  optional: sil loops need the self-improving-loop kernel (they exit cleanly without it)"
fi

# ---------------------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------------------
echo ""
echo "  Summary:"
[ ${#seeded[@]} -gt 0 ] && echo "  seeded: ${seeded[*]}"
[ ${#skipped[@]} -gt 0 ] && echo "  kept (already exist): ${skipped[*]}"
echo ""
echo "Done. State is ready. The plugin itself installs via /plugin install."
