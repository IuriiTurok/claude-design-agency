#!/usr/bin/env python3
"""design-agency adapter + entry for the `sil` self-improving loop (§2.1).

Tunes the **taste rubric thresholds** the `taste-guardian` enforces in Phase 5,
from a rolling window of archived `taste_report` outcomes. PROSE_RULE artifact,
capped at ONE_CLICK by the autonomy ladder (`rungs.py`): the loop PROPOSES +
SCORES + LOGS a reversible rubric edit, but a human applies it. The loop never
writes into the read-only `{AGENCY_ROOT}/roles/taste_guardian.md` (HARD RULE) —
its candidate `new_text` is the edited rubric, committed only to a LOOP-PRIVATE
git repo under `{AGENCY_STATE}` (`~/.claude/design-agency/sil/loop-repo`) — and
it never pushes.

Fitness signal: mean `taste_report` score per engagement over a rolling window
(higher is better), with the Phase-5 hard-gate pass-rate as a safety gate.

Subcommands:
  propose [--dry-run] [--window N] [--help]   one PROPOSE iteration
  confirm [--dry-run] [--window N]            resolve pending experiments past their window
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

KERNEL = os.path.expanduser(
    os.environ.get("SIL_KERNEL", "~/.claude/lib/self-improving-loop")
)
sys.path.insert(0, KERNEL)

# The self-improving-loop kernel is an OPTIONAL companion install, not a plugin
# dependency. Everything else in the agency works without it, so a missing kernel
# must degrade to a clear message rather than an ImportError traceback.
try:
    from sil import vcs
    from sil.ledger import Ledger
    from sil.loop import Loop
    from sil.models import ArtifactClass, Candidate, RunResult, Rung
except ImportError as exc:  # pragma: no cover - depends on the host machine
    sys.stderr.write(
        f"design-agency: self-improving loop unavailable ({exc}).\n"
        f"  Looked for the kernel at: {KERNEL}\n"
        "  This is optional — the agency's skills, QA gates, and hooks all work\n"
        "  without it. Only `propose`/`run` on this loop need it. Point SIL_KERNEL\n"
        "  at the kernel if you have it installed elsewhere.\n"
    )
    raise SystemExit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
BASELINE_RUBRIC = os.path.join(FIXTURES, "taste_rubric.baseline.json")
REPORTS = os.path.join(FIXTURES, "taste_reports.jsonl")

# {AGENCY_STATE} convention — the skill's live state dir (never {AGENCY_ROOT}).
STATE = os.path.expanduser(os.environ.get("DA_AGENCY_STATE", "~/.claude/design-agency"))
SIL_DIR = os.path.join(STATE, "sil")
LEDGER = os.path.join(SIL_DIR, "taste-ledger.jsonl")  # §2.1 ledger path
# Real archived taste_report outcomes (one JSON row per completed engagement),
# the realized signal measure() prefers over the fixture corpus once a post-
# Phase-5 archival step starts appending here. Absent today -> fixture fallback.
REAL_REPORTS = os.path.join(SIL_DIR, "taste-reports.jsonl")
LOOP_REPO = os.path.join(SIL_DIR, "loop-repo")
RUBRIC_REL = "taste_rubric.json"  # the one artifact, inside LOOP_REPO
BRANCH = "da-taste/auto"

WINDOW_N = 6  # rolling window of recent engagements to read
PERFECT_SLACK = 4.75  # mean >= this for a dim -> slack to tighten its threshold up
FAIL_BAND = 0.30  # mean within this of a dim's threshold -> recurring near-fail
THRESH_STEP = 0.25  # how much to move a threshold per iteration (0-5 scale)
MARGIN = 0.05  # min mean-taste-score gain (over the window) to KEEP


# ---- pure helpers (testable, no I/O) ------------------------------------


def _mean_per_dimension(reports: list[dict]) -> dict[str, float]:
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for r in reports:
        for dim, score in (r.get("scores") or {}).items():
            sums[dim] = sums.get(dim, 0.0) + float(score)
            counts[dim] = counts.get(dim, 0) + 1
    return {d: sums[d] / counts[d] for d in sums if counts[d]}


def _mean_taste_score(reports: list[dict]) -> float | None:
    """Engagement-level fitness signal: mean of each report's mean dimension score."""
    per_report = []
    for r in reports:
        vals = list((r.get("scores") or {}).values())
        if vals:
            per_report.append(sum(float(v) for v in vals) / len(vals))
    return (sum(per_report) / len(per_report)) if per_report else None


