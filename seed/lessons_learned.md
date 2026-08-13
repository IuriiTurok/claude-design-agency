# Lessons Learned

Universal design principles accumulated across all projects. Updated after every project iteration, especially when a customer requests changes.

**This file is the agency's institutional memory.** Agents MUST read this before starting any new project. It captures the WHY behind decisions, not just the WHAT.

---

## Typography

- **Single font family with role separation** works better than multi-family stacks. Formula: [Geometric sans for headings] + [Same family for body] + [Monospace for data].
- **Monospace for all data elements** (IDs, timestamps, scores, prices, metrics) is mandatory for data-heavy products. It signals precision and enables easy scanning.
- **Tight tracking** (-0.025em to -0.035em on display text) gives more character than default spacing while staying professional.
- **Three font weights max per screen.** Pick three and hold -- more weights dilute hierarchy.
- **Every font-family declaration must have a corresponding font load.** No `<link>` or `@font-face` = browser falls back to system fonts, destroying the brand.

## Color

- **Monochrome + single accent** creates premium feel without color drift. One accent color creates brand ownership; multi-accent dilutes.
- **Warm vs. cold neutral variants** give clients flexibility without diluting the brand. Offer both when the audience spans conservative and modern.
- **OKLCH color ramps** provide perceptually uniform shade steps. Use 10-shade ramps (50-950) for the accent color.
- Any color or font in the brand config's **`reserved_tokens`** belongs to the operating agency's own platform. No client project may use one.
- **Conservative glass** (nav + modals only) > aggressive glass for data-heavy products. Readability is sacred.

## Layout

- **Light-mode-first** for finance, B2B, conservative audiences (tax firms, legal, enterprise). Dark-first for dev tools, creative/consumer, gaming.
- **Low border-radius** (2-8px) signals precision. Higher radius (12-16px) signals friendliness. Vary by element: 12px cards, 8px buttons, 6px badges, full-circle avatars.
- **Generous whitespace** (80-96px section gaps) on landing pages creates breathing room. Dense layouts signal "data tool"; spacious layouts signal "premium product."
- **Cards as primary container** with subtle border + shadow, not heavy background color changes.

## Client Feedback Patterns

- When a client requests changes, capture the **WHY** not just the **WHAT**. "Remove the bridge element from the logo" -> WHY: "the space in between already reads as the letter."
- **Cultural brands MUST use real photography**, never stock or AI-generated. The client's Instagram, social media, or product photos are the source.
- **Multi-brand portfolios** benefit from shared color DNA with distinct accent variations per sub-brand.
- **Competitors' color choices matter.** If all competitors use blue, choose a different accent to differentiate.
- **Conservative clients** (tax/audit, legal, enterprise) respond to restraint over flash. Premium through simplicity (Apple/Uber influence), warmth through language and rounded forms (Airbnb influence).

## Process Anti-Patterns

- Never present deliverables with unresolved CSS variable font references (`var(--font-sans)` in `@theme inline` is a circular reference).
- Never ship placeholder images when real brand assets exist in `assets/`.
- Never generate/fabricate logos for real partner companies -- always source official logos via web search.
- Always produce actual visual assets (SVG/images), not text descriptions of logos.
- Run Style Enforcer before Visual QA -- automated compliance catches 80% of issues before subjective review.

## Character & Mascot Design

- **Pose-sheet consistency is a gate, not a hope.** Every batch must share an identical anatomy baseline (head ratio, hand size), identical hairstyle/accessory treatment, and identical canvas size with ≤2% scale variance. Inconsistency reads as AI slop and costs full correction rounds.
- **Multi-view sets (front/back/side/3/4) come from the same base model**, exported as separate files — independent prompts drift anatomy.
- **Upscale only after poses are finalized.** Upscaling drafts amplifies artifacts.
- **Uniform background treatment** — rembg all images or none; transparent PNGs stack best for 3D prep.
- **Iterate by file path, not re-embedding.** Re-embedding image batches into the conversation every round bloats sessions (27–31MB observed) and loses version history.

## Project Iteration Lessons

_This section is updated after every customer change request._

### B2B SaaS platform, own brand (v1 -> v2)

- **Change:** Switched off a default UI sans onto a more characterful one. **Why:** the default read as generic; the replacement gave character while staying professional.
- **Change:** Restricted glass effects to nav/overlays only. **Why:** Glass on cards/data surfaces hurt readability.
- **Change:** Removed the accent-colored bridge element from the logo. **Why:** the negative space already read as the letterform; an explicit bridge was redundant.

### Fintech landing (v1 -> v3 -> v4)

- **Change:** Created 4 separate iterations with different visual approaches. **Why:** Client needed to see concrete options to make decisions, not abstract descriptions.
- **Change:** Made "Warm Discovery" variant with softer, more approachable aesthetic. **Why:** a conservative professional-services audience needed warmth, not cold precision.

### Non-profit brand

- **Change:** Created 4 concept directions (Strategic Clarity, Digital Forge, Transform Bold, Veteran Power). **Why:** an NGO brand needed to balance professionalism with emotional impact for its audience.

### Character work (three mascot engagements)

- **Change:** Added consistency gates before user review (see Character & Mascot Design above) and the `character_designer` skill. **Why:** 6+ manual correction rounds per session on hair/scale/cut-off issues across three engagements — the user was acting as the QA gate.

### Product prototype (v3 → v31 → v6)

- **Change:** Added the `prototype_lead` skill: design brief + breakpoint table before code, regression-checked QA log before every review. **Why:** 18 sessions in 2 days with 0.7+ corrections per user turn; a fixed bug regressed; breakpoints were discovered mid-session by trial and error.
