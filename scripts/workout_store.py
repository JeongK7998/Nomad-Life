#!/usr/bin/env python3
"""Store structured workout session records."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from time_utils import local_timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = local_timezone()


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def workout_sessions_path() -> Path:
    return PROJECT_ROOT / "data/health/workout-sessions.jsonl"


def workout_date_from_payload(payload: dict, started_at: str, fallback: datetime) -> str:
    explicit_date = str(payload.get("date") or "").strip()
    if explicit_date:
        return explicit_date[:10]
    try:
        parsed = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        return parsed.astimezone(TIMEZONE).date().isoformat()
    except ValueError:
        return fallback.date().isoformat()


def read_workout_sessions(date: str | None = None, include_ignored: bool = False) -> list[dict]:
    records = read_jsonl(workout_sessions_path())
    if not include_ignored:
        records = [record for record in records if record.get("status") != "ignored"]
    if date is None:
        return records
    return [record for record in records if record.get("date") == date]


def summarize_strength_entries(entries: list[dict]) -> str:
    if not entries:
        return "세트 없음"

    by_exercise: dict[str, list[str]] = {}
    for entry in entries:
        exercise = entry.get("exercise") or "운동"
        weight = entry.get("weight_kg")
        reps = entry.get("reps")
        if entry.get("bodyweight"):
            label = f"맨몸x{reps}회" if reps is not None else "맨몸"
        elif weight is None or reps is None:
            label = "세트"
        else:
            label = f"{weight:g}kgx{reps}회"
        by_exercise.setdefault(exercise, []).append(label)

    parts = []
    for exercise, sets in by_exercise.items():
        parts.append(f"{exercise} " + ", ".join(sets) + f" 총 {len(sets)}set")
    return " / ".join(parts)


def save_workout_session(payload: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    workout_type = str(payload.get("type") or "strength")
    entries = payload.get("entries") or []
    if workout_type == "strength" and not entries:
        raise ValueError("At least one strength set is required.")

    started_at = str(payload.get("started_at") or now.isoformat())
    ended_at = str(payload.get("ended_at") or now.isoformat())
    session_date = workout_date_from_payload(payload, started_at, now)
    record = {
        "id": f"workout_session_{now.strftime('%Y%m%d_%H%M%S_%f')}",
        "created_at": now.isoformat(),
        "date": session_date,
        "type": workout_type,
        "source": str(payload.get("source") or "local_cockpit_form"),
        "client_submission_id": payload.get("client_submission_id"),
        "source_capture_id": payload.get("source_capture_id"),
        "started_at": started_at,
        "ended_at": ended_at,
        "status": "completed",
        "duration_minutes": payload.get("duration_minutes"),
        "activity_type": payload.get("activity_type") or workout_type,
        "muscle_group": payload.get("muscle_group"),
        "entries": entries,
        "note": str(payload.get("note") or "").strip() or None,
    }
    append_jsonl(workout_sessions_path(), record)
    return record


def update_workout_session(session_id: str, updates: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    records = read_jsonl(workout_sessions_path())
    for index, record in enumerate(records):
        if record.get("id") != session_id:
            continue
        entries = updates.get("entries", record.get("entries") or [])
        if str(updates.get("type") or record.get("type") or "strength") == "strength" and not entries:
            raise ValueError("At least one strength set is required.")
        updated = {
            **record,
            "updated_at": now.isoformat(),
            "date": workout_date_from_payload(updates, updates.get("started_at") or record.get("started_at") or now.isoformat(), now),
            "type": str(updates.get("type") or record.get("type") or "strength"),
            "started_at": updates.get("started_at") or record.get("started_at"),
            "ended_at": updates.get("ended_at") or now.isoformat(),
            "status": updates.get("status", record.get("status", "completed")),
            "duration_minutes": updates.get("duration_minutes", record.get("duration_minutes")),
            "activity_type": updates.get("activity_type") or record.get("activity_type") or "strength",
            "muscle_group": updates.get("muscle_group", record.get("muscle_group")),
            "client_submission_id": updates.get("client_submission_id", record.get("client_submission_id")),
            "entries": entries,
            "note": str(updates.get("note", record.get("note") or "") or "").strip() or None,
        }
        records[index] = updated
        write_jsonl(workout_sessions_path(), records)
        return updated
    raise ValueError(f"Workout session not found: {session_id}")


def delete_workout_session(session_id: str) -> dict:
    records = read_jsonl(workout_sessions_path())
    for index, record in enumerate(records):
        if record.get("id") != session_id:
            continue
        deleted = records.pop(index)
        write_jsonl(workout_sessions_path(), records)
        return deleted
    raise ValueError(f"Workout session not found: {session_id}")
