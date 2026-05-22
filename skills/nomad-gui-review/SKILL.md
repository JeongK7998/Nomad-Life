# nomad-gui-review

## Purpose

Validate the visual implementation quality of Nomad Dashboard and Quick Panels. This Skill checks layout breakage, spacing, responsive behavior, visual hierarchy, empty areas, clipping, overlap, and Design System alignment.

## Input Data

- Desktop screenshots
- Mobile screenshots
- Target URL
- Browser console output
- Changed CSS/HTML/JS files
- `docs/DESIGN_SYSTEM.md`

## Files To Read

- `AGENTS.md`
- `docs/UX_VALIDATION_AGENTS.md`
- `docs/DESIGN_SYSTEM.md`
- `web/design-tokens.css`
- Relevant files under `web/`

## Files To Write

- `reports/validation/YYYY-MM-DD-gui.md`
- `data/context/latest-validation.json` when Coordinator requests a consolidated validation context

## Available Tools

- Local files
- Browser screenshots
- CSS inspection
- Markdown
- JSON

## Procedure

1. Inspect desktop and mobile renderings of the changed surfaces.
2. Check for overlap, clipping, broken wrapping, off-screen controls, and unreadable text.
3. Check spacing, margins, empty areas, and panel density against the cockpit design direction.
4. Check whether colors, radius, shadows, and card usage follow the Design System.
5. Identify implementation artifacts such as accidental scrollbars, hidden content, or unstable layout shifts.
6. Produce prioritized findings with evidence and fix direction.

## Output Format

```json
{
  "agent": "nomad-gui-review",
  "scope": "",
  "verdict": "pass | needs_fix | blocked",
  "findings": [],
  "passes": [],
  "open_questions": []
}
```

## Forbidden

- Do not recommend marketing-style hero layouts for cockpit screens.
- Do not introduce decorative gradients, orbs, or brand assets from Wanted.
- Do not ignore Korean text wrapping.
- Do not approve a screen when primary controls overlap, clip, or become unreadable.

## Example

If the mobile Health workspace shows only one oversized review card and hides the rest of the status signals below excessive whitespace, flag it as a GUI density and spacing issue.
