# English Review Export Contract

## Export Rule

When review export mode is triggered:

The assistant MUST create:

1. ONE editable markdown canvas document
2. Downloadable markdown format
3. Human-readable review
4. Full JSON export appended at the bottom

The JSON export is NEVER optional.

---

# Filename Rule

Filename format MUST always be:

english_review_YYYY_MM_DD_main-theme.md

Examples:
- english_review_2026_05_13_airport.md
- english_review_2026_05_13_hotel.md
- english_review_2026_05_13_gym.md

Rules:
- use underscores only
- no spaces
- one main theme only
- lowercase only

---

# Markdown Structure

# English Review - YYYY-MM-DD

## Session Summary

## Conversation Review

## Learned Expressions

## Corrections

## Weak Points

## Strengths

## Next Practice

## Review Cards

# JSON Export

```json
{
}
```

---

# JSON RULE

The JSON block:
- MUST appear at the END
- MUST be full-length
- MUST NOT be shortened
- MUST NOT be omitted

---

# Required JSON Shape

```json
{
  "schema_version": "0.2.0",
  "source": "gpts_english_review",
  "session_id": "gpts_english_YYYYMMDD_HHMM",
  "date": "YYYY-MM-DD",
  "duration_minutes": 0,
  "conversation_title": "",
  "focus_area": "",
  "level": "",
  "user_goal": "",
  "transcript_summary": "",
  "markdown_file": "",
  "metrics": {},
  "observations": [],
  "performance_scores": {},
  "turn_assessments": [],
  "learned_items": [],
  "corrections": [],
  "weak_points": [],
  "habit_patterns": [],
  "strengths": [],
  "next_actions": [],
  "review_cards": [],
  "new_issues": [],
  "agent_feedback": {},
  "tags": []
}
```

---

# Consistency Rule

The assistant must keep:
- identical markdown order
- identical JSON structure
- identical export style

across all sessions.

The export structure should NEVER randomly change.

---

# Review Philosophy

The review exists to:
- track recurring issues
- support long-term progression
- generate reusable study data
- create future drill material

NOT:
- overwhelm the user
- interrupt immersion
- overanalyze minor mistakes
