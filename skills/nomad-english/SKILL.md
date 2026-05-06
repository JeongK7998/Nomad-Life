# nomad-english

## Purpose

English tracks study time, transcript-based learning material, repeated weak expressions, and practical progress for nomad life.

The goal is not generic language tutoring. The goal is to help the Coordinator understand what English practice happened, what material exists, and what small next step fits the user's schedule and energy.

## Input Data

- Quick captures about English study
- Start/end time or duration
- iCloud text transcripts from English practice with another AI
- Learned expressions
- Difficult expressions
- Situation notes
- Confidence score, when provided
- Calendar or travel context that implies future English situations

## Files To Read

- `data/captures/YYYY-MM-DD.jsonl`
- `data/context/latest-captures.json`
- Future `data/inbox/english-transcripts/` or configured iCloud transcript folder
- `data/english/english-notes.json`
- `AGENTS.md`
- `docs/AGENT_ROLE_MAP.md`

## Files To Write

Initial thin slice:

- `data/english/english-notes.json`
- `reports/daily/YYYY-MM-DD-english.md`
- `dashboard/english.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON
- Markdown
- Terminal scripts

Speech-to-text, transcript summarization, and voice practice tools are later additions.

## Procedure

1. Read recent captures and available transcript metadata.
2. Find English-related study records.
3. Extract study duration when obvious.
4. Identify expressions, situations, or weak points if clearly present.
5. Mark uncertain fields explicitly.
6. Summarize daily and weekly study time.
7. Track transcript count and freshness.
8. Suggest one small practical next step to Coordinator.
9. Log all writes.

## Output Shape

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "summary": {
    "study_minutes": 0,
    "transcript_count": 0,
    "practice_situations": [],
    "progress_signal": "unknown | light | steady | needs_review"
  },
  "notes": [
    {
      "id": "english_note_*",
      "date": "YYYY-MM-DD",
      "situation": null,
      "expression": null,
      "difficulty": null,
      "review_status": "candidate",
      "source": "capture_*",
      "confidence": 0.0
    }
  ]
}
```

## Forbidden

- Do not claim language progress without enough data.
- Do not store sensitive transcript content broadly unless the user explicitly approves the folder and retention policy.
- Do not turn English into a daily guilt task.
- Do not generate long study plans when the schedule or rest context is tight.

## Example

`저녁에 영어 40분, 길 묻는 표현 연습` can become study_minutes `40`, situation `directions`, and a light review candidate.
