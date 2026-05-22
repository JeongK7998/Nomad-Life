# nomad-review-value-review

## Purpose

Validate whether dashboard and review content provides real decision value. This Skill checks whether summaries are concise, non-repetitive, information-dense, easy to scan, and organized so the user can understand the whole situation at a glance.

## Input Data

- `dashboard/*.json`
- Coordinator Brief
- Agent Council entries
- Weekly Review
- English/Health/Activity/Finance review text
- Screenshots showing rendered text density

## Files To Read

- `AGENTS.md`
- `docs/UX_VALIDATION_AGENTS.md`
- `docs/AGENT_ROLE_MAP.md`
- `dashboard/*.json`
- `reports/**/*.md`
- Relevant files under `web/`

## Files To Write

- `reports/validation/YYYY-MM-DD-review-value.md`
- `data/context/latest-validation.json` when Coordinator requests a consolidated validation context

## Available Tools

- Local files
- JSON
- Markdown
- Screenshot inspection

## Procedure

1. Identify the review surface and the user's expected decision.
2. Check whether the visible content gives a quick whole-picture understanding.
3. Detect repeated phrases, generic advice, overlong paragraphs, and low-value filler.
4. Check whether data freshness, uncertainty, risk, and next action are visible without bloating the screen.
5. Check whether content hierarchy supports scanning before deep reading.
6. Produce prioritized findings and rewrite direction when needed.

## Output Format

```json
{
  "agent": "nomad-review-value-review",
  "scope": "",
  "verdict": "pass | needs_fix | blocked",
  "findings": [],
  "passes": [],
  "open_questions": []
}
```

## Forbidden

- Do not reward long text just because it sounds complete.
- Do not hide missing data behind confident language.
- Do not repeat the same recommendation across multiple cards unless the repetition itself is meaningful.
- Do not turn review cards into essays.

## Example

If five Agent Council cards all say "꾸준히 관리가 필요합니다" without distinct evidence or action, flag the content as repetitive and low-value.
