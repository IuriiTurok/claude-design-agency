# Official Skills & Tooling Catalog (Technical Execution Layer)

This is **Layer 5** of the agency architecture — the production-grade execution
layer. Where the agency's creative roles (`{AGENCY_ROOT}/roles/*.md`) make
domain decisions, the official Anthropic skills, deterministic scripts, and
Node.js tools below turn those decisions into production output.

**Binding rule:** every official skill, script, and tool listed here operates
**within** the project's `style_directive.md`. Where an official skill's defaults
(colors, fonts, motion, layout) conflict with the directive, the directive wins.
Sub-agents MUST invoke the appropriate official skill rather than hand-producing
PDFs, presentations, or production frontend code.

---

## Official Anthropic Skills

### `/frontend-design`

Production-grade frontend interfaces with bold, distinctive aesthetics.
Generates single-file HTML with embedded Tailwind v4 and custom fonts.

- **Invoked by:** UI/UX Designer (`{AGENCY_ROOT}/roles/uiux_designer.md`) and
  Asset Designer (`{AGENCY_ROOT}/roles/asset_designer.md`) for any web-facing
  deliverable.
- **Constraint:** output is clamped to `style_directive.md` tokens. Typography
  must use literal font-family names, never unresolved CSS variable references.

### `/canvas-design`

Visual art creation through design philosophy.

- **Invoked by:** Creative Director (`{AGENCY_ROOT}/roles/creative_director.md`)
  in Phase 2 to establish the brand's **visual philosophy**, and by the Asset
  Designer for poster/art assets.

### `/theme-factory`

Professional theme application with curated color/font pairings.

- **Invoked by:** Brandbook Designer (`{AGENCY_ROOT}/roles/brandbook_designer.md`)
  when PDF/PPTX deliverables are requested.

### `/pdf`

Full PDF creation, merging, watermarking, and processing using reportlab/pypdf.

- **Invoked by:** Brandbook Designer — **only** when the client explicitly
  requests a PDF. PDFs are supplements to, not replacements for, the four
  mandatory deliverables.

### `/pptx`

Professional PowerPoint creation with anti-slop design principles.

- **Invoked by:** Brandbook Designer — **only** when the client explicitly
  requests a presentation deck.

### `/web-artifacts-builder`

React/TypeScript/shadcn/ui HTML artifacts.

- **Invoked by:** UI/UX Designer for interactive prototypes and showcases, and
  Design System Expert (`{AGENCY_ROOT}/roles/design_system_expert.md`) for
  component showcases.

### `/brand-guidelines`

Anthropic's own brand styling reference. Available as a **structural model** for
how professional brand guidelines should be organized — not a template to copy
visually.

### `/ui-ux-pro-max`

UI/UX design intelligence with 50+ visual styles, 161 color palettes, 57 font
pairings, 161 product types, 99 UX guidelines, and 25 chart types.

- **Invoked by:** Creative Director in Phase 2 to select a concrete, **named**
  style archetype and palette.

---

## shadcn/ui CLI

Component source-code generator. Use over raw Tailwind divs when building
interactive HTML showcases (Button, Card, Dialog, Table, Badge, Sheet, Tabs,
Input, etc.).

```
npx shadcn@latest init -d
npx shadcn@latest add <component>
npx shadcn@latest docs
```

- **Used by:** Design System Expert to scaffold component libraries with proper
  theming. The Phase 2 `style_directive.md` must ship a Tailwind v4
  `@theme inline` block and a shadcn/ui `components.json` config so the system
  can be scaffolded directly.
- See the shadcn skill for CLI v4 commands, presets, and registry support.

---

## Execution Scripts (`{AGENCY_ROOT}/execution/`)

Deterministic Python tools. The plugin directory is read-only at runtime —
these scripts read inputs from and write outputs to `{AGENCY_STATE}` or the
project repo, never back into `{AGENCY_ROOT}`.

