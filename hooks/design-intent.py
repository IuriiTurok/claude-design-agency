#!/usr/bin/env python3
"""UserPromptSubmit hook for the design-agency plugin.

Classifies a prompt for design/branding intent and, when it fires, emits a
machine-readable <design-agency-decision> block instructing the parent to
invoke the design-agency:design-agency-routing skill.

Evaluation order (first hit wins):
  a. Hard silent opt-outs (#noagency/#nodesign, env, slash command, too short,
     continuation openers).
  b. Per-repo .claude/design-agency.json (disabled / ask_threshold / extra_signals).
  c. Session-engaged marker (user engaged the agency this session) -> silent.
  d. #agency override -> engage.
  e. Heuristic classifier -> ask/silent. A repo carrying
     DesignAgencyAgent/master_agent.md upgrades an ask to engage; below the
     threshold it stays silent there too, so ops prompts are not hijacked.
  f. Per-(session, engagement_type) asked marker: one false positive suppresses
     re-asks of the same type only, never the whole session.

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

# DESIGN_AGENCY_CACHE_DIR lets tests (and operators) keep fixture runs out of
# the real telemetry; the same variable is honoured by ui-edit-gate.py and
# log_override.py.
CACHE_DIR = Path(
    os.environ.get("DESIGN_AGENCY_CACHE_DIR")
    or os.path.expanduser("~/.claude/cache/design-agency")
)
ENGAGED_DIR = CACHE_DIR / "engaged"
ASKED_DIR = CACHE_DIR / "asked"
DECISIONS_DIR = CACHE_DIR / "decisions"
AUDIT_LOG = CACHE_DIR / "audit.jsonl"
# Emitted in every decision so the routing skill can call its scripts by
# absolute path (CLAUDE_PLUGIN_ROOT is not set in the session's Bash env).
PLUGIN_ROOT = str(Path(__file__).resolve().parent.parent)
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

# Harness events (background-task completions, scheduled fires) arrive as
# UserPromptSubmit payloads but are not human prompts; their payload text
# (agent reports, file lists) otherwise scores as design intent.
HARNESS_EVENT_OPENERS = (
    "<task-notification",
    "<scheduled-task",
    "[system notification",
)

CREATION_VERBS = re.compile(
    r"\b(design|create|make|build|redesign|restyle|polish|improve|iterate)\b", re.I
)
DELIVERABLE_PATH = re.compile(r"ui/.*\.html|\.svg|brand_book|design_system", re.I)
# Path-like tokens (~/Code/brandbook/x.md, src/app/page.tsx, URLs) are removed
# before phrase scoring: a repo or folder name is not a design request.
PATH_TOKEN = re.compile(r"(?:https?://\S+|[~.\w-]*/[\w./~-]+)")
# Word-boundary matching: bare substring checks misfire ("ci" in "social",
# "test" in "testimonial"). >=2 DISTINCT terms subtract ENGINEERING_PENALTY,
# which is large enough to cancel a single Tier-A hit; >=ENGINEERING_VETO
# distinct terms zero the score (meta prompts about tooling, CI chores).
ENGINEERING_RE = re.compile(
    r"\b(apis?|database|db|deploy(?:ment|s|ed)?|ci|cd|tests?|bugs?|migrations?|"
    r"backend|docker|kubernetes|endpoints?|refactor|lint(?:er)?|schema|sdk|"
    r"server|pull request|prs?|type-?check|commits?|push|branch|merge|git|repo|"
    r"script|hooks?|plugin|classifier|fixtures?|changelog|readme|"
    r"step|stl|cad|fusion|cadquery|nozzle|firmware)\b",
    re.I,
)
# Prompts about this plugin's own machinery (its name, hook or spec files)
# are tooling work whenever any engineering term rides along.
META_RE = re.compile(
    r"\b(design-agency|design-intent|ui-edit-gate|skill\.md|agents?\.md)\b", re.I
)
ENGINEERING_PENALTY = 0.45
ENGINEERING_VETO = 4
THEORY_OPENERS = ("what is", "why does", "explain", "how does")

# (phrase, engagement_type) — phrase match contributes a TIER_A base score.
TIER_A_SIGNALS = [
    ("brand identity", "brand_project"),
    ("brand book", "brand_project"),
    ("rebrand", "brand_project"),
    ("visual identity", "brand_project"),
    ("design system", "deliverable_iteration"),
    ("style guide", "deliverable_iteration"),
    ("style directive", "deliverable_iteration"),
    ("mascot", "character_3d"),
    ("character design", "character_3d"),
    ("pose sheet", "character_3d"),
    ("brand kit", "brand_project"),
    ("image to 3d", "character_3d"),
    ("image-to-3d", "character_3d"),
    ("three.js model", "character_3d"),
    ("procedural model", "character_3d"),
]
TIER_A_SCORE = 0.85
# Tier-A words that only count alongside a creation verb ("brandbook" is also
# the user's main repo name; "logo" appears in asset paths and git chatter).
VERB_GATED_SIGNALS = [
    ("logo", "asset"),
    ("brandbook", "brand_project"),
]
# "3d model" is CAD vocabulary in hardware repos; it only means character work
# next to character context.
CHARACTER_CONTEXT = re.compile(
    r"\b(mascot|character|three\.?js|avatar|creature|figurine)\b", re.I
)

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

# Product UI (the "Operate" surface): a UI noun AND a visual verb together.
# Either alone is everyday engineering ("fix the form validation bug").
PRODUCT_UI_NOUN = re.compile(
    r"\b(dashboards?|kpis?|kpi cards?|tables?|data tables?|sidebars?|modals?|"
    r"dialogs?|forms?|components?|pages?|screens?|navbar|nav bar|toolbar|"
    r"empty states?|charts?|cards?|tabs|settings|onboarding)\b",
    re.I,
)
PRODUCT_UI_VERB = re.compile(
    r"\b(polish|restyle|redesign|re-?skin|beautify|tidy|denser|density|spacing|"
    r"padding|alignment|align|hierarchy|layout|visual(?:ly)?|look(?:s)? (?:better|off|cheap|generic)|"
    r"feel(?:s)? (?:cramped|generic|off)|ui|ux|typography|contrast|dark mode|light mode)\b",
    re.I,
)
PRODUCT_UI_SCORE = 0.60
EXTRA_SIGNAL_SCORE = 0.45


def _phrase_re(phrase):
    """Whole-word match with an optional plural ("posters", not "posterior")."""
    return re.compile(r"\b" + re.escape(phrase) + r"(?:s|es)?\b", re.I)


_TIER_A_RES = [(_phrase_re(p), p, t) for p, t in TIER_A_SIGNALS]
_TIER_B_RES = [(_phrase_re(p), p, t) for p, t in TIER_B_SIGNALS]
_VERB_GATED_RES = [(_phrase_re(p), p, t) for p, t in VERB_GATED_SIGNALS]
_3D_MODEL_RE = _phrase_re("3d model")


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
    """Opportunistically delete marker files older than 7 days."""
    cutoff = time.time() - ENGAGED_RETAIN_SEC
    for d in (ENGAGED_DIR, ASKED_DIR, DECISIONS_DIR):
        try:
            for p in d.glob("*"):
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


def strip_paths(prompt):
    return PATH_TOKEN.sub(" ", prompt)


def classify_heuristic(prompt, ask_threshold, extra_signals, negative_signals=None):
    """Additive heuristic scorer. Returns (band, score, engagement_type,
    matched_signals, reason) where band is 'ask' or 'none'."""
    text = strip_paths(prompt)
    matched = []
    score = 0.0
    engagement_type = "unknown"
    # Phrase hits are blanked before the creation-verb check so "design
    # system" does not also count as the verb "design".
    residue = text

    def hit(name, etype, value):
        nonlocal score, engagement_type
        matched.append(name)
        score += value
        if engagement_type == "unknown":
            engagement_type = etype

    for rx, phrase, etype in _TIER_A_RES:
        if rx.search(text):
            hit(phrase, etype, TIER_A_SCORE)
            residue = rx.sub(" ", residue)
    if _3D_MODEL_RE.search(text) and CHARACTER_CONTEXT.search(text):
        hit("3d model", "character_3d", TIER_A_SCORE)

    has_creation_verb = bool(CREATION_VERBS.search(residue))
    for rx, phrase, etype in _VERB_GATED_RES:
        if rx.search(text) and has_creation_verb:
            hit(phrase, etype, TIER_A_SCORE)

    for rx, phrase, etype in _TIER_B_RES:
        if rx.search(text):
            hit(phrase, etype, TIER_B_SCORE)

    if not matched and PRODUCT_UI_NOUN.search(text) and PRODUCT_UI_VERB.search(text):
        hit("product_ui", "product_ui", PRODUCT_UI_SCORE)

    # Project extra_signals: {"pattern": regex, "score": float}, or a bare
    # word/phrase string worth EXTRA_SIGNAL_SCORE (the README's short form).
    for sig in extra_signals or []:
        if isinstance(sig, str) and sig.strip():
            sig = {"pattern": r"\b" + re.escape(sig.strip()) + r"\b", "score": EXTRA_SIGNAL_SCORE}
        if not isinstance(sig, dict):
            continue
        pattern = sig.get("pattern")
        if not pattern:
            continue
        try:
            if re.search(pattern, text, re.I):
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
    eng_terms = {m.lower() for m in ENGINEERING_RE.findall(text)}
    # Project negative_signals: list of regexes; each hit counts as one more
    # distinct engineering term (e.g. patyx: "3d model|STEP|STL|CAD").
    for pattern in negative_signals or []:
        try:
            if isinstance(pattern, str) and re.search(pattern, text, re.I):
                eng_terms.add(f"neg:{pattern}")
        except re.error:
            continue
    if len(eng_terms) >= ENGINEERING_VETO or (eng_terms and META_RE.search(text)):
        score = 0.0
        matched.append("engineering_veto")
    elif len(eng_terms) >= 2:
        score -= ENGINEERING_PENALTY
        matched.append("engineering_dominant")
    if text.lower().strip().startswith(THEORY_OPENERS) and not has_creation_verb:
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
    """Best-effort engagement_type guess for the #agency override, which skips
    scoring thresholds. Returns a type or 'unknown'."""
    _, _, engagement_type, _, _ = classify_heuristic(prompt, 2.0, [])
    return engagement_type


def asked_marker(session_id, engagement_type):
    return ASKED_DIR / f"{session_id}-{engagement_type}"


def emit(decision, msg_extra, cwd):
    """Write session markers, append audit, print the additionalContext block.

    engage -> the session is engaged (silent from now on). ask -> only this
    engagement_type is marked asked; the session is marked engaged later, by
    log_override.py, if and only if the user picks "Use design agency"
    (it maps decision_id -> session via DECISIONS_DIR)."""
    session_id = decision.get("_session_id")
    decision["plugin_root"] = PLUGIN_ROOT
    decision_public = {k: v for k, v in decision.items() if not k.startswith("_")}

    try:
        if session_id:
            if decision_public.get("band") == "engage":
                ENGAGED_DIR.mkdir(parents=True, exist_ok=True)
                (ENGAGED_DIR / str(session_id)).touch()
            else:
                ASKED_DIR.mkdir(parents=True, exist_ok=True)
                asked_marker(session_id, decision_public.get("engagement_type")).touch()
            DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
            (DECISIONS_DIR / str(decision_public.get("decision_id"))).write_text(
                str(session_id)
            )
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
    if lower.startswith(HARNESS_EVENT_OPENERS) or "<task-notification>" in lower[:300]:
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
    negative_signals = project_cfg.get("negative_signals") or []

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

    # --- (d) #agency override ---
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

    # --- (e) heuristic classifier ---
    band, score, engagement_type, matched, reason = classify_heuristic(
        prompt, ask_threshold, extra_signals, negative_signals
    )
    if band == "none":
        return 0

    # --- (f) same-type re-ask suppression ---
    if session_id:
        try:
            if asked_marker(session_id, engagement_type).exists():
                return 0
        except OSError:
            pass

    source = "heuristic"
    if find_brandbook_agent(cwd) is not None:
        band, source = "engage", "repo_agents_md"
        reason = "DesignAgencyAgent/master_agent.md present in repo; " + reason

    decision = {
        "band": band,
        "confidence": round(score, 2),
        "engagement_type": engagement_type,
        "matched_signals": matched,
        "reason": reason,
        "source": source,
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
