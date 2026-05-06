#!/usr/bin/env python3
"""Read and update the local exercise library."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")


def library_path() -> Path:
    return PROJECT_ROOT / "data/health/exercise-library.json"


def preferences_path() -> Path:
    return PROJECT_ROOT / "data/health/exercise-preferences.json"


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_library() -> dict:
    return read_json(library_path(), {"schema_version": "0.1.0", "exercises": []})


def read_preferences() -> dict:
    return read_json(preferences_path(), {"schema_version": "0.1.0", "exercises": {}})


def merged_exercises() -> list[dict]:
    library = read_library()
    preferences = read_preferences().get("exercises", {})
    exercises = []
    for exercise in library.get("exercises", []):
        pref = preferences.get(exercise["id"], {})
        exercises.append({
            **exercise,
            "favorite": bool(pref.get("favorite")),
            "usage_count": int(pref.get("usage_count") or 0),
            "last_used_at": pref.get("last_used_at"),
        })
    return sorted(
        exercises,
        key=lambda item: (
            not item["favorite"],
            -(item["usage_count"] or 0),
            item.get("name_ko") or item.get("name_en") or item["id"],
        ),
    )


def set_favorite(exercise_id: str, favorite: bool, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    preferences = read_preferences()
    items = preferences.setdefault("exercises", {})
    item = items.setdefault(exercise_id, {})
    item["favorite"] = favorite
    item["updated_at"] = now.isoformat()
    write_json(preferences_path(), preferences)
    return item


def mark_used(exercise_id: str, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    preferences = read_preferences()
    items = preferences.setdefault("exercises", {})
    item = items.setdefault(exercise_id, {})
    item["usage_count"] = int(item.get("usage_count") or 0) + 1
    item["last_used_at"] = now.isoformat()
    write_json(preferences_path(), preferences)
    return item
