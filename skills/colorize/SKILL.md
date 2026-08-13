---
name: colorize
description: Add strategic color to features that are too monochromatic or lack visual interest, making interfaces more engaging and expressive. Use when the user mentions the design looking gray, dull, lacking warmth, needing more color, or wanting a more vibrant or expressive palette.
version: 2.1.1
user-invocable: true
argument-hint: "[target]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

Strategically introduce color to designs that are too monochromatic, gray, or lacking in visual warmth and personality.

**Boundary — `colorize` vs `bolder`:** Use `colorize` when the problem is *specifically the palette* — the design is grayscale/monochrome/dull and needs strategic, meaningful color. `colorize` touches only color; it does not restructure hierarchy or type. Use `bolder` when the problem is *overall timidity* — generic fonts, flat hierarchy, no drama, no personality — which works across type, scale, contrast, layout, and color together. `bolder` may call `colorize` as one of its moves. Rule: color-only → `colorize`; everything-feels-safe → `bolder`.

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol. If no design context exists, run `/impeccable teach` first. Additionally gather: existing brand colors.

---

## Assess Color Opportunity

Analyze the current state and identify opportunities:

1. **Understand current state**:
   - **Color absence**: Pure grayscale? Limited neutrals? One timid accent?
   - **Missed opportunities**: Where could color add meaning, hierarchy, or delight?
   - **Context**: What's appropriate for this domain and audience?
   - **Brand**: Are there existing brand colors we should use?

2. **Identify where color adds value**:
   - **Semantic meaning**: Success (green), error (red), warning (yellow/orange), info (blue)
   - **Hierarchy**: Drawing attention to important elements
   - **Categorization**: Different sections, types, or states
   - **Emotional tone**: Warmth, energy, trust, creativity
   - **Wayfinding**: Helping users navigate and understand structure
   - **Delight**: Moments of visual interest and personality

If any of these are unclear from the codebase, STOP and call the AskUserQuestion tool to clarify.

**CRITICAL**: More color ≠ better. Strategic color beats rainbow vomit every time. Every color should have a purpose.

## Plan Color Strategy

Create a purposeful color introduction plan:

- **Color palette**: What colors match the brand/context? (Choose 2-4 colors max beyond neutrals)
- **Dominant color**: Which color owns 60% of colored elements?
- **Accent colors**: Which colors provide contrast and highlights? (30% and 10%)
- **Application strategy**: Where does each color appear and why?

**IMPORTANT**: Color should enhance hierarchy and meaning, not create chaos. Less is more when it matters more.

## Introduce Color Strategically

Add color systematically across these dimensions:

### Semantic Color
- **State indicators**:
  - Success: Green tones (emerald, forest, mint)
  - Error: Red/pink tones (rose, crimson, coral)
  - Warning: Orange/amber tones
  - Info: Blue tones (sky, ocean, indigo)
  - Neutral: Gray/slate for inactive states

- **Status badges**: Colored backgrounds or borders for states (active, pending, completed, etc.)
- **Progress indicators**: Colored bars, rings, or charts showing completion or health

### Accent Color Application
- **Primary actions**: Color the most important buttons/CTAs
- **Links**: Add color to clickable text (maintain accessibility)
- **Icons**: Colorize key icons for recognition and personality
- **Headers/titles**: Add color to section headers or key labels
- **Hover states**: Introduce color on interaction

### Background & Surfaces
- **Tinted backgrounds**: Replace pure gray (`#f5f5f5`) with warm neutrals (`oklch(97% 0.01 60)`) or cool tints (`oklch(97% 0.01 250)`)
- **Colored sections**: Use subtle background colors to separate areas
- **Gradient backgrounds**: Add depth with subtle, intentional gradients (not generic purple-blue)
- **Cards & surfaces**: Tint cards or surfaces slightly for warmth

**Use OKLCH for color**: It's perceptually uniform, meaning equal steps in lightness *look* equal. Great for generating harmonious scales.

### Data Visualization
- **Charts & graphs**: Use color to encode categories or values
- **Heatmaps**: Color intensity shows density or importance
- **Comparison**: Color coding for different datasets or timeframes

### Borders & Accents
- **Accent borders**: Add colored left/top borders to cards or sections
- **Underlines**: Color underlines for emphasis or active states
- **Dividers**: Subtle colored dividers instead of gray lines
- **Focus rings**: Colored focus indicators matching brand

### Typography Color
- **Colored headings**: Use brand colors for section headings (maintain contrast)
- **Highlight text**: Color for emphasis or categories
- **Labels & tags**: Small colored labels for metadata or categories

### Decorative Elements
- **Illustrations**: Add colored illustrations or icons
- **Shapes**: Geometric shapes in brand colors as background elements
- **Gradients**: Colorful gradient overlays or mesh backgrounds
- **Blobs/organic shapes**: Soft colored shapes for visual interest

## Balance & Refinement

Ensure color addition improves rather than overwhelms:

### Maintain Hierarchy
- **Dominant color** (60%): Primary brand color or most used accent
- **Secondary color** (30%): Supporting color for variety
- **Accent color** (10%): High contrast for key moments
- **Neutrals** (remaining): Gray/black/white for structure

### Accessibility
- **Contrast ratios**: Ensure WCAG compliance (4.5:1 for text, 3:1 for UI components)
- **Don't rely on color alone**: Use icons, labels, or patterns alongside color
- **Test for color blindness**: Verify red/green combinations work for all users

### Cohesion
- **Consistent palette**: Use colors from defined palette, not arbitrary choices
- **Systematic application**: Same color meanings throughout (green always = success)
- **Temperature consistency**: Warm palette stays warm, cool stays cool

**NEVER**:
- Use every color in the rainbow (choose 2-4 colors beyond neutrals)
- Apply color randomly without semantic meaning
- Put gray text on colored backgrounds—it looks washed out; use a darker shade of the background color or transparency instead
- Use pure gray for neutrals—add subtle color tint (warm or cool) for sophistication
- Use pure black (`#000`) or pure white (`#fff`) for large areas
- Violate WCAG contrast requirements
- Use color as the only indicator (accessibility issue)
- Make everything colorful (defeats the purpose)
- Default to purple-blue gradients (AI slop aesthetic)

## Verify Color Addition

Test that colorization improves the experience:

- **Better hierarchy**: Does color guide attention appropriately?
- **Clearer meaning**: Does color help users understand states/categories?
- **More engaging**: Does the interface feel warmer and more inviting?
- **Still accessible**: Do all color combinations meet WCAG standards?
- **Not overwhelming**: Is color balanced and purposeful?

Remember: Color is emotional and powerful. Use it to create warmth, guide attention, communicate meaning, and express personality. But restraint and strategy matter more than saturation and variety. Be colorful, but be intentional.

---

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/colorize.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/colorize.md`           (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: colorize/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "colorize/<project>"`

---

## Recommended next step

Next: `/polish` — palette is set; run a final consistency and token pass to reconcile the new color across the full design.