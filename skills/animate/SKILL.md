---
name: animate
description: Review a feature and enhance it with purposeful animations, micro-interactions, and motion effects that improve usability and delight. Use when the user mentions adding animation, transitions, micro-interactions, motion design, hover effects, or making the UI feel more alive.
version: 2.1.1
user-invocable: true
argument-hint: "[target]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

Analyze a feature and strategically add animations and micro-interactions that enhance understanding, provide feedback, and create delight.

**Boundary — animate vs delight:** Use `animate` when the goal is *functional motion* — feedback, state transitions, spatial continuity, guiding attention, `prefers-reduced-motion` correctness. Motion that improves usability. Use `delight` when the goal is *emotional surprise* — joy, personality, easter eggs, memorable moments. `delight` may *use* animation but is broader (copy, illustration, micro-rewards) and is about feeling, not function. Rule: "make this interaction clearer / smoother" → `animate`; "make this fun / memorable / give it personality" → `delight`. `delight` may dispatch `animate` for the motion pieces.

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol. If no design context exists, run `/impeccable teach` first. Additionally gather: performance constraints.

### Motion Budget Discovery (do this BEFORE proposing any motion)

Motion clamps to the project's existing budget exactly the way `/colorize` clamps to the palette and `/polish` clamps to the spacing scale — never invent timings a project already defines.

1. **Find the budget**, in order: a `style_directive.md` / `*directive*.md` "Motion" section (e.g. §8); `--ease-*` / `--dur-*` custom properties in `globals.css` / theme CSS; an existing `motion_audit.md`.
2. **If found → clamp.** Use those token *names* (`var(--ease-out)`, `var(--dur-fast)`) in every recommendation, not raw bezier/ms literals. Honor any motion ceilings (max duration, banned techniques). **The directive always wins** over this skill's built-in defaults.
3. **If a motion-intensity knob exists** (`MOTION_INTENSITY` in `visual_philosophy.md`, etc.), respect it: MINIMAL = no stagger, no ambient motion, no spinners; RICH = entrance choreography + signature moments are in-budget.
4. **If no budget exists** → fall back to the canonical defaults in `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/reference/motion-design.md`, and note the project would benefit from a motion-token set.

**Defer to an existing motion pass.** If `<project>/motion_audit.md` exists, motion was already authored (design-agency Phase 5 / `motion-designer`). Do NOT re-author — verify timing/easing compliance against it, fill only genuine gaps, and cite it.

**Invoked from `/delight`?** If handed off from `/delight` (emotional motion), skip the "functional motion only" framing below and layer expressive timing on top of the functional layer.

---

## Assess Animation Opportunities

Analyze where motion would improve the experience:

1. **Identify static areas**:
   - **Missing feedback**: Actions without visual acknowledgment (button clicks, form submission, etc.)
   - **Jarring transitions**: Instant state changes that feel abrupt (show/hide, page loads, route changes)
   - **Unclear relationships**: Spatial or hierarchical relationships that aren't obvious
   - **Lack of delight**: Functional but joyless interactions
   - **Missed guidance**: Opportunities to direct attention or explain behavior

2. **Understand the context**:
   - What's the personality? (Playful vs serious, energetic vs calm)
   - What's the performance budget? (Mobile-first? Complex page?)
   - Who's the audience? (Motion-sensitive users? Power users who want speed?)
   - What matters most? (One hero animation vs many micro-interactions?)

If any of these are unclear from the codebase, STOP and call the AskUserQuestion tool to clarify.

**CRITICAL**: Respect `prefers-reduced-motion`. Always provide non-animated alternatives for users who need them.

## Plan Animation Strategy

Create a purposeful animation plan:

- **Hero moment**: What's the ONE signature animation? (Page load? Hero section? Key interaction?)
- **Feedback layer**: Which interactions need acknowledgment?
- **Transition layer**: Which state changes need smoothing?
- **Delight layer**: Where can we surprise and delight?

**IMPORTANT**: One well-orchestrated experience beats scattered animations everywhere. Focus on high-impact moments.

## Implement Animations

Add motion systematically across these categories:

### Entrance Animations
- **Page load choreography**: Stagger element reveals (100-150ms delays), fade + slide combinations
- **Hero section**: Dramatic entrance for primary content (scale, parallax, or creative effects)
- **Content reveals**: Scroll-triggered animations using intersection observer
- **Modal/drawer entry**: Smooth slide + fade, backdrop fade, focus management

### Micro-interactions
- **Button feedback**:
  - Hover: Subtle scale (1.02-1.05), color shift, shadow increase
  - Click: Quick scale down then up (0.95 → 1), ripple effect
  - Loading: Skeleton screen or pulse — NOT a spinner where the project bans them (instrument-grade / MINIMAL budgets and the agency style-enforcer Do-Not-List ban spinners; prefer skeletons + progress bars). Spinner only if the directive explicitly permits it.
