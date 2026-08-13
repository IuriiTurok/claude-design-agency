---
name: ui-ux-pro-max
description: "UI/UX design intelligence for web and mobile — generates design systems, picks styles/palettes/type pairings, and reviews UI code for quality and accessibility. Use whenever the task changes how a feature looks, feels, moves, or is interacted with — building or refactoring pages and components, choosing color/typography/spacing/layout, adding animation or responsive behavior, or reviewing UI for usability and a11y — even if the user never says 'UI', 'UX', or 'design'. Covers 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, and 25 chart types across 10 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, HTML/CSS). Projects: website, landing, dashboard, admin, e-commerce, SaaS, portfolio, blog, mobile app. Styles: glassmorphism, claymorphism, minimalism, brutalism, bento, dark mode, flat. Skip for pure backend, API/DB-only, infra/DevOps, or non-visual scripting. Integrates shadcn/ui MCP."
---

# UI/UX Pro Max - Design Intelligence

Comprehensive design guide for web and mobile applications. A searchable database (50+ styles, 161 color palettes, 57 font pairings, 161 product types with reasoning rules, 99 UX guidelines, 25 chart types across 10 technology stacks) plus priority-based recommendations, driven by Python search scripts.

## Table of Contents

- [When to Apply](#when-to-apply)
- [Rule Categories by Priority](#rule-categories-by-priority)
- [How to Use This Skill](#how-to-use-this-skill) (Steps 1–4)
- [Search Reference](#search-reference) (domains + stacks)
- [Quick Reference §1–§10](#quick-reference) → `references/quick-reference.md`
- [Common App UI Rules](#common-app-ui-rules) → `references/app-ui-rules.md`
- [Pre-Delivery Checklist](#pre-delivery-checklist)
- [Eval](#eval)
- [I/O Contract](#io-contract)
- [Self-learning](#self-learning)
- [Self-improvement loop (sil)](#self-improvement-loop-sil) — heavyweight sil adapter; ONE_CLICK, never auto-applies
- [Recommended next step](#recommended-next-step)

## When to Apply

Use this Skill when the task involves **UI structure, visual design decisions, interaction patterns, or user experience quality control**.

**Upstream note:** typically entered from `design-agency` / `lead-design-engineer` (Design Phase 5); can also run standalone.

### Must Use

- Designing new pages (Landing Page, Dashboard, Admin, SaaS, Mobile App)
- Creating or refactoring UI components (buttons, modals, forms, tables, charts, etc.)
- Choosing color schemes, typography systems, spacing standards, or layout systems
- Reviewing UI code for user experience, accessibility, or visual consistency
- Implementing navigation structures, animations, or responsive behavior
- Making product-level design decisions (style, information hierarchy, brand expression)
- Improving perceived quality, clarity, or usability of interfaces

### Recommended

- UI looks "not professional enough" but the reason is unclear
- Receiving feedback on usability or experience
- Pre-launch UI quality optimization
- Aligning cross-platform design (Web / iOS / Android)
- Building design systems or reusable component libraries

### Skip

- Pure backend logic, API/DB-only, or infra/DevOps work
- Performance optimization unrelated to the interface
- Non-visual scripts or automation tasks

**Decision criteria:** if the task will change how a feature **looks, feels, moves, or is interacted with**, use this Skill.

## Rule Categories by Priority

*Follow priority 1→10 to decide which rule category to focus on first; use `--domain <Domain>` to query details. Scripts do not read this table.*

| Priority | Category | Impact | Domain | Key Checks (Must Have) | Anti-Patterns (Avoid) |
|----------|----------|--------|--------|------------------------|------------------------|
| 1 | Accessibility | CRITICAL | `ux` | Contrast 4.5:1, Alt text, Keyboard nav, Aria-labels | Removing focus rings, Icon-only buttons without labels |
| 2 | Touch & Interaction | CRITICAL | `ux` | Min size 44×44px, 8px+ spacing, Loading feedback | Reliance on hover only, Instant state changes (0ms) |
| 3 | Performance | HIGH | `ux` | WebP/AVIF, Lazy loading, Reserve space (CLS &lt; 0.1) | Layout thrashing, Cumulative Layout Shift |
| 4 | Style Selection | HIGH | `style`, `product` | Match product type, Consistency, SVG icons (no emoji) | Mixing flat & skeuomorphic randomly, Emoji as icons |
| 5 | Layout & Responsive | HIGH | `ux` | Mobile-first breakpoints, Viewport meta, No horizontal scroll | Horizontal scroll, Fixed px container widths, Disable zoom |
| 6 | Typography & Color | MEDIUM | `typography`, `color` | Base 16px, Line-height 1.5, Semantic color tokens | Text &lt; 12px body, Gray-on-gray, Raw hex in components |
| 7 | Animation | MEDIUM | `ux` | Duration 150–300ms, Motion conveys meaning, Spatial continuity | Decorative-only animation, Animating width/height, No reduced-motion |
| 8 | Forms & Feedback | MEDIUM | `ux` | Visible labels, Error near field, Helper text, Progressive disclosure | Placeholder-only label, Errors only at top, Overwhelm upfront |
| 9 | Navigation Patterns | HIGH | `ux` | Predictable back, Bottom nav ≤5, Deep linking | Overloaded nav, Broken back behavior, No deep links |
| 10 | Charts & Data | LOW | `chart` | Legends, Tooltips, Accessible colors | Relying on color alone to convey meaning |

The full per-rule digest for all ten categories lives in **`references/quick-reference.md`** (load it for review / fix / pre-delivery passes — see Pre-Delivery Checklist).

## Prerequisites

Check Python is installed: `python3 --version || python --version`. If absent, install per OS (macOS `brew install python3`; Debian/Ubuntu `sudo apt install python3`; Windows `winget install Python.Python.3.12`).

## How to Use This Skill

| Scenario | Trigger Examples | Start From |
|----------|-----------------|------------|
| **New project / page** | "Build a landing page", "Build a dashboard" | Step 1 → Step 2 (design system) |
| **New component** | "Create a pricing card", "Add a modal" | Step 3 (domain search: style, ux) |
| **Choose style / color / font** | "What style fits a fintech app?", "Recommend a palette" | Step 2 (design system) |
| **Review existing UI** | "Review this page for UX issues", "Check accessibility" | `references/quick-reference.md` checklist |
| **Fix a UI bug** | "Button hover is broken", "Layout shifts on load" | `references/quick-reference.md` → relevant § |
| **Improve / optimize** | "Make this faster", "Improve mobile experience" | Step 3 (domain search: ux + stack) |
| **Implement dark mode** | "Add dark mode support" | Step 3 (domain: style "dark mode") |
| **Add charts / data viz** | "Add an analytics dashboard chart" | Step 3 (domain: chart) |
| **Stack best practices** | "React performance tips", "SwiftUI navigation" | Step 4 (stack search) |

### Step 1: Analyze User Requirements

Extract key information from the user request:
- **Product type**: Entertainment (social, video, music, gaming), Tool (scanner, editor, converter), Productivity (task manager, notes, calendar), or hybrid
- **Target audience**: consider age group, usage context (commute, leisure, work)
- **Style keywords**: playful, vibrant, minimal, dark mode, content-first, immersive, etc.
- **Stack**: detected from repo manifest or user request; defaults to none — pass it to `search.py` via the `--stack` arg when known (available stacks listed in [Search Reference](#available-stacks)).

### Step 2: Generate Design System (REQUIRED)

**Always start with `--design-system`** for comprehensive recommendations with reasoning:

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

This searches domains in parallel (product, style, color, landing, typography), applies the reasoning rules in `data/ui-reasoning.csv` to select best matches, and returns a complete design system (pattern, style, colors, typography, effects) plus anti-patterns to avoid.

```bash
# Example
python3 skills/ui-ux-pro-max/scripts/search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### Step 2b: Persist Design System (Master + Overrides Pattern)

To save the design system for **hierarchical retrieval across sessions**, add `--persist`:

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name" [--page "dashboard"]
```

Creates `design-system/<project>/MASTER.md` (global source of truth) and, with `--page`, `design-system/<project>/pages/<page>.md` (page-specific overrides).

**Hierarchical retrieval:** when building a specific page, first check `design-system/<project>/pages/<page>.md`; if it exists, its rules **override** MASTER.md; otherwise use MASTER.md exclusively.

### Step 3: Supplement with Detailed Searches (as needed)

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

Use after the design system to deep-dive any dimension: `product`, `style`, `color`, `typography`, `chart`, `ux`, `google-fonts`, `landing`, `react`, `web`, `prompt` (see [Available Domains](#available-domains)).

### Step 4: Stack Guidelines

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack <stack>
```

Stacks: `react-native`, `nextjs`, `shadcn-ui`, `tailwindcss`, `swiftui`, `flutter` (see [Available Stacks](#available-stacks)).

**Then:** synthesize design system + detailed searches and implement the design. The `--design-system` flag also supports `-f markdown` for documentation output (default is an ASCII box for terminal display).

## Search Reference

### Available Domains

| Domain | Use For | Example Keywords |
|--------|---------|------------------|
| `product` | Product type recommendations | SaaS, e-commerce, portfolio, healthcare, beauty, service |
| `style` | UI styles, colors, effects | glassmorphism, minimalism, dark mode, brutalism |
| `typography` | Font pairings, Google Fonts | elegant, playful, professional, modern |
| `color` | Color palettes by product type | saas, ecommerce, healthcare, beauty, fintech, service |
| `landing` | Page structure, CTA strategies | hero, hero-centric, testimonial, pricing, social-proof |
| `chart` | Chart types, library recommendations | trend, comparison, timeline, funnel, pie |
| `ux` | Best practices, anti-patterns | animation, accessibility, z-index, loading |
| `google-fonts` | Individual Google Fonts lookup | sans serif, monospace, japanese, variable font, popular |
| `react` | React/Next.js performance | waterfall, bundle, suspense, memo, rerender, cache |
| `web` | App interface guidelines (iOS/Android/React Native) | accessibilityLabel, touch targets, safe areas, Dynamic Type |
| `prompt` | AI prompts, CSS keywords | (style name) |

### Available Stacks

| Stack | Focus |
|-------|-------|
| `react-native` | Components, Navigation, Lists, Styling, Performance |
| `nextjs` | App Router, Server Components, Data Fetching, Caching, Streaming |
| `shadcn-ui` | Theming, Components, Forms, Composition, Dark Mode, Accessibility |
| `tailwindcss` | Layout, Responsive, Dark Mode, Animation, States, Performance |
| `swiftui` | Views, Layout, State, Animation, Navigation, Accessibility |
| `flutter` | Widgets, Material 3, State, Animation, Theming, Performance |

### Query Strategy

- Use **multi-dimensional keywords** — combine product + industry + tone + density: `"entertainment social vibrant content-dense"` not just `"app"`.
- Try alternates for the same need: `"playful neon"` → `"vibrant dark"` → `"content-first minimal"`.
- Use `--design-system` first for full recommendations, then `--domain` to deep-dive.
- Pass `--stack <stack>` for implementation-specific guidance.

## Quick Reference

The full priority-ordered rule digest for **§1–§10** (Accessibility, Touch & Interaction, Performance, Style Selection, Layout & Responsive, Typography & Color, Animation, Forms & Feedback, Navigation, Charts & Data) lives in **`references/quick-reference.md`**. Load it when reviewing UI, fixing a UI bug, or running a final review pass. For deeper detail on any individual rule, query `--domain ux`.

## Common App UI Rules

Frequently overlooked issues that make App UI look unprofessional — Icons & Visual Elements, Interaction, Light/Dark Mode Contrast, Layout & Spacing — live in **`references/app-ui-rules.md`**.
Scope notice: those tables are for App UI (iOS/Android/React Native/Flutter), not desktop-web interaction patterns.

## Common Sticking Points

| Problem | What to Do |
|---------|------------|
| Can't decide on style/color | Re-run `--design-system` with different keywords |
| Dark mode contrast issues | quick-reference §6: `color-dark-mode` + `color-accessible-pairs` |
| Animations feel unnatural | quick-reference §7: `spring-physics` + `easing` + `exit-faster-than-enter` |
| Form UX is poor | quick-reference §8: `inline-validation` + `error-clarity` + `focus-management` |
| Navigation feels confusing | quick-reference §9: `nav-hierarchy` + `bottom-nav-limit` + `back-behavior` |
| Layout breaks on small screens | quick-reference §5: `mobile-first` + `breakpoint-consistency` |
| Performance / jank | quick-reference §3: `virtualize-lists` + `main-thread-budget` + `debounce-throttle` |

Before implementation, run the [Pre-Delivery Checklist](#pre-delivery-checklist) below.

## Pre-Delivery Checklist

Before delivering UI code, verify these items.
Scope notice: this checklist is for App UI (iOS/Android/React Native/Flutter).

First run `--domain ux "animation accessibility z-index loading"` as a validation pass, then walk `references/quick-reference.md` **§1–§3** (CRITICAL + HIGH) as a final review.

### Visual Quality
- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons come from a consistent icon family and style
- [ ] Official brand assets are used with correct proportions and clear space
- [ ] Pressed-state visuals do not shift layout bounds or cause jitter
- [ ] Semantic theme tokens are used consistently (no ad-hoc per-screen hardcoded colors)

### Interaction
- [ ] All tappable elements provide clear pressed feedback (ripple/opacity/elevation)
- [ ] Touch targets meet minimum size (>=44x44pt iOS, >=48x48dp Android)
- [ ] Micro-interaction timing stays in the 150-300ms range with native-feeling easing
- [ ] Disabled states are visually clear and non-interactive
- [ ] Screen reader focus order matches visual order, and interactive labels are descriptive
- [ ] Gesture regions avoid nested/conflicting interactions (tap/drag/back-swipe conflicts)

### Light/Dark Mode
- [ ] Primary text contrast >=4.5:1 in both light and dark mode
- [ ] Secondary text contrast >=3:1 in both light and dark mode
- [ ] Dividers/borders and interaction states are distinguishable in both modes
- [ ] Modal/drawer scrim opacity is strong enough to preserve foreground legibility (typically 40-60% black)
- [ ] Both themes are tested before delivery (not inferred from a single theme)

### Layout
- [ ] Safe areas are respected for headers, tab bars, and bottom CTA bars
- [ ] Scroll content is not hidden behind fixed/sticky bars
- [ ] Verified on 375px small phone, large phone, and tablet (portrait + landscape)
- [ ] Horizontal insets/gutters adapt correctly by device size and orientation
- [ ] 4/8dp spacing rhythm is maintained across component, section, and page levels
- [ ] Long-form text measure remains readable on larger devices (no edge-to-edge paragraphs)

### Accessibility
- [ ] All meaningful images/icons have accessibility labels
- [ ] Form fields have labels, hints, and clear error messages
- [ ] Color is not the only indicator
- [ ] Reduced motion and Dynamic Type (largest size) are supported without layout breakage
- [ ] Accessibility traits/roles/states (selected, disabled, expanded) are announced correctly

## Eval

Binary smoke check (the minimal pass/fail assertion for this skill). From the skill directory:

```bash
python3 scripts/search.py "SaaS dashboard analytics" --design-system
```

**PASS** iff: exit code is 0 **and** stdout contains a non-empty `Style` block **and** a non-empty `Color` block.
**FAIL** otherwise (non-zero exit, empty output, or a missing Style/Color section).

This is the precondition for any future heavyweight self-learning (sil) candidacy — see [Self-learning](#self-learning).

## I/O Contract

**Inputs**
- User intent string: product type + industry + style keywords (the positional `query` arg).
- Optional `-p "Project Name"` (persistence target) and `--page "<name>"` (page-specific override).
- Optional `--domain <domain>` / `--stack <stack>` for targeted searches.
- Optional repo/user-supplied stack hint (no default).

**Outputs**
- Design-system recommendation (ASCII box or `-f markdown`): pattern, style, colors, typography, effects, anti-patterns.
- With `--persist`: `design-system/<project>/MASTER.md` and (with `--page`) `design-system/<project>/pages/<page>.md`.
- Domain/stack search results: BM25-ranked excerpts (Style + Color + Typography + guideline blocks) backed by the CSVs in `data/`.

**Dependencies**
- Scripts: `scripts/search.py` (CLI entry), `scripts/design_system.py`, `scripts/core.py`. Data: `data/*.csv` (incl. `ui-reasoning.csv`) and `data/stacks/`.
- Upstream: `design-agency` / `lead-design-engineer` (Design Phase 5 entry).
- Downstream: `impeccable` (AI-slop / quality gate), then `ship` (delivery).
- Optional integration: shadcn/ui MCP for component search.

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/ui-ux-pro-max.md`  (preferred when inside a project)
2. `<this-skill-dir>/LESSONS.md`                  (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected a design-system pick or generated UI), a *gotcha* (a non-obvious failure you had to work around — e.g. a flagged AI-slop pattern, or an `impeccable` override), or a *durable insight* worth reusing. Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: ui-ux-pro-max/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 ~/.claude/lib/self-improving-loop/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "ui-ux-pro-max/<project>"`

> This lightweight loop is distinct from `--persist` (which writes per-project design-system *output*, not skill learning). The **heavyweight sil adapter** for design-system reasoning (learning which reasoning rules in `data/ui-reasoning.csv` survive vs. get overridden, scored by override-rate) is now wired — see [Self-improvement loop (sil)](#self-improvement-loop-sil) below ([sil/ui-ux-pro-max_loop.py](sil/ui-ux-pro-max_loop.py)). It remains ONE_CLICK / PROSE_RULE (never auto-applied); the lightweight append flow above still feeds it, since user corrections to design-system picks are the override signal the loop scores.

---

## Self-improvement loop (sil)

This skill is wired into the shared self-improving-loop kernel (`~/.claude/lib/self-improving-loop`) at the **heavyweight** tier (self-learning.md §2.3). The loop learns **which reasoning rules / style picks survive vs. get overridden** in persisted design systems (the Master + Overrides pattern `scripts/design_system.py persist=True` writes), and proposes adjusting the durable default for a rule whose generated field users keep editing away. It is the `propose() → execute() → measure()` adapter in [sil/ui-ux-pro-max_loop.py](sil/ui-ux-pro-max_loop.py); the kernel owns commit/decide/log/rollback.

- **Fitness signal:** override-rate — fraction of generated design-system fields the user **overrides** (edits in the page Overrides file) vs. keeps from the generated Master. **Lower is better** (better default selection → fewer overrides), so the loop runs `higher_is_better=False`. A candidate reasoning-rule edit is scored by re-computing the corpus override-rate with the candidate default applied vs. the current baseline, over a synthetic saved-project corpus (`sil/fixtures/project_*.json`).
- **propose():** if one reasoning rule's generated field is overridden in ≥ 50% of that rule's saved projects, emit a `Candidate` setting that field's default (`ui-reasoning.csv` cell) to the value users most often picked. `change_signature` = `uux-reasoning:<rule-id>`. `None` if no rule clears the threshold.
- **Gates** (both must pass): `schema_valid` (the edited rule keeps every column and its `Decision_Rules` JSON still parses) and `no_empty_field` (the new default is non-empty and no tracked generated field becomes blank). `metric` = projected corpus override-rate; `deferred=True` — the realized rate needs new real projects, so `confirm` measures it after the live window.
- **Ledger:** `sil/reasoning-ledger.jsonl` (the shared kernel schema). The kernel commits only to a loop-private repo (`~/.claude/cache/ui-ux-pro-max/loop-config`) and **never pushes** — and at the ONE_CLICK rung it never writes `ui-reasoning.csv` at all.
- **Artifact class:** `PROSE_RULE`. **Rung:** `ONE_CLICK`. The loop **proposes + scores + logs** one reasoning-rule edit per iteration; **a human clicks to apply** the surfaced proposal. It **NEVER auto-applies** — `rungs.may_auto_apply` returns False for PROSE_RULE at every rung, so a real iteration logs an `ASK` proposal row and stops.
- **Input:** the persisted Master + Overrides files across saved projects (the override signal). The fixtures under `sil/fixtures/` are synthetic stand-ins so the offline gate + projected metric are computable in-loop; real override-rate is realized later on projects persisted since a pending row's window.

**Run a dry-run iteration** (computes the projected override-rate + prints the proposal; touches NO real files, ledger, or repo):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/ui-ux-pro-max/sil/ui-ux-pro-max_loop.py propose --dry-run
```

A real (non-dry-run) `propose` logs an ONE_CLICK `ASK` row to the ledger and never edits `ui-reasoning.csv`; `confirm` resolves any pending experiment by realizing the override-rate on projects persisted since the window.

## Recommended next step

After generating or refactoring UI, run **impeccable** to gate against AI-slop and quality anti-patterns, then **ship** to deliver. For full brand-grade engagements this skill is invoked inside **design-agency** Phase 5.
