#!/usr/bin/env python3
r"""Directive-driven mechanical style linter for the design-agency plugin.

Usage:

  python3 execution/enforce.py <file> [<file>...] --directive <style_directive.md>
      [--surface persuade|operate|read|experience] [--json] [--report <path.md>]
      [--css <extra.css>...]
  python3 execution/enforce.py --list-rules

Exit codes: 0 = no violations, 1 = violations, 2 = usage / IO error.

Every brand-specific value comes from the project's style_directive.md:

  palette    every #rgb / #rrggbb / #rrggbbaa anywhere in the directive, plus
             any oklch(...) literal written verbatim. An 8-digit hex whose rgb
             part is on the palette counts as an alpha variant of it.
  fonts      family names in the `## Typography` section (backticked names,
             "Family"/"Font" table columns, `font-family:` lines, and bullet
             values like `- **Body:** Geist Sans — Regular`), plus generic
             families. If the section names a system stack ("System sans",
             system-ui), the usual system-stack members are allowed too.
  tokens     a `Token files: \`a.css\`, \`b.css\`` line (relative to the
             directive's dir), plus any tokens.css / *.tokens.css / theme.css /
             globals.css that holds only custom properties (and @font-face).
             Raw hex is allowed inside token files.
  surface    `SURFACE_MODE: <mode>` / `Surface mode: <mode>` in the directive
             or a sibling visual_philosophy.md; --surface overrides; otherwise
             inferred per file (.tsx/.jsx/.vue/.svelte/.ts/.js -> operate,
             everything else -> persuade).
  overrides  `## Brand Overrides` lines `- allow \`<rule-id>\` — <reason>`
             move that rule's hits from violations to waived.
  reserved   reserved_tokens / own_brand_folders / carve_outs come from
             state_paths.brand_config(), the same source as `state_paths.py
             --brand`.

Ported from tworocks/tools/audit.sh: Rule 2 (raw hex outside tokens), Rule 4
(div onclick), Rule 5 (z-index literals; threshold widened to >= 10), Rule 6
(spinners, now gated on the Do Not List naming spinners), Rule 11 (inline
<style> blocks: every rule here scans them, since inline styles are part of the
file) and Rule 12 (orphan classes, with the JS string-literal gap fixed:
classes applied via `className = "..."`, `classList.add/toggle/replace(...)`,
`setAttribute('class', ...)`, template literals and `class="..."` inside JS
strings are now checked; classes referenced as JS selectors still count as
resolved behaviour hooks, as in audit.sh).

Skipped, with reasons:
  Rule 1  glass allowlist   — the allowlisted selectors are repo-specific and
                              the directive format has no machine-readable list.
  Rule 3  Lucide-only glyphs — icon-library choice is repo-specific.
  Rule 7  doc/showcase parity — depends on one repo's docs layout.
  Rule 8  deleted classes   — needs a per-repo class list the directive lacks.
  Rules 9/10 px token migration — keyed off repo-specific baseline markers.
  The orphan-class baseline list is dropped: use Brand Overrides to waive.
  Tailwind's named z-index scale (z-10..z-50) is treated as a theme token;
  only z-[N] arbitrary values and zIndex literals are flagged.
  `font:` shorthand is not parsed; only font-family / fontFamily / font-[..] /
  Google Fonts links are.
"""

import argparse
import html as htmllib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state_paths  # noqa: E402

SURFACES = ("persuade", "operate", "read", "experience")

MARKUP_EXTS = {".html", ".htm", ".vue", ".svelte"}
SCRIPT_EXTS = {".tsx", ".jsx", ".ts", ".js"}
CSS_EXTS = {".css", ".scss"}
SUPPORTED_EXTS = MARKUP_EXTS | SCRIPT_EXTS | CSS_EXTS
OPERATE_EXTS = {".tsx", ".jsx", ".vue", ".svelte", ".ts", ".js"}

RULES = {
    "raw-hex-off-palette": "Hex or oklch colour not in the directive palette (outside token files and inline <svg>).",
    "raw-hex-outside-tokens": "Any raw hex in page/component code when the directive declares `Token files:`.",
    "font-off-directive": "font-family not named in the directive's Typography section.",
    "reserved-token-bleed": "Agency-reserved font/colour used outside own_brand_folders.",
    "z-index-literal": "z-index literal >= 10 (use var(--z-*); 0-9 allowed for local stacking).",
    "div-onclick": 'onclick/onClick on a non-interactive element without role="button".',
    "transition-all": "transition: all / Tailwind transition-all.",
    "loading-spinner": "Indeterminate spinner (only when the Do Not List bans spinners).",
    "orphan-class": "Class used in HTML markup or JS strings but defined in no CSS in scope.",
    "em-dash": "Em-dash (U+2014) in visible text.",
    "h-screen-hero": "Full-viewport height (h-screen / 100vh / 100dvh) on the hero or first section.",
    "scroll-cue": '"Scroll down" copy or bouncing chevron scroll cue.',
    "section-number-eyebrow": 'Numbered eyebrow ("01 —", "/ 02", "§ 03") next to a section heading.',
    "missing-tabular-nums": "Numeric table/KPI content with no tabular-nums / font-variant-numeric.",
}

# Override ids judged by the LLM gates (taste-guardian, visual-qa), not here.
# Accepted in Brand Overrides without a warning; they waive nothing in this script.
PROSE_RULE_IDS = {
    "mono-data-labels",
    "near-black-accent",
    "eyebrow-labels",
    "identical-card-grid",
    "cream-serif-terracotta",
}