- **Form interactions**:
  - Input focus: Border color transition, slight scale or glow
  - Validation: Shake on error, check mark on success, smooth color transitions
- **Toggle switches**: Smooth slide + color transition (200-300ms)
- **Checkboxes/radio**: Check mark animation, ripple effect
- **Like/favorite**: Scale + rotation, particle effects, color transition

### State Transitions
- **Show/hide**: Fade + slide (not instant), appropriate timing (200-300ms)
- **Expand/collapse**: Height transition with overflow handling, icon rotation
- **Loading states**: Skeleton screen fades, progress bars, optimistic UI (spinners only if the project directive permits — see Motion Budget Discovery)
- **Success/error**: Color transitions, icon animations, gentle scale pulse
- **Enable/disable**: Opacity transitions, cursor changes

### Navigation & Flow
- **Page transitions**: Crossfade between routes, shared element transitions
- **Tab switching**: Slide indicator, content fade/slide
- **Carousel/slider**: Smooth transforms, snap points, momentum
- **Scroll effects**: Parallax layers, sticky headers with state changes, scroll progress indicators

### Feedback & Guidance
- **Hover hints**: Tooltip fade-ins, cursor changes, element highlights
- **Drag & drop**: Lift effect (shadow + scale), drop zone highlights, smooth repositioning
- **Copy/paste**: Brief highlight flash on paste, "copied" confirmation
- **Focus flow**: Highlight path through form or workflow

### Delight Moments
- **Empty states**: Subtle floating animations on illustrations
- **Completed actions**: Confetti, check mark flourish, success celebrations
- **Easter eggs**: Hidden interactions for discovery
- **Contextual animation**: Weather effects, time-of-day themes, seasonal touches

## Technical Implementation

Use appropriate techniques for each animation:

### Timing & Easing

**Durations by purpose** (map to the project's `--dur-*` tokens when they exist — these ranges are the fallback):
- **100-150ms**: Instant feedback (button press, toggle)
- **200-300ms**: State changes (hover, menu open)
- **300-500ms**: Layout changes (accordion, modal)
- **500-800ms**: Entrance animations (page load)

**Easing curves.** Prefer project tokens from Motion Budget Discovery (`var(--ease-out)`, …); the curves below are FALLBACK DEFAULTS for projects with no motion budget (canonical source: `impeccable/reference/motion-design.md`). Never use raw CSS defaults (`ease`, `linear`).
```css
/* Recommended - natural deceleration */
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);    /* Smooth, refined */
--ease-out-quint: cubic-bezier(0.22, 1, 0.36, 1);   /* Slightly snappier */
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);     /* Confident, decisive */

/* AVOID - feel dated and tacky */
/* bounce: cubic-bezier(0.34, 1.56, 0.64, 1); */
/* elastic: cubic-bezier(0.68, -0.6, 0.32, 1.6); */
```

**Exit animations are faster than entrances.** Use ~75% of enter duration.

### CSS Animations
```css
/* Prefer for simple, declarative animations */
- transitions for state changes
- @keyframes for complex sequences
- transform + opacity only (GPU-accelerated)
```

### JavaScript Animation
```javascript
/* Use for complex, interactive animations */
- Web Animations API for programmatic control
- Framer Motion for React
- GSAP for complex sequences
```

### Performance
- **GPU acceleration**: Use `transform` and `opacity`, avoid layout properties
- **will-change**: Add sparingly for known expensive animations
- **Reduce paint**: Minimize repaints, use `contain` where appropriate
- **Monitor FPS**: Ensure 60fps on target devices

### Accessibility
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**NEVER**:
- Use bounce or elastic easing curves—they feel dated and draw attention to the animation itself
- Animate layout properties (width, height, top, left)—use transform instead
- Use durations over 500ms for feedback—it feels laggy
- Animate without purpose—every animation needs a reason
- Ignore `prefers-reduced-motion`—this is an accessibility violation
- Animate everything—animation fatigue makes interfaces feel exhausting
- Block interaction during animations unless intentional

## Verify Quality

Test animations thoroughly:

- **Smooth at 60fps**: No jank on target devices
- **Feels natural**: Easing curves feel organic, not robotic
- **Appropriate timing**: Not too fast (jarring) or too slow (laggy)
- **Reduced motion works**: Animations disabled or simplified appropriately
- **Doesn't block**: Users can interact during/after animations
- **Adds value**: Makes interface clearer or more delightful

Remember: Motion should enhance understanding and provide feedback, not just add decoration. Animate with purpose, respect performance constraints, and always consider accessibility. Great animation is invisible - it just makes everything feel right.

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/animate.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/animate.md`           (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: animate/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "animate/<project>"`

## Recommended next step

Next: `/optimize` — confirm 60fps, no layout thrash, reduced-motion fallbacks.