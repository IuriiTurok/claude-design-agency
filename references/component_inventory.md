# Component Inventory — Canonical Reference

> **Status:** canonical. This file is the single source of truth for "what a production app design system contains" inside this agency.
> **Distilled from:** a shipped fintech design system (44 sections, ~35 components, 10-criterion scorecard) cross-checked against Material 3, shadcn/ui, Polaris, Carbon.
> **Consumers:** [`design_system_expert.md`](../roles/design_system_expert.md), [`brandbook_designer.md`](../roles/brandbook_designer.md) (Section 05), [`style_enforcer.md`](../roles/style_enforcer.md) (Inventory Completeness check group).
> **Tiering legend:** **R** = v1-required (ship or document a deliberate skip) · **r** = v1-recommended (ship if product type warrants) · **a** = advanced (capture as backlog).

---

## A. Token Layers

Every project ships these token categories. Missing categories are flagged by the Style Enforcer.

| # | Layer | Required content | Status |
|---|-------|------------------|--------|
| A1 | **Color** | Primitive ramps (50→950) per hue · semantic aliases (`background`, `surface`, `surface-muted`, `border`, `text`, `text-muted`, `text-secondary`, `accent`, `accent-foreground`, `ring`) · status colors (`success`, `warning`, `destructive`, `info`) · **light + dark + system modes** · WCAG AA contrast target stated per pair | R |
| A2 | **Typography** | Scale display→caption (≥7 steps) · families (sans + display + mono) · weights (≤3 per screen) · line-height per step · letter-spacing per step · **tabular-figures variant** for data | R |
| A3 | **Spacing** | 4-based scale `4, 8, 12, 16, 24, 32, 48, 64, 96` with named tokens `xs..3xl`; component padding tokens defined separately | R |
| A4 | **Radius** | `sm` (8) · `md` (12) · `lg` (16) · `xl` (24) · `2xl` (32) · `full` (9999); vary by element (avoid one global radius) | R |
| A5 | **Shadow / elevation** | ≥4 tiers (`xs`/`sm`/`md`/`lg`) + dedicated `hover` tier; **dark-mode variants** (shadows fade in dark, replace with ring/border on dark surfaces) | R |
| A6 | **Motion** | Duration tokens (`instant` 100 / `fast` 200 / `standard` 300 / `page` 350 / `modal` 400 / `entrance` 500) · easing tokens (`out` / `material` / `spring` / `spring-strong`) · **`prefers-reduced-motion` block** mandatory | R |
| A7 | **Z-index** | Named scale: `base` 0 · `dropdown` 100 · `sticky` 200 · `overlay` 400 · `modal` 500 · `popover` 600 · `toast` 700 · `tooltip` 800 (never hardcode `z-index: 50`) | R |
| A8 | **Breakpoints** | `xs` 360 · `sm` 640 · `md` 768 · `lg` 1024 · `xl` 1280 · `2xl` 1536; document min/max; note container-query usage where appropriate | R |
| A9 | **Iconography** | Library choice (Lucide / Phosphor / custom) · stroke weight · sizes (`12` / `16` / `20` / `24` / `32`) · two-tone vs single-tone rule · custom icon spec | R |
| A10 | **Gradients** | Semantic name per gradient · **max 4** total (anti-bloat rule); each must trace to a directive entry | r |

**Token-system anti-patterns (auto-fail):**
- `var(--font-sans)` inside `@theme inline` (circular reference, breaks single-file HTML).
- Hardcoded hex values inside component CSS (must reference a token).
- Single-radius lazy default (`border-radius: 8px` applied to everything).
- No dark-mode tokens.
- No `prefers-reduced-motion` block.

---

## B. Component Inventory

Each row: name · purpose · expected variants · expected states · a11y notes · tier.
"States" baseline = `default · hover · focus-visible · active · disabled · loading · error · selected · readonly` (apply those that exist for the component).

### B1. Actions

