#!/usr/bin/env python3
"""
Log a user-choice override to the design-agency overrides file.

Cache path constant:
  OVERRIDES_LOG = ~/.claude/cache/design-agency/overrides.jsonl
  (override via env var DESIGN_AGENCY_OVERRIDES_LOG)

Usage:
  python3 log_override.py <decision_id> <engagement_type> <confidence> <user_choice>

  user_choice: one of  engaged | inline | not_design
"""

import json
import os
import sys
import datetime

OVERRIDES_LOG = os.environ.get(
    "DESIGN_AGENCY_OVERRIDES_LOG",
    os.path.expanduser("~/.claude/cache/design-agency/overrides.jsonl"),
)


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
    except Exception as exc:  # noqa: BLE001
        # Non-fatal: caller must proceed with the work regardless.
        print(f"[log_override] write failed (non-fatal): {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
