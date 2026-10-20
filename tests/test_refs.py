#!/usr/bin/env python3
"""Reference integrity for the plugin's own files.

  1. Every `design-agency:<name>` mention resolves to a bundled skill or agent.
  2. Dead references (tools/skills that do not exist or are not enabled) are
     not reintroduced: agent-browser-verify, chrome-devtools-mcp,
     a11y-debugging, figma:create-design-system-rules, slash-named official
     skills.
  3. Every SKILL.md and agent file has parseable frontmatter with name and
     description (a malformed one makes the skill silently unloadable).
  4. Agent descriptions do not claim a model their frontmatter does not set.

Run directly: python3 tests/test_refs.py
"""

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
# History and attribution may name what used to exist.
EXEMPT = {"CHANGELOG.md", "NOTICE.md"}
DEAD = re.compile(
    r"agent-browser-verify|chrome-devtools-mcp|a11y-debugging|figma:create-design-system-rules|"
    r"`/(frontend-design|web-artifacts-builder|canvas-design|theme-factory|brand-guidelines|pdf|pptx|ui-ux-pro-max)`"
)
REF = re.compile(r"design-agency:([a-z0-9][a-z0-9-]*)")


def doc_files():
    for p in PLUGIN.rglob("*"):
        if p.suffix in (".md", ".py", ".sh", ".json") and p.is_file():
            rel = p.relative_to(PLUGIN)
            if rel.parts[0] in (".git", "tests") or rel.name in EXEMPT:
                continue
            yield p


def frontmatter(path):
    text = path.read_text(errors="replace")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else None


class TestRefs(unittest.TestCase):
    def test_namespaced_refs_resolve(self):
        skills = {p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md")}
        agents = set()
        for p in (PLUGIN / "agents").glob("*.md"):
            m = re.search(r"^name:\s*(\S+)", frontmatter(p) or "", re.M)
            agents.add(m.group(1))
        known = skills | agents | {"design-agency", "design-agency-routing"}
        bad = []
        for p in doc_files():
            for name in REF.findall(p.read_text(errors="replace")):
                if name not in known:
                    bad.append(f"{p.relative_to(PLUGIN)}: design-agency:{name}")
        self.assertEqual(bad, [], "unresolved namespaced references")

    def test_no_dead_references(self):
        bad = []
        for p in doc_files():
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if DEAD.search(line):
                    bad.append(f"{p.relative_to(PLUGIN)}:{i}: {line.strip()[:100]}")
        self.assertEqual(bad, [], "dead references")

    def test_frontmatter_parses(self):
        files = list((PLUGIN / "skills").glob("*/SKILL.md")) + list((PLUGIN / "agents").glob("*.md"))
        self.assertTrue(files)
        for p in files:
            fm = frontmatter(p)
            self.assertIsNotNone(fm, f"{p}: no frontmatter")
            self.assertRegex(fm, r"(?m)^name:\s*\S", f"{p}: no name")
            self.assertRegex(fm, r"(?m)^description:", f"{p}: no description")
            # An unquoted single-line value containing ": " breaks YAML.
            for line in fm.splitlines():
                m = re.match(r"^(name|description):\s*(.+)$", line)
                if m and m.group(2)[0] not in "\"'>|" and ": " in m.group(2):
                    self.fail(f"{p}: unquoted '{m.group(1)}' contains ': '")

    def test_agent_model_claims_match(self):
        for p in (PLUGIN / "agents").glob("*.md"):
            fm = frontmatter(p) or ""
            model = re.search(r"^model:\s*(\S+)", fm, re.M)
            claim = re.search(r"Model:\s*(opus|sonnet|haiku)", fm)
            if claim and model:
                self.assertEqual(claim.group(1), model.group(1), f"{p}: description claims {claim.group(1)}")


if __name__ == "__main__":
    unittest.main()
