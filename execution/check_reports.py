#!/usr/bin/env python3
"""Check that QA gate reports exist on disk, are newer than the deliverable,
and record a passing verdict.

"Reports to disk" is a hard rule of the agency: a gate that only ran in the
transcript did not happen. This script makes the rule checkable.

Standard report names (v0.5.0), under <reports_dir>:

  enforcer_report_<name>.md   style-enforcer   (also written by enforce.py --report)
  vqa_report_<name>.md        visual-qa
  taste_report_<name>.md      taste-guardian
  polish_report_<name>.md     polish-inspector
  motion_report_<name>.md     motion-designer

<reports_dir> = `reports_dir` from <repo>/.claude/design-agency.json (relative to
the repo root), else <project>/reports. Legacy names are still accepted, in
<reports_dir> or the project root: style_enforcer_report_<name>.md,
visual_qa_report_<name>.md, taste_report.md, motion_audit.md.

A report's verdict is the first line matching `Verdict: PASS|FAIL|UNMEASURED`
(markdown bold allowed). UNMEASURED (e.g. visual-qa without a browser) is not
a pass.

Usage:
  python3 check_reports.py <deliverable> [--project DIR] [--name NAME]
                           [--gates enforcer,vqa] [--json]

Exit codes: 0 all required reports present, fresh and PASS; 1 otherwise;
2 usage error. Read-only: never writes anything.
"""

import argparse
import json
import re
import sys
from pathlib import Path

GATES = {
    "enforcer": ["enforcer_report_{n}.md", "style_enforcer_report_{n}.md"],
    "vqa": ["vqa_report_{n}.md", "visual_qa_report_{n}.md"],
    "taste": ["taste_report_{n}.md", "taste_report.md"],
    "polish": ["polish_report_{n}.md"],
    "motion": ["motion_report_{n}.md", "motion_audit_{n}.md", "motion_audit.md"],
}
VERDICT_RE = re.compile(r"verdict\W{0,4}\s*(PASS|FAIL|UNMEASURED)", re.I)
PROJECT_CONFIG_FILENAME = ".claude/design-agency.json"


def find_project_config(start):
    cur = start
    while True:
        candidate = cur / PROJECT_CONFIG_FILENAME
        if candidate.is_file():
            try:
                cfg = json.loads(candidate.read_text())
                if isinstance(cfg, dict):
                    return cfg, cur
            except (OSError, ValueError):
                pass
        if cur.parent == cur:
            return {}, None
        cur = cur.parent


def reports_dir(project):
    cfg, root = find_project_config(project)
    if root is not None and isinstance(cfg.get("reports_dir"), str):
        return root / cfg["reports_dir"]
    return project / "reports"


def check(deliverable, project, name, gates):
    rdir = reports_dir(project)
    try:
        edited = deliverable.stat().st_mtime
    except OSError:
        edited = None
    results = []
    for gate in gates:
        found = None
        for pattern in GATES[gate]:
            fname = pattern.format(n=name)
            for d in (rdir, project):
                if (d / fname).is_file():
                    found = d / fname
                    break
            if found:
                break
        row = {"gate": gate, "report": str(found) if found else None}
        if not found:
            row["status"] = "missing"
        elif edited is not None and found.stat().st_mtime < edited:
            row["status"] = "stale"
        else:
            m = VERDICT_RE.search(found.read_text(errors="replace"))
            verdict = m.group(1).upper() if m else None
            row["verdict"] = verdict
            row["status"] = "ok" if verdict == "PASS" else ("no-verdict" if verdict is None else verdict.lower())
        results.append(row)
    return {
        "deliverable": str(deliverable),
        "reports_dir": str(rdir),
        "gates": results,
        "pass": all(r["status"] == "ok" for r in results),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("deliverable")
    ap.add_argument("--project", help="project dir (default: deliverable's dir, or its parent when that is ui/)")
    ap.add_argument("--name", help="report name stem (default: deliverable file stem)")
    ap.add_argument("--gates", default="enforcer,vqa")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    gates = [g.strip() for g in args.gates.split(",") if g.strip()]
    unknown = [g for g in gates if g not in GATES]
    if unknown:
        print(f"unknown gate(s): {', '.join(unknown)}; known: {', '.join(GATES)}", file=sys.stderr)
        return 2
    deliverable = Path(args.deliverable).resolve()
    if args.project:
        project = Path(args.project).resolve()
    else:
        project = deliverable.parent.parent if deliverable.parent.name == "ui" else deliverable.parent
    result = check(deliverable, project, args.name or deliverable.stem, gates)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for r in result["gates"]:
            print(f"{r['gate']:<9} {r['status']:<11} {r['report'] or '-'}")
        print("PASS" if result["pass"] else "FAIL: gate reports missing, stale or not passing")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
