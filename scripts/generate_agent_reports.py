#!/usr/bin/env python3
"""Generate thin domain agent reports for Coordinator synthesis."""

from __future__ import annotations

import argparse
import json
from datetime import date as date_cls
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from capture_store import read_captures
from generate_activity_allocation import session_from_capture
from workout_store import read_workout_sessions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")

HEALTH_TYPES = {
    "수영": "swimming",
    "서핑": "surfing",
    "헬스": "gym",
    "산책": "walking",
    "러닝": "running",
    "요가": "mobility",
    "운동": "exercise",
}

ENGLISH_SITUATIONS = {
    "길": "directions",
    "주문": "ordering",
    "카페": "cafe",
    "호텔": "hotel",
    "공항": "airport",
    "스몰톡": "small_talk",
    "회화": "conversation",
}

MUSCLE_GROUPS = [
    ("chest", "가슴"),
    ("back", "등"),
    ("legs", "하체"),
    ("shoulders", "어깨"),
    ("arms", "팔"),
    ("core", "코어"),
    ("full_body", "전신"),
    ("other", "기타"),
]
MUSCLE_GROUP_ORDER = {muscle_group: index for index, (muscle_group, _label) in enumerate(MUSCLE_GROUPS)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Nomad Life agent reports.")
    parser.add_argument("--date", help="Date to process in YYYY-MM-DD. Defaults to today in Asia/Seoul.")
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def infer_health_type(text: str) -> str:
    for keyword, activity_type in HEALTH_TYPES.items():
        if keyword in text:
            return activity_type
    return "exercise"


def infer_english_situation(text: str) -> str | None:
    for keyword, situation in ENGLISH_SITUATIONS.items():
        if keyword in text:
            return situation
    return None


def duration_minutes_from_capture(capture: dict) -> int | None:
    session = session_from_capture(capture)
    if session:
        return session["duration_minutes"]

    activity = capture.get("parsed_result", {}).get("activity", {})
    duration_hours = activity.get("duration_hours")
    if duration_hours is None:
        return None
    return int(float(duration_hours) * 60)


def parse_date(value: str) -> date_cls:
    return datetime.strptime(value, "%Y-%m-%d").date()


def rolling_dates(target_date: str, window_days: int = 14) -> list[str]:
    end_date = parse_date(target_date)
    return [(end_date - timedelta(days=offset)).isoformat() for offset in range(window_days - 1, -1, -1)]


def build_muscle_dashboard(target_date: str, workout_records: list[dict]) -> dict:
    end_date = parse_date(target_date)
    dates = rolling_dates(target_date)
    date_set = set(dates)
    entries_by_group_date: dict[tuple[str, str], list[dict]] = {}

    for workout in workout_records:
        workout_date = workout.get("date")
        if workout_date not in date_set:
            continue
        for entry in workout.get("entries") or []:
            muscle_group = entry.get("muscle_group") or workout.get("muscle_group") or "other"
            key = (muscle_group, workout_date)
            entries_by_group_date.setdefault(key, []).append({
                "workout_id": workout.get("id"),
                "muscle_group": muscle_group,
                "exercise": entry.get("exercise"),
                "weight_kg": entry.get("weight_kg"),
                "reps": entry.get("reps"),
                "set_index": entry.get("set_index"),
                "rpe": entry.get("rpe"),
            })

    rows = []
    summaries = []
    for muscle_group, label in MUSCLE_GROUPS:
        cells = []
        total_14d = 0
        total_7d = 0
        last_date = None
        for item_date in dates:
            entries = entries_by_group_date.get((muscle_group, item_date), [])
            set_count = len(entries)
            total_14d += set_count
            if item_date >= dates[-7]:
                total_7d += set_count
            if set_count:
                last_date = item_date
            cells.append({
                "date": item_date,
                "set_count": set_count,
                "intensity": min(3, set_count),
                "entries": entries,
            })

        days_since_last = None
        if last_date:
            days_since_last = (end_date - parse_date(last_date)).days
        rows.append({
            "muscle_group": muscle_group,
            "label": label,
            "cells": cells,
        })
        summaries.append({
            "muscle_group": muscle_group,
            "label": label,
            "last_workout_date": last_date,
            "days_since_last": days_since_last,
            "sets_7d": total_7d,
            "sets_14d": total_14d,
        })

    return {
        "window_days": 14,
        "start_date": dates[0],
        "end_date": dates[-1],
        "dates": dates,
        "rows": rows,
        "summaries": summaries,
    }


def readiness_from_summary(item: dict) -> dict:
    days_since_last = item.get("days_since_last")
    sets_14d = item.get("sets_14d") or 0
    if days_since_last is None:
        status = "untracked"
        priority = 3
        reason = "최근 14일 기록 없음"
    elif days_since_last >= 7:
        status = "overdue"
        priority = 3
        reason = f"{days_since_last}일 공백"
    elif days_since_last >= 3:
        status = "ready"
        priority = 2
        reason = f"{days_since_last}일 회복"
    elif days_since_last == 0:
        status = "recent"
        priority = 0
        reason = "오늘 운동함"
    else:
        status = "cooldown"
        priority = 1
        reason = f"{days_since_last}일 전 운동"

    if sets_14d >= 8 and status in {"ready", "overdue"}:
        priority = max(0, priority - 1)
        reason = f"{reason} · 14일 {sets_14d}세트"

    return {
        "muscle_group": item["muscle_group"],
        "label": item["label"],
        "status": status,
        "priority": priority,
        "display_order": MUSCLE_GROUP_ORDER.get(item["muscle_group"], 99),
        "reason": reason,
        "days_since_last": days_since_last,
        "sets_7d": item.get("sets_7d") or 0,
        "sets_14d": sets_14d,
    }


def build_health_recommendations(muscle_dashboard: dict) -> list[dict]:
    readiness = [readiness_from_summary(item) for item in muscle_dashboard.get("summaries", [])]
    candidates = [
        item
        for item in readiness
        if item["muscle_group"] not in {"full_body", "other"} and item["status"] in {"untracked", "overdue", "ready"}
    ]
    candidates.sort(key=lambda item: (-item["priority"], item["sets_14d"], item["display_order"]))
    return [
        {
            "type": "muscle_focus",
            "muscle_group": item["muscle_group"],
            "label": item["label"],
            "reason": item["reason"],
            "suggestion": f"{item['label']} 중심으로 가볍게 확인",
        }
        for item in candidates[:3]
    ]


def build_exercise_progression(workout_records: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for workout in workout_records:
        workout_date = workout.get("date")
        for entry in workout.get("entries") or []:
            exercise = entry.get("exercise")
            if not exercise:
                continue
            record = grouped.setdefault(
                exercise,
                {
                    "exercise": exercise,
                    "muscle_group": entry.get("muscle_group") or workout.get("muscle_group") or "other",
                    "set_count_14d": 0,
                    "max_weight_14d": None,
                    "last_weight_kg": None,
                    "last_reps": None,
                    "last_date": None,
                },
            )
            weight = entry.get("weight_kg")
            record["set_count_14d"] += 1
            if isinstance(weight, (int, float)):
                record["max_weight_14d"] = weight if record["max_weight_14d"] is None else max(record["max_weight_14d"], weight)
                if not record["last_date"] or workout_date >= record["last_date"]:
                    record["last_weight_kg"] = weight
                    record["last_reps"] = entry.get("reps")
                    record["last_date"] = workout_date

    return sorted(
        grouped.values(),
        key=lambda item: (item["last_date"] or "", item["set_count_14d"]),
        reverse=True,
    )


def build_health_report(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict]:
    health_captures = [capture for capture in captures if "nomad-health" in capture.get("linked_agents", [])]
    workout_records = read_workout_sessions(date)
    dates = rolling_dates(date)
    recent_workout_records = [
        workout
        for workout in read_workout_sessions()
        if dates[0] <= workout.get("date", "") <= dates[-1]
    ]
    sessions = []
    recovery_mentions = []

    for capture in health_captures:
        text = capture.get("raw_content", "")
        minutes = duration_minutes_from_capture(capture)
        if any(word in text for word in ["피곤", "통증", "아팠", "무리", "회복"]):
            recovery_mentions.append(capture["id"])
        sessions.append(
            {
                "id": f"health_session_{capture['id'].replace('capture_', '')}",
                "date": capture["date"],
                "activity_type": infer_health_type(text),
                "duration_minutes": minutes,
                "sets": None,
                "reps": None,
                "intensity": "unknown",
                "source": capture["id"],
                "confidence": 0.62 if minutes else 0.48,
                "status": "candidate",
            }
        )

    strength_set_count = 0
    muscle_groups = set()
    exercise_names = set()
    max_weights: dict[str, float] = {}
    for workout in workout_records:
        entries = workout.get("entries") or []
        if workout.get("muscle_group"):
            muscle_groups.add(workout["muscle_group"])
        for entry in entries:
            strength_set_count += 1
            if entry.get("muscle_group"):
                muscle_groups.add(entry["muscle_group"])
            exercise = entry.get("exercise")
            if exercise:
                exercise_names.add(exercise)
                weight = entry.get("weight_kg")
                if isinstance(weight, (int, float)):
                    max_weights[exercise] = max(weight, max_weights.get(exercise, 0))

    exercise_minutes = sum(session["duration_minutes"] or 0 for session in sessions)
    workout_types = sorted({session["activity_type"] for session in sessions})
    if recovery_mentions:
        recovery_signal = "recovery_watch"
        status = "watch"
        score = 2
        risk = "회복/피로 관련 표현이 있어 운동 강도 판단은 보수적으로 봅니다."
    elif exercise_minutes >= 90:
        recovery_signal = "high_load"
        status = "watch"
        score = 3
        risk = "운동 시간이 긴 편이라 일정과 회복 여지를 함께 확인합니다."
    elif exercise_minutes:
        recovery_signal = "balanced"
        status = "steady"
        score = 3
        risk = None
    elif strength_set_count:
        recovery_signal = "strength_recorded"
        status = "steady"
        score = 3
        risk = None
    else:
        recovery_signal = "unknown"
        status = "empty"
        score = 1
        risk = None

    summary = {
        "exercise_minutes": exercise_minutes,
        "workout_types": workout_types,
        "session_count": len(sessions),
        "structured_workout_count": len(workout_records),
        "strength_set_count": strength_set_count,
        "muscle_groups": sorted(muscle_groups),
        "exercise_count": len(exercise_names),
        "max_weights": max_weights,
        "recovery_signal": recovery_signal,
    }
    muscle_dashboard = build_muscle_dashboard(date, recent_workout_records)
    readiness = [readiness_from_summary(item) for item in muscle_dashboard["summaries"]]
    recommendations = build_health_recommendations(muscle_dashboard)
    exercise_progression = build_exercise_progression(recent_workout_records)
    health_payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if sessions or workout_records else "empty",
            "notes": [
                "Health report uses local captures and structured workout form records.",
                "Apple Health / HealthKit is not connected.",
            ],
        },
        "summary": summary,
        "muscle_dashboard": muscle_dashboard,
        "readiness": readiness,
        "recommendations": recommendations,
        "exercise_progression": exercise_progression,
        "sessions": sessions,
        "workout_sessions": workout_records,
    }
    detail_line = ""
    if strength_set_count:
        detail_line = f" 근력 세트 {strength_set_count}개, 부위 {len(muscle_groups)}개가 구조화 기록으로 저장되었습니다."
    report = {
        "id": f"agent_report_{date}_nomad_health",
        "date": date,
        "agent_name": "nomad-health",
        "status": status,
        "score": score,
        "insight": (
            f"운동 후보 {len(sessions)}개, 총 {exercise_minutes}분이 기록되었습니다.{detail_line}"
            if sessions or workout_records
            else "오늘 health capture는 아직 없습니다."
        ),
        "recommendation": (
            "강한 추가 운동보다 회복 여지를 함께 확인합니다."
            if recovery_signal in {"high_load", "recovery_watch"}
            else "가벼운 움직임 기록만 유지해도 충분합니다."
        ),
        "risk": risk,
        "data_sources": [session["source"] for session in sessions],
        "confidence": 0.64 if sessions else 0.35,
        "summary": summary,
    }
    return health_payload, report


