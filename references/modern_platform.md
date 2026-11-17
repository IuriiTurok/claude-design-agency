# Modern web platform: what to use, and how safely

Required read for the UI/UX Designer and the Motion Designer before writing a persuade surface. Status checked 2026-11-13 against webstatus.dev and caniuse.com; re-check a feature there before relying on anything marked newer than a year. "PE" means progressive enhancement: the page must be complete and correct without the feature.

The rule behind every row: the platform first, a library only when the platform cannot do it. Less JavaScript is faster interaction, and speed has the strongest conversion evidence of anything in this file.

## Use freely

| Feature | Use it for | Note |
| --- | --- | --- |
| OKLCH, `color-mix()` | Token ramps, hover and pressed states derived from one token | Keep hex in a comment when a hand-off needs it |
| `light-dark()` | Themed tokens in one declaration | Needs `color-scheme` on `:root` |
| Relative colour syntax | Tints and alpha variants of a token | Give a plain fallback colour on the line before |
| Container queries (size) | Components that adapt to their slot, not the viewport | Cards, job rows, sidebars |
| `:has()` | Parent state without JavaScript (a form group with an invalid field, a card with a focused control) | |
| Subgrid | Aligning card internals across a row | |
| `text-wrap: balance` | Headings up to about six lines | |
| `@starting-style` and `transition-behavior: allow-discrete` | Entry and exit of popovers, dialogs, details content and toasts without JavaScript | |
| Popover API, `<dialog>` | Menus, sheets, tooltips, modals: top layer, light dismiss and focus handling come free | Replaces most custom overlay code |
| `<details name>` | Exclusive accordions without JavaScript | |
| `content-visibility: auto` with `contain-intrinsic-size` | Long pages: skip rendering work below the fold | Not on sections that are anchor targets with unknown height |
| `fetchpriority="high"`, `loading="lazy"`, `decoding="async"` | The LCP image gets high priority and is never lazy; everything below the fold is lazy | |
| AVIF with WebP fallback via `<picture>`, explicit `width` and `height` | Every content image | Missing dimensions are a layout-shift defect |
| Variable fonts, self-hosted WOFF2, `font-display: swap`, `size-adjust` fallback | One file per family, preload only the face used above the fold | No remote font CSS in client work |
| `scrollbar-gutter: stable`, `overscroll-behavior` | Sheets and scroll areas that do not jump or chain | |
| `inert` | Everything behind an open sheet or dialog | |
| `dvh`, `svh` units | Full-height phone layouts | Never `100vh` for a hero on phones |

## Use as progressive enhancement

| Feature | Status | Use it for | Fallback |
| --- | --- | --- | --- |
| Same-document View Transitions | Newly available, 2025-10 | State changes inside a page: filter results, tab swaps, expanding a card | Instant swap. Wrap in `if (document.startViewTransition)` |
| Cross-document View Transitions (`@view-transition`) | Limited, Firefox partial | Page-to-page continuity on a multi-page site: a shared header, a card growing into its detail page | A normal navigation. Costs two lines of CSS; keep it under 250 ms |
| Scroll-driven animations (`animation-timeline`) | Newly available, 2026-10 | A reading-progress bar, a header that condenses, one reveal that tracks scroll position | Static end state inside `@supports not (animation-timeline: scroll())`. Too new to carry meaning |
| Anchor positioning | Core in all engines since 2026-01 | Tooltips and menus tethered to their trigger | A fixed, sensible position before the anchor rules |
| Container style queries | Newly available, 2026-05 | Variant switching from a custom property | Default variant |
| Invoker commands (`commandfor`, `command`) | Newly available, 2025-12 | Opening popovers and dialogs from a button without JavaScript | `popovertarget` or a small script |
| `field-sizing: content` | Newly available, 2026-06 | Textareas that grow with their content | Fixed `rows` |
| `sibling-index()` | Newly available, 2026-08 | Stagger delays without per-item styles | No stagger, or inline custom properties |
| `text-wrap: pretty` | Limited, no Firefox | Body paragraphs without orphans | None needed |
| `interpolate-size: allow-keywords` | Chromium only | Animating to `height: auto` (accordions) | The grid `0fr` to `1fr` technique, or no animation |
| Speculation rules | Chromium only | Prerender or prefetch the likely next page on hover or pointer-down; near-instant navigation on a multi-page site | None needed. Exclude sign-out, form posts and anything with side effects |
| Scroll-state queries | Chromium only | Styling a stuck header or a snapped item | Unstyled stuck state |

## Do not ship

| Feature | Why |
| --- | --- |
| CSS `if()` | Chromium only, and it changes computed values, so there is no clean fallback |
| `corner-shape` | Chromium only; decorative use at most, never structural |
| Grid lanes (masonry) | One engine |
| Scroll listeners that set state or style | Replaced by scroll-driven animations and `IntersectionObserver`; they cost interaction latency |
| Animation libraries for effects CSS can do | Weight and main-thread work for no visible gain |

## Motion that earns its place

- Animate `transform` and `opacity` only. Anything that triggers layout is a defect unless measured.
- One orchestrated moment per page, at most, where the brand shows itself. Everything else is feedback: under 200 ms, on the element the visitor touched.
- Every animation has a `prefers-reduced-motion: reduce` counterpart that keeps the information and drops the movement.
- Motion never delays reading. Content above the fold is visible at first paint; an entrance that hides the headline for 600 ms costs more than it gives.

## Budgets the build is held to

Lab targets, checked by `execution/probes/page_probe.js` in Visual QA; a project directive may tighten them.

| Budget | Target |
| --- | --- |
| LCP | at or under 2.5 s (field, 75th percentile, mobile); aim under 1.8 s in the lab |
| INP | at or under 200 ms (field). Not measurable in the lab; keep total long-task time under 300 ms as its proxy |
| CLS | at or under 0.1 |
| JavaScript transferred | under 300 KB; a static marketing page should need far less |
| Total transfer, first load | under 1.5 MB |
| Render-blocking resources | 3 or fewer |
| Accessibility | WCAG 2.2 AA: contrast 4.5:1 (3:1 large text), targets 24 x 24 CSS px minimum and 44 x 44 for primary actions on touch, visible focus, no keyboard trap |
