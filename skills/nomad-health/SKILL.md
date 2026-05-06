# nomad-health

## Purpose

Health tracks exercise time, workout type, workout frequency, and basic recovery signals for Nomad Life.

The goal is not medical advice. The goal is to help the Coordinator understand whether the user's activity pattern supports or conflicts with the current schedule, work load, and recovery needs.

## Input Data

- Quick captures about exercise
- Start/end time or duration
- Workout type: swimming, surfing, gym, walking, running, mobility, other
- Structured strength training details: muscle group, exercise name, weight, reps, sets, RPE, note
- Optional sets/reps/counts
- Condition, fatigue, pain, soreness
- Future Apple Health export
- Future workout app export

## Files To Read

- `data/captures/YYYY-MM-DD.jsonl`
- `data/context/latest-captures.json`
- `data/context/calendar-context.json`
- `data/health/health-summary.json`
- `data/health/workout-sessions.jsonl`
- `data/health/exercise-library.json`
- `data/health/exercise-preferences.json`
- `data/health/exercise-library.import-preview.json`
- `AGENTS.md`
- `docs/AGENT_ROLE_MAP.md`

## Files To Write

Initial thin slice:

- `data/health/health-summary.json`
- `data/health/workout-sessions.jsonl`
- `data/health/exercise-preferences.json`
- `data/health/exercise-library.import-preview.json`
- `reports/daily/YYYY-MM-DD-health.md`
- `dashboard/health.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON
- Markdown
- Terminal scripts

Apple Health / HealthKit is a later read-only workout import integration and requires explicit approval.

The local Cockpit workout detail form may create structured workout sessions without external app access.

## Procedure

1. Read recent captures and existing health summary.
2. Find exercise-related captures.
3. Extract workout duration when obvious.
4. Extract workout type and optional counts/sets when obvious.
5. Read structured workout detail form records.
6. Read the local exercise library for exercise names, muscle mapping, equipment, and optional reference detail.
7. Keep user exercise preferences separate from source exercise data.
8. Summarize strength training by body part, exercise, sets, reps, and max weight.
9. Mark uncertain fields explicitly.
10. Summarize daily and weekly exercise time.
11. Identify simple balance signals: no activity, light activity, heavy activity, possible recovery need.
12. Pass interpreted signals to Coordinator.
13. Log all writes.

## Output Shape

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "summary": {
    "exercise_minutes": 0,
    "workout_types": [],
    "session_count": 0,
    "structured_workout_count": 0,
    "strength_set_count": 0,
    "muscle_groups": [],
    "exercise_count": 0,
    "max_weights": {},
    "recovery_signal": "unknown | light | balanced | high_load"
  },
  "readiness": [
    {
      "muscle_group": "back",
      "label": "등",
      "status": "untracked | overdue | ready | cooldown | recent",
      "priority": 0,
      "reason": "최근 14일 기록 없음",
      "days_since_last": null,
      "sets_7d": 0,
      "sets_14d": 0
    }
  ],
  "recommendations": [
    {
      "type": "muscle_focus",
      "muscle_group": "back",
      "label": "등",
      "reason": "최근 14일 기록 없음",
      "suggestion": "등 중심으로 가볍게 확인"
    }
  ],
  "exercise_progression": [
    {
      "exercise": "bench_press",
      "muscle_group": "chest",
      "set_count_14d": 0,
      "max_weight_14d": null,
      "last_weight_kg": null,
      "last_reps": null,
      "last_date": null
    }
  ],
  "sessions": [
    {
      "id": "health_session_*",
      "date": "YYYY-MM-DD",
      "activity_type": "swimming",
      "duration_minutes": 60,
      "sets": null,
      "reps": null,
      "intensity": "unknown",
      "source": "capture_*",
      "confidence": 0.0
    }
  ],
  "workout_sessions": [
    {
      "id": "workout_session_*",
      "type": "strength",
      "started_at": "ISO-8601",
      "ended_at": "ISO-8601",
      "muscle_group": "chest",
      "entries": [
        {
          "muscle_group": "chest",
          "exercise": "bench_press",
          "weight_kg": 60,
          "reps": 10,
          "set_index": 1,
          "rpe": null,
          "note": null
        }
      ]
    }
  ]
}
```

## Forbidden

- Do not provide medical diagnosis.
- Do not infer exact calories, heart rate, or recovery state without data.
- Do not access Apple Health or HealthKit without explicit approval.
- Do not make the user feel forced to exercise every day.
- Do not treat local workout form records as medical data or clinical advice.
- Do not copy large external exercise reference content into the local library without license review.
- Do not store user-specific favorites or usage counts inside source exercise library records.
- Do not apply an external exercise import directly without first generating and reviewing a preview.

## Example

`오후 3시부터 1시간 수영` can become a health session with type `swimming`, duration `60`, and source capture id.
