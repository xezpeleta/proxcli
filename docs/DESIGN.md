---
name: proxcli
version: "1.0"
colors:
  primary: "#0F172A"
  secondary: "#334155"
  tertiary: "#3B82F6"
  on-tertiary: "#FFFFFF"
  surface: "#F8FAFC"
  surface-variant: "#E2E8F0"
  on-surface: "#1E293B"
  border: "#CBD5E1"
  muted: "#94A3B8"
  success: "#10B981"
  warning: "#F59E0B"
  error: "#EF4444"
  code-bg: "#1E293B"
  code-fg: "#E2E8F0"
typography:
  heading:
    fontFamily: "Inter, system-ui, sans-serif"
    fontWeight: 700
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontWeight: 400
  mono:
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace"
    fontWeight: 400
  label-caps:
    fontFamily: "Inter, system-ui, sans-serif"
    fontWeight: 600
    letterSpacing: "0.05em"
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  "2xl": 48px
  "3xl": 64px
  "4xl": 96px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.lg}"
    typography: "{typography.label-caps}"
  button-primary-hover:
    backgroundColor: "#2563EB"
  code-block:
    backgroundColor: "{colors.code-bg}"
    textColor: "{colors.code-fg}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  hero-section:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-tertiary}"
  card:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
---

## Overview

**proxcli** is a developer-first CLI tool for Proxmox VE infrastructure.
The visual identity balances terminal minimalism with modern SaaS polish —
dark slate foundation, a single electric-blue accent, and crisp monospaced
code surfaces.

The brand sits at the intersection of **infrastructure professionalism**
and **developer joy**. Clean, confident, utilitarian — but never cold.
The blue accent (`#3B82F6`) provides the energy and forward momentum
of a tool that makes infrastructure feel fast, responsive, and under
control.

## Colors

- **Primary (`#0F172A`):** Deep navy-slate. Used for hero sections,
  the nav bar, and as a grounding dark surface. Conveys infrastructure
  seriousness and reliability.
- **Secondary (`#334155`):** Medium slate. Used for subheadings,
  muted text on light backgrounds, and secondary UI chrome.
- **Tertiary (`#3B82F6`):** Electric blue. The sole interactive accent —
  buttons, links, active states, code highlights. High-energy without
  being aggressive. Hover darkens to `#2563EB`.
- **Surface (`#F8FAFC`):** Near-white with a hint of cool gray. Primary
  page background. Softer than pure white for long-form reading.
- **Surface variant (`#E2E8F0`):** Light gray for alternating sections,
  card borders, and subtle visual separation.
- **Code background (`#1E293B`):** Dark slate for code blocks and
  terminal emulation. Paired with off-white `#E2E8F0` for code text.

## Typography

- **Headings:** Inter, bold weight. Clean and geometric for section
  titles. Large sizes (`4xl`, `3xl`, `2xl`) for hero and section heads.
- **Body:** Inter, regular weight. Optimized for screen reading at
  `16px` base size (1rem).
- **Mono:** JetBrains Mono for all code, terminal output, and
  command examples. Fallback stack: Fira Code → Cascadia Code → monospace.
- **Label/Caps:** Inter Semibold with 0.05em letter-spacing for button
  text, badges, and navigation items.

## Layout

- **Max content width:** 1280px centered, with generous horizontal
  padding (`2xl`) on wider screens.
- **Sections stack vertically** with `3xl` or `4xl` spacing between them.
- **Two-column grids** for feature cards, comparison tables, and
  use-case highlights.
- **Terminal/Code blocks** are full-width within content, with
  `lg` rounded corners and `lg` internal padding.

## Elevation & Depth

- Flat design with minimal shadow usage. Cards use a 1px border
  instead of box-shadow to maintain a crisp, editor-like aesthetic.
- Code blocks sit on the dark `code-bg` surface with no shadow —
  they feel "cut into" the page.
- Only the sticky navigation bar gets a subtle shadow on scroll.

## Shapes

- All interactive elements use `md` border radius (8px).
- Code blocks and terminal surfaces use `lg` (12px).
- Buttons use `md` (8px) — rounded enough to feel modern but not pill-shaped.
- Full-radius (`full`) reserved for badges and tags.

## Components

- **button-primary:** Electric blue background with white text, Inter semibold.
  Hover darkens to `#2563EB`. Used for primary CTAs.
- **code-block:** Dark slate surface (`#1E293B`) with off-white monospaced text.
  Used for all command examples, terminal output, and YAML samples.
- **hero-section:** Full-width dark slate background with centered white text.
  Features the proxcli logo/title, a one-line value prop, and a "Get Started"
  button.
- **card:** White surface with a subtle border, rounded corners, and internal
  padding. Used for feature tiles and documentation sections.

## Do's and Don'ts

### Do
- Use the single accent (`#3B82F6`) sparingly for interactive elements only
- Keep code examples concise — show the command and its output
- Use Inter for all prose, JetBrains Mono for all code
- Maintain generous whitespace around sections for readability
- Use the dark hero to ground the page immediately on landing

### Don't
- Don't introduce additional colors beyond the defined palette
- Don't use box-shadows on cards — use borders instead
- Don't use the accent color for non-interactive text
- Don't clump multiple code blocks without prose between them
- Don't use the dark surface (`#0F172A`) for large text blocks —
  it's reserved for hero sections and navigation
