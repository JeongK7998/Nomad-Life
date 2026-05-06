# nomad-dashboard-export

## Purpose

Dashboard Export converts reports and normalized local data into stable JSON files for the web cockpit. The web app should be able to render the cockpit without directly calling AI in the initial version.

## Input Data

- Daily brief
- Agent reports
- Normalized expenses
- Normalized meals
- Captures
- Action suggestions
- Weekly review in later versions

## Files To Read

- `reports/daily/*.md`
- `reports/weekly/*.md`
- `data/captures/*.jsonl`
- `data/expenses/normalized-expenses.json`
- `data/meals/normalized-meals.json`
- `dashboard/actions.json`
- `AGENTS.md`

## Files To Write

- `dashboard/today.json`
- `dashboard/weekly.json`
- `dashboard/budget.json`
- `dashboard/meal-balance.json`
- `dashboard/life-balance.json`
- `dashboard/actions.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON
- Markdown
- Terminal scripts

## Procedure

1. Read available reports and normalized data.
2. Validate required dashboard fields.
3. Keep missing data explicit instead of inventing it.
4. Generate chart-friendly arrays and summary fields.
5. Preserve approval status for action suggestions.
6. Write JSON in a stable shape.
7. Log all file writes.

## Output Format

Each dashboard file should include:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "data_quality": {
    "status": "partial",
    "notes": []
  }
}
```

## Forbidden

- Do not call AI directly from the web cockpit in the initial version.
- Do not silently omit missing data.
- Do not change dashboard schema without updating docs and dependent UI.
- Do not mark actions as approved unless the user explicitly approved them.

## Example

`dashboard/today.json` should contain the Coordinator Brief, Agent Council, missions, risks, and draft actions in one renderable file.
