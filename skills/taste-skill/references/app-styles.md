<!-- Source: https://github.com/Leonxlnx/taste-skill/blob/63aba5f43b5056758b15bbe7d683da8c86a7a7ad/skills/taste-skill/library/app.json (v2.1.3, commit 63aba5f43b5056758b15bbe7d683da8c86a7a7ad) -->
<!-- License: MIT, copyright leonxlnx; vendored into design-agency v0.5.0 -->
<!-- Derived reference: compact markdown digest of library/app.json `styles` (values copied verbatim; JSON is upstream's source of truth) -->

# App styles (taste-skill app library)

Digest of the 7 app-screen styles (directions) in upstream `library/app.json` (library version 1). Upstream description: App-screen library for tasteskill: styles (directions), shells and screen patterns, distilled from the study of 23 desktop product screens (17 light, 6 dark, 17 products) chosen by the owner. Every number is a measurement from the study or a median over it, except where a note says a value was moved for contrast or for the house palette bans. Reference products are not named; the screenshots stay private.

## Overview

| id | Name | Theme | Ground / Surface | Ink (text / muted) | Accent | Chart | Type | Density | Shell | Colour budget |
|---|---|---|---|---|---|---|---|---|---|---|
| `achromatic-ledger` | Achromatic ledger | light | `#f8f8f8` / `#ffffff` | `#0a0a0a` / `#6b6b6b` | `#141414` | `#141414`, `#8a8a8a`, `#1d5fbf` | Geist + Geist Mono, for IDs and keys only; body 14px, title 24px, KPI 30px; weights 400/500/700 | sparse (row 44px, ctrl 36px) | open-plane | under 1% coloured pixels; the chrome is ink, the one chart hue goes on the main data element, and the only other hue is a small change signal |
| `framed-sheet` | Framed sheet | light | `#f9fbfc` / `#ffffff` | `#131416` / `#5d5f60` | `#1b6c80` | `#1b6c80`, `#2f70bb`, `#a86f0c` | IBM Plex Sans + IBM Plex Mono, for IDs and keys only; body 14px, title 22px, KPI 28px; weights 400/500/600 | medium (row 48px, ctrl 32px) | framed-sheet | under 3%; the brand shrinks to the logo and a 2px tab underline, the data carries the chroma |
| `accent-ladder` | Accent ladder | light | `#f9fafb` / `#ffffff` | `#111827` / `#5f6672` | `#b8336a` | `#b8336a`, `#6b7280`, `#d4618f` | DM Sans; body 14px, title 32px, KPI 24px; weights 400/500/600/700 | sparse (row 45px, ctrl 32px) | open-plane | 3-10%, nearly all of it as pale tints of the one hue |
| `editorial-greeting` | Editorial greeting | light | `#ffffff` / `#f9f9f9` | `#1f201d` / `#636361` | `#1b6e66` | `#1f201d`, `#1b6e66`, `#8c8c88` | Instrument Sans + Instrument Serif, for the greeting only; body 14px, title 48px, KPI 32px; weights 400/500/600 | sparse (row 63px, ctrl 38px) | open-plane | under 2% for the accent; tonal panels carry the structure |
| `pastel-consumer` | Pastel consumer | light | `#f3f5f7` / `#ffffff` | `#1b1d1f` / `#5c6064` | `#1d5fd6` | `#1d5fd6`, `#b45309`, `#2a8798` | Manrope; body 16px, title 28px, KPI 32px; weights 400/500/600 | medium (row 72px, ctrl 40px) | open-plane | 5-8%, as pale tiles and data marks |
| `true-black-flat` | True-black flat | dark | `#000000` / `#111111` | `#ffffff` / `#b4b4b4` | `#c6f24e` | `#c6f24e`, `#e6e6e6`, `#6b6b6b` | Inter; body 14px, title 20px, KPI 24px; weights 400/500/600 | medium (row 80px, ctrl 36px) | ruled-t-frame | at or under 3%; the accent never touches buttons, tabs or nav |
| `data-terminal` | Data terminal | dark | `#171719` / `#131217` | `#ffffff` / `#8a8c92` | `#4a8ad6` | `#f2f2f3`, `#e5566f`, `#4a8ad6` | Public Sans; body 13px, title 26px, KPI 20px; weights 400/500/600/700 | dense (row 42px, ctrl 34px) | icon-rail | under 3%; the accent is never more than a 1px line |

## Per-style notes

### `achromatic-ledger` - Achromatic ledger (light)

- **Idea:** The chrome holds no colour at all; money and counts are set in ink, the one chart hue marks the screen's main data element, and the only other hue is a small signal where a figure changed.
- **Suits:** finance, commerce, devtools, support, report, workspace, builder
- **Shell:** open-plane (alternatives: icon-rail, no-sidebar)
- **Signature:** No brand colour anywhere in the chrome: the one primary action is near-black (a grey pill, #e5e5e5, is the secondary), the main data element (today's series, the booked bars, the current period) takes the one chart hue, #1d5fbf, and everything else is drawn in ink with the comparison or the part after the cursor in grey, zero balances are set in grey, and the only hue on the screen is a small triangle or a short coloured number where a figure changed.
- **Basis:** 4 screens: a seller home, a per-agent insights page, a generated report, a settings page with usage numbers
- **Colour budget:** under 1% coloured pixels; the chrome is ink, the one chart hue goes on the main data element, and the only other hue is a small change signal

**Tokens**

| Token | Value |
|---|---|
| ground | `#f8f8f8` |
| surface | `#ffffff` |
| raised | `#eeeeee` |
| border | `#e6e6e6` |
| rule | `#f0f0f0` |
| control | `#d4d4d4` |
| text | `#0a0a0a` |
| muted | `#6b6b6b` |
| accent | `#141414` |
| positive | `#2e7d32` |
| negative | `#c4242a` |
| warning | `#92400e` |
| chart | `#141414`, `#8a8a8a`, `#1d5fbf` |
| pill.positive (bg / ink) | `#dcfae5` / `#04250e` |
| pill.negative (bg / ink) | `#ffedea` / `#831c1e` |
| pill.warning (bg / ink) | `#fffbeb` / `#92400e` |
| pill.neutral (bg / ink) | `#eeeeee` / `#3d3d3d` |
| radius.card | 8px |
| radius.control | 6px |
| density | `sparse` |
| rowHeight | 44px |
| sidebarWidth | 256px |
| gap | 12px |
| pad | 24px |
| controlHeight | 36px |

**Type**

- Family: Geist; second: Geist Mono, for IDs and keys only; fallback: Inter, system-ui, sans-serif
- Sizes: title 24px, section 16px, kpi 30px, body 14px, small 12px
- Weights: 400, 500, 700
- Note: 700 is for money figures only; every other number is 400-500.

**Identity moves (make it the product's own)**

- A ground from the product's world in place of #f8f8f8, one level off white and low in chroma: a stone (#f4f3f1) for a bakery or a shop, a sage (#f2f5f2) for a garden or a greenhouse, a blue-grey (#f2f4f7) for a ledger or a meter. Cards stay white; a warm tint stays under the cream check (saturation under about 15%).
- The one chart hue (#1d5fbf, or the brand's own hue at 3:1 or more on white) on the screen's main data element: today's line, the booked bars, the current period's column, the margin that breaks. The chrome stays ink and the hue stays under 1% of the screen.
- Every figure in Geist Mono, as the style's decision, so money and counts read as a ledger's columns while the text stays Geist. Lint and the inspector flag mono; give the reason in the report.

**Avoid**

- a brand-coloured primary button
- tinted cards or tinted KPI tiles
- a coloured chart where one series in ink says it
- bold on anything but money
- a chart with no y-scale (the study's one example of this look hid magnitude behind hover and was flagged)
- a grey pill as the only button for the screen's main job: in testing an Approve repeated in grey on every row left the screen without a primary

**Notes**

The studied screens of this kind used 11-12px card radii, which §9.4 counts among the rare middle values; the library sets the tight pair (8 and 6) so the style lands on the bimodal rule. After testing, the chart hue moved from an unused third series colour onto the main data element: a screen whose only hue was a delta read as a kit.

### `framed-sheet` - Framed sheet (light)

- **Idea:** The app chrome is one tinted L-shaped frame; the work sits on a white sheet with a hairline edge and soft corners, so depth comes from a single tone step and no shadow.
- **Suits:** analytics, devtools, builder, smb-admin, support, commerce, report
- **Shell:** framed-sheet
- **Signature:** One tinted frame holds the sidebar and the 48px top bar with no rule between them; the page is a white sheet inset 8px from the window's right and bottom edges, with a 1px edge, 16px corners and no shadow. The active tab is a 2px underline in ink or the accent; everything else in the chrome is grey.
- **Avoid:** a border between the sidebar and the top bar; a shadow under the sheet; cards whose border is heavier than the sheet's (#cdcfcf on cards read as heavy in the study); a fourth nesting level: frame, sheet and card are enough; different gutters for the KPI row and the chart row (20 against 24 was flagged)
- **Notes:** The study's second data hue in this style was an orange (#e88e46) that falls inside the house terracotta range; the third chart colour here is an amber moved out of that range and darkened to 3:1 on white.

### `accent-ladder` - Accent ladder (light)

- **Idea:** One brand hue at full strength only on small marks, and its pale tints doing all the area work: the active nav row, a plan card, badges and progress tracks.
- **Suits:** creator, smb-admin, community, analytics
- **Shell:** open-plane (alternatives: ruled-t-frame)
- **Signature:** The full hue goes only on small marks: the one filled-button style, the data series and the active nav icon. Its 50-200 tints carry every area: the active nav row (tint fill with the dark ink of the hue), the plan or trial card, badges and progress tracks. The primary action may instead be near-black, as on the study's newsletter home.
- **Avoid:** the full hue on large areas; a second accent family (four families on one screen was flagged in the study); a gradient on the trial chip or upgrade button; a left accent bar on the active nav row on top of the tint (seen once in 23 screens); violet or indigo
- **Notes:** All three studied screens of this kind used violet, purple or pink as the one hue. The move does not depend on the hue, so the house's violet and indigo ban holds and the library deals a raspberry instead.

### `editorial-greeting` - Editorial greeting (light)

- **Idea:** A personal or team home that opens with a typeset greeting in a centred column; every number below it is set at regular weight on tonal panels.
- **Suits:** workspace, creator
- **Shell:** open-plane (alternatives: framed-sheet)
- **Signature:** The greeting is the h1, in a centred 1100px column on a real 12-column grid (77px columns, 16px gutters), with spans that change by row but share column lines (3/3/3/3, then 9/3, then 6/6, so every internal edge meets one above it). Every figure below is set at regular weight on tonal panels, one layer each: a panel one step off white holds its title and its content directly; a white inner card is used once, for the main chart.
- **Avoid:** an emoji in the greeting; a tracked uppercase date above the greeting (put the date after it or in the grey line below); a 624-864px column on a desktop screen (both were flagged as wasted width); a tray around every card (a grey panel with a white card 6px inside it, on every block, read as a bento template in testing); red as the accent: in testing red marked a record week of upgrades and read as an alarm; red is for the failing fact only
- **Notes:** One studied screen set its greeting in a serif at 48/700 and its counts in a mono; the other set the greeting at 24/400 in the sans. The red is the second screen's chart red moved two degrees of hue out of the house terracotta range. After testing, the studied red accent was replaced by a deep teal: red on good news read as an alarm.

### `pastel-consumer` - Pastel consumer (light)

- **Idea:** Categories are coded by pale tints whose ink is the dark of the same hue, all under one large radius, and each headline sum sits inside the card that explains it.
- **Suits:** wallet, finance
- **Shell:** open-plane (alternatives: icon-rail)
- **Signature:** Pale category tiles with the dark of their own hue as ink (#dcf1ff with #0a3a80), one large radius (20px on cards, stepping down to 10, 8 and 5 inside), and quiet money polarity: income green with a plus sign, spending in ink, no red on ordinary outgoings. Tints go on small tiles, avatars and chips; a panel that holds a list stays white. When the product has people (two partners, a family), each gets one hue, at least 60 degrees from the next.
- **Avoid:** a gradient balance card; two data palettes on one page (flagged in the study); red on every outgoing amount; a 624px phone-width column on a desktop screen (flagged as a stretched phone screen); a KPI strip on top: the sums belong in their cards; whole panels tinted per person or category beside white cards (two surface languages on one screen)
- **Notes:** The two studied screens used a pure #0000ff and an indigo #4723f5 as their brand colour, and pastels such as #7cbecf that fall under 3:1 on white. The library uses a cobalt that reads as blue rather than indigo, and data colours darkened to at least 3:1 on the card.

### `true-black-flat` - True-black flat (dark)

- **Idea:** Night mode on true black: sidebar, top bar and page share one ground, elevation is a lightness step alone, and colour is confined to data marks.
- **Suits:** community, creator, markets
- **Shell:** ruled-t-frame (alternatives: no-sidebar)
- **Signature:** Elevation by lightness alone (#000 ground, #111 card, #2a2a2a nested panel) with no borders or shadows on cards; the active nav item is marked only by its label going from #bbb to #fff; the primary control is made primary by inversion, a white 36px pill with black text.
- **Avoid:** a navy or slate dark theme; glow, neon borders or shadows; a hue per chart (five hues across four charts was flagged); the accent on buttons, tabs or nav; a 64px top bar left empty across most of its width (flagged twice)
- **Notes:** The studied screens of this kind used a violet-magenta (#dd6cff) and an orange (#ff5500) as their one data hue. The library deals a lime, which keeps the move and stays clear of the violet ban; because the lime is a yellow-green, it is also the positive colour (a second, mint green beside it read as two greens). The greys are #b4b4b4 for secondary text and #949494 for meta, 32 levels apart rather than the 20 of the measured #aaa and #969696, which read as one grey; #949494 still holds 4.5:1 on the #2a2a2a nested panel.

### `data-terminal` - Data terminal (dark)

- **Idea:** A research or monitoring screen read in long sessions: cards darker than the ground, tabular digits that stack, signs instead of colour, and every selection marked by the same 1px accent line.
- **Suits:** markets, devtools
- **Shell:** icon-rail
- **Signature:** Every selection (tab, toggle, range, nav item) is a 1px accent line exactly as wide as its label, placed on the nearest existing edge; numbers stay white or grey and carry their sign in the text ('+$24,000,000').
- **Basis:** 1 screen: a stock research view. Keep it narrow.
- **Colour budget:** under 3%; the accent is never more than a 1px line

**Tokens**

| Token | Value |
|---|---|
| ground | `#171719` |
| surface | `#131217` |
| raised | `#212023` |
| border | `#222224` |
| rule | `#1b1a1f` |
| control | `#3a3a3e` |
| text | `#ffffff` |
| muted | `#8a8c92` |
| accent | `#4a8ad6` |
| positive | `#44a282` |
| negative | `#e5566f` |
| warning | `#d9a441` |
| chart | `#f2f2f3`, `#e5566f`, `#4a8ad6` |
| pill.positive (bg / ink) | `#1b2828` / `#5fc39c` |
| pill.negative (bg / ink) | `#2c1a20` / `#e5566f` |
| pill.warning (bg / ink) | `#2a2416` / `#d9a441` |
| pill.neutral (bg / ink) | `#212023` / `#bdbdc0` |
| shadow | `0 12px 28px rgba(0,0,0,.2)` |
| radius.card | 6px |
| radius.control | 999px |
| density | `dense` |
| rowHeight | 42px |
| sidebarWidth | 50px |
| gap | 24px |
| pad | 32px |
| controlHeight | 34px |

**Type**

- Family: Public Sans; second: none; fallback: Inter, system-ui, sans-serif
- Sizes: title 26px, section 20px, kpi 20px, body 13px, small 12px
- Weights: 400, 500, 600, 700
- Note: Section titles 20/400 in the muted grey; card titles 16/600; tabular figures everywhere.

**Identity moves (make it the product's own)**

- Every figure in a monospace as the style's decision (IBM Plex Mono or JetBrains Mono for each price, count and time, digits that stack), with the text in Public Sans. Lint and the inspector flag mono; give the reason in the report.
- The one accent line from the product's world in place of the dealt blue (the exchange's or the team's hue): still the only selection mark, never violet or indigo.
- A signature of the market or the system as the lead: an order book's depth as two mirrored bar lists, an incident as a minute-by-minute strip, a region map with the list beside it.

**Avoid**

- filled pill tabs or a coloured segmented control
- a chart with no scale and no dates (the studied screen had none and was flagged)
- tertiary text under 4.5:1 (#4c4c4f read at about 2:1 in the study)
- lighter cards with borders and a glow
- green and red on every number; the one column whose job is "what moved today" and a negative headline figure may carry the polarity colours

**Notes**

The studied screen's muted grey #82848a and red #d4405d were lifted to #8a8c92 and #e5566f so text passes 4.5:1 on the card. Its card list rows sit on a 28px pitch and its table rows on 42px.
