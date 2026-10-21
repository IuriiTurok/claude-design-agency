#!/usr/bin/env python3
"""Session-marker contract between hooks/design-intent.py and the routing
skill's log_override.py.

  1. An ask names plugin_root, and the override logger exists under it.
  2. "Use design agency" (engaged) silences the hook for the session.
  3. "Not design work" (not_design) leaves other engagement types open.
  4. Writes stay inside DESIGN_AGENCY_CACHE_DIR (never the real HOME).

Run directly: python3 tests/test_session_markers.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
HOOK = PLUGIN / "hooks" / "design-intent.py"
LOGGER = "skills/design-agency-routing/scripts/log_override.py"


class TestSessionMarkers(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.cache = self.home / "cache"
        self.env = dict(os.environ, HOME=str(self.home), DESIGN_AGENCY_CACHE_DIR=str(self.cache))
        self.env.pop("DESIGN_AGENCY_OVERRIDES_LOG", None)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def prompt(self, text, session):
        out = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"prompt": text, "cwd": str(self.home), "session_id": session}),
            capture_output=True, text=True, env=self.env,
        ).stdout.strip()
        if not out:
            return None
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        return json.loads(re.search(r"<design-agency-decision>\n(.*?)\n", ctx).group(1))

    def log(self, decision, choice):
        return subprocess.run(
            [sys.executable, str(Path(decision["plugin_root"]) / LOGGER),
             decision["decision_id"], decision["engagement_type"],
             str(decision["confidence"]), choice],
            capture_output=True, text=True, env=self.env,
        )

    def test_plugin_root_resolves_logger(self):
        d = self.prompt("design a poster for the spring launch", "s1")
        self.assertEqual(d["band"], "ask")
        self.assertTrue((Path(d["plugin_root"]) / LOGGER).is_file())

    def test_engaged_choice_silences_session(self):
        d = self.prompt("design a poster for the spring launch", "s2")
        self.assertEqual(self.log(d, "engaged").returncode, 0)
        self.assertTrue((self.cache / "engaged" / "s2").exists())
        self.assertIsNone(self.prompt("now create a brand book for the series", "s2"))
        rows = (self.cache / "overrides.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(rows[-1])["user_choice"], "engaged")

    def test_not_design_keeps_other_types_open(self):
        d = self.prompt("design a poster for the spring launch", "s3")
        self.assertEqual(self.log(d, "not_design").returncode, 0)
        self.assertFalse((self.cache / "engaged" / "s3").exists())
        self.assertIsNone(self.prompt("make another poster variant please", "s3"))
        d2 = self.prompt("now create a brand book for the series", "s3")
        self.assertIsNotNone(d2)
        self.assertEqual(d2["engagement_type"], "brand_project")

    def test_writes_stay_in_cache_dir(self):
        self.prompt("design a poster for the spring launch", "s4")
        self.assertTrue((self.cache / "audit.jsonl").exists())
        self.assertFalse((self.home / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
