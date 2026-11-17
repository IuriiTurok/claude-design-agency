# Page probes

`page_probe.js` measures a loaded page from the inside: performance, accessibility and
conversion mechanics, each checked against a budget. It has no dependencies and makes no
network requests. The whole file is one expression (an async IIFE) that resolves to a
JSON-serialisable object of about 6 KB or less.

## Run it

**Browser JS tool** (Claude Browser `javascript_tool`, Chrome DevTools console, any REPL
that returns the value of the last expression): load the page, set the viewport, then paste
the file contents as the code to execute. The resolved object is the result.

**Playwright (Python):**

```python
from playwright.sync_api import sync_playwright

probe = open("execution/probes/page_probe.js", encoding="utf-8").read()
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in ((1440, 900), (390, 844)):
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="load")
        result = page.evaluate(probe)
        print(width, result["fail"], result["unmeasured"])
    browser.close()
```

Run it once per viewport on a fresh page load, after `load` has fired and before any
interaction. Override budgets first when the project sets its own:

```js
window.__PROBE_BUDGETS = { lcpMs: 2000, jsKB: 200, horizontalOverflow: false };
```

## Result

| Key | Contents |
|---|---|
| `page` | url, viewport, lang, title, `hasViewportMeta`, `horizontalOverflow`, `docHeight`, `screens` |
| `perf` | `ttfb`, `domContentLoaded`, `load`, `lcp {ms, sel, isImage, lazy, fetchpriority}`, `cls`, `longTaskMs`, `transferKB {total, js, css, img, font, other}`, `renderBlocking`, `thirdPartyOrigins`, `fontFiles`, `remoteFontCss`, `imagesNoDimensions`, `imagesLegacyFormat`, `findings`, `caveats` |
| `a11y` | `missingAlt`, `unlabelledControls`, `unnamedInteractive`, `headingSkips`, `h1Count` / `multipleH1`, `duplicateIds`, `smallTargets24`, `smallTargets44`, `lowContrast` (+ `sampled`, `unknown`), `reducedMotionHandled` |
| `conversion` | `ctasAboveFold`, `ctaTotal`, `distinctLabels` / `labels`, `contactLinkCtas`, `forms[] {sel, fields, required, topScreens, issues}`, `stickyAction`, `firstProofScreens` |
| `budgets` | thresholds in force (defaults merged with `window.__PROBE_BUDGETS`) |
| `verdicts` | per budget `{value, budget, pass}`; `pass` is `null` when the value could not be measured |
| `fail` | budget keys that failed |
| `unmeasured` | budget keys with no value (never count these as a pass) |

Finding lists are `{count, items: [{sel, note}]}` with at most 12 items; `count` is always
the full number. When the payload would exceed about 6 KB the example lists are shortened
and `truncated: true` is set. `sel` is a short CSS-ish path (`tag#id.class`, 60 chars).

## Hard gates and indicative numbers

Hard gates: deterministic for a given page and viewport, so a failure is a defect.

- `horizontalOverflow`
- `missingAlt`, `unlabelledControls`
- `smallTargets24` (WCAG 2.2 SC 2.5.8, with the inline-link and spacing exceptions)
- `lowContrast` (WCAG 1.4.3; 4.5:1, or 3:1 for text of 24 px, or 18.66 px bold, and up)
- `contactLinkCtas` (a button-like link that opens the mail or phone client)
- `cls`, `renderBlocking`, and `transferKB` / `jsKB` when the run is a cold load of the
  production build

Indicative: depend on the machine, the network and the build being served.

- `lcpMs`, `longTaskMs`, `ttfb`, `domContentLoaded`, `load`: lab timings from a dev
  machine. Compare before and after on the same machine; confirm with field data or a
  throttled Lighthouse run before claiming a Core Web Vitals result.
- `transferKB` / `jsKB` from a dev server (unminified, uncompressed) or a warm cache.
- `smallTargets44`, `headingSkips`, `multipleH1`, `duplicateIds`, `unnamedInteractive`,
  `imagesNoDimensions`, `imagesLegacyFormat`, `reducedMotionHandled`, `stickyAction`,
  `firstProofScreens`, form `issues`: advisory findings to review, with no budget.

## Caveats

- INP cannot be measured without real interaction, and total blocking time is only
  approximated by `longTaskMs` (time over 50 ms in each long task).
- LCP, CLS and long tasks need a Chromium browser and a visible tab. In a hidden tab,
  Firefox or Safari they come back `null` and the key is listed under `unmeasured`.
- Resources served from cache, or cross-origin without `Timing-Allow-Origin`, report no
  size, so `transferKB` is a floor. `perf.caveats` says how many.
- Contrast is computed from CSS colours. Text over a background image or gradient is
  counted as `unknown` and not flagged; text placed over another element by absolute
  positioning is judged against its own ancestors. Check those by eye.
- `reducedMotionHandled` cannot read cross-origin stylesheets; a rule that lives only
  there is not seen.
- Target sizes and overflow depend on the viewport: run at 1440×900 and at 390×844.
- The probe scrolls once to test `stickyAction` and restores the scroll position. That can
  trigger lazy loading and scroll-driven effects, so take screenshots and measurements
  that must not be affected before running it, or reload afterwards.
- The file must stay a bare expression. Do not let a formatter append a semicolon (the
  `prettier-ignore` comment in the file prevents that).
