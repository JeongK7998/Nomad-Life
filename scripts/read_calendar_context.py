#!/usr/bin/env python3
"""Read a small read-only Apple Calendar context snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")
SWIFT_BRIDGE = PROJECT_ROOT / "scripts/local_app_bridges/calendar_context.swift"
SWIFT_BRIDGE_BIN = PROJECT_ROOT / "scripts/local_app_bridges/calendar_context"
SWIFT_BRIDGE_PLIST = PROJECT_ROOT / "scripts/local_app_bridges/CalendarContextInfo.plist"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read Apple Calendar context into data/context.")
    parser.add_argument("--days", type=int, default=2, help="Number of days from today to read.")
    parser.add_argument(
        "--output",
        default="data/context/calendar-context.json",
        help="Output path relative to the project root.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def ensure_swift_bridge() -> tuple[Path | None, str | None]:
    sources = [SWIFT_BRIDGE, SWIFT_BRIDGE_PLIST]
    if SWIFT_BRIDGE_BIN.exists():
        binary_mtime = SWIFT_BRIDGE_BIN.stat().st_mtime
        if all(source.stat().st_mtime <= binary_mtime for source in sources):
            return SWIFT_BRIDGE_BIN, None

    result = subprocess.run(
        [
            "swiftc",
            str(SWIFT_BRIDGE),
            "-o",
            str(SWIFT_BRIDGE_BIN),
            "-Xlinker",
            "-sectcreate",
            "-Xlinker",
            "__TEXT",
            "-Xlinker",
            "__info_plist",
            "-Xlinker",
            str(SWIFT_BRIDGE_PLIST),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip() or "Could not compile Calendar EventKit bridge."

    sign_result = subprocess.run(
        ["codesign", "--force", "--sign", "-", "--identifier", "life.nomad.calendar-context", str(SWIFT_BRIDGE_BIN)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if sign_result.returncode != 0:
        return None, (sign_result.stderr or sign_result.stdout).strip() or "Could not sign Calendar EventKit bridge."
    return SWIFT_BRIDGE_BIN, None


def read_calendar(days: int) -> tuple[list[dict], str | None]:
    bridge, compile_error = ensure_swift_bridge()
    if not bridge:
        return [], compile_error

    try:
        result = subprocess.run(
            [str(bridge), str(days)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return [], "Apple Calendar bridge timed out while waiting for EventKit or macOS permission."
    if result.returncode != 0:
        return [], (result.stderr or result.stdout).strip() or "Apple Calendar read failed."

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        return [], f"Calendar bridge returned invalid JSON: {exc}"
    return payload.get("events", []), None


def parse_event_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(TIMEZONE)
    except ValueError:
        return None


def schedule_density(timed_event_count: int) -> str:
    if timed_event_count == 0:
        return "empty"
    if timed_event_count <= 2:
        return "light"
    if timed_event_count <= 4:
        return "medium"
    return "heavy"


def build_summary(events: list[dict]) -> dict:
    timed_events = [event for event in events if not event.get("all_day")]
    all_day_events = [event for event in events if event.get("all_day")]
    located_events = [event for event in events if event.get("location")]
    calendars = sorted({event.get("calendar") for event in events if event.get("calendar")})
    density = schedule_density(len(timed_events))

    next_event = None
    for event in sorted(timed_events, key=lambda item: item.get("start") or ""):
        start = parse_event_time(event.get("start"))
        end = parse_event_time(event.get("end"))
        next_event = {
            "title": event.get("title"),
            "start": start.isoformat() if start else event.get("start"),
            "end": end.isoformat() if end else event.get("end"),
            "calendar": event.get("calendar"),
            "has_location": bool(event.get("location")),
        }
        break

    signals = []
    if timed_events:
        signals.append(
            {
                "type": "schedule_density",
                "level": density,
                "message": f"{len(timed_events)}개의 시간 지정 일정이 있습니다.",
            }
        )
    if located_events:
        signals.append(
            {
                "type": "movement_context",
                "level": "watch",
                "message": "장소가 있는 일정이 있어 이동 여지를 확인합니다.",
            }
        )
    if all_day_events:
        signals.append(
            {
                "type": "all_day_context",
                "level": "info",
                "message": f"{len(all_day_events)}개의 종일 일정이 있습니다.",
            }
        )

    return {
        "event_count": len(events),
        "timed_event_count": len(timed_events),
        "all_day_event_count": len(all_day_events),
        "located_event_count": len(located_events),
        "calendar_count": len(calendars),
        "schedule_density": density,
        "has_scheduled_context": bool(events),
        "next_timed_event": next_event,
        "signals": signals,
    }


def build_context(days: int) -> dict:
    now = datetime.now(TIMEZONE)
    events, error = read_calendar(days)
    status = "partial" if events else "empty"
    notes = [
        "Read-only Apple Calendar snapshot through EventKit.",
        "Date fields are stored as ISO-8601 strings.",
    ]
    if error:
        status = "unavailable"
        notes.append(error)

    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "source": "apple_calendar",
        "scope": {"days_from_today": days, "mode": "read_only"},
        "data_quality": {"status": status, "notes": notes},
        "summary": build_summary(events),
        "events": events,
    }


def log_action(now: datetime, output_path: Path, status: str, event_count: int) -> None:
    date = now.date().isoformat()
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_calendar_context",
        "created_at": now.isoformat(),
        "agent_name": "nomad-calendar-context",
        "action_type": "read_local_app_context",
        "target_tool": "apple_calendar",
        "reason": "Create read-only calendar context for Coordinator analysis",
        "input": {"scope": "today_and_near_future"},
        "output": {"path": str(output_path.relative_to(PROJECT_ROOT)), "event_count": event_count},
        "status": status,
        "approval_required": False,
        "approved_by_user": True,
        "error": None if status != "unavailable" else "Calendar context unavailable",
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{date}.jsonl", record)


def main() -> None:
    args = parse_args()
    output_path = PROJECT_ROOT / args.output
    context = build_context(max(1, args.days))
    write_json(output_path, context)
    now = datetime.now(TIMEZONE)
    log_action(now, output_path, context["data_quality"]["status"], context["summary"]["event_count"])
    print(json.dumps({"output": str(output_path), "summary": context["summary"], "data_quality": context["data_quality"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
