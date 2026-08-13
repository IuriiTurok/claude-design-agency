#!/usr/bin/env python3
"""Append one anti-pattern candidate to the impeccable sil intake.

Deterministic writer for ``reference/ai-slop-candidates.jsonl`` — the realized
"observed violations" stream ``impeccable_loop.py`` reads: ``propose()`` promotes
a pattern seen >= 2x to the ban list, and ``measure()`` surfaces its realized
prevalence. The Phase-5 QA agents (``taste-guardian``, ``visual-qa``) call this
on a hard-gate rejection instead of hand-formatting JSON, so every row is
well-shaped. Append-only and fail-open: a failed write never blocks the verdict.

CLI:
  emit_candidate.py --source taste-guardian --engagement acme-landing \
    --tell "glassmorphism" --evidence "hero.css:42" --scope general \
    [--pattern-id glassmorphism] [--ts 2026-06-15T00:00:00+00:00]
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

CANDIDATES = os.path.expanduser(
    "~/.claude/design-agency/ai-slop-candidates.jsonl"
)


def emit_candidate(
    source: str,
    engagement: str,
    tell: str,
    evidence: str = "",
    scope: str = "general",
    pattern_id: str | None = None,
    ts: str | None = None,
    path: str = CANDIDATES,
) -> dict:
    """Append one candidate record and return it. ``pattern_id`` falls back to the
    free-text ``tell`` (the loop reads ``pattern_id or tell``); only a tell that
    matches a mechanical check is ever promoted. Fail-open: on a write error the
    record is returned with an ``error`` note rather than raising."""
    rec = {
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "source": source,
        "engagement": engagement,
        "pattern_id": pattern_id or tell,
        "tell": tell,
        "evidence": evidence,
        "scope": scope,
        "status": "candidate",
    }
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError as e:  # fail-open: never block the caller
        rec["error"] = str(e)
    return rec


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="emit_candidate",
        description="append one anti-pattern candidate to the impeccable sil intake",
    )
    p.add_argument(
        "--source",
        required=True,
        help="emitting agent (taste-guardian / visual-qa / design-agency)",
    )
    p.add_argument("--engagement", required=True, help="client / asset id")
    p.add_argument("--tell", required=True, help="the anti-pattern, <=140 chars")
    p.add_argument("--evidence", default="", help="file:line or asset ref")
    p.add_argument("--scope", default="general", choices=["general", "own_brand"])
    p.add_argument(
        "--pattern-id",
        default=None,
        help="mechanical pattern-id when known (else the tell is used)",
    )
    p.add_argument("--ts", default=None, help="ISO-8601 UTC (default: now)")
    a = p.parse_args(argv)
    rec = emit_candidate(
        source=a.source,
        engagement=a.engagement,
        tell=a.tell,
        evidence=a.evidence,
        scope=a.scope,
        pattern_id=a.pattern_id,
        ts=a.ts,
    )
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
