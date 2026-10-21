# CSS pitfalls (design-agency, from shipped-work corrections)

Agency-authored, not upstream Impeccable. Each item cost at least one review round on a real design system (brandbook / TwoRocks / PATYX, 2026-07 to 2026-10). polish-inspector checks these on every touched file; the fix column is the default unless the directive says otherwise.

| Pitfall | What breaks | Fix |
|---|---|---|
| `grid-template-columns: repeat(n, 1fr)` with long content | `1fr` has an implicit `min-width: auto`, so a long ID or URL blows the track wider than its share and the grid overflows | `repeat(n, minmax(0, 1fr))`; add `min-width: 0` on flex children that hold text |
| Variant borders added only on some states | Toggling a 1px border shifts layout by 2px (selected tab, active chip, focused input) | Give the base a `1px solid transparent` border; variants change only `border-color` |
| Modal scrim at or below the modal's `z-index` | Scrim paints over the dialog, or the page stays clickable around it | Scrim token sits directly under the dialog token (`--z-scrim` < `--z-modal`), both above sticky headers |
| Utility class expected to override a component class | When the component stylesheet loads later, the component wins on equal specificity | Use a modifier class on the component, or a token the component reads, not a later utility |
| Sticky table header with a transparent background | Rows scroll visibly under the header | Give the sticky header the surface colour and a bottom border |
| Numbers in proportional figures | Columns of figures jitter and misalign as values update | `font-variant-numeric: tabular-nums` (Tailwind `tabular-nums`) on every compared number |
| `transition: all` | Animates layout properties and colours you did not intend; janky on large trees | List the properties: `transition: background-color 150ms, color 150ms` |
| `100vh` on mobile | The browser chrome hides the bottom of the section | `100dvh` (or `min-height` with `svh`) |
| Scrollbar appears on data refresh | Content width changes by the scrollbar width, the table shifts | `scrollbar-gutter: stable` on the scrolling container |
| Popover inside an `overflow: hidden` / scrolling panel | The popover is clipped | Render it in a portal or the top layer (popover API / anchor positioning) |
| Documented values that were never computed | A design-system page states a contrast ratio, grid width or breakpoint that the CSS does not produce | Compute it (script or browser) before writing it into docs |
