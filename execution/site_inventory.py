#!/usr/bin/env python3
r"""Site inventory and redesign parity gate (stdlib only, Python 3.9+).

Usage:

  python3 execution/site_inventory.py capture (--base-url URL | --dist-dir DIR)
      --out FILE.json [--limit N] [--include GLOB]... [--exclude GLOB]...
  python3 execution/site_inventory.py compare BEFORE.json AFTER.json
      [--moved OLD=NEW]... [--redirects vercel.json]
      [--waive FIELD[:PATHGLOB]]... [--report out.md]

capture   Inventories every page into JSON. --base-url reads /sitemap.xml
          (following sitemap indexes) and falls back to crawling internal
          links from / when there is no usable sitemap. --dist-dir walks
          *.html in a build folder (a/index.html -> /a/, x.html -> /x.html).
          --include / --exclude are globs on the URL path. Exit 0, or 2 on a
          usage / IO error or when nothing could be captured.

compare   Parity gate for a redesign: what the old site promised to search
          engines, assistive tech and form backends must still be there.
          Exit 0 = PASS, 1 = FAIL, 2 = usage error.

  FAIL families (waivable with --waive):
    missing-page  page in BEFORE with no page in AFTER (after --moved / --redirects)
    lang          <html lang> changed
    canonical     canonical URL changed (not checked for moved pages)
    hreflang      hreflang map changed (language set only, for moved pages)
    jsonld        a JSON-LD @type was removed
    title         <title> changed
    form          a form (matched by action) was removed
    form-field    a field name or hidden field was removed, or `required` flipped
    anchor        an id that an internal #fragment link pointed at is gone
  WARN families (never fail the gate):
    meta-description, h1, word-count (drop > 30 %), broken-link, img-alt,
    img-dimensions, new-page

  Paths are matched after normalising: /a, /a/, /a.html and /a/index.html are
  the same page, so a live capture and a dist capture line up. A page that
  was not served with a 2xx status is treated as absent.
  --moved OLD=NEW        the page moved; compare OLD (before) with NEW (after).
  --redirects FILE       vercel.json; literal `source` entries of its
                         `redirects` array count as moves (patterns are skipped).
  --waive FIELD[:GLOB]   list that FAIL family as intentional instead, e.g.
                         --waive title:/  or  --waive form-field:/unternehmen/*
"""

import argparse
import fnmatch
import gzip
import html as htmllib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib import error, request
from urllib.parse import unquote, urljoin, urlsplit

USER_AGENT = "site-inventory/1.0"
TIMEOUT = 20
WORKERS = 8
DEFAULT_LIMIT = 300
LOCAL_BASE = "http://site.invalid"

SKIP_TEXT_TAGS = {"script", "style", "template", "noscript", "title"}
NON_FIELD_TYPES = {"submit", "button", "reset", "image"}
CTA_CLASS_RE = re.compile(r"btn|button|cta", re.I)
NON_LINK_SCHEME_RE = re.compile(
    r"(?i)^(?:mailto|tel|sms|javascript|data|blob|whatsapp):"
)
PAGE_EXT_RE = re.compile(r"\.(?:html?|php|aspx?)$", re.I)
FILE_EXT_RE = re.compile(r"\.[A-Za-z0-9]{1,5}$")

FAIL_FAMILIES = (
    "missing-page",
    "lang",
    "canonical",
    "hreflang",
    "jsonld",
    "title",
    "form",
    "form-field",
    "anchor",
)
WARN_FAMILIES = (
    "meta-description",
    "h1",
    "word-count",
    "broken-link",
    "img-alt",
    "img-dimensions",
    "new-page",
)
MAX_LINES_PER_FAMILY = 40


class UsageError(Exception):
    pass


def clean(text):
    """Collapse whitespace and drop soft hyphens."""
    return " ".join((text or "").replace("­", "").split())


def dedupe(items):
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def strip_www(host):
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


