#!/usr/bin/env python3
"""Generate sparse notification candidates from local Nomad Life context."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from capture_store import read_captures


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate notification candidates.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD. Defaults to today in Asia/Seoul.")
    return parser.parse_args()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def candidate(
    *,
    date: str,
    now: datetime,
    kind: str,
    title: str,
    message: str,
    priority: str,
    reason: str,
    source: str,
    action: str | None = None,
) -> dict:
    return {
        "id": f"notification_{date.replace('-', '')}_{kind}",
        "created_at": now.isoformat(),
        "kind": kind,
        "title": title,
        "message": message,
        "priority": priority,
        "reason": reason,
        "source": source,
        "channel": "telegram_candidate",
        "status": "candidate",
        "send_allowed": False,
        "approval_required_before_send": True,
        "suggested_action": action,
    }


def build_candidates(date: str, now: datetime) -> list[dict]:
    today = read_json(PROJECT_ROOT / "dashboard/today.json")
    calendar_context = read_json(PROJECT_ROOT / "data/context/calendar-context.json")
    notes_context = read_json(PROJECT_ROOT / "data/context/notes-context.json")
    captures = read_captures(date, include_ignored=False)

    candidates = []
    calendar_summary = calendar_context.get("summary", {})
    notes_summary = notes_context.get("summary", {})
    schedule_density = calendar_summary.get("schedule_density")

    if schedule_density in {"medium", "heavy"}:
        candidates.append(
            candidate(
                date=date,
                now=now,
                kind="schedule_density",
                title="일정 밀도 확인",
                message="이번 캘린더 스냅샷에서 일정 밀도가 높습니다. 작업을 더 넣기 전에 이동과 회복 여지를 먼저 확인하세요.",
                priority="medium" if schedule_density == "medium" else "high",
                reason=f"schedule_density={schedule_density}",
                source="data/context/calendar-context.json",
                action="Coordinator에게 일정 기반 오늘 운영안을 질문",
            )
        )

    if not captures and now.hour >= 18:
        candidates.append(
            candidate(
                date=date,
                now=now,
                kind="missing_capture",
                title="오늘 기록 없음",
                message="오늘 capture가 아직 없습니다. 하루를 길게 정리하지 말고 한 줄만 남기면 충분합니다.",
                priority="low",
                reason="no captures for target date after evening threshold",
                source=f"data/captures/{date}.jsonl",
                action="Quick Capture에 오늘 상태 한 줄 저장",
            )
        )

    if notes_summary.get("note_count", 0) and notes_summary.get("candidate_agents"):
        candidates.append(
            candidate(
                date=date,
                now=now,
                kind="notes_context_candidate",
                title="Nomad Life 노트 후보",
                message="Nomad Life 노트 metadata가 감지되었습니다. 본문은 읽지 않았으니 필요한 경우 capture로 전환하세요.",
                priority="low",
                reason="notes context has candidate metadata",
                source="data/context/notes-context.json",
                action="노트를 capture로 전환할지 검토",
            )
        )

    actions = today.get("actions", [])
    approval_actions = [action for action in actions if action.get("approval_required") and action.get("status") == "suggested"]
    if approval_actions:
        candidates.append(
            candidate(
                date=date,
                now=now,
                kind="approval_candidates",
                title="승인 후보 있음",
                message=f"{len(approval_actions)}개의 승인 필요 action 후보가 있습니다. 급하지 않으면 Action Center에서만 확인해도 됩니다.",
                priority="low",
                reason="dashboard/today.json has approval-required suggested actions",
                source="dashboard/today.json",
                action="Action Center 확인",
            )
        )

    return candidates[:4]


def log_action(now: datetime, date: str, count: int) -> None:
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_notifications",
        "created_at": now.isoformat(),
        "agent_name": "nomad-coordinator",
        "action_type": "generate_notification_candidates",
        "target_tool": "local_files",
        "reason": "Create sparse notification candidates without sending them",
        "input": {"date": date},
        "output": {"path": "dashboard/notifications.json", "candidate_count": count},
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{date}.jsonl", record)


def generate_notifications(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    date = date or now.date().isoformat()
    candidates = build_candidates(date, now)
    payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial",
            "notes": [
                "Notification candidates only.",
                "No notification has been sent.",
                "Telegram sending requires a separate approval-aware transport step.",
            ],
        },
        "policy": {
            "default_channel": "telegram",
            "max_candidates": 4,
            "send_allowed_by_default": False,
            "approval_required_before_send": True,
        },
        "notifications": candidates,
    }
    write_json(PROJECT_ROOT / "dashboard/notifications.json", payload)
    log_action(now, date, len(candidates))
    return {
        "date": date,
        "notifications": len(candidates),
        "outputs": ["dashboard/notifications.json"],
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(generate_notifications(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
