# Style Library

Cross-project design knowledge maintained by the Style Librarian. Each entry records the
aesthetic decisions, outcomes, and lessons from a completed project.

This file ships empty. It is copied once into `{AGENCY_STATE}/style_library.md` and grows
from there — it is **your** agency's memory, and it never returns to the plugin. Its two
jobs are (1) collision checks, so a new client does not inherit a past client's solution,
and (2) lesson capture. It is never a template to copy from.

Append one entry per project that reaches Phase 5. Project close is blocked until the
entry exists.

---

## Entry template

Copy the block below for each completed project.

```markdown
## Project: <Name> (<version> — <Month Year>)
**Client type:** <industry / product category — one line>
**Style archetype:** <the named direction chosen, e.g. "Structured Clarity", "Editorial Warmth">
**Palette:**
- <role>: <hex> — <why this value, not just what it is>
- Primary Action: <hex> — sole accent
- Surfaces: <solid / glass / layered, and where each is allowed>
**Typography:** <families, tracking, and what mono is reserved for>
**Layout:** <radius scale, spacing base, shadow levels, max-width>
**Logo:** <construction, color rules, what is deliberately absent>
**Client feedback:** <what they asked for in their own words; what they rejected and why>
**Iterations needed:**
- <what v1 got wrong and what replaced it>
**Key lessons:**
- <a rule you would apply to the next project in this category>
```

## What makes an entry useful later

- **Record rejections, not just decisions.** "Client rejected the accent bridge on the
  logo — the negative space already read as the letter" is worth more than the final hex.
- **Name the archetype.** Collision checks work by archetype and layout signature, not by
  client name. Two fintech landing pages with the same hero split-layout is a collision
  even when every token differs.
- **One rule per lesson.** A lesson you cannot state as a rule is an anecdote.
- **Keep client-identifying detail here, never in the plugin.** This file lives in
  `{AGENCY_STATE}`; the plugin directory is read-only at runtime and is distributed.