# ---------------------------------------------------------------------------
# Page parsing
# ---------------------------------------------------------------------------


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = None
        self.meta = {}
        self.canonical = None
        self.hreflang = {}
        self.h1 = []
        self.h2 = []
        self.jsonld_blocks = []
        self.ids = []
        self.hrefs = []
        self.ctas = []
        self.forms = []
        self.images = []
        self.stylesheets = []
        self.scripts = []
        self.words = 0
        self._skip = 0
        self._svg = 0
        self._form = None
        self._jsonld = None
        self._title = None
        self._captures = []  # [tag, text parts, callback]

    def _capture(self, tag, callback):
        self._captures.append([tag, [], callback])

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "svg":
            self._svg += 1
        if tag in SKIP_TEXT_TAGS:
            self._skip += 1

        if tag == "html":
            self.lang = a.get("lang", "").strip() or self.lang
        elif tag == "title":
            if not self._svg and self.title is None:
                self._title = []
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").strip().lower()
            if name and name not in self.meta:
                self.meta[name] = clean(a.get("content"))
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            href = a.get("href", "").strip()
            if "canonical" in rel and href and self.canonical is None:
                self.canonical = href
            if "alternate" in rel and a.get("hreflang") and href:
                self.hreflang[a["hreflang"].strip()] = href
            if "stylesheet" in rel and href:
                self.stylesheets.append(href)
        elif tag == "script":
            kind = a.get("type", "").strip().lower()
            if a.get("src"):
                self.scripts.append(
                    {
                        "src": a["src"].strip(),
                        "async": "async" in a,
                        "defer": "defer" in a,
                        "module": kind == "module",
                    }
                )
            if kind == "application/ld+json":
                self._jsonld = []
        elif tag in ("h1", "h2"):
            self._capture(tag, getattr(self, tag).append)
        elif tag == "a":
            if a.get("name"):
                self.ids.append(a["name"])
            if "href" in a:
                self.hrefs.append(a["href"])
            if CTA_CLASS_RE.search(a.get("class", "")) or a.get("role") == "button":
                self._cta("a", a.get("href"))
        elif tag == "button":
            kind = a.get("type", "").strip().lower()
            if (
                CTA_CLASS_RE.search(a.get("class", ""))
                or a.get("role") == "button"
                or kind == "submit"
                or (not kind and self._form is not None)
            ):
                self._cta("button", None)
        elif tag == "form":
            self._form = {
                "action": a.get("action", "").strip() or None,
                "method": (a.get("method", "").strip() or "get").lower(),
                "fields": [],
                "hidden_fields": [],
            }
            self.forms.append(self._form)
        elif tag == "img":
            src = (a.get("src") or a.get("data-src") or "").strip()
            ext = FILE_EXT_RE.search(urlsplit(src).path)
            self.images.append(
                {
                    "src": src,
                    "alt_present": "alt" in a,
                    "has_dimensions": bool(a.get("width") and a.get("height")),
                    "loading": a.get("loading") or None,
                    "fetchpriority": a.get("fetchpriority") or None,
                    "ext": ext.group(0)[1:].lower() if ext else None,
                }
            )
            if a.get("alt"):
                for cap in self._captures:
                    cap[1].append(" " + a["alt"] + " ")

        if tag in ("input", "select", "textarea"):
            self._control(tag, a)

    def _cta(self, tag, href):
        entry = {"text": "", "href": href, "tag": tag}
        self.ctas.append(entry)
        self._capture(tag, lambda text: entry.update(text=text))

    def _control(self, tag, a):
        kind = a.get("type", "").strip().lower() or "text" if tag == "input" else tag
        if tag == "input" and kind == "submit":
            self.ctas.append(
                {"text": clean(a.get("value")), "href": None, "tag": "input"}
            )
        if self._form is None:
            return
        name = a.get("name", "").strip() or None
        if kind == "hidden":
            if name:
                self._form["hidden_fields"].append(name)
        elif kind not in NON_FIELD_TYPES:
            self._form["fields"].append(
                {
                    "name": name,
                    "type": kind,
                    "required": "required" in a or a.get("aria-required") == "true",
                    "autocomplete": a.get("autocomplete") or None,
                }
            )

    def handle_endtag(self, tag):
        if tag == "svg":
            self._svg = max(0, self._svg - 1)
        if tag in SKIP_TEXT_TAGS:
            self._skip = max(0, self._skip - 1)
        if tag == "title" and self._title is not None:
            self.title = clean("".join(self._title))
            self._title = None
        elif tag == "script" and self._jsonld is not None:
            self.jsonld_blocks.append("".join(self._jsonld))
            self._jsonld = None
        elif tag == "form":
            self._form = None
        for i in range(len(self._captures) - 1, -1, -1):
            if self._captures[i][0] == tag:
                _, parts, callback = self._captures.pop(i)
                callback(clean("".join(parts)))
                break

    def handle_data(self, data):
        if self._jsonld is not None:
            self._jsonld.append(data)
            return
        if self._title is not None:
            self._title.append(data)
        if self._skip:
            return
        self.words += len(clean(data).split())
        for cap in self._captures:
            cap[1].append(data)

    def close(self):
        super().close()
        while self._captures:  # unclosed <h1>/<a>: keep what was read
            _, parts, callback = self._captures.pop()
            callback(clean("".join(parts)))


