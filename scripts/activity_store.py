#!/usr/bin/env python3
"""Store structured Nomad Life activity timeline records."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from time_utils import local_timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = local_timezone()

AREA_LABELS = {
    "work": "AI Work",
    "health": "Health",
    "food": "Food",
    "english": "English",
    "creator": "Creator/Social",
    "travel": "Travel/Experience",
    "social": "Creator/Social",
    "rest": "Rest",
    "admin": "Admin",
    "unclassified": "Unclassified",
}

AREA_AGENTS = {
    "work": ["nomad-work"],
    "health": ["nomad-health"],
    "food": ["nomad-food"],
    "english": ["nomad-english"],
    "creator": ["nomad-creator"],
    "travel": ["nomad-travel-guide"],
    "social": ["nomad-creator"],
    "rest": ["nomad-rest"],
    "admin": ["nomad-coordinator"],
    "unclassified": ["nomad-coordinator"],
}

VALID_AREAS = set(AREA_LABELS)
VALID_STATUSES = {"active", "completed", "candidate", "corrected", "ignored"}


def activity_sessions_path() -> Path:
    return PROJECT_ROOT / "data/activity/activity-sessions.jsonl"


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


def read_activity_sessions(date: str | None = None, include_ignored: bool = False) -> list[dict]:
    records = read_jsonl(activity_sessions_path())
    if date is not None:
        records = [record for record in records if record.get("date") == date]
    if not include_ignored:
        records = [record for record in records if record.get("status") != "ignored"]
    return records


def slugify(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9가-힣]+", text)
    return "_".join(words[:4])[:40] or "activity"


def normalize_area(value: str | None) -> str:
    area = str(value or "unclassified").strip().lower()
    return area if area in VALID_AREAS else "unclassified"


def normalize_time(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    match = re.match(r"^(\d{1,2}):(\d{2})$", raw)
    if not match:
        raise ValueError(f"Invalid time value: {raw}")
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23 or minute > 59:
        raise ValueError(f"Invalid time value: {raw}")
    return f"{hour:02d}:{minute:02d}"


def minutes_between(start_time: str, end_time: str) -> int:
    start_hour, start_minute = [int(part) for part in start_time.split(":")]
    end_hour, end_minute = [int(part) for part in end_time.split(":")]
    start_total = start_hour * 60 + start_minute
    end_total = end_hour * 60 + end_minute
    if end_total <= start_total:
        end_total += 24 * 60
    return end_total - start_total


def resolve_time_fields(payload: dict, now: datetime) -> tuple[str | None, str | None, int | None, str]:
    mode = str(payload.get("time_mode") or "duration").strip()
    start_time = normalize_time(payload.get("start_time"))
    end_time = normalize_time(payload.get("end_time"))
    duration_value = payload.get("duration_minutes")
    duration_minutes = int(duration_value) if duration_value not in (None, "") else None

    if mode == "start_now":
        return now.strftime("%H:%M"), None, None, "active"
    if mode == "ended_now":
        end_time = now.strftime("%H:%M")
        if duration_minutes is None:
            raise ValueError("duration_minutes is required for ended_now.")
        start = now - timedelta(minutes=duration_minutes)
        return start.strftime("%H:%M"), end_time, duration_minutes, "completed"
    if mode == "range":
        if not start_time or not end_time:
            raise ValueError("start_time and end_time are required for range mode.")
        return start_time, end_time, minutes_between(start_time, end_time), "completed"
    if mode == "duration":
        if duration_minutes is None or duration_minutes <= 0:
            raise ValueError("duration_minutes is required for duration mode.")
        return None, None, duration_minutes, "completed"
    raise ValueError(f"Unsupported time_mode: {mode}")


def save_activity_session(payload: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    area = normalize_area(payload.get("area"))
    detail = str(payload.get("detail") or payload.get("memo") or "").strip()
    if not detail:
        detail = AREA_LABELS[area]

    start_time, end_time, duration_minutes, status = resolve_time_fields(payload, now)
    requested_status = str(payload.get("status") or status).strip()
    if requested_status in VALID_STATUSES:
        status = requested_status

    review_required = bool(payload.get("review_required", False))
    if area == "unclassified":
        review_required = True
    if status == "completed" and not duration_minutes:
        review_required = True

    linked_agents = payload.get("linked_agents") or AREA_AGENTS[area]
    record = {
        "id": f"activity_{now.strftime('%Y%m%d_%H%M%S_%f')}_{slugify(detail)}",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "date": str(payload.get("date") or now.date().isoformat()),
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "area": area,
        "area_label": AREA_LABELS[area],
        "subcategory": str(payload.get("subcategory") or "").strip() or None,
        "place": str(payload.get("place") or "").strip() or None,
        "detail": detail,
        "source": str(payload.get("source") or "nomad_quick"),
        "source_id": payload.get("source_id"),
        "client_submission_id": payload.get("client_submission_id")
        or (payload.get("metadata") or {}).get("client_submission_id"),
        "linked_agents": linked_agents,
        "confidence": round(float(payload.get("confidence") or 0.92), 2),
        "review_required": review_required,
        "review_reason": payload.get("review_reason") or ("활동 영역 확인 필요" if area == "unclassified" else None),
        "status": status,
        "metadata": payload.get("metadata") or {},
    }
    append_jsonl(activity_sessions_path(), record)
    return record


def update_activity_session(activity_id: str, updates: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    records = read_jsonl(activity_sessions_path())
    for index, record in enumerate(records):
        if record.get("id") != activity_id:
            continue
        payload = {
            "area": updates.get("area", record.get("area")),
            "time_mode": updates.get("time_mode", "duration"),
            "duration_minutes": updates.get("duration_minutes", record.get("duration_minutes")),
            "start_time": updates.get("start_time", record.get("start_time")),
            "end_time": updates.get("end_time", record.get("end_time")),
            "detail": updates.get("detail", record.get("detail")),
            "subcategory": updates.get("subcategory", record.get("subcategory")),
            "place": updates.get("place", record.get("place")),
            "status": updates.get("status", record.get("status", "completed")),
            "review_required": updates.get("review_required", record.get("review_required", False)),
            "review_reason": updates.get("review_reason", record.get("review_reason")),
            "metadata": updates.get("metadata", record.get("metadata") or {}),
            "linked_agents": updates.get("linked_agents", record.get("linked_agents")),
            "confidence": updates.get("confidence", record.get("confidence", 0.92)),
            "date": updates.get("date", record.get("date")),
            "source": record.get("source", "nomad_quick"),
            "source_id": record.get("source_id"),
            "client_submission_id": updates.get("client_submission_id", record.get("client_submission_id")),
        }
        start_time, end_time, duration_minutes, status = resolve_time_fields(payload, now)
        updated = {
            **record,
            "updated_at": now.isoformat(),
            "date": str(payload.get("date") or record.get("date") or now.date().isoformat()),
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration_minutes,
            "area": normalize_area(payload.get("area")),
            "area_label": AREA_LABELS[normalize_area(payload.get("area"))],
            "subcategory": str(payload.get("subcategory") or "").strip() or None,
            "place": str(payload.get("place") or "").strip() or None,
            "detail": str(payload.get("detail") or "").strip() or record.get("detail"),
            "status": status,
            "review_required": bool(payload.get("review_required", False)),
            "review_reason": payload.get("review_reason"),
            "metadata": payload.get("metadata") or {},
            "linked_agents": payload.get("linked_agents") or AREA_AGENTS[normalize_area(payload.get("area"))],
            "confidence": round(float(payload.get("confidence") or 0.92), 2),
            "client_submission_id": payload.get("client_submission_id"),
        }
        records[index] = updated
        write_jsonl(activity_sessions_path(), records)
        return updated
    raise ValueError(f"Activity session not found: {activity_id}")


def delete_activity_session(activity_id: str) -> dict:
    records = read_jsonl(activity_sessions_path())
    for index, record in enumerate(records):
        if record.get("id") != activity_id:
            continue
        deleted = {**record}
        records.pop(index)
        write_jsonl(activity_sessions_path(), records)
        return deleted
    raise ValueError(f"Activity session not found: {activity_id}")
