#!/usr/bin/env python3
"""PostToolUse hook (Edit|Write|MultiEdit) for the design-agency plugin.

Fires a Style Enforcer gate reminder when a UI file is modified inside a
design-agency context. Debounced per (session, file) so it nags at most once.

Two kinds of UI file:
  - brand deliverables: ui/<name>.html (the original track);
  - product UI (the Operate track): *.tsx|*.jsx|*.vue|*.svelte|*.css|*.scss
    in a repo whose .claude/design-agency.json declares `directive_path` or
    `ui_globs`, or in an engaged session where a style_directive.md is found
    walking up. Tests, stories and type declarations are skipped.

Never crashes the tool flow: main() is wrapped in try/except and exits 0
silently on any error.
"""

import fnmatch
import hashlib
import json
import os
import re
import sys
from pathlib import Path

CACHE_DIR = Path(
    os.environ.get("DESIGN_AGENCY_CACHE_DIR")
    or os.path.expanduser("~/.claude/cache/design-agency")
)
ENGAGED_DIR = CACHE_DIR / "engaged"
GATE_DIR = CACHE_DIR / "gate"
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CONFIG_FILENAME = ".claude/design-agency.json"

UI_HTML = re.compile(r"(^|/)ui/[^/]+\.html$")
PRODUCT_UI_EXT = re.compile(r"\.(tsx|jsx|vue|svelte|css|scss)$")
NOT_UI = re.compile(r"(\.(test|spec|stories)\.[^/]+$|\.d\.ts$|(^|/)__tests__/)")
ENFORCER = "design-agency:style-enforcer"


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


def find_project_config(start_dir):
    """Walk up for .claude/design-agency.json. Return (config, repo_root) or
    ({}, None)."""
    cur = start_dir
    while True:
        candidate = cur / PROJECT_CONFIG_FILENAME
        try:
            with open(candidate) as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                return cfg, cur
        except (FileNotFoundError, NotADirectoryError, json.JSONDecodeError, OSError, ValueError):
            pass
        parent = cur.parent
        if parent == cur:
            return {}, None
        cur = parent


def session_engaged(session_id):
    if not session_id:
        return False
    try:
        return (ENGAGED_DIR / str(session_id)).exists()
    except OSError:
        return False


def resolve_product_ui(file_path, file_dir, session_id):
    """Return the directive Path (or None) when file_path is gated product UI,
    else False."""
    if not PRODUCT_UI_EXT.search(file_path) or NOT_UI.search(file_path):
        return False
    cfg, root = find_project_config(file_dir)
    if root is not None and (cfg.get("directive_path") or cfg.get("ui_globs")):
        globs = cfg.get("ui_globs")
        if isinstance(globs, list) and globs:
            try:
                rel = str(Path(file_path).resolve().relative_to(root))
            except (OSError, ValueError):
                return False
            if not any(fnmatch.fnmatch(rel, g) for g in globs if isinstance(g, str)):
                return False
        directive = None
        if isinstance(cfg.get("directive_path"), str):
            candidate = root / cfg["directive_path"]
            directive = candidate if candidate.is_file() else None
        return directive or find_style_directive(file_dir)
    if session_engaged(session_id):
        directive = find_style_directive(file_dir)
        if directive is not None:
            return directive
    return False


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

    try:
        file_dir = Path(file_path).resolve().parent
    except (OSError, ValueError):
        file_dir = Path(file_path).parent

    if UI_HTML.search(file_path):
        surface = "persuade"
        # Guards: at least one must hold.
        directive = find_style_directive(file_dir)
        if not (
            directive is not None
            or find_design_agency_dir(file_dir)
            or session_engaged(session_id)
        ):
            return 0
    else:
        surface = "operate"
        directive = resolve_product_ui(file_path, file_dir, session_id)
        if directive is False:
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
    enforce = (
        f'python3 "{PLUGIN_ROOT}/execution/enforce.py" "{file_path}" '
        f'--directive "{directive_path or "<style_directive.md>"}" --surface {surface}'
    )
    context = (
        "<design-agency-gate>"
        + json.dumps(
            {
                "file": file_path,
                "directive": directive_path,
                "surface": surface,
                "plugin_root": str(PLUGIN_ROOT),
            }
        )
        + "</design-agency-gate>\n"
        "Style Enforcer gate: this UI file was modified. Before commit, deploy, "
        f'or presenting the result, dispatch Agent(subagent_type="{ENFORCER}") '
        "against it and report 0 violations (an inline pass is not the gate). "
        f"Its mechanical first pass is: {enforce}"
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
