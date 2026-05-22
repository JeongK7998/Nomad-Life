# UX Validation Agents

Nomad Life Dashboard and Quick Panels should be checked by stable validation agents instead of one-off ad hoc review prompts. These agents are Hermes Skills that Coordinator can call whenever the UI, dashboard data, or review content changes.

They do not replace product judgment. They create repeatable findings that help Coordinator decide what should be fixed before the user relies on the dashboard.

## Operating Model

```txt
Implementation change
        ↓
Validation setup / sandbox fixture
        ↓
User-visible preview when needed
        ↓
Local/Hosted Dashboard render
        ↓
Validation Skills
        ↓
Findings JSON / Markdown summary
        ↓
Coordinator prioritization
        ↓
Fix / defer / document
```

## Run Modes

Validation should be staged so synthetic data never mixes with real Nomad Life records and the user can inspect the flow before treating findings as release evidence.

```bash
npm run validate:setup
```

Prepares `data/_validation_sandbox` only. It does not run browser scenarios.

```bash
npm run validate:serve
```

Serves the sandbox dashboard for manual preview. Use the printed local URL to inspect the fixture before running actual validation.

```bash
npm run validate:preview
```

Runs the validation scenarios in a visible browser with slower steps so the user can watch the flow.

```bash
npm run validate
```

Runs the headless validation suite and writes reports/screenshots.

The three validation agents are:

- `nomad-ux-flow-review`: checks whether the whole user journey is understandable and usable.
- `nomad-gui-review`: checks visual layout, spacing, responsive breakage, empty areas, and implementation artifacts.
- `nomad-review-value-review`: checks whether review content is concise, non-repetitive, information-dense, and useful at a glance.

## When To Run

Run all three when:

- A Dashboard workspace is added or substantially redesigned.
- Quick Capture, Nomad Quick PWA, or workout/detail input flow changes.
- Coordinator Brief, Weekly Review, Agent Council, or review card content structure changes.
- A hosted deployment is prepared for real iPhone/iPad use.

Run a focused subset when:

- Only navigation or task flow changed: run `nomad-ux-flow-review`.
- Only CSS/layout/responsive behavior changed: run `nomad-gui-review`.
- Only review text, dashboard copy, Agent Council summaries, or data density changed: run `nomad-review-value-review`.

## Review Inputs

Preferred inputs:

- Local URL or hosted URL
- Target workspace names
- Screenshots across desktop and mobile
- Browser console errors
- `dashboard/*.json`
- Relevant reports under `reports/`
- Changed web files
- User scenario being tested

Minimum useful input:

- A URL or screenshot
- The user scenario
- The changed dashboard/review data

## Standard Output

Each validation agent should produce concise findings in this shape:

```json
{
  "agent": "nomad-gui-review",
  "scope": "Health workspace mobile review",
  "verdict": "pass | needs_fix | blocked",
  "findings": [
    {
      "severity": "P0 | P1 | P2 | P3",
      "title": "Short issue title",
      "evidence": "What was observed",
      "impact": "Why it matters for the user",
      "recommendation": "Concrete fix direction"
    }
  ],
  "passes": [
    "Short note on what works well enough"
  ],
  "open_questions": []
}
```

Severity:

- `P0`: blocks core use or makes data/action meaning unsafe.
- `P1`: clearly harms real use and should be fixed before release.
- `P2`: noticeable quality issue that should be scheduled.
- `P3`: polish or optional improvement.

## Agent Responsibilities

### nomad-ux-flow-review

Focus:

- Can the user understand where to start?
- Can the user complete the intended task without hidden knowledge?
- Are navigation, save states, empty states, and error states understandable?
- Does the flow respect the Nomad Life principle that Coordinator is the single communication layer?
- Does the Dashboard act as review/approval UI rather than pretending to be the agent runtime?

Typical checks:

- Quick Capture first input within 10 seconds
- Workspace navigation clarity
- Capture to dashboard feedback path
- Approval-needed actions are clearly separated from completed actions
- Mobile use does not require desktop-only assumptions

### nomad-gui-review

Focus:

- Layout breakage
- Overlap, clipping, or unreadable text
- Unreasonable whitespace or cramped spacing
- Broken responsive behavior
- Visual artifacts from implementation
- Misuse of cards, shadows, colors, margins, and token rules
- Forced multi-column layouts where unrelated full-size sections should remain in a single reading flow
- CSS column or masonry-like layouts that cause long dashboard panels to overlap, fragment, or cross panel boundaries

Typical checks:

- Desktop and mobile screenshots
- Sidebar/mobile navigation behavior
- Panel density
- Whether each major content block follows the default one-column flow, with multi-column layout reserved for compact repeated boxes
- Repeated cards in the same comparison group use one shared grid so row heights align consistently
- Button/input hit targets
- Chart and table readability
- Workout routine cards support at-a-glance reading of a normal session, about five exercises with four sets each, without wasting a full row on date metadata
- Korean text wrapping
- Design System alignment

### nomad-review-value-review

Focus:

- Does review content help the user quickly understand the whole situation?
- Is text too repetitive, generic, or long?
- Are summaries information-dense enough for the available screen space?
- Can the user see patterns, risks, and recommended actions at a glance?
- Are uncertainty and data freshness shown without bloating the screen?

Typical checks:

- Coordinator Brief
- Agent Council cards
- Weekly Review
- English review summaries
- Health and activity review cards
- Notification candidates

## Coordinator Use

Coordinator should synthesize validation findings into one practical decision:

- Fix now
- Defer with reason
- Ask user for product direction
- Update data contract or design documentation

Validation agents should not directly decide product direction, expand scope, or rewrite core architecture.

## Storage

Validation outputs may be stored under:

```txt
reports/validation/YYYY-MM-DD-ux-flow.md
reports/validation/YYYY-MM-DD-gui.md
reports/validation/YYYY-MM-DD-review-value.md
data/context/latest-validation.json
```

When automated validation scripts are added, they should preserve the same output contract.
