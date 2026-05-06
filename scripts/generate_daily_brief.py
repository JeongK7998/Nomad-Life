#!/usr/bin/env python3
"""Generate a simple daily brief and dashboard JSON from local captures."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from capture_store import read_captures


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")


AGENT_LABELS = {
    "nomad-calendar-context": "Calendar",
    "nomad-finance": "Finance",
    "nomad-food": "Food",
    "nomad-health": "Health",
    "nomad-notes-context": "Notes",
    "nomad-work": "Work",
    "nomad-travel-guide": "Travel Guide",
    "nomad-creator": "Creator",
    "nomad-english": "English",
    "nomad-rest": "Rest",
}


LIFE_AREAS = {
    "AI Work": "nomad-work",
    "Creator": "nomad-creator",
    "Travel": "nomad-travel-guide",
    "Health": "nomad-health",
    "Food": "nomad-food",
    "Finance": "nomad-finance",
    "English": "nomad-english",
    "Rest": "nomad-rest",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Nomad Life daily brief.")
    parser.add_argument("--date", help="Date to process in YYYY-MM-DD. Defaults to today in Asia/Seoul.")
    return parser.parse_args()


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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_context(name: str) -> dict | None:
    path = PROJECT_ROOT / f"data/context/{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "data_quality": {
                "status": "unavailable",
                "notes": [f"{path.relative_to(PROJECT_ROOT)} could not be parsed."],
            }
        }


def read_agent_reports(date: str) -> list[dict]:
    path = PROJECT_ROOT / f"data/agent_reports/{date}.json"
    if not path.exists():
        path = PROJECT_ROOT / "data/context/agent-reports.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if payload.get("date") != date:
        return []
    return payload.get("reports", [])


def council_item_from_report(report: dict) -> dict:
    agent = report.get("agent_name", "unknown")
    return {
        "agent": agent,
        "label": AGENT_LABELS.get(agent, agent),
        "status": report.get("status", "unknown"),
        "score": report.get("score", 1),
        "insight": report.get("insight", ""),
        "recommendation": report.get("recommendation", ""),
        "risk": report.get("risk"),
        "data_sources": report.get("data_sources", []),
        "confidence": report.get("confidence", 0.0),
    }


def summarize_agent(agent: str, count: int, captures: list[dict], contexts: dict | None = None) -> dict:
    contexts = contexts or {}
    label = AGENT_LABELS.get(agent, agent)
    snippets = [capture["raw_content"] for capture in captures if agent in capture.get("linked_agents", [])]
    joined = " ".join(snippets)

    status = "watch"
    score = min(5, max(1, count + 1))
    insight = f"{label} 관련 기록이 {count}개 있습니다."
    recommendation = "데이터가 더 쌓이면 더 구체적으로 조율합니다."

    if agent == "nomad-work":
        status = "good" if count else "unknown"
        insight = "작업 관련 기록이 확인되었습니다."
        recommendation = "오늘의 산출물과 다음 액션을 짧게 남기면 좋습니다."
    elif agent == "nomad-finance":
        insight = "지출 관련 기록이 확인되었습니다."
        recommendation = "예산 기준이 설정되기 전까지는 지출 후보를 누적합니다."
    elif agent == "nomad-food":
        insight = "식사 또는 카페 관련 기록이 확인되었습니다."
        recommendation = "무거운 식사가 있었다면 다음 식사는 가볍게 조정합니다."
    elif agent == "nomad-health":
        insight = "운동 또는 컨디션 관련 기록이 확인되었습니다."
        recommendation = "피로도 정보가 부족하면 강한 운동보다 가벼운 움직임을 우선합니다."
    elif agent == "nomad-english":
        status = "light"
        insight = "영어 관련 기록이 확인되었습니다."
        recommendation = "부담 없는 10분 복습 정도로 충분합니다."
    elif agent == "nomad-rest":
        status = "protect"
        insight = "휴식 또는 피로 관련 기록이 확인되었습니다."
        recommendation = "오늘 남은 시간에는 회복 여지를 확보합니다."
    elif agent == "nomad-creator":
        insight = "콘텐츠 소재가 될 수 있는 생활 기록이 확인되었습니다."
        recommendation = "당장 발행보다 소재 후보로 보관합니다."
    elif agent == "nomad-calendar-context":
        status = "context"
        calendar_summary = contexts.get("calendar", {}).get("summary", {})
        density = calendar_summary.get("schedule_density", "unknown")
        event_count = calendar_summary.get("event_count", count)
        timed_count = calendar_summary.get("timed_event_count", 0)
        insight = f"Calendar Context Agent가 {event_count}개 일정 스냅샷을 제공했습니다."
        recommendation = f"시간 지정 일정 {timed_count}개, 밀도 {density} 기준으로 작업과 회복 여지를 확인합니다."
    elif agent == "nomad-notes-context":
        status = "context"
        notes_summary = contexts.get("notes", {}).get("summary", {})
        note_count = notes_summary.get("note_count", count)
        candidate_agents = notes_summary.get("candidate_agents", [])
        candidate_labels = [
            AGENT_LABELS.get(candidate, candidate.replace("nomad-", ""))
            for candidate in candidate_agents
            if candidate != "nomad-quick-capture"
        ]
        insight = f"Notes Context Agent가 제한된 노트 metadata {note_count}개를 제공했습니다."
        if candidate_labels:
            recommendation = f"{', '.join(candidate_labels[:3])} 맥락 후보로만 참고합니다."
        else:
            recommendation = "노트는 원본 기록이 아니라 맥락 후보로만 사용합니다."

    if "못" in joined or "거의" in joined:
        score = max(1, score - 1)

    return {
        "agent": agent,
        "label": label,
        "status": status,
        "score": score,
        "insight": insight,
        "recommendation": recommendation,
        "confidence": 0.55 if count == 1 else 0.68,
    }


def build_outputs(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict, str]:
    agent_counts = Counter(agent for capture in captures for agent in capture.get("linked_agents", []))
    reports = read_agent_reports(date)
    reported_agents = {report.get("agent_name") for report in reports}
    calendar_context = read_context("calendar-context")
    notes_context = read_context("notes-context")
    contexts = {
        "calendar": calendar_context or {},
        "notes": notes_context or {},
    }

    if calendar_context and calendar_context.get("summary", {}).get("event_count", 0):
        agent_counts["nomad-calendar-context"] += 1
    if notes_context and notes_context.get("summary", {}).get("note_count", 0):
        agent_counts["nomad-notes-context"] += 1

    council = [
        summarize_agent(agent, count, captures, contexts)
        for agent, count in sorted(agent_counts.items(), key=lambda item: item[0])
        if agent != "nomad-coordinator" and agent not in reported_agents
    ]
    council.extend(council_item_from_report(report) for report in reports)
    council.sort(key=lambda item: item["label"])

    focus_today = []
    calendar_summary = (calendar_context or {}).get("summary", {})
    notes_summary = (notes_context or {}).get("summary", {})
    schedule_density_value = calendar_summary.get("schedule_density")
    if calendar_summary.get("event_count", 0):
        if schedule_density_value in {"medium", "heavy"}:
            focus_today.append("캘린더 일정 밀도를 기준으로 작업과 이동 여지 먼저 확인")
        else:
            focus_today.append("캘린더 스냅샷 기준으로 오늘의 여유 시간 확인")
    if notes_summary.get("note_count", 0):
        focus_today.append("Nomad Life 노트는 맥락 후보로만 가볍게 확인")
    if agent_counts["nomad-work"]:
        focus_today.append("작업 흐름을 유지하되 다음 액션을 짧게 정리")
    if agent_counts["nomad-food"]:
        focus_today.append("다음 식사는 가볍고 관리 가능한 선택")
    if agent_counts["nomad-rest"]:
        focus_today.append("회복 여지 확보")
    if not focus_today:
        focus_today = ["오늘의 상태를 한 줄로 기록"]

    let_go_today = ["모든 영역을 한 번에 맞추려는 부담"]
    if agent_counts["nomad-english"]:
        let_go_today.append("영어를 길게 보충하려는 계획")

    risks = []
    if schedule_density_value == "heavy":
        risks.append(
            {
                "area": "calendar",
                "level": "medium",
                "message": "시간 지정 일정 밀도가 높아 작업과 회복 여지를 함께 확인합니다.",
                "confidence": 0.62,
            }
        )
    elif schedule_density_value == "medium":
        risks.append(
            {
                "area": "calendar",
                "level": "low",
                "message": "일정 밀도가 중간 수준이라 작업 블록을 과하게 잡지 않습니다.",
                "confidence": 0.56,
            }
        )
    if agent_counts["nomad-food"]:
        risks.append(
            {
                "area": "food",
                "level": "medium",
                "message": "식사 관련 기록이 있어 포만감과 다음 식사 균형을 확인합니다.",
                "confidence": 0.55,
            }
        )
    if agent_counts["nomad-finance"]:
        risks.append(
            {
                "area": "finance",
                "level": "low",
                "message": "지출 기록이 있으나 예산 기준이 없어 burn rate 판단은 보류합니다.",
                "confidence": 0.5,
            }
        )

    missions = [
        "오늘 기록을 한 번 더 짧게 남기기",
        "다음 식사 또는 휴식 선택을 의도적으로 하기",
        "내일 이어갈 작업의 첫 액션 한 줄 적기",
    ]

    summary = (
        f"{date}에는 {len(captures)}개의 capture가 기록되었습니다. "
        "아직 데이터는 적지만 Coordinator는 작업, 식사, 지출, 회복 신호를 중심으로 오늘을 조율합니다."
    )

    today = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if captures else "empty",
            "notes": [
                "Generated from local captures only.",
                "Calendar and Notes contexts are optional read-only local app snapshots.",
                "Health and English agent reports are thin capture-based reports.",
                "Sheet, HealthKit, and transcript integrations are not connected yet.",
            ],
        },
        "summary": summary,
        "focus_today": focus_today[:3],
        "let_go_today": let_go_today,
        "risks": risks,
        "missions": missions,
        "agent_council": council,
        "local_app_context": {
            "calendar": {
                "connected": calendar_context is not None,
                "data_quality": (calendar_context or {}).get("data_quality"),
                "summary": (calendar_context or {}).get("summary"),
            },
            "notes": {
                "connected": notes_context is not None,
                "data_quality": (notes_context or {}).get("data_quality"),
                "summary": (notes_context or {}).get("summary"),
            },
        },
        "actions": [
            {
                "id": f"action_{date.replace('-', '')}_daily_review",
                "title": "오늘 기록 기반 짧은 회고 생성",
                "type": "draft",
                "approval_required": True,
                "status": "suggested",
            }
        ],
    }

    areas = []
    for area, agent in LIFE_AREAS.items():
        count = agent_counts[agent]
        score = min(5, max(1, count + 1))
        intent = "unknown"
        if agent == "nomad-work" and count:
            intent = "focus"
        elif agent in {"nomad-rest", "nomad-health", "nomad-food", "nomad-finance"} and count:
            intent = "watch"
        elif agent == "nomad-english" and count:
            intent = "let_go_lightly"
        elif agent == "nomad-creator" and count:
            intent = "optional"
        areas.append({"name": area, "score": score, "intent": intent})

    life_balance = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if captures else "empty",
            "notes": ["Scores are based on capture frequency, not complete behavioral data."],
        },
        "areas": areas,
    }

    brief_lines = [
        f"# {date} Daily Brief",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Focus Today",
        "",
        *[f"- {item}" for item in today["focus_today"]],
        "",
        "## Let Go Today",
        "",
        *[f"- {item}" for item in today["let_go_today"]],
        "",
        "## Risks",
        "",
        *[f"- {risk['area']}: {risk['message']}" for risk in risks],
        "",
        "## Missions",
        "",
        *[f"- {item}" for item in missions],
        "",
        "## Agent Council",
        "",
        *[f"- {item['label']}: {item['insight']} {item['recommendation']}" for item in council],
        "",
    ]
    return today, life_balance, "\n".join(brief_lines)


def log_action(now: datetime, date: str) -> None:
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_daily_brief",
        "created_at": now.isoformat(),
        "agent_name": "nomad-coordinator",
        "action_type": "generate_daily_brief",
        "target_tool": "local_files",
        "reason": "Generate local dashboard and report from captures",
        "input": {"date": date},
        "output": {
            "brief_path": f"reports/daily/{date}-brief.md",
            "today_dashboard_path": "dashboard/today.json",
            "life_balance_path": "dashboard/life-balance.json",
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{date}.jsonl", record)


def generate_daily_brief(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    date = date or now.date().isoformat()
    captures = read_captures(date, include_ignored=False)
    today, life_balance, brief = build_outputs(date, now, captures)

    write_json(PROJECT_ROOT / "dashboard/today.json", today)
    write_json(PROJECT_ROOT / "dashboard/life-balance.json", life_balance)
    (PROJECT_ROOT / "reports/daily").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / f"reports/daily/{date}-brief.md").write_text(brief, encoding="utf-8")
    log_action(now, date)
    return {
        "date": date,
        "captures": len(captures),
        "outputs": [
            "dashboard/today.json",
            "dashboard/life-balance.json",
            f"reports/daily/{date}-brief.md",
        ],
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(generate_daily_brief(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
