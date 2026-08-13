#!/usr/bin/env python3
"""ui-ux-pro-max design-system reasoning adapter for the `sil` self-improving loop.

Heavyweight tier (self-learning.md §2.3). ui-ux-pro-max persists design systems
via the Master + Overrides pattern (`scripts/design_system.py persist=True`),
generating each Master from one reasoning rule in `data/ui-reasoning.csv`. This
loop learns **which reasoning rules / style picks survive vs. get overridden**
and proposes adjusting the durable default for a rule whose generated field the
user keeps editing away.

- Fitness signal: override-rate — fraction of generated design-system fields the
  user keeps unedited vs. overrides in the persisted Overrides file. Computed
  over a synthetic saved-project corpus (`sil/fixtures/project_*.json`).
  LOWER is better (better default selection -> fewer overrides), so the kernel
  runs with `higher_is_better=False`.
- propose(): if one reasoning rule's targeted field is overridden in >= THRESHOLD
  fraction of its projects, emit a Candidate adjusting that field's default to the
  value users most often picked. `change_signature` = `uux-reasoning:<rule-id>`.
  `None` if no rule clears the threshold.
- execute(): regenerate the corpus override-rate with the candidate rule applied;
  `gates = {"schema_valid": <bool>, "no_empty_field": <bool>}`; `metric` =
  projected override-rate. `deferred=True` — the true rate needs new real
  projects (a `confirm` pass realizes it later via `measure`).
- Artifact class: PROSE_RULE -> capped at ONE_CLICK by the autonomy ladder
  (`rungs.py`). The loop PROPOSES + SCORES + LOGS one reasoning-rule edit per
  iteration; a human clicks to apply. It NEVER auto-writes `ui-reasoning.csv`.
- Ledger: `<ui-ux-pro-max-dir>/sil/reasoning-ledger.jsonl` (shared kernel schema).
  The kernel commits only to a LOOP-PRIVATE repo and never pushes; at ONE_CLICK
  nothing is ever applied, so no repo write happens at all in normal operation.

Subcommands:
  propose [--dry-run]   one PROPOSE iteration (scores the corpus, logs a row)
  confirm               resolve pending experiments (deterministic re-check)

`--dry-run` forces the DRY_RUN rung and an in-memory path: it computes and prints
the projected override-rate / proposal WITHOUT touching the real ledger, the
reasoning CSV, or the kernel's git repo.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone

KERNEL = os.path.expanduser(
    os.environ.get("SIL_KERNEL", "~/.claude/lib/self-improving-loop")
)
sys.path.insert(0, KERNEL)

# The self-improving-loop kernel is an OPTIONAL companion install, not a plugin
# dependency. Everything else in this skill works without it, so a missing kernel
# must degrade to a clear message rather than an ImportError traceback.
try:
    from sil.ledger import Ledger
    from sil.loop import Loop
    from sil.models import ArtifactClass, Candidate, RunResult, Rung
except ImportError as exc:  # pragma: no cover - depends on the host machine
    sys.stderr.write(
        f"design-agency: self-improving loop unavailable ({exc}).\n"
        f"  Looked for the kernel at: {KERNEL}\n"
        "  This is optional. Point SIL_KERNEL at the kernel if it lives elsewhere.\n"
    )
    raise SystemExit(0)

# ---- paths --------------------------------------------------------------

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIL_DIR = os.path.join(SKILL_DIR, "sil")
FIXTURES = os.path.join(SIL_DIR, "fixtures")
REASONING_CSV = os.path.join(SKILL_DIR, "data", "ui-reasoning.csv")
LEDGER = os.path.join(SIL_DIR, "reasoning-ledger.jsonl")
LOOP_ID = "ui-ux-pro-max-reasoning"
# Loop-private repo (kernel commits here only when a rung permits auto-apply; at
# ONE_CLICK it never does). Kept out of any user project repo.
LOOP_REPO = os.path.expanduser("~/.claude/cache/ui-ux-pro-max/loop-config")
BRANCH = "ui-ux-pro-max-loop/reasoning"
# Real persisted design-system project records (JSONL, one {ts, rule_id, fields,
# overrides} per persisted project) — the realized corpus measure() prefers over
# the synthetic fixtures once persist_design_system() starts appending here.
# Absent today -> fixture fallback. Lives beside the loop state, out of any project.
REAL_PROJECTS = os.path.join(os.path.dirname(LOOP_REPO), "persisted-projects.jsonl")

WINDOW_DAYS = 2
ANTI_OSC_DAYS = 7
# Minimum override-rate REDUCTION (absolute, fraction in [0,1]) to KEEP. Override
# rate is lower-is-better, so the loop runs higher_is_better=False and a positive
# margin demands a real drop, not noise.
MARGIN = 0.05

# A reasoning rule's field is a propose candidate when overridden in >= this
# fraction of that rule's saved projects.
OVERRIDE_THRESHOLD = 0.5

# The generated design-system fields the corpus tracks (mirrors the dict
# `_apply_reasoning` produces in scripts/design_system.py: pattern / style /
# color_mood / typography_mood / key_effects). Each maps to a ui-reasoning.csv
# column so a candidate edit targets a concrete cell.
_FIELD_TO_COLUMN = {
    "pattern": "Recommended_Pattern",
    "style": "Style_Priority",
    "color_mood": "Color_Mood",
    "typography_mood": "Typography_Mood",
    "key_effects": "Key_Effects",
}


# ---- fixture corpus (the override-rate signal) --------------------------


def _load_projects() -> list[dict]:
    """Load synthetic saved-project fixtures. Fail-open: absent dir -> []."""
    out: list[dict] = []
    if not os.path.isdir(FIXTURES):
        return out
    for name in sorted(os.listdir(FIXTURES)):
        if not (name.startswith("project_") and name.endswith(".json")):
            continue
        path = os.path.join(FIXTURES, name)
        try:
            with open(path) as f:
                out.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _ts_dt(ts) -> datetime | None:
    """Parse an ISO-8601 timestamp to an aware datetime; None if unparseable.
    Normalizes a trailing 'Z' to '+00:00' so the kernel's `+00:00` row.ts and a
    'Z'-suffixed persisted-project ts compare by instant, not by raw string."""
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


def _read_real_projects() -> list[dict]:
    """Real persisted-project records (JSONL at REAL_PROJECTS), one
    {ts, rule_id, fields, overrides} per persisted project. `measure()` splits
    these into pre/post-apply windows by ts. Fail-open: an absent file or malformed
    rows -> dropped, so the caller cleanly falls back to the fixture corpus."""
    if not os.path.exists(REAL_PROJECTS):
        return []
    out: list[dict] = []
    with open(REAL_PROJECTS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _project_override_rate(
    project: dict, suppressed_fields: set[str] | None = None
) -> float:
    """Override-rate for one project = overridden fields / generated fields.

    `suppressed_fields` are fields whose default the candidate rule fixes so they
    would no longer be overridden — they are removed from the override count."""
    fields = project.get("fields") or {}
    if not fields:
        return 0.0
    overrides = set((project.get("overrides") or {}).keys())
    if suppressed_fields:
        overrides = overrides - suppressed_fields
    return len(overrides) / len(fields)


def corpus_override_rate(
    projects: list[dict],
    *,
    rule_id: str | None = None,
    suppressed_field: str | None = None,
) -> float:
    """Mean override-rate across the corpus.

    When (`rule_id`, `suppressed_field`) is given, that field is treated as fixed
    for projects generated from `rule_id` (the candidate's projected effect)."""
    if not projects:
        return 0.0
    total = 0.0
    for p in projects:
        suppress = None
        if (
            rule_id is not None
            and str(p.get("rule_id")) == str(rule_id)
            and suppressed_field
        ):
            suppress = {suppressed_field}
        total += _project_override_rate(p, suppress)
    return total / len(projects)


def _field_override_stats(projects: list[dict]) -> dict[tuple[str, str], dict]:
    """Per (rule_id, field) override stats over the corpus.

    Returns { (rule_id, field): {"n": projects, "overridden": count,
    "values": {override_value: count}} }."""
    stats: dict[tuple[str, str], dict] = {}
    for p in projects:
        rid = str(p.get("rule_id"))
        fields = p.get("fields") or {}
        overrides = p.get("overrides") or {}
        for field in fields:
            if field not in _FIELD_TO_COLUMN:
                continue
            key = (rid, field)
            slot = stats.setdefault(key, {"n": 0, "overridden": 0, "values": {}})
            slot["n"] += 1
            if field in overrides:
                slot["overridden"] += 1
                val = overrides[field]
                slot["values"][val] = slot["values"].get(val, 0) + 1
    return stats


# ---- reasoning CSV access -----------------------------------------------


def _load_rules() -> list[dict]:
    """Load ui-reasoning.csv rows. Fail-open: absent file -> []."""
    if not os.path.exists(REASONING_CSV):
        return []
    with open(REASONING_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _rule_by_id(rules: list[dict], rule_id: str) -> dict | None:
    for r in rules:
        if str(r.get("No")) == str(rule_id):
            return r
    return None


def _render_csv_with_edit(
    rules: list[dict], rule_id: str, column: str, value: str
) -> str:
    """Build the proposed full-file CSV text with one cell edited (a human reviews
    and applies it). Returns the complete file body; does NOT write to disk."""
    if not rules:
        return ""
    fieldnames = list(rules[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rules:
        row = dict(r)
        if str(row.get("No")) == str(rule_id):
            row[column] = value
        writer.writerow(row)
    return buf.getvalue()


# ---- the adapter --------------------------------------------------------


class UiUxAdapter:
    """propose() / execute() / measure() per self-learning.md §2.3."""

    def __init__(self, projects: list[dict] | None = None):
        self._projects = projects

    def _projects_or_load(self) -> list[dict]:
        return self._projects if self._projects is not None else _load_projects()

    def propose(self) -> Candidate | None:
        projects = self._projects_or_load()
        rules = _load_rules()
        if not projects or not rules:
            return None
        stats = _field_override_stats(projects)
        # Pick the (rule, field) with the highest override fraction at or above
        # threshold; deterministic tie-break by (rule_id, field).
        best: tuple[float, str, str] | None = None
        for (rid, field), slot in sorted(stats.items()):
            if slot["n"] == 0:
                continue
            frac = slot["overridden"] / slot["n"]
            if frac < OVERRIDE_THRESHOLD:
                continue
            if best is None or frac > best[0]:
                best = (frac, rid, field)
        if best is None:
            return None
        _frac, rid, field = best
        if _rule_by_id(rules, rid) is None:
            return None
        # The durable default users converged on = the most common override value.
        values = stats[(rid, field)]["values"]
        new_value = max(sorted(values.items()), key=lambda kv: kv[1])[0]
        return self._rule_candidate(rules, rid, field, new_value)

    def _rule_candidate(
        self, rules: list[dict], rule_id: str, field: str, new_value: str
    ) -> Candidate:
        column = _FIELD_TO_COLUMN[field]
        new_text = _render_csv_with_edit(rules, rule_id, column, new_value)
        return Candidate(
            artifact_path="data/ui-reasoning.csv",
            change_summary=(
                f"rule {rule_id}: set {column} default -> '{new_value}' "
                f"(field '{field}' overridden in >= {int(OVERRIDE_THRESHOLD * 100)}% of projects)"
            ),
            change_signature=f"uux-reasoning:{rule_id}",
            artifact_class=ArtifactClass.PROSE_RULE,
            new_text=new_text,
            meta={
                "rule_id": rule_id,
                "field": field,
                "column": column,
                "new_value": new_value,
            },
        )

    def _score(self, cand: Candidate) -> RunResult:
        projects = self._projects_or_load()
        rules = _load_rules()
        rid = cand.meta["rule_id"]
        field = cand.meta["field"]
        column = cand.meta["column"]
        new_value = cand.meta["new_value"]

        base_rate = corpus_override_rate(projects)
        proj_rate = corpus_override_rate(projects, rule_id=rid, suppressed_field=field)

        # Gates. schema_valid: the edited rule still has every column and its
        # Decision_Rules JSON still parses; no_empty_field: the new default is
        # non-empty and no generated field on the rule becomes blank.
        rule = _rule_by_id(rules, rid)
        schema_valid = False
        no_empty_field = False
        if rule is not None:
            edited = dict(rule)
            edited[column] = new_value
            cols_ok = all(
                c in edited and edited.get(c) not in (None,) for c in rule.keys()
            )
            try:
                json.loads(edited.get("Decision_Rules", "{}") or "{}")
                json_ok = True
            except json.JSONDecodeError:
                json_ok = False
            schema_valid = cols_ok and json_ok
            tracked_cols = [_FIELD_TO_COLUMN[fn] for fn in _FIELD_TO_COLUMN]
            no_empty_field = bool(new_value.strip()) and all(
                str(edited.get(c, "")).strip() for c in tracked_cols
            )
        gates = {"schema_valid": schema_valid, "no_empty_field": no_empty_field}
        return RunResult(
            metric=proj_rate,
            gates=gates,
            deferred=True,  # realized override-rate needs new real projects
            detail={
                "baseline": base_rate,
                "projected": proj_rate,
                "rule_id": rid,
                "field": field,
                "n_projects": len(projects),
            },
        )

    def execute(self, cand: Candidate) -> RunResult:
        return self._score(cand)

    def measure(self, row) -> RunResult:
        # Realized signal: a REAL before/after on the override-rate of THIS rule's
        # persisted projects. The kernel compares `row.baseline_metric` (frozen at
        # execute() from the fixture corpus) against the metric returned here, so to
        # keep the comparison meaningful we express the realized change ON THE
        # BASELINE'S SCALE. Override-rate is lower-is-better (higher_is_better=False),
        # so decide()'s gain is (baseline - metric); setting
        #     metric = baseline - (pre_rate - post_rate)
        # makes that gain exactly (pre_rate - post_rate) — the fixture baseline
        # cancels, and the decision depends only on whether real projects override
        # this rule LESS after the default was changed than before. This observes the
        # actual realized override-rate, so no field-suppression simulation (and no
        # corpus-dependent field re-derivation) is needed on the real path.
        #
        # Needs real projects for this rule on BOTH sides of the apply boundary
        # (`row.ts`). Otherwise fall back to the deterministic fixture re-check,
        # which matches the fixture baseline (gain 0 -> ASK) and preserves today's
        # behavior exactly.
        rules = _load_rules()
        rid = row.change_signature.split(":", 1)[-1]
        rule = _rule_by_id(rules, rid)
        since_dt = _ts_dt(getattr(row, "ts", None))
        real_rule = [
            p
            for p in (_read_real_projects() if since_dt else [])
            if str(p.get("rule_id")) == str(rid) and _ts_dt(p.get("ts")) is not None
        ]
        pre = [p for p in real_rule if _ts_dt(p.get("ts")) < since_dt]
        post = [p for p in real_rule if _ts_dt(p.get("ts")) >= since_dt]

        if pre and post:
            pre_rate = corpus_override_rate(pre)
            post_rate = corpus_override_rate(post)
            base = row.baseline_metric if row.baseline_metric is not None else 0.0
            metric = base - (pre_rate - post_rate)
            gates = {
                "schema_valid": rule is not None,
                "no_empty_field": rule is not None,
            }
            return RunResult(
                metric=metric,
                gates=gates,
                deferred=False,
                detail={
                    "source": "real",
                    "pre_rate": pre_rate,
                    "post_rate": post_rate,
                    "rule_id": rid,
                    "n_pre": len(pre),
                    "n_post": len(post),
                },
            )

        # Deterministic fixture re-check (matches the fixture-derived baseline).
        projects = self._projects_or_load()
        stats = _field_override_stats(projects)
        field = None
        best_frac = -1.0
        for (r, f), slot in sorted(stats.items()):
            if r != str(rid) or slot["n"] == 0:
                continue
            frac = slot["overridden"] / slot["n"]
            if frac > best_frac:
                best_frac, field = frac, f
        base_rate = corpus_override_rate(projects)
        proj_rate = (
            corpus_override_rate(projects, rule_id=rid, suppressed_field=field)
            if field
            else base_rate
        )
        gates = {
            "schema_valid": rule is not None,
            "no_empty_field": rule is not None,
        }
        return RunResult(
            metric=proj_rate,
            gates=gates,
            deferred=False,
            detail={
                "source": "fixture-fallback",
                "baseline": base_rate,
                "projected": proj_rate,
                "rule_id": rid,
                "field": field,
                "n_projects": len(projects),
            },
        )


# ---- entry points -------------------------------------------------------


def _make_loop(ledger_path: str, rung: Rung, repo: str) -> Loop:
    return Loop(
        LOOP_ID,
        Ledger(ledger_path),
        rung,
        repo=repo,
        branch=BRANCH,
        higher_is_better=False,  # override-rate: lower is better
        margin=MARGIN,
        window_days=WINDOW_DAYS,
        anti_oscillation_days=ANTI_OSC_DAYS,
    )


def cmd_propose(a) -> int:
    now = datetime.now(timezone.utc)
    adapter = UiUxAdapter()
    if a.dry_run:
        # Dry-run computes the metric/proposal by calling the adapter directly —
        # it never instantiates the kernel Loop, so it cannot touch the real
        # ledger, the reasoning CSV, or any git repo.
        cand = adapter.propose()
        if cand is None:
            base = corpus_override_rate(_load_projects())
            print(
                "[dry-run] no proposal: no reasoning rule overridden past "
                f"threshold {OVERRIDE_THRESHOLD:.0%}; corpus override-rate={base:.2f} "
                "(rung=DRY_RUN, ONE_CLICK in prod — never auto-applies)"
            )
            return 0
        result = adapter.execute(cand)
        print(
            f"[dry-run] PROPOSAL {cand.change_signature}: {cand.change_summary} "
            f"| metric(override-rate)={result.metric:.2f} "
            f"baseline={result.detail['baseline']:.2f} "
            f"gates={result.gates} "
            "(PROSE_RULE/ONE_CLICK — proposal logged, human applies; not written)"
        )
        return 0

    # Real iteration: ONE_CLICK rung -> the loop logs an ASK proposal row and never
    # writes the reasoning CSV (rungs.may_auto_apply == False for PROSE_RULE).
    loop = _make_loop(LEDGER, Rung.ONE_CLICK, repo=LOOP_REPO)
    row = loop.propose_iteration(adapter, now)
    if row is None:
        print("propose: nothing to try (or a pending experiment is open)")
        return 0
    print(
        f"propose: {row.decision} {row.change_signature} "
        f"metric={row.candidate_metric} note='{row.note}' (logged to {LEDGER})"
    )
    return 0


def cmd_confirm(a) -> int:
    now = datetime.now(timezone.utc)
    adapter = UiUxAdapter()
    loop = _make_loop(LEDGER, Rung.ONE_CLICK, repo=LOOP_REPO)
    rows = loop.confirm_pending(adapter, now)
    if not rows:
        print("confirm: no pending experiments past their window")
        return 0
    for r in rows:
        print(f"confirm: {r.decision} {r.change_signature} note='{r.note}'")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ui-ux-pro-max_loop",
        description="ui-ux-pro-max design-system reasoning sil adapter (PROSE_RULE / ONE_CLICK)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("propose", help="one PROPOSE iteration")
    pr.add_argument(
        "--dry-run",
        action="store_true",
        help="simulate only: call the adapter directly, never touch the ledger/CSV/repo",
    )
    pr.set_defaults(fn=cmd_propose)
    cf = sub.add_parser("confirm", help="resolve pending experiments past their window")
    cf.set_defaults(fn=cmd_confirm)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
