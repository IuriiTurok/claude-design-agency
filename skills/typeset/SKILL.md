---
name: typeset
description: Improves typography by fixing font choices, hierarchy, sizing, weight, and readability so text feels intentional. Use when the user mentions fonts, type, readability, text hierarchy, sizing looks off, or wants more polished, intentional typography.
version: 2.1.1
user-invocable: true
argument-hint: "[target]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

Assess and improve typography that feels generic, inconsistent, or poorly structured — turning default-looking text into intentional, well-crafted type.

**Workflow position:** `typeset` is the type stage of the `/refine` pipeline (`audit → layout → typeset → colorize → harden → polish`). Run it after `/layout` has settled the structural rhythm; it hands off to `/colorize` once hierarchy is clear.

**Boundary — `layout` vs `typeset`:** Use `/layout` when the problem is structural — grid, spacing, component arrangement, visual rhythm. Use `/typeset` when the structure is already sound but the *text itself* is generic, inconsistent, or poorly scaled. If both are broken, `/layout` first.

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol. If no design context exists, run `/impeccable teach` first.

---

## Assess Current Typography

Analyze what's weak or generic about the current type:

1. **Font choices**:
   - Are we using invisible defaults? (Inter, Roboto, Arial, Open Sans, system defaults)
   - Does the font match the brand personality? (A playful brand shouldn't use a corporate typeface)
   - Are there too many font families? (More than 2-3 is almost always a mess)

2. **Hierarchy**:
   - Can you tell headings from body from captions at a glance?
   - Are font sizes too close together? (14px, 15px, 16px = muddy hierarchy)
   - Are weight contrasts strong enough? (Medium vs Regular is barely visible)

3. **Sizing & scale**:
   - Is there a consistent type scale, or are sizes arbitrary?
   - Does body text meet minimum readability? (16px+)
   - Is the sizing strategy appropriate for the context? (Fixed `rem` scales for app UIs; fluid `clamp()` for marketing/content page headings)

4. **Readability**:
   - Are line lengths comfortable? (45-75 characters ideal)
   - Is line-height appropriate for the font and context?
   - Is there enough contrast between text and background?

5. **Consistency**:
   - Are the same elements styled the same way throughout?
   - Are font weights used consistently? (Not bold in one section, semibold in another for the same role)
   - Is letter-spacing intentional or default everywhere?

**CRITICAL**: The goal isn't to make text "fancier" — it's to make it clearer, more readable, and more intentional. Good typography is invisible; bad typography is distracting.

## Plan Typography Improvements

Consult the [typography reference](reference/typography.md) from the impeccable skill for detailed guidance on scales, pairing, and loading strategies.

Create a systematic plan:

- **Font selection**: Do fonts need replacing? What fits the brand/context?
- **Type scale**: Establish a modular scale (e.g., 1.25 ratio) with clear hierarchy
- **Weight strategy**: Which weights serve which roles? (Regular for body, Semibold for labels, Bold for headings — or whatever fits)
- **Spacing**: Line-heights, letter-spacing, and margins between typographic elements

## Improve Typography Systematically

### Font Selection

If fonts need replacing:
- Choose fonts that reflect the brand personality
- Pair with genuine contrast (serif + sans, geometric + humanist) — or use a single family in multiple weights
- Ensure web font loading doesn't cause layout shift (`font-display: swap`, metric-matched fallbacks)

### Establish Hierarchy

Build a clear type scale:
- **5 sizes cover most needs**: caption, secondary, body, subheading, heading
- **Use a consistent ratio** between levels (1.25, 1.333, or 1.5)
- **Combine dimensions**: Size + weight + color + space for strong hierarchy — don't rely on size alone
- **App UIs**: Use a fixed `rem`-based type scale, optionally adjusted at 1-2 breakpoints. Fluid sizing undermines the spatial predictability that dense, container-based layouts need
- **Marketing / content pages**: Use fluid sizing via `clamp(min, preferred, max)` for headings and display text. Keep body text fixed

### Fix Readability

- Set `max-width` on text containers using `ch` units (`max-width: 65ch`)
- Adjust line-height per context: tighter for headings (1.1-1.2), looser for body (1.5-1.7)
- Increase line-height slightly for light-on-dark text
- Ensure body text is at least 16px / 1rem

### Refine Details

- Use `tabular-nums` for data tables and numbers that should align
- Apply proper `letter-spacing`: slightly open for small caps and uppercase, default or tight for large display text
- Use semantic token names (`--text-body`, `--text-heading`), not value names (`--font-16`)
- Set `font-kerning: normal` and consider OpenType features where appropriate

### Weight Consistency

- Define clear roles for each weight and stick to them
- Don't use more than 3-4 weights (Regular, Medium, Semibold, Bold is plenty)
- Load only the weights you actually use (each weight adds to page load)

**NEVER**:
- Use more than 2-3 font families
- Pick sizes arbitrarily — commit to a scale
- Set body text below 16px
- Use decorative/display fonts for body text
- Disable browser zoom (`user-scalable=no`)
- Use `px` for font sizes — use `rem` to respect user settings
- Default to Inter/Roboto/Open Sans when personality matters
- Pair fonts that are similar but not identical (two geometric sans-serifs)

> Canonical font-ban list and typography scale reference: `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/reference/typography.md`

## Verify Typography Improvements

- **Hierarchy**: Can you identify heading vs body vs caption instantly?
- **Readability**: Is body text comfortable to read in long passages?
- **Consistency**: Are same-role elements styled identically throughout?
- **Personality**: Does the typography reflect the brand?
- **Performance**: Are web fonts loading efficiently without layout shift?
- **Accessibility**: Does text meet WCAG contrast ratios? Is it zoomable to 200%?

Remember: Typography is the foundation of interface design — it carries the majority of information. Getting it right is the highest-leverage improvement you can make.

---

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/typeset.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/typeset.md`           (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: typeset/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "typeset/<project>"`

---

## Recommended next step

Next: `/colorize` — type hierarchy is intentional → layer strategic, meaningful color on top of it.