# Rules restricted to some surfaces; anything absent runs on every surface.
RULE_SURFACES = {
    "em-dash": {"persuade", "read"},
    "h-screen-hero": {"persuade"},
    "scroll-cue": {"persuade"},
    "section-number-eyebrow": {"persuade"},
    "missing-tabular-nums": {"operate"},
}

GENERIC_FAMILIES = {
    "serif",
    "sans-serif",
    "monospace",
    "cursive",
    "fantasy",
    "system-ui",
    "ui-serif",
    "ui-sans-serif",
    "ui-monospace",
    "ui-rounded",
    "math",
    "emoji",
    "fangsong",
    "-apple-system",
    "blinkmacsystemfont",
    "inherit",
    "initial",
    "unset",
    "revert",
    "revert-layer",
    "apple color emoji",
    "segoe ui emoji",
    "segoe ui symbol",
    "noto color emoji",
}
SYSTEM_STACK = {
    "segoe ui",
    "roboto",
    "helvetica neue",
    "helvetica",
    "arial",
    "noto sans",
    "ubuntu",
    "cantarell",
    "oxygen",
    "sf pro text",
    "sf pro display",
    "sf mono",
    "menlo",
    "monaco",
    "consolas",
    "liberation mono",
    "courier new",
}

HEX_RE = re.compile(
    r"(?<![&\w#])#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])"
)
OKLCH_RE = re.compile(r"oklch\([^()]*\)", re.I)
TAG_OPEN_RE = re.compile(
    r"<([A-Za-z][\w.-]*)\b((?:[^<>{}\"']|\"[^\"]*\"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\})*)>",
    re.S,
)
HTML_REGION_RE = re.compile(
    r"(?P<comment><!--.*?-->)"
    r"|(?P<script><script\b[^>]*>.*?</script\s*>)"
    r"|(?P<style><style\b[^>]*>.*?</style\s*>)"
    r"|(?P<tag><[A-Za-z/!][^>]*>)",
    re.S | re.I,
)
SVG_RE = re.compile(r"<svg\b.*?</svg\s*>", re.S | re.I)
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.S | re.I)
SCRIPT_BLOCK_RE = re.compile(r"<script\b[^>]*>(.*?)</script\s*>", re.S | re.I)


# ---------------------------------------------------------------------------
# Text views — every view keeps the original length and newlines, so a match
# offset in any view maps to the same line in the source.
# ---------------------------------------------------------------------------


def blank(s):
    if not isinstance(s, str):
        s = s.group(0)
    return re.sub(r"[^\n]", " ", s)


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", blank, s, flags=re.S)
    return re.sub(r"(?<![:\\\"'\w(])//[^\n]*", blank, s)


def markup_views(text):
    """code: tags + script + style (text nodes and comments blanked).
    visible: text nodes only. nodes: tags + text nodes (no script/style)."""
    code, visible, nodes = [], [], []
    pos = 0
    for m in HTML_REGION_RE.finditer(text):
        gap = text[pos : m.start()]
        code.append(blank(gap))
        visible.append(gap)
        nodes.append(gap)
        chunk, kind = m.group(0), m.lastgroup
        if kind == "comment":
            code.append(blank(chunk))
            nodes.append(blank(chunk))
        elif kind in ("script", "style"):
            code.append(chunk)
            nodes.append(blank(chunk))
        else:
            code.append(chunk)
            nodes.append(chunk)
        visible.append(blank(chunk))
        pos = m.end()
    tail = text[pos:]
    code.append(blank(tail))
    visible.append(tail)
    nodes.append(tail)
    return {
        "code": strip_comments("".join(code)),
        "visible": "".join(visible),
        "nodes": "".join(nodes),
    }


def file_views(text, ext):
    if ext in MARKUP_EXTS:
        return markup_views(text)
    code = strip_comments(text)
    if ext in CSS_EXTS:
        return {"code": code, "visible": blank(text), "nodes": blank(text)}
    return {"code": code, "visible": code, "nodes": code}