def _hard_gate_pass_rate(reports: list[dict]) -> float | None:
    flags = [
        bool(r.get("hard_gate_passed")) for r in reports if "hard_gate_passed" in r
    ]
    return (sum(flags) / len(flags)) if flags else None


def propose_threshold_edit(
    rubric: dict, reports: list[dict]
) -> tuple[str, float, float] | None:
    """Pick ONE out-of-band dimension and a new threshold.

    Returns (dimension, old_threshold, new_threshold) or None.
    - mean >= PERFECT_SLACK and there is slack below scale_max  -> tighten (raise threshold)
    - mean within FAIL_BAND above the threshold (recurring near-fail) -> loosen (lower it)
    Deterministic: scans dimensions in sorted order, first out-of-band wins.
    """
    means = _mean_per_dimension(reports)
    dims = rubric.get("dimensions", {})
    scale_max = float(rubric.get("scale_max", 5))
    for dim in sorted(dims):
        if dim not in means:
            continue
        cur = float(dims[dim].get("min_threshold", 0.0))
        mean = means[dim]
        if mean >= PERFECT_SLACK and cur + THRESH_STEP <= scale_max:
            return (dim, cur, round(cur + THRESH_STEP, 4))
        if 0.0 < (mean - cur) <= FAIL_BAND and cur - THRESH_STEP >= 0.0:
            return (dim, cur, round(cur - THRESH_STEP, 4))
    return None


def rubric_parses(text: str) -> bool:
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(obj.get("dimensions"), dict) or not obj["dimensions"]:
        return False
    for spec in obj["dimensions"].values():
        if "min_threshold" not in spec or "weight" not in spec:
            return False
    return True


def no_regression_on_passers(
    rubric: dict, candidate_rubric: dict, reports: list[dict]
) -> bool:
    """Engagements that passed the hard gate under the baseline rubric must still
    pass under the candidate rubric (a tightened threshold must not retro-fail a
    known-good engagement)."""
    cand_dims = candidate_rubric.get("dimensions", {})
    for r in reports:
        if not r.get("hard_gate_passed"):
            continue
        for dim, score in (r.get("scores") or {}).items():
            thr = float(cand_dims.get(dim, {}).get("min_threshold", 0.0))
            if float(score) < thr:
                return False
    return True


# ---- I/O helpers --------------------------------------------------------


def _read_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _read_reports(window: int) -> list[dict]:
    if not os.path.exists(REPORTS):
        return []
    rows: list[dict] = []
    with open(REPORTS) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    rows.sort(key=lambda r: r.get("ts", ""))
    return rows[-window:] if window else rows


