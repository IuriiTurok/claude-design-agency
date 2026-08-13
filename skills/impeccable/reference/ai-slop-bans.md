# AI-Slop Ban List — Canonical Source of Truth

This is the **single, authoritative** AI-slop / anti-pattern ban list for the design
silo. It is consolidated from the `<absolute_bans>`, `<reflex_fonts_to_reject>`, and
DON'T content in [../SKILL.md](../SKILL.md). Sibling skills (`taste-skill`,
`design-agency`) and the Phase-5 QA agents (`taste-guardian`, `visual-qa`) **reference
this file** instead of maintaining their own copies — when they disagree, this file
wins.

Two sections, by scope:
- **General AI-slop bans** — provider/brand-agnostic tells. Apply to **every** design run.
- **Own-brand rules** — agency-specific overrides. Apply **only** inside a
  design-agency engagement, and only when the brand config declares an own brand.

New tells discovered in critique/audit/QA runs enter via Bridge D
(`ai-slop-candidates.jsonl`, `scope ∈ {general, own_brand}`) and, once promoted by the
impeccable anti-pattern sil, land in the matching section here. See the
[Self-learning](../SKILL.md#self-learning) block. All promotions are
PROSE_RULE ≤ ONE_CLICK — never auto-applied.

---

## General AI-slop bans

These apply to every design run, regardless of brand or project.

### Absolute CSS bans (match-and-refuse)

These CSS patterns are NEVER acceptable. They are the most recognizable AI design
tells. If you find yourself about to write any of these, stop and rewrite the element
with a different structure entirely.

**BAN 1: Side-stripe borders on cards / list items / callouts / alerts**
- PATTERN: `border-left:` or `border-right:` with width greater than 1px
- INCLUDES: hard-coded colors AND CSS variables
- FORBIDDEN: `border-left: 3px solid red`, `border-left: 4px solid #ff0000`,
  `border-left: 4px solid var(--color-warning)`, `border-left: 5px solid oklch(...)`, etc.
- WHY: this is the single most overused "design touch" in admin, dashboard, and medical
  UIs. It never looks intentional regardless of color, radius, opacity, or whether the
  variable name is "primary" or "warning" or "accent."
- REWRITE: use a different element structure entirely. Do not just swap to box-shadow
  inset. Reach for full borders, background tints, leading numbers/icons, or no visual
  indicator at all.

**BAN 2: Gradient text**
- PATTERN: `background-clip: text` (or `-webkit-background-clip: text`) combined with a
  gradient background
- FORBIDDEN: any combination that makes text fill come from a `linear-gradient`,
  `radial-gradient`, or `conic-gradient`
- WHY: gradient text is decorative rather than meaningful and is one of the top three AI
  design tells
- REWRITE: use a single solid color for text. If you want emphasis, use weight or size,
  not gradient fill.

### Reflex fonts to reject

These are the model's training-data defaults; reaching for them creates monoculture
across projects. Reject every font in this list — and do not simply switch to your
second-favorite. Look further (see the font-selection procedure in
[../SKILL.md](../SKILL.md)).

```
Fraunces
Newsreader
Lora
Crimson
Crimson Pro
Crimson Text
Playfair Display
Cormorant
Cormorant Garamond
Syne
IBM Plex Mono
IBM Plex Sans
IBM Plex Serif
Space Mono
Space Grotesk
Inter
DM Sans
DM Serif Display
DM Serif Text
Outfit
Plus Jakarta Sans
Instrument Sans
Instrument Serif
```

Also reject overused system/web defaults as body or display faces: Inter, Roboto,
Arial, Open Sans, and system-default stacks.

### Typography tells

- DO NOT use monospace typography as lazy shorthand for "technical/developer" vibes.
- DO NOT put large icons with rounded corners above every heading. They rarely add value
  and make sites look templated.
- DO NOT use only one font family for the entire page. Pair a distinctive display font
  with a refined body font.
- DO NOT use a flat type hierarchy where sizes are too close together. Aim for at least a
  1.25 ratio between steps.
- DO NOT set long body passages in uppercase. Reserve all-caps for short labels and
  headings.

### Color tells

- DO NOT use gray text on colored backgrounds; it looks washed out. Use a shade of the
  background color instead.
- DO NOT use pure black (#000) or pure white (#fff). Always tint; pure black/white never
  appears in nature.
- DO NOT use the AI color palette: cyan-on-dark, purple-to-blue gradients, neon accents
  on dark backgrounds.
- DO NOT default to dark mode with glowing accents. It looks "cool" without requiring
  actual design decisions.
- DO NOT default to light mode "to be safe" either. The point is to choose, not to
  retreat to a safe option.

### Layout tells

- DO NOT wrap everything in cards. Not everything needs a container.
- DO NOT nest cards inside cards. Visual noise; flatten the hierarchy.
- DO NOT use identical card grids (same-sized cards with icon + heading + text, repeated
  endlessly).
- DO NOT use the hero metric layout template (big number, small label, supporting stats,
  gradient accent).
- DO NOT center everything. Left-aligned text with asymmetric layouts feels more designed.
- DO NOT use the same spacing everywhere. Without rhythm, layouts feel monotonous.

### Visual-detail tells

- DO NOT use glassmorphism everywhere (blur effects, glass cards, glow borders used
  decoratively rather than purposefully).
- DO NOT use sparklines as decoration. Tiny charts that look sophisticated but convey
  nothing meaningful.
- DO NOT use rounded rectangles with generic drop shadows. Safe, forgettable, could be
  any AI output.
- DO NOT use modals unless there's truly no better alternative. Modals are lazy.

### Motion tells

- DO NOT animate layout properties (width, height, padding, margin). Use transform and
  opacity only.
- DO NOT use bounce or elastic easing. They feel dated and tacky; real objects decelerate
  smoothly.

### Content / icon tells

- DO NOT use emoji as icons in a production interface (the anti-emoji rule). Emoji render
  inconsistently across platforms and read as unconsidered; use a real icon set or a
  purposeful typographic mark instead.

### The AI Slop Test

If you showed this interface to someone and said "AI made this," would they believe you
immediately? If yes, that's the problem. A distinctive interface should make someone ask
"how was this made?" not "which AI made this?" The bans above are the fingerprints of
AI-generated work from 2024-2025.

---

## Own-brand rules

These apply **only** inside a design-agency engagement. They are overrides on
top of the General section, not replacements for it. Genuinely brand-specific additions
(palette locks, mascot/voice constraints, stack conventions) live here so the General set
stays reusable by any project.

- **LILA BAN.** Do not use the lila / generic lavender-purple AI accent in own-brand work
  (migrated here from `taste-skill`; it is a brand-specific palette lock layered on the
  General "AI purple/blue gradient" ban).
- **Brand palette locks, mascot, and voice** are defined by the active engagement's
  `style_library.md` and the agency seed/role files; defer to those for the
  brand-specific specifics. This file holds only the durable, cross-engagement own-brand
  ban additions — per-engagement choices stay in the engagement's own style library.
- **Stack conventions** (DESIGN_VARIANCE / MOTION_INTENSITY / VISUAL_DENSITY baselines)
  remain owned by `taste-skill`; this file does not duplicate them — it only carries the
  own-brand ban additions that are not already in the General section.

Promoted own-brand candidates (Bridge D, `scope: own_brand`) append here.
