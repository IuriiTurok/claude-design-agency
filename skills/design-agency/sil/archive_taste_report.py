#!/usr/bin/env python3
"""Append one taste_report outcome to the design-agency sil intake.

Deterministic writer for ``{AGENCY_STATE}/sil/taste-reports.jsonl`` — the
realized signal ``design-agency_loop.py`` reads (``measure()`` prefers it over the
fixture corpus, falling back when it is empty). Called after Phase-5 taste scoring
with the engagement's dimension scores + the hard-gate verdict, so the loop tunes
the taste rubric from real outcomes instead of fixtures. Append-only and
fail-open: a failed write never blocks the engagement.

CLI:
  archive_taste_report.py --engagement acme-rebrand \
    --scores '{"originality":4.0,"craft":3.5}' --hard-gate-passed \
    [--ts 2026-06-15T00:00:00+00:00]

Path mirrors the loop's REAL_REPORTS constant (DESIGN_AGENCY_STATE_DIR honored).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# The plugin's own state resolver, three levels up in execution/. Ships with the
# plugin (stdlib-only). Keeps DESIGN_AGENCY_STATE_DIR — the one documented
# override — authoritative here as it is everywhere else in the agency.
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "execution")
    ),
)
import state_paths  # noqa: E402

REAL_REPORTS = os.path.join(str(state_paths.resolve("sil")), "taste-reports.jsonl")


def archive_taste_report(
    engagement: str,
    scores: dict,
    hard_gate_passed: bool,
    ts: str | None = None,
    path: str = REAL_REPORTS,
) -> dict:
    """Append one taste_report row and return it. Scores are coerced to float so
    the loop's mean computation never sees strings. Fail-open on write error."""
    rec = {
        "engagement": engagement,
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "hard_gate_passed": bool(hard_gate_passed),
        "scores": {k: float(v) for k, v in (scores or {}).items()},
    }
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError as e:  # fail-open: never block the engagement
        rec["error"] = str(e)
    return rec


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="archive_taste_report",
        description="append one taste_report outcome to the design-agency sil intake",
    )
    p.add_argument("--engagement", required=True, help="engagement / project id")
    p.add_argument(
        "--scores",
        required=True,
        help='JSON object of dimension->score, e.g. {"originality":4.0,"craft":3.5}',
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--hard-gate-passed", dest="hard_gate", action="store_true")
    g.add_argument("--hard-gate-failed", dest="hard_gate", action="store_false")
    p.add_argument("--ts", default=None, help="ISO-8601 UTC (default: now)")
    a = p.parse_args(argv)
    try:
        scores = json.loads(a.scores)
    except json.JSONDecodeError as e:
        p.error(f"--scores must be valid JSON: {e}")
    rec = archive_taste_report(
        engagement=a.engagement,
        scores=scores,
        hard_gate_passed=a.hard_gate,
        ts=a.ts,
    )
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
