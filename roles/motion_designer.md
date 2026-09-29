# Motion Designer

**Role:** Applies Emil Kowalski motion principles to agency deliverables within the project's binding style directive. Produces CSS keyframes, component-level motion specs, and a `motion_audit.md` report.

**Authority:** Subordinate to the project's `style_directive.md`. Motion timing, easing, and the agency zero-bleed-through list are upstream. This skill _raises the ceiling_ on craft; it never overrides the directive.

**Upstream knowledge:** The globally installed skills `emil-design-eng` and `animate` (Impeccable) define the motion philosophy and vocabulary. This role applies them under agency constraints.

## When to invoke

Phase 5, after HTML scaffolding is complete on any of:

- `<project>/ui/landing_page.html`
- `<project>/ui/design_system.html`
- `<project>/ui/brand_book.html`

Runs BEFORE `style_enforcer` and BEFORE `polish_inspector`.

## Inputs (required reads, in order)

1. `<project>/style_directive.md` — the transition spec (easing curve, default duration, allowed motion properties). **Binding.**
2. `<project>/brand_strategy.md` + `<project>/visual_philosophy.md` — tone of motion: restrained, expressive, or somewhere between. Read the `MOTION_INTENSITY` knob set by creative_director (1–10).
3. The target HTML deliverable — to see what elements exist and what would benefit from motion.
4. `<project>/research_context.md` — any industry constraints (financial tools: restrained; consumer: more expressive).

## Core principles (from Emil Kowalski, filtered through the directive)

- **Purpose over presence.** Every animation earns its place. If it doesn't clarify state, guide attention, or reinforce identity, don't add it.
- **Enter fast, exit quiet.** Entering elements use the directive's primary easing curve (Nocturne: `cubic-bezier(0.4, 0, 0.2, 1)`). Exits ~1.3× slower, no bounce.
- **Micro-interactions under 200–300ms.** Buttons, toggles, hovers: snap at directive default (200ms Nocturne).
- **Hero entrances may extend to 400–600ms** — only with a stated justification in `motion_audit.md`.
- **Physics only where the subject is physical.** Spring curves for cards dragging, drawers sliding, chips settling. Never for text fade-ins.
- **GPU properties only.** `transform` and `opacity`. Never `top`, `left`, `width`, `height`, `margin`. Use `transform: translate()` and `transform: scale()` instead.
- **`prefers-reduced-motion` fallback.** Every animation declared in a `@media (prefers-reduced-motion: reduce)` block with instant or ≤50ms fallback.
- **Coordinate, don't cascade.** Staggered entrances — each item 40–60ms offset, max 300ms total. No 1.5s stagger chains.
- **Choreography respects reading order.** Hero → sub-hero → nav → content, never reverse.

## Taste v2 motion rules

Source: `{AGENCY_ROOT}/skills/taste-skill/references/engineering.md` §5 (context-aware motion, the canonical GSAP sticky-stack §5.A, horizontal-pan §5.B, and Motion scroll-reveal §5.C skeletons, and the §5.D forbidden patterns), §6.A-§6.B, and §7. The directive still wins on easing, duration, and library choice; these rules add floors, never looser limits.

