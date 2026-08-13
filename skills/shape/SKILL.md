---
name: shape
description: Plan the UX and UI for a feature before writing code. Runs a structured discovery interview, then produces a design brief that guides implementation. Use during the planning phase to establish design direction, constraints, and strategy before any code is written.
version: 2.1.1
user-invocable: true
argument-hint: "[feature to shape]"
license: Apache-2.0. Fork of Impeccable, itself based on Anthropic's frontend-design skill. See NOTICE.md.
---

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol. If no design context exists, run `/impeccable teach` first.

---

Shape the UX and UI for a feature before any code is written. This skill produces a **design brief**: a structured artifact that guides implementation through discovery, not guesswork.

**Scope**: Design planning only. This skill does NOT write code. It produces the thinking that makes code good.

**Output**: A design brief that can be handed off to /impeccable craft, /impeccable, or any other implementation skill.

**Boundary**: `shape` is the **upstream entry** of the design lifecycle — it runs before any implementation skill. It is explicitly excluded from the `/refine` pipeline (which operates on existing built UI). If you already have code or a rendered UI, skip `shape` and go to `/audit` or `/critique` instead.

## Philosophy

Most AI-generated UIs fail not because of bad code, but because of skipped thinking. They jump to "here's a card grid" without asking "what is the user trying to accomplish?" This skill inverts that: understand deeply first, so implementation is precise.

## Phase 1: Discovery Interview

**Do NOT write any code or make any design decisions during this phase.** Your only job is to understand the feature deeply enough to make excellent design decisions later.

Ask these questions in conversation, adapting based on answers. Don't dump them all at once; have a natural dialogue. STOP and call the AskUserQuestion tool to clarify.

### Purpose & Context
- What is this feature for? What problem does it solve?
- Who specifically will use it? (Not "users"; be specific: role, context, frequency)
- What does success look like? How will you know this feature is working?
- What's the user's state of mind when they reach this feature? (Rushed? Exploring? Anxious? Focused?)

### Content & Data
- What content or data does this feature display or collect?
- What are the realistic ranges? (Minimum, typical, maximum, e.g., 0 items, 5 items, 500 items)
- What are the edge cases? (Empty state, error state, first-time use, power user)
- Is any content dynamic? What changes and how often?

### Design Goals
- What's the single most important thing a user should do or understand here?
- What should this feel like? (Fast/efficient? Calm/trustworthy? Fun/playful? Premium/refined?)
- Are there existing patterns in the product this should be consistent with?
- Are there specific examples (inside or outside the product) that capture what you're going for?

### Constraints
- Are there technical constraints? (Framework, performance budget, browser support)
- Are there content constraints? (Localization, dynamic text length, user-generated content)
- Mobile/responsive requirements?
- Accessibility requirements beyond WCAG AA?

### Anti-Goals
- What should this NOT be? What would be a wrong direction?
- What's the biggest risk of getting this wrong?

## Phase 2: Design Brief

After the interview, synthesize everything into a structured design brief. Present it to the user for confirmation before considering this skill complete.

### Brief Structure

**1. Feature Summary** (2-3 sentences)
What this is, who it's for, what it needs to accomplish.

**2. Primary User Action**
The single most important thing a user should do or understand here.

**3. Design Direction**
How this should feel. What aesthetic approach fits. Reference the project's design context from `.impeccable.md` and explain how this feature should express it.

**4. Layout Strategy**
High-level spatial approach: what gets emphasis, what's secondary, how information flows. Describe the visual hierarchy and rhythm, not specific CSS.

**5. Key States**
List every state the feature needs: default, empty, loading, error, success, edge cases. For each, note what the user needs to see and feel.

**6. Interaction Model**
How users interact with this feature. What happens on click, hover, scroll? What feedback do they get? What's the flow from entry to completion?

**7. Content Requirements**
What copy, labels, empty state messages, error messages, and microcopy are needed. Note any dynamic content and its realistic ranges.

**8. Recommended References**
Based on the brief, list which impeccable reference files would be most valuable during implementation (e.g., spatial-design.md for complex layouts, motion-design.md for animated features, interaction-design.md for form-heavy features).

**9. Open Questions**
Anything unresolved that the implementer should resolve during build.

---

STOP and call the AskUserQuestion tool to clarify. Get explicit confirmation of the brief before finishing. If the user disagrees with any part, revisit the relevant discovery questions.

Once confirmed, the brief is complete. The user can now hand it to /impeccable, or use it to guide any other implementation approach. (If the user wants the full discovery-then-build flow in one step, they should use /impeccable craft instead, which runs this skill internally.)

---

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/shape.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/shape.md`  (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output),
  a *gotcha* (a non-obvious failure you had to work around), or a *durable insight* worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: shape/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "shape/<project>"`

---

## Recommended next step

Next: `/audit` *(or `/impeccable craft`)* — brief is done; implement it, then measure the build.