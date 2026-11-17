# Completeness Matrix

100% fill across this matrix before close. **HTML-gate chain** (applies to all three
`ui/*.html` rows): `motion_designer → polish_inspector → Style Enforcer →
taste_guardian → Visual QA + Browser Verify`.

| Deliverable | Sections Required | QA Gate |
|-------------|-------------------|---------|
| `ui/landing_page.html` | Content jobs, not a section template: see "Landing page content jobs" below | HTML-gate chain |
| `ui/design_system.html` | Colors, Typography, Spacing, Buttons, Cards, Inputs, Badges, Tables, Icons | HTML-gate chain |
| `ui/brand_book.html` | Hero, Strategy, Logo (SVG), Colors, Typography, Components, AI/Chat, Motion, Do Not List, Accessibility, File Reference | HTML-gate chain |
| `brand_book.md` | Brand Story, Strategy, Visual Identity, Logo Usage, Colors, Typography, Voice, Components, Do/Don't, Assets | polish_inspector → Content Review → taste_guardian |

Each gate ALSO writes a report artifact (`<reports_dir>/<gate>_report_<name>.md` for
`motion`, `polish`, `enforcer`, `taste`, `vqa`, each with a `Verdict:` line; advisory `heatmap_report_*.html` / `persona_report_*.html`) — their
required contents are specified at **`{AGENCY_ROOT}/roles/_official_skills.md` →
"Completeness Matrix — QA report-content rows"**.

## Landing page content jobs

This file is the single source for what a landing page must contain. Gates and roles
reference it and do not restate a section list. A landing page is complete when every
job below is done by real content (TBD/TODO/Lorem ipsum count as missing). The jobs are
not sections: one section may do two jobs, and one job may be spread over several.

| Job | Done when |
|-----|-----------|
| Orientation | The first viewport says who the page is for and what the offer is |
| One primary action | A single primary action is named and reachable in the first viewport; no second action competes with it |
| Proof | Evidence is specific and sourced (a named customer, a figure with its denominator, an attributed quote); never invented |
| Mechanism | The page shows how it works: the path from the first action to the value |
| Objection handling | The top objections are answered, as an FAQ or an equivalent; taken from `<project>/conversion_brief.md` when present |
| Closing action | The primary action is offered again at the end, with the same intent |
| Legal/footer | Legal links and the footer the jurisdiction requires |

Section count, order and layout family are the designer's decision under
`<project>/conversion_brief.md` (when present) and `style_directive.md`. There are no
required card counts, step counts or footer column counts.

The Project Manager tracks this matrix. No deliverable ships with a required section or
content job missing.
