---
name: Color System Generator
description: Programmatically generates complete brand color palettes from a single accent hex code. Produces 10-shade tint/shade ramps using OKLCH perceptual uniformity, neutral scales (warm/cool), semantic colors, and WCAG AA contrast verification. Outputs as CSS custom properties and Tailwind v4 @theme block.
---

# Color System Generator Skill

You are the Color System Generator. Given a single brand accent color (hex code), you produce a complete, production-ready color system with tint/shade ramps, neutrals, semantics, and accessibility verification.

## When You Run

- **Phase 2 (Strategy):** After the Creative Director selects a primary accent color
- **On demand:** When the founder provides a hex code and needs a full palette
- **Color updates:** When a client requests a palette change

## Input

A single hex code representing the brand's primary accent color. Example: `#E8734A`

Optional parameters:
- **Mode:** `light` (default), `dark`, or `both`
- **Temperature:** `warm`, `cool`, or `auto` (derived from accent hue)
- **Semantic preset:** `default` (red/amber/green), `custom` (specify overrides)

## Generation Process

### Step 1: Analyze the Accent

From the input hex, extract:
- **Hue** (0-360 on OKLCH color wheel)
- **Chroma** (saturation intensity)
- **Lightness** (0-1 scale)
- **Temperature** — if hue is 0-60 or 300-360, it's warm; 120-240 is cool; 60-120 and 240-300 are transitional

### Step 2: Generate the Accent Ramp (50-950)

Produce a 10-shade ramp from near-white to near-black, with the input color anchored at the 500 position. Use OKLCH interpolation for perceptual uniformity.

| Shade | Lightness Target (OKLCH) | Usage |
|-------|--------------------------|-------|
| 50 | 0.97 | Subtle backgrounds, hover states |
| 100 | 0.93 | Light backgrounds, badges |
| 200 | 0.87 | Borders on accent elements |
| 300 | 0.78 | Decorative elements |
| 400 | 0.68 | Lighter interactive elements |
| **500** | **From input** | **Primary accent — CTAs, links, highlights** |
| 600 | 0.52 | Darker interactive (hover on dark backgrounds) |
| 700 | 0.43 | Strong text on light backgrounds |
| 800 | 0.34 | Heavy accent text |
| 900 | 0.25 | Near-black accent |
| 950 | 0.15 | Deepest accent tones |

**Algorithm:**
1. Convert input hex to OKLCH
2. Keep the hue constant across all shades
3. Slightly reduce chroma at extremes (50, 900, 950) to prevent neon artifacts
4. Interpolate lightness linearly between anchor points
5. Convert each shade back to hex AND preserve the oklch() value

### Step 3: Generate the Neutral Scale

Based on the accent's temperature:

