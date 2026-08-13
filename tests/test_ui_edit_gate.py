#!/usr/bin/env python3
"""Unit tests for hooks/ui-edit-gate.py.

Tests:
  1. Project with style_directive.md + ui/page.html → gate emits.
  2. Project with no guards → silent.
  3. Debounce: second invocation same session+file → silent.
  4. Non-UI file path → silent.
  5. Missing tool_input in payload → silent (exit 0, no output).
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "ui-edit-gate.py"
CACHE_DIR = Path(os.path.expanduser("~/.claude/cache/design-agency"))
ENGAGED_DIR = CACHE_DIR / "engaged"
GATE_DIR = CACHE_DIR / "gate"


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )


def parse_gate_output(raw: str):
    """Return the parsed inner JSON from <design-agency-gate>...</design-agency-gate>,
    or None if the hook produced no output."""
    raw = raw.strip()
    if not raw:
        return None
    outer = json.loads(raw)
    ctx = outer["hookSpecificOutput"]["additionalContext"]
    m = re.search(r"<design-agency-gate>(.*?)</design-agency-gate>", ctx, re.DOTALL)
    if not m:
        return None
    return json.loads(m.group(1))


def fhash(file_path: str) -> str:
    return hashlib.sha1(file_path.encode("utf-8")).hexdigest()[:12]


def cleanup_gate_marker(session_id: str, file_path: str):
    sid = str(session_id) if session_id else "nosession"
    marker = GATE_DIR / f"{sid}-{fhash(file_path)}"
    try:
        marker.unlink()
    except FileNotFoundError:
        pass


def cleanup_engaged_marker(session_id: str):
    marker = ENGAGED_DIR / str(session_id)
    try:
        marker.unlink()
    except FileNotFoundError:
        pass


class TestUiEditGate(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.session_id = None
        self.file_paths = []

    def tearDown(self):
        # Remove any gate / engaged markers we created.
        for fp in self.file_paths:
            if self.session_id:
                cleanup_gate_marker(self.session_id, fp)
        if self.session_id:
            cleanup_engaged_marker(self.session_id)

        # Clean up tmpdir contents.
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Case 1: style_directive.md present + ui/page.html path → emits gate
    # ------------------------------------------------------------------
    def test_style_directive_triggers_gate(self):
        self.session_id = "pytest-gate-001"

        # Create style_directive.md at tmpdir root.
        style_path = Path(self.tmpdir) / "style_directive.md"
        style_path.write_text("# Style Directive\ncolor: #fff\n")

        # Create ui/ subdirectory and an HTML file inside.
        ui_dir = Path(self.tmpdir) / "ui"
        ui_dir.mkdir()
        html_file = ui_dir / "page.html"
        html_file.write_text("<html></html>")

        file_path = str(html_file)
        self.file_paths.append(file_path)

        payload = {
            "session_id": self.session_id,
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path},
        }

        result = run_hook(payload)
        self.assertEqual(result.returncode, 0)

        gate_data = parse_gate_output(result.stdout)
        self.assertIsNotNone(gate_data, "Expected gate output but got none")
        self.assertEqual(gate_data["file"], file_path)
        self.assertIsNotNone(gate_data["directive"])
        self.assertIn("style_directive.md", gate_data["directive"])

    # ------------------------------------------------------------------
    # Case 2: No guards (no style_directive, no DesignAgencyAgent dir,
    #          no engaged marker) → silent
    # ------------------------------------------------------------------
    def test_no_guards_silent(self):
        self.session_id = "pytest-gate-002"

        # Create ui/ subdir with an HTML file inside tmpdir (no style directive).
        ui_dir = Path(self.tmpdir) / "ui"
        ui_dir.mkdir()
        html_file = ui_dir / "page.html"
        html_file.write_text("<html></html>")

        file_path = str(html_file)
        self.file_paths.append(file_path)

        payload = {
            "session_id": self.session_id,
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path},
        }

        result = run_hook(payload)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "", "Expected silent output but got: " + result.stdout)

    # ------------------------------------------------------------------
    # Case 3: Debounce — second invocation same session+file → silent
    # ------------------------------------------------------------------
    def test_debounce_second_call_silent(self):
        self.session_id = "pytest-gate-003"

        style_path = Path(self.tmpdir) / "style_directive.md"
        style_path.write_text("# Style Directive\n")

        ui_dir = Path(self.tmpdir) / "ui"
        ui_dir.mkdir()
        html_file = ui_dir / "component.html"
        html_file.write_text("<html></html>")

        file_path = str(html_file)
        self.file_paths.append(file_path)

        payload = {
            "session_id": self.session_id,
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path},
        }

        # First call should emit.
        result1 = run_hook(payload)
        self.assertEqual(result1.returncode, 0)
        gate1 = parse_gate_output(result1.stdout)
        self.assertIsNotNone(gate1, "First call should emit gate output")

        # Second call same session+file must be silent.
        result2 = run_hook(payload)
        self.assertEqual(result2.returncode, 0)
        self.assertEqual(
            result2.stdout.strip(),
            "",
            "Second call should be debounced (silent) but got: " + result2.stdout,
        )

    # ------------------------------------------------------------------
    # Case 4: Non-UI file path → silent
    # ------------------------------------------------------------------
    def test_non_ui_path_silent(self):
        self.session_id = "pytest-gate-004"

        style_path = Path(self.tmpdir) / "style_directive.md"
        style_path.write_text("# Style Directive\n")

        # A file not matching ui/*.html
        src_file = Path(self.tmpdir) / "src" / "main.py"
        src_file.parent.mkdir()
        src_file.write_text("print('hello')")

        file_path = str(src_file)
        self.file_paths.append(file_path)

        payload = {
            "session_id": self.session_id,
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path},
        }

        result = run_hook(payload)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "", "Non-UI path should produce no output")

    # ------------------------------------------------------------------
    # Case 5: Missing tool_input → silent exit 0
    # ------------------------------------------------------------------
    def test_missing_tool_input_silent(self):
        self.session_id = "pytest-gate-005"

        payload = {
            "session_id": self.session_id,
            "tool_name": "Edit",
            # tool_input absent
        }

        result = run_hook(payload)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "", "Missing tool_input should produce no output")


if __name__ == "__main__":
    unittest.main()