def build_english_report(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict]:
    english_captures = [capture for capture in captures if "nomad-english" in capture.get("linked_agents", [])]
    notes = []

    for capture in english_captures:
        text = capture.get("raw_content", "")
        minutes = duration_minutes_from_capture(capture)
        notes.append(
            {
                "id": f"english_note_{capture['id'].replace('capture_', '')}",
                "date": capture["date"],
                "situation": infer_english_situation(text),
                "expression": None,
                "difficulty": "missed_or_light" if any(word in text for word in ["못", "거의"]) else None,
                "duration_minutes": minutes,
                "review_status": "candidate",
                "source": capture["id"],
                "confidence": 0.62 if minutes else 0.45,
            }
        )

    study_minutes = sum(note["duration_minutes"] or 0 for note in notes)
    practice_situations = sorted({note["situation"] for note in notes if note["situation"]})
    if study_minutes >= 30:
        progress_signal = "steady"
        status = "steady"
        score = 3
    elif study_minutes:
        progress_signal = "light"
        status = "light"
        score = 2
    elif notes:
        progress_signal = "needs_review"
        status = "watch"
        score = 2
    else:
        progress_signal = "unknown"
        status = "empty"
        score = 1

    summary = {
        "study_minutes": study_minutes,
        "transcript_count": 0,
        "practice_situations": practice_situations,
        "progress_signal": progress_signal,
    }
    english_payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if notes else "empty",
            "notes": ["English report is capture-based only. Transcript folders are not connected."],
        },
        "summary": summary,
        "notes": notes,
    }
    report = {
        "id": f"agent_report_{date}_nomad_english",
        "date": date,
        "agent_name": "nomad-english",
        "status": status,
        "score": score,
        "insight": (
            f"영어 학습 후보 {len(notes)}개, 총 {study_minutes}분이 기록되었습니다."
            if notes
            else "오늘 english capture는 아직 없습니다."
        ),
        "recommendation": (
            "오늘은 짧은 복습이나 실제 상황 표현 1개만 이어가도 충분합니다."
            if notes
            else "필요할 때만 10분 미만의 가벼운 표현 기록을 남깁니다."
        ),
        "risk": None,
        "data_sources": [note["source"] for note in notes],
        "confidence": 0.64 if notes else 0.35,
        "summary": summary,
    }
    return english_payload, report


