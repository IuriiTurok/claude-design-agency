---
name: impeccable
description: "Create distinctive, production-grade frontend interfaces that avoid generic \"AI slop\" aesthetics. Generates creative, polished code with intentional typography, color, layout, and motion. Use whenever the user asks to build or restyle a component, UI, page, screen, view, poster, dashboard, landing page, artifact, or app — anything involving HTML, CSS, JSX, Tailwind, or frontend — even if the user does not explicitly invoke a design skill, and whenever any other design skill needs project design context. Keywords: component, UI, page, poster, dashboard, landing page, frontend, CSS, \"looks generic\", \"looks like AI made it\". Call with 'craft' for shape-then-build, 'teach' for design-context setup, or 'extract' to pull reusable components and tokens into the design system."
version: 2.2.0
user-invocable: true
argument-hint: "[craft|teach|extract]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

<design-agency-binding>
**YOU ARE INSIDE THE DESIGN AGENCY.** Everything below in this skill and every skill that calls it as preparation (polish, audit, colorize, typeset, layout, animate, critique, distill, harden, optimize, delight, bolder, quieter, shape, clarify, adapt, overdrive) is subordinate to these rules. Where Impeccable's defaults conflict with these rules, these rules win.

**Required context resolution order (replaces Impeccable's default order):**
1. The active project's `style_directive.md` — or, for agency-own work, a `style_directive_*.md` from an `own_brand_folders` dir if present, else `{AGENCY_STATE}/style_directive_*.md`. This is the **binding** aesthetic contract: colors, typography, spacing, radii, shadow, motion. Read it fully before any skill action.
2. The active project's `brand_strategy.md` and `visual_philosophy.md` — intent, tone, the three Taste knobs (DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY).
3. `research_context.md` and the client brief — audience, use cases, industry constraints.
4. Fall back to Impeccable's `.impeccable.md` / `teach` flow ONLY if the above are absent (non-agency work inside the agency repo).

**Binding constraints — zero exceptions:**
- **Color:** Only hex/OKLCH values named in the style directive. `/colorize` and `/bolder` may propose tints/shades strictly within the directive family (surface ±2–3% lightness). Palette swaps are out of scope.
- **Typography:** Literal Google Font names from the directive, declared via `<link>` tag. Never CSS variables, never system fallbacks as primary, never Inter-as-default. `/typeset` may adjust weight/size/tracking within the directive scale; it may not swap font family.
- **Spacing / radius / shadow:** 8px base grid; 12/8/6/9999px radii; shadow levels from the directive. `/layout` works within these.
- **Motion:** Directive easing + duration only (Nocturne: 200ms `cubic-bezier(0.4, 0, 0.2, 1)` + spring; Atelier: same curve). GPU-only properties (`transform`, `opacity`). `prefers-reduced-motion` fallback required. `/animate` and `/overdrive` are clamped to this.
- **Zero agency bleed-through on client deliverables:** BANNED tokens — every font in `reserved_tokens.fonts` and every color in `reserved_tokens.colors` (from `python3 {AGENCY_ROOT}/execution/state_paths.py --brand`), plus grain overlays, drifting glow orbs, and any other agency signature. Allowed ONLY inside an `own_brand_folders` dir. In client project directories they are prohibited. When `reserved_tokens` is empty there is nothing to enforce here — skip the check.
- **Style Enforcer is upstream of Impeccable.** Impeccable skills produce advisory suggestions; the agency `style_enforcer.md` agent remains the zero-tolerance compliance gate. Any Impeccable suggestion that would fail Style Enforcer must be rejected at proposal time and logged to `polish_report_*.md` with the reason.
- **Visual QA Agent is downstream of taste_guardian.** Impeccable `/critique` does not replace Visual QA; it feeds it.

**Output convention:** every Impeccable skill invocation inside the agency writes a structured report to `<project>/polish_report_<deliverable>.md` (or `motion_audit.md` for `/animate`, `/overdrive`). The report lists: (a) directive tokens referenced, (b) suggestions made, (c) suggestions rejected (with reason), (d) before/after snippets.
</design-agency-binding>

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

## Contents
- [Context Gathering Protocol](#context-gathering-protocol)
- [Design Direction](#design-direction)
- [Frontend Aesthetics Guidelines](#frontend-aesthetics-guidelines) — Typography · Color · Layout · Visual Details · Motion · Interaction
- [The AI Slop Test](#the-ai-slop-test) — canonical ban list lives in [reference/ai-slop-bans.md](reference/ai-slop-bans.md)
- [Self-learning](#self-learning)
- [Self-improvement loop (sil)](#self-improvement-loop-sil) — heavyweight sil adapter; ONE_CLICK, never auto-applies
- [Implementation Principles](#implementation-principles)
- [Inputs / Outputs / Dependencies](#inputs--outputs--dependencies)
- [Modes](#craft-mode) — Craft · Teach · Extract

## Context Gathering Protocol

Design skills produce generic output without project context. You MUST have confirmed design context before doing any design work.

**Required context** (every design skill needs at minimum):
- **Target audience**: Who uses this product and in what context?
- **Use cases**: What jobs are they trying to get done?
- **Brand personality/tone**: How should the interface feel?

Individual skills may require additional context. Check the skill's preparation section for specifics.

**CRITICAL**: You cannot infer this context by reading the codebase. Code tells you what was built, not who it's for or what it should feel like. Only the creator can provide this context.

**Gathering order:**
1. **Check current instructions (instant)**: If your loaded instructions already contain a **Design Context** section, proceed immediately.
2. **Check .impeccable.md (fast)**: If not in instructions, read `.impeccable.md` from the project root. If it exists and contains the required context, proceed.
3. **Run impeccable teach (REQUIRED)**: If neither source has context, you MUST run /impeccable teach NOW before doing anything else. Do NOT skip this step. Do NOT attempt to infer context from the codebase instead.

---

## Design Direction

Commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work. The key is intentionality, not intensity.

Then implement working code that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

### Typography
→ *Consult [typography reference](reference/typography.md) for OpenType features, web font loading, and the deeper material on scales.*

Choose fonts that are beautiful, unique, and interesting. Pair a distinctive display font with a refined body font.

<typography_principles>
Always apply these — do not consult a reference, just do them. (These are the items the `<typography_rules>` block below does NOT cover.)

- Fluid (clamp) sizing is for headings on marketing/content pages; use fixed `rem` scales for app UIs and dashboards — no major design system uses fluid type in product UI.
- Line-height scales inversely with line length: narrow columns want tighter leading, wide columns want more. For light text on dark backgrounds, ADD 0.05-0.1 to your normal line-height — light type reads as lighter weight and needs more breathing room.
</typography_principles>

<font_selection_procedure>
DO THIS BEFORE TYPING ANY FONT NAME.

The model's natural failure mode is "I was told not to use Inter, so I will pick my next favorite font, which becomes the new monoculture." Avoid this by performing the following procedure on every project, in order:

Step 1. Read the brief once. Write down 3 concrete words for the brand voice (e.g., "warm and mechanical and opinionated", "calm and clinical and careful", "fast and dense and unimpressed", "handmade and a little weird"). NOT "modern" or "elegant" — those are dead categories.

Step 2. List the 3 fonts you would normally reach for given those words. Write them down. They are most likely from this list:

<reflex_fonts_to_reject>
Fraunces
Newsreader
Lora
Crimson
Crimson Pro
Crimson Text
Playfair Display
Cormorant
Cormorant Garamond
Syne
IBM Plex Mono
IBM Plex Sans
IBM Plex Serif
Space Mono
Space Grotesk
Inter
DM Sans
DM Serif Display
DM Serif Text
Outfit
Plus Jakarta Sans
Instrument Sans
Instrument Serif
</reflex_fonts_to_reject>

Reject every font that appears in the reflex_fonts_to_reject list. They are your training-data defaults and they create monoculture across projects.

Step 3. Browse a font catalog with the 3 brand words in mind. Sources: Google Fonts, Pangram Pangram, Future Fonts, Adobe Fonts, ABC Dinamo, Klim Type Foundry, Velvetyne. Look for something that fits the brand as a *physical object* — a museum exhibit caption, a hand-painted shop sign, a 1970s mainframe terminal manual, a fabric label on the inside of a coat, a children's book printed on cheap newsprint. Reject the first thing that "looks designy" — that's the trained reflex too. Keep looking.

Step 4. Cross-check the result. The right font for an "elegant" brief is NOT necessarily a serif. The right font for a "technical" brief is NOT necessarily a sans-serif. The right font for a "warm" brief is NOT Fraunces. If your final pick lines up with your reflex pattern, go back to Step 3.
</font_selection_procedure>

<typography_rules>
DO use a modular type scale with fluid sizing (clamp) on headings.
DO vary font weights and sizes to create clear visual hierarchy.
DO vary your font choices across projects. If you used a serif display font on the last project, look for a sans, monospace, or display face on this one.

DO NOT use overused fonts like Inter, Roboto, Arial, Open Sans, or system defaults — but also do not simply switch to your second-favorite. Every font in the reflex_fonts_to_reject list above is banned. Look further.
DO NOT use monospace typography as lazy shorthand for "technical/developer" vibes.
DO NOT put large icons with rounded corners above every heading. They rarely add value and make sites look templated.
DO NOT use only one font family for the entire page. Pair a distinctive display font with a refined body font.
DO NOT use a flat type hierarchy where sizes are too close together. Aim for at least a 1.25 ratio between steps.
DO NOT set long body passages in uppercase. Reserve all-caps for short labels and headings.
</typography_rules>

### Color & Theme
→ *Consult [color reference](reference/color-and-contrast.md) for the deeper material on contrast, accessibility, and palette construction.*

Commit to a cohesive palette. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.

<color_principles>
Always apply these — do not consult a reference, just do them. (These are the items the `<color_rules>` block below does NOT cover.)

- OKLCH is perceptually uniform: equal steps in lightness *look* equal, which HSL does not deliver. As you move toward white or black, REDUCE chroma — high chroma at extreme lightness looks garish. A light blue at 85% lightness wants ~0.08 chroma, not the 0.15 of your base color.
- When tinting neutrals, the hue must come from THIS brand, not a "warm = friendly" or "cool = tech" formula. Pick the brand's actual hue first, then tint everything toward it (a chroma of 0.005-0.01 is already perceptible).
- The 60-30-10 rule is about visual *weight*, not pixel count: 60% neutral/surface, 30% secondary text and borders, 10% accent. Accents work BECAUSE they're rare.
</color_principles>

<theme_selection>
Theme (light vs dark) should be DERIVED from audience and viewing context, not picked from a default. Read the brief and ask: when is this product used, by whom, in what physical setting?

- A perp DEX consumed during fast trading sessions → dark
- A hospital portal consumed by anxious patients on phones late at night → light
- A children's reading app → light
- A vintage motorcycle forum where users sit in their garage at 9pm → dark
- An observability dashboard for SREs in a dark office → dark
- A wedding planning checklist for couples on a Sunday morning → light
- A music player app for headphone listening at night → dark
- A food magazine homepage browsed during a coffee break → light

Do not default everything to light "to play it safe." Do not default everything to dark "to look cool." Both defaults are the lazy reflex. The correct theme is the one the actual user wants in their actual context.
</theme_selection>

<color_rules>
DO use modern CSS color functions (oklch, color-mix, light-dark) for perceptually uniform, maintainable palettes.
DO tint your neutrals toward your brand hue. Even a subtle hint creates subconscious cohesion.

DO NOT use gray text on colored backgrounds; it looks washed out. Use a shade of the background color instead.
DO NOT use pure black (#000) or pure white (#fff). Always tint; pure black/white never appears in nature.
DO NOT use the AI color palette: cyan-on-dark, purple-to-blue gradients, neon accents on dark backgrounds.
DO NOT use gradient text for impact — see <absolute_bans> below for the strict definition. Solid colors only for text.
DO NOT default to dark mode with glowing accents. It looks "cool" without requiring actual design decisions.
DO NOT default to light mode "to be safe" either. The point is to choose, not to retreat to a safe option.
</color_rules>

### Layout & Space
→ *Consult [spatial reference](reference/spatial-design.md) for the deeper material on grids, container queries, and optical adjustments.*

Create visual rhythm through varied spacing, not the same padding everywhere. Embrace asymmetry and unexpected compositions. Break the grid intentionally for emphasis.

<spatial_principles>
Always apply these — do not consult a reference, just do them. (These are the items the `<spatial_rules>` block below does NOT cover.)

- Use a 4pt spacing scale with semantic token names (`--space-sm`, `--space-md`), not pixel-named (`--spacing-8`). Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96. 8pt is too coarse — you'll often want 12px between two values.
- Use `gap` instead of margins for sibling spacing. It eliminates margin collapse and the cleanup hacks that come with it.
- Self-adjusting grid pattern: `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))` is the breakpoint-free responsive grid for card-style content.
- Container queries are for components, viewport queries are for page layout. A card in a sidebar should adapt to the sidebar's width, not the viewport's.
</spatial_principles>

<spatial_rules>
DO create visual rhythm through varied spacing: tight groupings, generous separations.
DO use fluid spacing with clamp() that breathes on larger screens.
DO use asymmetry and unexpected compositions; break the grid intentionally for emphasis.

DO NOT wrap everything in cards. Not everything needs a container.
DO NOT nest cards inside cards. Visual noise; flatten the hierarchy.
DO NOT use identical card grids (same-sized cards with icon + heading + text, repeated endlessly).
DO NOT use the hero metric layout template (big number, small label, supporting stats, gradient accent).
DO NOT center everything. Left-aligned text with asymmetric layouts feels more designed.
DO NOT use the same spacing everywhere. Without rhythm, layouts feel monotonous.
DO NOT let body text wrap beyond ~80 characters per line. Add a max-width like 65–75ch so the eye can track easily.
</spatial_rules>

### Visual Details

<absolute_bans>
These CSS patterns are NEVER acceptable. They are the most recognizable AI design tells. Match-and-refuse: if you find yourself about to write any of these, stop and rewrite the element with a different structure entirely.

BAN 1: Side-stripe borders on cards/list items/callouts/alerts
  - PATTERN: `border-left:` or `border-right:` with width greater than 1px
  - INCLUDES: hard-coded colors AND CSS variables
  - FORBIDDEN: `border-left: 3px solid red`, `border-left: 4px solid #ff0000`, `border-left: 4px solid var(--color-warning)`, `border-left: 5px solid oklch(...)`, etc.
  - WHY: this is the single most overused "design touch" in admin, dashboard, and medical UIs. It never looks intentional regardless of color, radius, opacity, or whether the variable name is "primary" or "warning" or "accent."
  - REWRITE: use a different element structure entirely. Do not just swap to box-shadow inset. Reach for full borders, background tints, leading numbers/icons, or no visual indicator at all.

BAN 2: Gradient text
  - PATTERN: `background-clip: text` (or `-webkit-background-clip: text`) combined with a gradient background
  - FORBIDDEN: any combination that makes text fill come from a `linear-gradient`, `radial-gradient`, or `conic-gradient`
  - WHY: gradient text is decorative rather than meaningful and is one of the top three AI design tells
  - REWRITE: use a single solid color for text. If you want emphasis, use weight or size, not gradient fill.
</absolute_bans>

DO: Use intentional, purposeful decorative elements that reinforce brand.
DO NOT: Use border-left or border-right greater than 1px as a colored accent stripe on cards, list items, callouts, or alerts. See <absolute_bans> above for the strict CSS pattern.
DO NOT: Use glassmorphism everywhere (blur effects, glass cards, glow borders used decoratively rather than purposefully).
DO NOT: Use sparklines as decoration. Tiny charts that look sophisticated but convey nothing meaningful.
DO NOT: Use rounded rectangles with generic drop shadows. Safe, forgettable, could be any AI output.
DO NOT: Use modals unless there's truly no better alternative. Modals are lazy.

### Motion
→ *Consult [motion reference](reference/motion-design.md) for timing, easing, and reduced motion.*

Focus on high-impact moments: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions.

**DO**: Use motion to convey state changes: entrances, exits, feedback
**DO**: Use exponential easing (ease-out-quart/quint/expo) for natural deceleration
**DO**: For height animations, use grid-template-rows transitions instead of animating height directly
**DON'T**: Animate layout properties (width, height, padding, margin). Use transform and opacity only
**DON'T**: Use bounce or elastic easing. They feel dated and tacky; real objects decelerate smoothly

### Interaction
→ *Consult [interaction reference](reference/interaction-design.md) for forms, focus, and loading patterns.*

Make interactions feel fast. Use optimistic UI: update immediately, sync later.

**DO**: Use progressive disclosure. Start simple, reveal sophistication through interaction (basic options first, advanced behind expandable sections; hover states that reveal secondary actions)
**DO**: Design empty states that teach the interface, not just say "nothing here"
**DO**: Make every interactive surface feel intentional and responsive
**DON'T**: Repeat the same information (redundant headers, intros that restate the heading)
**DON'T**: Make every button primary. Use ghost buttons, text links, secondary styles; hierarchy matters

### Responsive
→ *Consult [responsive reference](reference/responsive-design.md) for mobile-first, fluid design, and container queries.*

**DO**: Use container queries (@container) for component-level responsiveness
**DO**: Adapt the interface for different contexts, not just shrink it
**DON'T**: Hide critical functionality on mobile. Adapt the interface, don't amputate it

### UX Writing
→ *Consult [ux-writing reference](reference/ux-writing.md) for labels, errors, and empty states.*

**DO**: Make every word earn its place
**DON'T**: Repeat information users can already see

---

## The AI Slop Test

**Critical quality check**: If you showed this interface to someone and said "AI made this," would they believe you immediately? If yes, that's the problem.

A distinctive interface should make someone ask "how was this made?" not "which AI made this?"

Review the DON'T guidelines above. They are the fingerprints of AI-generated work from 2024-2025.

**Canonical ban list (single source of truth).** The complete, authoritative AI-slop ban list — General (provider/brand-agnostic) and Own Brand (brand-specific) — lives in [reference/ai-slop-bans.md](reference/ai-slop-bans.md). The `<absolute_bans>`, `<reflex_fonts_to_reject>`, and DON'T rules above are the always-loaded subset; the reference file is the consolidated canon that `taste-skill`, `design-agency`, and the Phase-5 `taste-guardian` reference instead of maintaining their own copies. When in doubt, that file is authoritative.

**Smoke eval (binary).** Given a generic "build me a card component" request with no Design Context, the produced CSS MUST NOT contain any of: `border-left` / `border-right` greater than 1px used as an accent stripe, `background-clip: text` combined with a gradient, or any font name from `<reflex_fonts_to_reject>`. PASS = none present; FAIL = any present. Baseline (the same model without this skill) is expected to FAIL on at least one — that is the measurable value the skill adds.

---

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/impeccable.md`  (preferred when inside a project)
2. `<this-skill-dir>/LESSONS.md`               (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: impeccable/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

When the new lesson is a *fresh AI-slop tell* not already in `<absolute_bans>`, the reflex-font list, or [reference/ai-slop-bans.md](reference/ai-slop-bans.md) — for example one flagged by a reviewer, `taste-skill`, or `polish` — phrase it as `pattern → why it reads as AI → prescribed rewrite`. A tell that recurs (seen ≥3×) graduates into the General section of `reference/ai-slop-bans.md` on the next refactor sweep, keeping the always-loaded body small while durable patterns harden.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "impeccable/<project>"`

> **Heavyweight tier (wired).** impeccable is the designated sil candidate for the anti-pattern-list loop (self-learning.md §2.2), now implemented in [sil/impeccable_loop.py](sil/impeccable_loop.py). See the [Self-improvement loop (sil)](#self-improvement-loop-sil) section below. The lightweight append flow above still feeds it: lessons and Bridge-D candidates are the loop's `propose()` input. All such edits are PROSE_RULE ≤ ONE_CLICK — never auto-applied.

---

## Self-improvement loop (sil)

This skill is wired into the shared self-improving-loop kernel (`~/.claude/lib/self-improving-loop`) at the **heavyweight** tier (self-learning.md §2.2). The loop **grows and prunes** the canonical AI-slop ban list (`reference/ai-slop-bans.md`) from observed violations, scoring each proposed edit against an offline fixture corpus. It is the `propose() → execute() → measure()` adapter in [sil/impeccable_loop.py](sil/impeccable_loop.py); the kernel owns commit/decide/log/rollback.

- **Fitness signal:** anti-pattern hit-rate — net violations caught on a fixed corpus of known-bad CSS fixtures (`sil/fixtures/bad_*.css`), with a hard **no-false-positive gate** on the known-good goldens (`sil/fixtures/good_*.css`). Higher is better. A candidate ban-list edit is scored by re-running the mechanical checker with the candidate pattern active vs. the current baseline.
- **Gates** (both must pass): `no_false_positive_on_goldens` (the goldens stay clean) and `catches_the_bad_fixture` (the candidate catches something the baseline misses). Synchronous — the fixture corpus makes the metric measurable in-loop (no live window needed).
- **Ledger:** `sil/antipattern-ledger.jsonl` (the shared kernel schema). The kernel commits only to a loop-private repo (`~/.claude/cache/impeccable/loop-config`) and **never pushes** — and at the ONE_CLICK rung it never writes the ban list at all.
- **Artifact class:** `PROSE_RULE`. **Rung:** `ONE_CLICK`. The loop **proposes + scores + logs** one ban-list add/prune per iteration; **a human clicks to apply** the surfaced proposal. It **NEVER auto-applies** — `rungs.may_auto_apply` returns False for PROSE_RULE at every rung, so a real iteration logs an `ASK` proposal row and stops.
- **Input:** recurring Bridge-D candidate records (`reference/ai-slop-candidates.jsonl`, fail-open if absent) plus the harvested `## Self-learning` lessons. A pattern recurring ≥ 2× that the checker does not yet enforce becomes a grow proposal.

**Run a dry-run iteration** (computes the metric + prints the proposal; touches NO real files, ledger, or repo):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/impeccable/sil/impeccable_loop.py propose --dry-run
# demo a concrete proposal against the bundled sample candidates:
python3 ${CLAUDE_PLUGIN_ROOT}/skills/impeccable/sil/impeccable_loop.py propose --dry-run \
  --candidates ${CLAUDE_PLUGIN_ROOT}/skills/impeccable/sil/fixtures/candidates.sample.jsonl
```

A real (non-dry-run) `propose` logs an ONE_CLICK `ASK` row to the ledger and never edits the ban list; `confirm` resolves any pending experiment with a deterministic fixture re-check.

---

## Implementation Principles

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices across generations.

Remember: Claude is capable of extraordinary creative work. Don't hold back. Show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

---

## Inputs / Outputs / Dependencies

**Inputs:** the user's prompt describing a UI component, page, or design task; optionally an existing `.impeccable.md` Design Context file at the project root; an optional mode argument (`craft` | `teach` | `extract`).

**Outputs:** production-grade frontend code (HTML/CSS/JS) with distinctive, non-AI-slop aesthetics; a `.impeccable.md` Design Context file (written in `teach` mode); extracted design tokens / reusable components (in `extract` mode).

**Upstream (who hands to impeccable):** `shape` (scopes the feature before `craft`); any design sub-skill that triggers `impeccable teach` when project context is missing. Via **Bridge D**, `design-agency`, `taste-guardian`, and `visual-qa` feed anti-slop candidates (see below).

**Downstream (who impeccable hands to):** the targeted design micro-skills it routes into — `typeset`, `colorize`, `layout`, `bolder`, `quieter`, `distill`, `polish`, `harden`, `animate`, `delight`, `overdrive`, `clarify`, `adapt`, `optimize` — plus `shape`, `ship`, `wrap-session`. All of these (and `taste-skill` + `design-agency`) inherit the canonical bans in [reference/ai-slop-bans.md](reference/ai-slop-bans.md).

**Bridge D — anti-slop single source of truth (fail-open consumer).** impeccable is the canon for the AI-slop ban list.
- **Intake:** `design-agency` Phase 7 (post-launch) and the QA agents `taste-guardian` / `visual-qa` (on a hard-gate rejection) append candidate anti-pattern records to `{AGENCY_STATE}/ai-slop-candidates.jsonl` (one JSON object per line: `{ts, source, engagement, tell, evidence, scope, status:"candidate"}`, `scope ∈ {general, own_brand}`). Producers only ever write `status:"candidate"`.
- **Curation:** the impeccable anti-pattern sil (heavyweight tier, see [Self-learning](#self-learning)) evaluates candidates and promotes survivors into [reference/ai-slop-bans.md](reference/ai-slop-bans.md) — General or Own-brand section per `scope`. Promotion is PROSE_RULE ≤ ONE_CLICK; never auto-applied.
- **Fail-open:** if `ai-slop-candidates.jsonl` is absent, behave exactly as today — the curated ban list is unaffected and design work proceeds normally. A candidate write never alters live behavior until promoted.

**Recommended next step.** After a `craft` build, route to the specific design micro-skill that matches the remaining gap (see the diagnosis router in [context-protocol.md](context-protocol.md)), then run the Phase-5 QA gate (`polish-inspector` / `style-enforcer` / `taste-guardian` / `visual-qa`), then `/ship` (or `/wrap-session` to hand off). When invoked by another design skill that lacked context, return control to that skill once `.impeccable.md` is written.

---

## Craft Mode

If this skill is invoked with the argument "craft" (e.g., `/impeccable craft [feature description]`), follow the [craft flow](reference/craft.md). Pass any additional arguments as the feature description.

---

## Teach Mode

If this skill is invoked with the argument "teach" (e.g., `/impeccable teach`), skip all design work above and instead run the teach flow below. This is a one-time setup that gathers design context for the project.

### Step 1: Explore the Codebase

Before asking questions, thoroughly scan the project to discover what you can:

- **README and docs**: Project purpose, target audience, any stated goals
- **Package.json / config files**: Tech stack, dependencies, existing design libraries
- **Existing components**: Current design patterns, spacing, typography in use
- **Brand assets**: Logos, favicons, color values already defined
- **Design tokens / CSS variables**: Existing color palettes, font stacks, spacing scales
- **Any style guides or brand documentation**

Note what you've learned and what remains unclear.

### Step 2: Ask UX-Focused Questions

STOP and call the AskUserQuestion tool to clarify. Focus only on what you couldn't infer from the codebase:

#### Users & Purpose
- Who uses this? What's their context when using it?
- What job are they trying to get done?
- What emotions should the interface evoke? (confidence, delight, calm, urgency, etc.)

#### Brand & Personality
- How would you describe the brand personality in 3 words?
- Any reference sites or apps that capture the right feel? What specifically about them?
- What should this explicitly NOT look like? Any anti-references?

#### Aesthetic Preferences
- Any strong preferences for visual direction? (minimal, bold, elegant, playful, technical, organic, etc.)
- Light mode, dark mode, or both?
- Any colors that must be used or avoided?

#### Accessibility & Inclusion
- Specific accessibility requirements? (WCAG level, known user needs)
- Considerations for reduced motion, color blindness, or other accommodations?

Skip questions where the answer is already clear from the codebase exploration.

### Step 3: Write Design Context

Synthesize your findings and the user's answers into a `## Design Context` section:

```markdown
## Design Context

### Users
[Who they are, their context, the job to be done]

### Brand Personality
[Voice, tone, 3-word personality, emotional goals]

### Aesthetic Direction
[Visual tone, references, anti-references, theme]

### Design Principles
[3-5 principles derived from the conversation that should guide all design decisions]
```

Write this section to `.impeccable.md` in the project root. If the file already exists, update the Design Context section in place.

Then STOP and call the AskUserQuestion tool to ask whether they'd also like the Design Context appended to CLAUDE.md. If yes, append or update the section there as well.

Confirm completion and summarize the key design principles that will now guide all future work.

---

## Extract Mode

If this skill is invoked with the argument "extract" (e.g., `/impeccable extract [target]`), follow the [extract flow](reference/extract.md). Pass any additional arguments as the extraction target.