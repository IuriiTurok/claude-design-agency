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
            orphans,
            {".ghost-panel", ".is-zz", ".row-on", ".badge-q", ".esc-cls", ".nest-on"},
        )

    def test_extra_css_resolves(self):
        extra = Path(TMP) / "extra.css"
        extra.write_text(
            ".ghost-panel{} .is-zz{} .row-on{} .badge-q{} .esc-cls{} .nest-on{}"
        )
        proc, res = run_json(
            FIX / "orphan_js.html", "--directive", DIRECTIVE, "--css", extra
        )
        self.assertEqual(proc.returncode, 0, res["violations"])

    def test_dynamic_class_fragments_skipped(self):
        page = Path(TMP) / "dyn.html"
        page.write_text(
            "<style>.pill{} .on{}</style>\n<script>\n"
            'const a = `<span class="pill status-${s}">x</span>`;\n'
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


class PageQualityRules(unittest.TestCase):
    """v0.6.0 accessibility / performance / conversion rules: one positive
    and one negative case each."""

    def lint(self, name, body, *extra):
        page = Path(TMP) / name
        page.write_text(body)
        return run_json(page, "--directive", DIRECTIVE, *extra)[1]

    def hits(self, res, rule):
        return [v for v in res["violations"] if v["rule"] == rule]

    def test_img_alt_missing(self):
        res = self.lint(
            "pq_alt.html",
            '<img src="a.png" width="10" height="10">\n'
            '<img src="b.png" alt="" width="10" height="10">\n'
            '<img src="c.png" alt="A chart" title="no alt here" width="10" height="10">\n'
            "<script>const t = '<img src=\"d.png\">';</script>\n",
        )
        got = self.hits(res, "img-alt-missing")
        self.assertEqual([v["line"] for v in got], [1])
        self.assertEqual(set(got[0]), {"rule", "file", "line", "excerpt", "message"})

    def test_img_alt_missing_jsx(self):
        res = self.lint(
            "pq_alt.tsx",
            "export const A = (p) => (\n"
            "  <>\n"
            "    <img src={p.src} />\n"
            "    <img src={p.src} alt={p.alt} />\n"
            "    <img {...p} />\n"
            "    <Img src={p.src} />\n"
            "  </>\n"
            ");\n",
        )
        self.assertEqual([v["line"] for v in self.hits(res, "img-alt-missing")], [3])
        # sizes live in CSS / parent components there: HTML-only rules stay off
        self.assertNotIn("img-dimensions-missing", res["rules_run"])
        self.assertNotIn("form-control-unlabelled", res["rules_run"])
        self.assertNotIn("heading-level-skip", res["rules_run"])

    def test_img_dimensions_missing(self):
        res = self.lint(
            "pq_dims.html",
            '<img src="a.png" alt="">\n'
            '<img src="b.png" alt="" width="10">\n'
            '<img src="c.png" alt="" width="10" height="10">\n'
            '<img src="d.png" alt="" style="width:100%; aspect-ratio: 16 / 9">\n',
        )
        self.assertEqual(
            [v["line"] for v in self.hits(res, "img-dimensions-missing")], [1, 2]
        )

    def test_html_lang_missing(self):
        res = self.lint(
            "pq_lang_bad.html", "<!doctype html>\n<html>\n<body></body></html>\n"
        )
        self.assertEqual([v["line"] for v in self.hits(res, "html-lang-missing")], [2])
        res = self.lint(
            "pq_lang_ok.html",
            '<!doctype html>\n<html lang="de">\n<body></body></html>\n',
        )
        self.assertEqual(self.hits(res, "html-lang-missing"), [])
        res = self.lint("pq_lang_fragment.html", "<section><p>partial</p></section>\n")
        self.assertEqual(self.hits(res, "html-lang-missing"), [])

    def test_form_control_unlabelled(self):
        res = self.lint(
            "pq_form.html",
            "<form>\n"
            '<input type="email" name="email" placeholder="Email">\n'
            '<select name="plan"><option>A</option></select>\n'
            '<textarea name="msg"></textarea>\n'
            '<label for="n">Name</label><input id="n" name="name">\n'
            '<label>Company <input name="org"></label>\n'
            '<input name="q" aria-label="Search">\n'
            '<input name="t" title="Phone">\n'
            '<input type="hidden" name="token">\n'
            '<input name="trap" hidden>\n'
            '<input type="submit" value="Send">\n'
            "</form>\n",
        )
        got = self.hits(res, "form-control-unlabelled")
        self.assertEqual([v["line"] for v in got], [2, 3, 4])
        self.assertIn("<input email>", got[0]["message"])

    def test_heading_level_skip(self):
        res = self.lint(
            "pq_headings.html",
            "<h1>One</h1>\n<h2>Two</h2>\n<h4>Four</h4>\n<h2>Back up is fine</h2>\n<h3>Three</h3>\n",
        )
        got = self.hits(res, "heading-level-skip")
        self.assertEqual([v["line"] for v in got], [3])
        self.assertIn("<h4> follows <h2>", got[0]["message"])
        res = self.lint(
            "pq_headings_ok.html", "<h1>One</h1>\n<h2>Two</h2>\n<h3>Three</h3>\n"
        )
        self.assertEqual(self.hits(res, "heading-level-skip"), [])

    def test_cta_contact_link(self):
        body = (
            "<style>.btn{} .btn-primary{} .hero-cta{}</style>\n"
            '<a class="btn btn-primary" href="mailto:hi@example.com">Contact us</a>\n'
            '<a class="hero-cta" href="MAILTO:hi@example.com">Write</a>\n'
            '<a href="mailto:hi@example.com">hi@example.com</a>\n'
            '<a class="btn" href="/contact/">Contact us</a>\n'
        )
        res = self.lint("pq_cta.html", body)
        self.assertEqual(
            [v["line"] for v in self.hits(res, "cta-contact-link")], [2, 3]
        )
        res = self.lint("pq_cta.html", body, "--surface", "operate")
        self.assertNotIn("cta-contact-link", res["rules_run"])

    def test_font_remote_css(self):
        res = self.lint(
            "pq_fonts.html",
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces">\n'
            '<link href="https://use.typekit.net/abc1def.css" rel="stylesheet">\n'
            '<link rel="stylesheet" href="fonts/local.css">\n',
        )
        self.assertEqual([v["line"] for v in self.hits(res, "font-remote-css")], [2, 3])
        res = self.lint(
            "pq_fonts.css",
            '@import url("https://fonts.googleapis.com/css2?family=Fraunces");\n'
            '@import "local.css";\n',
        )
        self.assertEqual([v["line"] for v in self.hits(res, "font-remote-css")], [1])

    def test_new_rules_waivable(self):
        directive = Path(TMP) / "pq_directive.md"
        directive.write_text(
            DIRECTIVE.read_text()
            + "\n## Brand Overrides\n\n- allow `font-remote-css` — fonts stay on the Google CDN (client decision)\n"
        )
        page = Path(TMP) / "pq_waived.html"
        page.write_text(
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces">\n'
        )
        proc, res = run_json(page, "--directive", directive)
        self.assertEqual(proc.returncode, 0, res["violations"])
        self.assertEqual([w["rule"] for w in res["waived"]], ["font-remote-css"])


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
        for rule in (
            "raw-hex-off-palette",
            "orphan-class",
            "missing-tabular-nums",
            "img-alt-missing",
            "img-dimensions-missing",
            "html-lang-missing",
            "form-control-unlabelled",
            "heading-level-skip",
            "cta-contact-link",
            "font-remote-css",
        ):
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