def generate_agent_reports(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    target_date = date or now.date().isoformat()
    captures = read_captures(target_date, include_ignored=False)

    health_payload, health_report = build_health_report(target_date, now, captures)
    english_payload, english_report = build_english_report(target_date, now, captures)
    reports = [health_report, english_report]
    bundle = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": target_date,
        "data_quality": {
            "status": "partial" if captures else "empty",
            "notes": ["Thin sub-agent reports generated from local captures only."],
        },
        "reports": reports,
    }

    write_json(PROJECT_ROOT / "data/health/health-summary.json", health_payload)
    write_json(PROJECT_ROOT / "dashboard/health.json", health_payload)
    write_json(PROJECT_ROOT / "data/english/english-notes.json", english_payload)
    write_json(PROJECT_ROOT / "dashboard/english.json", english_payload)
    write_json(PROJECT_ROOT / f"data/agent_reports/{target_date}.json", bundle)
    write_json(PROJECT_ROOT / "data/context/agent-reports.json", bundle)

    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_agent_reports",
        "created_at": now.isoformat(),
        "agent_name": "nomad-dashboard-export",
        "action_type": "generate_agent_reports",
        "target_tool": "local_files",
        "reason": "Create thin sub-agent reports for Coordinator synthesis",
        "input": {"date": target_date},
        "output": {
            "agent_report_path": f"data/agent_reports/{target_date}.json",
            "report_count": len(reports),
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{target_date}.jsonl", record)
    return {
        "date": target_date,
        "reports": len(reports),
        "outputs": [
            f"data/agent_reports/{target_date}.json",
            "data/context/agent-reports.json",
            "dashboard/health.json",
            "dashboard/english.json",
        ],
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(generate_agent_reports(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