| Script                                          | Purpose                                                                                                                                                                                                                                         | Invoked by                      |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `{AGENCY_ROOT}/execution/generate_logo.py`      | AI logo generation via Gemini 3.1 Flash Image Preview / Imagen 4.0. 6 visual options per concept with self-improvement feedback loop. Requires `GEMINI_API_KEY`. Logs feedback to `{AGENCY_STATE}/logo_feedback_log.json` via `--log-feedback`. | Logo Designer (Phases 3 & 4)    |
| `{AGENCY_ROOT}/execution/analyze_website.py`    | Web scraping for competitor analysis.                                                                                                                                                                                                           | Researcher / Analyzer (Phase 1) |
| `{AGENCY_ROOT}/execution/fetch_images.py`       | Image sourcing from reference material.                                                                                                                                                                                                         | Asset Designer, Researcher      |
| `{AGENCY_ROOT}/execution/generate_materials.py` | Programmatic collateral/material generation.                                                                                                                                                                                                    | Asset Designer                  |
| `{AGENCY_ROOT}/execution/predict_attention.py`  | Open-source saliency model (fallback chain: UEyes → DeepGaze IIE → OpenCV) over deliverable screenshots.                                                                                                                                        | Heatmap Analyst (Phase 5)       |
| `{AGENCY_ROOT}/execution/setup_vision.sh`       | Provisions the `{AGENCY_STATE}/.venv-vision` virtualenv from `requirements_vision.txt`.                                                                                                                                                         | One-time vision setup           |

**Vision venv:** `predict_attention.py` runs inside `{AGENCY_STATE}/.venv-vision`
(resolved via the State Resolution chain), never a venv inside the plugin
directory.

---

## Node.js Design Pipeline Tools

Design pipeline utilities (installed in the project's or agency-own
`tools/node_modules`).

| Tool                         | Purpose                                                                                                  | Used by                                                                  |
| ---------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `@marp-team/marp-cli`        | Markdown → PDF/HTML slide deck generation.                                                               | Presentation Creator (`{AGENCY_ROOT}/roles/presentation_creator.md`)     |
| `svgo`                       | SVG optimization. **MANDATORY** for all vector output before delivery (`npx svgo file.svg -o file.svg`). | All roles producing SVG                                                  |
| `chroma-js` + `culori`       | Color palette generation and OKLCH manipulation.                                                         | Color System Generator (`{AGENCY_ROOT}/roles/color_system_generator.md`) |
| `sharp`                      | Image processing (resize, composite, format conversion).                                                 | Asset Designer                                                           |
| `satori` + `@resvg/resvg-js` | JSX → SVG → PNG pipeline for programmatic visual generation.                                             | Asset Designer                                                           |
| `opentype.js`                | Font glyph extraction for custom wordmark SVGs.                                                          | Logo Designer, Asset Designer                                            |

---

## Quick Invocation Reference

| Need                                       | Use                                            |
| ------------------------------------------ | ---------------------------------------------- |
| Landing page / production frontend HTML    | `/frontend-design`                             |
| Visual philosophy / poster art             | `/canvas-design`                               |
| Style archetype + palette selection        | `/ui-ux-pro-max`                               |
| Interactive prototype / component showcase | `/web-artifacts-builder`                       |
| Design system scaffold                     | shadcn/ui CLI                                  |
| PDF (only on request)                      | `/pdf` (+ `/theme-factory`)                    |
| Presentation deck (only on request)        | `/pptx` (+ `/theme-factory`) or Marp CLI       |
| Logo generation                            | `{AGENCY_ROOT}/execution/generate_logo.py`     |
| Competitor scrape                          | `{AGENCY_ROOT}/execution/analyze_website.py`   |
| Saliency / attention heatmap               | `{AGENCY_ROOT}/execution/predict_attention.py` |
| SVG optimization (mandatory pre-delivery)  | `svgo`                                         |
| Color ramp / OKLCH                         | `chroma-js` + `culori`                         |

---

## Role Roster (23 Roles) — full detail

All roles live at `{AGENCY_ROOT}/roles/<file>` (the authoritative spec for each).
SKILL.md carries a compact grouped index; this is the full per-role reference. QA
gates also dispatch as subagents (parenthesized).

### Strategy & Discovery

| Role                   | File                        | Phase | Purpose                                                                                             |
| ---------------------- | --------------------------- | ----- | --------------------------------------------------------------------------------------------------- |
| Creative Director      | `creative_director.md`      | 1, 2  | Client interrogation, brand strategy, style archetype selection, visual philosophy, style directive |
| Researcher             | `researcher.md`             | 1     | Market research, audience insights, competitive analysis                                            |
| Analyzer               | `analyzer.md`               | 1     | Deep competitive analysis, positioning mapping                                                      |
| Style Librarian        | `style_librarian.md`        | 2, 6  | Past learnings, style collision prevention, outcome recording                                       |
| Color System Generator | `color_system_generator.md` | 2     | Full palette from single accent (OKLCH ramps, neutrals, semantics, WCAG)                            |

### Creative Design