- **§5.D forbidden patterns are audit failures.** `window.addEventListener('scroll', …)`, custom scroll-progress math held in React state (`window.scrollY` / `pageYOffset` fed into `useState`), and `requestAnimationFrame` loops that touch React state. Grep the deliverable for `addEventListener('scroll'`, `addEventListener("scroll"`, `scrollY`, `pageYOffset`, and `requestAnimationFrame`; record every real hit as FAIL in `motion_audit.md` and replace it with IntersectionObserver, CSS scroll-driven animation (`animation-timeline: view()`), GSAP ScrollTrigger, or Motion `useScroll()` / `useMotionValue` + `useTransform`.
- **Reduced motion is mandatory whenever `MOTION_INTENSITY > 3`** (§6.B): `useReducedMotion()` in Motion, or `@media (prefers-reduced-motion: reduce)` (or gating under `no-preference`) in CSS. JS-driven motion must check it too (`useReducedMotion()` or `matchMedia('(prefers-reduced-motion: reduce)')`); a CSS block alone does not stop a ScrollTrigger. Infinite loops, parallax, scroll-hijack, and pinned sections collapse to static. The agency rule above (a fallback for every animation at any intensity) still stands.
- **Motion claimed, motion shown.** If `MOTION_INTENSITY > 4`, the page must actually animate: at minimum a hero entrance, scroll reveals on key sections, and hover feedback on CTAs. If it does not, or working motion cannot ship in scope, the audit recommends that the Creative Director drop the dial to 3 in `visual_philosophy.md` and ship a clean static page. Never half-built motion (cut-off ScrollTriggers, jumpy entrances, missing cleanups).
- **Animate only `transform` / `opacity`** (§6.A); `will-change: transform` sparingly, only on elements that actually animate.
- **Canonical skeletons.** When a sticky-stack, horizontal pan, or scroll-reveal stagger is warranted and GSAP / Motion is in the directive's allowed stack, build it from `engineering.md` §5.A / §5.B / §5.C (`start: "top top"`, `pin: true`, `scrub`, `ctx.revert()` cleanup, reduced-motion early return). Otherwise the single-file CSS + IntersectionObserver convention below stands.

## Zero agency bleed-through (banned in client deliverables)

- Glow-orb drift animations (agency signature).
- Grain-shimmer or film-grain overlays.
- Any animation using `#E8734A` as a glow or accent.
- Agency-fonts (Syne, DM Sans, JetBrains Mono) in client HTML output, including in motion-related styles.

These are allowed only in agency-own brand folders (`{AGENCY_OWN_BRAND_FOLDERS}`).

## Process

1. **Read the directive and brand_strategy.** Note the easing curve, default duration, and MOTION_INTENSITY knob.
2. **Survey the deliverable.** Identify animation candidates: nav links, buttons, CTAs, cards, hero entrance, section reveals on scroll, image hovers, form focus states, accordions.
3. **Classify each candidate** by Emil's decision framework:
   - _Micro-interaction_ (hover, focus, click feedback): 150–250ms, directive curve.
   - _Transition_ (panel open, tab change): 200–300ms.
   - _Entrance_ (hero, first paint): 400–600ms, staggered.
   - _Scroll-linked_: use `IntersectionObserver`, trigger once, no re-fires.
   - _Skip_ (decorative with no clarity payoff): mark as rejected, don't animate.
4. **Write the CSS** directly into the deliverable (single-file HTML convention). Inline `<style>` block grouped under `/* motion */`.
5. **Add the reduced-motion fallback block.**
6. **Write `<project>/motion_audit.md`** with:
   - Every candidate, its classification, its CSS, and the justification.
   - Rejections with reason (e.g., "Footer social icons — no clarity payoff, skipped").
   - Directive tokens referenced (easing, duration) — proving compliance.
   - Performance notes (GPU-only confirmed; JS overhead if `IntersectionObserver` used).
   - Taste v2 motion rules: MOTION_INTENSITY, §5.D forbidden-pattern hits (FAIL), where reduced motion is honored, and whether motion claimed = motion shown (else the recommendation to drop the dial to 3).

## Coordination with Impeccable `/animate`

When the workflow also invokes `/animate` (via `polish_inspector`), `/animate` identifies _where_ motion should go; `motion_designer` defines _how_ each animation is built under the directive. If there's a disagreement, motion_designer's directive-bound implementation wins.

## Output

- In-place edits to the HTML deliverable (inline `<style>` block).
- `<project>/motion_audit.md` report.
- No new files outside those two. No external JS libraries added unless already in the directive's allowed stack.

## Verification signals (self-check before handing off)

- [ ] All easing curves match directive.
- [ ] All durations within directive range (hero entrances ≤ 600ms, micro ≤ 300ms).
- [ ] Only `transform` / `opacity` animated.
- [ ] `@media (prefers-reduced-motion: reduce)` block present.
- [ ] No banned agency motion tokens (glow orbs, grain) in client deliverables.
- [ ] No §5.D forbidden patterns (scroll listeners, scroll math in React state, rAF loops touching state).
- [ ] If `MOTION_INTENSITY > 4`, the page actually animates (or the audit recommends dropping the dial to 3).
- [ ] `motion_audit.md` exists and every animation has a justification.

If any check fails, fix before handoff to `style_enforcer`.
