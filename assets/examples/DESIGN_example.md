---
version: alpha
name: Example / Variant A: Plain
description: Structured Clarity. Swiss grid discipline with the surface honesty of a component library. Generated from style_directive_example.md, which stays the binding contract.
colors:
  background: "#FFFFFF"
  surface: "#F6F6F7"
  border: "#E4E4E7"
  text: "#18181B"
  text-muted: "#71717A"
  primary: "#2563EB"
  success: "#16A34A"
  warning: "#CA8A04"
  danger: "#DC2626"
typography:
  display:
    fontFamily: system-ui
    fontSize: 56px
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -0.03em
  heading:
    fontFamily: system-ui
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: -0.02em
  body:
    fontFamily: system-ui
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
  data:
    fontFamily: ui-monospace
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    fontFeature: '"tnum" 1'
rounded:
  badge: 6px
  control: 8px
  card: 12px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  section: 96px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    rounded: "{rounded.control}"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
---

# Example / Variant A: Plain

How to use this file: it is the optional Google-format DESIGN.md
(https://github.com/google-labs-code/design.md) the Creative Director writes next to
`style_directive.md` when other agents or tools will read the project. Every value comes
from the directive; when the two disagree, the directive wins and this file is regenerated.
Lint with `npx @google/design.md lint DESIGN.md`.

## Overview

Structured Clarity: light-mode-first, one blue accent, hierarchy carried by type and
radius rather than colour. Surface mode: persuade.

## Colors

Neutrals do the work; `primary` is the only accent and appears once per view. Semantic
colours (`success`, `warning`, `danger`) mark state, never decoration. `text-muted` is for
secondary text only, never body copy.

## Typography

System sans for display, headings and body; system mono only for data (IDs, timestamps,
scores, prices), always with tabular figures. Three weights at most per screen.

## Layout

8px base scale (`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96`), max content width 1200px,
gutters 24px mobile and 48px desktop, 96px between sections.

## Elevation & Depth

Three levels only: `0 1px 2px rgb(0 0 0 / 0.05)`, `0 4px 12px rgb(0 0 0 / 0.08)`,
`0 12px 32px rgb(0 0 0 / 0.12)`. A surface takes a border or a shadow, never both.

## Shapes

Radius carries hierarchy: badges 6px, controls 8px, cards 12px, avatars full. Never one
radius on everything.

## Components

Primary buttons are filled `primary` with background-coloured text; every interactive
element declares hover, focus-visible and active. Cards sit on `surface` with the card
radius.

## Do's and Don'ts

- Do keep one accent; don't add a second.
- Do use skeletons or progress bars; don't use spinners.
- Don't use glass or `backdrop-filter` on cards, tables or forms.
- Don't fabricate logos for real companies.
- Don't leave an `<img>` without meaningful `alt`.
