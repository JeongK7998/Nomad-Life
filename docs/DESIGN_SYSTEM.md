# Nomad Life Design System

Nomad Life uses a design system adapted from the local `Design System/` reference. The reference is Wanted-inspired, but Nomad Life must remain its own product.

## Design Position

```txt
Wanted-inspired, Nomad-owned.
Korean-first.
Calm operational cockpit.
Semantic tokens over raw colors.
Local-first product UI, not marketing UI.
```

The interface should feel like a quiet operating room for nomad life: fast to scan, low drama, and useful every day.

## What To Reuse

- Pretendard as the primary font family
- Semantic color token structure
- 4pt spacing grid
- 8px radius for controls
- 12px radius for compact cards and panels
- 16px radius only for larger hero-like panels
- 1px border before shadow
- Primary blue for CTA, active state, and strong product moments only
- Compact badges, chips, inputs, buttons, cards, and progress bars
- `currentColor` SVG icon strategy

## What Not To Reuse

- Wanted logos and product marks
- Wanted career/recruiting-specific copy
- Job-card patterns as literal UI
- Decorative gradients on large surfaces
- Multiple accent colors competing in one screen
- Shadows on every card
- Marketing hero layouts as the main cockpit

## Tokens

Product code should use semantic tokens from `web/design-tokens.css`.

Important groups:

- `--primary-normal`, `--primary-strong`
- `--label-normal`, `--label-neutral`, `--label-alternative`
- `--background-normal`, `--background-alternative`, `--background-elevated`
- `--line-normal`, `--line-neutral`, `--line-alternative`
- `--status-positive`, `--status-cautionary`, `--status-negative`
- `--space-*`
- `--radius-*`
- `--shadow-emphasize-*`

Raw atomic colors should stay inside token files unless there is a deliberate one-off visualization need.

## Typography

Use Pretendard for Korean and English. UI text should generally be 500 weight or stronger.

Recommended use:

- Page title: 24-32px, 700
- Section heading: 20-22px, 600-700
- Card title: 16-18px, 600-700
- Body: 15-16px, 500
- Label: 13-14px, 500-600
- Caption: 11-12px, 500

Numbers in dashboard cards should use `font-variant-numeric: tabular-nums`.

## Layout

- Use a persistent sidebar on desktop.
- Use a single-column stacked layout on mobile.
- Keep section padding around 20-24px.
- Use 12-16px gaps inside panels.
- Avoid nested cards unless the inner card is a repeated item.
- Prefer full-width operational sections over decorative landing-page sections.

## Cockpit Information Architecture

The cockpit uses workspace navigation instead of one long stacked page.

Current workspaces:

- Today: Coordinator summary, focus, let-go, missions, and life balance
- Capture: Quick Capture, inbox sync, and recent capture review
- Health: readiness, workout candidates, muscle schedule heatmap, exercise progress, and quick workout detail entry
- Activity: activity allocation and candidate sessions
- Finance: imported expense summaries, budget pressure, and read-only spending signals
- Context: local app context such as Calendar and Notes
- Council: Agent Council, notification candidates, and approval actions
- Reports: Hermes draft and later daily/weekly reports

The sidebar switches workspaces. Only one workspace should be visible at a time so the cockpit remains operational rather than an infinite scroll of modules.

## Components

### Buttons

Primary buttons use `--primary-normal`, white text, 40-48px height, 8px radius, and 600-700 weight.

Secondary buttons use a neutral fill or 1px outline.

### Inputs

Inputs use a white or elevated background, 1px neutral border, 8px radius, and blue focus ring.

### Cards

Cards use `--background-normal`, `--line-neutral`, 12px radius, and no shadow by default.

### Badges

Badges are compact, 18-24px height, 4-999px radius depending on use. Status color should be rare and meaningful.

### Charts

Charts should use restrained color. Primary blue can represent active/focus state. Neutral fills should carry most of the visual weight.

## Current Cockpit Mapping

- Quick Capture: input panel with primary CTA
- Today Dashboard: operational summary with three compact columns
- Agent Council: repeated analysis cards
- Life Dashboard: horizontal score bars before radar implementation
- Action Center: approval-state list

## Governance

When the visual language changes, update this file and the web token file together. If a proposed design makes the product feel like a marketing site, career app, or generic SaaS dashboard, pause and review against `AGENTS.md`.
