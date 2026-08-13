# Accumulated Anti-Patterns (MANDATORY enforcement)

Learned from 9+ projects (provenance/source per pattern is folded into
`{AGENCY_STATE}/lessons_learned.md`; the rule + rationale below are the enforced
substance). This is the design-agency-local copy of the AI-slop / anti-pattern ban
list. The canonical single source of truth is **impeccable**
(`{AGENCY_ROOT}/skills/impeccable/reference/ai-slop-bans.md`, General/own-brand split);
new candidate bans flow there via Bridge D, which appends to
`{AGENCY_STATE}/ai-slop-candidates.jsonl` (state, not the read-only plugin root). When
that consolidation lands, this file becomes a one-line pointer to the impeccable canon.

| #   | Anti-Pattern                                                                          | Why It's Banned                                                                                          |
| --- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1   | Purple/blue gradients on white                                                        | Signature of AI "slop" — signals low effort                                                              |
| 2   | Inter, Roboto, Arial as defaults                                                      | Generic; we use distinctive fonts (Geist, Plus Jakarta Sans, DM Sans, Syne, Playfair Display)            |
| 3   | Uniform 8px border-radius on everything                                               | Radius should vary (12px cards, 8px buttons, 6px badges, full-circle avatars)                            |
| 4   | Cookie-cutter centered hero with generic illustration                                 | Every layout must earn its composition                                                                   |
| 5   | No hover states or transitions                                                        | Interactivity mandatory — 200-300ms ease-out minimum                                                     |
| 6   | Multiple accent colors competing                                                      | Single accent creates brand ownership; multi-accent dilutes                                              |
| 7   | Glass effects on data surfaces (cards, tables, forms)                                 | Readability is sacred. Glass only on nav/overlays/modals                                                 |
| 8   | Loading spinners                                                                      | Use skeleton screens or progress bars                                                                    |
| 9   | CSS `var(--font-sans)` in `@theme inline`                                             | Circular reference — breaks font loading in single-file HTML                                             |
| 10  | Unequal deliverable sets between project variants                                     | Every variant gets the same count and quality                                                            |
| 11  | Missing HTML brand book when markdown exists                                          | `brand_book.html` mandatory alongside `brand_book.md`                                                    |
| 12  | Logo concepts as text descriptions without SVG/image                                  | Always produce actual visual assets, not descriptions                                                    |
| 13  | Placeholder images when real brand assets exist                                       | Check `assets/` before using placeholders                                                                |
| 14  | Stock photography or "unsplash" placeholders                                          | Icons, data, typography are our visual language                                                          |
| 15  | Banned copy: "leverage," "synergize," "cutting-edge," "seamlessly," "next-generation" | Marketing fluff erodes trust                                                                             |
| 16  | More than 3 font weights per screen                                                   | Pick three and hold                                                                                      |
| 17  | Missing `alt` text on images                                                          | Accessibility baseline — every `<img>` needs meaningful alt                                              |
| 18  | Font-family declaration without font loading (`<link>` / `@font-face`)                | Browser falls back to serif/sans-serif, destroying the brand                                             |
| 19  | A color from `reserved_tokens.colors` used outside `own_brand_folders`                | Reserved by the operating agency for its own brand — see the brand config                                |
| 20  | A font from `reserved_tokens.fonts` used outside `own_brand_folders`                  | Reserved by the operating agency for its own brand — see the brand config                                |
| 21  | Synthetic/placeholder logos for real companies in "Partners"/"Trusted by"             | Real companies need actual logos via WebSearch. May grayscale/tint, NEVER fabricate. If not found, omit. |
