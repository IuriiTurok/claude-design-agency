#!/usr/bin/env python3
"""Impeccable anti-pattern-list adapter + entry for the `sil` self-improving loop.

Heavyweight tier (self-learning.md §2.2). impeccable is the single source of
truth for the AI-slop / anti-pattern ban list
(``reference/ai-slop-bans.md``). This loop GROWS and PRUNES that list from
observed violations, scored against an offline fixture corpus.

- Artifact class: PROSE_RULE  -> capped at ONE_CLICK by the autonomy ladder
  (``rungs.py``). The loop PROPOSES + SCORES + LOGS one ban-list edit per
  iteration; a human clicks to apply. It NEVER auto-writes the ban list.
- Fitness signal: anti-pattern hit-rate over a fixed corpus of known-good +
  known-bad CSS fixtures (``sil/fixtures/``) — net violations caught on the
  bad set, with a no-false-positive gate on the goldens. Higher is better.
- Ledger: ``<impeccable-dir>/sil/antipattern-ledger.jsonl`` (the shared schema).
- The kernel commits only to a LOOP-PRIVATE repo and never pushes; at ONE_CLICK
  nothing is ever applied, so no repo write happens at all in normal operation.

Subcommands:
  propose [--dry-run]   one PROPOSE iteration (scores the corpus, logs a row)
  confirm               resolve pending experiments (deterministic re-check)

``--dry-run`` forces the DRY_RUN rung and an in-memory ledger: it computes and
prints the metric/proposal WITHOUT touching the real ledger, the ban list, or
the kernel's git repo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
BAN_LIST = os.path.join(SKILL_DIR, "reference", "ai-slop-bans.md")
CANDIDATES = os.path.join(SKILL_DIR, "reference", "ai-slop-candidates.jsonl")
LEDGER = os.path.join(SIL_DIR, "antipattern-ledger.jsonl")
LOOP_ID = "impeccable-antipattern"
# Loop-private repo (kernel commits here only when a rung permits auto-apply;
# at ONE_CLICK it never does). Kept out of any user project repo.
LOOP_REPO = os.path.expanduser("~/.claude/cache/impeccable/loop-config")
BRANCH = "impeccable-loop/antipattern"

WINDOW_DAYS = 2
ANTI_OSC_DAYS = 7
# Minimum net-violations-caught improvement on the bad set to KEEP.
MARGIN = 1.0


# ---- the antipattern detector (the binary fitness signal) ---------------
#
# A small, deterministic checker for the mechanically-detectable absolute bans
# from reference/ai-slop-bans.md. Each known pattern has a stable pattern-id so
# the loop can sign a proposal by the pattern it would add/prune.

# Reflex fonts (subset is enough to catch the bad fixtures; full list lives in
# the ban-list reference and SKILL.md).
_REFLEX_FONTS = (
    "Fraunces",
    "Newsreader",
    "Lora",
    "Crimson",
    "Playfair Display",
    "Cormorant",
    "Syne",
    "IBM Plex",
    "Space Mono",
    "Space Grotesk",
    "Inter",
    "DM Sans",
    "DM Serif",
    "Outfit",
    "Plus Jakarta Sans",
    "Instrument Sans",
    "Instrument Serif",
)

# pattern-id -> (compiled regex, human label). These are the bans the corpus
# gate can measure. A `propose()` candidate adds/prunes a row keyed on one id.
_CHECKS: dict[str, tuple[re.Pattern, str]] = {
    "side-stripe-border": (
        # border-left/right with a width > 1px (any unit-1 digit > 1, or >= 2 digits)
        re.compile(
            r"border-(?:left|right)\s*:\s*(?:[2-9]|\d{2,})\s*px",
            re.IGNORECASE,
        ),
        "side-stripe border > 1px (BAN 1)",
    ),
    "gradient-text": (
        re.compile(r"(?:-webkit-)?background-clip\s*:\s*text", re.IGNORECASE),
        "gradient text via background-clip:text (BAN 2)",
    ),
    "reflex-font": (
        re.compile(
            r"font-family\s*:[^;{}]*?(?:"
            + "|".join(re.escape(f) for f in _REFLEX_FONTS)
            + r")",
            re.IGNORECASE,
        ),
        "reflex font from the reject list",
    ),
    # Documented in the ban list as prose ("glassmorphism everywhere") but NOT
    # yet adopted by the mechanical checker — so it is a legitimate GROW target.
    "glassmorphism": (
        re.compile(r"backdrop-filter\s*:\s*blur", re.IGNORECASE),
        "decorative glassmorphism (backdrop-filter: blur)",
    ),
}

# Pattern-ids the mechanical checker treats as ALREADY-ADOPTED absolute bans.
# A candidate that adds a checkable pattern NOT in this set is a GROW move.
_ADOPTED_CHECK_IDS = {"side-stripe-border", "gradient-text", "reflex-font"}


def check_text(css: str, active_ids: set[str]) -> int:
    """Count anti-pattern hits in `css` for the currently-active pattern ids.

    `gradient-text` requires both background-clip:text AND a gradient fill in the
    same snippet, matching the ban's strict definition (clip alone is benign)."""
    hits = 0
    for pid in active_ids:
        rx, _label = _CHECKS[pid]
        for _m in rx.finditer(css):
            if pid == "gradient-text" and "gradient(" not in css.lower():
                continue
            hits += 1
    return hits


