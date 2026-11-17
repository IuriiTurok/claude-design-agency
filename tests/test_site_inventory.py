#!/usr/bin/env python3
"""Unit tests for execution/site_inventory.py (site inventory + parity gate).

No network: every site is a small dist folder built in a tempdir and captured
with `capture --dist-dir`. The CLI runs as a subprocess, as in test_enforce.py.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "execution" / "site_inventory.py"

HOME = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Kanzlei  Muster</title>
<meta name="description" content="Steuerberatung in Kiel.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://example.com/">
<link rel="alternate" hreflang="de" href="https://example.com/">
<link rel="alternate" hreflang="en" href="https://example.com/en/">
<meta property="og:title" content="Kanzlei Muster">
<meta property="og:image" content="https://example.com/og.png">
<link rel="stylesheet" href="/assets/site.css">
<style>.x { color: red; } /* twenty words that must never be counted as visible text */</style>
<script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [
  {"@type": "Organization", "name": "Muster", "address": {"@type": "PostalAddress"}},
  {"@type": ["WebSite"], "url": "https://example.com/"}
]}
</script>
<script src="/assets/app.js" type="module"></script>
<script src="/assets/legacy.js" defer></script>
</head>
<body>
<nav id="nav">
  <a href="/kontakt/">Kontakt</a>
  <a href="/leistungen.html#preise">Preise</a>
  <a href="#team">Team</a>
  <a href="https://other.example.org/x">Extern</a>
  <a href="mailto:hi@example.com">Mail</a>
</nav>
<h1>Steuer\u00adberatung
   mit Plan</h1>
<h2>Leistungen</h2>
<a class="btn btn-primary" href="/kontakt/">Termin   buchen</a>
<a role="button" href="/leistungen.html">Mehr</a>
<img src="/img/hero.jpg?v=2" alt="Team" width="1200" height="800" fetchpriority="high">
<img src="/img/logo.svg" loading="lazy">
<section id="team"><h2>Team</h2><p>Eins zwei drei vier.</p></section>
<script>var hidden = "these words are script text";</script>
</body>
</html>
"""

KONTAKT = """<!doctype html>
<html lang="de">
<head>
<title>Kontakt</title>
<link rel="canonical" href="https://example.com/kontakt/">
</head>
<body>
<h1>Kontakt</h1>
<form action="/api/contact" method="POST">
  <input type="hidden" name="source" value="site">
  <label>Name <input name="name" required autocomplete="name"></label>
  <label>E-Mail <input type="email" name="email" required autocomplete="email"></label>
  <label>Telefon <input type="tel" name="phone"></label>
  <label>Nachricht <textarea name="message"></textarea></label>
  <button type="submit">Senden</button>
</form>
</body>
</html>
"""

LEISTUNGEN = """<!doctype html>
<html lang="de">
<head><title>Leistungen</title></head>
<body>
<h1>Leistungen</h1>
<h2 id="preise">Preise</h2>
<p>%s</p>
</body>
</html>
""" % " ".join(["wort"] * 100)

ALT = """<!doctype html>
<html lang="de">
<head><title>Alte Seite</title></head>
<body><h1>Alt</h1><p>Inhalt der alten Seite.</p></body>
</html>
"""

BASE = {
    "index.html": HOME,
    "kontakt/index.html": KONTAKT,
    "leistungen.html": LEISTUNGEN,
    "alt/index.html": ALT,
}

TMP = None
BEFORE = None
_n = 0


def setUpModule():
    global TMP, BEFORE
    TMP = Path(tempfile.mkdtemp(prefix="site-inventory-test-"))
    BEFORE = capture(BASE)


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=TMP,
    )


def build(pages):
    global _n
    _n += 1
    dist = TMP / f"site{_n}"
    for rel, text in pages.items():
        f = dist / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    return dist


def capture(pages, *args):
    dist = build(pages)
    out = Path(str(dist) + ".json")
    proc = run("capture", "--dist-dir", dist, "--out", out, *args)
    assert proc.returncode == 0, proc.stderr
    return out


def swap(rel, old, new, pages=None):
    pages = dict(pages or BASE)
    assert old in pages[rel], f"{old!r} not in {rel}"
    pages[rel] = pages[rel].replace(old, new)
    return pages


def compare(after_pages, *args):
    """(exit code, {family: [messages]} for FAIL, same for WARN, report text)."""
    global _n
    after = capture(after_pages)
    _n += 1
    report = TMP / f"report{_n}.md"
    proc = run("compare", BEFORE, after, "--report", report, *args)
    text = report.read_text(encoding="utf-8") if report.exists() else ""
    return proc, text