| Role                 | File                      | Phase     | Purpose                                                                                                                  |
| -------------------- | ------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------ |
| Logo Designer        | `logo_designer.md`        | 3, 4      | AI logo concepts (6 per route), SVG variants, feedback loop                                                              |
| UI/UX Designer       | `uiux_designer.md`        | 5         | Landing pages, UI mockups via `/frontend-design`                                                                         |
| Asset Designer       | `asset_designer.md`       | 5         | Social media, business cards, email signatures, collateral                                                               |
| Design System Expert | `design_system_expert.md` | 5         | Interactive design system HTML, Tailwind config, developer handoff                                                       |
| Brandbook Designer   | `brandbook_designer.md`   | 5, 6      | Brand book (HTML + MD), 10-section template                                                                              |
| Character Designer   | `character_designer.md`   | Asset     | Mascots, characters, pose sheets, multi-view, 3D-prep — asset contract + consistency gate before review                  |
| Prototype Lead       | `prototype_lead.md`       | Prototype | Product prototypes: classification, design brief before code, token compliance, regression-checked QA loop, handoff docs |

### Quality & Enforcement

| Role             | File                                       | Phase   | Purpose                                                                                                                                                                                                                               |
| ---------------- | ------------------------------------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Motion Designer  | `motion_designer.md` (`motion-designer`)   | 5       | Emil Kowalski motion within directive easing/duration; produces `motion_audit.md`                                                                                                                                                     |
| Polish Inspector | `polish_inspector.md` (`polish-inspector`) | 5       | Orchestrates the forked Impeccable suite (18 sub-skills at `{AGENCY_ROOT}/skills/`) with directive-clamped suggestions; produces `polish_report_<deliverable>.md`                                                          |
| Style Enforcer   | `style_enforcer.md` (`style-enforcer`)     | 5, 6, 7 | Automated directive compliance (colors, fonts, layout, anti-patterns) — **HARD GATE**                                                                                                                                                 |
| Taste Guardian   | `taste_guardian.md` (`taste-guardian`)     | 5       | Anti-slop evaluation against the three knobs from `visual_philosophy.md`; collision check vs `{AGENCY_STATE}/style_library.md`; feeds Visual QA                                                                                       |
| Visual QA Agent  | `visual_qa_agent.md` (`visual-qa`)         | 3, 5, 6 | Screenshot-based quality grading, accessibility audit, browser verification — **HARD GATE**                                                                                                                                           |
| Heatmap Analyst  | `heatmap_analyst.md`                       | 5       | Saliency model (`{AGENCY_ROOT}/execution/predict_attention.py`) over screenshots; verifies directive focal points win attention; produces `heatmap_report_<deliverable>.html` + overlays. **Advisory**                                |
| Persona Critic   | `persona_critic.md`                        | 5       | Project-persona vision walkthroughs (from `research_context.md` / `brand_strategy.md`); per-persona friction, drop-off, token-cited fixes; cross-references heatmap zones; produces `persona_report_<deliverable>.html`. **Advisory** |

### Presentations & Proposals

| Role                 | File                      | Phase | Purpose                                                  |
| -------------------- | ------------------------- | ----- | -------------------------------------------------------- |
| Presentation Creator | `presentation_creator.md` | 7     | Branded slide decks (Marp CLI) — pitch, reveal, review   |
| Proposal Creator     | `proposal_creator.md`     | 7     | Branded HTML proposals — scope, timeline, pricing, terms |

### Process & Improvement

| Role            | File                 | Phase | Purpose                                                                          |
| --------------- | -------------------- | ----- | -------------------------------------------------------------------------------- |
| Project Manager | `project_manager.md` | 1-7   | Task tracking, deadline management, deliverable verification                     |
| Refactor Agent  | `refactor_agent.md`  | 6     | Post-project retrospective, instruction improvement (writes to `{AGENCY_STATE}`) |

---

## Original Asset Discovery (Mandatory)

Before generating placeholder imagery or synthetic assets, every project runs asset
discovery (SKILL.md carries a pointer here):

1. **Social Media Scrape:** if the client has Instagram/Facebook/etc., fetch real
   photos (Instagram API `/api/v1/users/web_profile_info/` or equivalent) — profile
   picture (potential logo source) + latest 8-12 posts → `assets/instagram/`.
2. **Logo Extraction:** if a logo exists (profile, website, uploads), use it as the
   primary reference; recreate as SVG for the brand book; store originals in
   `assets/logo/`.
