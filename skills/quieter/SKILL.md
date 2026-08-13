---
name: quieter
description: Tones down visually aggressive or overstimulating designs, reducing intensity while preserving quality. Use when the user mentions too bold, too loud, overwhelming, aggressive, garish, or wants a calmer, more refined aesthetic.
version: 2.1.1
user-invocable: true
argument-hint: "[target]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

Reduce visual intensity in designs that are too bold, aggressive, or overstimulating, creating a more refined and approachable aesthetic without losing effectiveness.

## Boundary

- **Use `quieter` when** the problem is *too much intensity* — the right elements are present but they shout (over-saturated color, extreme contrast, excess motion, heavy weights). Quieter **turns down** what stays (changes the styling, not the inventory). `quieter` is the **inverse of `bolder`** on the intensity axis (loud↔calm).
- **Use `distill` when** the problem is *too much stuff* — clutter, redundant elements, feature creep. Distill **removes elements** (changes the content/structure), not their intensity.
- A design can be both loud and cluttered → run `distill` first (remove), then `quieter` (tone down).

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol. If no design context exists, run `/impeccable teach` first.

---

## Assess Current State

Analyze what makes the design feel too intense:

1. **Identify intensity sources**:
   - **Color saturation**: Overly bright or saturated colors
   - **Contrast extremes**: Too much high-contrast juxtaposition
   - **Visual weight**: Too many bold, heavy elements competing
   - **Animation excess**: Too much motion or overly dramatic effects
   - **Complexity**: Too many visual elements, patterns, or decorations
   - **Scale**: Everything is large and loud with no hierarchy

2. **Understand the context**:
   - What's the purpose? (Marketing vs tool vs reading experience)
   - Who's the audience? (Some contexts need energy)
   - What's working? (Don't throw away good ideas)
   - What's the core message? (Preserve what matters)

If any of these are unclear from the codebase, STOP and call the AskUserQuestion tool to clarify.

**CRITICAL**: "Quieter" doesn't mean boring or generic. It means refined, sophisticated, and easier on the eyes. Think luxury, not laziness.

## Plan Refinement

Create a strategy to reduce intensity while maintaining impact:

- **Color approach**: Desaturate or shift to more sophisticated tones?
- **Hierarchy approach**: Which elements should stay bold (very few), which should recede?
- **Simplification approach**: What can be removed entirely?
- **Sophistication approach**: How can we signal quality through restraint?

**IMPORTANT**: Great quiet design is harder than great bold design. Subtlety requires precision.

## Refine the Design

Systematically reduce intensity across these dimensions:

### Color Refinement
- **Reduce saturation**: Shift from fully saturated to 70-85% saturation
- **Soften palette**: Replace bright colors with muted, sophisticated tones
- **Reduce color variety**: Use fewer colors more thoughtfully
- **Neutral dominance**: Let neutrals do more work, use color as accent (10% rule)
- **Gentler contrasts**: High contrast only where it matters most
- **Tinted grays**: Use warm or cool tinted grays instead of pure gray—adds sophistication without loudness
- **Never gray on color**: If you have gray text on a colored background, use a darker shade of that color or transparency instead

### Visual Weight Reduction
- **Typography**: Reduce font weights (900 → 600, 700 → 500), decrease sizes where appropriate
- **Hierarchy through subtlety**: Use weight, size, and space instead of color and boldness
- **White space**: Increase breathing room, reduce density
- **Borders & lines**: Reduce thickness, decrease opacity, or remove entirely

### Simplification
- **Remove decorative elements**: Gradients, shadows, patterns, textures that don't serve purpose
- **Simplify shapes**: Reduce border radius extremes, simplify custom shapes
- **Reduce layering**: Flatten visual hierarchy where possible
- **Clean up effects**: Reduce or remove blur effects, glows, multiple shadows

### Motion Reduction
- **Reduce animation intensity**: Shorter distances (10-20px instead of 40px), gentler easing
- **Remove decorative animations**: Keep functional motion, remove flourishes
- **Subtle micro-interactions**: Replace dramatic effects with gentle feedback
- **Refined easing**: Use ease-out-quart for smooth, understated motion—never bounce or elastic
- **Remove animations entirely** if they're not serving a clear purpose

### Composition Refinement
- **Reduce scale jumps**: Smaller contrast between sizes creates calmer feeling
- **Align to grid**: Bring rogue elements back into systematic alignment
- **Even out spacing**: Replace extreme spacing variations with consistent rhythm

**NEVER**:
- Make everything the same size/weight (hierarchy still matters)
- Remove all color (quiet ≠ grayscale)
- Eliminate all personality (maintain character through refinement)
- Sacrifice usability for aesthetics (functional elements still need clear affordances)
- Make everything small and light (some anchors needed)

## Verify Quality

Ensure refinement maintains quality:

- **Still functional**: Can users still accomplish tasks easily?
- **Still distinctive**: Does it have character, or is it generic now?
- **Better reading**: Is text easier to read for extended periods?
- **Sophistication**: Does it feel more refined and premium?

Remember: Quiet design is confident design. It doesn't need to shout. Less is more, but less is also harder. Refine with precision and maintain intentionality.

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/quieter.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/quieter.md`  (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: quieter/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "quieter/<project>"`

## Recommended next step

Next: `/polish` — verify the refinement holds together.