# nomad-quick-capture

## Purpose

Quick Capture is the entry point for all user input. It preserves the raw input, extracts obvious structure, tags likely Nomad Skills, and marks uncertainty instead of pretending to know more than the data supports.

## Input Data

- Text memo
- Voice transcription
- Photo metadata or path
- Expense amount and currency
- Place name
- Mood and condition
- Daily check-in
- Meal or receipt description

## Files To Read

- `data/inbox/local/*`
- `data/inbox/cloud/*`
- `data/context/latest-captures.json`
- `AGENTS.md`

## Files To Write

- `data/captures/YYYY-MM-DD.jsonl`
- `data/context/latest-captures.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON
- Markdown
- Terminal scripts

Vision, speech-to-text, cloud APIs, and external messaging integrations are later additions.

## Procedure

1. Receive raw capture input.
2. Generate a stable capture id.
3. Store the raw content unchanged.
4. Classify likely domains: finance, food, health, work, travel, creator, english, rest.
5. Extract obvious fields such as amount, currency, duration, place, meal, activity, mood, and next action.
6. Assign confidence.
7. Add follow-up questions only when useful.
8. Append a JSONL record to the daily capture file.
9. Update latest context for downstream skills.
10. Log the write action.

## Output Format

```json
{
  "id": "capture_YYYYMMDD_HHMMSS_slug",
  "created_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "type": "text",
  "raw_content": "",
  "media_url": null,
  "parsed_result": {},
  "linked_agents": [],
  "confidence": 0.0,
  "status": "parsed"
}
```

## Forbidden

- Do not discard raw input.
- Do not force a single category when multiple skills are relevant.
- Do not make financial, health, or schedule claims with high confidence unless the input clearly supports them.
- Do not modify external apps.
- Do not ask the user to manually classify everything.

## Example

Input:

```txt
오늘 카페에서 4시간 작업했고 점심은 12만 루피아. 맛은 좋았는데 좀 무거웠어.
```

Linked agents:

```txt
work, finance, food, rest, creator
```