| Component | Variants | Sizes | Key states | A11y | Tier |
|-----------|----------|-------|------------|------|------|
| Button | primary · secondary · ghost · destructive · link | sm · md · lg · xl | all baseline + `pending`/`loading` | `<button>`, focus ring, ≥44×44 target on touch | R |
| Icon Button | same variants | sm · md · lg | all baseline | mandatory `aria-label` | R |
| Toggle Button | unpressed / pressed | sm · md · lg | all + `aria-pressed` | `role="button"` + `aria-pressed` | r |
| Split Button | primary + menu | md · lg | all + menu open | menu keyboard nav, ESC closes | a |
| Button Group | segmented · separated | sm · md · lg | per-button states + `aria-current` for active | `role="group"`, arrow-key nav for segmented | r |
| FAB | regular · extended | md · lg | all baseline | position-fixed; `aria-label` mandatory | a |
| Arrow Link | inline · standalone | inherits text | hover translate-x, focus ring | `<a>` with visible focus | r |

### B2. Forms

| Component | Variants | Key states | A11y | Tier |
|-----------|----------|------------|------|------|
| Input | text · email · password · number · search · url · tel | default · focus · invalid · disabled · readonly · loading | `<label>` paired via `for`/`id`; `aria-describedby` for help/error | R |
| Textarea | resize-none · auto-grow | same as Input | same | R |
| Select (native) | single | default · focus · disabled | native `<select>`; never style away the affordance | R |
| Combobox | single · async · creatable | + open · loading · empty | `role="combobox"`, `aria-expanded`, listbox keyboard nav | r |
| Multi-select | chip · checkbox-list | + chips overflow | same as combobox + chip removal | r |
| Checkbox | single | default · checked · indeterminate · disabled · error | `<input type=checkbox>`, label clickable, focus ring | R |
| Checkbox Group | inline · stacked | per-checkbox | `<fieldset>` + `<legend>` | R |
| Radio Group | inline · stacked | per-radio | `<fieldset>` + `<legend>`, arrow-key nav | R |
| Toggle / Switch | sm · md | default · on · off · disabled | `role="switch"`, `aria-checked` | R |
| Slider | single · range | default · hover · focus · disabled | `<input type=range>`, `aria-valuemin/max/now` | r |
| Date Picker | single · range | + calendar open · invalid | text input fallback, screen-reader date readout | r |
| Time Picker | 12h · 24h | + open | same | r |
| File Upload | single · multi · drag-drop | + dragover · uploading · success · error | hidden `<input type=file>` paired with visible button | R |
| OTP / PIN Input | 4 · 6 digit | + filled · error | `inputmode="numeric"`, autofill `one-time-code` | a |
| Color Picker | swatch · spectrum | + open · invalid | text fallback, contrast hint | a |
| Rating | stars · numeric | + half-state · readonly | `role="radiogroup"`, label per option | r |
| Form Field | label · help · error anatomy | per-input | `aria-describedby` wiring, error `role="alert"` | R |
| Fieldset | bordered · borderless | per-group | `<fieldset>` + `<legend>` mandatory | R |

### B3. Data display

