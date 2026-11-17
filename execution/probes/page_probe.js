/* page_probe.js: in-page QA probe for the design-agency plugin (v0.6.0).
 *
 * Measures the loaded page from the inside: performance, accessibility and
 * conversion mechanics, each checked against a budget. No network, no
 * dependencies. The whole file is ONE expression (an async IIFE), so it works
 * pasted into a browser JS console tool (the value of the last expression is
 * the result) and as the argument of Playwright's page.evaluate().
 *
 * Override budgets before running:  window.__PROBE_BUDGETS = { lcpMs: 2000 }
 * Side effect: scrolls once to test for a sticky action, then restores the
 * original scroll position. See README.md next to this file.
 *
 * The prettier-ignore below is load-bearing: a formatter would append `;`,
 * and callers that wrap the file as `(<file>)` need a bare expression.
 */
/* prettier-ignore */
(async () => {
  const CAP = 12;
  const DEFAULT_BUDGETS = {
    lcpMs: 2500,
    cls: 0.1,
    longTaskMs: 300,
    transferKB: 1500,
    jsKB: 300,
    renderBlocking: 3,
    smallTargets24: 0,
    lowContrast: 0,
    missingAlt: 0,
    unlabelledControls: 0,
    horizontalOverflow: false,
    contactLinkCtas: 0,
  };
  const budgets = Object.assign(
    {},
    DEFAULT_BUDGETS,
    window.__PROBE_BUDGETS || {},
  );

  const doc = document;
  const de = doc.documentElement;
  const vw = window.innerWidth;
  const vh = window.innerHeight || 1;
  const startX = window.scrollX;
  const startY = window.scrollY;

  const r1 = (n) => Math.round(n * 10) / 10;
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const $$ = (q, root) => Array.from((root || doc).querySelectorAll(q));
  const txt = (s, n) =>
    String(s || "")
      .replace(/­/g, "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, n || 40);
  const attr = (el, name) => (el.getAttribute(name) || "").trim();

  const part = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += "#" + el.id;
    const cls = attr(el, "class").split(/\s+/).filter(Boolean).slice(0, 2);
    if (cls.length) s += "." + cls.join(".");
    return s;
  };
  // Short CSS-ish path: tag#id.class, prefixed with up to two ancestors while it fits.
  const sel = (el) => {
    if (!el || !el.tagName) return "";
    let s = part(el);
    if (!el.id) {
      let p = el.parentElement;
      for (
        let i = 0;
        i < 2 && p && p !== doc.body && p !== de;
        i++, p = p.parentElement
      ) {
        const next = part(p) + " > " + s;
        if (next.length > 60) break;
        s = next;
        if (p.id) break;
      }
    }
    return s.slice(0, 60);
  };
  const finding = (el, note) => ({
    sel: typeof el === "string" ? el.slice(0, 60) : sel(el),
    note: txt(note, 60),
  });
  const list = (arr) => ({ count: arr.length, items: arr.slice(0, CAP) });

  const visible = (el) => {
    // Content skipped by a closed <details> or content-visibility: hidden still
    // reports a layout box, but is neither painted nor tappable.
    if (el.checkVisibility && !el.checkVisibility()) return false;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const cs = getComputedStyle(el);
    return (
      cs.visibility !== "hidden" &&
      cs.display !== "none" &&
      parseFloat(cs.opacity) > 0
    );
  };
  const pageTop = (el) => el.getBoundingClientRect().top + window.scrollY;
  // Nearest fixed/sticky ancestor (or the element itself), else null.
  const pinnedAncestor = (el) => {
    for (let n = el; n && n.nodeType === 1 && n !== de; n = n.parentElement) {
      const pos = getComputedStyle(n).position;
      if (pos === "fixed" || pos === "sticky") return n;
    }
    return null;
  };

  // Button-like = <button>, input[type=submit], [role=button], or <a class~=btn|button|cta>.
  const BUTTON_CLASS = /btn|button|cta/i;
  const BUTTONISH = "button, input[type=submit], [role=button], a[class]";
  const isButtonLike = (el) =>
    el.matches("button, input[type=submit], [role=button]") ||
    (el.tagName === "A" && BUTTON_CLASS.test(attr(el, "class")));
  const labelOf = (el) =>
    txt(
      el.innerText ||
        el.value ||
        attr(el, "aria-label") ||
        attr(el, "title") ||
        el.textContent,
    );
  const NON_FIELD = /^(hidden|submit|button|reset|image)$/;
  const isField = (el) => !NON_FIELD.test(attr(el, "type").toLowerCase());
  const hasLabel = (el) =>
    !!(
      (el.labels && el.labels.length) ||
      attr(el, "aria-label") ||
      attr(el, "aria-labelledby") ||
      attr(el, "title")
    );

  const errors = [];
  const section = async (name, fn) => {
    try {
      return await fn();
    } catch (e) {
      errors.push(name + ": " + txt(e && e.message, 80));
      return { error: txt(e && e.message, 80) };
    }
  };

  // ---------------------------------------------------------------- page
  const docHeight = Math.max(
    de.scrollHeight,
    doc.body ? doc.body.scrollHeight : 0,
  );
  const scrollWidth = Math.max(
    de.scrollWidth,
    doc.body ? doc.body.scrollWidth : 0,
  );
  const page = {
    url: location.origin + location.pathname,
    viewport: { w: vw, h: vh, dpr: window.devicePixelRatio || 1 },
    lang: attr(de, "lang") || null,
    title: txt(doc.title, 80),
    hasViewportMeta: !!doc.querySelector("meta[name=viewport]"),
    horizontalOverflow: scrollWidth > vw + 1,
    docHeight,
    screens: r1(docHeight / vh),
  };

  // ---------------------------------------------------------------- perf
  const perf = await section("perf", async () => {
    const caveats = [
      "INP cannot be measured without real user interaction",
      "lab numbers from a dev machine are indicative only",
    ];
    const supported =
      typeof PerformanceObserver === "undefined"
        ? []
        : PerformanceObserver.supportedEntryTypes || [];
    const observe = (type) =>
      new Promise((resolve) => {
        if (!supported.includes(type)) return resolve(null);
        const out = [];
        let po;
        try {
          po = new PerformanceObserver((l) => out.push(...l.getEntries()));
          po.observe({ type, buffered: true });
        } catch (e) {
          return resolve(null);
        }
        setTimeout(() => {
          try {
            out.push(...po.takeRecords());
            po.disconnect();
          } catch (e) {
            /* observer already gone */
          }
          resolve(out);
        }, 300);
      });
    const [lcpEntries, shiftEntries, longTasks] = await Promise.all(
      ["largest-contentful-paint", "layout-shift", "longtask"].map(observe),
    );

    const nav = performance.getEntriesByType("navigation")[0];
    const ms = (v) => (v > 0 ? Math.round(v) : null);
    const findings = [];

    let lcp = null;
    const last =
      lcpEntries && lcpEntries.length
        ? lcpEntries[lcpEntries.length - 1]
        : null;
    if (last) {
      const el = last.element;
      const isImg = !!el && el.tagName === "IMG";
      lcp = {
        ms: Math.round(last.renderTime || last.loadTime || last.startTime),
        sel: sel(el),
        isImage: isImg || !!last.url,
        lazy: isImg && attr(el, "loading") === "lazy",
        fetchpriority: isImg ? attr(el, "fetchpriority") || null : null,
      };
      if (lcp.lazy) findings.push(finding(el, "LCP image is loading=lazy"));
      else if (isImg && lcp.fetchpriority !== "high")
        findings.push(finding(el, "LCP image lacks fetchpriority=high"));
    } else {
      caveats.push(
        "no LCP entry (unsupported browser, hidden tab or nothing painted yet)",
      );
    }
    if (!shiftEntries)
      caveats.push("layout-shift entries unsupported: cls unmeasured");
    if (!longTasks)
      caveats.push("longtask entries unsupported: longTaskMs unmeasured");

    const extOf = (url) => {
      const m = url.split(/[?#]/)[0].match(/\.([a-z0-9]{2,5})$/i);
      return m ? m[1].toLowerCase() : "";
    };
    const kindOf = (e) => {
      const x = extOf(e.name);
      if (/^m?js$/.test(x)) return "js";
      if (x === "css") return "css";
      if (/^(png|jpe?g|gif|webp|avif|svg|ico)$/.test(x)) return "img";
      if (/^(woff2?|ttf|otf|eot)$/.test(x)) return "font";
      if (e.initiatorType === "script") return "js";
      if (e.initiatorType === "img" || e.initiatorType === "image")
        return "img";
      if (e.initiatorType === "link" && /\/css/.test(e.name)) return "css";
      return "other";
    };
    const sizeOf = (e) => e.transferSize || e.encodedBodySize || 0;
    const FONT_HOST =
      /^https?:\/\/(fonts\.googleapis\.com|use\.typekit\.net)\//i;

    const resources = performance.getEntriesByType("resource");
    const bytes = { total: 0, js: 0, css: 0, img: 0, font: 0, other: 0 };
    const origins = new Set();
    const legacy = [];
    let fontFiles = 0;
    let blocking = 0;
    let unsized = 0;
    let remoteFontCss = $$("link[href]").some(
      (l) => /stylesheet/i.test(l.rel) && FONT_HOST.test(l.href),
    );
    const imgs = $$("img");
    for (const e of resources) {
      const kind = kindOf(e);
      const size = sizeOf(e);
      if (!size) unsized++;
      bytes[kind] += size;
      bytes.total += size;
      if (kind === "font") fontFiles++;
      if (e.renderBlockingStatus === "blocking") blocking++;
      if (FONT_HOST.test(e.name) && kind !== "js") remoteFontCss = true;
      try {
        const origin = new URL(e.name).origin;
        if (origin !== location.origin && origin !== "null")
          origins.add(origin);
      } catch (err) {
        /* not a URL */
      }
      if (
        kind === "img" &&
        /^(png|jpe?g)$/.test(extOf(e.name)) &&
        size > 60 * 1024
      ) {
        const img = imgs.find((i) => i.currentSrc === e.name);
        legacy.push(
          finding(
            img || e.name.split(/[?#]/)[0].split("/").pop(),
            Math.round(size / 1024) + " KB " + extOf(e.name),
          ),
        );
      }
    }
    if (nav) {
      bytes.other += sizeOf(nav);
      bytes.total += sizeOf(nav);
    }
    const transferKB = {};
    for (const k of Object.keys(bytes))
      transferKB[k] = Math.round(bytes[k] / 1024);
    if (unsized)
      caveats.push(
        unsized +
          " resource(s) report no size (cached or cross-origin): transferKB is a floor",
      );
    const blockingKnown =
      resources.length === 0 || "renderBlockingStatus" in resources[0];
    if (!blockingKnown)
      caveats.push(
        "renderBlockingStatus unsupported: renderBlocking unmeasured",
      );

    const noDims = imgs.filter(
      (i) =>
        !(i.hasAttribute("width") && i.hasAttribute("height")) &&
        getComputedStyle(i).aspectRatio === "auto",
    );

    return {
      ttfb: nav ? ms(nav.responseStart) : null,
      domContentLoaded: nav ? ms(nav.domContentLoadedEventEnd) : null,
      load: nav ? ms(nav.loadEventEnd) : null,
      lcp,
      cls: shiftEntries
        ? Math.round(
            shiftEntries
              .filter((e) => !e.hadRecentInput)
              .reduce((s, e) => s + e.value, 0) * 1000,
          ) / 1000
        : null,
      longTaskMs: longTasks
        ? Math.round(
            longTasks.reduce((s, e) => s + Math.max(0, e.duration - 50), 0),
          )
        : null,
      transferKB,
      renderBlocking: blockingKnown ? blocking : null,
      thirdPartyOrigins: Array.from(origins).slice(0, CAP),
      thirdPartyOriginCount: origins.size,
      fontFiles,
      remoteFontCss,
      imagesNoDimensions: list(
        noDims.map((i) => finding(i, txt(attr(i, "src").split("/").pop(), 40))),
      ),
      imagesLegacyFormat: list(legacy),
      findings: list(findings),
      caveats,
    };
  });

  // ---------------------------------------------------------------- a11y
  const a11y = await section("a11y", async () => {
    const missingAlt = $$("img:not([alt])").map((i) =>
      finding(i, txt(attr(i, "src").split("/").pop(), 40)),
    );

    const unlabelled = $$("input, select, textarea")
      .filter((el) => isField(el) && visible(el) && !hasLabel(el))
      .map((el) =>
        finding(
          el,
          attr(el, "name") || attr(el, "type") || el.tagName.toLowerCase(),
        ),
      );

    const named = (el) =>
      txt(el.textContent) ||
      attr(el, "aria-label") ||
      attr(el, "aria-labelledby") ||
      attr(el, "title") ||
      el.querySelector(
        'img[alt]:not([alt=""]), svg[aria-label], [aria-label], [aria-labelledby]',
      );
    const unnamed = $$("a[href], button, [role=button]")
      .filter((el) => visible(el) && !named(el))
      .map((el) => finding(el, "no accessible name"));

    const headingSkips = [];
    let prev = 0;
    for (const h of $$("h1, h2, h3, h4, h5, h6").filter(visible)) {
      const level = Number(h.tagName[1]);
      if (prev && level > prev + 1)
        headingSkips.push(finding(h, "h" + prev + " → h" + level));
      prev = level;
    }
    const h1Count = $$("h1").length;

    const idCounts = new Map();
    for (const el of $$("[id]"))
      if (el.id) idCounts.set(el.id, (idCounts.get(el.id) || 0) + 1);
    const duplicateIds = [];
    idCounts.forEach((n, id) => {
      if (n > 1) duplicateIds.push(finding("#" + id, "×" + n));
    });

    // Target size, WCAG 2.2 SC 2.5.8: under 24x24 CSS px fails unless the link
    // is inline in a sentence, or a 24px circle centred on the target touches
    // no other target (spacing exception).
    const boxOf = (el) => {
      const r = el.getBoundingClientRect();
      const b = { l: r.left, t: r.top, r: r.right, b: r.bottom };
      const grow = (q) => {
        if (q.width <= 0 || q.height <= 0) return;
        b.l = Math.min(b.l, q.left);
        b.t = Math.min(b.t, q.top);
        b.r = Math.max(b.r, q.right);
        b.b = Math.max(b.b, q.bottom);
      };
      if (el.labels)
        for (const lab of el.labels) grow(lab.getBoundingClientRect());
      if (el.tagName === "A")
        for (const child of el.children) grow(child.getBoundingClientRect());
      return b;
    };
    const inlineInText = (el) => {
      if (el.tagName !== "A" || getComputedStyle(el).display !== "inline")
        return false;
      const block =
        el.parentElement &&
        el.parentElement.closest(
          "p, li, td, th, dd, dt, blockquote, figcaption, label, div, span",
        );
      if (!block) return false;
      let linked = 0;
      for (const a of $$("a", block)) linked += txt(a.textContent, 1e5).length;
      return txt(block.textContent, 1e5).length - linked > 1;
    };
    const targets = $$(
      "a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=link], [role=checkbox], [role=radio], [role=switch], [role=tab], [role=menuitem]",
    )
      .filter((el) => !el.disabled && visible(el))
      .slice(0, 800)
      .map((el) => {
        const b = boxOf(el);
        const w = b.r - b.l;
        const h = b.b - b.t;
        return {
          el,
          b,
          w,
          h,
          cx: (b.l + b.r) / 2,
          cy: (b.t + b.b) / 2,
          small: w < 24 || h < 24,
        };
      })
      .filter(
        (t) =>
          !(t.w <= 1 && t.h <= 1) && t.b.r > 0 && t.b.b + window.scrollY > 0,
      );
    for (const t of targets) {
      t.inline = (t.w < 44 || t.h < 44) && inlineInText(t.el);
      t.layer = pinnedAncestor(t.el);
    }
    // Targets in a fixed/sticky layer only crowd each other: where such a layer
    // sits relative to the page content depends on the scroll position.
    const crowded = (t) =>
      targets.some((o) => {
        if (o === t || o.layer !== t.layer) return false;
        if (o.el.contains(t.el) || t.el.contains(o.el)) return false;
        if (o.small && Math.hypot(o.cx - t.cx, o.cy - t.cy) < 24) return true;
        const dx = Math.max(o.b.l - t.cx, 0, t.cx - o.b.r);
        const dy = Math.max(o.b.t - t.cy, 0, t.cy - o.b.b);
        return Math.hypot(dx, dy) < 12;
      });
    const dims = (t) =>
      Math.round(t.w) + "×" + Math.round(t.h) + " " + labelOf(t.el);
    const small24 = targets
      .filter((t) => t.small && !t.inline && crowded(t))
      .map((t) => finding(t.el, dims(t)));
    const small44 = targets
      .filter((t) => !t.inline && (t.w < 44 || t.h < 44))
      .map((t) => finding(t.el, dims(t)));

    // Contrast: text colour against the first opaque ancestor background,
    // compositing semi-transparent layers. A background-image anywhere on the
    // way makes the pair unknown (not flagged).
    const canvas = doc.createElement("canvas");
    canvas.width = canvas.height = 1;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    const colours = new Map();
    const rgba = (c) => {
      if (colours.has(c)) return colours.get(c);
      let v = null;
      const m =
        /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/.exec(
          c,
        );
      if (m) {
        const a =
          m[4] === undefined
            ? 1
            : m[4].endsWith("%")
              ? parseFloat(m[4]) / 100
              : parseFloat(m[4]);
        v = [Number(m[1]), Number(m[2]), Number(m[3]), a];
      } else if (ctx) {
        ctx.clearRect(0, 0, 1, 1);
        ctx.fillStyle = "#000";
        ctx.fillStyle = c;
        ctx.fillRect(0, 0, 1, 1);
        const d = ctx.getImageData(0, 0, 1, 1).data;
        v = [d[0], d[1], d[2], d[3] / 255];
      }
      colours.set(c, v);
      return v;
    };
    const over = (top, bottom) =>
      [0, 1, 2]
        .map((i) => top[i] * top[3] + bottom[i] * (1 - top[3]))
        .concat(1);
    const lum = (c) => {
      const f = (v) => {
        v /= 255;
        return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      };
      return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
    };
    const hex = (c) =>
      "#" +
      [0, 1, 2]
        .map((i) => Math.round(c[i]).toString(16).padStart(2, "0"))
        .join("");
    const backgroundOf = (el) => {
      const layers = [];
      for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (cs.backgroundImage && cs.backgroundImage !== "none") return null;
        const c = rgba(cs.backgroundColor);
        if (c && c[3] > 0) {
          layers.push(c);
          if (c[3] >= 1) break;
        }
      }
      let base = [255, 255, 255, 1];
      for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
      return base;
    };
    const low = [];
    let sampled = 0;
    let unknown = 0;
    const seen = new Set();
    const walker = doc.createTreeWalker(doc.body || de, NodeFilter.SHOW_TEXT);
    for (
      let node = walker.nextNode();
      node && sampled < 400;
      node = walker.nextNode()
    ) {
      const el = node.parentElement;
      if (!node.nodeValue.trim() || !el || seen.has(el)) continue;
      seen.add(el);
      if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|OPTION|TITLE)$/.test(el.tagName))
        continue;
      if (el.closest("svg, [disabled], [aria-disabled=true]") || !visible(el))
        continue;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 1 || rect.height <= 1) continue;
      sampled++;
      const cs = getComputedStyle(el);
      const fill = rgba(cs.webkitTextFillColor || cs.color);
      const fg = rgba(cs.color);
      const bg = backgroundOf(el);
      if (!bg || !fg || (fill && fill[3] === 0)) {
        unknown++;
        continue;
      }
      const ink = fg[3] < 1 ? over(fg, bg) : fg;
      const a = lum(ink);
      const b = lum(bg);
      const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      const px = parseFloat(cs.fontSize);
      const need =
        px >= 24 || (px >= 18.66 && parseInt(cs.fontWeight, 10) >= 700)
          ? 3
          : 4.5;
      if (ratio < need - 0.005)
        low.push(
          finding(
            el,
            ratio.toFixed(2) +
              ":1 < " +
              need +
              " " +
              hex(ink) +
              " on " +
              hex(bg) +
              " " +
              Math.round(px) +
              "px",
          ),
        );
    }

    // Reduced motion: handled if a readable stylesheet has a
    // prefers-reduced-motion media rule, or nothing moves for longer than 200 ms.
    let motionRule = false;
    let unreadableSheets = 0;
    const walk = (rules) => {
      for (const rule of Array.from(rules || [])) {
        if (motionRule) return;
        if (rule.media && /prefers-reduced-motion/.test(rule.media.mediaText)) {
          motionRule = true;
          return;
        }
        let inner = rule.cssRules;
        if (!inner && rule.styleSheet) {
          try {
            inner = rule.styleSheet.cssRules;
          } catch (e) {
            unreadableSheets++;
          }
        }
        if (inner && inner.length) walk(inner);
      }
    };
    for (const sheet of Array.from(doc.styleSheets)) {
      if (sheet.media && /prefers-reduced-motion/.test(sheet.media.mediaText))
        motionRule = true;
      try {
        walk(sheet.cssRules);
      } catch (e) {
        unreadableSheets++;
      }
      if (motionRule) break;
    }
    let longMotion = false;
    if (!motionRule) {
      const seconds = (v) =>
        Math.max(
          0,
          ...String(v)
            .split(",")
            .map(
              (x) =>
                (/ms\s*$/.test(x) ? parseFloat(x) / 1000 : parseFloat(x)) || 0,
            ),
        );
      const all = $$("*");
      for (let i = 0; i < all.length && i < 3000 && !longMotion; i++) {
        const cs = getComputedStyle(all[i]);
        longMotion =
          (cs.animationName !== "none" &&
            seconds(cs.animationDuration) > 0.2) ||
          (cs.transitionProperty !== "none" &&
            seconds(cs.transitionDuration) > 0.2);
      }
    }

    return {
      missingAlt: list(missingAlt),
      unlabelledControls: list(unlabelled),
      unnamedInteractive: list(unnamed),
      headingSkips: list(headingSkips),
      h1Count,
      multipleH1: h1Count > 1,
      duplicateIds: list(duplicateIds),
      smallTargets24: list(small24),
      smallTargets44: list(small44),
      lowContrast: Object.assign(list(low), { sampled, unknown }),
      reducedMotionHandled: motionRule || !longMotion,
      reducedMotion: { mediaRule: motionRule, longMotion, unreadableSheets },
    };
  });

  // ---------------------------------------------------------- conversion
  const conversion = await section("conversion", async () => {
    const buttons = $$(BUTTONISH).filter(
      (el) => isButtonLike(el) && visible(el),
    );
    const hrefOf = (el) =>
      el.hasAttribute("href") ? attr(el, "href").slice(0, 80) : null;
    const aboveFold = buttons.filter((el) => {
      const r = el.getBoundingClientRect();
      const top = r.top + window.scrollY;
      return top < vh && top + r.height > 0 && r.left < vw && r.right > 0;
    });
    const labels = Array.from(new Set(buttons.map(labelOf).filter(Boolean)));
    const contact = buttons
      .filter(
        (el) => el.tagName === "A" && /^(mailto|tel):/i.test(attr(el, "href")),
      )
      .map((el) =>
        finding(
          el,
          attr(el, "href").split(":")[0].toLowerCase() + ": " + labelOf(el),
        ),
      );

    const forms = $$("form")
      .filter(visible)
      .slice(0, 5)
      .map((form) => {
        const fields = $$("input, select, textarea", form).filter(
          (el) => isField(el) && visible(el),
        );
        const issues = new Set();
        const submit = $$(
          "button:not([type=button]):not([type=reset]), input[type=submit], input[type=image]",
          form,
        ).find((b) => visible(b) && (labelOf(b) || attr(b, "alt")));
        if (!submit) issues.add("no visible submit label");
        for (const el of fields) {
          const tag = el.tagName.toLowerCase();
          const type =
            tag === "input" ? attr(el, "type").toLowerCase() || "text" : tag;
          const name = attr(el, "name") || el.id || type;
          const hint = [
            attr(el, "name"),
            el.id,
            attr(el, "autocomplete"),
            attr(el, "placeholder"),
            el.labels && el.labels[0] ? el.labels[0].textContent : "",
          ]
            .join(" ")
            .toLowerCase();
          const texty = /^(text|email|tel|search|url)$/.test(type);
          const isEmail = /e-?mail/.test(hint);
          const isPhone =
            !isEmail && /phone|telefon|\btel\b|mobil|handy/.test(hint);
          if (texty && isEmail && type !== "email")
            issues.add(name + ": email field not type=email");
          if (texty && isPhone && type !== "tel")
            issues.add(name + ": phone field not type=tel");
          if (
            texty &&
            (isEmail ||
              isPhone ||
              /name|company|organi[sz]ation|firma|unternehmen/.test(hint)) &&
            !attr(el, "autocomplete")
          )
            issues.add(name + ": missing autocomplete");
          if (
            vw < 500 &&
            tag !== "select" &&
            !/^(checkbox|radio|range|file|color)$/.test(type) &&
            parseFloat(getComputedStyle(el).fontSize) < 16
          )
            issues.add(name + ": font-size under 16px (iOS zoom)");
          if (attr(el, "placeholder") && !hasLabel(el))
            issues.add(name + ": placeholder is the only label");
        }
        return {
          sel: sel(form),
          fields: fields.length,
          required: fields.filter(
            (el) => el.required || attr(el, "aria-required") === "true",
          ).length,
          topScreens: r1(pageTop(form) / vh),
          issueCount: issues.size,
          issues: Array.from(issues).slice(0, 8),
        };
      });

    const proof = $$(
      "[data-proof], .proof, [class*=proof], [class*=logos], [class*=testimonial], blockquote",
    ).find(visible);
    const firstProofScreens = proof ? r1(pageTop(proof) / vh) : null;

    // Sticky action: scroll 1.5 viewports, note button-likes inside a
    // fixed/sticky ancestor, scroll a little further and keep those whose
    // ancestor did not move in the viewport. Runs last: scrolling can trigger
    // lazy loads and shifts that must not leak into the numbers above.
    let stickyAction = null;
    let stickySel = null;
    const maxScroll = docHeight - vh;
    if (maxScroll >= 250) {
      const inView = (el) => {
        const r = el.getBoundingClientRect();
        return (
          r.width > 0 &&
          r.height > 0 &&
          r.bottom > 0 &&
          r.top < window.innerHeight &&
          r.right > 0 &&
          r.left < window.innerWidth
        );
      };
      const jump = async (top) => {
        window.scrollTo({ top, left: startX, behavior: "instant" });
        await sleep(150);
      };
      const y1 = Math.min(Math.round(vh * 1.5), maxScroll);
      const y2 = y1 + 200 <= maxScroll ? y1 + 200 : y1 - 200;
      try {
        await jump(y1);
        const pinned = $$(BUTTONISH)
          .filter((el) => isButtonLike(el) && visible(el) && inView(el))
          .map((el) => ({ el, anchor: pinnedAncestor(el) }))
          .filter((x) => x.anchor)
          .map((x) =>
            Object.assign(x, { top: x.anchor.getBoundingClientRect().top }),
          );
        await jump(y2);
        const stuck = pinned.filter(
          (x) =>
            inView(x.el) &&
            Math.abs(x.anchor.getBoundingClientRect().top - x.top) < 2,
        );
        stickyAction = stuck.length > 0;
        stickySel = stuck.length ? sel(stuck[0].el) : null;
      } finally {
        window.scrollTo({ top: startY, left: startX, behavior: "instant" });
      }
    }

    return {
      ctasAboveFold: aboveFold
        .slice(0, CAP)
        .map((el) => ({ text: labelOf(el), href: hrefOf(el) })),
      ctasAboveFoldCount: aboveFold.length,
      ctaTotal: buttons.length,
      distinctLabels: labels.length,
      labels: labels.slice(0, CAP),
      contactLinkCtas: list(contact),
      forms,
      formCount: $$("form").length,
      stickyAction,
      stickySel,
      firstProofScreens,
    };
  });

  // ------------------------------------------------------------- budgets
  const count = (x) => (x && typeof x.count === "number" ? x.count : null);
  const num = (v) => (typeof v === "number" ? v : null);
  const values = {
    lcpMs: perf.lcp ? perf.lcp.ms : null,
    cls: num(perf.cls),
    longTaskMs: num(perf.longTaskMs),
    transferKB: perf.transferKB ? perf.transferKB.total : null,
    jsKB: perf.transferKB ? perf.transferKB.js : null,
    renderBlocking: num(perf.renderBlocking),
    smallTargets24: count(a11y.smallTargets24),
    lowContrast: count(a11y.lowContrast),
    missingAlt: count(a11y.missingAlt),
    unlabelledControls: count(a11y.unlabelledControls),
    horizontalOverflow: page.horizontalOverflow,
    contactLinkCtas: count(conversion.contactLinkCtas),
  };
  const verdicts = {};
  const fail = [];
  const unmeasured = [];
  for (const key of Object.keys(values)) {
    const value = values[key];
    const budget = budgets[key];
    let pass = null;
    if (value === null) unmeasured.push(key);
    else if (typeof budget === "boolean") pass = budget || !value;
    else if (typeof budget === "number") pass = value <= budget;
    verdicts[key] = {
      value,
      budget: budget === undefined ? null : budget,
      pass,
    };
    if (pass === false) fail.push(key);
  }

  const result = {
    probe: "page_probe/1",
    page,
    perf,
    a11y,
    conversion,
    budgets,
    verdicts,
    fail,
    unmeasured,
  };
  if (errors.length) result.errors = errors;

  // Keep the payload near 6 KB: trim example lists, never the counts or verdicts.
  const KEEP = { fail: 1, unmeasured: 1, caveats: 1, errors: 1 };
  const trim = (node, n) => {
    if (!node || typeof node !== "object") return;
    for (const key of Object.keys(node)) {
      const v = node[key];
      if (Array.isArray(v) && !KEEP[key] && v.length > n)
        node[key] = v.slice(0, n);
      trim(node[key], n);
    }
  };
  for (const n of [8, 5, 3, 1]) {
    if (JSON.stringify(result).length <= 6000) break;
    trim(result, n);
    result.truncated = true;
  }
  return result;
})()
