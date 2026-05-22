#!/usr/bin/env python3
"""Generate activity allocation candidates from time-related captures."""

from __future__ import annotations

import argparse
import calendar
import json
import re
from datetime import datetime
from pathlib import Path
from time_utils import local_timezone

from capture_store import read_captures
from activity_store import read_activity_sessions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = local_timezone()

AREA_KEYWORDS = {
    "AI Work": ("작업", "코딩", "개발", "ai", "codex", "claude", "프로젝트", "집중"),
    "Health": ("운동", "수영", "서핑", "헬스", "산책", "러닝", "스쿼트", "푸시업", "요가"),
    "English": ("영어", "회화", "표현", "복습", "단어", "녹취", "transcript"),
    "Creator/Social": ("콘텐츠", "블로그", "인스타", "스레드", "영상", "사진", "업로드", "조회수", "소셜"),
    "Travel/Experience": ("여행", "이동", "체험", "숙소", "공항", "예약", "관광"),
    "Rest": ("휴식", "수면", "잠", "회복", "낮잠", "쉬"),
    "Finance": ("가계부", "정산", "예산", "지출", "비용"),
}

AGENT_AREAS = {
    "nomad-work": "AI Work",
    "nomad-health": "Health",
    "nomad-english": "English",
    "nomad-creator": "Creator/Social",
    "nomad-travel-guide": "Travel/Experience",
    "nomad-rest": "Rest",
    "nomad-finance": "Finance",
}

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

ACTIVITY_AGENT_PRIORITY = (
    "nomad-work",
    "nomad-health",
    "nomad-english",
    "nomad-rest",
    "nomad-creator",
    "nomad-travel-guide",
    "nomad-finance",
)

FINANCE_ACTIVITY_KEYWORDS = ("가계부", "정산", "예산 점검", "지출 정리", "비용 정리")
MONEY_KEYWORDS = ("원", "달러", "루피아", "엔", "유로", "썼", "결제", "카드", "현금")

