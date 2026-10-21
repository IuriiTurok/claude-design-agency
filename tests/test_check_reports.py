#!/usr/bin/env python3
"""Tests for execution/check_reports.py. Run: python3 tests/test_check_reports.py"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "execution" / "check_reports.py"


class TestCheckReports(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp())
        (self.project / "ui").mkdir()
        self.page = self.project / "ui" / "landing_page.html"
        self.page.write_text("<html></html>")
        old = time.time() - 60
        os.utime(self.page, (old, old))
        (self.project / "reports").mkdir()

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def run_check(self, *extra):
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.page), "--json", *extra],
                           capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)

    def report(self, name, verdict, where="reports"):
        (self.project / where / name).write_text(f"# Report\n\n**Verdict:** {verdict}\n")

    def test_missing_fails(self):
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual({g["status"] for g in out["gates"]}, {"missing"})

    def test_pass_with_standard_names(self):
        self.report("enforcer_report_landing_page.md", "PASS")
        self.report("vqa_report_landing_page.md", "PASS")
        self.assertEqual(self.run_check()[0], 0)

    def test_legacy_names_at_project_root(self):
        self.report("style_enforcer_report_landing_page.md", "PASS", where=".")
        self.report("visual_qa_report_landing_page.md", "PASS", where=".")
        self.assertEqual(self.run_check()[0], 0)

    def test_unmeasured_is_not_pass(self):
        self.report("enforcer_report_landing_page.md", "PASS")
        self.report("vqa_report_landing_page.md", "UNMEASURED")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(out["gates"][1]["status"], "unmeasured")

    def test_stale_report_fails(self):
        self.report("enforcer_report_landing_page.md", "PASS")
        self.report("vqa_report_landing_page.md", "PASS")
        self.page.write_text("<html>edited</html>")
        future = time.time() + 60
        os.utime(self.page, (future, future))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("stale", {g["status"] for g in out["gates"]})

    def test_reports_dir_from_config(self):
        (self.project / ".claude").mkdir()
        (self.project / ".claude" / "design-agency.json").write_text('{"reports_dir": "qa"}')
        (self.project / "qa").mkdir()
        self.report("enforcer_report_landing_page.md", "PASS", where="qa")
        code, out = self.run_check("--gates", "enforcer")
        self.assertEqual(code, 0)
        self.assertTrue(out["reports_dir"].endswith("/qa"))


if __name__ == "__main__":
    unittest.main()