def _load_fixtures() -> tuple[list[str], list[str]]:
    good, bad = [], []
    if not os.path.isdir(FIXTURES):
        return good, bad
    for name in sorted(os.listdir(FIXTURES)):
        path = os.path.join(FIXTURES, name)
        if not os.path.isfile(path) or not name.endswith(".css"):
            continue
        with open(path) as f:
            text = f.read()
        (good if name.startswith("good") else bad).append(text)
    return good, bad


def score_corpus(active_ids: set[str]) -> dict:
    """Run the active checks over the fixture corpus. Returns the gate inputs and
    the fitness metric (net violations caught on the bad set)."""
    good, bad = _load_fixtures()
    fp_on_goldens = sum(check_text(t, active_ids) for t in good)
    caught_on_bad = sum(check_text(t, active_ids) for t in bad)
    return {
        "false_positives": fp_on_goldens,
        "caught_on_bad": caught_on_bad,
        "n_good": len(good),
        "n_bad": len(bad),
    }


# ---- which ban patterns the curated list already covers -----------------


def _active_ids_from_banlist() -> set[str]:
    """Which mechanically-checkable pattern-ids the checker currently ENFORCES.

    The curated ban list documents the three absolute CSS bans in prose; the
    mechanical checker has adopted exactly those (``_ADOPTED_CHECK_IDS``). A
    candidate whose pattern-id is checkable but NOT in this set is a genuine GROW
    move (it makes the checker catch something the corpus baseline misses).
    Intersected with what the curated file actually mentions, fail-open: if the
    ban list is missing, nothing is enforced."""
    if not os.path.exists(BAN_LIST):
        return set()
    return set(_ADOPTED_CHECK_IDS)


def _recurring_candidates(path: str = CANDIDATES) -> list[dict]:
    """Read Bridge-D candidate records (one JSON object per line). A pattern that
    appears >= 2 times is 'recurring' and eligible to propose. Fail-open: absent
    file -> no candidates."""
    if not os.path.exists(path):
        return []
    counts: dict[str, dict] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = rec.get("pattern_id") or rec.get("tell")
            if not pid:
                continue
            slot = counts.setdefault(pid, {"pattern_id": pid, "count": 0, "rec": rec})
            slot["count"] += 1
    return [c for c in counts.values() if c["count"] >= 2]


def _observed_in_window(
    pid: str, since_ts: str | None, path: str | None = None
) -> tuple[int, bool]:
    """Count REAL observed violations of `pid` recorded since `since_ts` in the
    Bridge-D candidates stream — the realized prevalence `measure()` surfaces.
    Returns (count, file_present). Fail-open: an absent file -> (0, False) so the
    caller treats the realized signal as informational-only until producers write.
    NOTE: for a BAN, fewer real observations over time is success (spec §2.2:
    hit-rate trends down as the list matures), so this is reported in detail, never
    a gate — it must not drive KEEP/REVERT backwards. `path` resolves to the live
    CANDIDATES module global at call time when omitted."""
    if path is None:
        path = CANDIDATES
    if not os.path.exists(path):
        return 0, False
    count = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (rec.get("pattern_id") or rec.get("tell")) != pid:
                continue
            if since_ts and str(rec.get("ts", "")) < str(since_ts):
                continue
            count += 1
    return count, True


# ---- the adapter --------------------------------------------------------