MERIDIEM_HINTS = {
    "오전": "am",
    "새벽": "am",
    "오후": "pm",
    "저녁": "pm",
    "밤": "pm",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate activity allocation candidates.")
    parser.add_argument("--date", help="Date to process in YYYY-MM-DD. Defaults to today in configured local timezone.")
    return parser.parse_args()


def capture_dates_for_month(target_date: str) -> list[str]:
    captures_dir = PROJECT_ROOT / "data/captures"
    month_prefix = target_date[:7]
    return sorted(path.stem for path in captures_dir.glob(f"{month_prefix}-*.jsonl") if path.stem <= target_date)


def activity_dates_for_month(target_date: str) -> list[str]:
    month_prefix = target_date[:7]
    return sorted(
        {
            session.get("date")
            for session in read_activity_sessions()
            if session.get("date", "").startswith(month_prefix) and session.get("date") <= target_date
        }
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def normalize_hour(hour: int, meridiem: str | None) -> int:
    hint = MERIDIEM_HINTS.get((meridiem or "").strip())
    if hint == "pm" and hour < 12:
        return hour + 12
    if hint == "am" and hour == 12:
        return 0
    return hour


def time_label(hour: int, minute: int = 0) -> str:
    return f"{hour:02d}:{minute:02d}"


def minutes_between(start_hour: int, start_minute: int, end_hour: int, end_minute: int) -> int:
    start = start_hour * 60 + start_minute
    end = end_hour * 60 + end_minute
    if end <= start and end_hour <= 12:
        end += 12 * 60
    if end <= start:
        end += 24 * 60
    return max(0, end - start)


def extract_range(text: str) -> dict | None:
    pattern = re.compile(
        r"(?P<start_mer>오전|오후|저녁|밤|새벽)?\s*"
        r"(?P<start_hour>\d{1,2})\s*시(?!간)\s*(?:(?P<start_minute>\d{1,2})\s*분)?\s*"
        r"(?:부터|에서|~|-)\s*"
        r"(?P<end_mer>오전|오후|저녁|밤|새벽)?\s*"
        r"(?P<end_hour>\d{1,2})\s*시(?!간)\s*(?:(?P<end_minute>\d{1,2})\s*분)?\s*(?:까지)?"
    )
    match = pattern.search(text)
    if not match:
        return None

    start_hour = normalize_hour(int(match.group("start_hour")), match.group("start_mer"))
    start_minute = int(match.group("start_minute") or 0)
    end_mer = match.group("end_mer") or match.group("start_mer")
    end_hour = normalize_hour(int(match.group("end_hour")), end_mer)
    end_minute = int(match.group("end_minute") or 0)
    duration = minutes_between(start_hour, start_minute, end_hour, end_minute)
    if duration <= 0 or duration > 16 * 60:
        return None
    return {
        "start_time": time_label(start_hour, start_minute),
        "end_time": time_label(end_hour, end_minute),
        "duration_minutes": duration,
        "time_parse_method": "range",
    }


def extract_duration(text: str) -> dict | None:
    hours_minutes = re.search(r"(?P<hours>\d+(?:\.\d+)?)\s*시간\s*(?:(?P<minutes>\d{1,2})\s*분)?", text)
    minutes_only = re.search(r"(?P<minutes>\d{1,3})\s*분", text)

    duration = None
    if hours_minutes:
        duration = int(float(hours_minutes.group("hours")) * 60) + int(hours_minutes.group("minutes") or 0)
    elif minutes_only:
        duration = int(minutes_only.group("minutes"))

    if duration is None or duration <= 0 or duration > 16 * 60:
        return None

    start_pattern = re.compile(
        r"(?P<mer>오전|오후|저녁|밤|새벽)?\s*(?P<hour>\d{1,2})\s*시(?!간)\s*(?:(?P<minute>\d{1,2})\s*분)?\s*(?:부터|쯤부터|부터)?"
    )
    start_match = start_pattern.search(text)
    start_time = None
    end_time = None
    if start_match:
        start_hour = normalize_hour(int(start_match.group("hour")), start_match.group("mer"))
        start_minute = int(start_match.group("minute") or 0)
        start_total = start_hour * 60 + start_minute
        end_total = start_total + duration
        start_time = time_label(start_hour, start_minute)
        end_time = time_label((end_total // 60) % 24, end_total % 60)

    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration,
        "time_parse_method": "duration",
    }


def extract_time_info(text: str) -> dict | None:
    return extract_range(text) or extract_duration(text)


def infer_area(capture: dict) -> tuple[str, float]:
    text = capture.get("raw_content", "")
    lowered = text.lower()
    linked_agents = capture.get("linked_agents", [])
    for agent in ACTIVITY_AGENT_PRIORITY:
        if agent not in linked_agents:
            continue
        if agent == "nomad-finance" and not any(keyword in text for keyword in FINANCE_ACTIVITY_KEYWORDS):
            continue
        return AGENT_AREAS[agent], 0.68

    for agent in linked_agents:
        if agent in AGENT_AREAS:
            if agent == "nomad-finance" and not any(keyword in text for keyword in FINANCE_ACTIVITY_KEYWORDS):
                continue
            return AGENT_AREAS[agent], 0.68

    for area, keywords in AREA_KEYWORDS.items():
        if any(keyword in lowered if keyword.isascii() else keyword in text for keyword in keywords):
            return area, 0.6

    return "Unclassified", 0.35


def review_reason_for(capture: dict, area: str, time_info: dict) -> str | None:
    text = capture.get("raw_content", "")
    linked_agents = capture.get("linked_agents", [])
    if area == "Unclassified":
        return "활동 영역을 확정하기 어렵습니다."
    if time_info["time_parse_method"] == "duration" and not time_info["start_time"]:
        return "시작 시간이 없는 duration-only 기록입니다."
    if "nomad-finance" in linked_agents and any(keyword in text for keyword in MONEY_KEYWORDS) and area != "Finance":
        return "지출 표현이 섞여 있어 활동 시간과 비용을 분리 확인해야 합니다."
    if len(linked_agents) >= 3:
        return "여러 agent 신호가 섞여 있어 분류 확인이 필요합니다."
    return None


def label_for(text: str, area: str) -> str:
    for keyword in AREA_KEYWORDS.get(area, ()):
        if keyword.isascii():
            if keyword in text.lower():
                return keyword
        elif keyword in text:
            return keyword
    return area


def session_from_capture(capture: dict) -> dict | None:
    text = capture.get("raw_content", "")
    time_info = extract_time_info(text)
    if not time_info:
        return None

    area, area_confidence = infer_area(capture)
    review_reason = review_reason_for(capture, area, time_info)
    confidence = min(0.86, max(capture.get("confidence", 0.0), area_confidence))
    if review_reason:
        confidence = min(confidence, 0.64)
    return {
        "id": f"activity_session_{capture['id'].replace('capture_', '')}",
        "date": capture["date"],
        "area": area,
        "label": label_for(text, area),
        "start_time": time_info["start_time"],
        "end_time": time_info["end_time"],
        "duration_minutes": time_info["duration_minutes"],
        "source": capture["id"],
        "source_text": text,
        "confidence": round(confidence, 2),
        "status": "candidate",
        "review_required": bool(review_reason),
        "review_reason": review_reason,
        "parse_method": time_info["time_parse_method"],
    }


def session_from_activity(activity: dict) -> dict | None:
    if activity.get("status") == "ignored":
        return None
    duration = activity.get("duration_minutes")
    if not duration:
        return None
    area = activity.get("area_label") or AREA_LABELS.get(activity.get("area"), "Unclassified")
    return {
        "id": activity["id"],
        "date": activity["date"],
        "area": area,
        "area_key": activity.get("area"),
        "label": activity.get("subcategory") or activity.get("detail") or area,
        "start_time": activity.get("start_time"),
        "end_time": activity.get("end_time"),
        "duration_minutes": int(duration),
        "source": activity["id"],
        "source_text": activity.get("detail") or "",
        "subcategory": activity.get("subcategory"),
        "place": activity.get("place"),
        "confidence": activity.get("confidence", 0.92),
        "status": activity.get("status") or "completed",
        "review_required": bool(activity.get("review_required")),
        "review_reason": activity.get("review_reason"),
        "parse_method": "structured",
    }


def summarize_sessions(sessions: list[dict], capacity_minutes: int | None = None) -> dict:
    total = sum(session["duration_minutes"] for session in sessions)
    by_area: dict[str, dict] = {}
    for session in sessions:
        area = session["area"]
        item = by_area.setdefault(area, {"area": area, "minutes": 0, "source_count": 0, "labels": []})
        item["minutes"] += session["duration_minutes"]
        item["source_count"] += 1
        if session["label"] not in item["labels"]:
            item["labels"].append(session["label"])

    areas = []
    for item in by_area.values():
        minutes = item["minutes"]
        areas.append(
            {
                "area": item["area"],
                "minutes": minutes,
                "hours": round(minutes / 60, 2),
                "share": round(minutes / total, 4) if total else 0,
                "share_of_capacity": round(minutes / capacity_minutes, 4) if capacity_minutes else 0,
                "source_count": item["source_count"],
                "labels": item["labels"][:5],
            }
        )
    return {
        "total_tracked_minutes": total,
        "total_tracked_hours": round(total / 60, 2),
        "capacity_minutes": capacity_minutes,
        "capacity_hours": round(capacity_minutes / 60, 2) if capacity_minutes else None,
        "tracked_share_of_capacity": round(total / capacity_minutes, 4) if capacity_minutes else 0,
        "untracked_minutes": max(capacity_minutes - total, 0) if capacity_minutes else None,
        "areas": sorted(areas, key=lambda item: item["minutes"], reverse=True),
    }


def sessions_for_date(date: str) -> list[dict]:
    structured = [
        session
        for activity in read_activity_sessions(date)
        for session in [session_from_activity(activity)]
        if session
    ]
    capture_candidates = [
        session
        for capture in read_captures(date, include_ignored=False)
        for session in [session_from_capture(capture)]
        if session
    ]
    return structured + capture_candidates


def generate_activity_allocation(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    target_date = date or now.date().isoformat()
    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    day_capacity_minutes = 24 * 60
    month_dates = sorted(set(capture_dates_for_month(target_date)) | set(activity_dates_for_month(target_date)))
    month_elapsed_days = target_dt.day
    month_capacity_minutes = month_elapsed_days * day_capacity_minutes

    sessions = sessions_for_date(target_date)
    sessions.sort(key=lambda item: (item["start_time"] or "99:99", item["source"]))
    month_sessions = [
        session
        for capture_date in month_dates
        for session in sessions_for_date(capture_date)
    ]
    month_sessions.sort(key=lambda item: (item["date"], item["start_time"] or "99:99", item["source"]))
    summary = summarize_sessions(sessions, capacity_minutes=day_capacity_minutes)
    month_summary = summarize_sessions(month_sessions, capacity_minutes=month_capacity_minutes)
    days_in_month = calendar.monthrange(target_dt.year, target_dt.month)[1]
    payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": target_date,
        "month": target_date[:7],
        "data_quality": {
            "status": "partial" if sessions else "empty",
            "notes": [
            "Activity allocation is candidate-based and only parses clear time expressions.",
            "Structured Nomad Quick activity sessions are included when available.",
                "Ambiguous or missing durations are excluded until correction rules are defined.",
                "Daily share uses 24 hours as capacity. Monthly share uses elapsed days in the selected month.",
            ],
        },
        "summary": summary,
        "month_summary": {
            "month": target_date[:7],
            "elapsed_days": month_elapsed_days,
            "days_in_month": days_in_month,
            **month_summary,
        },
        "sessions": sessions,
        "month_sessions": month_sessions,
    }
    write_json(PROJECT_ROOT / "data/context/activity-allocation.json", payload)
    write_json(PROJECT_ROOT / "dashboard/activity-allocation.json", payload)

    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_activity_allocation",
        "created_at": now.isoformat(),
        "agent_name": "nomad-dashboard-export",
        "action_type": "generate_activity_allocation",
        "target_tool": "local_files",
        "reason": "Create time allocation dashboard data from activity captures",
        "input": {"date": target_date},
        "output": {
            "context_path": "data/context/activity-allocation.json",
            "dashboard_path": "dashboard/activity-allocation.json",
            "session_count": len(sessions),
            "total_tracked_minutes": summary["total_tracked_minutes"],
            "month_session_count": len(month_sessions),
            "month_total_tracked_minutes": month_summary["total_tracked_minutes"],
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{now.date().isoformat()}.jsonl", record)
    return {
        "date": target_date,
        "sessions": len(sessions),
        "total_tracked_minutes": summary["total_tracked_minutes"],
        "month_sessions": len(month_sessions),
        "month_total_tracked_minutes": month_summary["total_tracked_minutes"],
        "outputs": ["data/context/activity-allocation.json", "dashboard/activity-allocation.json"],
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(generate_activity_allocation(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
