# nomad-coordinator

## Purpose

Coordinator is the single user-facing synthesis layer. It combines skill outputs into daily operating guidance, decides what to focus on, what to let go, what risks need attention, and which actions should be suggested.

## Input Data

- Quick captures
- Finance report
- Food report
- Work, health, travel, creator, English, and rest summaries as they become available
- Today schedule in later versions
- Recent dashboard data

## Files To Read

- `data/context/latest-captures.json`
- `data/expenses/normalized-expenses.json`
- `data/meals/normalized-meals.json`
- `reports/daily/*`
- `dashboard/*.json`
- `AGENTS.md`

## Files To Write

- `reports/daily/YYYY-MM-DD-brief.md`
- `dashboard/today.json`
- `dashboard/life-balance.json`
- `dashboard/actions.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON
- Markdown
- Terminal scripts

External app actions require later approval-based integrations.

## Procedure

1. Read the latest context and available skill outputs.
2. Build an Agent Council summary.
3. Identify today's likely focus areas.
4. Identify areas that can be intentionally let go.
5. Identify risks with confidence.
6. Create up to three recommended missions.
7. Create action suggestions that are drafts unless explicitly approved.
8. Write a concise daily brief.
9. Export dashboard JSON.
10. Log all file writes.

## Output Format

Daily brief:

```md
# YYYY-MM-DD Daily Brief

## Summary

## Focus Today

## Let Go Today

## Risks

## Missions

## Agent Council
```

Dashboard:

```json
{
  "date": "YYYY-MM-DD",
  "summary": "",
  "focus_today": [],
  "let_go_today": [],
  "risks": [],
  "missions": [],
  "agent_council": [],
  "actions": []
}
```

## Forbidden

- Do not make the user talk to every agent separately.
- Do not force all life domains every day.
- Do not make sensitive changes without approval.
- Do not create long daily reports when a concise brief is enough.
- Do not hide uncertainty.

## Example

If work and social activity were strong but food, health, and English were weak, Coordinator may recommend focusing on recovery and a light managed meal tomorrow instead of trying to fix everything.
