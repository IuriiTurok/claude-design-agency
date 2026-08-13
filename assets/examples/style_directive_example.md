# Style Directive — Example / Variant A: Plain

A worked example of the format every project's `style_directive.md` must follow. It is
**not** a template to copy values from — the whole point of a directive is that its values
were chosen for one brief. Copy the *shape*, decide the *values*.

The Style Enforcer reads this file's real counterpart as its source of truth. Anything not
named here is a violation, so a directive that omits a section grants no permission — it
creates an unenforceable gap.

---

## Style Archetype

One named direction in a sentence, plus the two or three references it triangulates
between. "Structured Clarity — Swiss grid discipline, with the surface honesty of a
component library and none of the gloss."

## Color Palette

| Role | Value | Notes |
|---|---|---|
| Background | `#FFFFFF` | Light-mode-first; see Layout for when to invert |
| Surface | `#F6F6F7` | Cards, wells |
| Border | `#E4E4E7` | 1px, never heavier |
| Text | `#18181B` | Body |
| Text Muted | `#71717A` | Secondary only — never for body copy |
| Accent | `#2563EB` | **Sole** accent. One accent creates ownership; two dilute |

### Semantic Colors

| Role | Value |
|---|---|
| Success | `#16A34A` |
| Warning | `#CA8A04` |
| Danger | `#DC2626` |

Semantic colors are for state, never for decoration.

## Typography

| Role | Family | Weight | Size | Tracking |
|---|---|---|---|---|
| Display | System sans | 600 | 48–64px | -0.03em |
| Heading | System sans | 600 | 20–32px | -0.02em |
| Body | System sans | 400 | 16px | 0 |
| Data | System mono | 500 | 14px | 0 |

### Rules

- Three weights maximum per screen.
- Monospace is reserved for data (IDs, timestamps, scores, prices) — never for prose.
- Every `font-family` needs a matching `<link>` or `@font-face`. A declaration without a
  load silently falls back to serif and destroys the brand.

## Layout

### Spacing Scale (8px base)

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96` — no value off the scale.

### Corner Radius

Cards `12px` · buttons/inputs `8px` · badges `6px` · avatars `9999px`.
Uniform radius on everything is an anti-pattern; radius carries hierarchy.

### Elevation

Level 1 `0 1px 2px rgb(0 0 0 / 0.05)` · Level 2 `0 4px 12px rgb(0 0 0 / 0.08)` ·
Level 3 `0 12px 32px rgb(0 0 0 / 0.12)`. Nothing above level 3.

### Content Container

`max-width: 1200px`, gutter `24px` mobile / `48px` desktop, section gap `96px`.

## Interactive States

Every interactive element declares `:hover`, `:focus-visible`, and `:active`. A missing
hover state is a Style Enforcer violation, not a nit.

### Transitions

`200ms ease-out` default; `150ms` for color-only changes. Wrap anything above 200ms in
`@media (prefers-reduced-motion: no-preference)`.

## CSS Custom Properties

Declare every token above as a custom property on `:root` so the enforcer can grep for
definition sites. Redefine only the values under a dark-mode block — never give a color
its sole definition inside a media query.

## Do Not List

At least 12 entries, each a concrete banned pattern with the reason. Examples:

1. No purple/blue gradient on white — the signature AI-slop tell.
2. No glass or `backdrop-filter` on cards, tables, or forms — readability is sacred.
3. No second accent color.
4. No loading spinners — skeletons or progress bars.
5. No stock photography or `unsplash` placeholders.
6. No `var(--font-*)` inside a `@theme inline` block — circular reference, breaks loading.
7. No fabricated logos for real companies in "Trusted by" — source them or omit the section.
8. No `<img>` without meaningful `alt`.
9. No more than three consecutive sections sharing the same padding and structure.
10. No radius value outside the scale above.
11. No spacing value off the 8px scale.
12. No copy from the banned-words list ("leverage", "seamlessly", "next-generation").