| Component | Variants | Key states | A11y | Tier |
|-----------|----------|------------|------|------|
| Card | default · elevated · interactive · outlined | default · hover (interactive) · focus · disabled | if interactive: `<a>`/`<button>` wrap or `role="link"` | R |
| Stat / KPI Card | with-delta · with-sparkline | + loading skeleton | label associated with value, delta described | r |
| List | 1-line · 2-line · 3-line · with-icon · with-avatar | + selected | `role="list"` / `<ul>` | R |
| Description List | inline · stacked | — | `<dl>`/`<dt>`/`<dd>` | r |
| Table | sortable · selectable · sticky-header · expandable rows · inline-edit | + sort asc/desc · row hover · selected · empty · loading · paginated | `<th scope>`, `aria-sort`, caption mandatory | R |
| DataGrid | column reorder · resize · pinned cols · virtualized | + dragging col · resizing · loading more | `role="grid"`, full keyboard model | a |
| Tree | expandable · selectable · checkbox | + expanded · selected | `role="tree"`, arrow-key nav | a |
| Avatar | image · initials · icon | + size scale · status dot · loading | `alt` if image, `aria-label` if initials | R |
| Avatar Group / Stack | overlapping · spaced | + overflow count | each avatar labelled | r |
| Badge | semantic colors × 6 | + outline vs solid | text + color (don't rely on color alone) | R |
| Tag / Pill | static · removable | + focus · removing | if removable: keyboard delete | R |
| Chip | filter · input · choice | + selected · removable · disabled | role per use; arrow-key nav for chip groups | r |
| Timeline | vertical · horizontal · with-icons | + completed · active · pending | `<ol>` with semantic order | r |
| Calendar | month · week · year | + selected · range · disabled date | grid + arrow-key nav | a |
| Kanban | columns · cards | + dragging · drop-target | full keyboard reorder | a |

### B4. Navigation

| Component | Variants | Key states | A11y | Tier |
|-----------|----------|------------|------|------|
| Top Nav | static · sticky · transparent-on-hero | + scrolled · mobile-collapsed | `<nav aria-label>`, skip link | R |
| Sidebar Nav | expanded · collapsed · floating | + active · expanded section · hover | landmark `<nav>`, `aria-current="page"` | R |
| Tabs | line · segmented · pill | + active · disabled · with-badge | `role="tablist"`, arrow-key nav | R |
| Breadcrumb | with-icon · text-only · truncated | + current page | `<nav aria-label="Breadcrumb">`, `aria-current="page"` | R |
| Pagination | numbered · prev/next · jump-to · cursor | + current · disabled at bounds | `aria-label` per control | R |
| Stepper / Wizard | horizontal · vertical · numbered · icon | + completed · current · upcoming · error | progress announced to SR | r |
| Anchor / scroll-spy nav | sidebar · floating | + active section | smooth-scroll respects reduced-motion | r |
| Mobile Tab Bar | 3–5 items · with-FAB | + active · with-badge | `<nav>` + landmark, ≥44×44 targets | r |
| Menubar | top-level | + open · keyboard | full ARIA menubar pattern | a |
| Context Menu | right-click · long-press | + open · keyboard | `aria-haspopup`, ESC closes | r |

### B5. Overlays

| Component | Variants | Key states | A11y | Tier |
|-----------|----------|------------|------|------|
| Modal / Dialog | confirmation · form · alert · fullscreen | + open · closing · scrim click | focus trap, `role="dialog"`, `aria-labelledby`, ESC closes, focus restore | R |
| Drawer / Sheet | left · right · bottom · top | + open · closing · resizing | same as Modal | R |
| Popover | top · right · bottom · left · auto-flip | + open · closing | focus trap optional; click-outside closes | R |
| Tooltip | top · right · bottom · left | + show on hover/focus · delay | `role="tooltip"`, never hide critical info inside | R |
| Dropdown Menu | from button · from icon-button | + open · highlighted · disabled | `role="menu"`, arrow-key nav, ESC closes | R |
| User Menu | with-avatar · with-account-switcher | + open | same as Dropdown Menu | R |
| Combobox popover | from Combobox | + open · loading · empty | listbox pattern | r |
| Command Palette (⌘K) | search · grouped · with-recents | + open · highlighted · loading · empty | full keyboard model, listbox + textbox | r |
| Hover Card | from link/avatar | + delay · open | hover + focus parity (keyboardable) | r |

### B6. Feedback & status

| Component | Variants | Key states | A11y | Tier |
|-----------|----------|------------|------|------|
| Alert | info · success · warning · error | + dismissible · with-action | `role="alert"` for live ones; text + icon (don't rely on color) | R |
| Banner | top-of-page · sticky | + dismissible | `role="region"` + label | r |
| Toast / Snackbar | info · success · warning · error · with-action | + entering · visible · leaving · queue ≥2 | `role="status"` or `aria-live="polite"`; long-enough timeout; pause on focus | R |
| Inline message | help · warn · error | per-field | `aria-describedby` paired with input | R |
| Progress | linear · circular · indeterminate · segmented | + value · label · complete | `<progress>` or `role="progressbar"`, `aria-valuenow` | R |
| Spinner | sm · md · lg | only as last resort — prefer skeleton | `role="status"` + SR-only label | r |
| Skeleton | line · circle · rect · card · table-row | + shimmer · static | `aria-busy="true"` on container | R |
| Empty State | first-use · zero-results · zero-data | + with-illustration · with-action | meaningful copy, primary CTA | R |
| Error State | inline · full-page · partial | + retry · contact-support | clear cause + next action | R |
| Loading State | inline · overlay · full-page | + skeleton vs spinner choice documented | `aria-busy`, focus management on resolve | R |
| Status Indicator / Dot | online · offline · busy · away · custom | + with-label | text + color | R |

### B7. Media & content

| Component | Variants | Key states | A11y | Tier |
|-----------|----------|------------|------|------|
| Image | with-aspect-ratio · with-blur-placeholder · with-fallback | + loading · errored | `alt` mandatory, decorative = `alt=""` | R |
| Icon | inline · standalone · in-button | + size scale | `aria-hidden="true"` when decorative, `<title>` if standalone informational | R |
| Video | with-controls · with-poster · background-muted | + playing · paused · errored | captions track, controls keyboardable | r |
| Code Block | with-line-numbers · with-copy · with-language | + copied flash | language announced, copy button labelled | r |
| Quote / Blockquote | inline · standalone-pull | — | `<blockquote>` + `<cite>` | r |
| Divider | horizontal · vertical · with-label | — | `role="separator"` if non-decorative | R |
| Carousel | with-dots · with-arrows · auto-play | + transitioning · paused · current slide | `aria-roledescription="carousel"`, pause-on-hover, keyboard arrows | r |
| Logo Carousel / Marquee | infinite-scroll · paused-on-hover | + paused | `aria-hidden` on visual marquee; provide text list alt | r |

### B8. Layout primitives

These are the "Stack/Grid/Container" toolkit — define them as utilities, not components.

| Primitive | Purpose | Tier |
|-----------|---------|------|
| Container | max-width centering at breakpoints | R |
| Grid | 12-col + container-query variant | R |
| Stack (V/H) | gap-based vertical/horizontal stack | R |
| Cluster | wrap-on-overflow horizontal group | R |
| Sidebar Layout | nav + content with collapse | R |
| Split | two-pane resizable | r |
| Aspect Ratio Box | 16:9, 4:3, 1:1, custom | R |
| Scroll Area | styled scrollbar, momentum | r |
| AppShell | nav + main + aside + footer composition | R |

### B9. Data viz

If the product is data-heavy (analytics, finance, ops dashboards), the data-viz layer is **R**; otherwise **r**.

| Chart type | Tier |
|------------|------|
| Bar / Column | r |
| Line / Area | r |
| Pie / Donut | r |
| Scatter | a |
| Sparkline | r |
| Gauge / Radial progress | a |
| Heatmap | a |

**Chart token system** (define once, reuse across types):
- Categorical palette (≥8 hues, colorblind-checked).
- Sequential palette (light→dark, perceptually uniform).
- Diverging palette (negative→neutral→positive).
- Axis token (color, weight, label font size).
- Gridline token (color, opacity).
- Tooltip token (uses overlay surface + shadow + radius from token layers).
- Empty / loading / error states per chart.

### B10. Domain-specific (optional)

Surface these only if the product type calls for them:

| Component | Domain | Tier |
|-----------|--------|------|
| Map + Pins | location, logistics | a |
| Address Autocomplete | commerce, fintech | r |
| Phone Input (country) | international | r |
| Currency Input | finance, billing | r |
| Pricing Card | SaaS | r |
| Plan Picker (segmented) | SaaS | r |
| Diff Viewer | dev tools | a |
| Mention Input (`@`) | social, collaboration | a |
| Candidate / Profile Card | HR-tech | a |

---

## C. Patterns (page-level)

Patterns compose B-components. Every project ships the **R** patterns; promote others by product type.

| Pattern | Composes | Tier |
|---------|----------|------|
| AppShell | Top Nav · Sidebar Nav · Container · Scroll Area | R |
| Auth flow (sign-in / sign-up / reset / verify) | Form Field · Button · Alert · OTP | R |
| Onboarding (multi-step) | Stepper · Form Field · Progress · Empty State | R |
| Empty / zero-data | Empty State · Button · Icon · Illustration | R |
| Error recovery | Error State · Button · Code Block (if dev) | R |
| Settings | Sidebar Nav · Form Field · Toggle · Tabs · Confirmation Modal | R |
| Search results | Input · Combobox · Card / List · Pagination · Empty State | R |
| Detail page | Breadcrumb · Tabs · Card · Action bar · Toast | R |
| Confirmation | Modal · Button (primary + ghost) | R |
| Destructive confirm | Modal · Button (destructive) · Text-match-to-confirm input | R |
| Billing | Pricing Card · Plan Picker · Form Field · Payment input · Table | r |
| Profile | Avatar · Form Field · Tabs · Card | R |
| Dashboard | Stat Card · Chart · Table · Filter chips · Date Range | r |
| Activity feed | Timeline · Avatar · Empty State | r |
| Inbox | List · Badge · Filter · Empty State | r |
| Wizard | Stepper · Form Field · Button group (back/next) · Confirmation | r |

---

## D. Documentation depth (per component)

Lifted from that system's 10-criterion scorecard. **Min score 8/10 to ship a component.**

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 1 | Purpose statement | One sentence stating what the component is for |
| 2 | When to use | At least two scenarios listed |
| 3 | When NOT to use | At least one alternative pointed to |
| 4 | Variants visible | Every variant rendered, with label |
| 5 | Variant count declared | Count stated in section title, intro, or scorecard |
| 6 | Sizes shown | All supported sizes rendered side-by-side (N/A if no size scale) |
| 7 | States catalogued | default · hover · focus-visible · active · disabled · loading · error · selected · readonly (as applicable) |
| 8 | Class / prop reference | Dev-handoff `.class-ref` block listing base + modifier classes (or shadcn props table) |
| 9 | Brand alignment | Visibly conforms to `style_directive.md` (accent, focus ring, motion) |
| 10 | Accessibility note | Role, labelling, keyboard pattern documented |

---

## E. Tiering decision (per archetype)

Use these heuristics when scoping a client's v1 design system.

| Product archetype | Promote to v1-required (in addition to R-baseline) | Demote to a |
|-------------------|-----------------------------------------------------|-------------|
| **Marketing site** | Banner, Logo Carousel, Carousel, Hover Card | Table, DataGrid, Command Palette, Tree |
| **Consumer app (mobile-first)** | Mobile Tab Bar, FAB, Sheet (bottom), Toast with action, Empty State illustrations | DataGrid, Tree, Diff Viewer, Menubar |
| **B2B SaaS** | Sidebar Nav (collapsed/expanded), Table (full), Tabs, Stepper, Filter chips, Empty State, Command Palette | FAB, Mobile Tab Bar |
| **Data-heavy / analytics** | DataGrid, Charts (Bar/Line/Sparkline at min), Stat Card, Date Range, Filter chips, Heatmap (if relevant) | Carousel, Pricing Card |
| **Dev tool** | Code Block (with copy + language), Command Palette, Diff Viewer, Inline message, Toast | Carousel, FAB, Calendar |
| **Fintech / commerce** | Currency Input, Address Autocomplete, Pricing Card, Plan Picker, Table, Stepper | Map, Kanban |

---

## F. "Gaps to flag" — Style Enforcer rules

These map to the **Inventory Completeness** check group in [`style_enforcer.md`](../roles/style_enforcer.md). Each rule emits `OK` / `PARTIAL` / `MISSING`. Default severity is **advisory**; promote to **hard-fail** when the project's `style_directive.md` explicitly calls the item out (e.g. directive declares "dark mode required" → missing dark tokens becomes hard-fail).

| Rule | Detection (grep / DOM check) | Default severity |
|------|------------------------------|------------------|
| Dark-mode tokens missing | No `@media (prefers-color-scheme: dark)` block AND no `.dark` class AND no `[data-theme="dark"]` token set in `:root` | advisory |
| Breakpoint scale missing | Fewer than 3 distinct `@media (min-width: …)` values across the file | advisory |
| Z-index scale missing | More than 2 distinct hardcoded `z-index:` values without named CSS variables | advisory |
| Tabular-figures font missing | No `font-variant-numeric: tabular-nums` and no `font-feature-settings: "tnum"` anywhere | advisory |
| `prefers-reduced-motion` block missing | No `@media (prefers-reduced-motion: reduce)` block | **hard-fail** |
| Focus-visible absent on interactive elements | Any `<button>` / `<a>` / `<input>` selector lacks `:focus-visible` rule | **hard-fail** |
| Skeleton variants missing | DS file has no `.skeleton` / `.shimmer` / similar variant when product is data-heavy | advisory |
| Empty state pattern missing | DS file has no "empty state" section / pattern | advisory |
| Toast queue policy undocumented | Toast section exists but no copy describes queue length / pause-on-hover / timeout | advisory |
| Loading spinner used as primary loading affordance | `.spinner` / `@keyframes spin` present without skeleton or progress alternative | advisory (project anti-pattern: hard-fail) |
| Single uniform radius | All radius declarations resolve to one value | advisory |
| Multi-accent fight | More than 1 unique non-neutral, non-semantic color used as accent | **hard-fail** (already covered in `style_enforcer.md` anti-patterns) |
| Doc-depth shortfall | Component section scores <8/10 against [section D](#d-documentation-depth-per-component) | advisory |
| Coverage shortfall vs tier | Required `R` components for the chosen archetype are absent from the DS | advisory (report at Phase 6 close) |

---

## G. Tech-stack mapping

How the inventory maps to the agency's default stack (Tailwind v4 + shadcn/ui + Next.js, as set in [`design_system_expert.md`](../roles/design_system_expert.md)).

### Tailwind v4 `@theme inline` keys per token category

| Token category (A1–A10) | `@theme inline` keys |
|--------------------------|----------------------|
| A1 Color | `--color-background`, `--color-foreground`, `--color-primary[-foreground]`, `--color-muted[-foreground]`, `--color-accent[-foreground]`, `--color-destructive[-foreground]`, `--color-success`, `--color-warning`, `--color-info`, `--color-border`, `--color-input`, `--color-ring` |
| A2 Typography | `--font-sans`, `--font-display`, `--font-mono`; text size scale via `--text-*` |
| A3 Spacing | `--spacing-*` (Tailwind v4 auto-scales but document the named scale) |
| A4 Radius | `--radius`, `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-2xl` |
| A5 Shadow | `--shadow-xs`, `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-hover` |
| A6 Motion | `--ease-out`, `--ease-spring`, `--dur-fast`, `--dur-standard`, `--dur-modal` |
| A7 Z-index | `--z-dropdown`, `--z-sticky`, `--z-overlay`, `--z-modal`, `--z-popover`, `--z-toast`, `--z-tooltip` |
| A8 Breakpoints | Tailwind defaults; document overrides in `@theme` |

### shadcn/ui install map (B → shadcn primitives)

Use this as the canonical install list. Run `npx shadcn@latest add <names>` after `init`.

| B-group | shadcn primitives (R-tier minimum) |
|---------|------------------------------------|
| B1 Actions | `button` |
| B2 Forms | `input` · `textarea` · `select` · `checkbox` · `radio-group` · `switch` · `slider` · `label` · `form` |
| B3 Data display | `card` · `table` · `badge` · `avatar` · `separator` |
| B4 Navigation | `navigation-menu` · `tabs` · `breadcrumb` · `pagination` (community) · `sidebar` |
| B5 Overlays | `dialog` · `sheet` · `popover` · `tooltip` · `dropdown-menu` · `hover-card` · `command` |
| B6 Feedback | `alert` · `toast` (or `sonner`) · `progress` · `skeleton` |
| B7 Media | `aspect-ratio` |
| B8 Layout | `scroll-area` · `resizable` |

Add `data-table` (TanStack Table + shadcn recipe) for the **R**-tier `Table`; promote to `DataGrid` if archetype is data-heavy.

### Coverage matrix output format

Phase 5 deliverable (produced by `design_system_expert`, consumed by `style_enforcer` and `brandbook_designer`). Drop into `design_system/coverage_matrix.md`:

```markdown
## Coverage Matrix — <project>

**Archetype:** <marketing | consumer | b2b-saas | data-heavy | dev-tool | fintech>
**Tier targets:** R = required, r = recommended, a = advanced

| B-group | Component | Tier | Status | Notes |
|---------|-----------|------|--------|-------|
| B1 | Button | R | shipped | 4 variants × 4 sizes |
| B1 | Icon Button | R | shipped | — |
| B3 | Table | R | shipped (basic) | sortable; no virtualization (deferred to v2) |
| B5 | Command Palette | r | skipped | not required for archetype |
| B9 | Charts | r | deferred | sparkline only in v1 |
```

Skipped items must include a rationale. Deferred items must include a target version.

---

## Maintenance

- This file is **append-only-friendly**: new components get appended to the relevant B-group with a tier tag.
- Renames cascade — update [`design_system_expert.md`](../roles/design_system_expert.md), [`brandbook_designer.md`](../roles/brandbook_designer.md), [`style_enforcer.md`](../roles/style_enforcer.md) if a component name changes.
- Keep a shipped in-house design system as the live reference implementation for R-tier items, and track its known gaps alongside it.
