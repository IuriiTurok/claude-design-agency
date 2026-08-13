#!/usr/bin/env python3
"""UserPromptSubmit hook for the design-agency plugin.

Classifies a prompt for design/branding intent and, when it fires, emits a
machine-readable <design-agency-decision> block instructing the parent to
invoke the design-agency:design-agency-routing skill.

Evaluation order (first hit wins):
  a. Hard silent opt-outs (#noagency/#nodesign, env, slash command, too short,
     continuation openers).
  b. Per-repo .claude/design-agency.json (disabled / ask_threshold / extra_signals).
  c. Session-engaged marker (already routed this session) -> silent.
  d. Brandbook auto-engage: DesignAgencyAgent/master_agent.md found walking up.
  e. #agency override -> engage.
  f. Heuristic classifier -> engage/ask/silent.

Never crashes the prompt flow: main() is wrapped in try/except and exits 0
silently on any error.
"""

import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path(os.path.expanduser("~/.claude/cache/design-agency"))
ENGAGED_DIR = CACHE_DIR / "engaged"
AUDIT_LOG = CACHE_DIR / "audit.jsonl"
AUDIT_ROTATE_BYTES = 5 * 1024 * 1024
ENGAGED_RETAIN_SEC = 7 * 86400

DEFAULT_ASK_THRESHOLD = 0.55
PROJECT_CONFIG_FILENAME = ".claude/design-agency.json"

CONTINUATION_OPENERS = (
    "yes",
    "ok",
    "okay",
    "go ahead",
    "continue",
    "do it",
    "proceed",
    "sure",
    "thanks",
    "please do",
    "looks good",
    "lgtm",
    "approved",
)

CREATION_VERBS = re.compile(
    r"\b(design|create|make|build|redesign|restyle|polish|improve|iterate)\b", re.I
)
DELIVERABLE_PATH = re.compile(r"ui/.*\.html|\.svg|brand_book|design_system", re.I)
# Word-boundary matching: bare substring checks misfire ("ci" in "social",
# "test" in "testimonial"). Penalty needs >=2 DISTINCT terms, so a single
# ambiguous word ("refactor the landing page") never suppresses by itself.
ENGINEERING_RE = re.compile(
    r"\b(apis?|database|db|deploy(?:ment)?|ci|cd|tests?|bugs?|migrations?|"
    r"backend|docker|kubernetes|endpoints?|refactor|lint(?:er)?|schema|sdk|"
    r"server|pull request|type-?check)\b",
    re.I,
)
THEORY_OPENERS = ("what is", "why does", "explain", "how does")

# (phrase, engagement_type) — phrase match contributes a TIER_A base score.
TIER_A_SIGNALS = [
    ("brand identity", "brand_project"),
    ("brand book", "brand_project"),
    ("brandbook", "brand_project"),
    ("rebrand", "brand_project"),
    ("visual identity", "brand_project"),
    ("design system", "deliverable_iteration"),
    ("style guide", "deliverable_iteration"),
    ("style directive", "deliverable_iteration"),
    ("mascot", "character_3d"),
    ("character design", "character_3d"),
    ("pose sheet", "character_3d"),
    ("brand kit", "brand_project"),
]
TIER_A_SCORE = 0.85

TIER_B_SIGNALS = [
    ("landing page", "prototype"),
    ("hero section", "prototype"),
    ("ui mockup", "prototype"),
    ("wireframe", "prototype"),
    ("interactive prototype", "prototype"),
    ("favicon", "asset"),
    ("social card", "asset"),
    ("og image", "asset"),
    ("poster", "asset"),
    ("color palette", "deliverable_iteration"),
    ("colour palette", "deliverable_iteration"),
    ("font pairing", "deliverable_iteration"),
    ("icon set", "asset"),
    ("brand presentation", "brand_project"),
    ("brand proposal", "brand_project"),
    ("moodboard", "deliverable_iteration"),
    ("mood board", "deliverable_iteration"),
]
TIER_B_SCORE = 0.60


def load_project_config(start_dir):
    """Walk up from start_dir for .claude/design-agency.json; first hit wins."""
    try:
        cur = Path(start_dir or os.getcwd()).resolve()
    except (OSError, ValueError):
        return {}
    home = Path(os.path.expanduser("~"))
    while True:
        candidate = cur / PROJECT_CONFIG_FILENAME
        try:
            with open(candidate) as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                cfg["_source"] = str(candidate)
                return cfg
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            pass
        parent = cur.parent
        if parent == cur or cur == home:
            break
        cur = parent
    return {}