3. **Photo Integration:** real product/lifestyle photos MUST be used in landing page
   and brand book instead of placeholders (`object-fit: cover`, appropriate aspect
   ratios, descriptive `alt` on every `<img>`).
4. **URL References:** scrape/analyze any competitor/reference/inspiration links the
   client shared → screenshots in `assets/references/`.
5. **Gemini Enhancement (Optional):** for retouching/background removal/style-match,
   use the Gemini API. Never replace real photos with fully synthetic ones — enhance,
   don't replace.

**Rule:** no landing page or brand book ships with "Image Placeholder" rectangles
when real brand imagery exists. Placeholder-only deliverables are a quality failure.

## Design Quality — UI Defaults & Benchmarks

(SKILL.md carries the anti-slop standard + the MANDATORY anti-pattern table; these
are the supporting defaults and aspirational references.)

**UI Design Defaults (enforced across all deliverables):**

- shadcn/ui primitives (Button, Card, Dialog, Table, Badge, Sheet, etc.) over raw HTML
  - ad-hoc Tailwind in interactive showcases.
- Default to the brand's specified mode (light/dark); don't assume dark mode.
- Prefer zinc/neutral/slate tokens + one accent + clear borders over scattered rainbow
  accents. Let type, spacing, composition create hierarchy, not decorative elements.
- Avoid: raw `button`/`input`/`select`/`div` when shadcn primitives exist, nested
  cards in cards, multiple accent colors fighting, shipping empty/loading/error states
  without design treatment.
- Every generated HTML must include proper font loading (Google Fonts `<link>` or
  embedded `@font-face`) with literal font-family names, not CSS variable references.

**World-Class Quality Benchmarks (aspire to these):** Typography — Linear, Stripe,
Apple. Color systems — Vercel (zinc + single accent), Tailwind UI, Radix Colors
(OKLCH). Layout — Airbnb, Notion, Cal.com. Dark mode — Linear, Raycast, Warp. Brand
books — IBM Carbon, Atlassian, Uber Brand. Landing pages — Lemon Squeezy, Resend, Clerk.

---

## Completeness Matrix — QA report-content rows

SKILL.md carries the four deliverable rows + their QA-gate sequence. These are the
report-content specs each gate must satisfy (the gate roles own them):

| Artifact                            | Required Contents                                                                                                                                                                                                   | Gate                                                                                                                                |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `motion_audit.md`                   | Per-deliverable: every animation classified, justified, directive tokens cited, reduced-motion fallback confirmed                                                                                                   | Included in motion_designer output; verified by Style Enforcer                                                                      |
| `polish_report_<deliverable>.md`    | Per-deliverable: directive tokens referenced, suggestions applied (before/after), suggestions rejected (with reason), P0/P1 findings from /audit                                                                    | Included in polish_inspector output; reviewed before Style Enforcer                                                                 |
| `taste_report.md`                   | Knobs stated, anti-slop findings, craft signals present/missing, bleed-through check, collision check, Originality + Craft scores                                                                                   | Included in taste_guardian output; consumed by Visual QA                                                                            |
| `heatmap_report_<deliverable>.html` | Predictor name, knobs stated, intended focal points, top-5 AOIs per viewport, focal-point match table (rank/IoU/share/verdict), diagnoses + token-cited recommendations, cross-viewport synthesis, advisory verdict | **Advisory** — after Visual QA passes; `focal_attention_score < 0.5` alerts the originating designer but does not block delivery    |
| `persona_report_<deliverable>.html` | Personas evaluated, knobs stated, per-persona walkthrough (first impression, scan path, friction, drop-off risk, what works, token-cited fixes), cross-persona synthesis, heatmap cross-reference, advisory verdict | **Advisory** — after Visual QA passes; halts if personas are missing/under-specified (→ Creative Director); does not block delivery |

---

## Anti-Pattern Provenance (source per # in SKILL.md table)

Provenance is recorded by engagement type, not client name (client-attributed history
lives in `{AGENCY_STATE}/style_library.md`, which never leaves the operator's machine):

1 General · 2 SaaS dashboard · 3 General · 4 Fintech landing · 5 Marketing site ·
6 Fintech landing · 7 SaaS dashboard · 8 General · 9 SaaS dashboard · 10 Fintech landing
(multi-variant) · 11 Fintech landing · 12 General · 13 E-commerce · 14 Own brand ·
15 Own brand · 16 Own brand · 17 General · 18 Fintech landing · 19 Own brand ·
20 Own brand · 21 General.
