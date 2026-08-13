---
name: audit
description: Run technical quality checks across accessibility, performance, theming, responsive design, and anti-patterns. Generates a scored report with P0-P3 severity ratings and actionable plan. Use when the user wants an accessibility check, performance audit, or technical quality review.
version: 2.1.1
user-invocable: true
argument-hint: "[area (feature, page, component...)]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol. If no design context exists, run `/impeccable teach` first.

---

**Boundary — `audit` (technical, objective) vs `critique` (UX, subjective):** Use `audit` when you want *measurable, code-level* facts — WCAG contrast ratios, layout-thrashing, animating layout props, missing ARIA, responsive breakpoints, anti-patterns. Objective, scored P0–P3, no taste judgment. Use `critique` when you want a *subjective UX/design-director* read — visual hierarchy, information architecture, emotional resonance, cognitive load, AI-slop tells. **Containment:** `audit ⊂ critique`. For a thorough review, `critique` should call `audit` for the objective dimensions and fold those scores in, then add the subjective layer on top.

---

Run systematic **technical** quality checks and generate a comprehensive report. Don't fix issues — document them for other commands to address.

This is a code-level audit, not a design critique. Check what's measurable and verifiable in the implementation.

## Diagnostic Scan

Run comprehensive checks across 6 dimensions. Score each dimension 0-4 using the criteria below.

### 1. Accessibility (A11y)

**Check for**:
- **Contrast issues**: Text contrast ratios < 4.5:1 (or 7:1 for AAA)
- **Missing ARIA**: Interactive elements without proper roles, labels, or states
- **Keyboard navigation**: Missing focus indicators, illogical tab order, keyboard traps
- **Semantic HTML**: Improper heading hierarchy, missing landmarks, divs instead of buttons
- **Alt text**: Missing or poor image descriptions
- **Form issues**: Inputs without labels, poor error messaging, missing required indicators

**Score 0-4**: 0=Inaccessible (fails WCAG A), 1=Major gaps (few ARIA labels, no keyboard nav), 2=Partial (some a11y effort, significant gaps), 3=Good (WCAG AA mostly met, minor gaps), 4=Excellent (WCAG AA fully met, approaches AAA)

### 2. Performance

**Check for**:
- **Layout thrashing**: Reading/writing layout properties in loops
- **Expensive animations**: Animating layout properties (width, height, top, left) instead of transform/opacity
- **Missing optimization**: Images without lazy loading, unoptimized assets, missing will-change
- **Bundle size**: Unnecessary imports, unused dependencies
- **Render performance**: Unnecessary re-renders, missing memoization

**Score 0-4**: 0=Severe issues (layout thrash, unoptimized everything), 1=Major problems (no lazy loading, expensive animations), 2=Partial (some optimization, gaps remain), 3=Good (mostly optimized, minor improvements possible), 4=Excellent (fast, lean, well-optimized)

### 3. Theming

**Check for**:
- **Hard-coded colors**: Colors not using design tokens
- **Broken dark mode**: Missing dark mode variants, poor contrast in dark theme
- **Inconsistent tokens**: Using wrong tokens, mixing token types
- **Theme switching issues**: Values that don't update on theme change

**Score 0-4**: 0=No theming (hard-coded everything), 1=Minimal tokens (mostly hard-coded), 2=Partial (tokens exist but inconsistently used), 3=Good (tokens used, minor hard-coded values), 4=Excellent (full token system, dark mode works perfectly)

### 4. Responsive Design

**Check for**:
- **Fixed widths**: Hard-coded widths that break on mobile
- **Touch targets**: Interactive elements < 44x44px
- **Horizontal scroll**: Content overflow on narrow viewports
- **Text scaling**: Layouts that break when text size increases
- **Missing breakpoints**: No mobile/tablet variants

**Score 0-4**: 0=Desktop-only (breaks on mobile), 1=Major issues (some breakpoints, many failures), 2=Partial (works on mobile, rough edges), 3=Good (responsive, minor touch target or overflow issues), 4=Excellent (fluid, all viewports, proper touch targets)

### 5. Anti-Patterns (CRITICAL)

Check against ALL the **DON'T** guidelines in the impeccable skill. Look for AI slop tells (AI color palette, gradient text, glassmorphism, hero metrics, card grids, generic fonts) and general design anti-patterns (gray on color, nested cards, bounce easing, redundant copy).

**Score 0-4**: 0=AI slop gallery (5+ tells), 1=Heavy AI aesthetic (3-4 tells), 2=Some tells (1-2 noticeable), 3=Mostly clean (subtle issues only), 4=No AI tells (distinctive, intentional design)

### 6. Feedback & Motion