def find_brandbook_agent(start_dir):
    """Walk up from start_dir for DesignAgencyAgent/master_agent.md; return the
    DesignAgencyAgent dir (Path) or None."""
    try:
        cur = Path(start_dir or os.getcwd()).resolve()
    except (OSError, ValueError):
        return None
    while True:
        try:
            marker = cur / "DesignAgencyAgent" / "master_agent.md"
            if marker.is_file():
                return cur / "DesignAgencyAgent"
        except OSError:
            pass
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def prune_engaged_markers():
    """Opportunistically delete engaged-marker files older than 7 days."""
    try:
        cutoff = time.time() - ENGAGED_RETAIN_SEC
        for p in ENGAGED_DIR.glob("*"):
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink()
            except OSError:
                pass
    except OSError:
        pass


def audit_rotate_if_needed():
    try:
        if AUDIT_LOG.exists() and AUDIT_LOG.stat().st_size >= AUDIT_ROTATE_BYTES:
            AUDIT_LOG.rename(str(AUDIT_LOG) + ".1")
    except OSError:
        pass


def audit_append(record):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        audit_rotate_if_needed()
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass


def classify_heuristic(prompt, ask_threshold, extra_signals):
    """Additive heuristic scorer. Returns (band, score, engagement_type,
    matched_signals, reason) where band is 'ask' or 'none'."""
    lower = prompt.lower()
    matched = []
    score = 0.0

    best_tier = None  # "A" or "B" — highest tier sets the engagement_type
    engagement_type = "unknown"

    has_creation_verb = bool(CREATION_VERBS.search(prompt))

    # TIER_A phrases.
    for phrase, etype in TIER_A_SIGNALS:
        if phrase in lower:
            matched.append(phrase)
            score += TIER_A_SCORE
            if best_tier is None:
                best_tier = "A"
                engagement_type = etype
    # "logo" only when a creation verb is also present.
    if "logo" in lower and has_creation_verb:
        matched.append("logo")
        score += TIER_A_SCORE
        if best_tier is None:
            best_tier = "A"
            engagement_type = "asset"

    # TIER_B phrases.
    for phrase, etype in TIER_B_SIGNALS:
        if phrase in lower:
            matched.append(phrase)
            score += TIER_B_SCORE
            if best_tier is None:
                best_tier = "B"
                engagement_type = etype

    # Project extra_signals: list of {"pattern": regex, "score": float}.
    for sig in extra_signals or []:
        if not isinstance(sig, dict):
            continue
        pattern = sig.get("pattern")
        if not pattern:
            continue
        try:
            if re.search(pattern, prompt, re.I):
                matched.append(f"extra:{pattern}")
                score += float(sig.get("score", 0.0))
        except (re.error, TypeError, ValueError):
            continue

    # Modifiers.
    if has_creation_verb:
        score += 0.10
        matched.append("creation_verb")
    if DELIVERABLE_PATH.search(prompt):
        score += 0.15
        matched.append("deliverable_path")
    if len({m.lower() for m in ENGINEERING_RE.findall(lower)}) >= 2:
        score -= 0.30
        matched.append("engineering_dominant")
    if lower.strip().startswith(THEORY_OPENERS) and not has_creation_verb:
        score -= 0.40
        matched.append("theory_question")

    score = max(0.0, min(1.0, score))

    if score >= ask_threshold:
        reason = (
            f"design intent score {round(score, 2)} >= ask threshold "
            f"{round(ask_threshold, 2)} from signals: "
            f"{', '.join(matched) if matched else 'none'}"
        )
        return "ask", score, engagement_type, matched, reason
    return "none", score, engagement_type, matched, "below ask threshold"


def engagement_from_heuristics(prompt):
    """Best-effort engagement_type guess used by the brandbook auto-engage path,
    which skips scoring thresholds. Returns a type or 'unknown'."""
    lower = prompt.lower()
    has_creation_verb = bool(CREATION_VERBS.search(prompt))
    for phrase, etype in TIER_A_SIGNALS:
        if phrase in lower:
            return etype
    if "logo" in lower and has_creation_verb:
        return "asset"
    for phrase, etype in TIER_B_SIGNALS:
        if phrase in lower:
            return etype
    return "unknown"


