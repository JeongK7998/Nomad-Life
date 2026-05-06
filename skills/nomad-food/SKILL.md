# nomad-food

## Purpose

Food balances enjoyable meals and managed meals. It should help the user keep energy, digestion, protein, vegetables, and spending in view while preserving the pleasure of travel.

## Input Data

- Meal photo or description
- Meal time
- Place
- Menu
- Cost
- Satisfaction
- Fullness
- Alcohol
- Managed or enjoyable meal estimate
- Protein, vegetable, and carb estimate
- Finance food expense data

## Files To Read

- `data/captures/YYYY-MM-DD.jsonl`
- `data/meals/normalized-meals.json`
- `data/expenses/normalized-expenses.json`
- `data/context/latest-captures.json`
- `AGENTS.md`

## Files To Write

- `data/meals/normalized-meals.json`
- `reports/daily/YYYY-MM-DD-food.md`
- `dashboard/meal-balance.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON
- Markdown
- Image files metadata
- Terminal scripts

OpenAI Vision is a later addition.

## Procedure

1. Read recent captures and existing meal records.
2. Extract meal candidates.
3. Normalize meal type, place, cost, satisfaction, fullness, and balance estimates.
4. Mark uncertain estimates explicitly.
5. Estimate managed versus enjoyable meal ratio.
6. Connect food spending with finance data where possible.
7. Produce a short food report.
8. Export meal balance dashboard data.
9. Log all file writes.

## Output Format

```json
{
  "id": "meal_...",
  "date": "YYYY-MM-DD",
  "time": null,
  "photo_url": null,
  "meal_type": "lunch",
  "place": null,
  "cost": null,
  "satisfaction": null,
  "fullness": null,
  "estimated_balance": "enjoyable",
  "protein_estimate": "unknown",
  "vegetable_estimate": "unknown",
  "carb_estimate": "unknown",
  "alcohol": false,
  "note": "",
  "source": "quick_capture"
}
```

## Forbidden

- Do not provide medical nutrition advice.
- Do not overstate nutrient estimates from weak text input.
- Do not make the system feel like a diet punishment tool.
- Do not require detailed meal logging for every meal.

## Example

`맛은 좋았는데 좀 무거웠어` can indicate high satisfaction, high fullness, and an enjoyable/heavy meal estimate.