def jsonld_types(blocks):
    types = set()

    def walk(node):
        if isinstance(node, dict):
            kind = node.get("@type")
            if isinstance(kind, str):
                types.add(kind)
            elif isinstance(kind, list):
                types.update(k for k in kind if isinstance(k, str))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for raw in blocks:
        try:
            walk(json.loads(raw))
        except ValueError:
            continue
    return sorted(types)


def link_targets(hrefs, base, site_hosts):
    """(internal link paths, 'path#fragment' links) for hrefs on the page at
    `base`. A bare `#x` is a fragment link to the page itself, not a link."""
    base_host = urlsplit(base).netloc.lower()
    links, anchors = [], []
    for href in hrefs:
        href = href.strip()
        if not href or NON_LINK_SCHEME_RE.match(href):
            continue
        try:
            u = urlsplit(urljoin(base, href))
        except ValueError:
            continue
        if u.scheme not in ("http", "https"):
            continue
        host = u.netloc.lower()
        if host != base_host and strip_www(host) not in site_hosts:
            continue
        path = u.path or "/"
        if u.fragment:
            anchors.append(path + "#" + unquote(u.fragment))
        if not href.startswith("#"):
            links.append(path)
    return dedupe(links), dedupe(anchors)


def build_record(text, path, status, final_url, html_bytes, base, site_hosts):
    p = PageParser()
    try:
        p.feed(text)
        p.close()
    except Exception as e:  # malformed markup must not abort the inventory
        print(f"site_inventory: warning: {path}: parse error: {e}", file=sys.stderr)
    hosts = set(site_hosts)
    if p.canonical:
        hosts.add(strip_www(urlsplit(p.canonical).netloc))
    hosts.discard("")
    links, anchors = link_targets(p.hrefs, base, hosts)
    return {
        "path": path,
        "status": status,
        "final_url": final_url,
        "html_bytes": html_bytes,
        "lang": p.lang,
        "title": p.title,
        "meta_description": p.meta.get("description"),
        "robots": p.meta.get("robots"),
        "canonical": p.canonical,
        "hreflang": p.hreflang,
        "og": {"title": p.meta.get("og:title"), "image": p.meta.get("og:image")},
        "h1": p.h1,
        "h2": p.h2,
        "jsonld_types": jsonld_types(p.jsonld_blocks),
        "ids": dedupe(p.ids),
        "internal_links": links,
        "anchor_links": anchors,
        "ctas": p.ctas,
        "forms": p.forms,
        "images": p.images,
        "stylesheets": p.stylesheets,
        "scripts": p.scripts,
        "word_count": p.words,
    }


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------