def emit(decision, msg_extra, cwd):
    """Touch the engaged marker, append audit, print the additionalContext block."""
    session_id = decision.get("_session_id")
    decision_public = {k: v for k, v in decision.items() if not k.startswith("_")}

    # Side effects: engaged marker + audit line.
    try:
        ENGAGED_DIR.mkdir(parents=True, exist_ok=True)
        if session_id:
            (ENGAGED_DIR / str(session_id)).touch()
    except OSError:
        pass

    audit_append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "decision_id": decision_public.get("decision_id"),
            "band": decision_public.get("band"),
            "confidence": decision_public.get("confidence"),
            "engagement_type": decision_public.get("engagement_type"),
            "cwd": cwd,
        }
    )

    msg = (
        "<design-agency-decision>\n"
        + json.dumps(decision_public)
        + "\n</design-agency-decision>\n"
        + "(You MUST invoke the design-agency:design-agency-routing skill now, "
        "before any other action. Suppress with #noagency.)"
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": msg,
                }
            }
        )
    )


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    prompt = (payload.get("prompt") or "").strip()
    cwd = payload.get("cwd")
    session_id = payload.get("session_id")
    lower = prompt.lower()

    # --- (a) hard silent opt-outs ---
    if "#noagency" in lower or "#nodesign" in lower:
        return 0
    if os.environ.get("DESIGN_AGENCY_DISABLE") == "1":
        return 0
    if prompt.startswith("/"):
        return 0
    if len(prompt) < 15:
        return 0
    if lower.startswith(CONTINUATION_OPENERS):
        return 0

    # --- (b) per-repo config ---
    project_cfg = load_project_config(cwd)
    if project_cfg.get("disabled") is True:
        return 0
    try:
        ask_threshold = float(project_cfg.get("ask_threshold", DEFAULT_ASK_THRESHOLD))
    except (TypeError, ValueError):
        ask_threshold = DEFAULT_ASK_THRESHOLD
    extra_signals = project_cfg.get("extra_signals") or []

    # --- (c) session-engaged marker ---
    prune_engaged_markers()
    if session_id:
        try:
            if (ENGAGED_DIR / str(session_id)).exists():
                return 0
        except OSError:
            pass

    decision_id = "da_" + uuid.uuid4().hex[:10]
    thresholds = {"ask": round(ask_threshold, 2)}

    # --- (d) brandbook auto-engage ---
    if find_brandbook_agent(cwd) is not None:
        engagement_type = engagement_from_heuristics(prompt)
        decision = {
            "band": "engage",
            "confidence": 1.0,
            "engagement_type": engagement_type,
            "matched_signals": [],
            "reason": "DesignAgencyAgent/master_agent.md present in repo; auto-engaging.",
            "source": "repo_agents_md",
            "decision_id": decision_id,
            "thresholds": thresholds,
            "plan_mode": False,
            "_session_id": session_id,
        }
        emit(decision, None, cwd)
        return 0

    # --- (e) #agency override ---
    if "#agency" in lower:
        engagement_type = engagement_from_heuristics(prompt)
        decision = {
            "band": "engage",
            "confidence": 1.0,
            "engagement_type": engagement_type,
            "matched_signals": ["#agency"],
            "reason": "Explicit #agency override in prompt.",
            "source": "override",
            "decision_id": decision_id,
            "thresholds": thresholds,
            "plan_mode": False,
            "_session_id": session_id,
        }
        emit(decision, None, cwd)
        return 0

    # --- (f) heuristic classifier ---
    band, score, engagement_type, matched, reason = classify_heuristic(
        prompt, ask_threshold, extra_signals
    )
    if band == "none":
        return 0

    decision = {
        "band": "ask",
        "confidence": round(score, 2),
        "engagement_type": engagement_type,
        "matched_signals": matched,
        "reason": reason,
        "source": "heuristic",
        "decision_id": decision_id,
        "thresholds": thresholds,
        "plan_mode": False,
        "_session_id": session_id,
    }
    emit(decision, None, cwd)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never crash the prompt flow.
        sys.exit(0)
