#!/usr/bin/env python3
"""Read and update the local exercise library."""

from __future__ import annotations

import json
import re
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
            "archived": bool(pref.get("archived")),
            "usage_count": int(pref.get("usage_count") or 0),
            "last_used_at": pref.get("last_used_at"),
        })
    return sorted(
        exercises,
        key=lambda item: (
            int(item.get("display_order") if item.get("display_order") is not None else 9999),
            not item["favorite"],
            -(item["usage_count"] or 0),
            item.get("name_ko") or item.get("name_en") or item["id"],
        ),
    )


def active_exercises() -> list[dict]:
    return [exercise for exercise in merged_exercises() if not exercise.get("archived")]


def slugify(value: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value.strip().lower()).strip("_")
    return slug or "exercise"


def unique_exercise_id(base: str, existing_ids: set[str]) -> str:
    candidate = slugify(base)
    if candidate not in existing_ids:
        return candidate
    index = 2
    while f"{candidate}_{index}" in existing_ids:
        index += 1
    return f"{candidate}_{index}"


def add_custom_exercise(payload: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    library = read_library()
    exercises = library.setdefault("exercises", [])
    name_ko = str(payload.get("name_ko") or "").strip() or None
    name_en = str(payload.get("name_en") or "").strip() or None
    if not name_ko and not name_en:
        raise ValueError("name_ko or name_en is required.")
    existing_ids = {exercise["id"] for exercise in exercises}
    exercise_id = unique_exercise_id(str(payload.get("id") or name_en or name_ko), existing_ids)
    exercise = {
        "id": exercise_id,
        "name_ko": name_ko,
        "name_en": name_en,
        "primary_muscle": str(payload.get("primary_muscle") or "other"),
        "secondary_muscles": payload.get("secondary_muscles") or [],
        "equipment": payload.get("equipment") or [],
        "movement_pattern": payload.get("movement_pattern") or None,
        "difficulty": payload.get("difficulty") or None,
        "instructions": payload.get("instructions") or [],
        "source": "custom_user",
        "source_url": None,
        "display_order": next_display_order(exercises),
        "created_at": now.isoformat(),
        "needs_review": True,
    }
    exercises.append(exercise)
    library["generated_at"] = now.isoformat()
    write_json(library_path(), library)
    set_favorite(exercise_id, bool(payload.get("favorite", True)), now=now)
    return exercise


def update_exercise(exercise_id: str, updates: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    library = read_library()
    for exercise in library.get("exercises", []):
        if exercise.get("id") != exercise_id:
            continue
        for key in ("name_ko", "name_en", "primary_muscle", "movement_pattern", "difficulty"):
            if key in updates:
                value = updates[key]
                exercise[key] = str(value).strip() if value not in (None, "") else None
        for key in ("secondary_muscles", "equipment", "instructions"):
            if key in updates:
                exercise[key] = updates[key] or []
        exercise["updated_at"] = now.isoformat()
        write_json(library_path(), library)
        return exercise
    raise ValueError(f"Unknown exercise_id: {exercise_id}")


def next_display_order(exercises: list[dict]) -> int:
    orders = [
        int(exercise.get("display_order"))
        for exercise in exercises
        if exercise.get("display_order") is not None and str(exercise.get("display_order")).isdigit()
    ]
    return max(orders, default=-1) + 1


def reorder_exercises(ordered_ids: list[str], now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    library = read_library()
    exercises = library.get("exercises", [])
    by_id = {exercise.get("id"): exercise for exercise in exercises}
    clean_ids = []
    for exercise_id in ordered_ids:
        exercise_id = str(exercise_id or "").strip()
        if exercise_id and exercise_id in by_id and exercise_id not in clean_ids:
            clean_ids.append(exercise_id)
    if not clean_ids:
        raise ValueError("ordered_ids is required.")

    order = 0
    for exercise_id in clean_ids:
        by_id[exercise_id]["display_order"] = order
        by_id[exercise_id]["updated_at"] = now.isoformat()
        order += 1
    for exercise in exercises:
        if exercise.get("id") in clean_ids:
            continue
        exercise["display_order"] = order
        order += 1

    library["generated_at"] = now.isoformat()
    write_json(library_path(), library)
    return {"ordered_ids": clean_ids, "count": len(clean_ids)}


def set_archived(exercise_id: str, archived: bool, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    preferences = read_preferences()
    items = preferences.setdefault("exercises", {})
    item = items.setdefault(exercise_id, {})
    item["archived"] = archived
    item["updated_at"] = now.isoformat()
    write_json(preferences_path(), preferences)
    return item


def delete_exercise(exercise_id: str) -> dict:
    library = read_library()
    exercises = library.get("exercises", [])
    remaining = [exercise for exercise in exercises if exercise.get("id") != exercise_id]
    if len(remaining) == len(exercises):
        raise ValueError(f"Unknown exercise_id: {exercise_id}")
    library["exercises"] = remaining
    library["generated_at"] = datetime.now(TIMEZONE).isoformat()
    write_json(library_path(), library)

    preferences = read_preferences()
    preferences.setdefault("exercises", {}).pop(exercise_id, None)
    write_json(preferences_path(), preferences)
    return {"exercise_id": exercise_id, "deleted": True}


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
