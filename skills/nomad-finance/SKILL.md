# nomad-finance

## Purpose

Finance analyzes spending pace and spending quality for nomad life. It should help the user understand budget burn, category pressure, and value versus waste without moralizing.

## Input Data

- Date
- Amount
- Currency
- Exchange rate
- Category and subcategory
- Place
- Payment method
- Satisfaction
- Required or optional
- Notes
- Existing CSV or sheet exports
- Existing finance app scheduled exports/downloads
- Read-only finance app view/API after explicit approval
- Receipt OCR results in later versions

## Files To Read

- `data/expenses/normalized-expenses.json`
- `data/expenses/imports/`
- `data/context/latest-captures.json`
- `AGENTS.md`

## Files To Write

- `data/expenses/normalized-expenses.json`
- `reports/daily/YYYY-MM-DD-finance.md`
- `dashboard/budget.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- CSV
- JSON
- Markdown
- Terminal scripts

Google Sheets, external finance app APIs, and exchange-rate APIs are later additions.

## Procedure

1. Read existing normalized expenses and newly downloaded/exported finance files.
2. Normalize amount, currency, category, place, and source.
3. Mark imported rows with source app/export metadata.
4. Mark uncertain fields explicitly.
5. Estimate daily and weekly spending pressure.
6. Separate food, cafe, transport, experience, lodging, work, and other spending where possible.
7. Produce a short finance report.
8. Export budget dashboard data.
9. Log all file writes.

## Output Format

```json
{
  "id": "expense_...",
  "date": "YYYY-MM-DD",
  "amount": 0,
  "currency": "KRW",
  "exchange_rate": null,
  "category": "food",
  "subcategory": null,
  "place": null,
  "payment_method": null,
  "satisfaction": null,
  "required_or_optional": "optional",
  "note": "",
  "source": "finance_app_export"
}
```

## Forbidden

- Do not connect to bank or card accounts in the initial version.
- Do not replace the user's existing expense-entry app.
- Do not create a dedicated Nomad Life expense-entry workflow unless the user explicitly changes this principle.
- Do not claim exact budget health without a defined budget.
- Do not shame the user for spending.
- Do not execute payments or financial actions.

## Example

If an imported finance export contains `점심 120000 IDR`, normalize it as a food expense and analyze daily/weekly spending pressure. Incidental captures may provide context, but they are not the canonical finance ledger.
