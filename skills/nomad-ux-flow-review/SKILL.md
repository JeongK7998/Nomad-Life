# nomad-ux-flow-review

## Purpose

Validate whether Nomad Dashboard and Quick Panels are usable as complete user flows. This Skill checks task clarity, navigation, feedback, approval boundaries, and whether the interface supports the user's real nomad-life operating loop.

## Input Data

- Target URL or screenshots
- User scenario
- Changed dashboard/workspace list
- `dashboard/*.json`
- Relevant reports
- Browser console or interaction notes

## Files To Read

- `AGENTS.md`
- `docs/UX_VALIDATION_AGENTS.md`
- `docs/DESIGN_SYSTEM.md`
- `docs/AGENT_ROLE_MAP.md`
- `dashboard/*.json`
- `reports/**/*.md`
- Relevant files under `web/`

## Files To Write

- `reports/validation/YYYY-MM-DD-ux-flow.md`
- `data/context/latest-validation.json` when Coordinator requests a consolidated validation context

## Available Tools

- Local files
- Browser or screenshot inspection
- Markdown
- JSON

## Procedure

1. Identify the primary user scenario and expected task completion path.
2. Walk through the flow from entry point to completion or review.
3. Check whether navigation, save states, empty states, errors, and approval boundaries are understandable.
4. Confirm the Dashboard remains a review/approval surface and does not act as the Hermes runtime.
5. Mark unclear, blocked, or high-friction steps with severity.
6. Produce concise findings with concrete recommendations.

## Output Format

```json
{
  "agent": "nomad-ux-flow-review",
  "scope": "",
  "verdict": "pass | needs_fix | blocked",
  "findings": [],
  "passes": [],
  "open_questions": []
}
```

## Forbidden

- Do not expand MVP scope while reviewing.
- Do not require the user to talk to multiple domain agents.
- Do not suggest sensitive automatic actions without approval boundaries.
- Do not treat visual polish as more important than task completion.

## Example

If a user saves a workout detail but cannot tell whether it went to local fallback or Supabase queue, flag the missing feedback as a UX flow issue.
