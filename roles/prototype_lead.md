# Prototype Lead

**Role:** Owns product-prototype engagements — interactive app replicas, multi-screen clickable prototypes, prototype version iterations, and the developer handoff docs that follow. Prototypes are NOT one of the 4 mandatory brand deliverables; they get their own lighter protocol so they stop running ad-hoc.

**Why this skill exists:** 18 prototype sessions on one product across 2 days (a profile screen, v3 → v31 → v6) ran with no owning skill: 0.7+ corrections per user turn, a sticky-header bug that regressed after being fixed, responsive breakpoints discovered mid-session through trial and error, and a 200-line handoff doc written ad-hoc by the master agent.

## When to invoke

Any request to: replicate an app with client branding, build an interactive prototype, iterate a prototype version, or prepare a prototype for external developers (Lovable, agency dev partner).

## Protocol

### 1. Classification (3 questions, before any code)

- **Purpose:** stakeholder demo, developer handoff, or production-intent?
- **Lifespan:** throwaway, archived reference, or living artifact?
- **Success metric:** brand coherence, code reusability, or flow completeness?

The answers set the QA depth and whether a handoff doc is owed at the end.

### 2. Design brief BEFORE code

Write `<project>/ui/prototypes/<name>/design_brief.md`:

- **Component inventory** — every visual component and its states (default/hover/selected/disabled/empty).
- **Responsive breakpoint table** — exact breakpoints and what changes at each, decided upfront. Breakpoints are never discovered mid-session by asking the user.
- **Token constraints** — colors, typography, spacing pulled from the project's `style_directive.md` and `ui/design_system.html`. Literal font names with real font loading.
- **Interaction spec** — z-order rules, sticky behavior, menu/overlay layering, transition durations from the directive's motion spec.

For substantive new prototypes, get user confirmation on the brief before building. For small iterations, update the brief as part of the change.

### 3. Build

Reuse design-system tokens and component patterns from `ui/design_system.html` — a prototype that re-invents the card component is a defect. shadcn patterns over raw divs.

### 4. Prototype QA — before EVERY user review

Lightweight loop, not the full Phase 5 pipeline:

1. **Token compliance** — colors and fonts trace to the directive (style_enforcer scope, applied to the touched file).
2. **Motion spec adherence** — durations/easings match the directive.
3. **Browser verify** — page loads, zero console errors, screenshots at 1440px and 390px.
4. **Regression check** — maintain `<name>/prototype_qa_log.md`: a list of every issue the user reported and its fix. Re-verify the full list each round before review. This is what prevents "the bug is back."

### 5. Versioning

A new version directory (v3 → v4) requires a one-line stated reason in its `design_brief.md`. Every version carries the complete file set forward — no unequal variants (anti-pattern #10). Mark superseded versions in the brief header.

### 6. Developer handoff

This skill owns `<project>/handoff_<target>.md` (e.g., `handoff_lovable.md`): design tokens, motion spec, component patterns, asset inventory, known issues. Coordinate with `design_system_expert` (which owns `design_system/developer_handoff.md`) — link, don't duplicate.

## What this skill does NOT do

- Brand deliverables (`ui/landing_page.html` etc.) — those run the full Phase 5 pipeline.
- Backend or real data integration — prototypes are explicitly fake-data.
- Visual QA grading of brand quality — if a prototype is promoted to a client-facing deliverable, it enters the standard Phase 5 pipeline first.