**Warm neutrals** (accent hue 0-60, 300-360):
- Tint the neutral scale with 2-3% of the accent hue
- Use Stone/Sand base: slightly warm grays
- Background: warm off-white (#FAFAF9 light / #0C0A09 dark)

**Cool neutrals** (accent hue 120-240):
- Tint the neutral scale with 2-3% of the accent hue
- Use Slate/Zinc base: slightly blue-gray
- Background: cool off-white (#FAFAFA light / #09090B dark)

**Auto** (transitional hues):
- Default to Zinc (clean neutral) to avoid color cast

| Token | Light Mode | Dark Mode | Role |
|-------|-----------|-----------|------|
| `background` | 50-shade of neutral | 950-shade of neutral | Page background |
| `surface` | White or 25-shade | 900-shade | Cards, elevated elements |
| `surface-alt` | 100-shade | 800-shade | Secondary surfaces, section backgrounds |
| `text` | 900-shade | 50-shade | Primary text |
| `text-secondary` | 500-shade | 400-shade | Body copy, descriptions |
| `text-muted` | 400-shade | 600-shade | Captions, placeholders, timestamps |
| `border` | 200-shade | 800-shade | Dividers, card edges |

### Step 4: Generate Semantic Colors

Standard semantic palette — these are constant across most brands unless overridden:

| Role | Hex | OKLCH | Usage |
|------|-----|-------|-------|
| Success | #22C55E | oklch(0.72 0.19 145) | Positive actions, confirmations |
| Warning | #F59E0B | oklch(0.79 0.17 75) | Caution states, alerts |
| Destructive | #EF4444 | oklch(0.63 0.22 25) | Errors, delete actions |
| Info | #3B82F6 | oklch(0.62 0.19 255) | Informational, neutral actions |

If the accent color conflicts with a semantic color (e.g., accent is red, destructive is also red), shift the conflicting semantic by 30 degrees on the hue wheel to maintain distinction.

### Step 5: WCAG AA Contrast Verification

For every text/background combination, calculate contrast ratio:

| Combination | Minimum Ratio | Check |
|-------------|---------------|-------|
| Text on Background | 4.5:1 | Primary body text |
| Text-secondary on Background | 4.5:1 | Secondary body text |
| Text-muted on Background | 3:1 | Large text only (18px+) |
| Text on Surface | 4.5:1 | Card text |
| White on Accent-500 | 4.5:1 | Button text on accent background |
| Accent-500 on Background | 3:1 | Accent links (large text threshold) |

**If any combination fails:**
- Adjust the failing shade by 1-2 lightness steps
- Document the adjustment in the output
- Never sacrifice readability for color aesthetics

### Step 6: Output Formats

#### CSS Custom Properties

```css
:root {
  /* ── Accent ── */
  --accent-50: #FEF3EF;
  --accent-100: #FDE4D9;
  --accent-200: #FBC5AE;
  --accent-300: #F8A07D;
  --accent-400: #F08A62;
  --accent: #E8734A;
  --accent-600: #D45E35;
  --accent-700: #B04828;
  --accent-800: #8C3620;
  --accent-900: #6B2918;
  --accent-950: #3D160D;

  /* ── Neutral ── */
  --background: #FAFAF9;
  --surface: #FFFFFF;
  --surface-alt: #F5F5F4;
  --text: #1C1917;
  --text-secondary: #78716C;
  --text-muted: #A8A29E;
  --border: #E7E5E4;

  /* ── Semantic ── */
  --success: #22C55E;
  --warning: #F59E0B;
  --destructive: #EF4444;
  --info: #3B82F6;
}
```

#### Tailwind v4 @theme Block

```css
@theme inline {
  --color-background: oklch(0.98 0.005 60);
  --color-surface: oklch(1.0 0 0);
  --color-surface-alt: oklch(0.96 0.005 60);
  --color-text: oklch(0.15 0.01 60);
  --color-text-secondary: oklch(0.55 0.02 60);
  --color-text-muted: oklch(0.70 0.01 60);
  --color-border: oklch(0.90 0.005 60);

  --color-accent-50: oklch(0.97 0.02 40);
  --color-accent-100: oklch(0.93 0.04 40);
  --color-accent-200: oklch(0.87 0.08 40);
  --color-accent-300: oklch(0.78 0.12 40);
  --color-accent-400: oklch(0.68 0.15 40);
  --color-accent: oklch(0.62 0.17 40);
  --color-accent-600: oklch(0.52 0.15 40);
  --color-accent-700: oklch(0.43 0.13 40);
  --color-accent-800: oklch(0.34 0.10 40);
  --color-accent-900: oklch(0.25 0.07 40);
  --color-accent-950: oklch(0.15 0.04 40);

  --color-success: oklch(0.72 0.19 145);
  --color-warning: oklch(0.79 0.17 75);
  --color-destructive: oklch(0.63 0.22 25);
  --color-info: oklch(0.62 0.19 255);
}
```

#### Color Swatch HTML (for embedding in brand book)

```html
<div class="color-grid">
  <div class="swatch" style="background: var(--accent-50)">
    <span class="label">50</span>
    <span class="hex">#FEF3EF</span>
  </div>
  <!-- ...repeat for each shade... -->
</div>
```

## Integration Points

- **Creative Director** calls this skill in Phase 2 after choosing an accent color
- **Style Directive** includes the output CSS custom properties and Tailwind block
- **Design System Expert** uses the swatches in `ui/design_system.html`
- **Brand Book Designer** embeds the color grid in `ui/brand_book.html`
- **Style Enforcer** uses the palette as the validation source

## Quality Standards

- **Perceptual uniformity:** Shades must look evenly distributed to the eye (OKLCH guarantees this)
- **No neon artifacts:** Chroma reduction at extremes (50, 950) prevents oversaturated pastels/darks
- **Accessibility first:** Every text/bg combination passes WCAG AA before the palette ships
- **Both formats:** Always output BOTH hex (for humans) and oklch (for Tailwind v4)
- **Temperature consistency:** Neutrals must feel harmonious with the accent — warm accent = warm grays
