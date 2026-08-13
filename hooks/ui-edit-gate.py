#!/usr/bin/env python3
"""PostToolUse hook (Edit|Write|MultiEdit) for the design-agency plugin.

Fires a Style Enforcer gate reminder when a UI deliverable (a file matching
ui/<name>.html) is modified inside a design-agency context. Debounced per
(session, file) so it nags at most once.

Never crashes the tool flow: main() is wrapped in try/except and exits 0
silently on any error.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

CACHE_DIR = Path(os.path.expanduser("~/.claude/cache/design-agency"))
ENGAGED_DIR = CACHE_DIR / "engaged"
GATE_DIR = CACHE_DIR / "gate"

UI_HTML = re.compile(r"(^|/)ui/[^/]+\.html$")


def find_style_directive(start_dir):
    """Walk up from start_dir to filesystem root for a style_directive.md.
    Return its Path or None."""
    cur = start_dir
    while True:
        try:
            candidate = cur / "style_directive.md"
            if candidate.is_file():
                return candidate
        except OSError:
            pass
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def find_design_agency_dir(start_dir):
    """Walk up from start_dir to filesystem root for a DesignAgencyAgent/ dir."""
    cur = start_dir
    while True:
        try:
            if (cur / "DesignAgencyAgent").is_dir():
                return True
        except OSError:
            pass
        parent = cur.parent
        if parent == cur:
            return False
        cur = parent


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0
    session_id = payload.get("session_id")

    if not UI_HTML.search(file_path):
        return 0

    # Guards: at least one must hold. Compute directive_path for the emit body.
    try:
        file_dir = Path(file_path).resolve().parent
    except (OSError, ValueError):
        file_dir = Path(file_path).parent

    directive = find_style_directive(file_dir)
    guard_directive = directive is not None
    guard_agency_dir = find_design_agency_dir(file_dir)
    guard_engaged = False
    if session_id:
        try:
            guard_engaged = (ENGAGED_DIR / str(session_id)).exists()
        except OSError:
            guard_engaged = False

    if not (guard_directive or guard_agency_dir or guard_engaged):
        return 0

    # Debounce per (session, file).
    sid = str(session_id) if session_id else "nosession"
    fhash = hashlib.sha1(file_path.encode("utf-8")).hexdigest()[:12]
    marker = GATE_DIR / f"{sid}-{fhash}"
    try:
        GATE_DIR.mkdir(parents=True, exist_ok=True)
        if marker.exists():
            return 0
        marker.touch()
    except OSError:
        # If we can't manage the debounce marker, fall through and emit once.
        pass

    directive_path = str(directive) if directive is not None else None
    context = (
        "<design-agency-gate>"
        + json.dumps({"file": file_path, "directive": directive_path})
        + "</design-agency-gate>\n"
        "Style Enforcer gate: this deliverable was modified. Before commit, "
        "deploy, or presenting the result, dispatch "
        'Agent(subagent_type="style-enforcer") against it and report 0 violations.'
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never crash the tool flow.
        sys.exit(0)