def path_filter(include, exclude):
    def keep(path):
        if include and not any(fnmatch.fnmatchcase(path, g) for g in include):
            return False
        return not any(fnmatch.fnmatchcase(path, g) for g in exclude)

    return keep


def capture_dist(dist, limit, keep):
    paths = {}
    for f in sorted(dist.rglob("*.html")):
        rel = f.relative_to(dist).as_posix()
        if rel == "index.html":
            path = "/"
        elif rel.endswith("/index.html"):
            path = "/" + rel[: -len("index.html")]
        else:
            path = "/" + rel
        if keep(path):
            paths[path] = f
    pages = {}
    for path in sorted(paths)[:limit]:
        raw = paths[path].read_bytes()
        pages[path] = build_record(
            raw.decode("utf-8", "replace"),
            path,
            200,
            None,
            len(raw),
            LOCAL_BASE + path,
            set(),
        )
    return pages


def fetch(url):
    """(status, final url, headers, body, error). Status 0 = no response."""
    req = request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.geturl(), resp.headers, resp.read(), None
    except error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, e.geturl() or url, e.headers, body, None
    except Exception as e:  # URLError, timeout, TLS, bad URL
        return 0, url, None, b"", str(e)


def decode(body, headers):
    if body[:2] == b"\x1f\x8b":
        try:
            body = gzip.decompress(body)
        except (OSError, EOFError):
            pass
    charset = headers.get_content_charset() if headers is not None else None
    try:
        return body.decode(charset or "utf-8", "replace")
    except LookupError:
        return body.decode("utf-8", "replace")


def fetch_page(url, site_hosts):
    path = urlsplit(url).path or "/"
    status, final_url, headers, body, err = fetch(url)
    ctype = headers.get_content_type() if headers is not None else ""
    text = decode(body, headers) if (not ctype or "html" in ctype) else ""
    record = build_record(
        text, path, status, final_url, len(body), final_url, site_hosts
    )
    if err:
        record["error"] = err
    return record


def sitemap_urls(base_url):
    queue, seen, urls = [urljoin(base_url, "/sitemap.xml")], set(), []
    while queue and len(seen) < 50:
        sitemap = queue.pop(0)
        if sitemap in seen:
            continue
        seen.add(sitemap)
        status, _, headers, body, _ = fetch(sitemap)
        if status != 200:
            continue
        text = decode(body, headers)
        locs = [
            htmllib.unescape(loc.strip())
            for loc in re.findall(
                r"<loc>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</loc>", text, re.S | re.I
            )
        ]
        if re.search(r"<sitemapindex\b", text, re.I):
            queue += locs
        else:
            urls += locs
    return dedupe(urls)


def capture_live(base_url, limit, keep):
    root = urljoin(base_url, "/")
    site_hosts = {strip_www(urlsplit(root).netloc)}
    targets = {}
    for url in sitemap_urls(base_url):
        u = urlsplit(url)
        path = u.path or "/"
        if strip_www(u.netloc) in site_hosts and keep(path) and path not in targets:
            targets[path] = url
    pages = {}
    with ThreadPoolExecutor(WORKERS) as pool:
        if targets:
            urls = [targets[p] for p in sorted(targets)[:limit]]
            for rec in pool.map(lambda u: fetch_page(u, site_hosts), urls):
                pages[rec["path"]] = rec
            return pages, "sitemap"
        # No usable sitemap: breadth-first crawl of internal links from /.
        seen, frontier, fetched = {"/"}, ["/"], 0
        while frontier and fetched < limit:
            batch, frontier = frontier[: limit - fetched], frontier[limit - fetched :]
            fetched += len(batch)
            results = pool.map(
                lambda p: fetch_page(urljoin(root, p), site_hosts), batch
            )
            for rec in results:
                if keep(rec["path"]):
                    pages[rec["path"]] = rec
                for link in rec["internal_links"]:
                    is_page = PAGE_EXT_RE.search(link) or not FILE_EXT_RE.search(link)
                    if link not in seen and is_page and (keep(link) or link == "/"):
                        seen.add(link)
                        frontier.append(link)
    return pages, "crawl"


