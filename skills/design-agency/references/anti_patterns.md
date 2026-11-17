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
| 2   | Inter, Roboto, Arial as defaults                                                      | Generic. Canon for banned and reflex fonts: impeccable `reference/ai-slop-bans.md` (path above)          |
| 3   | Uniform 8px border-radius on everything                                               | Radius should vary (12px cards, 8px buttons, 6px badges, full-circle avatars)                            |
| 4   | Cookie-cutter centered hero with generic illustration                                 | Every layout must earn its composition                                                                   |
| 5   | No hover states or transitions                                                        | Interactivity mandatory. Hover and press feedback 100-160 ms ease-out (`emil-design-eng/SKILL.md` §4)    |
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
| 22 | The 2026 default look: cream background, serif display, terracotta accent; or near-black with acid green | The current template signature, as purple gradients were in 2024. A palette needs a reason from the brief |
| 23 | Italic serif hero headline, or one accented or gradient word in the headline | Reads as generated on sight |
| 24 | All-caps letter-spaced eyebrows, monospace micro-labels as decoration, 01/02/03 markers with no real sequence | Structure must carry meaning; mono is for figures and code |
| 25 | Fade-up on every section, marquees, pulsing dots, bounce easing | Motion as filler. One orchestrated moment per page; the rest is feedback under 200 ms |
| 26 | Hero-metric layouts and identical card grids, nested cards, an arrow on every link | Template tells; vary the layout family and let hierarchy do the work |
| 27 | A primary action that opens the mail client (button-styled mailto) | Conversion leak; a button that promises a booking opens a booking (enforce.py cta-contact-link) |
| 28 | More than one primary-styled action in a viewport, or the same action under several labels | Splits the decision; one primary conversion per page (conversion_brief.md) |
| 29 | A number without its source, denominator or date; an invented benchmark or lift in a client document | Unverifiable proof costs the trust it is meant to earn |
| 30 | Placeholder-only labels, inputs under 16 px on phones, a form asking more than the next human step needs | Form friction; see the form policy in roles/conversion_strategist.md |
| 31 | Remote font CSS (Google Fonts, Typekit) in client deliverables | Privacy exposure in the EU and render-blocking; self-host WOFF2 (enforce.py font-remote-css) |
| 32 | Content hidden until an entrance animation finishes; the LCP image lazy-loaded | Delays reading and the largest paint; speed has the strongest conversion evidence |

Rows 22 to 26 are the late-2026 tell set (checked 2026-11-13 against the Impeccable and taste-skill tell lists); rows 27 to 32 are conversion and delivery defects added with v0.6.0. A project directive may waive a tell with a written Brand Override; it may not waive rows 27 to 32.