**Check for**:
- **Missing feedback**: actions with no visual acknowledgment (button press, form submit, toggle, copy)
- **Jarring transitions**: instant state changes that should ease (show/hide, expand/collapse, route/tab switches)
- **No entrance choreography**: content that pops in with no fade/stagger where it would aid comprehension
- **Poor loading feedback**: blank waits — or spinners where the project bans them (prefer skeletons / progress bars)
- **Motion budget drift**: hard-coded durations/easing instead of the project `--dur-*` / `--ease-*` tokens; missing `prefers-reduced-motion` fallback

Measures the *absence* of purposeful motion (a page can score 4/4 Performance while being completely static). Does not author motion — low scores route to `/animate`, which clamps to the project motion budget.

**Score 0-4**: 0=Entirely static (no feedback, instant everything), 1=Major gaps (most interactions unacknowledged), 2=Partial (some feedback, key transitions missing/unmotivated), 3=Good (purposeful motion on most interactions, reduced-motion respected, minor gaps), 4=Excellent (coherent motion language, budget-clamped, reduced-motion complete)

## Generate Report

### Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | ? | [most critical a11y issue or "--"] |
| 2 | Performance | ? | |
| 3 | Responsive Design | ? | |
| 4 | Theming | ? | |
| 5 | Anti-Patterns | ? | |
| 6 | Feedback & Motion | ? | [static UI / missing feedback or "--"] |
| **Total** | | **??/24** | **[Rating band]** |

**Rating bands**: 22-24 Excellent (minor polish), 17-21 Good (address weak dimensions), 12-16 Acceptable (significant work needed), 7-11 Poor (major overhaul), 0-6 Critical (fundamental issues)

### Anti-Patterns Verdict
**Start here.** Pass/fail: Does this look AI-generated? List specific tells. Be brutally honest.

### Executive Summary
- Audit Health Score: **??/24** ([rating band])
- Total issues found (count by severity: P0/P1/P2/P3)
- Top 3-5 critical issues
- Recommended next steps

### Detailed Findings by Severity

Tag every issue with **P0-P3 severity**:
- **P0 Blocking**: Prevents task completion — fix immediately
- **P1 Major**: Significant difficulty or WCAG AA violation — fix before release
- **P2 Minor**: Annoyance, workaround exists — fix in next pass
- **P3 Polish**: Nice-to-fix, no real user impact — fix if time permits

For each issue, document:
- **[P?] Issue name**
- **Location**: Component, file, line
- **Category**: Accessibility / Performance / Theming / Responsive / Anti-Pattern / Feedback & Motion
- **Impact**: How it affects users
- **WCAG/Standard**: Which standard it violates (if applicable)
- **Recommendation**: How to fix it
- **Suggested command**: Which command to use (prefer: /animate, /quieter, /shape, /optimize, /adapt, /clarify, /layout, /distill, /delight, /audit, /harden, /polish, /bolder, /typeset, /critique, /colorize, /overdrive)

### Patterns & Systemic Issues

Identify recurring problems that indicate systemic gaps rather than one-off mistakes:
- "Hard-coded colors appear in 15+ components, should use design tokens"
- "Touch targets consistently too small (<44px) throughout mobile experience"

### Positive Findings

Note what's working well — good practices to maintain and replicate.

## Recommended Actions

List recommended commands in priority order (P0 first, then P1, then P2):

1. **[P?] `/command-name`** — Brief description (specific context from audit findings)
2. **[P?] `/command-name`** — Brief description (specific context)

**Rules**: Only recommend commands from: /animate, /quieter, /shape, /optimize, /adapt, /clarify, /layout, /distill, /delight, /audit, /harden, /polish, /bolder, /typeset, /critique, /colorize, /overdrive. Map findings to the most appropriate command. End with `/polish` as the final step if any fixes were recommended.

After presenting the summary, tell the user:

> You can ask me to run these one at a time, all at once, or in any order you prefer.
>
> Re-run `/audit` after fixes to see your score improve.

**IMPORTANT**: Be thorough but actionable. Too many P3 issues creates noise. Focus on what actually matters.

**NEVER**:
- Report issues without explaining impact (why does this matter?)
- Provide generic recommendations (be specific and actionable)
- Skip positive findings (celebrate what works)
- Forget to prioritize (everything can't be P0)
- Report false positives without verification

Remember: You're a technical quality auditor. Document systematically, prioritize ruthlessly, cite specific code locations, and provide clear paths to improvement.

---

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/audit.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/audit.md`           (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: audit/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "audit/<project>"`

---

**Next: `/refine`** — Scored findings in hand → run the fix pipeline (`audit → layout → typeset → colorize → harden → polish`) that addresses them.