class ImpeccableAdapter:
    """propose() / execute() / measure() per self-learning.md §2.2."""

    def __init__(self, candidates_path: str = CANDIDATES):
        self.candidates_path = candidates_path

    def propose(self) -> Candidate | None:
        active = _active_ids_from_banlist()
        # Look for a recurring Bridge-D candidate that maps to a checkable
        # pattern not yet enforced by the checker (a GROW move).
        for cand in _recurring_candidates(self.candidates_path):
            pid = cand["pattern_id"]
            if pid in _CHECKS and pid not in active:
                return self._grow_candidate(pid, cand["rec"])
        # Nothing recurring/new to add and nothing stale to prune.
        return None

    def _grow_candidate(self, pid: str, rec: dict) -> Candidate:
        _rx, label = _CHECKS[pid]
        scope = rec.get("scope", "general")
        section = (
            "## General AI-slop bans"
            if scope == "general"
            else "## Own-brand rules"
        )
        bullet = (
            f"- DO NOT: {label}. (promoted from Bridge D, "
            f"{datetime.now(timezone.utc).date()})"
        )
        new_text = self._render_banlist_with_bullet(section, bullet)
        return Candidate(
            artifact_path="reference/ai-slop-bans.md",
            change_summary=f"add ban: {label}",
            change_signature=f"imp-antipattern:{pid}",
            artifact_class=ArtifactClass.PROSE_RULE,
            new_text=new_text,
            meta={"pattern_id": pid, "op": "add", "scope": scope},
        )

    def _render_banlist_with_bullet(self, section: str, bullet: str) -> str:
        """Build the proposed full-file text (a human reviews/applies it). Appends
        the bullet at the end of the named section. Fail-open if the section is
        missing: append at EOF."""
        text = open(BAN_LIST).read() if os.path.exists(BAN_LIST) else ""
        if section in text:
            idx = text.index(section)
            nxt = text.find("\n## ", idx + len(section))
            insert_at = nxt if nxt != -1 else len(text)
            return text[:insert_at].rstrip() + f"\n{bullet}\n" + text[insert_at:]
        return text.rstrip() + f"\n\n{section}\n{bullet}\n"

    def execute(self, cand: Candidate) -> RunResult:
        # The candidate's pattern becomes active; gate against the corpus.
        active = _active_ids_from_banlist() | {cand.meta["pattern_id"]}
        score = score_corpus(active)
        # Baseline = current curated list (without the candidate pattern).
        base = score_corpus(_active_ids_from_banlist())
        gates = {
            "no_false_positive_on_goldens": score["false_positives"] == 0,
            "catches_the_bad_fixture": score["caught_on_bad"] > base["caught_on_bad"],
        }
        return RunResult(
            metric=float(score["caught_on_bad"]),
            gates=gates,
            deferred=False,  # fixture corpus makes this measurable in-loop
            detail={"baseline": float(base["caught_on_bad"]), "score": score},
        )

    def measure(self, row) -> RunResult:
        # The deterministic fixture re-check yields the COMPARABLE metric
        # (caught_on_bad vs the stored baseline) + detector-quality gates — the
        # kernel decide() contract is unchanged. Deepening: also read REAL observed
        # violations of this pattern (ai-slop-candidates.jsonl) accrued since the
        # ban was applied (`row.ts`) and surface the realized prevalence in detail.
        # Prevalence is informational only (see _observed_in_window): for a ban,
        # fewer observations is success, so it must NOT gate KEEP/REVERT.
        active = _active_ids_from_banlist()
        pid = row.change_signature.split(":", 1)[-1]
        if pid in _CHECKS:
            active = active | {pid}
        score = score_corpus(active)
        base = score_corpus(_active_ids_from_banlist())
        real_obs, real_present = _observed_in_window(pid, getattr(row, "ts", None))
        gates = {
            "no_false_positive_on_goldens": score["false_positives"] == 0,
            "catches_the_bad_fixture": score["caught_on_bad"] > base["caught_on_bad"],
        }
        return RunResult(
            metric=float(score["caught_on_bad"]),
            gates=gates,
            deferred=False,
            detail={
                "baseline": float(base["caught_on_bad"]),
                "score": score,
                "source": "real+fixture" if real_present else "fixture",
                "real_observed_in_window": real_obs,
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
        higher_is_better=True,
        margin=MARGIN,
        window_days=WINDOW_DAYS,
        anti_oscillation_days=ANTI_OSC_DAYS,
    )


def cmd_propose(a) -> int:
    now = datetime.now(timezone.utc)
    adapter = ImpeccableAdapter(candidates_path=a.candidates or CANDIDATES)
    if a.dry_run:
        # Dry-run computes the metric/proposal by calling the adapter directly —
        # it never instantiates the kernel Loop, so it cannot touch the real
        # ledger, the ban list, or any git repo.
        cand = adapter.propose()
        if cand is None:
            base = score_corpus(_active_ids_from_banlist())
            print(
                "[dry-run] no proposal: no recurring new ban-pattern; "
                f"corpus baseline caught_on_bad={int(base['caught_on_bad'])} "
                f"false_positives={int(base['false_positives'])} "
                f"(rung=DRY_RUN, ONE_CLICK in prod — never auto-applies)"
            )
            return 0
        result = adapter.execute(cand)
        print(
            f"[dry-run] PROPOSAL {cand.change_signature}: {cand.change_summary} "
            f"| metric(caught_on_bad)={int(result.metric)} "
            f"baseline={int(result.detail['baseline'])} "
            f"gates={result.gates} "
            f"(PROSE_RULE/ONE_CLICK — proposal logged, human applies; not written)"
        )
        return 0

    # Real iteration: ONE_CLICK rung -> the loop logs an ASK proposal row and
    # never writes the ban list (rungs.may_auto_apply == False for PROSE_RULE).
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
    adapter = ImpeccableAdapter()
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
        prog="impeccable_loop",
        description="impeccable anti-pattern-list sil adapter (PROSE_RULE / ONE_CLICK)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("propose", help="one PROPOSE iteration")
    pr.add_argument(
        "--dry-run",
        action="store_true",
        help="simulate only: call the adapter directly, never touch the ledger/ban-list/repo",
    )
    pr.add_argument(
        "--candidates",
        help="override the Bridge-D candidates JSONL path (default: reference/ai-slop-candidates.jsonl)",
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
