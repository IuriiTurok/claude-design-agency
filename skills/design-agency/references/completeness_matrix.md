# Completeness Matrix

100% fill across this matrix before close. **HTML-gate chain** (applies to all three
`ui/*.html` rows): `motion_designer → polish_inspector → Style Enforcer →
taste_guardian → Visual QA + Browser Verify`.

| Deliverable | Sections Required | QA Gate |
|-------------|-------------------|---------|
| `ui/landing_page.html` | Nav, Hero, Trust, Benefits, How-it-works, Features, Testimonial, CTA, Footer | HTML-gate chain |
| `ui/design_system.html` | Colors, Typography, Spacing, Buttons, Cards, Inputs, Badges, Tables, Icons | HTML-gate chain |
| `ui/brand_book.html` | Hero, Strategy, Logo (SVG), Colors, Typography, Components, AI/Chat, Motion, Do Not List, Accessibility, File Reference | HTML-gate chain |
| `brand_book.md` | Brand Story, Strategy, Visual Identity, Logo Usage, Colors, Typography, Voice, Components, Do/Don't, Assets | polish_inspector → Content Review → taste_guardian |

Each gate ALSO writes a report artifact (`motion_audit.md`, `polish_report_*.md`,
`taste_report.md`, advisory `heatmap_report_*.html` / `persona_report_*.html`) — their
required contents are specified at **`{AGENCY_ROOT}/roles/_official_skills.md` →
"Completeness Matrix — QA report-content rows"**.

The Project Manager tracks this matrix. No deliverable ships without all sections.
