#!/usr/bin/env python3
"""
Log a user-choice override to the design-agency overrides file.

Cache path constants:
  CACHE_DIR     = ~/.claude/cache/design-agency   (env DESIGN_AGENCY_CACHE_DIR)
  OVERRIDES_LOG = CACHE_DIR/overrides.jsonl       (env DESIGN_AGENCY_OVERRIDES_LOG)

Usage (call by absolute path; the decision block carries plugin_root):
  python3 <plugin_root>/skills/design-agency-routing/scripts/log_override.py \
      <decision_id> <engagement_type> <confidence> <user_choice>

  user_choice: one of  engaged | inline | not_design | auto_default

On `engaged` the session that produced decision_id (recorded by the hook in
CACHE_DIR/decisions/) is marked engaged, which silences the hook for the rest
of that session. Any other choice leaves the session open for later prompts of
a different engagement type.
"""

import json
import os
import sys
import datetime

CACHE_DIR = os.environ.get("DESIGN_AGENCY_CACHE_DIR") or os.path.expanduser(
    "~/.claude/cache/design-agency"
)
OVERRIDES_LOG = os.environ.get(
    "DESIGN_AGENCY_OVERRIDES_LOG", os.path.join(CACHE_DIR, "overrides.jsonl")
)


def mark_engaged(decision_id):
    """Touch engaged/<session> for the session that produced decision_id."""
    try:
        with open(os.path.join(CACHE_DIR, "decisions", decision_id)) as fh:
            session_id = fh.read().strip()
    except OSError:
        return
    if not session_id or "/" in session_id:
        return
    engaged_dir = os.path.join(CACHE_DIR, "engaged")
    os.makedirs(engaged_dir, exist_ok=True)
    open(os.path.join(engaged_dir, session_id), "a").close()


def main():
    if len(sys.argv) != 5:
        print(
            "Usage: log_override.py <decision_id> <engagement_type> <confidence> <user_choice>",
            file=sys.stderr,
        )
        sys.exit(1)

    decision_id, engagement_type, confidence_raw, user_choice = sys.argv[1:]

    try:
        confidence = float(confidence_raw)
    except ValueError:
        print(f"Invalid confidence value: {confidence_raw!r}", file=sys.stderr)
        sys.exit(1)

    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "decision_id": decision_id,
        "engagement_type": engagement_type,
        "confidence": confidence,
        "user_choice": user_choice,
    }

    try:
        os.makedirs(os.path.dirname(OVERRIDES_LOG), exist_ok=True)
        with open(OVERRIDES_LOG, "a") as fh:
            fh.write(json.dumps(record) + "\n")
        if user_choice == "engaged" and "/" not in decision_id:
            mark_engaged(decision_id)
    except Exception as exc:  # noqa: BLE001
        # Non-fatal: caller must proceed with the work regardless.
        print(f"[log_override] write failed (non-fatal): {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
