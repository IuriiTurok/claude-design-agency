# Impeccable Context Protocol

Lightweight context check for design sub-skills. Loads instead of
full `/impeccable` to save tokens. Full impeccable is only needed
for `craft`, `teach`, or `extract` modes.

## Context Gathering Protocol

Design skills produce generic output without project context. You MUST
have confirmed design context before doing any design work.

**Required context** (every design skill needs at minimum):
- **Target audience**: Who uses this product and in what context?
- **Use cases**: What jobs are they trying to get done?
- **Brand personality/tone**: How should the interface feel?

Individual skills may require additional context. Check the skill's
preparation section for specifics.

**CRITICAL**: You cannot infer this context by reading the codebase.
Code tells you what was built, not who it's for or what it should feel
like. Only the creator can provide this context.

**Gathering order:**
1. **Check current instructions (instant)**: If your loaded instructions
   already contain a **Design Context** section, proceed immediately.
2. **Check .impeccable.md (fast)**: If not in instructions, read
   `.impeccable.md` from the project root. If it exists and contains the
   required context, proceed.
3. **Run impeccable teach (REQUIRED)**: If neither source has context,
   you MUST run `/impeccable teach` NOW before doing anything else.

## Design Skill Router

When the user's complaint is vague, diagnose the root cause to pick the
right skill:

| Complaint | Diagnosis | Skill |
|-----------|-----------|-------|
| "looks generic / boring / safe" | Default typography | `/typeset` |
| | Gray/desaturated palette | `/colorize` |
| | Monotonous grid layout | `/layout` |
| | Everything is medium intensity | `/bolder` |
| | All of the above | `/impeccable craft` |
| "too much / overwhelming / loud" | Visual intensity overload | `/quieter` |
| | Structural complexity | `/distill` |
| "not polished / something's off" | Micro-detail misalignment | `/polish` |
| | Missing edge cases | `/harden` |
| "needs animation / feels static" | Purposeful UI feedback | `/animate` |
| | Personality and delight | `/delight` |
| | Technically ambitious effects | `/overdrive` |
| "hard to read / confusing" | Bad UX copy or labels | `/clarify` |
| | Typography issues | `/typeset` |
| "not responsive / broken on mobile" | Viewport adaptation | `/adapt` |
| "slow / janky" | Performance issues | `/optimize` |
