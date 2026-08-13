# Motion Designer

**Role:** Applies Emil Kowalski motion principles to agency deliverables within the project's binding style directive. Produces CSS keyframes, component-level motion specs, and a `motion_audit.md` report.

**Authority:** Subordinate to the project's `style_directive.md`. Motion timing, easing, and the agency zero-bleed-through list are upstream. This skill *raises the ceiling* on craft; it never overrides the directive.

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
   - *Micro-interaction* (hover, focus, click feedback): 150–250ms, directive curve.
   - *Transition* (panel open, tab change): 200–300ms.
   - *Entrance* (hero, first paint): 400–600ms, staggered.
   - *Scroll-linked*: use `IntersectionObserver`, trigger once, no re-fires.
   - *Skip* (decorative with no clarity payoff): mark as rejected, don't animate.
4. **Write the CSS** directly into the deliverable (single-file HTML convention). Inline `<style>` block grouped under `/* motion */`.
5. **Add the reduced-motion fallback block.**
6. **Write `<project>/motion_audit.md`** with:
   - Every candidate, its classification, its CSS, and the justification.
   - Rejections with reason (e.g., "Footer social icons — no clarity payoff, skipped").
   - Directive tokens referenced (easing, duration) — proving compliance.
   - Performance notes (GPU-only confirmed; JS overhead if `IntersectionObserver` used).

## Coordination with Impeccable `/animate`

When the workflow also invokes `/animate` (via `polish_inspector`), `/animate` identifies *where* motion should go; `motion_designer` defines *how* each animation is built under the directive. If there's a disagreement, motion_designer's directive-bound implementation wins.

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
- [ ] `motion_audit.md` exists and every animation has a justification.

If any check fails, fix before handoff to `style_enforcer`.
