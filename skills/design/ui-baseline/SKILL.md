---
name: ui-baseline
description: "Theme-agnostic web UI baseline covering layout hierarchy, typographic contrast, spacing grid, radius geometry, progressive interactions, desktop menus, and real-browser render verification. Use standalone when building, restyling, or polishing web pages, components, or typography (e.g., UI 基线, 默认设计规范), and ALWAYS load alongside the `ui` skill whenever `ui` is triggered. Not for backend logic, data pipelines, or print/PDF document typesetting."
---

# UI Baseline

## Scope and Precedence

- **Theme-agnostic**: This baseline governs universal layout structure, typographic hierarchy, spatial rhythm, interaction quality, and render verification. It does not prescribe color schemes, font families, or icon libraries (leave those to project conventions or the `ui` skill).
- **Precedence**: Applies standalone or alongside the `ui` skill. When a repository already defines a design system that conflicts with specific numeric defaults (such as corner radius range or type scale), follow the repository's tokens while preserving structural restraint, interaction stability, and real-browser render verification.

## Layout and Information

- **No nested containers**: Avoid boxes inside boxes, nested cards, redundant bordered wrappers, and decorative dividers.
- **Minimal UI copy**: Omit decorative or marketing taglines, redundant subtitles, cluttered secondary badges/labels, and explanatory prose narrating the interface. Keep only functional microcopy that prevents user error or communicates state (e.g., form validation errors, empty-state prompts, destructive action confirmations).
- **Hierarchy through structure**: Distinguish content hierarchy using typographic alignment, spacing, and type scale rather than borders or explanatory text.

## Typography and Contrast

- **Weight and contrast**: Give headings heavier weight and higher contrast against the background; give body and secondary text lighter weight and lower contrast (applies to both light and dark themes).
- **Size and weight**: Default section and component headings to `18px` bold (weight `600` or `700`), scaling page-level main headings up as hierarchy requires. Use `16px` or `14px` (weight `400` or `500`) for body text; secondary metadata may step down as needed, never below `12px`.
- **Numerals and icon-text alignment**: Use tabular numerals (`font-variant-numeric: tabular-nums`) for dynamic or column-aligned numbers such as tables, metrics, prices, and timers. Vertically center icons with single-line text to avoid baseline misalignment.

## Whitespace, Grid, and Radius

- **Generous whitespace**: Set component padding and section margins to roughly `1.5×` typical page density, snapped to the `4px` grid; prefer open space over crowding. Keep proximity clear (tighter spacing within related elements, wider spacing between distinct groups), and scale proportionally tighter in high-density views such as data tables and toolbars.
- **4px spacing grid**: Every spacing value (`margin`, `padding`, `gap`) must be an integer multiple of `4px`, with no exceptions.
- **Corner radius**: Unless the active theme explicitly calls for sharp corners, default to radii between `8px` and `40px` scaled by component size and hierarchy (smaller radii for compact buttons and inputs; larger radii for cards, panels, and dialogs). Keep nested controls or media inside cards and dialogs concentric (`outer radius ≈ inner radius + padding`).

## Interaction and Desktop Menus

- **Reveal controls on intent**: Keep secondary action buttons hidden at rest; reveal them when the user hovers, focuses, scrolls close to, or begins interacting with the region.
- **Desktop multi-level menus**: Implement an open delay, a close delay, and a safe triangle together. When the pointer moves from parent menu A toward submenu B, form a triangle from the current pointer coordinates to the top and bottom edge endpoints of submenu B; while the pointer remains inside this triangle, keep submenu B open and defer switching to other menu items crossed along the path.

## Render Verification

- **Verify actual rendered output**: Judge by the actual rendered visuals in the browser, not by source code or computed CSS values. Check alignment, line wrapping/truncation, whitespace rhythm, stacking occlusion/overflow clipping, and key interactive states across at least standard desktop and narrow/mobile viewports.
- **Report verification gaps honestly**: If the current environment cannot render or inspect the live page in a browser, explicitly state which visual checks remain unverified; never fabricate visual verification results.
