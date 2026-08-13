#!/usr/bin/env python3
"""State-path resolver for the design-agency plugin.

Two public entry points:

  resolve(filename, cwd=None)     -> Path to a writable state file
  brand_config(cwd=None)          -> dict of brand-enforcement settings

resolve(filename, cwd=None) maps a logical state filename to a concrete path
using a three-tier chain (first hit wins):

  (a) DESIGN_AGENCY_STATE_DIR env set  -> <that dir>/<filename>
  (b) repo-local: walk up from cwd looking for a directory that contains a
      DesignAgencyAgent/ subdir, then map known filenames into that repo:
        style_library.md        -> DesignAgencyAgent/style_library.md
        logo_feedback_log.json   -> DesignAgencyAgent/execution/logo_feedback_log.json
        lessons_learned.md       -> <repo>/lessons_learned.md
        .venv-vision             -> DesignAgencyAgent/execution/.venv-vision
  (c) fallback                  -> ~/.claude/design-agency/<filename>

At each tier resolve() prefers an existing path; if nothing exists it returns
the tier-(c) path. Creating parent directories on write-intent is the caller's
job — resolve() only returns the path.
"""

import json
import os
from pathlib import Path

PROJECT_CONFIG_FILENAME = ".claude/design-agency.json"
GLOBAL_CONFIG_FILENAME = "config.json"

# Neutral defaults. The agency ships with no reserved brand of its own; an
# operator declares theirs in the global or per-repo config. Empty lists mean
# "no bleed-through enforcement", not "enforcement disabled" — the enforcer
# still runs, it just has no owned tokens to protect.
DEFAULT_BRAND_CONFIG = {
    # How the agency signs its own collateral (proposals, decks, footers).
    # Empty name => unsigned; templates omit the byline rather than invent one.
    "agency_name": "",
    "agency_tagline": "",
    # Directories (repo-relative) holding the agency's OWN brand work. Reserved
    # tokens are permitted inside these and banned everywhere else.
    "own_brand_folders": [],
    # Tokens the agency reserves for itself: fonts by name, colors by hex.
    "reserved_tokens": {"fonts": [], "colors": []},
    # Documented per-project exceptions: {"<project-dir>": ["Inter", "#123456"]}.
    "carve_outs": {},
}

# Logical filename -> path relative to the repo that holds DesignAgencyAgent/.
REPO_RELATIVE = {
    "style_library.md": ("DesignAgencyAgent", "style_library.md"),
    "logo_feedback_log.json": (
        "DesignAgencyAgent",
        "execution",
        "logo_feedback_log.json",
    ),
    "lessons_learned.md": ("lessons_learned.md",),
    ".venv-vision": ("DesignAgencyAgent", "execution", ".venv-vision"),
}


def _find_repo_root(cwd):
    """Walk up from cwd to filesystem root looking for a dir that contains a
    DesignAgencyAgent/ subdirectory. Return that dir as a Path, or None."""
    try:
        cur = Path(cwd).resolve()
    except (OSError, ValueError):
        return None
    while True:
        try:
            if (cur / "DesignAgencyAgent").is_dir():
                return cur
        except OSError:
            pass
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def _fallback_path(filename):
    return Path(os.path.expanduser("~/.claude/design-agency")) / filename


def _read_json(path):
    """Return a dict from a JSON file, or {} if it is missing or malformed."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _find_project_config(cwd):
    """Walk up from cwd for .claude/design-agency.json; first hit wins.

    Mirrors load_project_config() in hooks/design-intent.py — same file, same
    walk-up, so an operator configures the agency in exactly one place.
    """
    try:
        cur = Path(cwd if cwd is not None else os.getcwd()).resolve()
    except (OSError, ValueError):
        return {}
    home = Path(os.path.expanduser("~"))
    while True:
        cfg = _read_json(cur / PROJECT_CONFIG_FILENAME)
        if cfg:
            return cfg
        parent = cur.parent
        if parent == cur or cur == home:
            return {}
        cur = parent


def brand_config(cwd=None):
    """Resolve brand-enforcement settings through a three-tier merge.

      (1) DEFAULT_BRAND_CONFIG      — neutral, ships with the plugin
      (2) <state dir>/config.json   — the operator's own agency brand
      (3) <repo>/.claude/design-agency.json, "brand" key — per-repo overrides

    Later tiers replace earlier ones key by key (not deep-merged): a repo that
    declares "reserved_tokens" owns that whole key. Unknown keys are ignored.
    """
    merged = {
        "agency_name": DEFAULT_BRAND_CONFIG["agency_name"],
        "agency_tagline": DEFAULT_BRAND_CONFIG["agency_tagline"],
        "own_brand_folders": list(DEFAULT_BRAND_CONFIG["own_brand_folders"]),
        "reserved_tokens": dict(DEFAULT_BRAND_CONFIG["reserved_tokens"]),
        "carve_outs": dict(DEFAULT_BRAND_CONFIG["carve_outs"]),
    }

    for source in (
        _read_json(resolve(GLOBAL_CONFIG_FILENAME, cwd=cwd)).get("brand"),
        _find_project_config(cwd).get("brand"),
    ):
        if isinstance(source, dict):
            for key in merged:
                if key in source:
                    merged[key] = source[key]

    return merged


def resolve(filename, cwd=None):
    """Resolve a logical state filename to a concrete Path (see module docstring)."""
    # Tier (a): explicit override directory.
    state_dir = os.environ.get("DESIGN_AGENCY_STATE_DIR")
    if state_dir:
        return Path(os.path.expanduser(state_dir)) / filename

    # Tier (b): repo-local mapping.
    if filename in REPO_RELATIVE:
        repo = _find_repo_root(cwd if cwd is not None else os.getcwd())
        if repo is not None:
            repo_path = repo.joinpath(*REPO_RELATIVE[filename])
            if repo_path.exists():
                return repo_path
            # Repo found but the file doesn't exist yet: prefer the repo-local
            # path only if its parent directory already exists (a real repo
            # checkout), otherwise fall through to the fallback tier.
            try:
                if repo_path.parent.is_dir():
                    return repo_path
            except OSError:
                pass

    # Tier (c): fallback, preferring an existing path.
    fallback = _fallback_path(filename)
    return fallback


if __name__ == "__main__":
    import sys

    arg = sys.argv[1] if len(sys.argv) > 1 else "logo_feedback_log.json"
    if arg == "--brand":
        print(json.dumps(brand_config(), indent=2))
    else:
        print(resolve(arg))