def section(report, heading):
    """Body of one `## heading` block of the report."""
    out, on = [], False
    for line in report.splitlines():
        if line.startswith("## "):
            on = line == f"## {heading}"
            continue
        if on:
            out.append(line)
    return "\n".join(out)


class Capture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = json.loads(BEFORE.read_text(encoding="utf-8"))
        cls.home = cls.inv["pages"]["/"]
        cls.kontakt = cls.inv["pages"]["/kontakt/"]

    def test_top_level_and_paths(self):
        self.assertEqual(
            set(self.inv), {"captured_at", "source", "page_count", "pages"}
        )
        self.assertRegex(self.inv["captured_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(self.inv["page_count"], 4)
        self.assertEqual(
            list(self.inv["pages"]), ["/", "/alt/", "/kontakt/", "/leistungen.html"]
        )
        self.assertEqual(self.home["path"], "/")
        self.assertEqual(self.home["status"], 200)
        self.assertEqual(self.home["html_bytes"], len(HOME.encode("utf-8")))

    def test_head_fields(self):
        h = self.home
        self.assertEqual(h["lang"], "de")
        self.assertEqual(h["title"], "Kanzlei Muster")
        self.assertEqual(h["meta_description"], "Steuerberatung in Kiel.")
        self.assertEqual(h["robots"], "index, follow")
        self.assertEqual(h["canonical"], "https://example.com/")
        self.assertEqual(
            h["hreflang"],
            {"de": "https://example.com/", "en": "https://example.com/en/"},
        )
        self.assertEqual(
            h["og"], {"title": "Kanzlei Muster", "image": "https://example.com/og.png"}
        )
        self.assertEqual(h["stylesheets"], ["/assets/site.css"])
        self.assertEqual(
            h["scripts"],
            [
                {
                    "src": "/assets/app.js",
                    "async": False,
                    "defer": False,
                    "module": True,
                },
                {
                    "src": "/assets/legacy.js",
                    "async": False,
                    "defer": True,
                    "module": False,
                },
            ],
        )

    def test_headings_strip_soft_hyphens_and_whitespace(self):
        self.assertEqual(self.home["h1"], ["Steuerberatung mit Plan"])
        self.assertEqual(self.home["h2"], ["Leistungen", "Team"])

    def test_jsonld_types_inside_graph(self):
        self.assertEqual(
            self.home["jsonld_types"], ["Organization", "PostalAddress", "WebSite"]
        )

    def test_ids_and_links(self):
        self.assertEqual(self.home["ids"], ["nav", "team"])
        self.assertEqual(self.home["internal_links"], ["/kontakt/", "/leistungen.html"])
        self.assertEqual(
            self.home["anchor_links"], ["/leistungen.html#preise", "/#team"]
        )

    def test_ctas(self):
        self.assertEqual(
            self.home["ctas"],
            [
                {"text": "Termin buchen", "href": "/kontakt/", "tag": "a"},
                {"text": "Mehr", "href": "/leistungen.html", "tag": "a"},
            ],
        )
        self.assertEqual(
            self.kontakt["ctas"], [{"text": "Senden", "href": None, "tag": "button"}]
        )

    def test_forms(self):
        (form,) = self.kontakt["forms"]
        self.assertEqual(form["action"], "/api/contact")
        self.assertEqual(form["method"], "post")
        self.assertEqual(form["hidden_fields"], ["source"])
        self.assertEqual(
            form["fields"],
            [
                {
                    "name": "name",
                    "type": "text",
                    "required": True,
                    "autocomplete": "name",
                },
                {
                    "name": "email",
                    "type": "email",
                    "required": True,
                    "autocomplete": "email",
                },
                {
                    "name": "phone",
                    "type": "tel",
                    "required": False,
                    "autocomplete": None,
                },
                {
                    "name": "message",
                    "type": "textarea",
                    "required": False,
                    "autocomplete": None,
                },
            ],
        )

    def test_images(self):
        self.assertEqual(
            self.home["images"],
            [
                {
                    "src": "/img/hero.jpg?v=2",
                    "alt_present": True,
                    "has_dimensions": True,
                    "loading": None,
                    "fetchpriority": "high",
                    "ext": "jpg",
                },
                {
                    "src": "/img/logo.svg",
                    "alt_present": False,
                    "has_dimensions": False,
                    "loading": "lazy",
                    "fetchpriority": None,
                    "ext": "svg",
                },
            ],
        )

    def test_word_count_excludes_script_style_and_head(self):
        # nav 5 + h1 3 + h2 1 + CTAs 3 + section 5
        self.assertEqual(self.home["word_count"], 17)
        self.assertEqual(self.inv["pages"]["/leistungen.html"]["word_count"], 102)

    def test_include_exclude_limit(self):
        inv = json.loads(capture(BASE, "--exclude", "/alt/*").read_text())
        self.assertNotIn("/alt/", inv["pages"])
        inv = json.loads(
            capture(BASE, "--include", "/kontakt/*", "--include", "/").read_text()
        )
        self.assertEqual(list(inv["pages"]), ["/", "/kontakt/"])
        inv = json.loads(capture(BASE, "--limit", "2").read_text())
        self.assertEqual(inv["page_count"], 2)

    def test_usage_errors(self):
        self.assertEqual(run().returncode, 2)
        self.assertEqual(run("capture", "--out", TMP / "x.json").returncode, 2)
        self.assertEqual(
            run(
                "capture", "--dist-dir", TMP / "nope", "--out", TMP / "x.json"
            ).returncode,
            2,
        )
        self.assertEqual(
            run(
                "capture", "--base-url", "ftp://example.com", "--out", TMP / "x.json"
            ).returncode,
            2,
        )


class ComparePass(unittest.TestCase):
    def test_identical_site_passes(self):
        proc, report = compare(BASE)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        lines = report.splitlines()
        self.assertEqual(lines[0], "# Site Parity Report")
        self.assertEqual(lines[1], "Verdict: PASS")
        self.assertIn("0 FAIL", report)
        self.assertEqual(section(report, "FAIL").strip(), "None.")
        self.assertIn("PASS", proc.stdout)

    def test_path_spellings_are_one_page(self):
        pages = dict(BASE)
        pages["leistungen/index.html"] = pages.pop("leistungen.html")
        proc, report = compare(pages)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("### broken-link", report)
        self.assertNotIn("### new-page", report)

    def test_warnings_do_not_fail(self):
        pages = swap("index.html", "Steuerberatung in Kiel.", "Neu getextet.")
        pages = swap("index.html", "mit Plan</h1>", "ohne Plan</h1>", pages)
        pages = swap("index.html", 'alt="Team" width="1200" height="800"', "", pages)
        pages = swap(
            "index.html", 'href="/kontakt/">Kontakt', 'href="/weg/">Kontakt', pages
        )
        pages = swap("leistungen.html", " ".join(["wort"] * 100), "kurz", pages)
        pages["neu/index.html"] = ALT
        proc, report = compare(pages)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(report.splitlines()[1], "Verdict: PASS")
        warn = section(report, "WARN")
        for family in (
            "meta-description",
            "h1",
            "word-count",
            "broken-link",
            "img-alt",
            "img-dimensions",
            "new-page",
        ):
            self.assertIn(f"### {family} (", warn)
        self.assertIn("`/weg/`", warn)
        self.assertIn("`/neu/`", warn)
        self.assertIn("2 image(s) without alt", warn)


class CompareFail(unittest.TestCase):
    def assertFails(self, pages, family, needle, *args):
        proc, report = compare(pages, *args)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(report.splitlines()[1], "Verdict: FAIL")
        fail = section(report, "FAIL")
        self.assertIn(f"### {family} (", fail)
        self.assertIn(needle, fail)
        return fail

    def test_missing_page(self):
        pages = dict(BASE)
        del pages["alt/index.html"]
        fail = self.assertFails(
            pages, "missing-page", "`/alt/`: present before, missing after"
        )
        self.assertEqual(
            len([ln for ln in fail.splitlines() if ln.startswith("- ")]), 1
        )

    def test_moved_page(self):
        pages = dict(BASE)
        pages["neu/index.html"] = pages.pop("alt/index.html")
        proc, report = compare(pages, "--moved", "/alt/=/neu/")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("### new-page", report)
        self.assertFails(
            pages, "missing-page", "`/alt/`", "--moved", "/alt/=/nirgends/"
        )

    def test_redirects_file(self):
        pages = dict(BASE)
        pages["neu/index.html"] = pages.pop("alt/index.html")
        vercel = TMP / "vercel.json"
        vercel.write_text(
            json.dumps(
                {
                    "redirects": [
                        {"source": "/alt", "destination": "/neu", "permanent": True},
                        {"source": "/blog/:slug", "destination": "/news/:slug"},
                    ]
                }
            )
        )
        proc, _ = compare(pages, "--redirects", vercel)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_lang(self):
        self.assertFails(
            swap("index.html", '<html lang="de">', '<html lang="en">'),
            "lang",
            "`de` -> `en`",
        )

    def test_canonical(self):
        self.assertFails(
            swap("kontakt/index.html", "example.com/kontakt/", "example.com/contact/"),
            "canonical",
            "https://example.com/contact/",
        )

    def test_hreflang(self):
        pages = swap(
            "index.html",
            '<link rel="alternate" hreflang="en" href="https://example.com/en/">',
            "",
        )
        self.assertFails(pages, "hreflang", "removed en")

    def test_jsonld(self):
        pages = swap(
            "index.html", '{"@type": ["WebSite"], "url": "https://example.com/"}', "{}"
        )
        self.assertFails(pages, "jsonld", "JSON-LD type removed: WebSite")

    def test_title(self):
        self.assertFails(
            swap(
                "kontakt/index.html",
                "<title>Kontakt</title>",
                "<title>Schreiben Sie uns</title>",
            ),
            "title",
            '"Kontakt" -> "Schreiben Sie uns"',
        )

    def test_form_removed(self):
        self.assertFails(
            swap("kontakt/index.html", 'action="/api/contact"', 'action="/api/lead"'),
            "form",
            "form action=`/api/contact` removed",
        )

    def test_form_field_removed(self):
        pages = swap(
            "kontakt/index.html",
            '<label>Telefon <input type="tel" name="phone"></label>',
            "",
        )
        self.assertFails(pages, "form-field", "field `phone` removed")

    def test_form_field_required_changed(self):
        pages = swap("kontakt/index.html", 'name="email" required', 'name="email"')
        self.assertFails(pages, "form-field", "field `email` is now optional")

    def test_form_hidden_field_removed(self):
        pages = swap(
            "kontakt/index.html", '<input type="hidden" name="source" value="site">', ""
        )
        self.assertFails(pages, "form-field", "hidden field `source` removed")

    def test_anchor_cross_page(self):
        pages = swap("leistungen.html", '<h2 id="preise">', '<h2 id="kosten">')
        self.assertFails(pages, "anchor", "`/leistungen.html`: id `#preise` is gone")

    def test_anchor_same_page(self):
        pages = swap("index.html", '<section id="team">', "<section>")
        self.assertFails(pages, "anchor", "`/`: id `#team` is gone")


class Waive(unittest.TestCase):
    PAGES = swap("index.html", "<title>Kanzlei  Muster</title>", "<title>Neu</title>")

    def test_waive_by_path(self):
        proc, report = compare(self.PAGES, "--waive", "title:/")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(report.splitlines()[1], "Verdict: PASS")
        self.assertIn("### title (1)", section(report, "Intentional (waived)"))
        self.assertIn("1 intentional", report)

    def test_waive_whole_family(self):
        proc, _ = compare(self.PAGES, "--waive", "title")
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_waive_other_path_or_family_does_not_apply(self):
        proc, _ = compare(self.PAGES, "--waive", "title:/kontakt/*")
        self.assertEqual(proc.returncode, 1)
        proc, _ = compare(self.PAGES, "--waive", "canonical:/")
        self.assertEqual(proc.returncode, 1)

    def test_waive_path_glob(self):
        pages = swap(
            "kontakt/index.html",
            '<label>Telefon <input type="tel" name="phone"></label>',
            "",
        )
        proc, _ = compare(pages, "--waive", "form-field:/kont*")
        self.assertEqual(proc.returncode, 0, proc.stdout)


class ReportAndCli(unittest.TestCase):
    def test_family_capped_at_40_lines(self):
        many = dict(BASE)
        for i in range(45):
            many[f"p/{i:02d}.html"] = ALT
        before = capture(many)
        after = capture(BASE)
        report = TMP / "cap_report.md"
        proc = run("compare", before, after, "--report", report)
        self.assertEqual(proc.returncode, 1)
        fail = section(report.read_text(encoding="utf-8"), "FAIL")
        self.assertIn("### missing-page (45)", fail)
        lines = [ln for ln in fail.splitlines() if ln.startswith("- ")]
        self.assertEqual(len(lines), 41)
        self.assertEqual(lines[-1], "- +5 more")
        self.assertLess(len(proc.stdout.splitlines()), 30)  # one-screen summary

    def test_usage_errors(self):
        self.assertEqual(run("compare", BEFORE).returncode, 2)
        self.assertEqual(run("compare", BEFORE, TMP / "nope.json").returncode, 2)
        self.assertEqual(
            run("compare", BEFORE, BEFORE, "--waive", "bogus").returncode, 2
        )
        self.assertEqual(run("compare", BEFORE, BEFORE, "--moved", "/a").returncode, 2)
        not_inventory = TMP / "not_inventory.json"
        not_inventory.write_text("[]")
        self.assertEqual(run("compare", BEFORE, not_inventory).returncode, 2)


if __name__ == "__main__":
    unittest.main()
