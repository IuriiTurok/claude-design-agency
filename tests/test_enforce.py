#!/usr/bin/env python3
"""Unit tests for execution/enforce.py (directive-driven style linter).

Runs the CLI as a subprocess against tests/fixtures/enforce/. HOME and the
design-agency state dir point at a tempdir so the operator's real brand config
(~/.claude) never leaks in, and the only file written is the --report inside
that tempdir.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "execution" / "enforce.py"
FIX = Path(__file__).resolve().parent / "fixtures" / "enforce"
DIRECTIVE = FIX / "style_directive.md"

TMP = None
ENV = None


def setUpModule():
    global TMP, ENV
    TMP = tempfile.mkdtemp(prefix="enforce-test-")
    ENV = dict(os.environ)
    ENV["HOME"] = TMP
    ENV["DESIGN_AGENCY_STATE_DIR"] = os.path.join(TMP, "state")


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


def run(*args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        env=env or ENV,
        cwd=TMP,
    )


def run_json(*args, env=None):
    proc = run(*args, "--json", env=env)
    return proc, json.loads(proc.stdout)


def rules_hit(result):
    return {v["rule"] for v in result["violations"]}


class CleanLanding(unittest.TestCase):
    def test_passes(self):
        proc, res = run_json(FIX / "landing_clean.html", "--directive", DIRECTIVE)
        self.assertEqual(proc.returncode, 0, res["violations"])
        self.assertEqual(res["summary"], {"violations": 0, "waived": 0})
        self.assertEqual(res["surface_mode"], "persuade")
        self.assertIn("em-dash", res["rules_run"])
        self.assertIn("loading-spinner", res["rules_run"])  # Do Not List bans spinners
        self.assertNotIn(
            "raw-hex-outside-tokens", res["rules_run"]
        )  # no Token files line
        self.assertNotIn(
            "reserved-token-bleed", res["rules_run"]
        )  # empty reserved list


class DirtyLanding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc, cls.res = run_json(
            FIX / "landing_dirty.html", "--directive", DIRECTIVE
        )

    def test_exit_code(self):
        self.assertEqual(self.proc.returncode, 1)

    def test_every_persuade_rule_fires(self):
        expected = {
            "raw-hex-off-palette",
            "font-off-directive",
            "z-index-literal",
            "div-onclick",
            "transition-all",
            "loading-spinner",
            "orphan-class",
            "em-dash",
            "h-screen-hero",
            "scroll-cue",
            "section-number-eyebrow",
        }
        self.assertEqual(expected - rules_hit(self.res), set())

    def test_violation_shape(self):
        v = next(v for v in self.res["violations"] if v["rule"] == "z-index-literal")
        self.assertEqual(v["line"], 9)
        self.assertEqual(v["excerpt"], ".nav { position: fixed; z-index: 100; }")
        self.assertTrue(v["file"].endswith("landing_dirty.html"))
        for v in self.res["violations"]:
            self.assertLessEqual(len(v["excerpt"]), 120)
            self.assertEqual(set(v), {"rule", "file", "line", "excerpt", "message"})

    def test_inline_svg_hex_ignored(self):
        msgs = [
            v["message"]
            for v in self.res["violations"]
            if v["rule"] == "raw-hex-off-palette"
        ]
        self.assertTrue(any("#333333" in m for m in msgs))
        self.assertFalse(any("#123456" in m for m in msgs))

    def test_em_dash_counted(self):
        em = [v for v in self.res["violations"] if v["rule"] == "em-dash"]
        self.assertEqual(len(em), 2)
        self.assertIn("2 in file", em[0]["message"])


class DirtyProductScreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc, cls.res = run_json(
            FIX / "product_dirty.tsx", "--directive", DIRECTIVE
        )

    def test_operate_inferred(self):
        self.assertEqual(self.res["surface_mode"], "operate")
        self.assertNotIn("em-dash", self.res["rules_run"])
        self.assertNotIn("h-screen-hero", self.res["rules_run"])
        self.assertIn("missing-tabular-nums", self.res["rules_run"])

    def test_rules(self):
        hit = rules_hit(self.res)
        self.assertNotIn("em-dash", hit)
        self.assertIn("transition-all", hit)
        self.assertIn("raw-hex-off-palette", hit)
        self.assertIn("missing-tabular-nums", hit)
        self.assertIn("div-onclick", hit)  # onClick={() => ...} with `>` inside braces
        msgs = [
            v["message"]
            for v in self.res["violations"]
            if v["rule"] == "raw-hex-off-palette"
        ]
        self.assertEqual(
            msgs, ["#0f0f0f is not in the directive palette"]
        )  # #FAFAF9 is on palette

    def test_surface_override(self):
        _, res = run_json(
            FIX / "product_dirty.tsx", "--directive", DIRECTIVE, "--surface", "persuade"
        )
        self.assertEqual(res["surface_mode"], "persuade")
        self.assertIn("em-dash", rules_hit(res))
        self.assertNotIn("missing-tabular-nums", rules_hit(res))


class Waiver(unittest.TestCase):
    def test_em_dash_moves_to_waived(self):
        proc, res = run_json(
            FIX / "landing_dirty.html", "--directive", FIX / "style_directive_waiver.md"
        )
        self.assertNotIn("em-dash", rules_hit(res))
        waived = [w for w in res["waived"] if w["rule"] == "em-dash"]
        self.assertEqual(len(waived), 2)
        self.assertIn("editorial voice", waived[0]["reason"])
        self.assertEqual(res["summary"]["waived"], 2)
        self.assertIn("unknown rule `not-a-rule`", proc.stderr)
        self.assertEqual(res["surface_mode"], "persuade")  # from SURFACE_MODE line


class OrphanClassesInJs(unittest.TestCase):
    def test_string_literal_classes(self):
        _, res = run_json(FIX / "orphan_js.html", "--directive", DIRECTIVE)
        orphans = {
            v["message"].split()[0]
            for v in res["violations"]
            if v["rule"] == "orphan-class"
        }
        # Applied only from JS strings; none defined in inline <style> or linked CSS.
        self.assertEqual(
            orphans, {".ghost-panel", ".is-zz", ".row-on", ".badge-q", ".esc-cls", ".nest-on"}
        )

    def test_extra_css_resolves(self):
        extra = Path(TMP) / "extra.css"
        extra.write_text(".ghost-panel{} .is-zz{} .row-on{} .badge-q{} .esc-cls{} .nest-on{}")
        proc, res = run_json(
            FIX / "orphan_js.html", "--directive", DIRECTIVE, "--css", extra
        )
        self.assertEqual(proc.returncode, 0, res["violations"])

    def test_dynamic_class_fragments_skipped(self):
        page = Path(TMP) / "dyn.html"
        page.write_text(
            "<style>.pill{} .on{}</style>\n<script>\n"
            "const a = `<span class=\"pill status-${s}\">x</span>`;\n"
            "const b = `<i class=\"pill ${s === 'ok' ? 'on' : ''}\">y</i>`;\n"
            "</script>\n"
        )
        proc, res = run_json(page, "--directive", DIRECTIVE)
        self.assertEqual(proc.returncode, 0, res["violations"])

    def test_tailwind_utilities_ignored(self):
        page = Path(TMP) / "tw.html"
        page.write_text(
            '<script src="https://cdn.tailwindcss.com"></script>\n'
            '<div class="flex p-4 text-sm md:grid my-widget"></div>\n'
        )
        _, res = run_json(page, "--directive", DIRECTIVE)
        orphans = [
            v["message"] for v in res["violations"] if v["rule"] == "orphan-class"
        ]
        self.assertEqual(orphans, [".my-widget is used but defined in no CSS in scope"])


class TokenFiles(unittest.TestCase):
    def test_hex_allowed_in_token_file_only(self):
        d = FIX / "tokens_case"
        _, res = run_json(
            d / "tokens.css",
            d / "components.css",
            "--directive",
            d / "style_directive.md",
        )
        self.assertIn("raw-hex-outside-tokens", res["rules_run"])
        files = {(v["rule"], Path(v["file"]).name) for v in res["violations"]}
        self.assertEqual(files, {("raw-hex-outside-tokens", "components.css")})


class ReservedTokens(unittest.TestCase):
    def test_bleed_and_own_folder(self):
        state = Path(TMP) / "brand-state"
        state.mkdir(exist_ok=True)
        (state / "config.json").write_text(
            json.dumps(
                {
                    "brand": {
                        "own_brand_folders": ["agency-own"],
                        "reserved_tokens": {
                            "fonts": ["Fraunces"],
                            "colors": ["#10B981"],
                        },
                    }
                }
            )
        )
        env = dict(ENV, DESIGN_AGENCY_STATE_DIR=str(state))
        _, res = run_json(FIX / "landing_clean.html", "--directive", DIRECTIVE, env=env)
        bleed = [
            v["message"]
            for v in res["violations"]
            if v["rule"] == "reserved-token-bleed"
        ]
        self.assertTrue(any("Fraunces" in m for m in bleed))
        self.assertTrue(any("#10b981" in m for m in bleed))

        own = Path(TMP) / "agency-own"
        own.mkdir(exist_ok=True)
        shutil.copy(FIX / "landing_clean.html", own / "page.html")
        proc, res = run_json(own / "page.html", "--directive", DIRECTIVE, env=env)
        self.assertEqual(proc.returncode, 0, res["violations"])


class Report(unittest.TestCase):
    def test_report_contents(self):
        report = Path(TMP) / "enforcer_report.md"
        proc = run(
            FIX / "landing_dirty.html",
            "--directive",
            FIX / "style_directive_waiver.md",
            "--report",
            report,
        )
        self.assertEqual(proc.returncode, 1)
        text = report.read_text()
        self.assertIn("# Style Enforcement Report", text)
        self.assertIn(f"`{FIX / 'style_directive_waiver.md'}`", text)
        self.assertIn("**Surface mode:** persuade", text)
        self.assertRegex(text, r"\*\*Generated:\*\* \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
        self.assertIn("**Verdict:** FAIL", text)
        self.assertIn("| Rule | File | Line | Excerpt | Message |", text)
        self.assertIn("| `z-index-literal` |", text)
        self.assertIn("## Waived", text)
        self.assertIn("| `em-dash` |", text)

    def test_pass_report(self):
        report = Path(TMP) / "pass_report.md"
        proc = run(
            FIX / "landing_clean.html", "--directive", DIRECTIVE, "--report", report
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("**Verdict:** PASS", report.read_text())


class Cli(unittest.TestCase):
    def test_list_rules(self):
        proc = run("--list-rules")
        self.assertEqual(proc.returncode, 0)
        for rule in ("raw-hex-off-palette", "orphan-class", "missing-tabular-nums"):
            self.assertIn(rule, proc.stdout)

    def test_usage_errors(self):
        self.assertEqual(run(FIX / "landing_clean.html").returncode, 2)
        self.assertEqual(run(FIX / "nope.html", "--directive", DIRECTIVE).returncode, 2)
        self.assertEqual(
            run(FIX / "landing_clean.html", "--directive", FIX / "nope.md").returncode,
            2,
        )
        self.assertEqual(
            run(DIRECTIVE, "--directive", DIRECTIVE).returncode, 2
        )  # .md unsupported


if __name__ == "__main__":
    unittest.main()