def cmd_capture(args):
    keep = path_filter(args.include, args.exclude)
    if args.limit < 1:
        raise UsageError("--limit must be at least 1")
    if args.dist_dir:
        dist = Path(args.dist_dir)
        if not dist.is_dir():
            raise UsageError(f"--dist-dir not found: {dist}")
        pages, source, how = capture_dist(dist, args.limit, keep), str(dist), "dist"
    else:
        if urlsplit(args.base_url).scheme not in ("http", "https"):
            raise UsageError("--base-url must start with http:// or https://")
        pages, how = capture_live(args.base_url, args.limit, keep)
        source = args.base_url
    if not pages:
        raise UsageError(f"no pages captured from {source}")
    inventory = {
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "page_count": len(pages),
        "pages": {path: pages[path] for path in sorted(pages)},
    }
    try:
        Path(args.out).write_text(
            json.dumps(inventory, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError as e:
        raise UsageError(f"cannot write {args.out}: {e}")
    bad = sum(1 for r in pages.values() if not ok_status(r))
    print(
        f"site_inventory capture: {len(pages)} page(s) via {how} from {source}"
        f" ({bad} not 2xx) -> {args.out}"
    )
    return 0


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


def norm_path(path):
    """/a, /a/, /a.html and /a/index.html are one page."""
    p = unquote(urlsplit(path).path or "/")
    p = re.sub(r"/index\.html?$", "/", p)
    p = re.sub(r"\.html?$", "", p)
    if len(p) > 1:
        p = p.rstrip("/")
    return p or "/"


def ok_status(record):
    status = record.get("status")
    return status is None or 200 <= status < 300


def load_inventory(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise UsageError(f"cannot read inventory {path}: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("pages"), dict):
        raise UsageError(f"{path} is not a site_inventory capture (no `pages`)")
    return data


def load_moves(moved, redirects_file):
    """{normalised old path: normalised new path, or None when it leaves the site}."""
    moves = {}
    if redirects_file:
        try:
            cfg = json.loads(Path(redirects_file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise UsageError(f"cannot read --redirects {redirects_file}: {e}")
        rules = cfg.get("redirects") if isinstance(cfg, dict) else None
        for rule in rules if isinstance(rules, list) else []:
            if not isinstance(rule, dict):
                continue
            src, dst = rule.get("source"), rule.get("destination")
            if not isinstance(src, str) or not isinstance(dst, str):
                continue
            if re.search(r"[:*()?\[\]{}|+$^\\]", src) or re.search(
                r"[:$]\w", urlsplit(dst).path
            ):
                continue  # pattern / parameterised rule: literal sources only
            moves[norm_path(src)] = (
                None if re.match(r"(?i)https?://", dst) else norm_path(dst)
            )
    for item in moved:
        old, sep, new = item.partition("=")
        if not sep or not old.strip() or not new.strip():
            raise UsageError(f"--moved expects OLD=NEW, got: {item}")
        moves[norm_path(old.strip())] = norm_path(new.strip())
    return moves


def parse_waivers(items):
    waivers = []
    for item in items:
        family, _, glob = item.partition(":")
        if family not in FAIL_FAMILIES:
            raise UsageError(
                f"--waive: unknown field `{family}`; known: {', '.join(FAIL_FAMILIES)}"
            )
        waivers.append((family, glob or None))
    return waivers


def short(text, width=70):
    text = clean(text)
    return text if len(text) <= width else text[: width - 1] + "…"


def forms_by_action(record):
    out = {}
    for form in record.get("forms") or []:
        out.setdefault((form.get("action") or "").strip(), []).append(form)
    return out


def compare_page(b, a, path, was_moved, add):
    b_lang, a_lang = (b.get("lang") or "").lower(), (a.get("lang") or "").lower()
    if b_lang and b_lang != a_lang:
        add("FAIL", "lang", path, f"lang `{b_lang}` -> `{a_lang or 'none'}`")

    b_can, a_can = (
        (b.get("canonical") or "").strip(),
        (a.get("canonical") or "").strip(),
    )
    if b_can and b_can != a_can and not was_moved:
        add("FAIL", "canonical", path, f"canonical `{b_can}` -> `{a_can or 'none'}`")

    b_hl, a_hl = b.get("hreflang") or {}, a.get("hreflang") or {}
    if was_moved:
        b_hl, a_hl = dict.fromkeys(b_hl), dict.fromkeys(a_hl)
    if b_hl and b_hl != a_hl:
        parts = []
        removed = sorted(set(b_hl) - set(a_hl))
        added = sorted(set(a_hl) - set(b_hl))
        changed = sorted(k for k in set(b_hl) & set(a_hl) if b_hl[k] != a_hl[k])
        if removed:
            parts.append("removed " + ", ".join(removed))
        if added:
            parts.append("added " + ", ".join(added))
        if changed:
            parts.append("href changed for " + ", ".join(changed))
        add("FAIL", "hreflang", path, "hreflang " + "; ".join(parts))

    gone = sorted(set(b.get("jsonld_types") or []) - set(a.get("jsonld_types") or []))
    if gone:
        add("FAIL", "jsonld", path, "JSON-LD type removed: " + ", ".join(gone))

    b_title, a_title = clean(b.get("title")), clean(a.get("title"))
    if b_title and b_title != a_title:
        add("FAIL", "title", path, f'title "{short(b_title)}" -> "{short(a_title)}"')

    a_forms = forms_by_action(a)
    for action, before_forms in forms_by_action(b).items():
        label = f"form action=`{action or '(none)'}`"
        after_forms = a_forms.get(action, [])
        for i, bf in enumerate(before_forms):
            if i >= len(after_forms):
                add("FAIL", "form", path, f"{label} removed")
                continue
            af = after_forms[i]
            a_fields = {f["name"]: f for f in af.get("fields") or [] if f.get("name")}
            for f in bf.get("fields") or []:
                name = f.get("name")
                if not name:
                    continue
                if name not in a_fields:
                    add("FAIL", "form-field", path, f"{label}: field `{name}` removed")
                elif bool(f.get("required")) != bool(a_fields[name].get("required")):
                    now = "required" if a_fields[name].get("required") else "optional"
                    add(
                        "FAIL",
                        "form-field",
                        path,
                        f"{label}: field `{name}` is now {now}",
                    )
            for name in bf.get("hidden_fields") or []:
                if name not in (af.get("hidden_fields") or []):
                    add(
                        "FAIL",
                        "form-field",
                        path,
                        f"{label}: hidden field `{name}` removed",
                    )

    b_desc, a_desc = clean(b.get("meta_description")), clean(a.get("meta_description"))
    if b_desc and b_desc != a_desc:
        add("WARN", "meta-description", path, f'"{short(b_desc)}" -> "{short(a_desc)}"')
    b_h1 = [clean(h) for h in b.get("h1") or []]
    a_h1 = [clean(h) for h in a.get("h1") or []]
    if b_h1 and b_h1 != a_h1:
        add(
            "WARN",
            "h1",
            path,
            f'h1 "{short(" | ".join(b_h1))}" -> "{short(" | ".join(a_h1))}"',
        )
    b_words, a_words = b.get("word_count") or 0, a.get("word_count") or 0
    if b_words and a_words < 0.7 * b_words:
        drop = round(100 * (b_words - a_words) / b_words)
        add(
            "WARN",
            "word-count",
            path,
            f"word count dropped {drop} % ({b_words} -> {a_words})",
        )


def compare(before, after, moves, waivers):
    b_pages = {norm_path(p): r for p, r in before["pages"].items() if ok_status(r)}
    a_pages = {norm_path(p): r for p, r in after["pages"].items() if ok_status(r)}
    findings = []

    def add(level, family, path, message):
        findings.append(
            {"level": level, "family": family, "path": path, "message": message}
        )

    def resolve(path):
        """(after path or None when it leaves the site, was moved)."""
        target, hops = path, 0
        while target in moves and hops < 5:
            target, hops = moves[target], hops + 1
            if target is None:
                return None, True
        return target, hops > 0

    counterpart = {}
    for bp in sorted(b_pages):
        record = b_pages[bp]
        shown = record.get("path") or bp
        target, was_moved = resolve(bp)
        if target is None:
            continue
        if target not in a_pages:
            why = (
                f"moved to {target}, which is not in AFTER"
                if was_moved
                else "present before, missing after"
            )
            add("FAIL", "missing-page", shown, why)
            continue
        counterpart[bp] = target
        compare_page(record, a_pages[target], shown, was_moved, add)

    # Fragment targets that BEFORE linked to must survive.
    wanted = {}
    for record in b_pages.values():
        for link in record.get("anchor_links") or []:
            path, _, fragment = link.partition("#")
            wanted.setdefault((norm_path(path), fragment), []).append(
                record.get("path")
            )
    for (target, fragment), sources in sorted(wanted.items()):
        old = b_pages.get(target)
        if (
            old is None
            or fragment not in (old.get("ids") or [])
            or target not in counterpart
        ):
            continue
        if fragment not in (a_pages[counterpart[target]].get("ids") or []):
            add(
                "FAIL",
                "anchor",
                old.get("path") or target,
                f"id `#{fragment}` is gone; linked from {len(sources)} page(s), e.g. {sources[0]}",
            )

    known = set(counterpart.values())
    broken = {}
    for ap in sorted(a_pages):
        record = a_pages[ap]
        shown = record.get("path") or ap
        if ap not in known:
            add("WARN", "new-page", shown, "new page (not in BEFORE)")
        for link in record.get("internal_links") or []:
            if FILE_EXT_RE.search(link) and not PAGE_EXT_RE.search(link):
                continue  # asset, not a page
            target = norm_path(link)
            if target not in a_pages and target not in moves:
                broken.setdefault(link, []).append(shown)
        images = record.get("images") or []
        for family, key, what in (
            ("img-alt", "alt_present", "without alt"),
            ("img-dimensions", "has_dimensions", "without width/height"),
        ):
            bad = [img.get("src") or "(no src)" for img in images if not img.get(key)]
            if bad:
                add(
                    "WARN",
                    family,
                    shown,
                    f"{len(bad)} image(s) {what}, e.g. {short(bad[0], 60)}",
                )
    for link in sorted(broken):
        sources = broken[link]
        add(
            "WARN",
            "broken-link",
            link,
            f"linked from {len(sources)} page(s), e.g. {sources[0]}, but not in AFTER",
        )

    for f in findings:
        if f["level"] != "FAIL":
            continue
        for family, glob in waivers:
            if family == f["family"] and (
                glob is None
                or fnmatch.fnmatchcase(f["path"], glob)
                or fnmatch.fnmatchcase(norm_path(f["path"]), glob)
            ):
                f["level"] = "INTENTIONAL"
                break

    counts = {
        level: sum(1 for f in findings if f["level"] == level)
        for level in ("FAIL", "WARN", "INTENTIONAL")
    }
    return {
        "verdict": "FAIL" if counts["FAIL"] else "PASS",
        "counts": counts,
        "findings": findings,
        "pages": {
            "before": len(b_pages),
            "after": len(a_pages),
            "matched": len(counterpart),
        },
    }


def grouped(findings, level):
    """[(family, [findings])] for one level, in the documented family order."""
    order = list(FAIL_FAMILIES) + list(WARN_FAMILIES)
    groups = {}
    for f in findings:
        if f["level"] == level:
            groups.setdefault(f["family"], []).append(f)
    return [(family, groups[family]) for family in order if family in groups]


def render_report(result, before, after, before_path, after_path):
    c = result["counts"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = [
        "# Site Parity Report",
        f"Verdict: {result['verdict']}",
        "",
        f"- **Counts:** {c['FAIL']} FAIL, {c['WARN']} WARN, {c['INTENTIONAL']} intentional (waived)",
        f"- **Pages:** {result['pages']['before']} before, {result['pages']['after']} after,"
        f" {result['pages']['matched']} matched",
        f"- **Before:** `{before_path}` ({before.get('source')}, captured {before.get('captured_at')})",
        f"- **After:** `{after_path}` ({after.get('source')}, captured {after.get('captured_at')})",
        f"- **Generated:** {now}",
    ]
    for level, heading in (
        ("FAIL", "FAIL"),
        ("WARN", "WARN"),
        ("INTENTIONAL", "Intentional (waived)"),
    ):
        out += ["", f"## {heading}", ""]
        groups = grouped(result["findings"], level)
        if not groups:
            out.append("None.")
            continue
        for i, (family, items) in enumerate(groups):
            if i:
                out.append("")
            out += [f"### {family} ({len(items)})", ""]
            for f in items[:MAX_LINES_PER_FAMILY]:
                out.append(f"- `{f['path']}`: {f['message']}")
            if len(items) > MAX_LINES_PER_FAMILY:
                out.append(f"- +{len(items) - MAX_LINES_PER_FAMILY} more")
    return "\n".join(out) + "\n"


def render_summary(result):
    c = result["counts"]
    out = [
        f"site_inventory compare: {result['verdict']}: {c['FAIL']} FAIL, {c['WARN']} WARN,"
        f" {c['INTENTIONAL']} intentional; pages {result['pages']['before']} before,"
        f" {result['pages']['after']} after, {result['pages']['matched']} matched"
    ]
    for level in ("FAIL", "WARN", "INTENTIONAL"):
        for family, items in grouped(result["findings"], level):
            first = items[0]
            out.append(
                f"  {level:<11} {family:<16} {len(items):>4}  {first['path']}: {short(first['message'], 80)}"
            )
    return "\n".join(out)


def cmd_compare(args):
    before, after = load_inventory(args.before), load_inventory(args.after)
    moves = load_moves(args.moved, args.redirects)
    result = compare(before, after, moves, parse_waivers(args.waive))
    if args.report:
        try:
            Path(args.report).write_text(
                render_report(result, before, after, args.before, args.after),
                encoding="utf-8",
            )
        except OSError as e:
            raise UsageError(f"cannot write report: {e}")
    print(render_summary(result))
    if args.report:
        print(f"report: {args.report}")
    return 1 if result["verdict"] == "FAIL" else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Site inventory and redesign parity gate.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cap = sub.add_parser(
        "capture", help="inventory a live site or a dist folder into JSON"
    )
    src = cap.add_mutually_exclusive_group(required=True)
    src.add_argument("--base-url")
    src.add_argument("--dist-dir")
    cap.add_argument("--out", required=True)
    cap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    cap.add_argument("--include", action="append", default=[], metavar="GLOB")
    cap.add_argument("--exclude", action="append", default=[], metavar="GLOB")

    cmp_ = sub.add_parser("compare", help="parity gate between two inventories")
    cmp_.add_argument("before")
    cmp_.add_argument("after")
    cmp_.add_argument("--moved", action="append", default=[], metavar="OLD=NEW")
    cmp_.add_argument("--redirects", metavar="FILE")
    cmp_.add_argument(
        "--waive", action="append", default=[], metavar="FIELD[:PATHGLOB]"
    )
    cmp_.add_argument("--report", metavar="FILE")

    args = ap.parse_args(argv)
    try:
        return cmd_capture(args) if args.cmd == "capture" else cmd_compare(args)
    except UsageError as e:
        print(f"site_inventory: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