def make_hit(rule, path, text, offset, message):
    line_no = text.count("\n", 0, offset) + 1
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    line = text[start:] if end == -1 else text[start:end]
    excerpt = line.strip()
    if len(excerpt) > 120:
        lo = max(0, offset - start - 50)
        excerpt = line[lo : lo + 120].strip()
    return {
        "rule": rule,
        "file": path,
        "line": line_no,
        "excerpt": excerpt,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Directive parsing
# ---------------------------------------------------------------------------


def norm_hex(value):
    h = value.lstrip("#").lower()
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    return h if len(h) in (6, 8) and re.fullmatch(r"[0-9a-f]+", h) else None


def norm_oklch(value):
    return re.sub(r"\s+", " ", value.lower()).replace("( ", "(").replace(" )", ")")


def section(text, title):
    """Body of the first heading whose name starts with `title` (lowercase),
    up to the next heading of the same or higher level."""
    out, level = [], None
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if m:
            lvl, name = len(m.group(1)), m.group(2).strip().lower()
            if level is not None and lvl <= level:
                break
            if level is None and name.startswith(title):
                level = lvl
                continue
        if level is not None:
            out.append(line)
    return "\n".join(out)


def _add_font(names, raw):
    name = raw.strip().strip("`*").strip().strip("\"'").strip()
    name = re.sub(r"\s*!important$", "", name).strip()
    if not name or name.startswith("--") or name[0].isdigit():
        return
    if any(c in name for c in "():;=/"):
        return
    names.add(name.lower())


def parse_fonts(text):
    sec = section(text, "typography")
    names = set()
    for m in re.finditer(r"`([^`]+)`", sec):
        for part in m.group(1).split(","):
            _add_font(names, part)
    for m in re.finditer(r"font-family\s*:\s*([^;\n`]+)", sec, re.I):
        for part in m.group(1).split(","):
            _add_font(names, part)
    for m in re.finditer(r"^\s*[-*]\s+\*\*[^*\n]+\*\*:?\s*(.+)$", sec, re.M):
        value = m.group(1).replace("`", "")
        _add_font(names, re.split(r"\s[—–-]\s|[,(;]", value)[0])
    # Markdown tables: take the cells of any Family/Font column.
    rows = [line for line in sec.splitlines() if line.strip().startswith("|")]
    cols = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if not cols and any(re.search(r"family|font", c, re.I) for c in cells):
            cols = [
                i for i, c in enumerate(cells) if re.search(r"family|font", c, re.I)
            ]
            continue
        if cols and not re.fullmatch(r"[\s|:-]+", row):
            for i in cols:
                if i < len(cells):
                    for part in cells[i].split(","):
                        _add_font(names, part)
    if re.search(r"system[\s-]?(sans|ui|stack|font)|-apple-system", sec, re.I):
        names |= SYSTEM_STACK
    return names


def parse_directive(path):
    text = path.read_text(encoding="utf-8")
    palette = {h for h in (norm_hex(m.group(0)) for m in HEX_RE.finditer(text)) if h}
    oklch = {norm_oklch(m.group(0)) for m in OKLCH_RE.finditer(text)}

    token_files, tokens_declared = set(), False
    m = re.search(r"^[\s>*-]*\**Token files?\**\s*:\s*(.+)$", text, re.I | re.M)
    if m:
        tokens_declared = True
        raw = re.findall(r"`([^`]+)`", m.group(1)) or m.group(1).split(",")
        for p in raw:
            p = p.strip()
            if p:
                token_files.add((path.parent / p).resolve())

    surface = None
    mode_re = re.compile(
        r"(?:SURFACE_MODE|Surface[ _]mode)\**\s*[:=]\s*\**\s*`?(persuade|operate|read|experience)\b",
        re.I,
    )
    for source in (path, path.parent / "visual_philosophy.md"):
        try:
            src = text if source == path else source.read_text(encoding="utf-8")
        except OSError:
            continue
        sm = mode_re.search(src)
        if sm:
            surface = sm.group(1).lower()
            break

    overrides = {}
    for om in re.finditer(
        r"^\s*[-*]\s*allow\s+`([^`]+)`\s*(?:[—–:-]+\s*(.*))?$",
        section(text, "brand overrides"),
        re.I | re.M,
    ):
        rule_id = om.group(1).strip()
        if rule_id in PROSE_RULE_IDS:
            continue
        if rule_id not in RULES:
            print(
                f"enforce: warning: Brand Overrides names unknown rule `{rule_id}` (ignored)",
                file=sys.stderr,
            )
            continue
        overrides[rule_id] = (om.group(2) or "").strip() or "Brand override"

    return {
        "path": path,
        "palette": palette,
        "oklch": oklch,
        "fonts": parse_fonts(text),
        "token_files": token_files,
        "tokens_declared": tokens_declared,
        "surface": surface,
        "overrides": overrides,
        "bans_spinners": "spinner" in section(text, "do not").lower(),
    }


# ---------------------------------------------------------------------------
# Shared extractors
# ---------------------------------------------------------------------------


def hex_matches(code):
    """Yield (offset, normalised hex) for colour hex literals in code."""
    for m in HEX_RE.finditer(code):
        before = code[max(0, m.start() - 20) : m.start()]
        if re.search(r"(?:href\s*=\s*[\"']?|url\(\s*[\"']?)$", before, re.I):
            continue
        if re.match(r"\s*\{", code[m.end() : m.end() + 10]):
            continue  # CSS id selector
        h = norm_hex(m.group(0))
        if h:
            yield m.start(), h


def _split_families(value):
    out = []
    for part in value.split(","):
        p = part.strip()
        if not p:
            continue
        if p[0] in "\"'":
            end = p.find(p[0], 1)
            out.append(p[1:end] if end > 0 else p[1:])
            continue
        q = re.search(r"[\"'>]", p)
        out.append(p[: q.start()] if q else p)
        if q:
            break  # value ended mid-part (style attribute closed)
    names = []
    for n in out:
        n = re.sub(r"\s*!important\s*$", "", n).strip()
        if n and not n.lower().startswith("var(") and not n[0].isdigit():
            names.append(n)
    return names


def font_families(code):
    """Yield (offset, family name) for every font-family usage in code."""
    for m in re.finditer(r"(?<![\w-])font-family\s*:\s*([^;{}\n<]+)", code, re.I):
        for name in _split_families(m.group(1)):
            yield m.start(), name
    for m in re.finditer(r"\bfontFamily\s*:\s*([\"'`])(.*?)\1", code):
        for name in _split_families(m.group(2)):
            yield m.start(), name
    for m in re.finditer(r"(?<![\w-])font-\[([^\]]+)\]", code):
        value = m.group(1).replace("_", " ")
        if re.fullmatch(r"\d+", value) or "var(" in value or ":" in value:
            continue
        for name in _split_families(value):
            yield m.start(), name
    for m in re.finditer(r"fonts\.googleapis\.com/css2?\?([^\"'\s>)]+)", code):
        for fam in re.findall(r"family=([^&:]+)", m.group(1)):
            yield m.start(), fam.replace("+", " ").replace("%20", " ")


def font_allowed(name, allowed):
    n = name.lower().strip()
    if n in GENERIC_FAMILIES or n in allowed:
        return True
    return any(a.startswith(n + " ") or n.startswith(a + " ") for a in allowed)


def only_custom_props(css):
    css = re.sub(r"@font-face\s*\{[^{}]*\}", "", strip_comments(css), flags=re.I)
    decls = 0
    for body in re.findall(r"\{([^{}]*)\}", css):
        for decl in body.split(";"):
            if not decl.strip():
                continue
            if not decl.strip().startswith("--"):
                return False
            decls += 1
    return decls > 0


def is_token_file(path, text, directive):
    if path.resolve() in directive["token_files"]:
        return True
    name = path.name.lower()
    if name in ("tokens.css", "theme.css", "globals.css") or name.endswith(
        ".tokens.css"
    ):
        return only_custom_props(text)
    return False


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def css_scope(path, text, ext, extra_css):
    """All CSS text the file can see: inline <style>, linked/imported local
    stylesheets, and --css files."""
    parts = list(extra_css)
    if ext in CSS_EXTS:
        parts.append(text)
    if ext in MARKUP_EXTS:
        parts += STYLE_BLOCK_RE.findall(text)
        for tag in re.findall(r"<link\b[^>]*>", text, re.I):
            if not re.search(r"rel\s*=\s*[\"']?stylesheet", tag, re.I):
                continue
            href = re.search(r"href\s*=\s*[\"']([^\"']+)[\"']", tag, re.I)
            if href and not re.match(r"^(?:[a-z]+:)?//", href.group(1), re.I):
                parts.append(
                    _read(path.parent / href.group(1).split("?")[0].split("#")[0])
                )
    for imp in re.findall(r"""import\s+['"](\.[^'"]+\.s?css)['"]""", text):
        parts.append(_read(path.parent / imp))
    return "\n".join(parts)


def _under(path, folder, directive_dir):
    """True if path sits inside folder. A relative folder is repo-relative, so
    it also matches as a run of path components anywhere in the file's path."""
    p = path.resolve()
    f = Path(folder).expanduser()
    if not f.is_absolute():
        parts, fp = p.parts, f.parts
        if fp and any(parts[i:i + len(fp)] == fp for i in range(len(parts) - len(fp))):
            return True
    bases = [f] if f.is_absolute() else [Path.cwd() / f, directive_dir / f]
    for b in bases:
        try:
            p.relative_to(b.resolve())
            return True
        except (ValueError, OSError):
            continue
    return False


# ---------------------------------------------------------------------------
# Rules — each takes the per-file context and returns a list of hits.
# ---------------------------------------------------------------------------


def rule_raw_hex_off_palette(c):
    if c["is_token_file"]:
        return []
    d = c["directive"]
    code = SVG_RE.sub(blank, c["views"]["code"])
    hits = []
    for off, h in hex_matches(code):
        if h in d["palette"] or (len(h) == 8 and h[:6] in d["palette"]):
            continue
        hits.append(
            make_hit(
                "raw-hex-off-palette",
                c["display"],
                c["text"],
                off,
                f"#{h} is not in the directive palette",
            )
        )
    for m in OKLCH_RE.finditer(code):
        if norm_oklch(m.group(0)) not in d["oklch"]:
            hits.append(
                make_hit(
                    "raw-hex-off-palette",
                    c["display"],
                    c["text"],
                    m.start(),
                    f"{m.group(0)} is not in the directive palette",
                )
            )
    return hits


def rule_raw_hex_outside_tokens(c):
    if c["is_token_file"]:
        return []
    code = SVG_RE.sub(blank, c["views"]["code"])
    return [
        make_hit(
            "raw-hex-outside-tokens",
            c["display"],
            c["text"],
            off,
            f"raw #{h} outside the declared token files; use var(--*)",
        )
        for off, h in hex_matches(code)
    ]


def rule_font_off_directive(c):
    allowed = c["directive"]["fonts"]
    return [
        make_hit(
            "font-off-directive",
            c["display"],
            c["text"],
            off,
            f'font "{name}" is not named in the directive\'s Typography section',
        )
        for off, name in font_families(c["views"]["code"])
        if not font_allowed(name, allowed)
    ]


def rule_reserved_token_bleed(c):
    brand, path, ddir = c["brand"], c["path"], c["directive"]["path"].parent
    rt = brand.get("reserved_tokens") or {}
    fonts = {str(f).lower() for f in rt.get("fonts") or []}
    colors = {h for h in (norm_hex(str(x)) for x in rt.get("colors") or []) if h}
    if not fonts and not colors:
        return []
    if any(_under(path, f, ddir) for f in brand.get("own_brand_folders") or []):
        return []
    carved = set()
    for folder, toks in (brand.get("carve_outs") or {}).items():
        if isinstance(toks, list) and _under(path, folder, ddir):
            for t in toks:
                carved.add(norm_hex(str(t)) or str(t).lower())
    hits = []
    for off, name in font_families(c["views"]["code"]):
        if name.lower() in fonts and name.lower() not in carved:
            hits.append(
                make_hit(
                    "reserved-token-bleed",
                    c["display"],
                    c["text"],
                    off,
                    f'reserved agency font "{name}" used outside own_brand_folders',
                )
            )
    for off, h in hex_matches(c["views"]["code"]):
        if h in colors and h not in carved:
            hits.append(
                make_hit(
                    "reserved-token-bleed",
                    c["display"],
                    c["text"],
                    off,
                    f"reserved agency colour #{h} used outside own_brand_folders",
                )
            )
    return hits


def rule_z_index_literal(c):
    code, hits = c["views"]["code"], []
    for pat in (
        r"z-index\s*:\s*(\d+)",
        r"\bzIndex\s*:\s*[\"']?(\d+)",
        r"(?<![\w-])z-\[(\d+)\]",
    ):
        for m in re.finditer(pat, code, re.I):
            if int(m.group(1)) >= 10:
                hits.append(
                    make_hit(
                        "z-index-literal",
                        c["display"],
                        c["text"],
                        m.start(),
                        f"z-index {m.group(1)} literal; use a var(--z-*) token",
                    )
                )
    return hits


def rule_div_onclick(c):
    hits = []
    for m in TAG_OPEN_RE.finditer(c["views"]["code"]):
        if m.group(1).lower() not in ("div", "span", "p", "li", "td"):
            continue
        attrs = m.group(2)
        if re.search(r"\bon[cC]lick\s*=", attrs) and not re.search(
            r"\brole\s*=\s*[{\"']*\s*[\"']?button", attrs
        ):
            hits.append(
                make_hit(
                    "div-onclick",
                    c["display"],
                    c["text"],
                    m.start(),
                    f'click handler on <{m.group(1)}>; use <button> or <a>, or add role="button"',
                )
            )
    return hits


def rule_transition_all(c):
    pat = (
        r"transition(?:-property)?\s*:\s*[\"'`]?all\b|(?<![\w-])transition-all(?![\w-])"
    )
    return [
        make_hit(
            "transition-all",
            c["display"],
            c["text"],
            m.start(),
            "transition on `all`; name the properties that animate",
        )
        for m in re.finditer(pat, c["views"]["code"], re.I)
    ]


def rule_loading_spinner(c):
    pat = (
        r"class(?:Name)?\s*=\s*[\"'{`][^\"'`}]*\bspinner|(?<![\w-])animate-spin(?![\w-])"
        r"|animation(?:-name)?\s*:\s*spin\b|@keyframes\s+spin\b"
    )
    return [
        make_hit(
            "loading-spinner",
            c["display"],
            c["text"],
            m.start(),
            "indeterminate spinner; the Do Not List bans spinners",
        )
        for m in re.finditer(pat, c["views"]["code"], re.I)
    ]


TW_STANDALONE = {
    "flex",
    "grid",
    "block",
    "inline",
    "inline-block",
    "inline-flex",
    "inline-grid",
    "hidden",
    "contents",
    "flow-root",
    "relative",
    "absolute",
    "fixed",
    "sticky",
    "static",
    "container",
    "truncate",
    "uppercase",
    "lowercase",
    "capitalize",
    "normal-case",
    "italic",
    "not-italic",
    "underline",
    "overline",
    "line-through",
    "no-underline",
    "antialiased",
    "subpixel-antialiased",
    "sr-only",
    "not-sr-only",
    "visible",
    "invisible",
    "collapse",
    "grow",
    "shrink",
    "transform",
    "filter",
    "isolate",
    "tabular-nums",
    "lining-nums",
    "proportional-nums",
    "ordinal",
    "shadow",
    "rounded",
    "border",
    "ring",
    "outline",
    "transition",
    "prose",
    "group",
    "peer",
    "dark",
    "table",
    "resize",
    "italic",
}
# Spacing/size utilities only count with a scale value (p-4, w-1/2, mt-auto),
# so a project class like `my-widget` is not mistaken for margin-y.
TW_SCALE_RE = re.compile(
    r"^-?(?:p[xytrbl]?|m[xytrbl]?|w|h|size|min-w|min-h|max-w|max-h|gap|gap-[xy]"
    r"|space-[xy]|top|left|right|bottom|inset|inset-[xy]|start|end|z|order|basis"
    r"|col-span|row-span|col-start|col-end|row-start|row-end|grid-cols|grid-rows"
    r"|translate-[xy]|scale|scale-[xy]|rotate|opacity|duration|delay|leading|tracking)"
    r"-(?:\d[\d./]*|px|auto|full|screen|min|max|fit|none|svh|dvh|lvh"
    r"|(?:\d?x?s|sm|md|lg|\d?xl|prose)|\[.*\])$"
)
TW_PREFIX_RE = re.compile(
    r"^-?(?:text|bg|from|via|to|border|rounded|items|justify|content|self|place|font"
    r"|shadow|grow|shrink|flex|overflow|ring|outline|divide|transition|ease"
    r"|animate|origin|cursor|select|fill|stroke|object"
    r"|aspect|decoration|underline|line-clamp|columns|backdrop|blur|brightness"
    r"|contrast|grayscale|invert|saturate|sepia|drop-shadow|list|whitespace|break"
    r"|indent|align|accent|caret|scroll|snap|touch|will-change|mix-blend|bg-blend"
    r"|float|clear|box|table|pointer-events)-"
)
CLASS_TOKEN_RE = re.compile(r"^-?[A-Za-z_][\w-]*$")
STRING_LIT_RE = re.compile(r"([\"'`])((?:\\.|(?!\1).)*)\1", re.S)


def _class_tokens(value):
    """Class names in an attribute/string value. Static parts of template
    literals count; a token glued to an interpolation (`status-${x}`) is
    dynamic and skipped. A standalone `${...}` contributes its quoted string
    branches (`${on ? 'is-on' : ''}`), but not comparison operands."""
    tokens = []
    for m in re.finditer(r"(?<!\S)\$\{(.*?)\}(?!\S)", value, re.S):
        for lit in STRING_LIT_RE.finditer(m.group(1)):
            around = m.group(1)[max(0, lit.start() - 4):lit.end() + 4]
            if not re.search(r"[!=]=|[<>]", around):
                tokens += lit.group(2).split()
    tokens += re.sub(r"\$\{.*?\}", "\0", value, flags=re.S).split()
    return [t for t in tokens if CLASS_TOKEN_RE.match(t)]


def used_classes(code):
    """Return [(offset, class)] for classes applied in markup and in JS."""
    used = []
    markup = SCRIPT_BLOCK_RE.sub(blank, code)
    markup = STYLE_BLOCK_RE.sub(blank, markup)
    for m in re.finditer(
        r"(?<![\w:.-])class\s*=\s*([\"'])(.*?)\1", markup, re.S | re.I
    ):
        if "{{" not in m.group(2):
            used += [(m.start(), t) for t in _class_tokens(m.group(2))]
    for sm in SCRIPT_BLOCK_RE.finditer(code):
        js, base = sm.group(1), sm.start(1)
        for m in re.finditer(
            r"\bclassName\s*\+?=\s*([\"'`])((?:\\.|(?!\1).)*)\1", js, re.S
        ):
            used += [(base + m.start(), t) for t in _class_tokens(m.group(2))]
        for m in re.finditer(
            r"\bclassList\s*\.\s*(?:add|toggle|replace)\s*\(([^)]*)\)", js
        ):
            args = m.group(1)
            lits = list(STRING_LIT_RE.finditer(args))
            if "toggle" in js[m.start() : m.start() + 30]:
                lits = lits[:1]  # second arg of toggle is the force flag
            for lit in lits:
                used += [(base + m.start(), t) for t in _class_tokens(lit.group(2))]
        for m in re.finditer(
            r"""setAttribute\(\s*['"]class['"]\s*,\s*([\"'`])((?:\\.|(?!\1).)*)\1""",
            js,
            re.S,
        ):
            used += [(base + m.start(), t) for t in _class_tokens(m.group(2))]
        for m in re.finditer(r"(?<![\w:.-])class\s*=\s*\\?([\"'])((?:\$\{[^}]*\}|(?!\\?\1)[^\n`])*)\\?\1", js, re.S):
            used += [(base + m.start(), t) for t in _class_tokens(m.group(2))]
    return used


def js_hook_classes(code):
    """Classes referenced as selectors from JS — behaviour hooks, resolved."""
    hooks = set()
    for sm in SCRIPT_BLOCK_RE.finditer(code):
        js = sm.group(1)
        for m in re.finditer(
            r"(?:querySelector(?:All)?|closest|matches)\s*\(\s*([\"'`])(.*?)\1", js
        ):
            hooks |= set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", m.group(2)))
        for m in re.finditer(
            r"(?:getElementsByClassName|classList\s*\.\s*(?:contains|remove))\s*\(([^)]*)\)",
            js,
        ):
            for lit in STRING_LIT_RE.finditer(m.group(1)):
                hooks |= set(lit.group(2).split())
    return hooks


def is_tailwindish(cls):
    return cls in TW_STANDALONE or bool(TW_SCALE_RE.match(cls) or TW_PREFIX_RE.match(cls))


def rule_orphan_class(c):
    if c["ext"] not in (".html", ".htm"):
        return []
    text, code, scope = c["text"], c["views"]["code"], c["css_scope"]
    defined = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", strip_comments(scope)))
    defined |= js_hook_classes(code)
    tailwind = bool(
        re.search(r"tailwindcss", text, re.I)
        or re.search(r"@tailwind\b|@import\s+[\"']tailwindcss", scope)
    )
    hits, seen = [], set()
    for off, cls in used_classes(code):
        if cls in seen or cls in defined or (tailwind and is_tailwindish(cls)):
            continue
        seen.add(cls)
        hits.append(
            make_hit(
                "orphan-class",
                c["display"],
                text,
                off,
                f".{cls} is used but defined in no CSS in scope",
            )
        )
    return hits


def rule_em_dash(c):
    if c["ext"] in CSS_EXTS:
        return []
    visible = c["views"]["visible"]
    offs = [
        m.start()
        for m in re.finditer(r"\u2014|&mdash;|&#8212;|&#x2014;", visible, re.I)
    ]
    hits, lines = [], set()
    for off in offs:
        hit = make_hit(
            "em-dash",
            c["display"],
            c["text"],
            off,
            f"em-dash in visible text ({len(offs)} in file)",
        )
        if hit["line"] not in lines:
            lines.add(hit["line"])
            hits.append(hit)
    return hits


HERO_HEIGHT_RE = re.compile(
    r"(?<![\w-])(?:min-)?h-(?:screen|dvh|svh|lvh)(?![\w-])|\b100(?:d|s|l)?vh\b"
)


def rule_h_screen_hero(c):
    code, hits = c["views"]["code"], []
    first_section = True
    for m in TAG_OPEN_RE.finditer(code):
        name, attrs = m.group(1).lower(), m.group(2)
        ident = " ".join(
            re.findall(r"(?:class|className|id)\s*=\s*([\"'{`][^\"'`}]*)", attrs)
        )
        is_first = name == "section" and first_section
        if name == "section":
            first_section = False
        if (is_first or "hero" in ident.lower()) and HERO_HEIGHT_RE.search(attrs):
            hits.append(
                make_hit(
                    "h-screen-hero",
                    c["display"],
                    c["text"],
                    m.start(),
                    "full-viewport height on the hero / first section",
                )
            )
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", code):
        if "hero" in m.group(1).lower() and re.search(
            r"(?:min-)?height\s*:\s*100(?:d|s|l)?vh", m.group(2), re.I
        ):
            hits.append(
                make_hit(
                    "h-screen-hero",
                    c["display"],
                    c["text"],
                    m.start(2),
                    "full-viewport height on a hero selector",
                )
            )
    return hits


def rule_scroll_cue(c):
    hits = []
    copy_re = r"\bscroll\s+(?:down|to\s+(?:explore|discover|continue|begin|see\s+more|learn\s+more)|for\s+more)\b"
    for m in re.finditer(copy_re, c["views"]["visible"], re.I):
        hits.append(
            make_hit(
                "scroll-cue", c["display"], c["text"], m.start(), '"scroll" cue copy'
            )
        )
    code = c["views"]["code"]
    for m in re.finditer(
        r"(?<![\w-])scroll-(?:cue|indicator|hint|down|arrow|prompt)(?![\w-])",
        code,
        re.I,
    ):
        hits.append(
            make_hit(
                "scroll-cue", c["display"], c["text"], m.start(), "scroll-cue element"
            )
        )
    for m in re.finditer(
        r"(?<![\w-])animate-bounce(?![\w-])|animation(?:-name)?\s*:\s*bounce\b",
        code,
        re.I,
    ):
        near = code[max(0, m.start() - 200) : m.end() + 200]
        if re.search(r"chevron|arrow|\u2193|scroll", near, re.I):
            hits.append(
                make_hit(
                    "scroll-cue",
                    c["display"],
                    c["text"],
                    m.start(),
                    "bouncing chevron scroll cue",
                )
            )
    return hits


EYEBROW_RE = re.compile(
    r"^(?:§\s*\d{1,3}\b|/\s*\d{1,3}\b|\(\s*0\d\s*\)|0\d\s*(?:[\u2014\u2013\-/·.:|](?!\s*\d)|$)|\d{1,2}\s+[\u2014\u2013]\s)"
)


def rule_section_number_eyebrow(c):
    nodes, hits = c["views"]["nodes"], []
    for m in re.finditer(r">([^<>]+)<", nodes):
        node = htmllib.unescape(m.group(1)).strip()
        if not node or len(node) > 60 or not EYEBROW_RE.match(node):
            continue
        window = nodes[max(0, m.start() - 300) : m.end() + 300]
        if re.search(r"<h[1-6]\b|<Heading\b", window, re.I):
            hits.append(
                make_hit(
                    "section-number-eyebrow",
                    c["display"],
                    c["text"],
                    m.start(1),
                    f'numbered eyebrow "{node}" next to a heading',
                )
            )
    return hits


def rule_missing_tabular_nums(c):
    trigger = re.search(
        r"<(?:table|td)\b|(?:class|className)\s*=\s*[\"'{`][^\"'`}]*\b(?:kpi|metric|stat)s?\b",
        c["views"]["code"],
        re.I,
    )
    if not trigger:
        return []
    pat = r"tabular-nums|font-variant-numeric|fontVariantNumeric"
    if re.search(pat, c["text"]) or re.search(pat, c["css_scope"]):
        return []
    return [
        make_hit(
            "missing-tabular-nums",
            c["display"],
            c["text"],
            trigger.start(),
            "numeric table/KPI content but no tabular-nums / font-variant-numeric in scope",
        )
    ]


RULE_FUNCS = {
    "raw-hex-off-palette": rule_raw_hex_off_palette,
    "raw-hex-outside-tokens": rule_raw_hex_outside_tokens,
    "font-off-directive": rule_font_off_directive,
    "reserved-token-bleed": rule_reserved_token_bleed,
    "z-index-literal": rule_z_index_literal,
    "div-onclick": rule_div_onclick,
    "transition-all": rule_transition_all,
    "loading-spinner": rule_loading_spinner,
    "orphan-class": rule_orphan_class,
    "em-dash": rule_em_dash,
    "h-screen-hero": rule_h_screen_hero,
    "scroll-cue": rule_scroll_cue,
    "section-number-eyebrow": rule_section_number_eyebrow,
    "missing-tabular-nums": rule_missing_tabular_nums,
}


def applicable_rules(directive, brand, surface, ext):
    rt = brand.get("reserved_tokens") or {}
    out = []
    for rule_id in RULES:
        if surface not in RULE_SURFACES.get(rule_id, set(SURFACES)):
            continue
        if rule_id == "raw-hex-outside-tokens" and not directive["tokens_declared"]:
            continue
        if rule_id == "reserved-token-bleed" and not (
            rt.get("fonts") or rt.get("colors")
        ):
            continue
        if rule_id == "loading-spinner" and not directive["bans_spinners"]:
            continue
        if rule_id == "orphan-class" and ext not in (".html", ".htm"):
            continue
        out.append(rule_id)
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run(files, directive_path, surface_flag=None, extra_css=()):
    directive = parse_directive(directive_path)
    try:
        brand = state_paths.brand_config(cwd=str(directive_path.parent))
    except Exception:  # a broken operator config must not crash the gate
        brand = dict(state_paths.DEFAULT_BRAND_CONFIG)
    extra_texts = [p.read_text(encoding="utf-8", errors="replace") for p in extra_css]

    fixed = surface_flag or directive["surface"]
    surfaces, rules_run, violations, waived = set(), [], [], []
    for display in files:
        path = Path(display)
        ext = path.suffix.lower()
        text = path.read_text(encoding="utf-8", errors="replace")
        surface = fixed or ("operate" if ext in OPERATE_EXTS else "persuade")
        surfaces.add(surface)
        ctx = {
            "path": path,
            "display": display,
            "ext": ext,
            "text": text,
            "views": file_views(text, ext),
            "directive": directive,
            "brand": brand,
            "is_token_file": ext in CSS_EXTS and is_token_file(path, text, directive),
            "css_scope": css_scope(path, text, ext, extra_texts),
        }
        for rule_id in applicable_rules(directive, brand, surface, ext):
            if rule_id not in rules_run:
                rules_run.append(rule_id)
            for hit in RULE_FUNCS[rule_id](ctx):
                if rule_id in directive["overrides"]:
                    waived.append(
                        {
                            "rule": rule_id,
                            "file": hit["file"],
                            "line": hit["line"],
                            "reason": directive["overrides"][rule_id],
                        }
                    )
                else:
                    violations.append(hit)

    rules_run.sort(key=list(RULES).index)
    if fixed:
        surface_mode = fixed
    elif len(surfaces) == 1:
        surface_mode = next(iter(surfaces))
    else:
        surface_mode = "inferred-per-file"
    return {
        "directive": str(directive_path),
        "surface_mode": surface_mode,
        "files": list(files),
        "rules_run": rules_run,
        "violations": violations,
        "waived": waived,
        "summary": {"violations": len(violations), "waived": len(waived)},
    }


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(result):
    verdict = "FAIL" if result["violations"] else "PASS"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = [
        "# Style Enforcement Report",
        "",
        f"- **Directive:** `{result['directive']}`",
        f"- **Surface mode:** {result['surface_mode']}",
        f"- **Generated:** {now}",
        f"- **Verdict:** {verdict}",
        f"- **Files:** {', '.join('`%s`' % f for f in result['files'])}",
        f"- **Rules run:** {', '.join('`%s`' % r for r in result['rules_run'])}",
        f"- **Summary:** {result['summary']['violations']} violation(s), {result['summary']['waived']} waived",
        "",
        "## Violations",
        "",
    ]
    if result["violations"]:
        out += ["| Rule | File | Line | Excerpt | Message |", "|---|---|---|---|---|"]
        for v in result["violations"]:
            out.append(
                f"| `{v['rule']}` | {_cell(v['file'])} | {v['line']} | `{_cell(v['excerpt'])}` | {_cell(v['message'])} |"
            )
    else:
        out.append("None.")
    out += ["", "## Waived", ""]
    if result["waived"]:
        out += ["| Rule | File | Line | Reason |", "|---|---|---|---|"]
        for w in result["waived"]:
            out.append(
                f"| `{w['rule']}` | {_cell(w['file'])} | {w['line']} | {_cell(w['reason'])} |"
            )
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def render_text(result):
    out = [f"enforce: {result['directive']} (surface: {result['surface_mode']})"]
    for v in result["violations"]:
        out.append(f"FAIL  {v['rule']}  {v['file']}:{v['line']}  {v['excerpt']}")
        out.append(f"      {v['message']}")
    for w in result["waived"]:
        out.append(f"WAIVE {w['rule']}  {w['file']}:{w['line']}  ({w['reason']})")
    verdict = "FAIL" if result["violations"] else "PASS"
    out.append(
        f"{verdict}: {result['summary']['violations']} violation(s), {result['summary']['waived']} waived"
    )
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Directive-driven mechanical style linter."
    )
    ap.add_argument("files", nargs="*")
    ap.add_argument("--directive")
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("--css", nargs="+", default=[])
    ap.add_argument("--list-rules", action="store_true")
    args = ap.parse_args(argv)

    if args.list_rules:
        for rule_id, desc in RULES.items():
            surfaces = ",".join(
                s for s in SURFACES if s in RULE_SURFACES.get(rule_id, set(SURFACES))
            )
            print(f"{rule_id:<24} [{surfaces}] {desc}")
        return 0

    if not args.files or not args.directive:
        print("enforce: need at least one file and --directive", file=sys.stderr)
        return 2
    directive = Path(args.directive)
    if not directive.is_file():
        print(f"enforce: directive not found: {directive}", file=sys.stderr)
        return 2
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            print(f"enforce: file not found: {f}", file=sys.stderr)
            return 2
        if p.suffix.lower() not in SUPPORTED_EXTS:
            print(f"enforce: unsupported file type: {f}", file=sys.stderr)
            return 2
    extra = [Path(c) for c in args.css]
    for c in extra:
        if not c.is_file():
            print(f"enforce: --css file not found: {c}", file=sys.stderr)
            return 2

    try:
        result = run(args.files, directive, args.surface, extra)
    except (OSError, UnicodeDecodeError) as e:
        print(f"enforce: {e}", file=sys.stderr)
        return 2

    if args.report:
        try:
            Path(args.report).write_text(render_report(result), encoding="utf-8")
        except OSError as e:
            print(f"enforce: cannot write report: {e}", file=sys.stderr)
            return 2

    print(
        json.dumps(result, indent=2, ensure_ascii=False)
        if args.json
        else render_text(result)
    )
    return 1 if result["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
