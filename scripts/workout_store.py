#!/usr/bin/env python3
"""Store structured workout session records."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
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


def read_workout_sessions(date: str | None = None) -> list[dict]:
    records = read_jsonl(workout_sessions_path())
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
        if weight is None or reps is None:
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
    record = {
        "id": f"workout_session_{now.strftime('%Y%m%d_%H%M%S_%f')}",
        "created_at": now.isoformat(),
        "date": now.date().isoformat(),
        "type": workout_type,
        "source": str(payload.get("source") or "local_cockpit_form"),
        "source_capture_id": payload.get("source_capture_id"),
        "started_at": started_at,
        "ended_at": ended_at,
        "status": "completed",
        "muscle_group": payload.get("muscle_group"),
        "entries": entries,
        "note": str(payload.get("note") or "").strip() or None,
    }
    append_jsonl(workout_sessions_path(), record)
    return record