def _ts_dt(ts) -> datetime | None:
    """Parse an ISO-8601 timestamp to an aware datetime; None if unparseable.
    Normalizes a trailing 'Z' to '+00:00' so the kernel's `+00:00` row.ts and the
    'Z'-suffixed report convention compare by instant, not by raw string."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    # Coerce a parseable-but-naive ts to UTC so it never raises when compared
    # against the kernel's tz-aware row.ts (one naive row would otherwise crash
    # the whole confirm pass instead of degrading to the fixture fallback).
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _read_real_reports() -> list[dict]:
    """Real archived taste_report outcomes (JSONL at REAL_REPORTS) that carry a
    parseable ts, sorted by instant. The realized signal `measure()` splits these
    into pre/post-apply windows. Fail-open: an absent file or unparseable rows ->
    dropped, so the caller cleanly falls back to the deterministic fixture re-run."""
    if not os.path.exists(REAL_REPORTS):
        return []
    rows: list[dict] = []
    with open(REAL_REPORTS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _ts_dt(r.get("ts")) is not None:
                rows.append(r)
    rows.sort(key=lambda r: _ts_dt(r.get("ts")))
    return rows


def _current_rubric() -> dict:
    """The live loop-private rubric (seeded from the baseline fixture)."""
    p = os.path.join(LOOP_REPO, RUBRIC_REL)
    if os.path.exists(p):
        try:
            return _read_json(p)
        except (json.JSONDecodeError, OSError):
            pass
    return _read_json(BASELINE_RUBRIC)


# ---- adapter ------------------------------------------------------------


class TasteRubricAdapter:
    def __init__(self, window: int = WINDOW_N):
        self.window = window

    def propose(self) -> Candidate | None:
        rubric = _current_rubric()
        reports = _read_reports(self.window)
        move = propose_threshold_edit(rubric, reports)
        if move is None:
            return None
        dim, old, new = move
        newrubric = json.loads(json.dumps(rubric))  # deep copy
        newrubric["dimensions"][dim]["min_threshold"] = new
        direction = "tighten" if new > old else "loosen"
        return Candidate(
            artifact_path=RUBRIC_REL,
            change_summary=f"taste rubric: {dim} min_threshold {old} -> {new} ({direction})",
            change_signature=f"da-taste:{dim}",
            artifact_class=ArtifactClass.PROSE_RULE,
            new_text=json.dumps(newrubric, indent=2) + "\n",
            meta={"dimension": dim, "old": old, "new": new},
        )

    def execute(self, cand: Candidate) -> RunResult:
        reports = _read_reports(self.window)
        baseline_rubric = _current_rubric()
        cand_rubric = json.loads(cand.new_text)
        gates = {
            "rubric_parses": rubric_parses(cand.new_text),
            "no_regression_on_passers": no_regression_on_passers(
                baseline_rubric, cand_rubric, reports
            ),
        }
        # Offline projection: mean taste score over the window (the realized
        # signal needs the NEXT real engagement -> deferred).
        projected = _mean_taste_score(reports)
        baseline = _mean_taste_score(reports)
        return RunResult(
            metric=projected,
            gates=gates,
            deferred=True,
            detail={
                "baseline": baseline,
                "hard_gate_pass_rate": _hard_gate_pass_rate(reports),
                "dimension": cand.meta["dimension"],
                "window": self.window,
                "n_reports": len(reports),
            },
        )

    def measure(self, row) -> RunResult:
        # Realized signal: a REAL before/after on the engagement stream. The
        # kernel compares `row.baseline_metric` (frozen at execute() from the
        # fixture corpus) against the metric returned here, so to keep the
        # comparison meaningful we express the realized improvement ON THE
        # BASELINE'S SCALE: metric = baseline + (post_mean - pre_mean). The gain
        # decide() sees is then exactly (post_mean - pre_mean) — the fixture
        # baseline cancels, and the decision depends only on whether real
        # engagements scored higher AFTER the rubric edit than BEFORE it.
        #
        # Real before/after needs real reports on BOTH sides of the apply
        # boundary (`row.ts`). When that isn't available (no real file yet, no
        # pre-apply real history, or no post-apply engagements), fall back to the
        # deterministic fixture re-check, which matches the fixture baseline
        # (gain 0 -> ASK) and preserves today's conservative behavior exactly.
        since_dt = _ts_dt(getattr(row, "ts", None))
        real = _read_real_reports() if since_dt else []
        pre = [r for r in real if _ts_dt(r.get("ts")) < since_dt][-self.window :]
        post = [r for r in real if _ts_dt(r.get("ts")) >= since_dt][-self.window :]
        pre_mean = _mean_taste_score(pre)
        post_mean = _mean_taste_score(post)

        if pre and post and pre_mean is not None and post_mean is not None:
            base = row.baseline_metric if row.baseline_metric is not None else 0.0
            metric = base + (post_mean - pre_mean)
            pass_rate = _hard_gate_pass_rate(post)
            gates = {"hard_gate_not_worse": pass_rate is None or pass_rate >= 1.0}
            return RunResult(
                metric=metric,
                gates=gates,
                detail={
                    "source": "real",
                    "pre_mean": pre_mean,
                    "post_mean": post_mean,
                    "n_pre": len(pre),
                    "n_post": len(post),
                    "pass_rate": pass_rate,
                },
            )

        # Deterministic fixture re-check (matches the fixture-derived baseline).
        reports = _read_reports(self.window)
        metric = _mean_taste_score(reports)
        pass_rate = _hard_gate_pass_rate(reports)
        gates = {
            # Hard-gate pass-rate must not collapse below the rubric's bar.
            "hard_gate_not_worse": pass_rate is None or pass_rate >= 1.0,
        }
        return RunResult(
            metric=metric,
            gates=gates,
            detail={
                "source": "fixture-fallback",
                "pass_rate": pass_rate,
                "n_real": len(real),
                "window": self.window,
            },
        )


# ---- entry --------------------------------------------------------------


def _ensure_baseline(dry_run: bool) -> None:
    """Seed the loop-private repo with the baseline rubric. In --dry-run we never
    create or touch the repo (DRY_RUN must not mutate real artifacts)."""
    if dry_run:
        return
    os.makedirs(LOOP_REPO, exist_ok=True)
    p = os.path.join(LOOP_REPO, RUBRIC_REL)
    if not os.path.exists(p):
        with open(p, "w") as f:
            json.dump(_read_json(BASELINE_RUBRIC), f, indent=2)
            f.write("\n")
    vcs.ensure_repo(LOOP_REPO)
    try:
        vcs.commit_file(LOOP_REPO, RUBRIC_REL, "baseline taste rubric", branch=BRANCH)
    except ValueError:
        pass  # already committed / nothing to commit


def _summ(row) -> dict:
    return {
        "decision": row.decision,
        "change": row.change_summary,
        "baseline_metric": row.baseline_metric,
        "candidate_metric": row.candidate_metric,
        "gates": row.gates,
        "reverted": row.reverted,
        "pending_until": row.pending_until,
        "commit_sha": (row.commit_sha or "")[:10] or None,
        "note": row.note,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="design-agency-loop",
        description="sil taste-rubric tuning loop (§2.1). PROSE_RULE / ONE_CLICK: "
        "proposes + scores + logs a reversible rubric edit; NEVER auto-applies.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("propose", help="one PROPOSE iteration")
    pp.add_argument(
        "--dry-run",
        action="store_true",
        help="DRY_RUN rung: simulate + log only, never seed/commit the loop repo",
    )
    pp.add_argument("--window", type=int, default=WINDOW_N, help="rolling window size")
    cf = sub.add_parser("confirm", help="resolve pending experiments past their window")
    cf.add_argument("--dry-run", action="store_true", help="DRY_RUN rung")
    cf.add_argument("--window", type=int, default=WINDOW_N)
    a = p.parse_args(argv)

    dry = getattr(a, "dry_run", False)
    _ensure_baseline(dry)
    ledger = Ledger(LEDGER)
    # PROSE_RULE is capped at ONE_CLICK by rungs.py regardless; --dry-run drops to
    # DRY_RUN. Neither rung ever auto-applies a PROSE_RULE edit.
    rung = Rung.DRY_RUN if dry else Rung.ONE_CLICK
    loop = Loop(
        "design-agency",
        ledger,
        rung,
        repo=LOOP_REPO,
        branch=BRANCH,
        higher_is_better=True,
        margin=MARGIN,
        window_days=2,
    )
    now = datetime.now(timezone.utc)
    adapter = TasteRubricAdapter(window=a.window)

    if a.cmd == "propose":
        if dry:
            # DRY_RUN: compute the proposal + projected metric WITHOUT touching the
            # ledger or the loop repo (a pure simulation the user can inspect).
            cand = adapter.propose()
            if cand is None:
                print("no proposal (no taste dimension is out of band)")
                return 0
            res = adapter.execute(cand)
            print(
                json.dumps(
                    {
                        "rung": "DRY_RUN",
                        "would_apply": False,
                        "change": cand.change_summary,
                        "change_signature": cand.change_signature,
                        "artifact_class": cand.artifact_class.value,
                        "projected_metric": res.metric,
                        "baseline_metric": res.detail.get("baseline"),
                        "gates": res.gates,
                        "detail": res.detail,
                    },
                    indent=2,
                )
            )
            return 0
        row = loop.propose_iteration(adapter, now)
        print(
            json.dumps(_summ(row), indent=2)
            if row
            else "no proposal (no dimension out of band, or an experiment is pending)"
        )
    else:
        if dry:
            print("dry-run confirm: no pending experiments are mutated")
            return 0
        rows = loop.confirm_pending(adapter, now)
        print(
            json.dumps([_summ(r) for r in rows], indent=2)
            if rows
            else "no pending experiments are due"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
